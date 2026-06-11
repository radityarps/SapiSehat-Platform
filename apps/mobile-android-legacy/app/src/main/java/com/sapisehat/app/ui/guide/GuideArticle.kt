package com.sapisehat.app.ui.guide

import androidx.annotation.StringRes
import androidx.compose.ui.graphics.Color
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors

data class GuideArticle(
    val id: String,
    val category: GuideCategory,
    val icon: String,
    val title: String,
    val summary: String,
    val body: String,
)

enum class GuideCategory(
    @StringRes val titleRes: Int,
    val icon: String,
    val color: Color,
) {
    APP_USAGE(R.string.guide_tab_app, "📱", SapiSehatColors.Primary),
    FMD(R.string.guide_tab_fmd, "🦠", SapiSehatColors.DangerPMK),
    LSD(R.string.guide_tab_lsd, "🟠", SapiSehatColors.WarningLSD),
    HEALTHY(R.string.guide_tab_healthy, "✅", SapiSehatColors.Healthy),
}
