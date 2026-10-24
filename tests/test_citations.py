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
