package com.rewardapp

import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.IdlingRegistry
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.isEnabled
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.rewardapp.api.RewardsApi
import org.hamcrest.Matchers.not
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Against the real Kotlin backend running on the host (10.0.2.2:8080), as in CI. */
@RunWith(AndroidJUnit4::class)
class CashoutFlowTest {
    @Before
    fun register() {
        IdlingRegistry.getInstance().register(MainActivity.idling)
    }

    @After
    fun unregister() {
        IdlingRegistry.getInstance().unregister(MainActivity.idling)
    }

    private fun signInAndEarn(rounds: Int) {
        onView(withId(R.id.sign_in)).perform(click())
        onView(withId(R.id.status)).check(matches(withText("Signed in")))
        repeat(rounds) { onView(withId(R.id.play)).perform(click()) }
    }

    @Test
    fun cashOutIsOnlyOfferedWithEnoughCoins() {
        ActivityScenario.launch(MainActivity::class.java).use {
            signInAndEarn(3)
            onView(withId(R.id.coins)).check(matches(withText("750 coins")))
            onView(withId(R.id.cash_out)).check(matches(not(isEnabled())))
            onView(withId(R.id.play)).perform(click())
            onView(withId(R.id.cash_out)).check(matches(isEnabled()))
        }
    }

    @Test
    fun aCashOutPaysOnceAndUpdatesTheBalance() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            signInAndEarn(5)
            onView(withId(R.id.cash_out)).perform(click())
            onView(withId(R.id.status)).check(matches(withText("Cash-out requested: \$1.00")))
            onView(withId(R.id.coins)).check(matches(withText("250 coins")))
            var id = ""
            scenario.onActivity { id = it.playerIdForTest() }
            val player = RewardsApi(BuildConfig.API_URL).player(id)
            assertEquals(1, player.cashouts.size)
            assertEquals(250L, player.coins)
        }
    }
}
