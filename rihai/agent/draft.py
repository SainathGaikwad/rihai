"""Draft the Section 479 application and the DLSA memo from an Assessment.

Template mode needs no model: every number and every section comes from the Assessment, so the draft cannot
contain a figure the engine did not compute. A model (Muse Spark / Nemotron / Claude) may later rewrite the prose
or translate it; the citation gate runs on whatever it produces.

Hindi and Marathi templates follow the same structure; the statutory references stay in English, as courts in
Maharashtra accept.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..eligibility import Assessment, Status
from ..gate import check as gate_check

SC_CASE = "In Re: Inhuman Conditions in 1382 Prisons, W.P.(C) No. 406 of 2013"
SC_ORDERS = "orders dated 23.08.2024 and 22.10.2024"


@dataclass
class Particulars:
    """What the engine does not know and a human must supply. Keep names out of logs; they belong only here."""
    applicant_name: str = "________"
    applicant_age: str = "__"
    parent_name: str = "________"
    jail: str = "Yerawada Central Prison, Pune"
    court: str = "the Court of the Judicial Magistrate First Class, Pune"
    district: str = "Pune"
    state: str = "Maharashtra"
    police_station: str = "________"
    fir_no: str = "____ of 20__"
    case_no: str = "____ of 20__"
    case_type: str = "R.C.C."
    filed_through: str = "the Legal Aid Defence Counsel, District Legal Services Authority, Pune"
    place: str = "Pune"
    extra_facts: list[str] = field(default_factory=list)


def _years_words(y: float) -> str:
    if y is None:
        return "____"
    if y >= 1 and float(y).is_integer():
        n = int(y)
        return {1: "one year", 2: "two years", 3: "three years", 5: "five years", 7: "seven years", 10: "ten years",
                14: "fourteen years", 20: "twenty years"}.get(n, f"{n} years")
    months = round(y * 12)
    return f"{months} month{'s' if months != 1 else ''}"


def _months_words(y: float, frac: float) -> str:
    m = round(y * 12 * frac)
    return f"{m} month{'s' if m != 1 else ''}"


def _d(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else "__.__.____"


def _charges_sentence(a: Assessment) -> str:
    parts = []
    for r in a.rows:
        act_long = {"BNS": "the Bharatiya Nyaya Sanhita, 2023", "IPC": "the Indian Penal Code, 1860",
                    "NDPS": "the Narcotic Drugs and Psychotropic Substances Act, 1985", "ARMS": "the Arms Act, 1959",
                    "POCSO": "the Protection of Children from Sexual Offences Act, 2012",
                    "MPA": "the Maharashtra Prohibition Act, 1949", "IT": "the Information Technology Act, 2000"}.get(r.act, r.act)
        sec = r.section.split("/")[-1]
        title = f" ({r.title.lower()})" if r.title else ""
        parts.append(f"Section {sec} of {act_long}{title}")
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def application_en(a: Assessment, p: Particulars) -> str:
    if a.status not in (Status.ELIGIBLE, Status.MUST_RELEASE_MAX_TERM):
        raise ValueError(f"no application is drafted for status {a.status.value}; reasons: {a.reasons}")
    c = a.controlling
    first = a.prisoner.first_time_offender
    sec_c = c.section.split("/")[-1]
    act_c = {"BNS": "the Bharatiya Nyaya Sanhita, 2023", "IPC": "the Indian Penal Code, 1860"}.get(c.act, c.act)

    if a.status == Status.MUST_RELEASE_MAX_TERM:
        ground = (
            f"The applicant has been in custody since {_d(a.prisoner.custody_start)}, that is for {a.days_served} days as on "
            f"{_d(a.as_of)}, which equals or exceeds the maximum period of imprisonment of {_years_words(c.max_years)} prescribed for the "
            f"offence under Section {sec_c} of {act_c}. Under the third proviso to Section 479(1) of the Bharatiya Nagarik Suraksha "
            f"Sanhita, 2023, no undertrial prisoner shall in any case be detained during investigation, inquiry or trial for more than "
            f"the maximum period of imprisonment provided for the offence. The applicant's continued detention is therefore without "
            f"authority of law."
        )
        prayer_mode = "forthwith release the applicant from custody"
        heading = "APPLICATION UNDER THE THIRD PROVISO TO SECTION 479(1) OF THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR RELEASE OF AN UNDERTRIAL PRISONER DETAINED BEYOND THE MAXIMUM PERIOD"
    else:
        if first:
            ground = (
                f"The applicant is a first-time offender who has never been convicted of any offence. Under the first proviso to "
                f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023, where such a person has undergone detention for a "
                f"period extending up to one-third of the maximum period of imprisonment specified for the offence, he shall be "
                f"released on bond by the Court. One-third of {_years_words(c.max_years)} is {_months_words(c.max_years, 1/3)}, which "
                f"period was completed on {_d(a.eligible_on)}."
            )
            prayer_mode = "release the applicant on bond under the first proviso to Section 479(1)"
            heading = "APPLICATION UNDER SECTION 479(1) OF THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR RELEASE OF A FIRST-TIME UNDERTRIAL PRISONER ON BOND"
        else:
            ground = (
                f"Under Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023, where a person has undergone detention for a "
                f"period extending up to one-half of the maximum period of imprisonment specified for the offence, he shall be "
                f"released by the Court on bail. One-half of {_years_words(c.max_years)} is {_months_words(c.max_years, 1/2)}, which "
                f"period was completed on {_d(a.eligible_on)}."
            )
            prayer_mode = "release the applicant on bail under Section 479(1)"
            heading = "APPLICATION UNDER SECTION 479(1) OF THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR RELEASE OF AN UNDERTRIAL PRISONER ON BAIL"

    paras = [
        f"The applicant is an undertrial prisoner lodged at {p.jail} in connection with {p.case_type} No. {p.case_no} arising out of "
        f"C.R. No. {p.fir_no} registered at {p.police_station} Police Station, {p.district}, for offences punishable under {_charges_sentence(a)}.",
        f"The applicant was arrested and has been in continuous custody since {_d(a.prisoner.custody_start)}. As on {_d(a.as_of)} the "
        f"applicant has undergone detention for {a.days_served} days"
        + (f", after excluding {a.prisoner.delay_attributable_days} days of delay attributable to the applicant as required by the Explanation to Section 479(1)." if a.prisoner.delay_attributable_days else "."),
        f"The offence under Section {sec_c} of {act_c}, which carries the longest maximum sentence among the offences charged, is punishable "
        f"with imprisonment for a term which may extend to {_years_words(c.max_years)}. It is not an offence for which death or imprisonment "
        f"for life has been specified as one of the punishments.",
        ground,
        "No investigation, inquiry or trial in any other offence or case is pending against the applicant, and Section 479(2) of the "
        "Sanhita therefore has no application." if not a.prisoner.multiple_cases_pending else
        "[REVIEW: the roster records another pending case. Section 479(2) bars release under sub-section (1) where more than one case is pending; "
        "confirm whether that case is live. The third proviso applies regardless.]",
        f"The Hon'ble Supreme Court of India in {SC_CASE}, by its {SC_ORDERS}, has directed all States and Union Territories to apply "
        f"Section 479 to all undertrial prisoners and to take proactive steps to identify and release eligible undertrials, and has "
        f"directed Undertrial Review Committees and Legal Services Authorities to act on such cases on an ongoing basis.",
        f"Under Section 479(3) of the Sanhita, the Superintendent of the jail is required, on completion of the relevant period, to "
        f"forthwith make an application in writing to this Hon'ble Court for the release of the applicant. This application is filed "
        f"through {p.filed_through} so that the applicant's statutory entitlement is placed before this Hon'ble Court without further delay.",
    ]
    paras += p.extra_facts

    body = "\n\n".join(f"{i}. {t}" for i, t in enumerate(paras, 1))
    text = f"""IN {p.court.upper()}
{p.district.upper()}

