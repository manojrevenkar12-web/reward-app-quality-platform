"""The designs compared on the same releases, defects and players."""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Design:
    name: str
    label: str
    manual: bool = False             # manual regression checklist on the top devices
    e2e: str = "none"                # none | all | selected | top
    locales: str = "us"              # us | top3
    quarantine: bool = False
    exploratory: bool = False
    risk: str = "learned"            # learned | static
    contracts: bool = False
    ledger: bool = False
    rollout: str = "as_found"        # as_found | staged
    monitoring: str = "daily_crash"  # daily_crash | guardrails
    backend_canary: bool = False
    triage: str = "manual"           # manual | agent


AS_FOUND = Design("as_found", "As found: manual regression on 4 devices, 20% then 100%, daily crash check, support escalates", manual=True)
EVERYTHING = Design("automate_everything", "Automate everything: every E2E test on all 15 device classes, as-found rollout and triage",
                    e2e="all")
PLATFORM = Design("platform", "Platform: risk-based testing on a covering device matrix, contracts, ledger checks, staged rollout "
                              "with guardrails, ticket agent",
                  e2e="selected", locales="top3", quarantine=True, exploratory=True, contracts=True, ledger=True,
                  rollout="staged", monitoring="guardrails", backend_canary=True, triage="agent")

ABLATIONS = [
    replace(PLATFORM, name="platform_static_risk", label="Platform, exploratory time by a fixed ranking, no learned risk", risk="static"),
    replace(PLATFORM, name="platform_top_devices", label="Platform, the 7 most popular devices instead of a covering set", e2e="top"),
    replace(PLATFORM, name="platform_us_only", label="Platform, tests in the US locale only", locales="us"),
    replace(PLATFORM, name="platform_no_contracts", label="Platform, no contract tests", contracts=False),
    replace(PLATFORM, name="platform_no_ledger", label="Platform, no coin-ledger checks", ledger=False),
    replace(PLATFORM, name="platform_no_quarantine", label="Platform, no flaky-test quarantine", quarantine=False),
    replace(PLATFORM, name="platform_no_exploratory", label="Platform, no exploratory testing", exploratory=False),
    replace(PLATFORM, name="platform_no_staged_rollout", label="Platform, 20% then 100% with guardrails", rollout="as_found",
            backend_canary=False),
    replace(PLATFORM, name="platform_no_guardrails", label="Platform, staged rollout but only the daily crash check",
            monitoring="daily_crash"),
    replace(PLATFORM, name="platform_no_ticket_agent", label="Platform, support escalates tickets by hand", triage="manual"),
]

DESIGNS = [AS_FOUND, EVERYTHING, *ABLATIONS, PLATFORM]
BY_NAME = {d.name: d for d in DESIGNS}
ORDER = [d.name for d in DESIGNS]
