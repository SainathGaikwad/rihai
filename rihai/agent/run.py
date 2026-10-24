"""Rihai agent entry point.

Two ways to run the same pipeline:

  deterministic (default; no model, no key, no network)
      python -m rihai.agent.run --charges "BNS 303(2)" --custody 2025-01-10 --first-time --lang mr
      python -m rihai.agent.run --roster data/samples/roster_sample.csv --out out/
      add --polish to let the configured model (rihai.agent.llm) rewrite the prose, subject to the gate

  agentic (Claude Agent SDK, which is what AgentFoundry's Claude scaffold runs on)
      python -m rihai.agent.run --agent --charges "BNS 303(2)" --custody 2025-01-10 --first-time
      python -m rihai.agent.run --agent --roster data/samples/roster_sample.csv

In agent mode the model gets exactly six tools (rihai.agent.tools) and nothing else: built-in tools are switched
off, a PreToolUse hook denies anything that is not a Rihai tool, a Stop hook runs the citation gate over the
model's final answer and sends it back if a section does not resolve, and the runner runs the gate once more on
whatever comes out. The model can narrate; it cannot compute a date, change a maximum term or invent a section.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

from ..eligibility import Assessment, assess_roster
from ..gate import check as gate_check
from .draft import Particulars, draft
from .llm import polish as llm_polish
from .tools import _SPECS, sdk_tools

ROOT = Path(__file__).resolve().parents[2]

SYSTEM_PROMPT = """You are Rihai, an assistant to legal-aid lawyers in India working on the release of undertrial
prisoners under Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023.

Rules you cannot break, because the tools enforce them:
1. The code decides. You never state whether a prisoner is eligible, on what date, or after how many days, except by
   quoting the output of check_eligibility or assess_roster_tool. If you have not called the tool, you do not know.
2. You never compute a sentence maximum yourself. lookup_section is the only source. If it says a section is unknown,
   say so and stop; do not guess from memory.
3. Every application comes from draft_application. If you rewrite or translate any text, run check_citations on your
   version before you show it. If the gate says BLOCKED, do not show the text; show the gate report instead.
4. Statuses mean exactly what the tool says: ELIGIBLE, MUST_RELEASE_MAX_TERM, NOT_YET, EXCLUDED_LIFE_OR_DEATH,
   EXCLUDED_MULTIPLE_CASES, NEEDS_REVIEW, UNKNOWN_SECTION. Do not soften NEEDS_REVIEW into a yes or a no.
5. Nothing you produce is filed, sent or decided by you. End every answer with the one-line reminder that a legal-aid
   lawyer reviews and the court decides.
6. Prisoner names and phone numbers never appear in your summaries; use the roster identifier.

Answer in plain language a jail superintendent or a DLSA secretary can act on: status, controlling section and its
maximum term, days served, the eligibility date, and what to do next."""

RIHAI_TOOL_NAMES = [f"mcp__rihai__{n}" for n in _SPECS]


# ----------------------------------------------------------------------------------------------------------------
# deterministic pipeline
# ----------------------------------------------------------------------------------------------------------------

def read_roster(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "identifier": (r.get("identifier") or "").strip(),
                "charges": [c.strip() for c in (r.get("charges") or "").split(";") if c.strip()],
                "custody_start": (r.get("custody_start") or "").strip(),
                "first_time_offender": (r.get("first_time_offender") or "").strip().lower() in ("1", "true", "yes", "y"),
                "multiple_cases_pending": (r.get("multiple_cases_pending") or "").strip().lower() in ("1", "true", "yes", "y"),
                "delay_attributable_days": int((r.get("delay_attributable_days") or "0").strip() or 0),
            })
    return rows


def pipeline(a: Assessment, lang: str = "en", particulars: Optional[Particulars] = None, polish: bool = False) -> dict[str, Any]:
    """Assessment -> draft -> gate -> (optional) model polish -> gate again. Returns a JSON-able dict."""
    d = draft(a, particulars or Particulars(), lang=lang)
    out: dict[str, Any] = {"assessment": a.to_dict(), "lang": lang, "memo": d["memo"], "application": d["application"],
                           "gate": None, "polish": None}
    g = d["gate"]
    if g is not None:
        out["gate"] = {"blocked": g.blocked, "summary": g.summary()}
    if polish and d["application"]:
        p = llm_polish(d["application"], a, lang=lang)
        out["application"] = p.text
        out["polish"] = p.to_dict()
        g2 = gate_check(p.text)
        out["gate"] = {"blocked": g2.blocked, "summary": g2.summary()}
    return out


def run_rows(rows: list[dict[str, Any]], as_of: Optional[date], lang: str, polish: bool) -> list[dict[str, Any]]:
    return [pipeline(a, lang=lang, polish=polish) for a in assess_roster(rows, as_of=as_of)]


def write_outputs(results: list[dict[str, Any]], out_dir: str | Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["identifier", "status", "controlling", "max_term_years", "days_served", "eligible_on", "max_term_end", "release_mode",
            "first_time_offender", "reason", "gate"]
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in results:
            a = r["assessment"]
            w.writerow([a["identifier"], a["status"], a["controlling"] or "", a["max_term_years"] if a["max_term_years"] is not None else "",
                        a["days_served"] if a["days_served"] is not None else "", a["eligible_on"] or "", a["max_term_end"] or "",
                        a["release_mode"] or "", a["first_time_offender"], (a["reasons"] or [""])[0], (r["gate"] or {}).get("summary", "")])
    memos = [r["memo"] for r in results if r["assessment"]["status"] in ("ELIGIBLE", "MUST_RELEASE_MAX_TERM")]
    (out_dir / "dlsa_memos.txt").write_text("\n\n".join(memos), encoding="utf-8")
    n_apps = 0
    for r in results:
        if r["application"]:
            ident = r["assessment"]["identifier"] or f"row{n_apps + 1}"
            (out_dir / f"s479_application_{ident}_{r['lang']}.txt").write_text(r["application"], encoding="utf-8")
            n_apps += 1
    counts: dict[str, int] = {}
    for r in results:
        counts[r["assessment"]["status"]] = counts.get(r["assessment"]["status"], 0) + 1
    summary = {"rows": len(results), "counts": counts, "applications_written": n_apps, "out_dir": str(out_dir)}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


# ----------------------------------------------------------------------------------------------------------------
# Claude Agent SDK harness (AgentFoundry's Claude scaffold)
# ----------------------------------------------------------------------------------------------------------------

async def _deny_foreign_tools(input_data: dict, tool_use_id: Optional[str], context: Any) -> dict:
    """PreToolUse guardrail: only Rihai's tools may run. Everything else is denied with the reason."""
    name = input_data.get("tool_name", "")
    if name in RIHAI_TOOL_NAMES:
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": f"Rihai allows only its six tools; {name} is not one of them."}}


