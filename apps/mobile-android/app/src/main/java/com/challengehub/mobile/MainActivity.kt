package com.challengehub.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.challengehub.mobile.core.design.Background
import com.challengehub.mobile.core.design.ChallengeHubTheme
import com.challengehub.mobile.core.session.SessionStore
import com.challengehub.mobile.navigation.ChallengeHubNav

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val sessionStore = SessionStore(applicationContext)
        setContent {
            ChallengeHubTheme {
                AppRoot(sessionStore)
            }
        }
    }
}

@Composable
private fun AppRoot(sessionStore: SessionStore) {
    val token by sessionStore.token.collectAsState(initial = null)
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Background),
        contentAlignment = Alignment.Center,
    ) {
        ChallengeHubNav(sessionStore = sessionStore, initialToken = token)
    }
}
