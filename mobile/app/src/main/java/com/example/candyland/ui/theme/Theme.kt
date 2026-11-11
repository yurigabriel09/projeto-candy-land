package com.example.candyland.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

// Paleta extraída dos protótipos
object CandyColors {
    val Pink = Color(0xFFFF4D7E)
    val Orange = Color(0xFFFF7A3D)
    val Brown = Color(0xFF4A1C1C)
    val Cream = Color(0xFFFFEBE0)
    val Peach = Color(0xFFFFD9B0)
    val PeachSoft = Color(0xFFFFE3CC)
    val Muted = Color(0xFF9A7B73)
    val Green = Color(0xFF16A34A)
    val Red = Color(0xFFDC2626)
    val White = Color(0xFFFFFFFF)

    val Gradient = Brush.horizontalGradient(listOf(Pink, Orange))
}

private val CandyScheme = lightColorScheme(
    primary = CandyColors.Pink,
    onPrimary = Color.White,
    secondary = CandyColors.Orange,
    background = CandyColors.Cream,
    onBackground = CandyColors.Brown,
    surface = Color.White,
    onSurface = CandyColors.Brown,
    outline = CandyColors.Peach
)

@Composable
fun CandylandTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = CandyScheme, content = content)
}
