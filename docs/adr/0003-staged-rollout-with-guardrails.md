# 0003: Roll out in stages and halt on guardrails per device class

**Status:** accepted

**Decision.** App releases go to 1%, 10%, 50% and then everyone, 12 hours a stage; backend deploys go to a 10%
canary for two hours. Every two hours, per device class on the new version, crashes, failed cash-outs and coin
anomalies are compared with that segment's baseline (one-sided Poisson test, Bonferroni over 45 segment-metrics,
alpha 0.001). A failing check halts the rollout.

**Trade-off.** The median release reaches every player 44 hours after code freeze instead of 39 as found. In
exchange, a bug found at 1% has reached 1% of its players. Without staging, player-days rise from 10,315 to 13,819
a week; without guardrails (daily crash check only), to 13,935.
