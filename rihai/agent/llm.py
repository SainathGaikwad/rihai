"""The narrating layer. A language model may rewrite or translate a template draft; it may not change a fact.

Any OpenAI-compatible chat endpoint works, so the same code runs against Nebius (Nemotron, Llama), Meta's Llama API
(Muse Spark), Groq, Together, a local vLLM, or nothing at all. Configuration is three environment variables, or
the same three keys in .streamlit/secrets.toml (git-ignored):

    RIHAI_LLM_BASE_URL   e.g. https://api.studio.nebius.com/v1   or   https://api.llama.com/compat/v1
    RIHAI_LLM_API_KEY    the key for that endpoint (never in the repo, never in a chat)
    RIHAI_LLM_MODEL      e.g. nvidia/Llama-3_3-Nemotron-Super-49B-v1   or   Llama-4-Maverick-17B-128E-Instruct-FP8

The contract, enforced in code and not in the prompt:

  1. The model receives the finished template draft, not the case. It never sees a tool that can compute a date.
  2. Its output is accepted only if (a) the citation gate passes - every section it names exists in the law table -
     and (b) every anchor fact of the assessment (custody date, assessment date, eligibility date, days served, the
     controlling section, "479") is still present verbatim. Otherwise the template draft is returned unchanged,
     with the reason, so a reviewer sees exactly why the model's version was refused.
  3. No network, no key, or an endpoint error -> the template draft, flagged `polished: False`. The product never
     depends on a model being up.

Standard library only (urllib), so the Streamlit Cloud deploy needs nothing extra.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from ..eligibility import Assessment
from ..gate import check as gate_check

LANG_NAME = {"en": "English", "hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}

SYSTEM_POLISH = """You are a legal-aid drafting assistant for undertrial release applications in India.
You will be given a complete draft application under Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023.
Rewrite it in clear, formal court language in {lang}. You may improve grammar, flow and tone.

You must NOT:
- change, add or remove any date, number of days, number of months, number of years, or fraction;
- change, add or remove any section number or Act name; cite nothing that is not already cited;
- add any fact about the applicant, the case, the court or the law that is not in the draft;
- change the structure: keep the cause title, the heading, the numbered paragraphs, the prayer and the verification.
Keep every date exactly in the dd.mm.yyyy form it appears in, with Western Arabic digits (0-9).
Keep every statutory reference in English exactly as written, even in a Hindi or Marathi draft.
Return only the rewritten application, no commentary."""


def _secret(name: str) -> Optional[str]:
    v = os.environ.get(name)
    if v:
        return v
    try:  # Streamlit Cloud puts secrets here; fine to miss outside Streamlit
        import streamlit as st  # type: ignore
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def config() -> dict:
    return {"base_url": _secret("RIHAI_LLM_BASE_URL"), "api_key": _secret("RIHAI_LLM_API_KEY"), "model": _secret("RIHAI_LLM_MODEL")}


def available() -> bool:
    c = config()
    return bool(c["base_url"] and c["api_key"] and c["model"])


def complete(system: str, user: str, *, temperature: float = 0.2, max_tokens: int = 3000, timeout: int = 90) -> str:
    """One chat completion against the configured OpenAI-compatible endpoint. Raises on any failure."""
    c = config()
    if not available():
        raise RuntimeError("no model configured (RIHAI_LLM_BASE_URL / RIHAI_LLM_API_KEY / RIHAI_LLM_MODEL)")
    body = json.dumps({
        "model": c["model"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        c["base_url"].rstrip("/") + "/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {c['api_key']}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https endpoint from config
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _d(d: Optional[date]) -> Optional[str]:
    return d.strftime("%d.%m.%Y") if d else None


def anchors(a: Assessment, template: Optional[str] = None) -> list[str]:
    """The facts a rewrite must carry over verbatim: the dates, the day count, the controlling section, '479'.
    With a template given, only the facts that template actually states are required (an eligibility application
    does not mention the maximum-term end date, so a rewrite is not faulted for not mentioning it either)."""
    out = [_d(a.prisoner.custody_start), _d(a.as_of), _d(a.eligible_on), _d(a.max_term_end),
           str(a.days_served) if a.days_served is not None else None, "479"]
    if a.controlling is not None:
        out.append(a.controlling.section.split("/")[-1])
    out = [x for x in out if x]
    if template is not None:
        out = [x for x in out if x in template]
    return out


@dataclass
class Polished:
    text: str                 # what to show: the model's version if accepted, else the template
    polished: bool            # True only if the model's version was accepted
    reason: str               # why it was or was not
    gate_summary: str = ""
    missing_anchors: list[str] = field(default_factory=list)
    model: Optional[str] = None

    def to_dict(self) -> dict:
        return {"polished": self.polished, "reason": self.reason, "gate": self.gate_summary,
                "missing_anchors": self.missing_anchors, "model": self.model}


def accept(candidate: str, template: str, a: Assessment) -> Polished:
    """Decide whether a model's rewrite may replace the template. Pure; used by polish() and by the tests."""
    g = gate_check(candidate)
    if g.blocked:
        return Polished(template, False, "model draft refused: citation gate blocked it", g.summary(), [], None)
    # the gate also must not have fewer real citations than the template: a rewrite that silently drops the
    # Supreme Court order or a section is not an improvement
    g0 = gate_check(template)
    if len(g.citations) < len(g0.citations):
        return Polished(template, False, f"model draft refused: it cites {len(g.citations)} provisions, the template cites {len(g0.citations)}",
                        g.summary(), [], None)
    missing = [x for x in anchors(a, template) if x not in candidate]
    if missing:
        return Polished(template, False, "model draft refused: facts missing or altered", g.summary(), missing, None)
    if len(candidate) < 0.5 * len(template):
        return Polished(template, False, "model draft refused: less than half the length of the template", g.summary(), [], None)
    return Polished(candidate.strip() + "\n", True, "model draft accepted: gate passed, all anchor facts present", g.summary(), [], None)


def polish(template: str, a: Assessment, lang: str = "en", *, completer: Optional[Callable[[str, str], str]] = None) -> Polished:
    """Rewrite a template application with the configured model, then let accept() decide.

    completer: injectable for tests and other harnesses; defaults to complete() against the configured endpoint."""
    if completer is None:
        if not available():
            return Polished(template, False, "no model configured; template draft returned", gate_check(template).summary())
        completer = lambda s, u: complete(s, u)  # noqa: E731
    try:
        out = completer(SYSTEM_POLISH.format(lang=LANG_NAME.get(lang, lang)), template)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, KeyError, ValueError, RuntimeError) as e:
        return Polished(template, False, f"model unavailable ({type(e).__name__}); template draft returned", gate_check(template).summary())
    out = _strip_fences(out)
    p = accept(out, template, a)
    p.model = config().get("model")
    return p


def _strip_fences(s: str) -> str:
    s = s.strip()
    m = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", s, flags=re.S)
    return m.group(1) if m else s
