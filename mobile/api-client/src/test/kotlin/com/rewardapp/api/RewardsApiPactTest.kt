package com.rewardapp.api

import au.com.dius.pact.consumer.MockServer
import au.com.dius.pact.consumer.dsl.PactDslJsonArray
import au.com.dius.pact.consumer.dsl.PactDslJsonBody
import au.com.dius.pact.consumer.dsl.PactDslWithProvider
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt
import au.com.dius.pact.consumer.junit5.PactTestFor
import au.com.dius.pact.core.model.PactSpecVersion
import au.com.dius.pact.core.model.RequestResponsePact
import au.com.dius.pact.core.model.annotations.Pact
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith

/**
 * What the app needs from the rewards backend, written as a Pact contract. The backend's build replays every
 * interaction against the real service (ProviderContractTest), so the two cannot drift apart unnoticed.
 */
@ExtendWith(PactConsumerTestExt::class)
@PactTestFor(providerName = "rewards-backend", pactVersion = PactSpecVersion.V3)
class RewardsApiPactTest {
    private val json = mapOf("Content-Type" to "application/json")

    @Pact(consumer = "reward-app")
    fun signIn(builder: PactDslWithProvider): RequestResponsePact = builder
        .uponReceiving("a sign-in from a new device")
        .path("/v1/sessions").method("POST").headers(json)
        .body(PactDslJsonBody().stringType("deviceId", "device-1"))
        .willRespondWith().status(201)
        .body(PactDslJsonBody().stringType("playerId", "p-1").integerType("coins", 0))
        .toPact()

    @Pact(consumer = "reward-app")
    fun playRound(builder: PactDslWithProvider): RequestResponsePact = builder
        .given("player p-1 has 0 coins")
        .uponReceiving("a finished round")
        .path("/v1/players/p-1/rounds").method("POST").headers(json)
        .body(PactDslJsonBody().stringType("gameId", "puzzle"))
        .willRespondWith().status(200)
        .body(PactDslJsonBody().integerType("coins", 250).integerType("earned", 250))
        .toPact()

    @Pact(consumer = "reward-app")
    fun cashout(builder: PactDslWithProvider): RequestResponsePact = builder
        .given("player p-1 has 1200 coins")
        .uponReceiving("a cash-out of one dollar")
        .path("/v1/players/p-1/cashouts").method("POST")
        .headers(json + ("Idempotency-Key" to "key-1"))
        .body(PactDslJsonBody().integerType("amountCents", 100).stringValue("method", "paypal"))
        .willRespondWith().status(201)
        .body(
            PactDslJsonBody().stringType("cashoutId", "c-1").stringValue("status", "requested")
                .integerType("amountCents", 100).integerType("coins", 200),
        )
        .toPact()

    @Pact(consumer = "reward-app")
    fun cashoutReplayed(builder: PactDslWithProvider): RequestResponsePact = builder
        .given("player p-1 already requested a cash-out with key key-1")
        .uponReceiving("the same cash-out sent again after a lost response")
        .path("/v1/players/p-1/cashouts").method("POST")
        .headers(json + ("Idempotency-Key" to "key-1"))
        .body(PactDslJsonBody().integerType("amountCents", 100).stringValue("method", "paypal"))
        .willRespondWith().status(200)
        .body(
            PactDslJsonBody().stringType("cashoutId", "c-1").stringValue("status", "requested")
                .integerType("amountCents", 100).integerType("coins", 200),
        )
        .toPact()

    @Pact(consumer = "reward-app")
    fun cashoutTooEarly(builder: PactDslWithProvider): RequestResponsePact = builder
        .given("player p-1 has 200 coins")
        .uponReceiving("a cash-out without enough coins")
        .path("/v1/players/p-1/cashouts").method("POST")
        .headers(json + ("Idempotency-Key" to "key-2"))
        .body(PactDslJsonBody().integerType("amountCents", 100).stringValue("method", "paypal"))
        .willRespondWith().status(409)
        .body(PactDslJsonBody().stringType("error", "not enough coins"))
        .toPact()

    @Pact(consumer = "reward-app")
    fun player(builder: PactDslWithProvider): RequestResponsePact = builder
        .given("player p-1 already requested a cash-out with key key-1")
        .uponReceiving("the player's balance and cash-outs")
        .path("/v1/players/p-1").method("GET")
        .willRespondWith().status(200)
        .body(
            PactDslJsonBody().stringValue("playerId", "p-1").integerType("coins", 200)
                .minArrayLike("cashouts", 1)
                .stringType("cashoutId", "c-1").stringType("status", "requested").integerType("amountCents", 100).integerType("coins", 200)
                .closeObject()!!.closeArray()!!,
        )
        .toPact()

    @Test
    @PactTestFor(pactMethod = "signIn")
    fun `signs in`(mock: MockServer) {
        assertEquals(0, RewardsApi(mock.getUrl()).signIn("device-1").coins)
    }

    @Test
    @PactTestFor(pactMethod = "playRound")
    fun `plays a round`(mock: MockServer) {
        assertEquals(250, RewardsApi(mock.getUrl()).playRound("p-1", "puzzle").earned)
    }

    @Test
    @PactTestFor(pactMethod = "cashout")
    fun `requests a cash-out`(mock: MockServer) {
        val c = RewardsApi(mock.getUrl()).requestCashout("p-1", 100, "key-1")
        assertEquals("requested", c.status)
        assertEquals(100, c.amountCents)
    }

    @Test
    @PactTestFor(pactMethod = "cashoutReplayed")
    fun `a retried cash-out returns the first one`(mock: MockServer) {
        assertEquals("requested", RewardsApi(mock.getUrl()).requestCashout("p-1", 100, "key-1").status)
    }

    @Test
    @PactTestFor(pactMethod = "cashoutTooEarly")
    fun `a cash-out without enough coins is refused`(mock: MockServer) {
        val e = assertThrows(ApiException::class.java) { RewardsApi(mock.getUrl()).requestCashout("p-1", 100, "key-2") }
        assertEquals(409, e.status)
    }

    @Test
    @PactTestFor(pactMethod = "player")
    fun `reads the balance`(mock: MockServer) {
        assertEquals(1, RewardsApi(mock.getUrl()).player("p-1").cashouts.size)
    }
}
