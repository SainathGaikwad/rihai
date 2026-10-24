"""The citation gate. Every statutory reference in a draft must resolve to something in the law table (or the small
list of procedural/constitutional provisions below). One unknown citation blocks the whole draft.

This is the same idea as SEEN's claim checker, pointed at sections instead of numbers: the model may write the
prose, but it cannot invent a section.

Three kinds of reference are read:
  * named:     "Section 303(2) of the Bharatiya Nyaya Sanhita, 2023", "s. 379 IPC", "BNS s.303(2)", "Article 21 of the Constitution"
  * "the Sanhita": a s.479 application says "Section 479(2) of the Sanhita" after naming the BNSS once; the number must
               then exist in the BNSS procedural list or in the BNS law table
  * bare:      "Section 999" with no Act at all; the number must exist in an Act the same text names (or, failing
               any, in the BNSS procedural list, the BNS or the IPC). Otherwise it is an invented section and blocks.
Hindi and Marathi forms (धारा / कलम, भारतीय न्याय संहिता, भारतीय नागरिक सुरक्षा संहिता, भारतीय दंड संहिता) are read the
same way, so a translated draft is gated like an English one.
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

# A word boundary that also works after Devanagari (combining vowel signs are not \w, so \b misfires there).
_END = r"(?![A-Za-z0-9ऀ-ॿ])"

# Longest alternatives first: BNSS before BNS, "NDPS Act" before "NDPS", the full Sanhita names before bare "Sanhita",
# so a prefix never wins.
_ACT_WORDS = (
    r"(?P<act>Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita(?:,\s*2023)?|Bharatiya\s+Nyaya\s+Sanhita(?:,\s*2023)?|"
    r"भारतीय\s+नागरिक\s+सुरक्षा\s+संहिता(?:,\s*2023)?|भारतीय\s+न्याय\s+संहिता(?:,\s*2023)?|भारतीय\s+दंड\s+संहिता(?:,\s*1860)?|"
    r"BNSS|BNS(?:,?\s*2023)?|Sanhita|संहिता|"
    r"Indian\s+Penal\s+Code(?:,\s*1860)?|IPC|Code\s+of\s+Criminal\s+Procedure(?:,\s*1973)?|Cr\.P\.C\.?|CrPC|"
    r"Constitution(?:\s+of\s+India)?|NDPS\s+Act|NDPS|Arms\s+Act|POCSO\s+Act|POCSO|Maharashtra\s+Prohibition\s+Act|MCOCA|UAPA|PMLA|"
    r"Information\s+Technology\s+Act|IT\s+Act|SC/ST\s+Act|Dowry\s+Prohibition\s+Act|Motor\s+Vehicles\s+Act|MV\s+Act)" + _END
)
_SEC = r"(?P<sec>\d+[A-Z]{0,2}(?:\s*\(\s*[\w]+\s*\))*(?:\s*\(\s*[a-z]+\s*\))?)"
# "s." only as a standalone token (not the end of "years."), and never across a line break
_SECWORD = r"(?:Section|Sec\.?|(?<![A-Za-z])s\.|धारा|कलम)[ \t]*"

PATTERNS = [
    # Section 303(2) of the Bharatiya Nyaya Sanhita, 2023 / Section 479 of the BNSS / धारा 303(2) भारतीय न्याय संहिता
    re.compile(_SECWORD + _SEC + r"\s*(?:of\s+the\s+|of\s+|,\s*|के\s+तहत\s+|अन्वये\s+)?" + _ACT_WORDS, re.I),
    # 303(2) BNS / 379 IPC (act after section, no 'Section' word)
    re.compile(r"\b" + _SEC + r"\s+" + _ACT_WORDS, re.I),
    # Article 21 of the Constitution
    re.compile(r"Article\s*(?P<sec>\d+[A-Z]?)\s*(?:of\s+the\s+)?(?P<act>Constitution(?:\s+of\s+India)?)", re.I),
    # BNS s.303(2) / IPC s. 379 / NDPS s.20 / भारतीय न्याय संहिता की धारा 303(2)
    re.compile(_ACT_WORDS + r"\s+(?:की\s+|च्या\s+|चे\s+)?" + _SECWORD + _SEC, re.I),
]
# "Section 999" with nothing after it that names an Act
BARE = re.compile(_SECWORD + _SEC, re.I)

ACT_MAP = {
    "bharatiya nyaya sanhita": "BNS", "bns": "BNS", "भारतीय न्याय संहिता": "BNS",
    "indian penal code": "IPC", "ipc": "IPC", "भारतीय दंड संहिता": "IPC",
    "bharatiya nagarik suraksha sanhita": "BNSS", "bnss": "BNSS", "भारतीय नागरिक सुरक्षा संहिता": "BNSS",
    "code of criminal procedure": "CRPC", "crpc": "CRPC", "cr.p.c": "CRPC", "cr.p.c.": "CRPC",
    "constitution": "CONSTITUTION", "constitution of india": "CONSTITUTION",
    "sanhita": "SANHITA", "संहिता": "SANHITA",   # ambiguous: BNS or BNSS, resolved against both
    "ndps act": "NDPS", "ndps": "NDPS", "arms act": "ARMS", "pocso act": "POCSO", "pocso": "POCSO",
    "maharashtra prohibition act": "MPA", "mcoca": "MCOCA", "uapa": "UAPA", "pmla": "PMLA",
    "information technology act": "IT", "it act": "IT", "sc/st act": "SCST", "dowry prohibition act": "DPA",
    "motor vehicles act": "MV", "mv act": "MV",
}
BARE_ACT = "?"


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
    key = re.sub(r"\s+", " ", s.strip().lower())
    key = re.sub(r",?\s*(2023|1860|1973)$", "", key).strip()
    return ACT_MAP.get(key, s.strip().upper())


def _norm_sec(s: str) -> str:
    return re.sub(r"\s+", "", s)


def extract(text: str) -> list[tuple[str, str, str]]:
    """Distinct (act, section, raw) references in the text. Bare references come back with act '?'."""
    seen, out, spans = set(), [], []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            spans.append(m.span())
            act, sec = _norm_act(m.group("act")), _norm_sec(m.group("sec"))
            k = (act, sec)
            if k in seen:
                continue
            seen.add(k)
            out.append((act, sec, m.group(0).strip()))
    for m in BARE.finditer(text):
        s, e = m.span()
        if any(a <= s < b for a, b in spans):
            continue                                   # part of a named reference already read
        sec = _norm_sec(m.group("sec"))
        k = (BARE_ACT, sec)
        if k in seen:
            continue
        seen.add(k)
        out.append((BARE_ACT, sec, m.group(0).strip()))
    return out


def _in_law_table(act: str, sec: str) -> bool:
    try:
        lookup(act, sec)
        return True
    except UnknownSection:
        return False


def _in_procedural(act: str, sec: str) -> bool:
    return sec in PROCEDURAL.get(act, ()) or sec.split("(")[0] in PROCEDURAL.get(act, ())


def check(text: str) -> GateResult:
    refs = extract(text)
    context_acts = [a for a, _, _ in refs if a not in (BARE_ACT, "SANHITA")]
    cits = []
    for act, sec, raw in refs:
        if act == "SANHITA":
            ok = _in_procedural("BNSS", sec) or _in_law_table("BNS", sec)
            cits.append(Citation(act, sec, raw, ok, "" if ok else "no such section in the BNS or among the BNSS provisions an application may cite"))
        elif act == BARE_ACT:
            tried = []
            for a in dict.fromkeys(context_acts + ["BNSS", "BNS", "IPC"]):
                tried.append(a)
                if _in_procedural(a, sec) or (a not in PROCEDURAL and _in_law_table(a, sec)):
                    cits.append(Citation(a, sec, raw, True, "section cited without an Act; resolved to " + a))
                    break
            else:
                cits.append(Citation(act, sec, raw, False, "section cited without an Act and not found in " + "/".join(tried)))
        elif act in PROCEDURAL:
            ok = _in_procedural(act, sec)
            cits.append(Citation(act, sec, raw, ok, "" if ok else f"{act} s.{sec} is not a provision this application may cite"))
        else:
            ok = _in_law_table(act, sec)
            cits.append(Citation(act, sec, raw, ok, "" if ok else "not in the law table"))
    return GateResult(blocked=any(not c.ok for c in cits), citations=cits)
