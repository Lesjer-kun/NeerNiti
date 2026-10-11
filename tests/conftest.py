import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import loader, rules, metrics, ranking  # noqa: E402


@pytest.fixture(scope="session")
def readings():
    return loader.load_readings()


@pytest.fixture(scope="session")
def thresholds():
    return loader.load_class_b_thresholds()


@pytest.fixture(scope="session")
def rows(readings, thresholds):
    return rules.evaluate_all(readings, thresholds)


@pytest.fixture(scope="session")
def ranked(readings, rows):
    meta = loader.site_meta(readings)
    per_ghat = {s: metrics.ghat_metrics(s, rows) for s in loader.sites(readings)}
    return ranking.rank_ghats(per_ghat, meta)


@pytest.fixture(scope="session")
def build_result():
    import build
    return build.run(date(2026, 10, 11), write=False)
