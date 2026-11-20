"""One design on one org: every release is planned, tested, rolled out and watched, and every escaped defect is
followed in production until someone finds it and it is fixed.

The engine is the only place that holds both the world and the platform. The platform's components get what
production would give them (changes, test results, counts per segment, ticket texts); the truth about each
defect is used here only to decide what those observations are.
"""
from __future__ import annotations

import math
from collections import Counter, deque

from raq.keyed import uniform
from raq.rollout.guardrail import Check, halt
from raq.sim.designs import Design
from raq.testing.devices import DeviceInfo, select, top_by_share
from raq.testing.flaky import FlakeDetector
from raq.testing.plan import allocate, flow_risk
from raq.testing.risk import RiskModel, features
from raq.triage.clusters import ClusterWatch
from raq.triage.reader import RuleReader
from raq.world.app import AppWorld, Defect, Release
from raq.world.tickets import write

GUARD_METRICS = ("crash", "cashout_fail", "coins_anomaly")
SYMPTOM_SHARE = {"crash": 0.2, "cashout_stuck": 0.25, "coins_wrong": 0.1, "display_broken": 0.15, "slow": 0.15, "error": 0.15}
FLOW_TICKET_SHARE = {"cashout": 0.35, "play_round": 0.2, "offerwall": 0.15, "live_event": 0.1, "login": 0.08,
                     "identity_check": 0.05, "notifications": 0.03, "onboarding": 0.02, "settings": 0.02}


def _stage_share(stages: list[list[float]], h: float) -> float:
    t = 0.0
    for share, dur in stages:
        if dur == 0 or h < t + dur:
            return share
        t += dur
    return stages[-1][0]


def _rollout_hours(stages: list[list[float]]) -> float:
    return float(sum(dur for _, dur in stages))


