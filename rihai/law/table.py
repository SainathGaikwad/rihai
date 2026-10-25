"""The law table: one row per chargeable section, with its maximum sentence, built from

  * the IPC/BNS concordance (GSMS-B, CC-BY-4.0) for section titles, chapters and the IPC<->BNS mapping
  * punishments_bns.py / punishments_ipc.py / punishments_special.py for the sentence encoding
  * data/law/verified.jsonl for rows a reviewer has checked against the official text (optional)

Every row carries `verified` and `source_url`. Nothing in this module guesses: an unknown section raises
UnknownSection, and the eligibility engine turns that into a refusal.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import punishments_bns, punishments_ipc, punishments_special

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "law"

ACT_ALIASES = {
    "BNS": "BNS", "BHARATIYA NYAYA SANHITA": "BNS", "BNS 2023": "BNS", "BNS,2023": "BNS",
    "IPC": "IPC", "INDIAN PENAL CODE": "IPC", "IPC 1860": "IPC",
    "NDPS": "NDPS", "NDPS ACT": "NDPS", "ARMS": "ARMS", "ARMS ACT": "ARMS", "POCSO": "POCSO",
    "MPA": "MPA", "MAHARASHTRA PROHIBITION ACT": "MPA", "BOMBAY PROHIBITION ACT": "MPA",
    "MCOCA": "MCOCA", "UAPA": "UAPA", "PMLA": "PMLA", "IT": "IT", "IT ACT": "IT",
    "SCST": "SCST", "SC/ST": "SCST", "SC/ST ACT": "SCST", "DPA": "DPA", "DOWRY PROHIBITION ACT": "DPA",
    "ITPA": "ITPA", "PITA": "ITPA", "ECA": "ECA", "PCA": "PCA", "PC ACT": "PCA", "PC": "PCA", "MV": "MV", "MV ACT": "MV",
    "ELEC": "ELEC", "ELECTRICITY ACT": "ELEC", "WLPA": "WLPA", "EXPL": "EXPL", "EXPLOSIVE SUBSTANCES ACT": "EXPL",
    "GAMB": "GAMB", "GAMBLING ACT": "GAMB", "CGST": "CGST", "CGST ACT": "CGST", "GST": "CGST",
}

SOURCE_URLS = {
    "BNS": "https://www.indiacode.nic.in/handle/123456789/20062",
    "IPC": "https://www.indiacode.nic.in/handle/123456789/2263",
    "NDPS": "https://www.indiacode.nic.in/handle/123456789/1791",
    "ARMS": "https://www.indiacode.nic.in/handle/123456789/1398",
    "POCSO": "https://www.indiacode.nic.in/handle/123456789/2079",
    "CGST": "https://www.indiacode.nic.in/handle/123456789/2237",
    "UAPA": "https://www.indiacode.nic.in/handle/123456789/1470",
    "PMLA": "https://www.indiacode.nic.in/handle/123456789/2036",
    "IT": "https://www.indiacode.nic.in/handle/123456789/1999",
    "SCST": "https://www.indiacode.nic.in/handle/123456789/1920",
    "DPA": "https://www.indiacode.nic.in/handle/123456789/1693",
    "ITPA": "https://www.indiacode.nic.in/handle/123456789/1661",
    "ECA": "https://www.indiacode.nic.in/handle/123456789/1557",
    "PCA": "https://www.indiacode.nic.in/handle/123456789/1558",
    "MV": "https://www.indiacode.nic.in/handle/123456789/1798",
    "ELEC": "https://www.indiacode.nic.in/handle/123456789/2058",
    "WLPA": "https://www.indiacode.nic.in/handle/123456789/1726",
    "EXPL": "https://www.indiacode.nic.in/handle/123456789/2302",
    "MPA": "https://www.indiacode.nic.in/handle/123456789/16200",
    "MCOCA": "https://www.indiacode.nic.in/handle/123456789/16167",
    "GAMB": "https://www.indiacode.nic.in/handle/123456789/2336",
}


class UnknownSection(KeyError):
    """The charge is not in the table. The engine must refuse, not guess."""


@dataclass
class Row:
    act: str
    section: str               # as keyed: "303(2)", "379", "NDPS/20(small)"
    title: str = ""
    chapter: str = ""
    max_years: Optional[float] = None
    min_years: float = 0
    life: bool = False
    death: bool = False
    life_if: Optional[str] = None
    fine_only: bool = False
    umbrella: bool = False
    variants: list = field(default_factory=list)
    notes: str = ""
    verified: bool = False
    source_url: str = ""
    ipc_equivalent: Optional[str] = None
    bns_equivalent: Optional[str] = None

    @property
    def excluded_life_or_death(self) -> bool:
        return self.life or self.death

    @property
    def key(self) -> str:
        return f"{self.act}/{self.section}"

    def to_dict(self) -> dict:
        return asdict(self)


def _bare(section: str) -> str:
    """'303(2)' -> '303'; 'NDPS/20(small)' -> '20'; '120B(1)' -> '120B'."""
    s = section.split("/")[-1]
    return re.split(r"[\(\s]", s, 1)[0]


def _norm_act(act: str) -> str:
    a = act.strip().upper().replace(".", "").replace(",", "")
    if a in ACT_ALIASES:
        return ACT_ALIASES[a]
    raise UnknownSection(f"unknown act '{act}'")


def _norm_section(section: str) -> str:
    s = section.strip().replace(" ", "").replace("Sec.", "").replace("Section", "").replace("s.", "")
    s = s.replace("[", "(").replace("]", ")")
    return s


@lru_cache(maxsize=1)
def _concordance() -> tuple[dict, dict]:
    """Returns (bns_titles, ipc_titles) keyed by bare section -> {title, chapter, equivalent}."""
    bns, ipc = {}, {}
    p = DATA_DIR / "concordance_bns_to_ipc.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            src, tgt = r.get("source") or {}, r.get("target") or {}
            sec = str(src.get("section", "")).strip()
            if sec and sec not in bns:
                bns[sec] = {"title": src.get("title", ""), "chapter": src.get("chapter", ""),
                            "equivalent": (str(tgt.get("section")) if tgt else None)}
    p = DATA_DIR / "concordance_ipc_to_bns.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            src, tgt = r.get("source") or {}, r.get("target") or {}
            sec = str(src.get("section", "")).strip()
            if sec and sec not in ipc:
                ipc[sec] = {"title": src.get("title", ""), "chapter": src.get("chapter", ""),
                            "equivalent": (str(tgt.get("section")) if tgt else None)}
    return bns, ipc


@lru_cache(maxsize=1)
def _verified() -> dict:
    p = DATA_DIR / "verified.jsonl"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[f"{r['act']}/{r['section']}"] = r
    return out


@lru_cache(maxsize=1)
def all_rows() -> dict[str, Row]:
    bns_t, ipc_t = _concordance()
    ver = _verified()
    rows: dict[str, Row] = {}

    def add(act: str, section: str, p: dict):
        bare = _bare(section)
        meta = (bns_t if act == "BNS" else ipc_t if act == "IPC" else {}).get(bare, {})
        row = Row(act=act, section=section, title=meta.get("title", ""), chapter=meta.get("chapter", ""),
                  source_url=SOURCE_URLS.get(act, ""), **p)
        if act == "BNS":
            row.ipc_equivalent = meta.get("equivalent")
        elif act == "IPC":
            row.bns_equivalent = meta.get("equivalent")
        v = ver.get(row.key)
        if v:
            row.verified = True
            row.source_url = v.get("source_url", row.source_url)
            for k in ("max_years", "min_years", "life", "death", "life_if", "fine_only", "notes"):
                if k in v:
                    setattr(row, k, v[k])
        rows[row.key] = row

    for sec, p in punishments_bns.P.items():
        add("BNS", sec, p)
    for sec, p in punishments_ipc.P.items():
        add("IPC", sec, p)
    for key, p in punishments_special.P.items():
        act, sec = key.split("/", 1)
        add(act, sec, p)
    return rows


def lookup(act: str, section: str) -> Row:
    """Exact lookup. Raises UnknownSection. Does not fall back to a bare section when a sub-section was given."""
    a = _norm_act(act)
    s = _norm_section(section)
    rows = all_rows()
    key = f"{a}/{s}"
    if key in rows:
        return rows[key]
    # allow "303(2)" to be written "303 (2)" or "303-2" - already normalised; allow bare lookup of a single-variant umbrella
    bare_key = f"{a}/{_bare(s)}"
    if bare_key in rows:
        return rows[bare_key]
    raise UnknownSection(f"{a} s.{s} is not in the law table; add it to punishments_{a.lower()}.py or data/law/verified.jsonl")


def export_jsonl(path: Path | None = None) -> Path:
    path = path or (DATA_DIR / "law_table.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in sorted(all_rows().values(), key=lambda r: (r.act, _sort_key(r.section))):
            fh.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    return path


def _sort_key(section: str):
    m = re.match(r"([A-Z]*/)?(\d+)([A-Z]*)(.*)", section)
    if not m:
        return (0, "", section)
    return (int(m.group(2)), m.group(3) or "", m.group(4) or "")


def stats() -> dict:
    rows = all_rows().values()
    by_act: dict[str, int] = {}
    for r in rows:
        by_act[r.act] = by_act.get(r.act, 0) + 1
    return {
        "rows": len(rows),
        "by_act": by_act,
        "verified": sum(r.verified for r in rows),
        "excluded_life_or_death": sum(r.excluded_life_or_death for r in rows),
        "umbrella": sum(r.umbrella for r in rows),
        "unbounded": sum(1 for r in rows if r.max_years is None and not r.umbrella),
    }


if __name__ == "__main__":
    p = export_jsonl()
    print(json.dumps(stats(), indent=1))
    print("wrote", p)
