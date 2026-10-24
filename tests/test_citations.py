from rihai.gate import check, extract


def test_extracts_common_forms():
    t = ("The applicant is charged under Section 303(2) of the Bharatiya Nyaya Sanhita, 2023 and s. 379 IPC. "
         "This application is under Section 479 of the BNSS. Article 21 of the Constitution guarantees liberty. "
         "He is also charged under NDPS s.20(small).")
    found = {(a, s) for a, s, _ in extract(t)}
    assert ("BNS", "303(2)") in found
    assert ("IPC", "379") in found
    assert ("BNSS", "479") in found
    assert ("CONSTITUTION", "21") in found
    assert ("NDPS", "20(small)") in found


def test_pass_when_all_known():
    t = "Charged under Section 303(2) of the Bharatiya Nyaya Sanhita, 2023. Application under Section 479(1) BNSS."
    r = check(t)
    assert not r.blocked
    assert r.summary().startswith("PASS")


def test_blocks_invented_section():
    t = "Charged under Section 303(2) of the Bharatiya Nyaya Sanhita, 2023 and Section 912 of the Bharatiya Nyaya Sanhita, 2023."
    r = check(t)
    assert r.blocked
    assert any(c.section == "912" for c in r.failures)
    assert "BLOCKED" in r.summary()


def test_blocks_wrong_procedural_section():
    t = "This application is under Section 999 of the BNSS."
    r = check(t)
    assert r.blocked


def test_no_citations_is_pass():
    r = check("The applicant prays for release on bond.")
    assert not r.blocked and r.citations == []


# ---- references without an Act name: the hole a model-written draft would otherwise slip through

def test_bare_invented_section_is_blocked():
    g = check("The applicant is covered by Section 999.")
    assert g.blocked and "without an Act" in g.summary()


def test_bare_real_section_resolves_against_the_acts_the_text_names():
    g = check("Charged under Section 303(2) of the Bharatiya Nyaya Sanhita, 2023; Section 303(2) is bailable in this sense.")
    assert not g.blocked and all(c.ok for c in g.citations)


def test_the_sanhita_shorthand_resolves_but_cannot_invent():
    assert not check("Section 479(2) of the Sanhita has no application.").blocked
    assert check("Section 999 of the Sanhita applies.").blocked


def test_devanagari_forms_are_read():
    assert not check("भारतीय न्याय संहिता की धारा 303(2)").blocked
    assert not check("कलम 303(2) भारतीय न्याय संहिता, 2023").blocked
    assert check("धारा 999 के तहत").blocked


def test_sentence_endings_and_paragraph_numbers_are_not_sections():
    assert check("true to my knowledge and belief.\n\n3. The offence").citations == []
    assert check("for 652 days. 3 years later").citations == []
