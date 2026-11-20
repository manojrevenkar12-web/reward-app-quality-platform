"""Settings live in config/*.yaml. The world reads world.yaml, its held-out overlay and the product catalogue; the
platform reads its own files and the catalogue, never world.yaml."""
from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"


@cache
def _load(name: str) -> dict:
    return yaml.safe_load((CONFIG / f"{name}.yaml").read_text())


def load(name: str) -> dict:
    """A fresh copy, so callers may change it."""
    import copy

    return copy.deepcopy(_load(name))


def world_config(heldout: bool = False) -> dict:
    """world.yaml with the product catalogue (flows, devices, modules), and the held-out overlay if asked."""
    cfg = load("world")
    cfg.update(load("catalogue"))
    if heldout:
        cfg.update(load("heldout"))
    return cfg
