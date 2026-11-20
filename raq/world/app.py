"""The simulated rewarded-gaming app: releases, the changes in them, and the defects those changes carry.

Visible to the platform (through the engine): which modules a release changes, how many lines, whether a
backend change touches the API, whether the author is new to the module; test results; production counts;
player tickets. Hidden: which change carries a defect, what kind, on which devices and in which region it
shows, and how good each kind of test is at finding it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from statistics import NormalDist

import numpy as np

from raq.keyed import rng, uniform

_NORMAL = NormalDist()
KINDS = ("crash", "ui", "money_block", "money_overpay", "perf", "contract_break")
MONEY = {"money_block", "money_overpay", "contract_break"}


@dataclass(frozen=True)
class Device:
    name: str
    platform: str
    oem: str
    os: str
    tier: str
    share: float


@dataclass(frozen=True)
class Module:
    name: str
    side: str
    flows: tuple[str, ...]


@dataclass
class Change:
    """What a release changes. Everything here is visible to the platform."""
    release: int
    module: str
    side: str
    lines: int
    api_change: bool
    new_author: bool


@dataclass
class Defect:
    """Truth: never handed to the platform's components."""
    id: str
    release: int
    module: str
    side: str
    flow: str
    kind: str
    trigger: tuple[str, str]           # ("all", "") | ("oem", "xiaomi") | ("os", "a13") | ("tier", "low")
    region: str | None                 # None: every region
    devices: tuple[str, ...]           # device classes it shows on

    @property
    def money(self) -> bool:
        return self.kind in MONEY


@dataclass
class Release:
    index: int
    hour: float                        # when the release is cut, hours from the start
    changes: list[Change]
    defects: list[Defect] = field(default_factory=list)


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


