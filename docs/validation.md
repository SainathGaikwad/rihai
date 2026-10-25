# Validation against published court orders

**What this is.** Rihai's rule engine run on the facts stated in published High Court orders that decided a
Section 479 BNSS (or 436A CrPC) claim, compared with what the court did. No partner data is needed for this, and no
names: each row is an Indian Kanoon document id, the charged sections, the custody date, and the result.
`python scripts/court_orders_eval.py` rebuilds the table from `data/validation/court_orders.csv`.

**Caveat first.** High Courts publish the contested cases: NDPS, economic offences, POCSO, gang rape, repeat
applications. The routine magistrate-level release that Rihai exists to speed up is almost never reported. So this
set is harder than a prison roster, and it is small (19 orders, 9 courts, 10 granted / 9 refused). It is a check on
the rule, not a measure of impact.

## Result, 25 October 2026

| | Orders |
|---|---:|
| Engine and court agree (eligible and released; or not eligible and refused) | 13 |
| Court released although the statute, read strictly, did not require it | 6 |
| Court refused although the engine found the person eligible | 0 |
| Engine abstained (unknown section or unresolved ambiguity) | 0 |

Agreement on the 19 comparable orders: 13/19. **In no case did the engine call a prisoner eligible whom a court then
refused**, which is the error that would matter in a jail. Every disagreement is in the other direction, and each has
a named reason:

- In four orders (Allahabad, Delhi) the FIR carried a life-punishable section (IPC 467, IPC 409) that the court did not
  treat as the operative offence, and granted release on the lesser section (IPC 419 or 420). The statute excludes any
  offence with life as a possible punishment, so the engine excludes too; it now adds the line *"the exclusion rests
  on IPC 409 alone; on the remaining sections the one-third threshold was reached on …"* so counsel can make exactly
  the argument those courts accepted.
- In one order (J&K) an NDPS commercial-quantity undertrial was released after five years under the Supreme Court
  Legal Aid Committee directions, which are not Section 479 arithmetic. The engine now flags that rule when an NDPS
  prisoner with a ten-year minimum passes five years in custody.
- In one order (Delhi) bail was granted on prolonged incarceration and parity after 3 years 10 months in an NDPS
  case, below both the statutory threshold and the five-year mark: judicial discretion the engine does not model.

## What the exercise changed in the engine

Before this set was run, the engine abstained on 10 of the first 12 orders. Real charge-sheets are not like a sample
roster. Three changes followed, each with tests:

1. **Derivative sections no longer stall an assessment.** IPC 120B, 34, 109, 114, 149, 511, 471 and NDPS 25, 29 carry
   no punishment of their own; they take the principal offence's. They appear on nearly every charge-sheet. The
   engine now sets them aside with a note and takes the maximum from the substantive sections; if only derivative
   sections are charged it still asks for the principal offence.
2. **Ambiguity that cannot change the answer is noted, not blocking.** A bare "IPC 505" (3 or 5 years) next to IPC 354B
   (7 years) cannot move the threshold, so the assessment proceeds with a note. A bare section whose variants include
   life, death or a higher ceiling than anything resolved still goes to a human.
3. **Law-table gaps found and filled**: CGST Act s.132 (five clauses), IPC 274 to 276, IPC 505 (three sub-sections),
   the POCSO definitional sections 3, 5, 7, 9, 11 that charge-sheets cite alongside the punishing sections, and the
   clause-level SC/ST Act s.3(1) entries. The table has 783 rows, all still flagged unverified until a law student
   checks them against India Code.

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


19 orders: agree 13, court_liberal 6, court_strict 0, engine_abstains 0
agreement on comparable rows: 13/19 = 68%

*Encoding rules.* Custody start is the arrest date the order states; where the order gives only a period ("more than
one year") the start is approximated and the notes say so. "First-time" follows the court's own treatment, and is
taken as not first-time when the order is silent, which is the conservative reading. Days spent on interim bail are
entered as days not in custody. Convicts seeking suspension of sentence were excluded; Section 479 is for undertrials.
