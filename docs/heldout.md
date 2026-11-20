# The held-out run

Run once on 20 November 2026 (`config/heldout.lock`: seeds 4201–4203, config hash `cc91fabe6296a106`), after the
development evaluation passed its gate and nothing in `config/` or `raq/` changed afterwards.

**Gate: passed.** Against the app as found, on the held-out orgs (91 defects in 72 releases):

| | As found | Platform |
|---|---:|---:|
| Defects found before release | 30 of 91 | 69 of 91 |
| Defects in coins or cash-outs that reached players | 29 | 3 |
| Player-days hit a week | 161,520 | 12,281 |
| QA hours a week | 32.8 | 17.8 |
| Median hours from code freeze to every player | 39.0 | 43.7 |
| Cost of quality a week | €70,947 | €3,028 |

## What was worse than on the development orgs

- **Escaped defects were found more slowly**: a median of 35.5 hours against 19 on the development orgs, and 7 of
  22 escaped defects were never found within two weeks (as found: 13 of 61). Most of them are layout and
  performance bugs in small segments (one maker, one locale), which neither guardrails nor ticket counts see.
- **The learned risk model added nothing here**: the platform with a fixed ranking found exactly the same defects
  (12,281 player-days both). On the development orgs it helped a little (10,315 against 11,626). The model needs more
  history than 24 releases to beat a sensible prior; the claim in ADR 0002 is weaker than it looked.
- **The ticket agent was worth less**: without it, 32,988 player-days a week instead of 12,281 (development: 39,460
  against 10,315). Still the largest single part.

## Changes after the run

None so far. Anything changed from here on is listed here, and the held-out numbers are not re-run.
