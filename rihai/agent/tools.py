"""Tools the agent may call. Plain Python with type hints and docstrings, so AgentFoundry's Build panel (and the
Claude Agent SDK / Google ADK scaffolds) can discover them. None of them can file anything, send anything, or pay
anything; they compute, look up, draft and check.

The policy lives here, not in the prompt:
  * eligibility is computed by rihai.eligibility.assess, never by the model
  * every draft passes rihai.gate.check before it is returned; a blocked draft is returned with the gate report
  * unknown sections are refused
"""
from __future__ import annotations

import json
from datetime import date
from typing import Optional

from ..eligibility import assess_roster
from ..gate import check as gate_check
from ..law import UnknownSection, lookup, stats
from .draft import Particulars, draft


def lookup_section(act: str, section: str) -> str:
    """Return the law-table row for a charge, e.g. act='BNS', section='303(2)'. Refuses unknown sections."""
    try:
        r = lookup(act, section)
    except UnknownSection as e:
        return json.dumps({"error": str(e)})
    return json.dumps(r.to_dict(), ensure_ascii=False)


def check_eligibility(charges: list[str], custody_start: str, first_time_offender: bool,
                      multiple_cases_pending: bool = False, delay_attributable_days: int = 0,
                      identifier: str = "", as_of: Optional[str] = None) -> str:
    """Section 479 BNSS eligibility for one prisoner. charges like ['BNS 303(2)', 'IPC/379', 'NDPS/20(small)'];
    dates ISO yyyy-mm-dd. Returns the assessment as JSON. Deterministic."""
    rows = [{"identifier": identifier, "charges": charges, "custody_start": custody_start,
             "first_time_offender": first_time_offender, "multiple_cases_pending": multiple_cases_pending,
             "delay_attributable_days": delay_attributable_days}]
    a = assess_roster(rows, as_of=date.fromisoformat(as_of) if as_of else None)[0]
    return json.dumps(a.to_dict(), ensure_ascii=False)


def assess_roster_tool(roster_json: str, as_of: Optional[str] = None) -> str:
    """Assess a whole roster. roster_json: JSON list of {identifier, charges, custody_start, first_time_offender,
    multiple_cases_pending, delay_attributable_days}. Returns a JSON list of assessments."""
    rows = json.loads(roster_json)
    out = assess_roster(rows, as_of=date.fromisoformat(as_of) if as_of else None)
    return json.dumps([a.to_dict() for a in out], ensure_ascii=False)


def draft_application(charges: list[str], custody_start: str, first_time_offender: bool,
                      multiple_cases_pending: bool = False, delay_attributable_days: int = 0, identifier: str = "",
                      particulars_json: str = "{}", as_of: Optional[str] = None) -> str:
    """Draft the Section 479 application and the DLSA memo for one prisoner; runs the citation gate on the draft.
    Returns JSON {status, assessment, application, memo, gate}. application is null unless the prisoner is eligible."""
    rows = [{"identifier": identifier, "charges": charges, "custody_start": custody_start,
             "first_time_offender": first_time_offender, "multiple_cases_pending": multiple_cases_pending,
             "delay_attributable_days": delay_attributable_days}]
    a = assess_roster(rows, as_of=date.fromisoformat(as_of) if as_of else None)[0]
    p = Particulars(**json.loads(particulars_json or "{}"))
    d = draft(a, p)
    g = d["gate"]
    return json.dumps({
        "status": a.status.value,
        "assessment": a.to_dict(),
        "application": d["application"],
        "memo": d["memo"],
        "gate": None if g is None else {"blocked": g.blocked, "summary": g.summary(),
                                        "citations": [c.__dict__ for c in g.citations]},
    }, ensure_ascii=False)


def check_citations(text: str) -> str:
    """Run the citation gate over any text: every statutory reference must exist in the law table.
    Returns JSON {blocked, summary, citations}. Use on any model-written or translated draft before it leaves the system."""
    g = gate_check(text)
    return json.dumps({"blocked": g.blocked, "summary": g.summary(), "citations": [c.__dict__ for c in g.citations]}, ensure_ascii=False)


def law_table_stats() -> str:
    """Size of the law table and how much of it is verified against India Code."""
    return json.dumps(stats())


PLAIN_TOOLS = [lookup_section, check_eligibility, assess_roster_tool, draft_application, check_citations, law_table_stats]

_SPECS = {
    "lookup_section": ("Look up the maximum sentence for a charged section in the verified law table.", {"act": str, "section": str}),
    "check_eligibility": ("Compute Section 479 BNSS release eligibility for one undertrial prisoner. Deterministic.",
                          {"charges": list, "custody_start": str, "first_time_offender": bool, "multiple_cases_pending": bool,
                           "delay_attributable_days": int, "identifier": str, "as_of": str}),
    "assess_roster_tool": ("Assess a whole prison roster under Section 479 BNSS.", {"roster_json": str, "as_of": str}),
    "draft_application": ("Draft the Section 479 application and DLSA memo for an eligible prisoner; runs the citation gate.",
                          {"charges": list, "custody_start": str, "first_time_offender": bool, "multiple_cases_pending": bool,
                           "delay_attributable_days": int, "identifier": str, "particulars_json": str, "as_of": str}),
    "check_citations": ("Run the citation gate over any text.", {"text": str}),
    "law_table_stats": ("Size and verification status of the law table.", {}),
}


def sdk_tools():
    """The same six functions wrapped for the Claude Agent SDK (AgentFoundry's Claude scaffold). Empty list if the
    SDK is not installed, so every other harness still works with PLAIN_TOOLS."""
    try:
        from claude_agent_sdk import tool  # type: ignore
    except Exception:
        return []
    out = []
    for f in PLAIN_TOOLS:
        desc, schema = _SPECS[f.__name__]

        async def _handler(args, _f=f):
            return {"content": [{"type": "text", "text": _f(**args)}]}

        out.append(tool(f.__name__, desc, schema)(_handler))
    return out


TOOLS = PLAIN_TOOLS
