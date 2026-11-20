from raq.world.app import AppWorld


def test_same_seed_same_releases_and_defects(cfg):
    a, b = AppWorld(cfg, 7), AppWorld(cfg, 7)
    assert [(c.module, c.lines) for r in a.releases for c in r.changes] == [(c.module, c.lines) for r in b.releases for c in r.changes]
    assert [x.id for r in a.releases for x in r.defects] == [x.id for r in b.releases for x in r.defects]


def test_defects_show_only_where_they_trigger(world):
    for r in world.releases:
        for x in r.defects:
            assert x.devices, x
            for d in world.devices:
                assert (d.name in x.devices) == world.triggers(x.trigger, d)


def test_adoption_rises_and_saturates(world):
    xs = [world.adoption(h) for h in (0, 12, 24, 72, 200, 1000)]
    assert xs == sorted(xs) and xs[0] == 0 and xs[-1] < 1


def test_more_exposure_never_shows_fewer_counts_on_the_same_luck(world):
    for k in range(50):
        assert world.observe(("same", k), 3.0) <= world.observe(("same", k), 6.0)
        assert world.observe(("big", k), 500.0) <= world.observe(("big", k), 800.0)
