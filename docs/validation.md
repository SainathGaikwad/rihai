# Validation against published court orders

**What this is.** Rihai's rule engine run on the facts stated in published court orders that decided a Section 479
BNSS (or 436A CrPC) claim, compared with what the court did. No partner data is needed for this, and no names: each
row is an Indian Kanoon document id, the charged sections, the custody date, and the result.
`python scripts/court_orders_eval.py` rebuilds the table from `data/validation/court_orders.csv`.

**Caveat first.** Courts publish the contested cases: NDPS, money-laundering, POCSO, gang rape, repeat applications,
politicians. The routine magistrate-level release that Rihai exists to speed up is almost never reported. So this set
is harder than a prison roster, and it is small (34 orders from 14 courts including the Supreme Court; 19 granted or
referred, 15 refused). Orders of convicts seeking suspension of sentence pending appeal were read and left out: Section
479 is about undertrials. It is a check on the rule, not a measure of impact.

## Result, 25 October 2026

| | Orders |
|---|---:|
| Engine and court agree (eligible and released; or not eligible and refused) | 19 |
| Court released although the statute, read strictly, did not require it | 14 |
| Court refused although the engine found the person eligible | 0 |
| Engine abstained (sub-section not stated in the order) | 1 |

Agreement on the 33 comparable orders: 19/33. **In no case did the engine call a prisoner eligible whom a court then
refused**, which is the error that would matter in a jail. Every disagreement is in the other direction, and each has
a named reason:

- **A life-punishable section in the FIR that the court did not treat as operative** (four orders: Allahabad, Delhi;
  IPC 467 or 409 beside 419 or 420). The statute excludes any offence with life as a possible punishment, so the
  engine excludes too; it adds the line *"the exclusion rests on IPC 409 alone; on the remaining sections the
  one-third threshold was reached on ..."* so counsel can make exactly the argument those courts accepted.
- **Article 21, not Section 479** (seven orders, four of them money-laundering: Supreme Court three times, Delhi twice,
  Calcutta, and Punjab and Haryana). The court said in terms that the threshold was not met, or
  that the offence was excluded, or that the question was left open, and released on prolonged incarceration. In the
  Calcutta order the court's own arithmetic ("short of about four months" of one-third of seven years) is the engine's
  (eligible from 2025-02-10). Discretion the engine does not model, and says so.
- **Section 479(2) read narrowly** (two orders: Delhi, Karnataka). Other cases were pending; the courts held that the
  bar on release where multiple cases are pending does not shut out the first proviso, or is not absolute, following
  the Supreme Court's order in *Badshah Majid Malik v. Directorate of Enforcement* (18.10.2024). The engine applies the
  sub-section as written and now adds, whenever the threshold itself has been reached, the flag
  `MULTIPLE_CASES_THRESHOLD_MET` with those citations: a point for counsel, not for the engine.
- **The NDPS five-year directions** (one order, J&K): released after five years under *Supreme Court Legal Aid
  Committee*, which is not Section 479 arithmetic. The engine flags that rule when an NDPS prisoner with a ten-year
  minimum passes five years.

The one abstention is a Patna order charging Arms Act s.26 without the sub-section (7 or 10 years); the engine asks
for it rather than guess, and the court refused under s.479(2) anyway.

## What the exercise changed in the engine

Before this set was run, the engine abstained on 10 of the first 12 orders. Real charge-sheets are not like a sample
roster. The changes, each with tests:

1. **Derivative sections no longer stall an assessment.** IPC 120B, 34, 109, 114, 149, 511, 471, NDPS 8, 25, 28, 29 and
   Arms Act 35 carry no punishment of their own; they take the principal offence's. They appear on nearly every
   charge-sheet. The engine sets them aside with a note and takes the maximum from the substantive sections; if only
   derivative sections are charged it still asks for the principal offence.
2. **Ambiguity that cannot change the answer is noted, not blocking.** A bare "IPC 505" (3 or 5 years) next to IPC 354B
   (7 years) cannot move the threshold, so the assessment proceeds with a note. A bare section whose variants include
   life, death or a higher ceiling than anything resolved still goes to a human.
3. **Law-table gaps found and filled**: CGST Act s.132 (five clauses), IPC 274 to 276, 440, IPC 505 (three
   sub-sections), PMLA s.3 beside s.4, NDPS s.23 (three quantity classes), Arms Act s.26 (three sub-sections), PC Act
   s.13(2) and the pre-2018 s.13(1)(d), the POCSO definitional sections 3, 5, 7, 9, 11 that charge-sheets cite
   alongside the punishing sections, and the clause-level SC/ST Act s.3(1) entries. The table has 800 rows, all still
   flagged unverified until a law student checks them against India Code.
