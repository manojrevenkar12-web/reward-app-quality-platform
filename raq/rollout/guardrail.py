"""Rollout guardrails: is a segment of players on the new version seeing more crashes, failed cash-outs or odd
coin balances than its baseline? A one-sided Poisson test per segment and metric, Bonferroni over the segments
checked, so a staged rollout halts on a real excess and rarely on noise.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def poisson_sf(k: int, mu: float) -> float:
    """P(X >= k) for X ~ Poisson(mu): exact in log space for small means, normal with continuity correction above."""
    if k <= 0:
        return 1.0
    if mu <= 0:
        return 0.0
    if mu > 400:
        return 0.5 * math.erfc(((k - 0.5) - mu) / math.sqrt(2 * mu))
    def logpmf(i: int) -> float:
        return i * math.log(mu) - mu - math.lgamma(i + 1)

    if k > mu:                                       # the upper tail directly, so tiny p-values stay accurate
        hi = k + 60 + int(10 * math.sqrt(mu))
        return min(1.0, sum(math.exp(logpmf(i)) for i in range(k, hi)))
    return max(0.0, 1.0 - sum(math.exp(logpmf(i)) for i in range(k)))


@dataclass(frozen=True)
class Check:
    segment: str            # e.g. "crash|redmi_android13|v41"
    observed: int
    expected: float         # baseline count for the exposure in the window


def halt(checks: list[Check], alpha: float, n_tests: int | None = None, min_count: int = 3) -> list[Check]:
    """The checks that fail: observed count improbably high for the baseline, after Bonferroni over all the checks made
    in the round (n_tests; by default the checks passed in)."""
    if not checks:
        return []
    a = alpha / (n_tests or len(checks))
    return [c for c in checks if c.observed >= min_count and poisson_sf(c.observed, c.expected) < a]