def _last_assistant_text(transcript_path: str) -> str:
    """Pull the final assistant text out of a Claude Code JSONL transcript. Empty string if it cannot be read."""
    text = ""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("type") != "assistant":
                    continue
                content = (rec.get("message") or {}).get("content") or []
                parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                if parts:
                    text = "\n".join(parts)
    except OSError:
        return ""
    return text


async def _gate_final_answer(input_data: dict, tool_use_id: Optional[str], context: Any) -> dict:
    """Stop guardrail: the model's final answer must pass the citation gate. If not, it is sent back once."""
    if input_data.get("stop_hook_active"):
        return {}  # already a retry; the runner's own gate will report whatever remains
    text = _last_assistant_text(input_data.get("transcript_path", ""))
    if not text:
        return {}
    g = gate_check(text)
    if g.blocked:
        return {"decision": "block", "reason": "Citation gate: " + g.summary() +
                ". Remove or correct every section that did not resolve, using lookup_section, then answer again."}
    return {}


def build_options(model: Optional[str] = None, max_turns: int = 16):
    """ClaudeAgentOptions for the Rihai agent: six MCP tools, no built-ins, both guardrail hooks."""
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, create_sdk_mcp_server  # type: ignore

    server = create_sdk_mcp_server("rihai", version="0.1.0", tools=sdk_tools())
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"rihai": server},
        tools=[],                                  # no Bash, no file tools, no web
        allowed_tools=RIHAI_TOOL_NAMES,
        disallowed_tools=["Bash", "Read", "Write", "Edit", "WebFetch", "WebSearch", "Task", "Agent"],
        permission_mode="dontAsk",                 # anything that would prompt is refused; nothing is interactive
        max_turns=max_turns,
        model=model,
        setting_sources=None,                      # hermetic: no CLAUDE.md, no user settings
        hooks={"PreToolUse": [HookMatcher(hooks=[_deny_foreign_tools])],
               "Stop": [HookMatcher(hooks=[_gate_final_answer])]},
        cwd=str(ROOT),
    )


def agent_prompt(rows: list[dict[str, Any]], lang: str, as_of: Optional[date]) -> str:
    as_of_s = (as_of or date.today()).isoformat()
    if len(rows) == 1:
        r = rows[0]
        return (f"Assess this undertrial prisoner under Section 479 BNSS as on {as_of_s} using check_eligibility, then, if eligible, "
                f"call draft_application with lang='{lang}' and show the DLSA memo and the application. Report status, controlling "
                f"section and maximum term, days served, eligibility date and next step.\n\n"
                f"identifier: {r['identifier'] or 'UTP'}\ncharges: {r['charges']}\ncustody_start: {r['custody_start']}\n"
                f"first_time_offender: {r['first_time_offender']}\nmultiple_cases_pending: {r['multiple_cases_pending']}\n"
                f"delay_attributable_days: {r['delay_attributable_days']}")
    return (f"Assess this roster under Section 479 BNSS as on {as_of_s} with assess_roster_tool (pass the JSON below as roster_json). "
            f"Then list, for the DLSA secretary: every ELIGIBLE or MUST_RELEASE_MAX_TERM prisoner with the controlling section, days "
            f"served and eligibility date; every NEEDS_REVIEW with the reason; every NOT_YET with the date it becomes eligible; the "
            f"UNKNOWN_SECTION rows. Use identifiers only.\n\nroster_json:\n{json.dumps(rows, ensure_ascii=False)}")


