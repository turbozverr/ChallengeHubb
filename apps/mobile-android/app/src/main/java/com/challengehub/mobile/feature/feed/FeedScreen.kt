package com.challengehub.mobile.feature.feed

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
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
import com.challengehub.mobile.core.network.NetworkModule
import com.challengehub.mobile.core.network.VideoDto
import kotlinx.coroutines.launch

@Composable
fun FeedScreen(contentPadding: PaddingValues, token: String?) {
    val scope = rememberCoroutineScope()
    var videos by remember { mutableStateOf<List<VideoDto>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { NetworkModule.api.feed() }
            .onSuccess { videos = it }
            .onFailure { error = "Не вдалося завантажити стрічку" }
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
            Text("Стрічка", modifier = Modifier.padding(bottom = 4.dp))
            Text("Опубліковані відео-звіти та нативна реклама", color = TextMuted)
        }
        if (error != null) {
            item { Text(error.orEmpty()) }
        }
        items(videos) { video ->
            VideoCard(
                video = video,
                onLike = {
                    val currentToken = token ?: return@VideoCard
                    scope.launch {
                        runCatching {
                            if (video.likedByMe) {
                                NetworkModule.api.unlikeVideo("Bearer $currentToken", video.id)
                            } else {
                                NetworkModule.api.likeVideo("Bearer $currentToken", video.id)
                            }
                        }.onSuccess { updated ->
                            videos = videos.map { if (it.id == updated.id) updated else it }
                        }
                    }
                },
            )
        }
    }
}

@Composable
private fun VideoCard(video: VideoDto, onLike: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(if (video.isAd) "Рекламне відео" else "Відео-звіт")
            Spacer(Modifier.height(8.dp))
            Text(video.description ?: "Без опису")
            Spacer(Modifier.height(8.dp))
            Text("URL: ${video.url}", color = TextMuted)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Перегляди: ${video.viewsCount}")
                Text("Лайки: ${video.likesCount}")
                Text("Коментарі: ${video.commentsCount}")
            }
            Spacer(Modifier.height(12.dp))
            Button(onClick = onLike) {
                Text(if (video.likedByMe) "Прибрати лайк" else "Лайк")
            }
        }
    }
}
