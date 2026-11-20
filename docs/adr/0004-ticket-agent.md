# 0004: A ticket agent turns player tickets into bug reports; it labels, a count test decides

**Status:** accepted

**Context.** Players report what tests miss, in English, German and French, with typos, and often vaguely. Support
escalating by hand takes days, and by then a stuck cash-out has reached many players.

**Decision.** A reader labels each ticket with a flow and a symptom (keyword rules in the evaluation, so it is free
and repeatable; Claude when `RAQ_READER=claude` and an API key are set, with its answer checked against the
allowed labels and the rules as fallback). Code counts labels per pair in a six-hour window and files a bug when the
count is improbably high for that pair (Poisson, Bonferroni over pairs). Ticket text is data: an instruction inside
a ticket changes nothing.

**Result (development orgs).** Without the agent, support escalating by hand, player-days rise from 10,315 to
39,460 a week: the largest single part of the platform. The rule reader labels 73% of tickets exactly right,
vague ones included.

**Limit.** The reader's lexicon was written against the simulated tickets' phrasing; real tickets will read worse.
That is the case for the Claude reader in production, measured against a labelled sample first.
