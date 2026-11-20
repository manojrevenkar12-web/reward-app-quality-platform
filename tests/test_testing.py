import numpy as np

from raq.keyed import rng
from raq.testing.devices import DeviceInfo, select, top_by_share
from raq.testing.flaky import FlakeDetector
from raq.testing.plan import allocate, flow_risk
from raq.testing.risk import RiskModel, features

PRIOR = {"intercept": -2.6, "log_lines": 0.4, "new_author": 0.5, "api_change": 0.8, "recent_found": 0.3, "backend": 0.0}


def test_risk_model_uses_the_prior_until_it_has_history_then_learns():
    m = RiskModel(PRIOR, min_rows=40)
    x_big = features(800, True, True, 2, True)
    x_small = features(20, False, False, 0, False)
    assert m.predict(x_big) > m.predict(x_small) and not m.learned
    r = rng("risk-test")
    for _ in range(600):                        # truth: only new authors matter
        new = bool(r.random() < 0.3)
        x = features(int(r.integers(20, 900)), new, bool(r.random() < 0.2), int(r.integers(0, 3)), bool(r.random() < 0.5))
        m.add(x, int(r.random() < (0.5 if new else 0.03)))
    m.fit()
    assert m.learned
    assert m.predict(features(100, True, False, 0, False)) > 4 * m.predict(features(100, False, False, 0, False))


def test_static_model_never_learns():
    m = RiskModel(PRIOR, min_rows=1, learn=False)
    for _ in range(100):
        m.add(np.zeros(5), 1)
    m.fit()
    assert not m.learned


DEVS = [DeviceInfo("galaxy_a", "android", "samsung", "a14", "low", 0.25), DeviceInfo("galaxy_s", "android", "samsung", "a15", "high", 0.2),
        DeviceInfo("iphone", "ios", "apple", "i18", "high", 0.25), DeviceInfo("redmi", "android", "xiaomi", "a13", "low", 0.1),
        DeviceInfo("moto", "android", "motorola", "a12", "low", 0.1), DeviceInfo("pixel", "android", "google", "a15", "high", 0.1)]


def test_device_selection_covers_makers_and_os_versions_the_top_list_misses():
    top = top_by_share(DEVS, 3)
    chosen = select(DEVS, 3)
    assert "redmi" not in top and "moto" not in top
    oems = {d.oem for d in DEVS if d.name in chosen}
    oss = {d.os for d in DEVS if d.name in chosen}
    assert len(oems) == 3 and len(oss) == 3


def test_exploratory_time_goes_where_the_risk_is():
    risk = flow_risk([(["cashout"], 0.4), (["settings"], 0.02), (["play_round", "cashout"], 0.2)])
    hours = allocate(risk, 6, 2)
    assert max(hours, key=hours.get) == "cashout" and sum(hours.values()) == 6 and "settings" not in hours


def test_flaky_test_is_quarantined_and_healthy_test_is_not():
    f = FlakeDetector()
    r = rng("flaky-test")
    for rel in range(300):
        f.observe("flaky", bool(r.random() < 0.1), rel)
        f.observe("healthy", bool(r.random() < 0.001), rel)
    assert not f.blocking("flaky") and f.blocking("healthy")
