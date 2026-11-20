"""Generated reports: the README results block and the charts. Never edited by hand."""
from __future__ import annotations

import json

from raq.config import ROOT

REPORTS = ROOT / "reports"
CHARTS = REPORTS / "charts"
README = ROOT / "README.md"
START, END = "<!-- results:start -->", "<!-- results:end -->"
AS_FOUND, EVERYTHING, PLATFORM, ABLATION = "#eb6834", "#1baf7a", "#2a78d6", "#A3A9A6"   # validated: colour-blind safe, all pairs
INK, MUTED, SURFACE = "#1F2430", "#5E6573", "#FCFCFB"
FONT = 'font-family="Inter, system-ui, sans-serif"'


def load(name: str) -> dict | None:
    p = REPORTS / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def write(name: str, obj: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")


def _n(x: float | None, d: int = 0) -> str:
    return "–" if x is None else f"{x:,.{d}f}"


def _svg(w: int, h: int, title: str, sub: str, body: list[str]) -> str:
    return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" {FONT} role="img" aria-label="{title}">',
                      f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>',
                      f'<text x="20" y="28" font-size="15" font-weight="600" fill="{INK}">{title}</text>',
                      f'<text x="20" y="46" font-size="12" fill="{MUTED}">{sub}</text>', *body, "</svg>"]) + "\n"


def _colour(n: str) -> str:
    return {"platform": PLATFORM, "as_found": AS_FOUND, "automate_everything": EVERYTHING}.get(n, ABLATION)


def chart_bars(s: dict, order: list[str], key: str, ci: str | None, title: str, sub: str, unit: str, prefix: str = "") -> str:
    d = s["designs"]
    rows = [n for n in order if n in d]
    W, L, R, T, rh = 800, 340, 90, 62, 26
    H = T + rh * len(rows) + 20
    vmax = max(max(d[n][key], (d[n][ci][1] if ci else 0)) for n in rows) * 1.05 or 1

    def X(v):
        return L + (W - L - R) * v / vmax

    body = []
    for i, n in enumerate(rows):
        y = T + i * rh
        wt = ' font-weight="600"' if n == "platform" else ""
        body.append(f'<text x="{L - 10}" y="{y + 15}" font-size="12" text-anchor="end" fill="{INK}"{wt}>{d[n]["label"].split(":")[0]}</text>')
        body.append(f'<rect x="{L}" y="{y + 5}" width="{max(X(d[n][key]) - L, 1):.1f}" height="14" rx="3" fill="{_colour(n)}"/>')
        right = X(d[n][key])
        if ci:
            lo, hi = d[n][ci]
            body.append(f'<line x1="{X(lo):.1f}" x2="{X(hi):.1f}" y1="{y + 12}" y2="{y + 12}" stroke="{INK}" stroke-width="1.5"/>')
            right = max(right, X(hi))
        body.append(f'<text x="{right + 8:.1f}" y="{y + 16}" font-size="11" fill="{MUTED}">{prefix}{_n(d[n][key])} {unit}</text>')
    return _svg(W, H, title, sub, body)


def charts(s: dict, order: list[str]) -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    (CHARTS / "player_days.svg").write_text(chart_bars(
        s, order, "player_days_per_week", "player_days_ci", "Player-days hit by escaped defects, per week",
        "Players a defect reached, times the days it reached them; 95% intervals over org-weeks", ""))
    (CHARTS / "cost.svg").write_text(chart_bars(
        s, order, "cost_eur_per_week", None, "Cost of quality per week",
        "Lost player value, QA and engineering time, device farm; same releases and players for every design", "", "€"))


COLS = (("platform", "Platform"), ("automate_everything", "Automate everything"), ("as_found", "As found"))


def _headline(s: dict, title: str) -> list[str]:
    d = s["designs"]
    cols = [(n, lab) for n, lab in COLS if n in d]
    rows = [
        ("Defects found before release", lambda x: f"{x['found_before_release']} of {x['defects']}"),
        ("Defects in coins or cash-outs that reached players", lambda x: str(x["escaped_money"])),
        ("Player-days hit by escaped defects, per week (95% interval)",
         lambda x: f"{_n(x['player_days_per_week'])} ({_n(x['player_days_ci'][0])}–{_n(x['player_days_ci'][1])})"),
        ("... of them in money flows", lambda x: _n(x["money_player_days_per_week"])),
        ("Median hours to find an escaped defect", lambda x: _n(x["detect_hours_median"], 1)),
        ("Escaped defects nobody found within two weeks", lambda x: str(x["undetected"])),
        ("QA hours per week", lambda x: _n(x["qa_hours_per_week"], 1)),
        ("Flaky test failures per week", lambda x: _n(x["flaky_failures_per_week"], 1)),
        ("Device farm per week", lambda x: f"€{x['device_eur_per_week']:,.0f}"),
        ("Median hours from code freeze to every player", lambda x: _n(x["lead_hours_median"], 1)),
        ("Rollouts halted by a guardrail (false halts)", lambda x: f"{x['halts']} ({x['false_halts']})"),
        ("Cost of quality per week", lambda x: f"€{x['cost_eur_per_week']:,.0f}"),
    ]
    out = [f"| {title} | " + " | ".join(lab for _, lab in cols) + " |", "|---|" + "---:|" * len(cols)]
    for lab, f in rows:
        out.append(f"| {lab} | " + " | ".join(("**" + f(d[n]) + "**") if n == "platform" else f(d[n]) for n, _ in cols) + " |")
    w = s["world"]
    out += ["", f"{w['orgs']} simulated orgs, {w['weeks']} weeks each, {w['dau']:,} daily players: {w['releases']} releases, "
                f"{w['changes']:,} module changes, {w['defects']} defects."]
    return out


def _designs(s: dict, order: list[str]) -> list[str]:
    d = s["designs"]
    out = ["| Design | Found before release | Money defects escaped | Player-days / wk | QA h / wk | Lead h | Cost / wk |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for n in order:
        if n in d:
            x = d[n]
            b = "**" if n == "platform" else ""
            out.append(f"| {b}{x['label'].split(':')[0]}{b} | {x['found_before_release']} of {x['defects']} | {x['escaped_money']} | "
                       f"{_n(x['player_days_per_week'])} | {_n(x['qa_hours_per_week'], 1)} | {_n(x['lead_hours_median'], 1)} | "
                       f"€{x['cost_eur_per_week']:,.0f} |")
    return out


def readme(order: list[str], check: bool = False) -> bool:
    from raq.eval.gate import gate

    dev, ho = load("dev"), load("heldout")
    if dev is None:
        block = f"{START}\n_No results yet: run `python -m raq.eval.cli evaluate`._\n{END}"
    else:
        lines = [START, "", "### Dashboard (development orgs)", "", *_headline(dev, "Development"), "",
                 "![Player-days hit per week](reports/charts/player_days.svg)", "",
                 "![Cost of quality per week](reports/charts/cost.svg)", "", "### Every design on the same orgs", "", *_designs(dev, order)]
        if ho:
            fails = gate(ho)
            lines += ["", "### Held-out orgs (run once)", "", *_headline(ho, "Held-out"), "",
                      "Gate (`config/gate.yaml`) on the held-out orgs: " +
                      ("**passed**." if not fails else "**not passed**: " + "; ".join(fails) + "."),
                      "", "The record of that run: [docs/heldout.md](docs/heldout.md)."]
        lines += ["", END]
        block = "\n".join(lines)
    text = README.read_text()
    a, b = text.index(START), text.index(END) + len(END)
    new = text[:a] + block + text[b:]
    changed = new != text
    if changed and not check:
        README.write_text(new)
    return changed
