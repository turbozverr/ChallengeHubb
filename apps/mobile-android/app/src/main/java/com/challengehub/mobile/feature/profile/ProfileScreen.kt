package com.challengehub.mobile.feature.profile

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.challengehub.mobile.core.design.Background
import com.challengehub.mobile.core.design.TextMuted
import com.challengehub.mobile.core.network.MobileUserDto
import com.challengehub.mobile.core.network.NetworkModule

@Composable
fun ProfileScreen(contentPadding: PaddingValues, token: String?, onLogout: () -> Unit) {
    var user by remember { mutableStateOf<MobileUserDto?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(token) {
        val currentToken = token ?: return@LaunchedEffect
        runCatching { NetworkModule.api.me("Bearer $currentToken") }
            .onSuccess { user = it }
            .onFailure { error = "Не вдалося завантажити профіль" }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(contentPadding)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Профіль")
        if (error != null) {
            Text(error.orEmpty())
        }
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(user?.fullName ?: "Користувач")
                Text("@${user?.username ?: "unknown"}", color = TextMuted)
                Text(user?.bio ?: "Опис профілю ще не додано")
                Text("XP: ${user?.xp ?: 0}")
                Text(if (user?.isPremium == true) "Premium активний" else "Free акаунт")
            }
        }
        Button(onClick = onLogout) {
            Text("Вийти")
        }
    }
}
