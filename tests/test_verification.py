from engine import verification


def test_full_build_verifies(build_result):
    r = build_result["report"]
    assert r["passed"], {k: v for k, v in r["texts"].items() if not v["passed"]}
    assert r["health_claims"] == 0
    assert r["numbers_found"] > 100
    assert r["numbers_verified"] == r["numbers_found"]
    assert r["badge"].startswith("Verified: ")


def test_tamper_test_catches_changed_number(build_result):
    allowed = build_result["allowed"]
    text = build_result["brief_en"]
    assert verification.verify_text(text, allowed)["passed"]
    tampered = text.replace("1524", "1525", 1)
    res = verification.verify_text(tampered, allowed)
    assert not res["passed"] and res["unverified"] == ["1525"]


def test_tamper_test_catches_invented_number(build_result):
    res = verification.verify_text(build_result["brief_en"] + "\nDO was 77.77 mg/l.", build_result["allowed"])
    assert res["unverified"] == ["77.77"]


def test_health_claim_blocker_en(build_result):
    for bad in ("The water is safe to bathe in.", "This ghat is toxic.", "Immersion will cause disease.",
                "No health risk was found."):
        res = verification.verify_text(bad, build_result["allowed"])
        assert res["health_claims"] and not res["passed"], bad


def test_health_claim_blocker_hi(build_result):
    for bad in ("यह पानी नहाने के लिए सुरक्षित है।", "यह घाट खतरनाक है।", "इससे बीमारी हो सकती है।"):
        res = verification.verify_text(bad, build_result["allowed"])
        assert res["health_claims"], bad


def test_number_extraction_handles_decimals_and_ranges():
    assert verification.extract_numbers("pH 6.5-8.5, DO 0.6 mg/l, 2023-2025, page 26.") == \
        ["6.5", "8.5", "0.6", "2023", "2025", "26"]


def test_every_fact_has_id_and_value(build_result):
    ids = [f["fact_id"] for f in build_result["facts"]]
    assert len(ids) == len(set(ids))
    assert all("value" in f and "claim_text" in f and "source_readings" in f for f in build_result["facts"])
