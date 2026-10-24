"""The narrating layer and the agent harness: the model may rephrase, it may not change a fact or escape its tools."""
import asyncio
import json
from datetime import date
from pathlib import Path

import pytest

from rihai.agent import llm
from rihai.agent.draft import Particulars, draft
from rihai.agent.run import (RIHAI_TOOL_NAMES, _deny_foreign_tools, _gate_final_answer, _last_assistant_text, agent_prompt,
                             pipeline, read_roster, run_rows, write_outputs)
from rihai.eligibility import Charge, Prisoner, assess

AS_OF = date(2026, 10, 24)


def demo():
    p = Prisoner(charges=[Charge("BNS", "303(2)")], custody_start=date(2025, 1, 10), first_time_offender=True, identifier="UTP-0417")
    return assess(p, as_of=AS_OF)


def template():
    a = demo()
    return a, draft(a, Particulars(), lang="en")["application"]


# ---------------------------------------------------------------- llm.accept: the contract, without any network

def test_anchors_cover_the_facts_that_matter():
    a = demo()
    anc = llm.anchors(a)
    assert "10.01.2025" in anc and "24.10.2026" in anc and "10.01.2026" in anc and "652" in anc and "303(2)" in anc and "479" in anc


def test_faithful_rewrite_is_accepted():
    a, t = template()
    rewritten = t.replace("MOST RESPECTFULLY SHOWETH:", "MOST RESPECTFULLY SHOWETH:\n\n(The applicant submits as follows.)")
    p = llm.accept(rewritten, t, a)
    assert p.polished and p.text.startswith(rewritten[:40]) and not p.missing_anchors


def test_invented_section_is_refused_by_the_gate():
    a, t = template()
    bad = t.replace("Section 479(3) of the Sanhita", "Section 479(3) and Section 999 of the Sanhita")
    p = llm.accept(bad, t, a)
    assert not p.polished and p.text == t and "gate" in p.reason


def test_changed_date_is_refused_by_the_anchor_check():
    a, t = template()
    bad = t.replace("10.01.2026", "10.02.2026")
    p = llm.accept(bad, t, a)
    assert not p.polished and p.text == t and "10.01.2026" in p.missing_anchors


def test_changed_days_served_is_refused():
    a, t = template()
    bad = t.replace("652 days", "752 days")
    p = llm.accept(bad, t, a)
    assert not p.polished and "652" in p.missing_anchors


def test_dropping_the_supreme_court_order_is_refused():
    a, t = template()
    lines = [ln for ln in t.split("\n\n") if "Hon'ble Supreme Court of India" not in ln]
    p = llm.accept("\n\n".join(lines), t, a)
    assert not p.polished and "cites" in p.reason


def test_polish_without_a_model_returns_the_template(monkeypatch):
    for k in ("RIHAI_LLM_BASE_URL", "RIHAI_LLM_API_KEY", "RIHAI_LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    a, t = template()
    p = llm.polish(t, a)
    assert not p.polished and p.text == t and "no model configured" in p.reason


def test_polish_survives_an_endpoint_error():
    a, t = template()

    def broken(system, user):
        raise RuntimeError("502")

    p = llm.polish(t, a, completer=broken)
    assert not p.polished and p.text == t and "unavailable" in p.reason


def test_polish_strips_code_fences_and_accepts(monkeypatch):
    a, t = template()
    p = llm.polish(t, a, lang="en", completer=lambda s, u: "```text\n" + u + "\n```")
    assert p.polished and p.text.strip() == t.strip()
    assert "English" in llm.SYSTEM_POLISH.format(lang=llm.LANG_NAME["en"])


# ---------------------------------------------------------------- pipeline and roster run

def test_pipeline_demo_case():
    r = pipeline(demo(), lang="hi")
    assert r["assessment"]["status"] == "ELIGIBLE" and r["assessment"]["eligible_on"] == "2026-01-10"
    assert r["gate"] and not r["gate"]["blocked"] and r["application"] and r["lang"] == "hi"


def test_roster_run_and_outputs(tmp_path):
    rows = read_roster(Path(__file__).resolve().parents[1] / "data" / "samples" / "roster_sample.csv")
    assert len(rows) == 25 and rows[0]["charges"]
    results = run_rows(rows, AS_OF, "en", polish=False)
    summary = write_outputs(results, tmp_path)
    assert summary["rows"] == 25 and (tmp_path / "results.csv").exists() and (tmp_path / "dlsa_memos.txt").exists()
    assert summary["applications_written"] == sum(1 for r in results if r["application"])
    assert summary["applications_written"] >= 1
    for r in results:
        if r["gate"]:
            assert not r["gate"]["blocked"]


def test_agent_prompt_uses_identifiers_only():
    rows = [{"identifier": "UTP-7", "charges": ["BNS 303(2)"], "custody_start": "2025-01-10", "first_time_offender": True,
             "multiple_cases_pending": False, "delay_attributable_days": 0}]
    s = agent_prompt(rows, "mr", AS_OF)
    assert "check_eligibility" in s and "UTP-7" in s and "lang='mr'" in s and "2026-10-24" in s


# ---------------------------------------------------------------- guardrail hooks (pure functions, no SDK needed)

def test_pre_tool_use_hook_denies_everything_but_rihai():
    allow = asyncio.run(_deny_foreign_tools({"tool_name": "mcp__rihai__check_eligibility"}, "t1", None))
    deny = asyncio.run(_deny_foreign_tools({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}, "t2", None))
    assert allow == {}
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert len(RIHAI_TOOL_NAMES) == 6 and all(n.startswith("mcp__rihai__") for n in RIHAI_TOOL_NAMES)


def test_stop_hook_blocks_an_invented_section(tmp_path):
    tr = tmp_path / "t.jsonl"
    tr.write_text("\n".join([
        json.dumps({"type": "user", "message": {"content": "hi"}}),
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "He is eligible under Section 479(1) BNSS."}]}}),
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Also see Section 999 of the BNS."}]}}),
    ]), encoding="utf-8")
    assert _last_assistant_text(str(tr)) == "Also see Section 999 of the BNS."
    out = asyncio.run(_gate_final_answer({"transcript_path": str(tr), "stop_hook_active": False}, None, None))
    assert out.get("decision") == "block" and "999" in out["reason"]
    # a retry is not blocked again, so the loop always ends
    assert asyncio.run(_gate_final_answer({"transcript_path": str(tr), "stop_hook_active": True}, None, None)) == {}


def test_stop_hook_passes_a_clean_answer(tmp_path):
    tr = tmp_path / "t.jsonl"
    tr.write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "UTP-0417: ELIGIBLE under Section 479(1) BNSS; controlling BNS 303(2), 3 years; eligible since 10.01.2026."}]}}),
        encoding="utf-8")
    assert asyncio.run(_gate_final_answer({"transcript_path": str(tr), "stop_hook_active": False}, None, None)) == {}
    assert _last_assistant_text(str(tmp_path / "missing.jsonl")) == ""


def test_build_options_if_sdk_present():
    pytest.importorskip("claude_agent_sdk")
    from rihai.agent.run import build_options
    o = build_options(max_turns=3)
    assert o.tools == [] and set(o.allowed_tools) == set(RIHAI_TOOL_NAMES) and o.permission_mode == "dontAsk"
    assert "rihai" in o.mcp_servers and "PreToolUse" in o.hooks and "Stop" in o.hooks
    assert "The code decides" in o.system_prompt
