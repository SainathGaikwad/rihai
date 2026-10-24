"""The citation gate. Every statutory reference in a draft must resolve to something in the law table (or the small
list of procedural/constitutional provisions below). One unknown citation blocks the whole draft.

This is the same idea as SEEN's claim checker, pointed at sections instead of numbers: the model may write the
prose, but it cannot invent a section.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..law import UnknownSection, lookup

# Provisions a s.479 application legitimately cites that are not "offences" in the law table.
PROCEDURAL = {
    "BNSS": {"479", "479(1)", "479(2)", "479(3)", "480", "481", "482", "483", "484", "485", "486", "187", "193"},
    "CRPC": {"436A", "437", "439", "167", "173"},
    "CONSTITUTION": {"14", "21", "22", "39A"},
}

# "Section 303(2) of the Bharatiya Nyaya Sanhita, 2023", "s. 379 IPC", "Section 479 BNSS", "Article 21 of the Constitution"
# Longest alternatives first: BNSS before BNS, "NDPS Act" before "NDPS", so a prefix never wins. A trailing \b stops
# "BNS" from matching the first three letters of "BNSS".
_ACT_WORDS = (
    r"(?P<act>Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita(?:,\s*2023)?|Bharatiya\s+Nyaya\s+Sanhita(?:,\s*2023)?|BNSS|BNS(?:,?\s*2023)?|"
    r"Indian\s+Penal\s+Code(?:,\s*1860)?|IPC|Code\s+of\s+Criminal\s+Procedure(?:,\s*1973)?|Cr\.P\.C\.?|CrPC|"
    r"Constitution(?:\s+of\s+India)?|NDPS\s+Act|NDPS|Arms\s+Act|POCSO\s+Act|POCSO|Maharashtra\s+Prohibition\s+Act|MCOCA|UAPA|PMLA|"
    r"Information\s+Technology\s+Act|IT\s+Act|SC/ST\s+Act|Dowry\s+Prohibition\s+Act|Motor\s+Vehicles\s+Act|MV\s+Act)\b"
)
_SEC = r"(?P<sec>\d+[A-Z]{0,2}(?:\s*\(\s*[\w]+\s*\))*(?:\s*\(\s*[a-z]+\s*\))?)"

PATTERNS = [
    # Section 303(2) of the Bharatiya Nyaya Sanhita, 2023 / Section 479 of the BNSS
    re.compile(r"(?:Section|Sec\.?|s\.)\s*" + _SEC + r"\s*(?:of\s+the\s+|of\s+|,\s*)?" + _ACT_WORDS, re.I),
    # 303(2) BNS / 379 IPC (act after section, no 'Section' word)
    re.compile(r"\b" + _SEC + r"\s+" + _ACT_WORDS + r"\b", re.I),
    # Article 21 of the Constitution
    re.compile(r"Article\s*(?P<sec>\d+[A-Z]?)\s*(?:of\s+the\s+)?(?P<act>Constitution(?:\s+of\s+India)?)", re.I),
    # BNS s.303(2) / IPC s. 379 / NDPS s.20
    re.compile(_ACT_WORDS + r"\s*,?\s*(?:Section|Sec\.?|s\.)\s*" + _SEC, re.I),
]

ACT_MAP = {
    "bharatiya nyaya sanhita": "BNS", "bns": "BNS", "indian penal code": "IPC", "ipc": "IPC",
    "bharatiya nagarik suraksha sanhita": "BNSS", "bnss": "BNSS", "code of criminal procedure": "CRPC", "crpc": "CRPC", "cr.p.c": "CRPC", "cr.p.c.": "CRPC",
    "constitution": "CONSTITUTION", "constitution of india": "CONSTITUTION",
    "ndps act": "NDPS", "ndps": "NDPS", "arms act": "ARMS", "pocso act": "POCSO", "pocso": "POCSO",
    "maharashtra prohibition act": "MPA", "mcoca": "MCOCA", "uapa": "UAPA", "pmla": "PMLA",
    "information technology act": "IT", "it act": "IT", "sc/st act": "SCST", "dowry prohibition act": "DPA",
    "motor vehicles act": "MV", "mv act": "MV",
}


@dataclass
class Citation:
    act: str
    section: str
    text: str
    ok: bool
    reason: str = ""


@dataclass
class GateResult:
    blocked: bool
    citations: list[Citation] = field(default_factory=list)

    @property
    def failures(self) -> list[Citation]:
        return [c for c in self.citations if not c.ok]

    def summary(self) -> str:
        n = len(self.citations)
        bad = self.failures
        if not bad:
            return f"PASS - {n} citation{'s' if n != 1 else ''} matched"
        return f"BLOCKED - {len(bad)} of {n} citations unknown: " + "; ".join(f"{c.text} ({c.reason})" for c in bad)


def _norm_act(s: str) -> str:
    key = re.sub(r"\s+", " ", s.strip().lower()).replace(", 2023", "").replace(",2023", "").replace(", 1860", "").replace(", 1973", "")
    key = key.replace(" 2023", "").replace(" 1860", "").replace(" 1973", "")
    return ACT_MAP.get(key, s.strip().upper())


def _norm_sec(s: str) -> str:
    return re.sub(r"\s+", "", s)


def extract(text: str) -> list[tuple[str, str, str]]:
    seen, out = set(), []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            act, sec = _norm_act(m.group("act")), _norm_sec(m.group("sec"))
            k = (act, sec)
            if k in seen:
                continue
            seen.add(k)
            out.append((act, sec, m.group(0).strip()))
    return out


def check(text: str) -> GateResult:
    cits = []
    for act, sec, raw in extract(text):
        if act in PROCEDURAL:
            ok = sec in PROCEDURAL[act] or sec.split("(")[0] in PROCEDURAL[act]
            cits.append(Citation(act, sec, raw, ok, "" if ok else f"{act} s.{sec} is not a provision this application may cite"))
            continue
        try:
            lookup(act, sec)
            cits.append(Citation(act, sec, raw, True))
        except UnknownSection as e:
            cits.append(Citation(act, sec, raw, False, "not in the law table"))
    return GateResult(blocked=any(not c.ok for c in cits), citations=cits)
