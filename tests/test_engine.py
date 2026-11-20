from raq.eval.run import run_all, summarize
from raq.sim.designs import BY_NAME
from raq.sim.engine import run
from raq.world.app import AppWorld


def test_platform_hits_fewer_players_than_as_found(cfg):
    s = summarize(run_all(False, names=["as_found", "platform"], weeks=12, seeds=[4102], workers=1), n_boot=100)["designs"]
    assert s["platform"]["player_days_per_week"] < s["as_found"]["player_days_per_week"]
    assert s["platform"]["found_before_release"] > s["as_found"]["found_before_release"]


def test_every_design_meets_the_same_defects(cfg, platform, value):
    seen = {}
    for n in ("as_found", "automate_everything", "platform"):
        w = AppWorld(cfg, 4102)
        rel = run(w, BY_NAME[n], platform, value)
        seen[n] = sum(r["defects"] for r in rel)
    assert len(set(seen.values())) == 1


def test_a_better_test_finds_a_superset(cfg, platform, value):
    """Same luck: the draw for a test layer is keyed by the defect, so more exploratory hours never find less."""
    w = AppWorld(cfg, 4103)
    x = next(d for r in w.releases for d in r.defects)
    assert all(w.caught(x, "exploratory", hi) >= w.caught(x, "exploratory", lo) for lo, hi in [(0.1, 0.2), (0.3, 0.9), (0.5, 0.51)])
