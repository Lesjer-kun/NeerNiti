from engine import ranking


def test_all_seven_ghats_ranked_once(ranked):
    assert len(ranked) == 7
    assert [e["rank"] for e in ranked] == list(range(1, 8))
    assert len({e["site"] for e in ranked}) == 7


def test_deterministic_and_sorted(ranked):
    sev = [e["severity"] for e in ranked]
    assert sev == sorted(sev, reverse=True)
    assert all(0 <= s <= 100 for s in sev)


def test_tiers():
    assert ranking.tier_for(75)["key"] == "critical"
    assert ranking.tier_for(74.9)["key"] == "high"
    assert ranking.tier_for(50)["key"] == "high"
    assert ranking.tier_for(25)["key"] == "moderate"
    assert ranking.tier_for(24.9)["key"] == "lower"


def test_evidence_strength_is_separate_axis(ranked):
    # Lowest-severity ghat still has strong evidence: the axes must not collapse into one.
    lowest = ranked[-1]
    assert lowest["tier"]["key"] == "lower"
    assert lowest["evidence"]["key"] == "strong"
    assert {e["evidence"]["key"] for e in ranked} <= {"strong", "moderate", "limited"}


def test_evidence_strength_thresholds():
    def m(n, combos):
        return {"assessed_sampled": n, "coverage": {"covered": combos, "expected": 18}}
    assert ranking.evidence_strength(m(12, 4))["key"] == "strong"
    assert ranking.evidence_strength(m(11, 4))["key"] == "moderate"
    assert ranking.evidence_strength(m(6, 2))["key"] == "moderate"
    assert ranking.evidence_strength(m(5, 5))["key"] == "limited"
    assert ranking.evidence_strength(m(20, 1))["key"] == "limited"


def test_bairagarh_is_top_and_has_gaps(ranked):
    assert ranked[0]["short_name"] == "Bairagarh"
    assert len(ranked[0]["coverage"]["gaps"]) == 5
    assert ranked[0]["testing_priority"]["rank"] == 1


def test_testing_ranking_differs_from_severity(ranked):
    sev_order = [e["site"] for e in ranked]
    test_order = [e["site"] for e in sorted(ranked, key=lambda e: e["testing_priority"]["rank"])]
    assert sev_order != test_order


def test_reasons_are_prefixed_with_ghat(ranked):
    for e in ranked:
        assert e["reason_en"].startswith(e["short_name"] + ":")
        assert e["reason_hi"].startswith(e["short_name"] + ":")
