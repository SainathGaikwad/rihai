"""The Hindi and Marathi drafts carry the same figures as the English one and pass the citation gate."""
from datetime import date

import pytest

from rihai.agent.draft import Particulars, draft
from rihai.eligibility import Charge, Prisoner, assess

A = assess(Prisoner([Charge("BNS", "303(2)")], date(2025, 1, 10), True, identifier="UTP-0417"), as_of=date(2026, 10, 24))
P = Particulars(applicant_name="R. K.", applicant_age="24", parent_name="K. S.", police_station="Yerawada",
                fir_no="212 of 2025", case_no="1180 of 2025")


@pytest.mark.parametrize("lang,bond_word,date_word", [("hi", "मुचलके", "10.01.2026"), ("mr", "जातमुचलक्यावर", "10.01.2026")])
def test_draft_renders_and_passes_gate(lang, bond_word, date_word):
    d = draft(A, P, lang=lang)
    assert d["gate"] is not None and not d["gate"].blocked
    app = d["application"]
    assert bond_word in app                      # first-time offender -> bond, not bail
    assert date_word in app                      # the eligibility date from the engine
    assert "652" in app                          # days served
    assert "Section 303(2) of the Bharatiya Nyaya Sanhita, 2023" in app   # references stay in English
    assert "Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023" in app
    assert app.startswith("[")                   # the review line


def test_bail_not_bond_when_not_first_time():
    a = assess(Prisoner([Charge("IPC", "379")], date(2024, 3, 1), False), as_of=date(2026, 10, 24))
    assert "जमानत" in draft(a, P, lang="hi")["application"]
    assert "जामिनावर" in draft(a, P, lang="mr")["application"]


def test_max_term_variant_in_both_languages():
    a = assess(Prisoner([Charge("BNS", "303(2)")], date(2023, 6, 1), False, multiple_cases_pending=True), as_of=date(2026, 10, 24))
    for lang in ("hi", "mr"):
        d = draft(a, P, lang=lang)
        assert not d["gate"].blocked
        assert "479(1)" in d["application"]


def test_unknown_language_rejected():
    with pytest.raises(ValueError):
        draft(A, P, lang="ur")
