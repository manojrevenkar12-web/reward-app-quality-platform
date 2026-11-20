package com.rewardapp.backend

import io.ktor.http.HttpStatusCode
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import kotlinx.serialization.Serializable

@Serializable
data class SignInBody(val deviceId: String)

@Serializable
data class SessionBody(val playerId: String, val coins: Long)

@Serializable
data class RoundRequestBody(val gameId: String)

@Serializable
data class RoundBody(val coins: Long, val earned: Long)

@Serializable
data class CashoutRequestBody(val amountCents: Long, val method: String)

@Serializable
data class CashoutBody(val cashoutId: String, val status: String, val amountCents: Long, val coins: Long)

@Serializable
data class PlayerBody(val playerId: String, val coins: Long, val cashouts: List<CashoutBody>)

@Serializable
data class ErrorBody(val error: String)

@Serializable
data class LedgerCheck(val balanced: Boolean)

/** The rewards backend: sign-in, coins for rounds, cash-outs with idempotency keys, and the ledger check. */
fun Application.module(store: Store = Store()) {
    install(ContentNegotiation) { json() }
    routing {
        get("/healthz") { call.respondText("ok") }
        post("/v1/sessions") {
            val req = call.receive<SignInBody>()
            if (req.deviceId.isBlank()) return@post call.respond(HttpStatusCode.BadRequest, ErrorBody("deviceId is required"))
            val id = store.newPlayer()
            call.respond(HttpStatusCode.Created, SessionBody(id, store.coins(id) ?: 0))
        }
        post("/v1/players/{id}/rounds") {
            call.receive<RoundRequestBody>()
            val r = store.round(call.parameters["id"]!!) ?: return@post call.respond(HttpStatusCode.NotFound, ErrorBody("no such player"))
            call.respond(r)
        }
        post("/v1/players/{id}/cashouts") {
            val key = call.request.headers["Idempotency-Key"]
            if (key.isNullOrBlank() || key.length > 64) {
                return@post call.respond(HttpStatusCode.BadRequest, ErrorBody("Idempotency-Key header is required"))
            }
            val req = call.receive<CashoutRequestBody>()
            if (req.amountCents <= 0 || req.method !in setOf("paypal", "gift_card")) {
                return@post call.respond(HttpStatusCode.BadRequest, ErrorBody("invalid cash-out"))
            }
            when (val r = store.cashout(call.parameters["id"]!!, key, req.amountCents)) {
                is CashoutResult.Created -> call.respond(HttpStatusCode.Created, r.cashout)
                is CashoutResult.Replayed -> call.respond(HttpStatusCode.OK, r.cashout)
                is CashoutResult.KeyReused -> call.respond(HttpStatusCode.UnprocessableEntity, ErrorBody(r.reason))
                CashoutResult.NotEnoughCoins -> call.respond(HttpStatusCode.Conflict, ErrorBody("not enough coins"))
                CashoutResult.NoSuchPlayer -> call.respond(HttpStatusCode.NotFound, ErrorBody("no such player"))
            }
        }
        get("/v1/players/{id}") {
            val p = store.player(call.parameters["id"]!!) ?: return@get call.respond(HttpStatusCode.NotFound, ErrorBody("no such player"))
            call.respond(p)
        }
        get("/v1/ledger/check") { call.respond(LedgerCheck(store.ledgerBalanced())) }
    }
}

fun main() {
    val port = System.getenv("PORT")?.toIntOrNull() ?: 8080
    embeddedServer(Netty, port = port, host = "0.0.0.0") { module() }.start(wait = true)
}
