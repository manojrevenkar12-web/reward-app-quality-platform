# SKILLS.md

Repeatable tasks, each with the command and how to know it worked.

## Evaluate after a change

`python -m raq.eval.cli evaluate`, then `python -m raq.eval.cli gate --dev`. Commit `reports/` and the README
together; CI fails if they do not match a fresh run.

## Add an ablation

1. Add a `Design` in `raq/sim/designs.py` that switches one thing off, in `DESIGNS`.
2. Add its short name in `web/src/shared/format.ts` (`ORDER`, `NAME`).
3. Evaluate; the README table and the dashboard pick it up.

## Add a contract interaction

1. Add a `@Pact` method and a test in `mobile/api-client/src/test/.../RewardsApiPactTest.kt`.
2. If it needs a provider state, add a `@State` method in `mobile/backend/src/test/.../ProviderContractTest.kt`.
3. `gradle :api-client:test :backend:test`: the consumer writes the contract, the backend must pass it.

## Add an end-to-end flow

Add a YAML file to `mobile/maestro/` (one flow per file, `clearState: true`, wait on visible text rather than
sleeps). For a check that needs the backend's answer, write an Espresso test in `mobile/app/src/androidTest/`.

## Teach the ticket reader a word

Add the pattern to `FLOW_LEX` or `SYMPTOM_LEX` in `raq/triage/reader.py` and a case to
`tests/test_rollout_and_triage.py`. Evaluate: `reader_accuracy` in the report should rise, and the platform's
hours to find escaped defects should not.

## Change the rollout or a guardrail

Stages, check interval and alpha are in `config/platform.yaml` (`rollout`). Evaluate and compare
`lead_hours_median` (slower rollouts) with player-days and false halts.

## Refresh the dashboard screenshots

Start `uvicorn raq.service.api:app --port 8098`, open each view and save to `docs/screenshots/`.
