# Section 479 BNSS, as encoded

The full text of the section is in the header of [`rihai/eligibility/s479.py`](../rihai/eligibility/s479.py).
This note maps each branch of the code to the words it implements, and lists the choices a reviewer should
challenge.

## Inputs

| Field | From | Statutory hook |
|---|---|---|
| charges (act, section, sub-section) | charge-sheet / roster | "an offence under any law" |
| custody_start | arrest / first remand date | "undergone detention for a period" |
| first_time_offender | prior-conviction record | first proviso: "never been convicted of any offence in the past" |
| multiple_cases_pending | roster / court records | sub-section (2) |
| delay_attributable_days | court record | Explanation: "delay in proceeding caused by the accused shall be excluded" |

## Decision order

1. **Resolve every charge in the law table.** Unknown → `UNKNOWN_SECTION`, refuse. A bare section with
   sub-sections carrying different terms → `NEEDS_REVIEW`, ask for the sub-section.
2. **Exclusion.** Any charge where death or life is "specified as one of the punishments" → `EXCLUDED_LIFE_OR_DEATH`.
   Read literally: life as *one of several* options excludes (e.g. BNS 118(2): "life, or 1 to 10 years").
3. **Conditional life** (BNS 109(1) / IPC 307: life only "if hurt is caused") → `NEEDS_REVIEW`; the FIR decides.
4. **No stated ceiling** (IPC 397/398, BNS 311/312 "not less than seven years"; attempts and abetments that defer to
   a principal offence) → `NEEDS_REVIEW`.
5. **Controlling offence** = the charge with the longest maximum term. The threshold is computed on it alone.
6. **Third proviso first.** If detention ≥ the maximum term → `MUST_RELEASE_MAX_TERM`. This applies even where
   sub-section (2) would otherwise bar release ("subject to the third proviso thereof").
7. **Sub-section (2).** If another case is pending → `EXCLUDED_MULTIPLE_CASES`, with a note to verify the other
   case is live. Several High Courts read this bar narrowly; the engine flags rather than decides.
8. **Threshold.** First-time offender: one-third of the maximum, release on *bond*. Otherwise: one-half, release on
   *bail*. Calendar arithmetic (years and months from the custody date), then add the delay days.
   `ELIGIBLE` if as-of ≥ that date, else `NOT_YET` with the date.

## Choices to challenge

- **Life as one of several punishments excludes.** The text says "specified as one of the punishments". Where the
  charged limb carries a fixed term (BNS 105 knowledge limb; IPC 304 Part II) the better view may be that the
  limb, not the section, governs. We encode the section-level reading and return the limb as a separate key where
  the charge-sheet names it (IPC 304(II)).
- **Fractions.** One-third of three years is twelve months; one-third of seven years is 28 months. We round to the
  nearest month. A court may count in days.
- **The maximum-term proviso with multiple cases.** We apply it; sub-section (2) is expressly subject to it.
- **"First-time offender."** The proviso says "never been convicted of any offence". A prior conviction for a
  petty offence counts. We take the roster's flag at face value and say so in the memo.
- **Delay attributable to the accused.** Taken from the roster as a number of days; the engine does not assess it.

## Sources

NALSA UTRC Q3 2025 report; Rajya Sabha reply of 3 April 2025 (334 released under s.479); Supreme Court orders of
23 August and 22 October 2024 in W.P.(C) 406/2013; the Act text on India Code (handle 123456789/20062 for BNS).
