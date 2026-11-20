package com.rewardapp

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.test.espresso.idling.CountingIdlingResource
import com.rewardapp.api.RewardsApi
import java.util.UUID
import java.util.concurrent.Executors

/**
 * A minimal rewarded-gaming screen: sign in, play rounds for coins, cash out a dollar. Enough for the flows the
 * end-to-end tests protect: the cash-out button is disabled while a request is in flight, and a retry after a
 * failure reuses the same idempotency key, so a double tap or a lost response never pays twice.
 */
class MainActivity : Activity() {
    companion object {
        /** Espresso waits for this to be idle before it checks the screen. */
        val idling = CountingIdlingResource("rewards-api")
        const val CASHOUT_CENTS = 100L
        const val CASHOUT_COINS = 1000L
    }

    private val io = Executors.newSingleThreadExecutor()
    private val api by lazy { RewardsApi(BuildConfig.API_URL) }
    private var playerId: String? = null
    private var coins = 0L
    private var busy = false
    private var pendingKey: String? = null

    private lateinit var coinsView: TextView
    private lateinit var status: TextView
    private lateinit var signIn: Button
    private lateinit var play: Button
    private lateinit var cashOut: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        coinsView = findViewById(R.id.coins)
        status = findViewById(R.id.status)
        signIn = findViewById(R.id.sign_in)
        play = findViewById(R.id.play)
        cashOut = findViewById(R.id.cash_out)

        signIn.setOnClickListener {
            background({ api.signIn(UUID.randomUUID().toString()) }) {
                playerId = it.playerId
                coins = it.coins
                status.text = "Signed in"
            }
        }
        play.setOnClickListener {
            val id = playerId ?: return@setOnClickListener
            background({ api.playRound(id, "puzzle") }) {
                coins = it.coins
                status.text = "+${it.earned} coins"
            }
        }
        cashOut.setOnClickListener {
            val id = playerId ?: return@setOnClickListener
            val key = pendingKey ?: UUID.randomUUID().toString().also { pendingKey = it }
            background({ api.requestCashout(id, CASHOUT_CENTS, key) }) {
                coins = it.coins
                pendingKey = null
                status.text = "Cash-out requested: $1.00"
            }
        }
        render()
    }

    private fun <T> background(work: () -> T, done: (T) -> Unit) {
        if (busy) return
        busy = true
        render()
        idling.increment()
        io.execute {
            val result = runCatching(work)
            runOnUiThread {
                busy = false
                result.onSuccess(done).onFailure { status.text = "Something went wrong: ${it.message}. Try again." }
                render()
                idling.decrement()
            }
        }
    }

    private fun render() {
        coinsView.text = "$coins coins"
        val signedIn = playerId != null
        signIn.isEnabled = !signedIn && !busy
        play.isEnabled = signedIn && !busy
        cashOut.isEnabled = signedIn && !busy && coins >= CASHOUT_COINS
    }

    /** For instrumented tests: which backend player this screen signed in as. */
    fun playerIdForTest(): String = playerId.orEmpty()

    override fun onDestroy() {
        io.shutdown()
        super.onDestroy()
    }
}
