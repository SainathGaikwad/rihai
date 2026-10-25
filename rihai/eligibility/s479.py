"""Section 479, Bharatiya Nagarik Suraksha Sanhita, 2023 - the rule, encoded.

    479. Maximum period for which undertrial prisoner can be detained.
    (1) Where a person has, during the period of investigation, inquiry or trial under this Sanhita of an offence
        under any law (not being an offence for which the punishment of death or life imprisonment has been
        specified as one of the punishments under that law) undergone detention for a period extending up to
        one-half of the maximum period of imprisonment specified for that offence under that law, he shall be
        released by the Court on bail:
        Provided that where such person is a first-time offender (who has never been convicted of any offence in
        the past) he shall be released on bond by the Court, if he has undergone detention for the period extending
        up to one-third of the maximum period of imprisonment specified for such offence under that law:
        Provided further that the Court may, after hearing the Public Prosecutor and for reasons to be recorded by
        it in writing, order the continued detention of such person for a period longer than one-half of the said
        period or release him on bail bond instead of his bond:
        Provided also that no such person shall in any case be detained during the period of investigation, inquiry
        or trial for more than the maximum period of imprisonment provided for the said offence under that law.
        Explanation. - In computing the period of detention under this section for granting bail, the period of
        detention passed due to delay in proceeding caused by the accused shall be excluded.
    (2) Notwithstanding anything in sub-section (1), and subject to the third proviso thereof, where an
        investigation, inquiry or trial in more than one offence or in multiple cases are pending against a person,
        he shall not be released on bail by the Court.
    (3) The Superintendent of jail, where the accused person is detained, on completion of one-half or one-third of
        the period mentioned in sub-section (1), as the case may be, shall forthwith make an application in writing
        to the Court to proceed under sub-section (1) for the release of such person on bail.

Everything below is a direct encoding of that text. Where the text leaves room for argument (the "more than one
offence" bar in (2); the half-of-life reading of attempts; sections with no stated ceiling) the engine returns
NEEDS_REVIEW with the reason, instead of deciding.

The Supreme Court in *In Re: Inhuman Conditions in 1382 Prisons* (W.P.(C) 406/2013, orders of 23 Aug and 22 Oct
2024) directed that s.479 applies to all undertrials regardless of when the case was registered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Optional

from ..law import Row, UnknownSection, lookup

try:
    from dateutil.relativedelta import relativedelta
except ImportError:  # pragma: no cover - dateutil is in requirements, but keep the engine importable
    relativedelta = None


class Status(str, Enum):
    ELIGIBLE = "ELIGIBLE"                              # threshold met: s.479(1) release on bail / on bond
    MUST_RELEASE_MAX_TERM = "MUST_RELEASE_MAX_TERM"    # third proviso: detained >= maximum term, no discretion
    NOT_YET = "NOT_YET"                                # threshold not yet met; eligible_on tells when
    EXCLUDED_LIFE_OR_DEATH = "EXCLUDED_LIFE_OR_DEATH"  # an offence carries death or life as a specified punishment
    EXCLUDED_MULTIPLE_CASES = "EXCLUDED_MULTIPLE_CASES"  # s.479(2)
    NEEDS_REVIEW = "NEEDS_REVIEW"                      # the law table cannot settle it without a human
    UNKNOWN_SECTION = "UNKNOWN_SECTION"                # a charge is not in the law table: refuse


@dataclass
class Charge:
    act: str
    section: str

    def __str__(self) -> str:
        return f"{self.act} s.{self.section}"


@dataclass
class Prisoner:
    charges: list[Charge]
    custody_start: date                    # date of arrest / first remand - detention counts from here
    first_time_offender: bool              # "never been convicted of any offence in the past"
    multiple_cases_pending: bool = False   # s.479(2): investigation/inquiry/trial in more than one case pending
    delay_attributable_days: int = 0       # Explanation: delay caused by the accused, excluded from the count
    identifier: str = ""                   # roster id / UTP number - never a name in logs


@dataclass
class Assessment:
    status: Status
    as_of: date
    prisoner: Prisoner
    controlling: Optional[Row] = None          # the charge with the longest maximum term
    rows: list[Row] = field(default_factory=list)
    max_term_years: Optional[float] = None
    fraction: Optional[float] = None           # 1/3 or 1/2
    threshold_days: Optional[int] = None
    days_served: Optional[int] = None          # custody days minus delay attributable to the accused
    eligible_on: Optional[date] = None         # date the threshold is / was crossed
    max_term_end: Optional[date] = None        # third proviso date
    release_mode: Optional[str] = None         # "bond" (first-time) or "bail"
    reasons: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)   # rows used that nobody has checked against India Code yet
    flags: list[str] = field(default_factory=list)        # machine-readable hints: EXCLUSION_HINGES_ON:<key>, NDPS_FIVE_YEAR_RULE

    @property
    def eligible(self) -> bool:
        return self.status in (Status.ELIGIBLE, Status.MUST_RELEASE_MAX_TERM)

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "as_of": self.as_of.isoformat(),
            "identifier": self.prisoner.identifier,
            "charges": [str(c) for c in self.prisoner.charges],
            "controlling": self.controlling.key if self.controlling else None,
            "max_term_years": self.max_term_years,
            "fraction": self.fraction,
            "threshold_days": self.threshold_days,
            "days_served": self.days_served,
            "eligible_on": self.eligible_on.isoformat() if self.eligible_on else None,
            "max_term_end": self.max_term_end.isoformat() if self.max_term_end else None,
            "release_mode": self.release_mode,
            "first_time_offender": self.prisoner.first_time_offender,
            "reasons": self.reasons,
            "unverified": self.unverified,
            "flags": self.flags,
        }


def _variants_with_maxima(r) -> str:
    """'303(2) 3y, 303(3) 7y' so a reviewer sees the thresholds at stake without a second lookup."""
    out = []
    for v in r.variants:
        try:
            row = lookup(r.act, v)
        except UnknownSection:
            out.append(v)
            continue
        if row.death or row.life:
            out.append(f"{v} life/death")
        elif row.max_years is None:
            out.append(f"{v} no ceiling")
        else:
            out.append(f"{v} {row.max_years:g}y")
    return ", ".join(out)


def _add_years(d: date, years: float) -> date:
    """Calendar arithmetic the way courts count sentences: whole years then months, not 365.25-day floats."""
    whole = int(years)
    months = int(round((years - whole) * 12))
    if relativedelta is not None:
        return d + relativedelta(years=whole, months=months)
    # fallback without dateutil: approximate
    return d + timedelta(days=int(round(years * 365.25)))


# Sections that carry no punishment of their own: they borrow the principal offence's. On a charge-sheet they ride
# alongside the substantive section (IPC 379 r/w 34; NDPS 21(c)/29), so they never raise the maximum and must not stall
# the assessment. If every charge is derivative there is nothing to borrow from -> NEEDS_REVIEW.
#   IPC 34 / BNS 3(5)   common intention            IPC 149 / BNS 190   unlawful assembly, constructive liability
#   IPC 109, 114 / BNS 49, 54  abetment             IPC 120B, 120B(1) / BNS 61(2), 61(2)(a)  conspiracy to a 2y+ offence
#   IPC 511 / BNS 62    attempt (half the term)     IPC 471 / BNS 340(2) using a forged document (as the forgery charged)
#   NDPS 25 (allowing premises) and 29 (abetment/conspiracy): "punishable with the punishment provided for the offence"
DERIVATIVE = {
    ("IPC", "34"), ("IPC", "109"), ("IPC", "114"), ("IPC", "149"), ("IPC", "120B"), ("IPC", "120B(1)"), ("IPC", "511"), ("IPC", "471"),
    ("BNS", "3(5)"), ("BNS", "49"), ("BNS", "54"), ("BNS", "190"), ("BNS", "61(2)"), ("BNS", "61(2)(a)"), ("BNS", "62"), ("BNS", "340(2)"),
    ("NDPS", "25"), ("NDPS", "29"),
}


def _is_derivative(c: Charge) -> bool:
    from ..law.table import ACT_ALIASES
    act = ACT_ALIASES.get(c.act.strip().upper(), c.act.strip().upper())
    return (act, c.section.strip().upper().replace(" ", "")) in DERIVATIVE


def assess(p: Prisoner, as_of: Optional[date] = None) -> Assessment:
    as_of = as_of or date.today()
    a = Assessment(status=Status.NEEDS_REVIEW, as_of=as_of, prisoner=p)

    if not p.charges:
        a.reasons.append("no charges given")
        return a

    # 0. Set aside the derivative sections (34, 120B, 511, NDPS 29 ...): they take the principal offence's punishment.
    principal = [c for c in p.charges if not _is_derivative(c)]
    derivative = [c for c in p.charges if _is_derivative(c)]
    if derivative and not principal:
        a.reasons.append(f"{', '.join(str(c) for c in derivative)}: punished as the principal offence, and no principal offence is charged; specify it.")
        return a
    if derivative:
        a.reasons.append(f"{', '.join(str(c) for c in derivative)}: punished as the principal offence; the maximum is taken from the substantive sections.")

    # 1. Resolve every charge. Unknown -> refuse. Umbrella (bare section with differing sub-sections) -> see step 1b.
    rows: list[Row] = []
    umbrellas: list[Row] = []
    for c in principal:
        try:
            r = lookup(c.act, c.section)
        except UnknownSection as e:
            a.status = Status.UNKNOWN_SECTION
            a.reasons.append(str(e))
            return a
        if r.umbrella:
            umbrellas.append(r)
            continue
        rows.append(r)
        if not r.verified:
            a.unverified.append(r.key)

    # 1b. An ambiguous bare section stalls the assessment only if the answer could depend on it: if every variant's
    #     ceiling is at or below the ceiling of a section that is already resolved, the ambiguity cannot change the
    #     threshold and is noted instead. A variant carrying life or death, or no ceiling, always needs a human.
    settled_max = max((r.max_years for r in rows if r.max_years is not None), default=None)
    settled_excluded = any(r.excluded_life_or_death for r in rows)
    for u in umbrellas:
        variants = []
        for v in u.variants:
            try:
                variants.append(lookup(u.act, v))
            except UnknownSection:
                variants = []
                break
        harmless = (bool(variants) and not settled_excluded and settled_max is not None
                    and all(not vr.excluded_life_or_death and not vr.life_if and vr.max_years is not None and vr.max_years <= settled_max
                            for vr in variants))
        if harmless:
            a.reasons.append(f"{u.key}: sub-section not specified ({_variants_with_maxima(u)}); it cannot exceed the controlling maximum, so it does not change the threshold.")
            continue
        a.status = Status.NEEDS_REVIEW
        a.reasons.append(f"{u.key}: specify the sub-section; variants {_variants_with_maxima(u)}. {u.notes}".strip())
        return a
    if not rows:
        a.reasons.append("no substantive section could be resolved")
        return a
    a.rows = rows

    # 2. Statutory exclusion: any offence with death or life as a specified punishment.
    excluded_rows = [r for r in rows if r.excluded_life_or_death]
    if excluded_rows:
        a.status = Status.EXCLUDED_LIFE_OR_DEATH
        for r in excluded_rows:
            a.reasons.append(f"{r.key} ({r.title or 'untitled'}): {'death' if r.death else 'life imprisonment'} is a specified punishment; s.479 does not apply. {r.notes}".strip())
        # Courts regularly treat a graver section in the FIR as not made out at the charge stage (IPC 409 alongside
        # 420, 467 alongside 468). Say what the position would be on the remaining sections so counsel can argue it.
        remaining = [r for r in rows if not r.excluded_life_or_death and not r.life_if and r.max_years]
        if remaining:
            alt = max(remaining, key=lambda r: r.max_years)
            frac = 1 / 3 if p.first_time_offender else 1 / 2
            alt_on = _add_years(p.custody_start, alt.max_years * frac) + timedelta(days=max(0, p.delay_attributable_days))
            a.flags.append("EXCLUSION_HINGES_ON:" + ",".join(r.key for r in excluded_rows))
            a.reasons.append(
                f"The exclusion rests on {', '.join(r.key for r in excluded_rows)} alone. If that section is not pressed at the charge stage, "
                f"the controlling section is {alt.key} ({alt.max_years:g} years) and the {'one-third' if p.first_time_offender else 'one-half'} "
                f"threshold {'was' if as_of >= alt_on else 'is'} reached on {alt_on.isoformat()}."
            )
        return a

    # 3. Conditional life (e.g. attempt to murder if hurt caused) -> a human must look at the FIR.
    for r in rows:
        if r.life_if:
            a.status = Status.NEEDS_REVIEW
            a.reasons.append(f"{r.key}: life imprisonment becomes available {r.life_if}; check the FIR/charge-sheet. {r.notes}".strip())
            return a

    # 4. Sections with no stated ceiling, or that defer to a principal offence.
    for r in rows:
        if r.max_years is None:
            a.status = Status.NEEDS_REVIEW
            a.reasons.append(f"{r.key}: no fixed maximum in the table ({r.notes}); resolve against the principal offence or the statute text.")
            return a

    # 5. s.479(2): multiple cases pending -> not to be released under (1). Flagged, not silently applied, because
    #    the bar is read narrowly by several High Courts; the third proviso still applies regardless.
    controlling = max(rows, key=lambda r: r.max_years)
    a.controlling = controlling
    a.max_term_years = controlling.max_years

    if controlling.max_years == 0:
        a.status = Status.NEEDS_REVIEW
        a.reasons.append(f"{controlling.key}: punishable with fine only / no imprisonment term; continued detention needs review on other grounds.")
        return a

    a.fraction = 1 / 3 if p.first_time_offender else 1 / 2
    a.release_mode = "bond" if p.first_time_offender else "bail"

    threshold_date = _add_years(p.custody_start, controlling.max_years * a.fraction)
    max_term_end = _add_years(p.custody_start, controlling.max_years)
    delay = timedelta(days=max(0, p.delay_attributable_days))
    a.eligible_on = threshold_date + delay
    a.max_term_end = max_term_end + delay
    a.threshold_days = (a.eligible_on - p.custody_start).days
    a.days_served = (as_of - p.custody_start).days - max(0, p.delay_attributable_days)

    # 6. Third proviso: never beyond the maximum term - absolute, applies even with multiple cases (s.479(2) is
    #    "subject to the third proviso").
    if as_of >= a.max_term_end:
        a.status = Status.MUST_RELEASE_MAX_TERM
        a.reasons.append(f"detained since {p.custody_start.isoformat()}: {a.days_served} days served, which is the full maximum term of {controlling.max_years:g} years for {controlling.key}; third proviso to s.479(1) - no discretion to continue detention.")
        return a

    if p.multiple_cases_pending:
        a.status = Status.EXCLUDED_MULTIPLE_CASES
        a.reasons.append("s.479(2): investigation, inquiry or trial in more than one case is pending; not to be released under s.479(1). The third proviso (maximum-term cap) still applies. Verify the other case(s) are live and not disposed.")
        return a

    if as_of >= a.eligible_on:
        a.status = Status.ELIGIBLE
        a.reasons.append(
            f"{controlling.key} ({controlling.title or 'untitled'}) carries a maximum of {controlling.max_years:g} years; "
            f"{'first-time offender, one-third' if p.first_time_offender else 'one-half'} = eligible from {a.eligible_on.isoformat()}; "
            f"detained since {p.custody_start.isoformat()} ({a.days_served} days served). Release on {a.release_mode} under s.479(1)."
        )
    else:
        a.status = Status.NOT_YET
        a.reasons.append(f"threshold for {controlling.key} ({controlling.max_years:g} years x {'1/3' if p.first_time_offender else '1/2'}) is reached on {a.eligible_on.isoformat()}; {(a.eligible_on - as_of).days} days to go.")
        # Supreme Court Legal Aid Committee v. Union of India (1994) 6 SCC 731, reaffirmed in Satender Kumar Antil (2022):
        # an undertrial charged with an NDPS offence carrying a minimum of ten years who has been in custody for five
        # years may be released on bail (with a Rs 1 lakh bond), s.37 notwithstanding. Not s.479, but the same list.
        if any(r.act == "NDPS" and (r.min_years or 0) >= 10 for r in rows) and a.days_served is not None and a.days_served >= 5 * 365:
            a.flags.append("NDPS_FIVE_YEAR_RULE")
            a.reasons.append(
                f"NDPS commercial quantity, {a.days_served} days in custody: the five-year directions in Supreme Court Legal Aid "
                f"Committee v. Union of India (1994) 6 SCC 731, reaffirmed in Satender Kumar Antil (2022), may apply; refer to counsel."
            )

    if a.unverified:
        a.reasons.append(f"law-table rows not yet verified against India Code: {', '.join(a.unverified)}. A reviewer must confirm the maximum term before filing.")
    return a


def assess_roster(rows: list[dict], as_of: Optional[date] = None) -> list[Assessment]:
    """rows: dicts with keys identifier, charges (list of 'ACT s.SEC' or 'ACT/SEC'), custody_start (ISO),
    first_time_offender (bool), multiple_cases_pending (bool), delay_attributable_days (int)."""
    out = []
    for r in rows:
        charges = []
        for c in r.get("charges", []):
            if isinstance(c, dict):
                charges.append(Charge(c["act"], str(c["section"])))
            else:
                act, sec = _split_charge(str(c))
                charges.append(Charge(act, sec))
        p = Prisoner(
            charges=charges,
            custody_start=date.fromisoformat(str(r["custody_start"])[:10]),
            first_time_offender=bool(r.get("first_time_offender", False)),
            multiple_cases_pending=bool(r.get("multiple_cases_pending", False)),
            delay_attributable_days=int(r.get("delay_attributable_days", 0) or 0),
            identifier=str(r.get("identifier", "")),
        )
        out.append(assess(p, as_of))
    return out


def _split_charge(s: str) -> tuple[str, str]:
    s = s.strip()
    if "/" in s and not s.upper().startswith(("NDPS", "ARMS", "POCSO", "MPA", "MCOCA", "UAPA", "PMLA", "IT/", "SCST", "DPA", "ITPA", "ECA", "PCA", "MV", "ELEC", "WLPA", "EXPL", "GAMB")):
        act, sec = s.split("/", 1)
        return act.strip(), sec.strip()
    for sep in (" s.", " s ", " Sec.", " Section ", " sec. ", " sec "):
        if sep in s:
            act, sec = s.split(sep, 1)
            return act.strip(), sec.strip()
    if "/" in s:
        act, sec = s.split("/", 1)
        return act.strip(), sec.strip()
    parts = s.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    raise ValueError(f"cannot parse charge '{s}'; write it as 'BNS 303(2)' or 'NDPS/20(small)'")
