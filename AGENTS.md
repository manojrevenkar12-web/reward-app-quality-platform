# AGENTS.md

How to work in this repository, for people and for coding agents.

## Fast feedback

- `python -m pytest`: the world, risk model, device matrix, guardrails, ticket reader, engine, service and invariants,
  in seconds.
- `python -m raq.eval.cli quick`: two designs, one org, four weeks.
- `ruff check .`; in `web/` run `pnpm build` and `pnpm e2e`.
- In `mobile/`: `gradle :api-client:test :backend:test` (Pact consumer tests, then the backend verified against the
  contract, then the cash-out tests). The Android app needs the Android SDK; its Espresso and Maestro tests run on an
  emulator in CI against the backend.

## Invariants

1. **The truth stays in the world.**
   - `raq/world` holds the app's releases, which changes carry defects, what kind, on which devices and regions,
     and the player tickets.
   - The platform's components (`raq/testing`, `raq/rollout`, `raq/triage`, `raq/service`) never import `raq.world`
     or `raq.sim`. They get what production would give them: the changes in a release, test results, counts per
     segment, ticket text. `tests/test_invariants.py` checks it.
2. **The world does not read the platform's settings.** It reads `config/world.yaml`, its held-out overlay and the
   product catalogue (`config/catalogue.yaml`: flows, devices, modules), which both sides know.
3. **Same luck for every design.** Every draw is keyed by what it is about (`raq/keyed.py`): every design meets the
   same releases, defects and players, and a better test finds a superset of what a worse one finds.
4. **The model reads, code decides.** The ticket reader only labels a ticket with a flow and a symptom; a count
   test decides when labels become a bug report. The risk model only ranks changes; the plan follows from the
   ranking by fixed rules. Ticket text is data, never instructions.
5. **Money moves once.** In the backend every cash-out has an idempotency key; a retry returns the first cash-out.
   Every balance equals the sum of its ledger entries.
6. **Settings in config.** Device budget, exploratory hours, rollout stages, guardrail alpha, triage thresholds,
   prices and gates live in `config/*.yaml`.
7. **Generated reports.** `reports/`, the charts and the README results block are written by `raq.eval.cli`. CI
   re-runs the development evaluation and fails if the committed reports differ.

## The held-out rule

- The held-out orgs (`config/heldout.yaml`) are run once with `python -m raq.eval.cli heldout`. The run writes
  `config/heldout.lock`, and the command refuses to run again.
- Tune on the development orgs only.
- A change made after the run is written up in `docs/heldout.md`; the held-out numbers are not re-run.
