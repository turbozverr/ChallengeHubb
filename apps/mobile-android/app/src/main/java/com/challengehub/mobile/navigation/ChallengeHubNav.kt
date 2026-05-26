package com.challengehub.mobile.navigation

import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.challengehub.mobile.core.design.Background
import com.challengehub.mobile.core.session.SessionStore
import com.challengehub.mobile.feature.auth.AuthScreen
import com.challengehub.mobile.feature.challenges.ChallengesScreen
import com.challengehub.mobile.feature.feed.FeedScreen
import com.challengehub.mobile.feature.profile.ProfileScreen
import kotlinx.coroutines.launch

private const val AUTH = "auth"
private const val FEED = "feed"
private const val CHALLENGES = "challenges"
private const val PROFILE = "profile"

@Composable
fun ChallengeHubNav(sessionStore: SessionStore, initialToken: String?) {
    val navController = rememberNavController()
    val scope = rememberCoroutineScope()
    var token by remember(initialToken) { mutableStateOf(initialToken) }
    val backStackEntry by navController.currentBackStackEntryAsState()
    val start = if (token.isNullOrBlank()) AUTH else FEED
    val tabs = listOf(FEED to "Стрічка", CHALLENGES to "Челенджі", PROFILE to "Профіль")

    LaunchedEffect(initialToken) {
        if (!initialToken.isNullOrBlank()) {
            token = initialToken
            if (navController.currentDestination?.route != FEED) {
                navController.navigate(FEED) {
                    popUpTo(AUTH) { inclusive = true }
                }
            }
        }
    }

    Scaffold(
        containerColor = Background,
        bottomBar = {
            if (!token.isNullOrBlank()) {
                NavigationBar {
                    tabs.forEach { (route, label) ->
                        NavigationBarItem(
                            selected = backStackEntry?.destination?.route == route,
                            onClick = { navController.navigate(route) },
                            icon = {},
                            label = { Text(label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(navController = navController, startDestination = start) {
            composable(AUTH) {
                AuthScreen(
                    onAuthenticated = { newToken ->
                        token = newToken
                        scope.launch { sessionStore.saveToken(newToken) }
                        navController.navigate(FEED) {
                            popUpTo(AUTH) { inclusive = true }
                        }
                    },
                )
            }
            composable(FEED) {
                FeedScreen(
                    contentPadding = padding,
                    token = token,
                )
            }
            composable(CHALLENGES) {
                ChallengesScreen(
                    contentPadding = padding,
                    token = token,
                )
            }
            composable(PROFILE) {
                ProfileScreen(
                    contentPadding = padding,
                    token = token,
                    onLogout = {
                        scope.launch { sessionStore.clear() }
                        token = null
                        navController.navigate(AUTH) {
                            popUpTo(0)
                        }
                    },
                )
            }
        }
    }
}
