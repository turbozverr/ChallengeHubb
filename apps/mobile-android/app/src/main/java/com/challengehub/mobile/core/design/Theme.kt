package com.challengehub.mobile.core.design

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val Background = Color(0xFF121212)
val Surface = Color(0xFF1A1A1A)
val SurfaceSoft = Color(0xFF242424)
val HotPink = Color(0xFFFE2C55)
val Purple = Color(0xFFAD46FF)
val TextPrimary = Color(0xFFF7F7F7)
val TextMuted = Color(0xFFA8A8A8)

private val Colors = darkColorScheme(
    primary = HotPink,
    secondary = Purple,
    background = Background,
    surface = Surface,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
)

@Composable
fun ChallengeHubTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = Colors,
        content = content,
    )
}
