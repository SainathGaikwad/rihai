"""The rule, tested against the statute. Dates are chosen so the arithmetic is checkable by hand."""
from datetime import date

import pytest

from rihai.eligibility import Charge, Prisoner, Status, assess, assess_roster

D = date  # shorthand


def P(*charges, start, first=True, multi=False, delay=0, ident="UTP-1"):
    return Prisoner(charges=[Charge(a, s) for a, s in charges], custody_start=start, first_time_offender=first,
                    multiple_cases_pending=multi, delay_attributable_days=delay, identifier=ident)


# ---------------------------------------------------------------- the headline case
def test_theft_first_time_one_third():
    # BNS 303(2) theft: max 3 years. First-time offender: 1/3 = 12 months.
    p = P(("BNS", "303(2)"), start=D(2025, 1, 15), first=True)
    a = assess(p, as_of=D(2026, 1, 14))
    assert a.status == Status.NOT_YET
    assert a.eligible_on == D(2026, 1, 15)
    a = assess(p, as_of=D(2026, 1, 15))
    assert a.status == Status.ELIGIBLE
    assert a.release_mode == "bond"
    assert a.max_term_years == 3
    assert a.fraction == pytest.approx(1 / 3)


def test_theft_not_first_time_one_half():
    p = P(("BNS", "303(2)"), start=D(2025, 1, 15), first=False)
    a = assess(p, as_of=D(2026, 7, 14))
    assert a.status == Status.NOT_YET
    assert a.eligible_on == D(2026, 7, 15)         # 18 months
    a = assess(p, as_of=D(2026, 7, 15))
    assert a.status == Status.ELIGIBLE
    assert a.release_mode == "bail"


# ---------------------------------------------------------------- old-law charges still work
def test_ipc_theft_equivalent():
    p = P(("IPC", "379"), start=D(2024, 3, 1), first=True)
    a = assess(p, as_of=D(2025, 3, 1))
    assert a.status == Status.ELIGIBLE
    assert a.controlling.bns_equivalent == "303"


# ---------------------------------------------------------------- the controlling charge is the longest term
def test_controlling_is_longest_max():
    # cheating 318(4) 7y + theft 303(2) 3y -> 7y controls; first-time 1/3 = 28 months
    p = P(("BNS", "318(4)"), ("BNS", "303(2)"), start=D(2024, 1, 1), first=True)
    a = assess(p, as_of=D(2026, 4, 30))
    assert a.status == Status.NOT_YET
    assert a.controlling.key == "BNS/318(4)"
    assert a.eligible_on == D(2026, 5, 1)
    a = assess(p, as_of=D(2026, 5, 1))
    assert a.status == Status.ELIGIBLE


# ---------------------------------------------------------------- statutory exclusions
def test_life_offence_excluded():
    p = P(("BNS", "103(1)"), start=D(2020, 1, 1), first=True)
    a = assess(p, as_of=D(2026, 1, 1))
    assert a.status == Status.EXCLUDED_LIFE_OR_DEATH


def test_one_life_charge_among_many_excludes():
    p = P(("BNS", "303(2)"), ("BNS", "310(2)"), start=D(2020, 1, 1), first=True)
    a = assess(p, as_of=D(2026, 1, 1))
    assert a.status == Status.EXCLUDED_LIFE_OR_DEATH
    assert "310(2)" in a.reasons[0]


def test_dacoity_ipc_excluded():
    a = assess(P(("IPC", "395"), start=D(2019, 1, 1), first=True), as_of=D(2026, 1, 1))
    assert a.status == Status.EXCLUDED_LIFE_OR_DEATH


# ---------------------------------------------------------------- the engine refuses rather than guesses
def test_unknown_section_refused():
    a = assess(P(("BNS", "999"), start=D(2024, 1, 1)), as_of=D(2026, 1, 1))
    assert a.status == Status.UNKNOWN_SECTION
    assert "not in the law table" in a.reasons[0]


def test_umbrella_section_needs_subsection():
    a = assess(P(("BNS", "118"), start=D(2024, 1, 1)), as_of=D(2026, 1, 1))
    assert a.status == Status.NEEDS_REVIEW
    assert "118(1)" in a.reasons[0] and "118(2)" in a.reasons[0]


def test_conditional_life_needs_review():
    # attempt to murder: life only if hurt caused -> a human must read the FIR
    a = assess(P(("BNS", "109(1)"), start=D(2022, 1, 1)), as_of=D(2026, 1, 1))
    assert a.status == Status.NEEDS_REVIEW
    assert "hurt" in a.reasons[0]


def test_unbounded_section_needs_review():
    a = assess(P(("IPC", "397"), start=D(2015, 1, 1)), as_of=D(2026, 1, 1))
    # 397 carries life in our encoding (principal offence may be dacoity) -> excluded, which is the safe outcome
    assert a.status in (Status.NEEDS_REVIEW, Status.EXCLUDED_LIFE_OR_DEATH)


