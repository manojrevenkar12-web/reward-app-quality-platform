"""Keyed luck: every draw is named by what it is about.

So every design meets the same releases, the same defects and the same players.
"""
from __future__ import annotations

import hashlib

import numpy as np


def rng(*parts: object) -> np.random.Generator:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))


def uniform(*parts: object) -> float:
    """One named uniform draw in [0, 1)."""
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:8], "little") / 2**64