Criminal Misc. Application No. ______ of {a.as_of.year}
In
{p.case_type} No. {p.case_no}
(C.R. No. {p.fir_no}, {p.police_station} Police Station)

{p.applicant_name}, age {p.applicant_age} years,
s/o or d/o {p.parent_name},
presently lodged at {p.jail}                                   ... Applicant / Accused

versus

The State of {p.state}
(through {p.police_station} Police Station)                       ... Respondent

{heading}

MOST RESPECTFULLY SHOWETH:

{body}

PRAYER

In the premises, it is most respectfully prayed that this Hon'ble Court may be pleased to:

(a) {prayer_mode} of the Bharatiya Nagarik Suraksha Sanhita, 2023, in {p.case_type} No. {p.case_no};

(b) direct the Superintendent, {p.jail}, to release the applicant forthwith on compliance; and

(c) pass such other and further orders as this Hon'ble Court deems fit in the interests of justice.

Place: {p.place}
Date: {_d(a.as_of)}
                                                                  Applicant
                                                                  through {p.filed_through}

VERIFICATION

I, the applicant above named, do hereby state that the contents of paragraphs 1 to {len(paras)} above are true to my knowledge and
belief, and that nothing material has been concealed.

Place: {p.place}
Date: {_d(a.as_of)}                                               Applicant
"""
    return text


def dlsa_memo_en(a: Assessment, p: Particulars) -> str:
    """Two-paragraph note for the DLSA Secretary / UTRC list. No name, roster identifier only."""
    c = a.controlling
    sec_c = c.section.split("/")[-1] if c else "____"
    line = {
        Status.ELIGIBLE: f"eligible under s.479(1) BNSS since {_d(a.eligible_on)} ({'first-time offender, one-third' if a.prisoner.first_time_offender else 'one-half'} of {_years_words(c.max_years)} for {c.act} s.{sec_c}); {a.days_served} days in custody as on {_d(a.as_of)}; release on {a.release_mode}.",
        Status.MUST_RELEASE_MAX_TERM: f"detained beyond the maximum term of {_years_words(c.max_years)} for {c.act} s.{sec_c} since {_d(a.max_term_end)}; third proviso to s.479(1) BNSS - release is mandatory.",
        Status.NOT_YET: f"not yet eligible; threshold for {c.act} s.{sec_c} reached on {_d(a.eligible_on)}.",
        Status.EXCLUDED_LIFE_OR_DEATH: "excluded: an offence charged carries death or life imprisonment.",
        Status.EXCLUDED_MULTIPLE_CASES: "s.479(2): other case(s) pending - verify; maximum-term cap still applies.",
        Status.NEEDS_REVIEW: "needs review: " + "; ".join(a.reasons),
        Status.UNKNOWN_SECTION: "refused: " + "; ".join(a.reasons),
    }[a.status]
    unv = f"\nLaw-table rows used but not yet verified against India Code: {', '.join(a.unverified)}." if a.unverified else ""
    return (f"UTRC / DLSA note - {p.jail}\n"
            f"UTP ref: {a.prisoner.identifier or '____'} | Charges: {', '.join(str(x) for x in a.prisoner.charges)} | Custody since {_d(a.prisoner.custody_start)}\n"
            f"Status ({_d(a.as_of)}): {a.status.value} - {line}{unv}\n"
            f"Action: {'file s.479 application through LADC; inform the prisoner (NALSA SOP on Prison Legal Aid Clinics, 2022)' if a.eligible else 'no filing; recheck on the next review date'}.")


def draft(a: Assessment, p: Particulars | None = None, lang: str = "en") -> dict:
    """Returns {'application': str|None, 'memo': str, 'gate': GateResult|None}. The gate runs on the application."""
    p = p or Particulars()
    if lang != "en":
        raise NotImplementedError("Hindi and Marathi templates land on Day 2 (Sharvari); statutory references stay in English.")
    memo = dlsa_memo_en(a, p)
    if not a.eligible:
        return {"application": None, "memo": memo, "gate": None}
    app = application_en(a, p)
    return {"application": app, "memo": memo, "gate": gate_check(app)}
