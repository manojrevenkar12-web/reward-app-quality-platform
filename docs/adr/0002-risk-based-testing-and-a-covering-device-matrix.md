# 0002: Spend testing where the risk is, on a device matrix that covers what defects key on

**Status:** accepted

**Decision.**
- End-to-end tests (Maestro, Espresso) run on every release, on 7 device classes chosen to cover every maker,
  OS version and low-end tier that many players use, not the 7 most popular models. In the top three locales.
- Exploratory testing, the QA chapter's hands-on time, goes in two-hour blocks to the flows a logistic regression on
  the team's own history ranks riskiest (lines changed, new author, API change, recent defects in the module).
- Contract tests (Pact) between the app and the backend, and a check in staging that every coin balance equals its
  ledger.

**Ablations (development orgs).** The 7 most popular devices instead of a covering set: 11,728 player-days a week
instead of 10,315. A fixed risk ranking instead of the learned one: 11,626. No exploratory testing: 14,474, but
€147 a week cheaper: exploratory time is the one part that costs more than the player value it saves, and it is
kept because it halves the bugs players meet in layout and performance, which the price per player-day undervalues.

**Held-out orgs (run once).** The covering matrix held up (12,281 player-days against 14,177 with the 7 most popular
devices); the learned ranking did not: a fixed ranking found exactly the same defects. Keep the model, but treat
its value as unproven until it has a few months of the team's history.