4. **The s.479(2) flag** described above, and a fix to the review message that lists an umbrella section's variants
   with their maxima (it previously printed "no ceiling" for every variant).

## The orders

| Order | Court | Date | Charges | Days | Engine | Court | Verdict |
|---|---|---|---|---:|---|---|---|
| [105787768](https://indiankanoon.org/doc/105787768/) | Allahabad HC | 2025-09-01 | IPC/120B, IPC/419, IPC/417, IPC/467, IPC/468, IPC/471 | None | EXCLUDED_LIFE_OR_DEATH | granted (s479_threshold_met) | court_liberal |
| [141200891](https://indiankanoon.org/doc/141200891/) | Delhi HC | 2025-09-25 | IPC/274, IPC/275, IPC/276, IPC/420, IPC/468, IPC/471, IPC/120B | 1049 | EXCLUDED_MULTIPLE_CASES | refused (discretion_merits) | agree |
| [143084077](https://indiankanoon.org/doc/143084077/) | Punjab-Haryana HC | 2025-03-05 | CGST/132(1)(i) | 1512 | ELIGIBLE | granted (s479_threshold_met) | agree |
| [90387710](https://indiankanoon.org/doc/90387710/) | Bombay HC | 2025-03-20 | IPC/354A, IPC/354B, POCSO/8, POCSO/10, POCSO/12 | 731 | NOT_YET | refused (s479_not_met) | agree |
| [117497953](https://indiankanoon.org/doc/117497953/) | J&K HC | 2025-10-07 | NDPS/15(commercial), NDPS/29 | 1832 | NOT_YET | granted (other_rule_ndps_5y) | court_liberal |
| [73871200](https://indiankanoon.org/doc/73871200/) | Bombay HC | 2025-03-17 | IPC/376D | None | EXCLUDED_LIFE_OR_DEATH | refused (life_or_death_excluded) | agree |
| [40078885](https://indiankanoon.org/doc/40078885/) | Delhi HC | 2026-04-13 | IPC/406, IPC/409, IPC/420, IPC/120B, IPC/506 | None | EXCLUDED_LIFE_OR_DEATH | granted (s479_threshold_met) | court_liberal |
| [42344785](https://indiankanoon.org/doc/42344785/) | Allahabad HC | 2025-10-14 | IPC/306, IPC/120B | 1483 | ELIGIBLE | referred_utrc (s479_threshold_met) | agree |
| [83299005](https://indiankanoon.org/doc/83299005/) | Rajasthan HC | 2026-10-07 | NDPS/15(commercial), NDPS/29 | 1138 | NOT_YET | refused (s479_not_met) | agree |
| [16124318](https://indiankanoon.org/doc/16124318/) | Delhi HC | 2026-04-30 | IPC/420, IPC/406, IPC/120B | 1650 | ELIGIBLE | granted (s479_threshold_met) | agree |
| [195821603](https://indiankanoon.org/doc/195821603/) | Tripura HC | 2026-04-28 | IPC/153A, IPC/354A, IPC/354B, IPC/504, IPC/505, IPC/509, IT/67 | 921 | NOT_YET | refused (s479_not_met) | agree |
| [58695558](https://indiankanoon.org/doc/58695558/) | Gauhati HC | 2025-01-08 | NDPS/21(commercial), NDPS/29 | 819 | NOT_YET | refused (s479_not_met) | agree |
| [130280712](https://indiankanoon.org/doc/130280712/) | Allahabad HC | 2025-08-05 | IPC/419, IPC/420, IPC/467, IPC/468, IPC/471, IPC/120B | None | EXCLUDED_LIFE_OR_DEATH | granted (s479_threshold_met) | court_liberal |
| [140418341](https://indiankanoon.org/doc/140418341/) | Allahabad HC | 2025-08-05 | IPC/419, IPC/420, IPC/467, IPC/468, IPC/471, IPC/120B | None | EXCLUDED_LIFE_OR_DEATH | granted (s479_threshold_met) | court_liberal |
| [99829746](https://indiankanoon.org/doc/99829746/) | Delhi HC | 2024-09-18 | IPC/302, IPC/307, IPC/201, IPC/34 | None | EXCLUDED_LIFE_OR_DEATH | refused (life_or_death_excluded) | agree |
| [96382206](https://indiankanoon.org/doc/96382206/) | Delhi HC | 2025-08-04 | IPC/354, IPC/354A, POCSO/8, POCSO/10 | 861 | ELIGIBLE | granted (s479_threshold_met) | agree |
| [102736763](https://indiankanoon.org/doc/102736763/) | Madhya Pradesh HC | 2024-08-28 | IPC/420 | 855 | EXCLUDED_MULTIPLE_CASES | refused (multiple_cases) | agree |
| [152999267](https://indiankanoon.org/doc/152999267/) | Gauhati HC | 2024-11-28 | NDPS/21(commercial), NDPS/29 | 764 | NOT_YET | refused (s479_not_met) | agree |
| [108004126](https://indiankanoon.org/doc/108004126/) | Delhi HC | 2024-10-21 | NDPS/20(commercial), NDPS/25, NDPS/29 | 1406 | NOT_YET | granted (discretion_merits) | court_liberal |
| [163970760](https://indiankanoon.org/doc/163970760/) | Delhi HC | 2026-05-05 | PMLA/3, PMLA/4 | 1669 | EXCLUDED_MULTIPLE_CASES | granted (s479_threshold_met) | court_liberal |
| [126233110](https://indiankanoon.org/doc/126233110/) | Bombay HC | 2026-05-06 | IPC/420, IPC/406, IPC/34 | 1038 | ELIGIBLE | granted (s479_threshold_met) | agree |
| [9029756](https://indiankanoon.org/doc/9029756/) | Supreme Court | 2026-08-17 | NDPS/21(commercial), NDPS/23(commercial), NDPS/27A, NDPS/28, NDPS/29, NDPS/31A | None | EXCLUDED_LIFE_OR_DEATH | refused (life_or_death_excluded) | agree |
| [91259213](https://indiankanoon.org/doc/91259213/) | Supreme Court | 2025-12-11 | IPC/120B, IPC/302, IPC/307, IPC/323, IPC/325, IPC/326, IPC/440, IPC/212, UAPA/16, UAPA/18 | None | EXCLUDED_LIFE_OR_DEATH | granted (discretion_merits) | court_liberal |
| [72611293](https://indiankanoon.org/doc/72611293/) | Supreme Court | 2024-12-13 | PMLA/4 | 874 | EXCLUDED_MULTIPLE_CASES | granted (discretion_merits) | court_liberal |
| [171801252](https://indiankanoon.org/doc/171801252/) | Calcutta HC | 2024-09-12 | PMLA/3, PMLA/4 | 703 | NOT_YET | granted (discretion_merits) | court_liberal |
| [51123243](https://indiankanoon.org/doc/51123243/) | Gauhati HC | 2024-11-20 | NDPS/8(c), NDPS/20(commercial), NDPS/21(commercial), NDPS/22(commercial), NDPS/29 | 702 | NOT_YET | refused (s479_not_met) | agree |
| [136313040](https://indiankanoon.org/doc/136313040/) | Supreme Court | 2025-12-11 | IPC/120B, IPC/409, IPC/420, IPC/477A, PCA/13(2), PCA/13(1)(d) | None | EXCLUDED_LIFE_OR_DEATH | granted (discretion_merits) | court_liberal |
| [79474792](https://indiankanoon.org/doc/79474792/) | Delhi HC | 2025-07-04 | IPC/306 | 1394 | NOT_YET | refused (discretion_merits) | agree |
| [55143398](https://indiankanoon.org/doc/55143398/) | Karnataka HC | 2025-07-17 | PMLA/3, PMLA/4 | 877 | EXCLUDED_MULTIPLE_CASES | granted (s479_threshold_met) | court_liberal |
| [46297435](https://indiankanoon.org/doc/46297435/) | Patna HC | 2025-06-27 | ARMS/25(1B), ARMS/26, ARMS/35 | None | NEEDS_REVIEW | refused (multiple_cases) | engine_abstains |
| [17700124](https://indiankanoon.org/doc/17700124/) | Jharkhand HC | 2024-12-06 | PMLA/3, PMLA/4 | 1070 | EXCLUDED_MULTIPLE_CASES | refused (multiple_cases) | agree |
| [106948597](https://indiankanoon.org/doc/106948597/) | Delhi HC | 2024-11-20 | PMLA/3, PMLA/4 | 882 | NOT_YET | granted (discretion_merits) | court_liberal |
| [121190325](https://indiankanoon.org/doc/121190325/) | Punjab-Haryana HC | 2026-08-14 | PMLA/3, PMLA/4 | 388 | NOT_YET | granted (discretion_merits) | court_liberal |
| [82059282](https://indiankanoon.org/doc/82059282/) | Rajasthan HC | 2026-10-06 | NDPS/8, NDPS/15(commercial) | 936 | NOT_YET | refused (s479_not_met) | agree |


34 orders: agree 19, court_liberal 14, court_strict 0, engine_abstains 1
agreement on comparable rows: 19/33 = 58%
