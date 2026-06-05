package com.sapisehat.app.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.runtime.Composable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * Shapes: less rounded = more confident.
 * Not bubbly, not sharp. Grounded.
 */
val SapiSehatShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(20.dp),
)

@Composable
fun SapiSehatTheme(
    darkTheme: Boolean = false,
    textSizeMode: String = "system",
    content: @Composable () -> Unit
) {
    val typographyScale = when (textSizeMode) {
        "small" -> 0.9f
        "large" -> 1.12f
        "medium", "system" -> 1.0f
        else -> 1.0f
    }

    MaterialTheme(
        colorScheme = SapiSehatLightColorScheme,
        typography = SapiSehatTypography.scaled(typographyScale),
        shapes = SapiSehatShapes,
        content = content,
    )
}

/**
 * Extension property for secondary text color.
 */
val ColorScheme.textSecondary: Color
    @Composable
    @ReadOnlyComposable
    get() = SapiSehatColors.TextSecondary
