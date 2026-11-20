"""Flaky end-to-end tests: Wald's sequential probability ratio test per test on 'failed, then passed on retry'.

A test that flips at the healthy rate p0 is kept blocking; one that flips at p1 or more is quarantined: it still
runs and reports, but its failures no longer fail the release pipeline, and it goes to its owner.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class FlakeDetector:
    p0: float = 0.002
    p1: float = 0.04
    alpha: float = 0.01
    beta: float = 0.05
    llr: dict = field(default_factory=dict)
    quarantined: dict = field(default_factory=dict)       # test -> release quarantined

    @property
    def upper(self) -> float:
        return math.log((1 - self.beta) / self.alpha)

    def observe(self, test, flipped: bool, release: int) -> None:
        if test in self.quarantined:
            return
        step = math.log(self.p1 / self.p0) if flipped else math.log((1 - self.p1) / (1 - self.p0))
        v = max(0.0, self.llr.get(test, 0.0) + step)
        self.llr[test] = v
        if v >= self.upper:
            self.quarantined[test] = release

    def blocking(self, test) -> bool:
        return test not in self.quarantined
