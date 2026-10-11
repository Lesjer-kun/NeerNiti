import pytest

from engine import rules
from engine.loader import Reading


def mk(parameter, value, state="numeric"):
    return Reading(2025, "Durga", "X", "Y", "during", parameter, value, "mg/l", "", str(value), parameter, "X", "high", 1, state)


@pytest.mark.parametrize("value,expected", [(4.99, "breach"), (5.0, "ok"), (5.01, "ok"), (0.0, "breach")])
def test_do_boundary(thresholds, value, expected):
    assert rules.evaluate(mk("Dissolved oxygen", value), thresholds) == expected


@pytest.mark.parametrize("value,expected", [(3.01, "breach"), (3.0, "ok"), (2.99, "ok"), (30.0, "breach")])
def test_bod_boundary(thresholds, value, expected):
    assert rules.evaluate(mk("BOD", value), thresholds) == expected


@pytest.mark.parametrize("value,expected", [(6.49, "breach"), (6.5, "ok"), (7.0, "ok"), (8.5, "ok"), (8.51, "breach")])
def test_ph_boundary(thresholds, value, expected):
    assert rules.evaluate(mk("pH", value), thresholds) == expected


def test_bdl_and_missing_not_evaluated(thresholds):
    assert rules.evaluate(mk("BOD", None, "bdl"), thresholds) == "bdl"
    assert rules.evaluate(mk("BOD", None, "missing"), thresholds) == "missing"


def test_other_parameters_not_assessed(thresholds):
    for p in ("COD", "Lead", "Turbidity", "Conductivity", "Total solids"):
        assert rules.evaluate(mk(p, 9999.0), thresholds) == "not_assessed"


def test_exceedance_factor_bounds(thresholds):
    assert rules.exceedance_factor("Dissolved oxygen", 0.0, thresholds) == 1.0
    assert rules.exceedance_factor("Dissolved oxygen", 5.0, thresholds) == 0.0
    assert rules.exceedance_factor("BOD", 30.0, thresholds) == 1.0
    assert 0 < rules.exceedance_factor("BOD", 10.0, thresholds) < 1
    assert rules.exceedance_factor("pH", 7.0, thresholds) == 0.0
    assert rules.exceedance_factor("pH", 9.0, thresholds) == pytest.approx(1 / 3)