async def run_agent(prompt: str, options, *, echo: bool = True) -> dict[str, Any]:
    """Run one agent query; print tool calls as they happen; gate the final text once more."""
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock, query  # type: ignore

    final = ""
    tool_calls: list[str] = []
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    tool_calls.append(block.name)
                    if echo:
                        print(f"[tool] {block.name} {json.dumps(block.input, ensure_ascii=False)[:400]}", file=sys.stderr)
                elif isinstance(block, TextBlock) and echo:
                    print(block.text)
        elif isinstance(msg, ResultMessage):
            final = msg.result or ""
            if echo and msg.total_cost_usd is not None:
                print(f"[result] turns={msg.num_turns} cost=${msg.total_cost_usd:.4f}", file=sys.stderr)
    g = gate_check(final)
    verdict = {"final_text": final, "tool_calls": tool_calls, "gate": {"blocked": g.blocked, "summary": g.summary()},
               "used_rihai_tools_only": all(t in RIHAI_TOOL_NAMES for t in tool_calls), "called_check_eligibility":
               any(t.endswith("check_eligibility") or t.endswith("assess_roster_tool") for t in tool_calls)}
    if echo:
        print(f"[gate] {g.summary()}", file=sys.stderr)
    return verdict


# ----------------------------------------------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------------------------------------------

def _parse(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m rihai.agent.run", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_argument_group("one prisoner")
    src.add_argument("--charges", help="comma-separated, e.g. 'BNS 303(2), IPC/411, NDPS/20(small)'")
    src.add_argument("--custody", help="custody start, yyyy-mm-dd")
    src.add_argument("--first-time", action="store_true", help="never convicted of any offence")
    src.add_argument("--multiple-cases", action="store_true", help="another case or investigation pending (s.479(2))")
    src.add_argument("--delay", type=int, default=0, help="days of delay attributable to the accused")
    src.add_argument("--id", default="UTP-0001", help="roster identifier (never a name)")
    p.add_argument("--roster", help="CSV with identifier, charges, custody_start, first_time_offender, multiple_cases_pending, delay_attributable_days")
    p.add_argument("--as-of", help="assessment date, yyyy-mm-dd (default today)")
    p.add_argument("--lang", default="en", choices=["en", "hi", "mr"])
    p.add_argument("--polish", action="store_true", help="let the configured model rewrite the prose (rihai.agent.llm), gated")
    p.add_argument("--out", help="directory for results.csv, dlsa_memos.txt, applications")
    p.add_argument("--json", action="store_true", help="print the full result as JSON")
    p.add_argument("--agent", action="store_true", help="run through the Claude Agent SDK instead of the deterministic pipeline")
    p.add_argument("--model", help="model for --agent (default: the SDK's default)")
    p.add_argument("--max-turns", type=int, default=16)
    a = p.parse_args(argv)
    if not a.roster and not (a.charges and a.custody):
        p.error("give --roster PATH, or --charges and --custody")
    return a


def main(argv: Optional[list[str]] = None) -> int:
    a = _parse(argv)
    as_of = date.fromisoformat(a.as_of) if a.as_of else None
    if a.roster:
        rows = read_roster(a.roster)
    else:
        rows = [{"identifier": a.id, "charges": [c.strip() for c in a.charges.split(",") if c.strip()], "custody_start": a.custody,
                 "first_time_offender": a.first_time, "multiple_cases_pending": a.multiple_cases, "delay_attributable_days": a.delay}]

    if a.agent:
        try:
            options = build_options(model=a.model, max_turns=a.max_turns)
        except ImportError:
            print("claude-agent-sdk is not installed: pip install claude-agent-sdk  (or drop --agent for the deterministic run)", file=sys.stderr)
            return 2
        verdict = asyncio.run(run_agent(agent_prompt(rows, a.lang, as_of), options))
        if a.json:
            print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return 0 if not verdict["gate"]["blocked"] else 1

    results = run_rows(rows, as_of, a.lang, a.polish)
    if a.out:
        summary = write_outputs(results, a.out)
        print(json.dumps(summary, indent=2))
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif not a.out:
        for r in results:
            s = r["assessment"]
            print(f"{s['identifier']}: {s['status']}  controlling={s['controlling']} max={s['max_term_years']}y "
                  f"served={s['days_served']}d eligible_on={s['eligible_on']}")
            for reason in s["reasons"]:
                print("   - " + reason)
            if r["gate"]:
                print("   gate: " + r["gate"]["summary"])
            if r["polish"]:
                print("   polish: " + r["polish"]["reason"])
            if r["application"]:
                print()
                print(r["memo"])
                print()
                print(r["application"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
