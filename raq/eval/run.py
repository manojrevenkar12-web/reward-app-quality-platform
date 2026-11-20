"""Every design on every org, then a summary with paired bootstrap intervals over (org, week) blocks."""
from __future__ import annotations

import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from raq.config import load, world_config
from raq.keyed import rng
from raq.sim.designs import BY_NAME, DESIGNS
from raq.sim.engine import run
from raq.world.app import AppWorld


def run_seed(args) -> dict:
    cfg, seed, names = args
    p, v = load("platform"), load("value")
    out = {"seed": seed, "weeks": cfg["weeks"], "designs": {}}
    for n in names:
        world = AppWorld(cfg, seed)                  # a fresh world per design: nothing carries over but the truth
        out["designs"][n] = run(world, BY_NAME[n], p, v)
    w = AppWorld(cfg, seed)
    out["defects"] = sum(len(r.defects) for r in w.releases)
    out["releases"] = len(w.releases)
    out["changes"] = sum(len(r.changes) for r in w.releases)
    return out


def run_all(heldout: bool = False, names: list[str] | None = None, weeks: int | None = None,
            seeds: list[int] | None = None, workers: int | None = None) -> list[dict]:
    cfg = world_config(heldout)
    if weeks:
        cfg["weeks"] = weeks
    seeds = seeds or cfg["seeds"]
    names = names or [d.name for d in DESIGNS]
    args = [(cfg, s, names) for s in seeds]
    workers = workers or min(len(seeds), os.cpu_count() or 1)
    if workers == 1:
        return [run_seed(a) for a in args]
    with ProcessPoolExecutor(workers) as ex:
        return list(ex.map(run_seed, args))


def _weeks(rels: list[dict], weeks: int, v: dict, p: dict) -> list[dict]:
    rows = []
    for wk in range(weeks):
        rs = [r for r in rels if r["week"] == wk]
        qa = sum(r["qa_hours"] for r in rs)
        eng = sum(r["eng_hours"] for r in rs)
        dev_eur = sum(r["device_minutes"] for r in rs) * p["e2e"]["device_minute_eur"]
        player = sum(r["player_eur"] for r in rs)
        rows.append({"player_days": sum(r["player_days"] for r in rs), "player_eur": player,
                     "money_player_days": sum(r["money_player_days"] for r in rs),
                     "qa_hours": qa, "eng_hours": eng, "device_eur": dev_eur,
                     "cost_eur": player + dev_eur + qa * v["qa_hour_eur"] + eng * v["engineer_hour_eur"],
                     "defects": sum(r["defects"] for r in rs), "found": sum(r["found"] for r in rs),
                     "escaped": sum(r["escaped"] for r in rs), "escaped_money": sum(r["escaped_money"] for r in rs),
                     "undetected": sum(r["undetected"] for r in rs), "reds": sum(r["reds"] for r in rs),
                     "flaky_failures": sum(r["flaky_failures"] for r in rs),
                     "halts": sum(r["halts"] for r in rs), "false_halts": sum(r["false_halts"] for r in rs),
                     "tickets": sum(r["tickets"] for r in rs), "read": sum(r["read"] for r in rs), "read_ok": sum(r["read_ok"] for r in rs),
                     "lead": [r["lead_hours"] for r in rs], "detect": [h for r in rs for h in r["detect_hours"]],
                     "channels": sum((r["channels"] for r in rs), Counter()), "devices": [r["devices"] for r in rs],
                     "quarantined": rs[-1]["quarantined"] if rs else 0})
    return rows


KEYS = ("player_days", "player_eur", "money_player_days", "qa_hours", "eng_hours", "device_eur", "cost_eur", "defects", "found",
        "escaped", "escaped_money", "undetected", "reds", "flaky_failures", "halts", "false_halts", "tickets")


def summarize(runs: list[dict], heldout: bool = False, n_boot: int = 2000) -> dict:
    v, p, cfg = load("value"), load("platform"), world_config(heldout)
    names = list(runs[0]["designs"])
    per = {n: [row for r in runs for row in _weeks(r["designs"][n], r["weeks"], v, p)] for n in names}
    blocks = len(per[names[0]])
    idx = rng("bootstrap", blocks).integers(0, blocks, size=(n_boot, blocks))
    base_pd = np.array([x["player_days"] for x in per["as_found"]]) if "as_found" in per else None
    base_cost = np.array([x["cost_eur"] for x in per["as_found"]]) if "as_found" in per else None
    out = {}
    for n in names:
        rows = per[n]
        a = {k: np.array([x[k] for x in rows], dtype=float) for k in KEYS}
        lead = np.concatenate([x["lead"] for x in rows])
        det = [h for x in rows for h in x["detect"]]
        ch: Counter = sum((x["channels"] for x in rows), Counter())
        defects = a["defects"].sum()
        s = {
            "label": BY_NAME[n].label,
            "player_days_per_week": float(a["player_days"].mean()),
            "player_days_ci": [float(x) for x in np.percentile(a["player_days"][idx].mean(axis=1), [2.5, 97.5])],
            "money_player_days_per_week": float(a["money_player_days"].mean()),
            "player_eur_per_week": float(a["player_eur"].mean()),
            "qa_hours_per_week": float(a["qa_hours"].mean()),
            "eng_hours_per_week": float(a["eng_hours"].mean()),
            "device_eur_per_week": float(a["device_eur"].mean()),
            "cost_eur_per_week": float(a["cost_eur"].mean()),
            "defects": int(defects), "found_before_release": int(a["found"].sum()),
            "found_share": float(a["found"].sum() / max(defects, 1)),
            "escaped": int(a["escaped"].sum()), "escaped_money": int(a["escaped_money"].sum()),
            "undetected": int(a["undetected"].sum()),
            "reds_per_week": float(a["reds"].mean()), "flaky_failures_per_week": float(a["flaky_failures"].mean()),
            "halts": int(a["halts"].sum()), "false_halts": int(a["false_halts"].sum()),
            "lead_hours_median": float(np.median(lead)), "lead_hours_p90": float(np.percentile(lead, 90)),
            "detect_hours_median": float(np.median(det)) if det else None,
            "channels": dict(ch),
            "tickets": int(a["tickets"].sum()),
            "reader_accuracy": float(sum(x["read_ok"] for x in rows) / max(sum(x["read"] for x in rows), 1)) if any(x["read"] for x in rows) else None,
            "devices_tested": float(np.mean([d for x in rows for d in x["devices"]])),
            "quarantined": int(np.mean([x["quarantined"] for x in rows])),
        }
        if base_pd is not None:
            dpd = a["player_days"] - base_pd
            dc = a["cost_eur"] - base_cost
            s["player_days_vs_as_found_ci"] = [float(x) for x in np.percentile(dpd[idx].mean(axis=1), [2.5, 97.5])]
            s["cost_vs_as_found_ci"] = [float(x) for x in np.percentile(dc[idx].mean(axis=1), [2.5, 97.5])]
        out[n] = s
    return {"designs": out, "world": {"orgs": len(runs), "seeds": [r["seed"] for r in runs], "weeks": cfg["weeks"],
                                      "releases": int(sum(r["releases"] for r in runs)), "changes": int(sum(r["changes"] for r in runs)),
                                      "defects": int(sum(r["defects"] for r in runs)), "dau": cfg["players"]["dau"]}}
