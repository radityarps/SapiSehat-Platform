package com.sapisehat.app.ui.theme

import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

/**
 * SapiSehat "Bold Agricultural" palette.
 *
 * Design intent: confident, grounded, high-contrast.
 * Works outdoors in direct sunlight. Feels intentional, not template-generated.
 */
object SapiSehatColors {
    // ── Primary: Deep Forest Green ──────────────────────────────────────
    val Primary = Color(0xFF1B4332)
    val OnPrimary = Color(0xFFFFFFFF)
    val PrimaryContainer = Color(0xFFB7E4C7)
    val OnPrimaryContainer = Color(0xFF0B2118)
    val PrimaryLight = Color(0xFF2D6A4F)       // interactive hover/pressed

    // ── Secondary: Harvest Gold ─────────────────────────────────────────
    val Secondary = Color(0xFFD4A017)
    val OnSecondary = Color(0xFF1A1A1A)
    val SecondaryContainer = Color(0xFFFFF3CD)
    val OnSecondaryContainer = Color(0xFF3D2E00)

    // ── Tertiary: Warm Terracotta ───────────────────────────────────────
    val Tertiary = Color(0xFFA0522D)
    val OnTertiary = Color(0xFFFFFFFF)

    // ── Background & Surface ────────────────────────────────────────────
    val Background = Color(0xFFFAFAF7)         // clean warm white
    val OnBackground = Color(0xFF1A1A1A)
    val Surface = Color(0xFFFFFFFF)            // pure white cards
    val OnSurface = Color(0xFF1A1A1A)
    val SurfaceVariant = Color(0xFFF3F1EC)     // subtle warm gray
    val OnSurfaceVariant = Color(0xFF4A4A4A)

    // ── Text ────────────────────────────────────────────────────────────
    val TextPrimary = Color(0xFF1A1A1A)        // near-black, high contrast
    val TextSecondary = Color(0xFF6B7280)      // medium gray

    // ── Semantic: Disease indicators ────────────────────────────────────
    val Healthy = Color(0xFF059669)            // vivid green — SEHAT
    val DangerPMK = Color(0xFFDC2626)          // strong red — PMK
    val WarningLSD = Color(0xFFD97706)         // deep amber — LSD

    // ── Utility ─────────────────────────────────────────────────────────
    val Outline = Color(0xFFD1D5DB)
    val OutlineVariant = Color(0xFFE5E7EB)
    val Error = Color(0xFFDC2626)
    val OnError = Color(0xFFFFFFFF)
    val ErrorContainer = Color(0xFFFEE2E2)
    val OnErrorContainer = Color(0xFF7F1D1D)

    // ── Elevation tints ─────────────────────────────────────────────────
    val SurfaceTint = Primary
}

val SapiSehatLightColorScheme = lightColorScheme(
    primary = SapiSehatColors.Primary,
    onPrimary = SapiSehatColors.OnPrimary,
    primaryContainer = SapiSehatColors.PrimaryContainer,
    onPrimaryContainer = SapiSehatColors.OnPrimaryContainer,
    secondary = SapiSehatColors.Secondary,
    onSecondary = SapiSehatColors.OnSecondary,
    secondaryContainer = SapiSehatColors.SecondaryContainer,
    onSecondaryContainer = SapiSehatColors.OnSecondaryContainer,
    tertiary = SapiSehatColors.Tertiary,
    onTertiary = SapiSehatColors.OnTertiary,
    background = SapiSehatColors.Background,
    onBackground = SapiSehatColors.OnBackground,
    surface = SapiSehatColors.Surface,
    onSurface = SapiSehatColors.OnSurface,
    surfaceVariant = SapiSehatColors.SurfaceVariant,
    onSurfaceVariant = SapiSehatColors.OnSurfaceVariant,
    outline = SapiSehatColors.Outline,
    outlineVariant = SapiSehatColors.OutlineVariant,
    error = SapiSehatColors.Error,
    onError = SapiSehatColors.OnError,
    errorContainer = SapiSehatColors.ErrorContainer,
    onErrorContainer = SapiSehatColors.OnErrorContainer,
    surfaceTint = SapiSehatColors.SurfaceTint,
)

// ── Legacy alias for migration ──────────────────────────────────────────────
// Screens that still reference TropisBersihColors will compile without changes.
// Migrate them to SapiSehatColors over time.
@Deprecated("Use SapiSehatColors instead", ReplaceWith("SapiSehatColors"))
object TropisBersihColors {
    val Primary = SapiSehatColors.Primary
    val OnPrimary = SapiSehatColors.OnPrimary
    val PrimaryContainer = SapiSehatColors.PrimaryContainer
    val OnPrimaryContainer = SapiSehatColors.OnPrimaryContainer
    val Secondary = SapiSehatColors.SecondaryContainer
    val OnSecondary = SapiSehatColors.OnSecondary
    val SecondaryContainer = SapiSehatColors.SecondaryContainer
    val OnSecondaryContainer = SapiSehatColors.OnSecondaryContainer
    val Accent = SapiSehatColors.Secondary
    val Background = SapiSehatColors.Background
    val OnBackground = SapiSehatColors.OnBackground
    val Surface = SapiSehatColors.Surface
    val OnSurface = SapiSehatColors.OnSurface
    val SurfaceVariant = SapiSehatColors.SurfaceVariant
    val OnSurfaceVariant = SapiSehatColors.OnSurfaceVariant
    val TextPrimary = SapiSehatColors.TextPrimary
    val TextSecondary = SapiSehatColors.TextSecondary
    val Success = SapiSehatColors.Healthy
    val Danger = SapiSehatColors.DangerPMK
    val Warning = SapiSehatColors.WarningLSD
    val Outline = SapiSehatColors.Outline
    val OutlineVariant = SapiSehatColors.OutlineVariant
    val Error = SapiSehatColors.Error
    val OnError = SapiSehatColors.OnError
    val ErrorContainer = SapiSehatColors.ErrorContainer
    val OnErrorContainer = SapiSehatColors.OnErrorContainer
}
