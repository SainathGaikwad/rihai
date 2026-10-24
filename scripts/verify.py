#!/usr/bin/env python3
"""Record that a law-table row has been checked against the official text.

A law student opens the section on India Code (or the bare Act), confirms the maximum term and whether death/life
is a specified punishment, and runs:

    python scripts/verify.py BNS 303(2) --max-years 3 --by "A. Student, ILS legal aid clinic" \
        --url "https://www.indiacode.nic.in/show-data?...&sectionno=303"

    python scripts/verify.py IPC 326 --max-years 10 --life --by "..." --url "..."
    python scripts/verify.py NDPS "20(small)" --max-years 1 --by "..." --url "..."

Each call appends one line to data/law/verified.jsonl. The table loader applies it on top of the encoded value and
flips `verified` to true, so the engine stops reporting that row as unverified. Disagreements with the encoded value
are printed loudly; the verified value wins.

    python scripts/verify.py --status        # how many rows are verified, and which common ones are not
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rihai.law import UnknownSection, all_rows, lookup  # noqa: E402

OUT = ROOT / "data" / "law" / "verified.jsonl"

# The sections that fill rosters; verify these first.
PRIORITY = [
    ("BNS", "303(2)"), ("BNS", "304(2)"), ("BNS", "305"), ("BNS", "115(2)"), ("BNS", "117(2)"), ("BNS", "118(1)"), ("BNS", "118(2)"),
    ("BNS", "109(1)"), ("BNS", "318(2)"), ("BNS", "318(4)"), ("BNS", "316(2)"), ("BNS", "317(2)"), ("BNS", "309(4)"), ("BNS", "310(2)"),
    ("BNS", "351(2)"), ("BNS", "351(3)"), ("BNS", "191(2)"), ("BNS", "191(3)"), ("BNS", "189(2)"), ("BNS", "74"), ("BNS", "85"),
    ("BNS", "137(2)"), ("BNS", "331(3)"), ("BNS", "336(3)"), ("BNS", "106(1)"), ("BNS", "103(1)"), ("BNS", "64(1)"),
    ("IPC", "379"), ("IPC", "380"), ("IPC", "323"), ("IPC", "324"), ("IPC", "325"), ("IPC", "326"), ("IPC", "307"), ("IPC", "302"),
    ("IPC", "420"), ("IPC", "406"), ("IPC", "411"), ("IPC", "392"), ("IPC", "395"), ("IPC", "457"), ("IPC", "498A"), ("IPC", "506"),
    ("IPC", "354"), ("IPC", "363"), ("IPC", "376"), ("IPC", "147"), ("IPC", "148"), ("IPC", "468"), ("IPC", "471"),
    ("NDPS", "20(small)"), ("NDPS", "20(intermediate)"), ("NDPS", "20(commercial)"), ("NDPS", "22(small)"), ("NDPS", "22(commercial)"),
    ("ARMS", "25(1B)"), ("POCSO", "8"), ("POCSO", "10"), ("MPA", "65"),
]


def status() -> None:
    rows = all_rows()
    n = len(rows)
    v = sum(r.verified for r in rows.values())
    print(f"{v} of {n} rows verified ({100 * v / n:.1f}%)")
    todo = [f"{a}/{s}" for a, s in PRIORITY if not rows.get(f"{a}/{s}", None) or not rows[f"{a}/{s}"].verified]
    print(f"priority rows still unverified: {len(todo)} of {len(PRIORITY)}")
    for k in todo:
        r = rows.get(k)
        enc = "(not in table!)" if r is None else f"encoded max={r.max_years} life={r.life} death={r.death}"
        print(f"  {k:22s} {enc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("act", nargs="?")
    ap.add_argument("section", nargs="?")
    ap.add_argument("--max-years", type=float, help="maximum term in years as the statute states it (0 for fine-only)")
    ap.add_argument("--min-years", type=float, default=None)
    ap.add_argument("--life", action="store_true", help="life imprisonment is one of the specified punishments")
    ap.add_argument("--death", action="store_true", help="death is one of the specified punishments")
    ap.add_argument("--life-if", default=None, help="condition under which life becomes available")
    ap.add_argument("--by", required=False, help="reviewer name and affiliation")
    ap.add_argument("--url", required=False, help="India Code (or other official) URL of the section text")
    ap.add_argument("--note", default="")
    ap.add_argument("--status", action="store_true", help="print verification coverage and exit")
    ap.add_argument("--list", action="store_true", help="list priority sections from the law table and exit")
    args = ap.parse_args()

    if args.list:
        for a, s in PRIORITY:
            try:
                r = lookup(a, s)
                print(f"{r.act} {r.section} {r.title} {r.max_years} {r.life} {r.death}")
            except UnknownSection:
                print(f"{a} {s} UNKNOWN")
        return 0

    if args.status or not args.act:
        status()
        return 0
    if args.max_years is None or not args.by or not args.url:
        ap.error("--max-years, --by and --url are required to record a verification")

    try:
        r = lookup(args.act, args.section)
    except UnknownSection as e:
        print(f"refusing: {e}. Add the row to the punishments file first, then verify it.")
        return 2
    if r.umbrella:
        print(f"refusing: {r.key} is an umbrella; verify its sub-sections: {', '.join(r.variants)}")
        return 2

    rec = {
        "act": r.act, "section": r.section, "max_years": args.max_years, "life": bool(args.life), "death": bool(args.death),
        "source_url": args.url, "verified_by": args.by, "verified_on": date.today().isoformat(),
    }
    if args.min_years is not None:
        rec["min_years"] = args.min_years
    if args.life_if:
        rec["life_if"] = args.life_if
    if args.note:
        rec["notes"] = (r.notes + " | " if r.notes else "") + f"verified: {args.note}"

    diffs = []
    if r.max_years != args.max_years:
        diffs.append(f"max_years encoded {r.max_years} -> verified {args.max_years}")
    if r.life != bool(args.life):
        diffs.append(f"life encoded {r.life} -> verified {bool(args.life)}")
    if r.death != bool(args.death):
        diffs.append(f"death encoded {r.death} -> verified {bool(args.death)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"recorded {r.key} as verified by {args.by}")
    if diffs:
        print("DISAGREEMENT with the encoded value (the verified value now wins):")
        for d in diffs:
            print("  " + d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
