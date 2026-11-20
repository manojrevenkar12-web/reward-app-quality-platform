"""Which changes in a release are likely to carry a defect: a logistic regression on the team's own history.

Features are what a pull request shows: lines changed, whether the author is new to the module, whether a backend
change touches the API the app calls, and how many defects the team has found in the module lately. Labels are
the defects the team found, before or after release, so a defect nobody found is a "clean" label: the model is
trained on what the team knows, as it would be in production. Until enough releases are seen, a hand-set prior
ranks changes (the static ranking the ablation keeps for good).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

FEATURES = ("log_lines", "new_author", "api_change", "recent_found", "backend")


def features(lines: int, new_author: bool, api_change: bool, recent_found: int, backend: bool) -> np.ndarray:
    return np.array([math.log(max(lines, 1) / 100), float(new_author), float(api_change), float(recent_found), float(backend)])


@dataclass
class RiskModel:
    prior: dict                      # intercept and weights before there is history
    min_rows: int = 40
    l2: float = 1.0
    learn: bool = True
    X: list[np.ndarray] = field(default_factory=list)
    y: list[int] = field(default_factory=list)
    w: np.ndarray | None = None

    def _prior_w(self) -> np.ndarray:
        return np.array([self.prior["intercept"], *(self.prior[f] for f in FEATURES)])

    def add(self, x: np.ndarray, label: int) -> None:
        self.X.append(x)
        self.y.append(label)

    def fit(self) -> None:
        if not self.learn or len(self.y) < self.min_rows or sum(self.y) < 3:
            self.w = None
            return
        X = np.column_stack([np.ones(len(self.X)), np.array(self.X)])
        y = np.array(self.y, dtype=float)
        w = self._prior_w().copy()
        prior = self._prior_w()
        for _ in range(60):                                   # Newton steps, L2 towards the prior
            p = 1 / (1 + np.exp(-X @ w))
            g = X.T @ (p - y) + self.l2 * (w - prior)
            H = (X * (p * (1 - p))[:, None]).T @ X + self.l2 * np.eye(len(w))
            step = np.linalg.solve(H, g)
            w -= step
            if np.abs(step).max() < 1e-6:
                break
        self.w = w

    def predict(self, x: np.ndarray) -> float:
        w = self.w if self.w is not None else self._prior_w()
        return float(1 / (1 + math.exp(-(w[0] + w[1:] @ x))))

    @property
    def learned(self) -> bool:
        return self.w is not None
