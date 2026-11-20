package com.rewardapp.backend

import java.util.UUID

data class LedgerEntry(val playerId: String, val delta: Long, val reason: String)

sealed interface CashoutResult {
    data class Created(val cashout: CashoutBody) : CashoutResult
    data class Replayed(val cashout: CashoutBody) : CashoutResult
    data object NotEnoughCoins : CashoutResult
    data object NoSuchPlayer : CashoutResult
    data class KeyReused(val reason: String) : CashoutResult
}

/**
 * Players' coins as a ledger: every change is an entry, the balance is their sum, and a cash-out is keyed by
 * (player, idempotency key) so a retry after a lost response returns the first cash-out instead of paying again.
 * In memory here; the same rules hold on a database with a unique index on (player, key).
 */
class Store(val coinsPerRound: Long = 250, val coinsPerCent: Long = 10) {
    private val balances = HashMap<String, Long>()
    private val ledger = ArrayList<LedgerEntry>()
    private val cashouts = LinkedHashMap<Pair<String, String>, Pair<Long, CashoutBody>>()   // key -> (amount, response)

    @Synchronized
    fun reset() {
        balances.clear()
        ledger.clear()
        cashouts.clear()
    }

    @Synchronized
    fun newPlayer(id: String = "p-" + UUID.randomUUID().toString().take(8), coins: Long = 0): String {
        balances[id] = 0
        if (coins != 0L) credit(id, coins, "seed")
        return id
    }

    @Synchronized
    fun coins(id: String): Long? = balances[id]

    @Synchronized
    fun round(id: String): RoundBody? {
        if (id !in balances) return null
        credit(id, coinsPerRound, "round")
        return RoundBody(balances.getValue(id), coinsPerRound)
    }

    @Synchronized
    fun cashout(id: String, key: String, amountCents: Long): CashoutResult {
        if (id !in balances) return CashoutResult.NoSuchPlayer
        cashouts[id to key]?.let { (amount, body) ->
            return if (amount == amountCents) CashoutResult.Replayed(body) else CashoutResult.KeyReused("key already used for another amount")
        }
        val cost = amountCents * coinsPerCent
        if (balances.getValue(id) < cost) return CashoutResult.NotEnoughCoins
        credit(id, -cost, "cashout:$key")
        val body = CashoutBody("c-" + UUID.randomUUID().toString().take(8), "requested", amountCents, balances.getValue(id))
        cashouts[id to key] = amountCents to body
        return CashoutResult.Created(body)
    }

    @Synchronized
    fun player(id: String): PlayerBody? {
        val coins = balances[id] ?: return null
        return PlayerBody(id, coins, cashouts.filterKeys { it.first == id }.values.map { it.second })
    }

    /** The ledger invariant the release pipeline checks in staging: every balance is the sum of its entries. */
    @Synchronized
    fun ledgerBalanced(): Boolean = balances.all { (id, b) -> ledger.filter { it.playerId == id }.sumOf { it.delta } == b }

    @Synchronized
    fun cashoutCount(id: String): Int = cashouts.keys.count { it.first == id }

    /** For the contract tests' provider states: the store as the state describes it. */
    @Synchronized
    fun forceCashout(id: String, key: String, cashoutId: String, amountCents: Long) {
        val cost = amountCents * coinsPerCent
        credit(id, -cost, "cashout:$key")
        cashouts[id to key] = amountCents to CashoutBody(cashoutId, "requested", amountCents, balances.getValue(id))
    }

    private fun credit(id: String, delta: Long, reason: String) {
        ledger += LedgerEntry(id, delta, reason)
        balances[id] = balances.getValue(id) + delta
    }
}
