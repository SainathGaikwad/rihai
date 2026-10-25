"""Validate the engine against published court orders on Section 479 BNSS.

    python scripts/court_orders_eval.py                 # table + summary
    python scripts/court_orders_eval.py --md > docs/validation.md

Each row of data/validation/court_orders.csv is a published High Court order (Indian Kanoon document id, no names)
with the facts the order states: charged sections, custody start, days not in custody, whether the court treated the
person as a first-time offender, whether other cases were pending, what the court did and on what basis. The engine
is run on those facts as on the order date and its status is compared with the court's result.

How a row is scored:
  agree            engine says eligible and the court granted (or referred to the UTRC); or engine says not yet /
                   excluded and the court refused
  engine_abstains  engine refused to decide (NEEDS_REVIEW or UNKNOWN_SECTION); nothing to compare, but it is a gap
                   in the law table worth listing
  court_liberal    engine says not eligible, court released anyway (discretion, a special rule such as the NDPS
                   five-year directions, or a life-punishable section in the FIR that the court did not treat as
                   operative)
  court_strict     engine says eligible, court refused (second proviso, merits, delay attributed to the accused)

The engine applies the statute as written. Courts also exercise discretion, so "court_liberal" is not an engine
error; "court_strict" rows are the ones to read closely.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rihai.eligibility import Status, assess_roster  # noqa: E402

DATA = ROOT / "data" / "validation" / "court_orders.csv"
ELIGIBLE = {Status.ELIGIBLE, Status.MUST_RELEASE_MAX_TERM}
NOT = {Status.NOT_YET, Status.EXCLUDED_LIFE_OR_DEATH, Status.EXCLUDED_MULTIPLE_CASES}
ABSTAIN = {Status.NEEDS_REVIEW, Status.UNKNOWN_SECTION}


def _bool(s: str, default: bool) -> bool:
    s = (s or "").strip().lower()
    if s in ("true", "yes", "1", "y"):
        return True
    if s in ("false", "no", "0", "n"):
        return False
    return default


def score(status: Status, court_result: str) -> str:
    granted = court_result in ("granted", "referred_utrc")
    if status in ABSTAIN:
        return "engine_abstains"
    if status in ELIGIBLE:
        return "agree" if granted else "court_strict"
    if status in NOT:
        return "court_liberal" if granted else "agree"
    return "other"


def run(path: Path = DATA):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    out = []
    for r in rows:
        as_of = date.fromisoformat(r["order_date"])
        first = _bool(r.get("first_time"), default=False)       # unknown -> the one-half rule (the safe assumption)
        a = assess_roster([{
            "identifier": r["id"], "charges": [c.strip() for c in r["charges"].split(";") if c.strip()],
            "custody_start": r["custody_start"], "first_time_offender": first,
            "multiple_cases_pending": _bool(r.get("multiple_cases"), default=False),
            "delay_attributable_days": int(r.get("not_in_custody_days") or 0),
        }], as_of=as_of)[0]
        out.append({**r, "engine_status": a.status.value, "engine_controlling": a.controlling.key if a.controlling else "",
                    "engine_eligible_on": a.eligible_on.isoformat() if a.eligible_on else "", "days_served": a.days_served,
                    "verdict": score(a.status, r["court_result"]), "engine_reason": a.reasons[0] if a.reasons else ""})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true", help="print a Markdown table")
    ap.add_argument("--csv", help="write the scored rows to this CSV")
    args = ap.parse_args()
    out = run()
    counts = Counter(o["verdict"] for o in out)
    n = len(out)
    if args.md:
        print(f"| Order | Court | Date | Charges | Days | Engine | Court | Verdict |")
        print("|---|---|---|---|---:|---|---|---|")
        for o in out:
            print(f"| [{o['id']}](https://indiankanoon.org/doc/{o['id']}/) | {o['court']} | {o['order_date']} | {o['charges'].replace(';', ', ')} | "
                  f"{o['days_served']} | {o['engine_status']} | {o['court_result']} ({o['court_basis']}) | {o['verdict']} |")
        print()
    else:
        for o in out:
            print(f"{o['id']:>10} {o['court'][:18]:18} {o['order_date']} {o['engine_status']:24} court={o['court_result']:13} {o['verdict']}")
    comparable = n - counts["engine_abstains"]
    print(f"\n{n} orders: agree {counts['agree']}, court_liberal {counts['court_liberal']}, court_strict {counts['court_strict']}, "
          f"engine_abstains {counts['engine_abstains']}")
    if comparable:
        print(f"agreement on comparable rows: {counts['agree']}/{comparable} = {100 * counts['agree'] / comparable:.0f}%")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader(); w.writerows(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
