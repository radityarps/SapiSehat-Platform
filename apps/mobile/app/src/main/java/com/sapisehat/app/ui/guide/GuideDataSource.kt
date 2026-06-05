package com.sapisehat.app.ui.guide

import android.content.Context
import com.sapisehat.app.R

object GuideDataSource {
    fun articles(context: Context): List<GuideArticle> = listOf(
        // ── App Usage ───────────────────────────────────────────────────
        GuideArticle(
            id = "app_1",
            category = GuideCategory.APP_USAGE,
            icon = "📷",
            title = context.getString(R.string.guide_app_title_1),
            summary = context.getString(R.string.guide_app_summary_1),
            body = context.getString(R.string.guide_app_body_1),
        ),
        GuideArticle(
            id = "app_2",
            category = GuideCategory.APP_USAGE,
            icon = "🌐",
            title = context.getString(R.string.guide_app_title_2),
            summary = context.getString(R.string.guide_app_summary_2),
            body = context.getString(R.string.guide_app_body_2),
        ),
        GuideArticle(
            id = "app_3",
            category = GuideCategory.APP_USAGE,
            icon = "📊",
            title = context.getString(R.string.guide_app_title_3),
            summary = context.getString(R.string.guide_app_summary_3),
            body = context.getString(R.string.guide_app_body_3),
        ),

        // ── PMK / FMD ───────────────────────────────────────────────────
        GuideArticle(
            id = "fmd_1",
            category = GuideCategory.FMD,
            icon = "🔬",
            title = context.getString(R.string.guide_fmd_title_1),
            summary = context.getString(R.string.guide_fmd_summary_1),
            body = context.getString(R.string.guide_fmd_body_1),
        ),
        GuideArticle(
            id = "fmd_2",
            category = GuideCategory.FMD,
            icon = "🩺",
            title = context.getString(R.string.guide_fmd_title_2),
            summary = context.getString(R.string.guide_fmd_summary_2),
            body = context.getString(R.string.guide_fmd_body_2),
        ),
        GuideArticle(
            id = "fmd_3",
            category = GuideCategory.FMD,
            icon = "🛡️",
            title = context.getString(R.string.guide_fmd_title_3),
            summary = context.getString(R.string.guide_fmd_summary_3),
            body = context.getString(R.string.guide_fmd_body_3),
        ),
        GuideArticle(
            id = "fmd_4",
            category = GuideCategory.FMD,
            icon = "🚨",
            title = context.getString(R.string.guide_fmd_title_4),
            summary = context.getString(R.string.guide_fmd_summary_4),
            body = context.getString(R.string.guide_fmd_body_4),
        ),

        // ── LSD ─────────────────────────────────────────────────────────
        GuideArticle(
            id = "lsd_1",
            category = GuideCategory.LSD,
            icon = "🔬",
            title = context.getString(R.string.guide_lsd_title_1),
            summary = context.getString(R.string.guide_lsd_summary_1),
            body = context.getString(R.string.guide_lsd_body_1),
        ),
        GuideArticle(
            id = "lsd_2",
            category = GuideCategory.LSD,
            icon = "🩺",
            title = context.getString(R.string.guide_lsd_title_2),
            summary = context.getString(R.string.guide_lsd_summary_2),
            body = context.getString(R.string.guide_lsd_body_2),
        ),
        GuideArticle(
            id = "lsd_3",
            category = GuideCategory.LSD,
            icon = "🛡️",
            title = context.getString(R.string.guide_lsd_title_3),
            summary = context.getString(R.string.guide_lsd_summary_3),
            body = context.getString(R.string.guide_lsd_body_3),
        ),
        GuideArticle(
            id = "lsd_4",
            category = GuideCategory.LSD,
            icon = "🚨",
            title = context.getString(R.string.guide_lsd_title_4),
            summary = context.getString(R.string.guide_lsd_summary_4),
            body = context.getString(R.string.guide_lsd_body_4),
        ),

        // ── Sapi Sehat ──────────────────────────────────────────────────
        GuideArticle(
            id = "healthy_1",
            category = GuideCategory.HEALTHY,
            icon = "🐄",
            title = context.getString(R.string.guide_healthy_title_1),
            summary = context.getString(R.string.guide_healthy_summary_1),
            body = context.getString(R.string.guide_healthy_body_1),
        ),
        GuideArticle(
            id = "healthy_2",
            category = GuideCategory.HEALTHY,
            icon = "🏠",
            title = context.getString(R.string.guide_healthy_title_2),
            summary = context.getString(R.string.guide_healthy_summary_2),
            body = context.getString(R.string.guide_healthy_body_2),
        ),
    )
}