class AppWorld:
    def __init__(self, cfg: dict, seed: int):
        self.cfg, self.seed = cfg, seed
        self.devices = [Device(**d) for d in cfg["devices"]]
        self.modules = [Module(m["name"], m["side"], tuple(m["flows"])) for m in cfg["modules"]]
        self.flows = cfg["flows"]
        self.regions = cfg["players"]["regions"]
        self.n_releases = cfg["weeks"] * cfg["releases_per_week"]
        self.release_gap = 168 / cfg["releases_per_week"]
        r = rng(seed, "modules")
        self._module_effect = {m.name: float(r.normal(0, cfg["changes"]["defect_model"]["module_sd"])) for m in self.modules}
        self._releases: list[Release] = []
        self._build()

    # --- releases -------------------------------------------------------------------------------------------
    def _build(self) -> None:
        c = self.cfg["changes"]
        dm = c["defect_model"]
        history: list[list[str]] = []          # true defective modules per release, for the recent-defects effect
        for i in range(self.n_releases):
            r = rng(self.seed, "release", i)
            n = int(r.integers(c["modules_per_release"][0], c["modules_per_release"][1] + 1))
            mods = r.choice(len(self.modules), size=n, replace=False)
            rel = Release(i, i * self.release_gap, [])
            recent = [m for h in history[-8:] for m in h]
            bad = []
            for j in sorted(mods):
                m = self.modules[int(j)]
                lo, hi = math.log(c["lines"][0]), math.log(c["lines"][1])
                lines = int(math.exp(r.uniform(lo, hi)))
                api = m.side == "backend" and bool(r.random() < c["api_change_share"])
                new = bool(r.random() < c["new_author_share"])
                ch = Change(i, m.name, m.side, lines, api, new)
                rel.changes.append(ch)
                z = (dm["intercept"] + dm["log_lines"] * math.log(lines / 100) + dm["new_author"] * new + dm["api_change"] * api
                     + dm["recent_defects"] * recent.count(m.name) + self._module_effect[m.name] + r.normal(0, dm["noise_sd"]))
                if uniform(self.seed, "defect", i, m.name) < sigmoid(z):
                    rel.defects.append(self._defect(rel, ch, m))
                    bad.append(m.name)
            history.append(bad)
            self._releases.append(rel)

    def _defect(self, rel: Release, ch: Change, m: Module) -> Defect:
        c, p = self.cfg["changes"], self.cfg["production"]
        r = rng(self.seed, "defect-shape", rel.index, m.name)
        mix = c["kinds"][m.side]
        kind = str(r.choice(list(mix), p=np.array(list(mix.values())) / sum(mix.values())))
        if ch.api_change and r.random() < c["contract_break_if_api_change"]:
            kind = "contract_break"
        flow = str(r.choice(m.flows))
        if m.side == "backend" and r.random() < p["backend_trigger_all"]:
            trig = ("all", "")
        else:
            t = str(r.choice(list(c["triggers"]), p=np.array(list(c["triggers"].values())) / sum(c["triggers"].values())))
            if t == "all":
                trig = ("all", "")
            else:
                values = sorted({getattr(d, t) for d in self.devices if t != "tier" or d.tier == "low"})
                trig = (t, str(r.choice(values)))
        region = None
        if r.random() < c["region_only_share"]:
            others = {k: v for k, v in self.regions.items() if k != "US"}
            region = str(r.choice(list(others), p=np.array(list(others.values())) / sum(others.values())))
        devs = tuple(d.name for d in self.devices if self.triggers(trig, d))
        return Defect(f"{self.seed}-{rel.index}-{m.name}", rel.index, m.name, m.side, flow, kind, trig, region, devs)

    @staticmethod
    def triggers(trig: tuple[str, str], d: Device) -> bool:
        t, v = trig
        return t == "all" or getattr(d, t) == v

    def release(self, i: int) -> Release:
        return self._releases[i]

    @property
    def releases(self) -> list[Release]:
        return self._releases

    # --- exposure -------------------------------------------------------------------------------------------
    def device_share(self, names: tuple[str, ...] | list[str]) -> float:
        s = set(names)
        return sum(d.share for d in self.devices if d.name in s)

    def region_share(self, region: str | None) -> float:
        return 1.0 if region is None else self.regions[region]

    def reach(self, d: Defect) -> float:
        """Share of daily players a fully rolled-out defect reaches."""
        share = self.flows[d.flow]["usage"] * self.device_share(d.devices) * self.region_share(d.region)
        if d.kind == "contract_break":
            share *= self.cfg["production"]["old_version_share"]
        return share

    def adoption(self, hours_since_eligible: float) -> float:
        """Share of eligible players who have installed a new version, by hours since it became available."""
        curve = [0.0, *self.cfg["players"]["update_curve"]]
        x = max(hours_since_eligible, 0) / 24
        k = int(x)
        if k >= len(curve) - 1:
            return curve[-1]
        return curve[k] + (curve[k + 1] - curve[k]) * (x - k)

    # --- tests (truth about how good each test is) ----------------------------------------------------------
    def sensitivity(self, test: str, kind: str) -> float:
        return float(self.cfg["tests"][test].get(kind, 0.0))

    def caught(self, d: Defect, layer: str, p: float) -> bool:
        """Same luck for every design: the draw is keyed by defect and test layer, so a better test finds a superset."""
        return uniform(self.seed, "catch", d.id, layer) < p

    # --- flaky end-to-end tests -----------------------------------------------------------------------------
    def e2e_tests(self, per_flow: int) -> list[tuple[str, int]]:
        return [(f, k) for f in self.flows for k in range(per_flow)]

    def flake_rate(self, test: tuple[str, int], release: int) -> float:
        onset, rate = self._flake(test)
        return rate if release >= onset else 0.0

    @lru_cache(maxsize=4096)  # noqa: B019 - one world per process, a few hundred tests
    def _flake(self, test: tuple[str, int]) -> tuple[int, float]:
        t = self.cfg["tests"]
        key = f"{test[0]}-{test[1]}"
        r = rng(self.seed, "flaky", key)
        rate = float(r.uniform(*t["e2e_flaky_rate"]))
        if r.random() < t["e2e_flaky_share"]:
            return 0, rate
        # tests that turn flaky later (a new animation, a slower device farm, a timing change)
        per_test = t["e2e_new_flaky_per_week"] / max(len(self.flows) * 6, 1) / self.cfg["releases_per_week"]
        return int(r.geometric(min(per_test, 0.99))), rate

    def flipped(self, test: tuple[str, int], release: int, device: str, attempt: int) -> bool:
        rate = self.flake_rate(test, release)
        return rate > 0 and uniform(self.seed, "flip", test, release, device, attempt) < rate

    # --- production -----------------------------------------------------------------------------------------
    def baseline(self, metric: str) -> float:
        """Expected count per 1,000 player-days without any defect."""
        return float(self.cfg["production"]["baseline_per_1k_player_days"][metric])

    def excess(self, d: Defect, metric: str) -> float:
        """Extra count per 1,000 player-days the defect reaches."""
        return float(self.cfg["production"]["excess_per_1k_affected_player_days"][d.kind].get(metric, 0.0))

    def observe(self, key: tuple, expected: float) -> int:
        """A Poisson count, drawn by inversion of one keyed uniform: designs that expose more players see more,
        on the same luck."""
        mu = max(expected, 0.0)
        if mu == 0:
            return 0
        u = uniform(self.seed, "observe", *key)
        if mu > 40:
            return max(0, round(mu + math.sqrt(mu) * _NORMAL.inv_cdf(min(max(u, 1e-12), 1 - 1e-12))))
        k, term = 0, math.exp(-mu)
        cdf = term
        while u > cdf and k < 400:
            k += 1
            term *= mu / k
            cdf += term
        return k
