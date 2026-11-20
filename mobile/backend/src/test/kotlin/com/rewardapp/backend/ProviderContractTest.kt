package com.rewardapp.backend

import au.com.dius.pact.provider.junit5.HttpTestTarget
import au.com.dius.pact.provider.junit5.PactVerificationContext
import au.com.dius.pact.provider.junit5.PactVerificationInvocationContextProvider
import au.com.dius.pact.provider.junitsupport.Provider
import au.com.dius.pact.provider.junitsupport.State
import au.com.dius.pact.provider.junitsupport.loader.PactFolder
import io.ktor.server.engine.EmbeddedServer
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import org.junit.jupiter.api.AfterAll
import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.TestTemplate
import org.junit.jupiter.api.extension.ExtendWith

/** Replays every interaction the app's consumer tests recorded against the real backend. */
@Provider("rewards-backend")
@PactFolder("../contracts/pacts")
class ProviderContractTest {
    companion object {
        private const val PORT = 18080
        val store = Store()
        private lateinit var server: EmbeddedServer<*, *>

        @BeforeAll
        @JvmStatic
        fun start() {
            server = embeddedServer(Netty, port = PORT) { module(store) }.start(wait = false)
        }

        @AfterAll
        @JvmStatic
        fun stop() {
            server.stop(100, 500)
        }
    }

    @BeforeEach
    fun target(context: PactVerificationContext) {
        context.target = HttpTestTarget("localhost", PORT)
    }

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider::class)
    fun verify(context: PactVerificationContext) {
        context.verifyInteraction()
    }

    @State("player p-1 has 0 coins")
    fun noCoins() {
        store.reset()
        store.newPlayer("p-1")
    }

    @State("player p-1 has 1200 coins")
    fun enoughCoins() {
        store.reset()
        store.newPlayer("p-1", 1200)
    }

    @State("player p-1 has 200 coins")
    fun tooFewCoins() {
        store.reset()
        store.newPlayer("p-1", 200)
    }

    @State("player p-1 already requested a cash-out with key key-1")
    fun alreadyCashedOut() {
        store.reset()
        store.newPlayer("p-1", 1200)
        store.forceCashout("p-1", "key-1", "c-1", 100)
    }
}
