"""The dashboard's API: the generated reports, a release planner and the ticket reader.

- `GET /health`
- `GET /api/results`: the development report, the held-out report (once run) and the gate on each.
- `GET /api/catalogue`: modules, flows and device classes, for the planner's form.
- `POST /api/plan`: a release's changes; risk per change, risk per flow, the device matrix, where the exploratory
  hours go, which contract suites must pass and the rollout stages.
- `POST /api/triage`: a player ticket; the flow and symptom the reader finds. Ticket text is data, never instructions.
The built dashboard (web/dist) is served at `/`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from raq.config import ROOT, load
from raq.eval.gate import gate
from raq.testing.devices import DeviceInfo, select
from raq.testing.plan import allocate, flow_risk
from raq.testing.risk import RiskModel, features
from raq.triage.reader import default_reader

REPORTS = ROOT / "reports"
app = FastAPI(title="reward-app-quality-platform", version="1.0.0")
CAT, PLATFORM = load("catalogue"), load("platform")
MODULES = {m["name"]: m for m in CAT["modules"]}
READER = default_reader()


def _report(name: str) -> dict | None:
    p = REPORTS / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


@app.get("/health")
def health() -> dict:
    return {"ok": True, "reports": sorted(p.stem for p in REPORTS.glob("*.json"))}


@app.get("/api/results")
def results() -> dict:
    dev, held = _report("dev"), _report("heldout")
    if dev is None:
        raise HTTPException(503, "No report yet: run python -m raq.eval.cli evaluate.")
    return {"dev": dev, "heldout": held, "gate": {"dev": gate(dev), "heldout": gate(held) if held else None}}


@app.get("/api/catalogue")
def catalogue() -> dict:
    return {"modules": CAT["modules"], "flows": CAT["flows"], "devices": CAT["devices"]}


class ChangeIn(BaseModel):
    module: str
    lines: int = Field(ge=1, le=100_000)
    api_change: bool = False
    new_author: bool = False
    recent_found: int = Field(default=0, ge=0, le=50)


class PlanIn(BaseModel):
    changes: list[ChangeIn] = Field(min_length=1, max_length=40)


@app.post("/api/plan")
def plan(req: PlanIn) -> dict:
    unknown = [c.module for c in req.changes if c.module not in MODULES]
    if unknown:
        raise HTTPException(422, f"Unknown module: {', '.join(unknown)}. Pick one from the catalogue.")
    rk = PLATFORM["risk"]
    model = RiskModel(rk["prior"], rk["min_rows"], rk["l2"])
    rows = []
    for c in req.changes:
        m = MODULES[c.module]
        p = model.predict(features(c.lines, c.new_author, c.api_change and m["side"] == "backend", c.recent_found, m["side"] == "backend"))
        rows.append({"module": c.module, "side": m["side"], "flows": m["flows"], "risk": round(p, 4)})
    fr = flow_risk([(r["flows"], r["risk"]) for r in rows])
    devs = [DeviceInfo(**d) for d in CAT["devices"]]
    app_risk = sum(r["risk"] for r in rows if r["side"] == "app")
    matrix = select(devs, PLATFORM["devices"], {"android": app_risk, "ios": app_risk * 0.5})
    hours = allocate(fr, PLATFORM["exploratory_hours"], PLATFORM["exploratory_block_hours"])
    contracts = sorted({r["module"] for r in rows if r["side"] == "backend"})
    shares = {d.name: d.share for d in devs}
    return {"changes": rows, "flows": {f: round(v, 4) for f, v in sorted(fr.items(), key=lambda kv: -kv[1])},
            "devices": [{"name": n, "share": shares[n]} for n in matrix],
            "device_share": round(sum(shares[n] for n in matrix), 3),
            "exploratory": hours, "contracts": contracts, "rollout": PLATFORM["rollout"]["staged"],
            "model": "prior (the platform refits it on the team's own found defects once it has 40 changes)"}


class TicketIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@app.post("/api/triage")
def triage(req: TicketIn) -> dict:
    r = READER.read(req.text)
    return {"flow": r.flow, "symptom": r.symptom, "source": r.source}


_dist = Path(os.environ.get("RAQ_WEB_DIST", ROOT / "web" / "dist"))
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="web")
