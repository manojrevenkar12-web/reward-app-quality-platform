# Runbook: a rollout halted on a guardrail

The staged rollout stopped because a segment on the new version (device class × metric) saw improbably many
crashes, failed cash-outs or odd coin balances.

1. Read the halt: which segment and metric, observed against expected. One segment usually means one maker or OS
   version: reproduce on that device class in the farm first.
2. Crashes: the crash reporter's top new signature for that version and device. Failed cash-outs: the payout
   service's errors by app version. Coin anomalies: `/v1/ledger/check`, then the ledger entries for affected players.
3. Real defect: keep the rollout halted, fix, ship a hotfix through the same stages. A money defect also needs the
   affected players' ledgers corrected by migration, never by hand.
4. No defect found within two hours: it may be a false halt (about one in a thousand checks). Resume the stage and
   record it; three false halts in a month means the baseline for that segment needs a look.