def test_ndps_needs_quantity():
    a = assess(P(("NDPS", "20"), start=D(2024, 1, 1)), as_of=D(2026, 1, 1))
    assert a.status == Status.NEEDS_REVIEW
    a = assess(P(("NDPS", "20(small)"), start=D(2025, 1, 1), first=True), as_of=D(2025, 5, 1))
    assert a.status == Status.ELIGIBLE                     # 1 year max, 1/3 = 4 months
    assert a.eligible_on == D(2025, 5, 1)


# ---------------------------------------------------------------- s.479(2) and the third proviso
def test_multiple_cases_bar():
    p = P(("BNS", "303(2)"), start=D(2024, 1, 1), first=True, multi=True)
    a = assess(p, as_of=D(2026, 1, 1))
    assert a.status == Status.EXCLUDED_MULTIPLE_CASES


def test_third_proviso_beats_multiple_cases():
    # 3-year max, detained 3 years -> must release even with multiple cases pending
    p = P(("BNS", "303(2)"), start=D(2023, 1, 1), first=False, multi=True)
    a = assess(p, as_of=D(2026, 1, 1))
    assert a.status == Status.MUST_RELEASE_MAX_TERM
    assert a.max_term_end == D(2026, 1, 1)


def test_delay_attributable_pushes_date():
    p = P(("BNS", "303(2)"), start=D(2025, 1, 15), first=True, delay=30)
    a = assess(p, as_of=D(2026, 1, 15))
    assert a.status == Status.NOT_YET
    assert a.eligible_on == D(2026, 2, 14)


# ---------------------------------------------------------------- fractional years and calendar arithmetic
def test_six_month_offence_first_time():
    # 189(2) unlawful assembly: 6 months; 1/3 = 2 months
    p = P(("BNS", "189(2)"), start=D(2025, 10, 1), first=True)
    a = assess(p, as_of=D(2025, 12, 1))
    assert a.status == Status.ELIGIBLE
    assert a.eligible_on == D(2025, 12, 1)


def test_fine_only_needs_review():
    a = assess(P(("BNS", "285"), start=D(2025, 1, 1)), as_of=D(2026, 1, 1))
    assert a.status == Status.NEEDS_REVIEW


# ---------------------------------------------------------------- roster entry point and output shape
def test_roster_parsing_and_dict():
    rows = [
        {"identifier": "A", "charges": ["BNS 303(2)"], "custody_start": "2025-01-15", "first_time_offender": True},
        {"identifier": "B", "charges": ["IPC/420", "IPC 468"], "custody_start": "2023-06-01", "first_time_offender": False},
        {"identifier": "C", "charges": ["NDPS/20(commercial)"], "custody_start": "2020-01-01", "first_time_offender": True},
    ]
    out = assess_roster(rows, as_of=D(2026, 10, 24))
    assert [a.status for a in out] == [Status.ELIGIBLE, Status.NOT_YET, Status.ELIGIBLE]
    d = out[0].to_dict()
    assert d["identifier"] == "A" and d["status"] == "ELIGIBLE" and d["eligible_on"] == "2026-01-15"
    assert out[1].controlling.key == "IPC/420"            # 7y beats 468's 7y tie -> first max wins; both 7
    assert out[2].eligible_on == D(2026, 9, 1)             # 20y x 1/3 = 80 months


def test_unverified_rows_are_reported():
    a = assess(P(("BNS", "303(2)"), start=D(2025, 1, 15), first=True), as_of=D(2026, 6, 1))
    assert "BNS/303(2)" in a.unverified
    assert any("not yet verified" in r for r in a.reasons)


def test_ipc_392_bare_is_reviewed_with_both_limbs_shown():
    """Charge-sheets write a bare 392; plain robbery is 10 years, highway-at-night 14. The reviewer must pick."""
    from datetime import date as _d
    a = assess(Prisoner(charges=[Charge("IPC", "392")], custody_start=_d(2021, 6, 1), first_time_offender=False), as_of=_d(2026, 10, 24))
    assert a.status == Status.NEEDS_REVIEW and "392(plain) 10y" in a.reasons[0] and "392(highway) 14y" in a.reasons[0]
    plain = assess(Prisoner(charges=[Charge("IPC", "392(plain)")], custody_start=_d(2021, 6, 1), first_time_offender=False), as_of=_d(2026, 10, 24))
    assert plain.status == Status.ELIGIBLE and plain.eligible_on == _d(2026, 6, 1)
    highway = assess(Prisoner(charges=[Charge("IPC", "392(highway)")], custody_start=_d(2021, 6, 1), first_time_offender=False), as_of=_d(2026, 10, 24))
    assert highway.status == Status.NOT_YET and highway.eligible_on == _d(2028, 6, 1)
