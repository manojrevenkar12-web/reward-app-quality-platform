# 0001: Measure QA designs on simulated releases, with the same luck for every design

**Status:** accepted

**Context.** Arguments about testing are usually about effort ("we need more automation", "manual is safer"). What
matters to a rewarded-gaming app is how many players meet a bug, how much money moves wrongly, and what the
team spends to prevent it.

**Decision.** A simulated app (`raq/world`) with hidden truth: which changes carry defects, what kind (crash, layout,
slowness, a stuck cash-out, coins credited twice, a backend change that breaks older app versions), on which
device makers, OS versions and regions they show, and what players write when they meet them. Every design runs
on the same draws. Development seeds for tuning, held-out seeds run once. The headline is player-days hit by
escaped defects, with the cost of quality per week beside it: lost player value (priced from revenue per daily
player), QA and engineering time, and the device farm.

**Consequences.** Every number is about the simulated app; the README says so. Detection rates of each kind of
test are assumptions in `config/world.yaml`; the ablations show which part of the platform carries the result.
