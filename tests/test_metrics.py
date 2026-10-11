from engine import metrics


def test_headline_counts(rows):
    h = metrics.headline_metrics(rows)
    assert h["total_rows"] == 1524
    assert (h["Dissolved oxygen"]["breaches"], h["Dissolved oxygen"]["sampled"]) == (42, 116)
    assert (h["BOD"]["breaches"], h["BOD"]["sampled"]) == (100, 112)


def test_do_zero_at_bairagarh_four_times(rows):
    z = [r for r in rows if r["parameter"] == "Dissolved oxygen" and r["value"] == 0.0]
    assert len(z) == 4 and all(r["site"].startswith("Bairagarh") for r in z)


def test_bdl_not_counted_either_way(rows):
    m = metrics.param_metrics(rows, "BOD")
    assert m["sampled"] + m["bdl"] + m["missing"] == sum(1 for r in rows if r["parameter"] == "BOD")
    assert m["breaches"] <= m["sampled"]


def test_coverage_matrix_gaps(rows):
    g = metrics.ghat_metrics("Bairagarh (Sant Hirdaram) kund", rows)
    assert g["coverage"]["expected"] == 18
    no_table = {(x["year"], x["festival"]) for x in g["coverage"]["gaps"] if x["status"] == "no_table"}
    assert no_table == {(2025, "Durga")}
    full = metrics.ghat_metrics("Shahpura lake ghat", rows)
    assert full["coverage"]["covered"] == 18 and full["coverage"]["gaps"] == []


def test_durga_weighting_changes_rate():
    base = {"year": 2024, "parameter": "BOD", "exceedance": 0.1}
    rows = [
        {**base, "festival": "Durga", "outcome": "breach"},
        {**base, "festival": "Ganesh", "outcome": "ok"},
    ]
    m = metrics.param_metrics(rows, "BOD")
    assert m["breach_rate"] == 0.5
    assert m["weighted_breach_rate"] == 2 / 3
