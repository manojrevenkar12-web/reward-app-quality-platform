# 0005: Cash-outs are idempotent and coins are a ledger

**Status:** accepted

**Decision.** The backend keys every cash-out by (player, idempotency key); the app creates the key when the player
taps and reuses it on a retry, and disables the button while a request is in flight. Coins are ledger entries; a
balance is their sum, and `/v1/ledger/check` verifies it. The contract between app and backend includes the replayed
cash-out (200 with the first cash-out), so a backend change cannot quietly drop it.

**Checked for real.** Backend tests send twenty concurrent cash-outs with one key and see one payout; the Maestro
flow double-taps "Cash out" on an emulator against the running backend and sees one dollar leave.
