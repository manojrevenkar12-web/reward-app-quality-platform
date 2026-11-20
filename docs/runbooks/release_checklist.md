# Runbook: cutting a release

1. Plan it: list the changes in the dashboard's "Plan a release" (or `POST /api/plan`). It returns the flows at risk,
   the device matrix, where the exploratory hours go, and the contract suites that must pass.
2. CI must be green: Pact contracts verified against the backend, Espresso and Maestro on the emulator, end-to-end
   tests on the device matrix. A quarantined flaky test that fails every retry still blocks.
3. Exploratory sessions on the planned flows, notes in the release ticket.
4. Backend first, through its 10% canary; then the app at 1%. Do not skip stages for a hotfix: start at 10%.
