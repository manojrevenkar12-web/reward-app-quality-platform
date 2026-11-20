"""Where the QA chapter spends its exploratory hours in a release: two-hour blocks, greedily to the flows with the
most risk left, where risk is the chance that some change touching the flow carries a defect."""
from __future__ import annotations


def flow_risk(changes: list[tuple[list[str], float]]) -> dict[str, float]:
    """changes: (flows the changed module touches, P(defect) of the change). A change's risk is split over its flows."""
    clean: dict[str, float] = {}
    for flows, p in changes:
        for f in flows:
            clean[f] = clean.get(f, 1.0) * (1 - p / len(flows))
    return {f: 1 - c for f, c in clean.items()}


def allocate(risk: dict[str, float], hours: float, block: float = 2.0, find_per_block: float = 0.5) -> dict[str, float]:
    """Each block on a flow finds what is there with `find_per_block`; give each block to the flow where it removes the
    most expected risk."""
    out = {f: 0.0 for f in risk}
    left = {f: r for f, r in risk.items()}
    n = int(hours // block)
    for _ in range(n):
        if not left:
            break
        f = max(left, key=lambda k: (left[k] * find_per_block, k))
        if left[f] <= 0:
            break
        out[f] += block
        left[f] *= 1 - find_per_block
    return {f: h for f, h in out.items() if h > 0}
