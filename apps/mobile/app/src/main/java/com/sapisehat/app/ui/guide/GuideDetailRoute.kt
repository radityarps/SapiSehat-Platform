package com.sapisehat.app.ui.guide

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GuideDetailRoute(
    articleId: String,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val article = GuideDataSource.articles(context).find { it.id == articleId }

    if (article == null) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(stringResource(R.string.guide_title)) },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = stringResource(R.string.nav_back),
                            )
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                )
            },
        ) { innerPadding ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(R.string.guide_article_not_found),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
            }
        }
        return
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(article.category.titleRes),
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.SemiBold,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = stringResource(R.string.nav_back),
                            tint = SapiSehatColors.TextPrimary,
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(innerPadding),
        ) {
            // Hero banner
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(140.dp)
                    .background(article.category.color),
                contentAlignment = Alignment.Center,
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = Color.Black.copy(alpha = 0.20f),
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(12.dp),
                ) {
                    Text(
                        text = stringResource(article.category.titleRes),
                        style = MaterialTheme.typography.labelMedium,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
                    )
                }
            }

            // Content
            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(20.dp))

                // Title
                Text(
                    text = article.title,
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = SapiSehatColors.TextPrimary,
                )

                Spacer(Modifier.height(8.dp))

                // Summary
                Text(
                    text = article.summary,
                    style = MaterialTheme.typography.bodyLarge,
                    color = SapiSehatColors.TextSecondary,
                )

                Spacer(Modifier.height(16.dp))
                HorizontalDivider(color = SapiSehatColors.OutlineVariant)
                Spacer(Modifier.height(16.dp))

                // Body — rendered with section formatting
                ArticleBody(body = article.body, accentColor = article.category.color)

                Spacer(Modifier.height(32.dp))
            }
        }
    }
}

/**
 * Renders article body text with basic formatting:
 * - Lines that don't start with • are treated as section headers or paragraphs
 * - Lines starting with • are bullet points
 * - Lines starting with a digit and period (1. 2. 3.) are numbered items
 * - Empty lines create spacing
 */
@Composable
private fun ArticleBody(body: String, accentColor: Color) {
    val paragraphs = body.split("\n\n")

    paragraphs.forEach { paragraph ->
        val trimmed = paragraph.trim()
        if (trimmed.isEmpty()) {
            Spacer(Modifier.height(8.dp))
            return@forEach
        }

        val lines = trimmed.split("\n")

        // Check if this paragraph is a section header (single line, no bullet, no numbered)
        if (lines.size == 1 && !trimmed.startsWith("•") && !trimmed.matches(Regex("^\\d+\\..*"))) {
            // Section header
            Spacer(Modifier.height(12.dp))
            Text(
                text = trimmed,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = SapiSehatColors.TextPrimary,
            )
            Spacer(Modifier.height(8.dp))
        } else {
            // Mixed content — render line by line
            lines.forEach { line ->
                val l = line.trim()
                when {
                    l.isEmpty() -> Spacer(Modifier.height(4.dp))
                    l.startsWith("•") -> {
                        // Bullet point
                        Row(modifier = Modifier.padding(vertical = 3.dp)) {
                            Text(
                                text = "•",
                                style = MaterialTheme.typography.bodyLarge,
                                color = accentColor,
                                modifier = Modifier.width(16.dp),
                            )
                            Text(
                                text = l.removePrefix("•").trim(),
                                style = MaterialTheme.typography.bodyLarge,
                                color = SapiSehatColors.TextPrimary,
                                lineHeight = 24.sp,
                            )
                        }
                    }
                    l.matches(Regex("^\\d+\\.\\s.*")) -> {
                        // Numbered item
                        val number = l.substringBefore(".").trim()
                        val content = l.substringAfter(".").trim()
                        Row(modifier = Modifier.padding(vertical = 3.dp)) {
                            Text(
                                text = "$number.",
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.SemiBold,
                                color = accentColor,
                                modifier = Modifier.width(24.dp),
                            )
                            Text(
                                text = content,
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.SemiBold,
                                color = SapiSehatColors.TextPrimary,
                                lineHeight = 24.sp,
                            )
                        }
                    }
                    l.startsWith("  -") || l.startsWith("  •") -> {
                        // Sub-bullet (indented)
                        Row(modifier = Modifier.padding(start = 16.dp, top = 2.dp, bottom = 2.dp)) {
                            Text(
                                text = "–",
                                style = MaterialTheme.typography.bodyMedium,
                                color = SapiSehatColors.TextSecondary,
                                modifier = Modifier.width(16.dp),
                            )
                            Text(
                                text = l.removePrefix("  -").removePrefix("  •").trim(),
                                style = MaterialTheme.typography.bodyMedium,
                                color = SapiSehatColors.TextPrimary,
                                lineHeight = 22.sp,
                            )
                        }
                    }
                    else -> {
                        // Regular paragraph text
                        Text(
                            text = l,
                            style = MaterialTheme.typography.bodyLarge,
                            color = SapiSehatColors.TextPrimary,
                            lineHeight = 24.sp,
                            modifier = Modifier.padding(vertical = 2.dp),
                        )
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
        }
    }
}
