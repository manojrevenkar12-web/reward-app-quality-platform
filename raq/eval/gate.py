"""The held-out gate, used by the CLI, the README and the dashboard."""
from __future__ import annotations

from raq.config import load


def gate(summary: dict) -> list[str]:
    g = load("gate")["platform"]
    d = summary["designs"]
    p, a = d["platform"], d["as_found"]
    fails = []
    if p["player_days_per_week"] > g["max_player_days_share"] * a["player_days_per_week"]:
        fails.append(f"{p['player_days_per_week']:,.0f} player-days hit a week against {a['player_days_per_week']:,.0f}")
    if p["escaped_money"] > g["max_escaped_money_share"] * a["escaped_money"]:
        fails.append(f"{p['escaped_money']} money defects reached players against {a['escaped_money']}")
    if p["qa_hours_per_week"] > g["max_qa_hours_share"] * a["qa_hours_per_week"]:
        fails.append(f"{p['qa_hours_per_week']:.1f} QA hours a week against {a['qa_hours_per_week']:.1f}")
    if p["lead_hours_median"] > g["max_lead_hours_median"]:
        fails.append(f"median {p['lead_hours_median']:.0f} hours from code freeze to every player")
    if p["found_share"] < g["min_found_share"]:
        fails.append(f"{p['found_share']:.0%} of defects found before release")
    return fails
