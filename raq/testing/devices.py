"""Which devices to test a release on: greedy coverage of what defects key on (maker, OS version, low-end
hardware), weighted by how many players have it and by the release's risk on that platform.

A defect that only shows on Xiaomi phones with Android 13 is only found on such a phone, so the set should cover
every maker and OS version that many players use, not just the four most popular models.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    name: str
    platform: str
    oem: str
    os: str
    tier: str
    share: float


def attributes(d: DeviceInfo) -> set[tuple[str, str]]:
    a = {("oem", d.oem), ("os", d.os), ("platform", d.platform)}
    if d.tier == "low":
        a.add(("tier", "low"))
    return a


def select(devices: list[DeviceInfo], budget: int, platform_risk: dict[str, float] | None = None) -> list[str]:
    """Pick up to `budget` devices. Each attribute value is worth the player share that has it; a device is worth
    the attributes it covers that are not covered yet, plus its own share (ties go to the popular device)."""
    platform_risk = platform_risk or {}
    value: dict[tuple[str, str], float] = {}
    for d in devices:
        for a in attributes(d):
            value[a] = value.get(a, 0.0) + d.share * (1 + platform_risk.get(d.platform, 0.0))
    chosen: list[str] = []
    covered: set[tuple[str, str]] = set()
    left = list(devices)
    while left and len(chosen) < budget:
        best = max(left, key=lambda d: (sum(value[a] for a in attributes(d) - covered) + 0.5 * d.share, d.share))
        chosen.append(best.name)
        covered |= attributes(best)
        left.remove(best)
    return chosen


def top_by_share(devices: list[DeviceInfo], n: int) -> list[str]:
    return [d.name for d in sorted(devices, key=lambda d: -d.share)[:n]]