class Run:
    def __init__(self, world: AppWorld, design: Design, p: dict, value: dict):
        self.w, self.d, self.p, self.v = world, design, p, value
        self.devinfo = [DeviceInfo(x.name, x.platform, x.oem, x.os, x.tier, x.share) for x in world.devices]
        self.flows = list(world.flows)
        self.tests = world.e2e_tests(p["e2e"]["tests_per_flow"])
        rk = p["risk"]
        self.risk = RiskModel(rk["prior"], rk["min_rows"], rk["l2"], learn=design.risk == "learned")
        self.flake = FlakeDetector()
        self.module_flows = {m.name: list(m.flows) for m in world.modules}
        self.found: list[tuple[str, int, float]] = []          # (module, release, hour found)
        self.pending: list[tuple[float, object, int]] = []       # (hour the label is known, features, label)
        self.reader = RuleReader()
        dau = world.cfg["players"]["dau"]
        per_hour = dau / 1000 * world.baseline("tickets") / 24
        self.ticket_base = {(f, s): per_hour * fs * ss for f, fs in FLOW_TICKET_SHARE.items() for s, ss in SYMPTOM_SHARE.items()}

    # --- planning --------------------------------------------------------------------------------------------
    def _recent_found(self, module: str, rel: Release) -> int:
        k = self.p["risk"]["recent_releases"]
        return sum(1 for m, r, h in self.found if m == module and r >= rel.index - k and h <= rel.hour)

    def plan(self, rel: Release) -> dict:
        p, d = self.p, self.d
        for item in [x for x in self.pending if x[0] <= rel.hour]:
            self.risk.add(item[1], item[2])
            self.pending.remove(item)
        self.risk.fit()
        xs = [features(c.lines, c.new_author, c.api_change, self._recent_found(c.module, rel), c.side == "backend") for c in rel.changes]
        preds = [self.risk.predict(x) for x in xs]
        fr = flow_risk([(self.module_flows[c.module], pr) for c, pr in zip(rel.changes, preds, strict=True)])
        manual = top_by_share(self.devinfo, p["manual"]["devices"]) if d.manual else []
        if d.e2e == "all":
            e2e = [x.name for x in self.devinfo]
        elif d.e2e == "selected":
            app_risk = sum(pr for c, pr in zip(rel.changes, preds, strict=True) if c.side == "app")
            e2e = select(self.devinfo, p["devices"], {"android": app_risk, "ios": app_risk * 0.5})
        elif d.e2e == "top":
            e2e = top_by_share(self.devinfo, p["devices"])
        else:
            e2e = []
        locales = ["US"] if d.locales == "us" else list(p["locales"])
        expl = allocate(fr, p["exploratory_hours"], p["exploratory_block_hours"]) if d.exploratory else {}
        return {"xs": xs, "preds": preds, "manual": manual, "e2e": e2e, "locales": locales, "expl": expl,
                "explorers": e2e or manual, "risk_learned": self.risk.learned}

    # --- before release --------------------------------------------------------------------------------------
    def test(self, rel: Release, plan: dict) -> dict:
        p, d, w = self.p, self.d, self.w
        team = p["team"]["qa_engineers"] * p["team"]["hours_per_day"]
        qa, wall, dev_min, reds, glances = 0.0, 0.0, 0.0, 0, 0
        if d.manual:
            h = len(self.flows) * len(plan["manual"]) * p["manual"]["minutes_per_flow_device"] / 60
            qa += h
            wall = max(wall, 24 * h / team)
        if plan["e2e"]:
            e = p["e2e"]
            dev_min = len(self.tests) * len(plan["e2e"]) * e["minutes_per_test"] * (1 + e["extra_locale_share"] * (len(plan["locales"]) - 1))
            for t in self.tests:
                for dev in plan["e2e"]:
                    if not w.flipped(t, rel.index, dev, 0):
                        if d.quarantine:
                            self.flake.observe(t, False, rel.index)
                        continue
                    passed = any(not w.flipped(t, rel.index, dev, a) for a in range(1, e["max_reruns"] + 1))
                    if d.quarantine:
                        self.flake.observe(t, True, rel.index)
                    if self.flake.blocking(t):
                        glances += 1
                        reds += int(not passed)
            touched = {f for c in rel.changes if c.side == "app" for f in self.module_flows[c.module]}
            maint = len(touched) * e["maintenance_hours_per_flow"] * (1 + e["maintenance_per_device"] * len(plan["e2e"]))
            qa += reds * e["investigate_hours"] + glances * e["glance_hours"] + maint
            wall = max(wall, e["wall_hours"] + reds * e["investigate_hours"])
        if plan["expl"]:
            h = sum(plan["expl"].values())
            qa += h
            wall += 24 * h / team
        if d.contracts:
            wall += p["contracts"]["wall_hours"]
        found, escaped = [], []
        for x in rel.defects:
            (found if self._caught(x, plan) else escaped).append(x)
        return {"qa": qa, "wall": wall, "device_minutes": dev_min, "reds": reds, "glances": glances, "found": found, "escaped": escaped}

    def _caught(self, x: Defect, plan: dict) -> bool:
        w, d, p = self.w, self.d, self.p

        def covers(devs):
            return any(n in x.devices for n in devs)

        def local(locs):
            return x.region is None or x.region in locs

        layers = []
        if plan["manual"] and covers(plan["manual"]) and local(["US"]):
            layers.append(("manual", w.sensitivity("manual", x.kind)))
        if plan["e2e"] and covers(plan["e2e"]) and local(plan["locales"]):
            pe = w.sensitivity("e2e", x.kind)
            # a defect makes its test fail on every retry, and a quarantined test that fails every retry still blocks,
            # so quarantine costs no detection here; it only stops fail-then-pass flakes from blocking
            layers.append(("e2e", pe))
        h = plan["expl"].get(x.flow, 0.0)
        if h and covers(plan["explorers"]) and local(plan["locales"]):
            layers.append(("exploratory", 1 - (1 - w.sensitivity("exploratory", x.kind)) ** (h / p["exploratory_block_hours"])))
        if d.contracts and x.side == "backend":
            layers.append(("contract", w.sensitivity("contract", x.kind)))
        if d.ledger and plan["e2e"]:
            layers.append(("ledger", w.sensitivity("ledger", x.kind)))
        return any(w.caught(x, layer, pr) for layer, pr in layers if pr > 0)

    # --- production ------------------------------------------------------------------------------------------
    def stages(self, side: str) -> list[list[float]]:
        if side == "backend":
            c = self.p["rollout"]["backend_canary"]
            return [[c[0], c[1]], [1.0, 0]] if self.d.backend_canary else [[1.0, 0]]
        return self.p["rollout"]["staged" if self.d.rollout == "staged" else "as_found"]

    def follow(self, x: Defect, go_live: float) -> dict:
        """Hour by hour after go-live: who the defect reaches, what each channel sees, when it is found and fixed."""
        w, p, d = self.w, self.p, self.d
        prod = w.cfg["production"]
        dau = w.cfg["players"]["dau"]
        reach = w.reach(x)
        stages = self.stages(x.side)
        app = x.side == "app"
        cap = int(prod["undetected_cap_hours"])
        every = p["rollout"]["check_every_hours"]
        n_tests = len(self.devinfo) * len(GUARD_METRICS) if app else 2 * len(GUARD_METRICS)
        watch = None
        if d.triage == "agent":
            a = p["triage"]["agent"]
            watch = ClusterWatch(self.ticket_base, a["window_hours"], a["alpha"], a["min_count"])
        day_tickets: deque[int] = deque(maxlen=24)
        crash_day: deque[float] = deque(maxlen=24)
        td, channel, frozen = None, None, None
        pd, tickets, read_ok, read_n = 0.0, 0, 0, 0
        end = None
        inf = float("inf")
        for h in range(cap + 1):
            normal = _stage_share(stages, h) * (w.adoption(h) if app else 1.0)
            if td is None or h < td:
                share = normal
            else:
                if frozen is None:
                    frozen = normal                 # the rollout halts (app) or is rolled back (backend) at detection
                fix = prod["hotfix_hours"] if app else prod["backend_rollback_hours"]
                ramp = prod["hotfix_adoption_hours"] if app else 0.0
                since = h - td
                if since < fix:
                    share = frozen
                elif ramp and since < fix + ramp:
                    share = frozen * (1 - (since - fix) / ramp)
                else:
                    end = h
                    break
            pd_h = dau * reach * share / 24
            pd += pd_h
            if td is not None and h >= td:
                continue
            found_at: list[tuple[float, str]] = []
            # tickets from affected players
            n = w.observe((x.id, "tickets", h), pd_h * w.excess(x, "tickets") / 1000)
            tickets += n
            if d.triage == "manual":
                vague = sum(1 for i in range(n) if uniform(w.seed, "vague", x.id, h, i) < 0.12)
                day_tickets.append(n - vague)
                if sum(day_tickets) >= p["triage"]["manual"]["escalate_per_day"]:
                    m = p["triage"]["manual"]
                    z = _probit(uniform(w.seed, "escalation", x.id))
                    found_at.append((h + m["delay_median_hours"] * math.exp(m["delay_sd"] * z), "support"))
            else:
                counts: Counter = Counter()
                sym = prod["ticket_symptoms"][x.kind]
                for i in range(min(n, p["triage"]["agent"]["max_read_per_hour"])):
                    dev = x.devices[int(uniform(w.seed, "tdev", x.id, h, i) * len(x.devices))]
                    t = write(w.seed, (x.id, h, i), x.flow, sym, dev, x.region or "US", f"v{x.release}")
                    rd = self.reader.read(t.text)
                    read_n += 1
                    read_ok += int(rd.flow == x.flow and rd.symptom == sym)
                    if rd.flow and rd.symptom:
                        counts[(rd.flow, rd.symptom)] += 1
                for pair in set(counts) | set(watch._hist):
                    counts[pair] += w.observe((x.id, "bg", pair, h), self.ticket_base.get(pair, 0.0))
                if watch.add_hour(dict(counts)):
                    found_at.append((h + p["triage"]["agent"]["review_qa_hours"], "ticket_agent"))
            # crash reporting, looked at once a day
            crash_day.append(pd_h * w.excess(x, "crash") / 1000)
            if int((go_live + h) % 24) == p["daily_crash_check"]["hour_of_day"] and sum(crash_day) > 0:
                k = w.observe((x.id, "crashday", h), sum(crash_day))
                if k >= p["daily_crash_check"]["min_crashes"]:
                    found_at.append((h, "crash_report"))
            # guardrails on segments of the new version
            if d.monitoring == "guardrails" and h % every == every - 1 and h <= p["rollout"]["watch_hours"] and share > 0:
                checks = self._segments(x, h, share, every, app)
                if checks and halt(checks, p["rollout"]["alpha"], n_tests):
                    found_at.append((h, "guardrail"))
            for when, ch in found_at:
                if when < (td if td is not None else inf):
                    td, channel = when, ch
        detected = td is not None
        return {"player_days": pd, "detected": detected, "detect_hours": td if detected else None, "channel": channel or "none",
                "tickets": tickets, "read": read_n, "read_ok": read_ok, "end": end if end is not None else cap,
                "reach_at_detect": frozen if frozen is not None else None}

    def _segments(self, x: Defect, h: int, share: float, window: int, app: bool) -> list[Check]:
        w = self.w
        dau = w.cfg["players"]["dau"]
        flow_part = w.flows[x.flow]["usage"] * w.region_share(x.region)
        checks = []
        if app:
            for dev in self.devinfo:
                if dev.name not in x.devices:
                    continue                      # segments without the defect only add Bonferroni weight (n_tests)
                seg_pd = dau * dev.share * share * window / 24
                for m in GUARD_METRICS:
                    ex = w.excess(x, m)
                    if ex == 0:
                        continue
                    base = seg_pd * w.baseline(m) / 1000
                    obs = w.observe((x.id, "guard", h, dev.name, m), base + seg_pd * flow_part * ex / 1000)
                    checks.append(Check(f"{m}|{dev.name}", obs, base))
        else:
            old = w.cfg["production"]["old_version_share"]
            for version, vshare in (("new", 1 - old), ("old", old)):
                if x.kind == "contract_break" and version == "new":
                    continue
                seg_pd = dau * vshare * share * window / 24
                dev_part = w.device_share(x.devices)
                for m in GUARD_METRICS:
                    ex = w.excess(x, m)
                    if ex == 0:
                        continue
                    base = seg_pd * w.baseline(m) / 1000
                    obs = w.observe((x.id, "guard", h, version, m), base + seg_pd * flow_part * dev_part * ex / 1000)
                    checks.append(Check(f"{m}|{version}", obs, base))
        return checks

    # --- one release -----------------------------------------------------------------------------------------
    def release(self, rel: Release) -> dict:
        p, v = self.p, self.v
        plan = self.plan(rel)
        t = self.test(rel, plan)
        go_live = rel.hour + t["wall"]
        out = {"release": rel.index, "week": rel.index // self.w.cfg["releases_per_week"], "defects": len(rel.defects),
               "found": len(t["found"]), "escaped": len(t["escaped"]), "qa_hours": t["qa"], "device_minutes": t["device_minutes"],
               "reds": t["reds"], "flaky_failures": t["glances"], "eng_hours": len(t["found"]) * v["fix_before_release_engineer_hours"], "player_days": 0.0,
               "player_eur": 0.0, "escaped_money": 0, "money_player_days": 0.0, "detect_hours": [], "channels": Counter(),
               "undetected": 0, "tickets": 0, "read": 0, "read_ok": 0, "halts": 0, "risk_learned": plan["risk_learned"],
               "quarantined": len(self.flake.quarantined), "devices": len(plan["e2e"] or plan["manual"])}
        found_modules = {x.module for x in t["found"]}
        for x in t["found"]:
            self.found.append((x.module, rel.index, rel.hour + t["wall"]))
        detected_at: dict[str, float] = {}
        for x in t["escaped"]:
            f = self.follow(x, go_live)
            cost = f["player_days"] * v["eur_per_affected_player_day"][x.kind]
            out["player_days"] += f["player_days"]
            out["player_eur"] += cost
            out["tickets"] += f["tickets"]
            out["read"] += f["read"]
            out["read_ok"] += f["read_ok"]
            if x.money:
                out["escaped_money"] += 1
                out["money_player_days"] += f["player_days"]
            out["channels"][f["channel"]] += 1
            if f["detected"]:
                out["detect_hours"].append(f["detect_hours"])
                detected_at[x.module] = go_live + f["detect_hours"]
                self.found.append((x.module, rel.index, go_live + f["detect_hours"]))
                out["eng_hours"] += v["hotfix_engineer_hours"] if x.side == "app" else v["rollback_engineer_hours"]
                out["qa_hours"] += (p["triage"]["manual"]["repro_qa_hours"] if f["channel"] == "support"
                                    else p["triage"]["agent"]["review_qa_hours"] if f["channel"] == "ticket_agent" else 1.0)
                if f["channel"] == "guardrail" and x.side == "app":
                    out["halts"] += 1
            else:
                out["undetected"] += 1
        # labels for the risk model: known once a defect is found, or after a quiet watch period
        watch = p["rollout"]["watch_hours"]
        for c, xv in zip(rel.changes, plan["xs"], strict=True):
            if c.module in found_modules:
                self.pending.append((rel.hour + t["wall"], xv, 1))
            elif c.module in detected_at:
                self.pending.append((detected_at[c.module], xv, 1))
            else:
                self.pending.append((go_live + watch, xv, 0))
        stages = self.stages("app")
        rounds = int(_rollout_hours(stages) // p["rollout"]["check_every_hours"]) if self.d.monitoring == "guardrails" else 0
        false_halts = sum(1 for i in range(rounds) if uniform(self.w.seed, "false-halt", rel.index, i) < p["rollout"]["alpha"])
        out["false_halts"] = false_halts
        out["qa_hours"] += false_halts * p["rollout"]["false_halt_qa_hours"]
        out["lead_hours"] = t["wall"] + _rollout_hours(stages) + false_halts * p["rollout"]["false_halt_hours"]
        return out


def _probit(u: float) -> float:
    from statistics import NormalDist

    return NormalDist().inv_cdf(min(max(u, 1e-9), 1 - 1e-9))


def run(world: AppWorld, design: Design, p: dict, value: dict) -> list[dict]:
    r = Run(world, design, p, value)
    return [r.release(rel) for rel in world.releases]
