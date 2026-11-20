"""python -m raq.eval.cli evaluate | heldout | gate [--dev] | readme [--check] | quick"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime

from raq.config import CONFIG
from raq.eval import report
from raq.eval.gate import gate
from raq.eval.run import run_all, summarize
from raq.sim.designs import ORDER

LOCK = CONFIG / "heldout.lock"


def _hash() -> str:
    h = hashlib.sha256()
    for n in ("world", "catalogue", "heldout", "platform", "value", "gate"):
        h.update((CONFIG / f"{n}.yaml").read_bytes())
    return h.hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="raq.eval.cli")
    ap.add_argument("cmd", choices=["evaluate", "heldout", "gate", "readme", "quick"])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "quick":
        s = summarize(run_all(False, names=["as_found", "platform"], weeks=4, seeds=[4101], workers=1), n_boot=200)["designs"]
        print(json.dumps({n: {k: round(x[k], 1) for k in ("player_days_per_week", "qa_hours_per_week", "cost_eur_per_week")}
                          for n, x in s.items()}, indent=1))
        ok = s["platform"]["player_days_per_week"] < s["as_found"]["player_days_per_week"]
        print("platform: fewer player-days hit than as found:", ok)
        return 0 if ok else 1
    if a.cmd == "evaluate":
        dev = summarize(run_all(False))
        report.write("dev", dev)
        report.charts(dev, ORDER)
        report.readme(ORDER)
        print(json.dumps({n: [x["found_before_release"], x["escaped_money"], round(x["player_days_per_week"]),
                              round(x["qa_hours_per_week"], 1), round(x["cost_eur_per_week"])] for n, x in dev["designs"].items()}))
        return 0
    if a.cmd == "heldout":
        if LOCK.exists():
            print(f"held-out already run: {LOCK.read_text().strip()}", file=sys.stderr)
            return 1
        s = summarize(run_all(True), heldout=True)
        report.write("heldout", s)
        LOCK.write_text(json.dumps({"ran_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "config_sha": _hash(),
                                    "seeds": s["world"]["seeds"]}) + "\n")
        report.readme(ORDER)
        print("held-out:", gate(s) or "gate passed")
        return 0
    if a.cmd == "gate":
        held = report.REPORTS / "heldout.json"
        path = held if held.exists() and not a.dev else report.REPORTS / "dev.json"
        fails = gate(json.loads(path.read_text()))
        print(f"{path.name}: " + ("; ".join(fails) if fails else "gate passed"))
        return 1 if fails else 0
    if a.cmd == "readme":
        changed = report.readme(ORDER, check=a.check)
        if a.check and changed:
            print("README results block is out of date: run python -m raq.eval.cli readme", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
