package com.rewardapp.backend

import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.testing.testApplication
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class CashoutTest {
    private val body = """{"amountCents":100,"method":"paypal"}"""

    @Test
    fun `a retried cash-out pays once`() = testApplication {
        val store = Store()
        application { module(store) }
        val id = store.newPlayer(coins = 1200)
        val first = client.post("/v1/players/$id/cashouts") {
            header("Idempotency-Key", "k1"); contentType(ContentType.Application.Json); setBody(body)
        }
        val again = client.post("/v1/players/$id/cashouts") {
            header("Idempotency-Key", "k1"); contentType(ContentType.Application.Json); setBody(body)
        }
        assertEquals(HttpStatusCode.Created, first.status)
        assertEquals(HttpStatusCode.OK, again.status)
        assertEquals(first.bodyAsText(), again.bodyAsText())
        assertEquals(200L, store.coins(id))
        assertEquals(1, store.cashoutCount(id))
    }

    @Test
    fun `twenty taps at once still pay once`() {
        val store = Store()
        val id = store.newPlayer(coins = 1200)
        val pool = Executors.newFixedThreadPool(8)
        val results = pool.invokeAll(List(20) { Callable { store.cashout(id, "same-key", 100) } }).map { it.get() }
        pool.shutdown()
        assertEquals(1, results.count { it is CashoutResult.Created })
        assertEquals(19, results.count { it is CashoutResult.Replayed })
        assertEquals(200L, store.coins(id))
        assertTrue(store.ledgerBalanced())
    }

    @Test
    fun `no cash-out without enough coins, and none without a key`() = testApplication {
        val store = Store()
        application { module(store) }
        val id = store.newPlayer(coins = 200)
        val poor = client.post("/v1/players/$id/cashouts") {
            header("Idempotency-Key", "k2"); contentType(ContentType.Application.Json); setBody(body)
        }
        val keyless = client.post("/v1/players/$id/cashouts") { contentType(ContentType.Application.Json); setBody(body) }
        assertEquals(HttpStatusCode.Conflict, poor.status)
        assertEquals(HttpStatusCode.BadRequest, keyless.status)
        assertEquals(200L, store.coins(id))
    }

    @Test
    fun `rounds credit coins and the ledger stays balanced`() = testApplication {
        val store = Store()
        application { module(store) }
        val id = store.newPlayer()
        repeat(5) {
            client.post("/v1/players/$id/rounds") { contentType(ContentType.Application.Json); setBody("""{"gameId":"puzzle"}""") }
        }
        assertEquals(1250L, store.coins(id))
        assertTrue(client.get("/v1/ledger/check").bodyAsText().contains("true"))
    }
}
