"""When do tickets add up to a bug? Count readings per (flow, symptom) in a rolling window and compare with what
that pair usually gets; file a bug report when the count is improbably high (one-sided Poisson test, Bonferroni
over the pairs). The reader labels, this decides.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from raq.rollout.guardrail import poisson_sf


@dataclass
class ClusterWatch:
    baseline_per_hour: dict[tuple[str, str], float]      # usual tickets per hour for each (flow, symptom)
    window_hours: int = 6
    alpha: float = 1e-3
    min_count: int = 6
    _hist: dict = field(default_factory=dict)

    def add_hour(self, counts: dict[tuple[str, str], int]) -> list[tuple[tuple[str, str], int, float]]:
        """Feed one hour of ticket counts per pair (background and new); returns the pairs that alarm this hour."""
        alarms = []
        n_pairs = max(len(self.baseline_per_hour), 1)
        for pair in set(self._hist) | set(counts):          # pairs with no tickets yet have nothing to test
            base = self.baseline_per_hour.get(pair, 0.0)
            q = self._hist.setdefault(pair, deque(maxlen=self.window_hours))
            q.append(counts.get(pair, 0))
            k, mu = sum(q), base * len(q)
            if k >= self.min_count:
                p = poisson_sf(k, mu)
                if p < self.alpha / n_pairs:
                    alarms.append((pair, k, mu))
        return alarms
