package com.rewardapp.api

import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.net.HttpURLConnection
import java.net.URL

@Serializable
data class Session(val playerId: String, val coins: Long)

@Serializable
data class RoundResult(val coins: Long, val earned: Long)

@Serializable
data class Cashout(val cashoutId: String, val status: String, val amountCents: Long, val coins: Long)

@Serializable
data class Player(val playerId: String, val coins: Long, val cashouts: List<Cashout> = emptyList())

@Serializable
private data class SignInRequest(val deviceId: String)

@Serializable
private data class RoundRequest(val gameId: String)

@Serializable
private data class CashoutRequest(val amountCents: Long, val method: String)

@Serializable
private data class ApiError(val error: String)

class ApiException(val status: Int, message: String) : Exception(message)

/**
 * The app's client for the rewards backend. The contract it relies on is written by its consumer tests (Pact) and
 * verified against the backend, so a backend change that would break this version of the app fails the backend's
 * build, not the player's cash-out.
 */
class RewardsApi(private val baseUrl: String, private val timeoutMs: Int = 5000) {
    private val json = Json { ignoreUnknownKeys = true }

    fun signIn(deviceId: String): Session =
        json.decodeFromString(call("POST", "/v1/sessions", json.encodeToString(SignInRequest(deviceId))))

    fun playRound(playerId: String, gameId: String): RoundResult =
        json.decodeFromString(call("POST", "/v1/players/$playerId/rounds", json.encodeToString(RoundRequest(gameId))))

    /** The same key on a retry returns the same cash-out: a lost response never pays twice. */
    fun requestCashout(playerId: String, amountCents: Long, idempotencyKey: String): Cashout =
        json.decodeFromString(
            call(
                "POST", "/v1/players/$playerId/cashouts",
                json.encodeToString(CashoutRequest(amountCents, "paypal")),
                mapOf("Idempotency-Key" to idempotencyKey),
            ),
        )

    fun player(playerId: String): Player = json.decodeFromString(call("GET", "/v1/players/$playerId", null))

    private fun call(method: String, path: String, body: String?, headers: Map<String, String> = emptyMap()): String {
        val c = URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection
        try {
            c.requestMethod = method
            c.connectTimeout = timeoutMs
            c.readTimeout = timeoutMs
            c.setRequestProperty("Accept", "application/json")
            headers.forEach { (k, v) -> c.setRequestProperty(k, v) }
            if (body != null) {
                c.doOutput = true
                c.setRequestProperty("Content-Type", "application/json")
                c.outputStream.use { it.write(body.toByteArray()) }
            }
            val code = c.responseCode
            val stream = if (code < 400) c.inputStream else c.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() } ?: ""
            if (code >= 400) {
                val message = runCatching { json.decodeFromString<ApiError>(text).error }.getOrDefault("HTTP $code")
                throw ApiException(code, message)
            }
            return text
        } finally {
            c.disconnect()
        }
    }
}
