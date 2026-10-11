from engine import loader


def test_row_count(readings):
    assert len(readings) == 1524


def test_seven_ghats_and_13_parameters(readings):
    assert len(loader.sites(readings)) == 7
    assert len({r.parameter for r in readings}) == 13


def test_classify_numeric():
    assert loader.classify("2.5", "", "2.5") == (2.5, "numeric")


def test_classify_bdl_is_not_zero_and_not_missing():
    v, state = loader.classify("", "BDL", "BDL")
    assert v is None and state == "bdl"
    assert loader.classify("", "", "ND")[1] == "bdl"


def test_classify_missing_markers():
    for printed, flag in [("", ""), ("_", "not sampled"), ("-", ""), ("*", "*"), ("**", "**"), ("", "not sampled")]:
        assert loader.classify("", flag, printed) == (None, "missing"), (printed, flag)


def test_states_in_dataset(readings):
    states = {s: sum(1 for r in readings if r.state == s) for s in ("numeric", "bdl", "missing")}
    assert states == {"numeric": 1289, "bdl": 174, "missing": 61}
    assert all(r.value is None for r in readings if r.state != "numeric")


def test_as_printed_preserved(readings):
    r = next(r for r in readings if r.flag == "BDL")
    assert r.value_as_printed == "BDL" and r.site_as_printed and r.parameter_as_printed


def test_class_b_thresholds(thresholds):
    assert thresholds["Dissolved oxygen"] == {"type": "min", "min": 5.0, "unit": "mg/l"}
    assert thresholds["BOD"] == {"type": "max", "max": 3.0, "unit": "mg/l"}
    assert thresholds["pH"]["min"] == 6.5 and thresholds["pH"]["max"] == 8.5


def test_site_meta_ambiguity(readings):
    meta = loader.site_meta(readings)
    assert meta["Rani Kamlapati ghat / Kamla Park kund"]["site_ambiguous"] is True
    assert meta["Rani Kamlapati ghat / Kamla Park kund"]["water_body"] == "Lower Lake"
    assert all(not m["site_ambiguous"] for s, m in meta.items() if not s.startswith("Rani"))
