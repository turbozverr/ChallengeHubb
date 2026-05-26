package com.challengehub.mobile.feature.challenges

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.challengehub.mobile.core.design.Background
import com.challengehub.mobile.core.design.TextMuted
import com.challengehub.mobile.core.network.ChallengeDto
import com.challengehub.mobile.core.network.JoinChallengeRequestDto
import com.challengehub.mobile.core.network.NetworkModule
import kotlinx.coroutines.launch

@Composable
fun ChallengesScreen(contentPadding: PaddingValues, token: String?) {
    val scope = rememberCoroutineScope()
    var challenges by remember { mutableStateOf<List<ChallengeDto>>(emptyList()) }
    var message by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { NetworkModule.api.challenges() }
            .onSuccess { challenges = it }
            .onFailure { message = "Не вдалося завантажити челенджі" }
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(contentPadding)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text("Челенджі")
            Text("Звичайні й спонсорські завдання з XP-нагородою", color = TextMuted)
            if (message != null) {
                Spacer(Modifier.height(12.dp))
                Text(message.orEmpty())
            }
        }
        items(challenges) { challenge ->
            ChallengeCard(
                challenge = challenge,
                onJoin = {
                    val currentToken = token ?: return@ChallengeCard
                    scope.launch {
                        runCatching {
                            NetworkModule.api.joinChallenge(
                                authorization = "Bearer $currentToken",
                                id = challenge.id,
                                body = JoinChallengeRequestDto(challenge.challengeType),
                            )
                        }.onSuccess {
                            message = "Челендж додано до активних"
                        }.onFailure {
                            message = "Не вдалося приєднатися. Можливо, ліміт 5 активних челенджів уже досягнуто."
                        }
                    }
                },
            )
        }
    }
}

@Composable
private fun ChallengeCard(challenge: ChallengeDto, onJoin: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(challenge.title)
            Spacer(Modifier.height(8.dp))
            Text(challenge.description, color = TextMuted)
            Spacer(Modifier.height(10.dp))
            Text("Тип: ${if (challenge.challengeType == "SPONSORED") "Спонсорський" else "Користувацький"}")
            Text("Складність: ${translateDifficulty(challenge.difficulty)}")
            Text("Тривалість: ${challenge.durationDays} дн.")
            Text("XP: ${challenge.xpReward}")
            Spacer(Modifier.height(12.dp))
            Button(onClick = onJoin) {
                Text("Взяти участь")
            }
        }
    }
}

private fun translateDifficulty(value: String): String = when (value) {
    "easy" -> "легко"
    "hard" -> "важко"
    else -> "нормально"
}
