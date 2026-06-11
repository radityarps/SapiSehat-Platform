package com.sapisehat.app.ui.about

import android.app.Activity
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.graphics.ColorUtils
import androidx.core.view.WindowCompat
import com.sapisehat.app.BuildConfig
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.ui.theme.SapiSehatTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutRoute(onBack: () -> Unit, onNavigateToSettings: () -> Unit = {}) {
    val view = LocalView.current
    val statusBarColorArgb = MaterialTheme.colorScheme.surface.toArgb()
    val isLightStatusBar = ColorUtils.calculateLuminance(statusBarColorArgb) > 0.5

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = statusBarColorArgb
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = isLightStatusBar
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.about_title),
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = SapiSehatColors.TextPrimary,
                    )
                },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(
                            Icons.Filled.Settings,
                            contentDescription = stringResource(R.string.settings_title),
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
                windowInsets = TopAppBarDefaults.windowInsets.only(WindowInsetsSides.Horizontal),
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.height(24.dp))

            Image(
                painter = painterResource(R.drawable.logo),
                contentDescription = stringResource(R.string.app_name),
                modifier = Modifier.size(112.dp),
            )

            Spacer(Modifier.height(16.dp))

            // App name
            Text(
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = SapiSehatColors.Primary,
            )

            Spacer(Modifier.height(8.dp))

            // Description
            Text(
                text = stringResource(R.string.about_desc),
                style = MaterialTheme.typography.bodyLarge,
                color = SapiSehatColors.TextSecondary,
                textAlign = TextAlign.Center,
            )

            Spacer(Modifier.height(8.dp))

            // Version
            Text(
                text = "${stringResource(R.string.about_version)}: ${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.labelMedium,
                color = SapiSehatColors.TextSecondary,
            )

            Spacer(Modifier.height(24.dp))

            HorizontalDivider()

            Spacer(Modifier.height(24.dp))

            // Sections
            AboutSection(
                title = stringResource(R.string.about_team_title),
                items = listOf(
                    stringResource(R.string.about_team_member_1),
                    stringResource(R.string.about_team_member_2),
                ),
            )

            Spacer(Modifier.height(12.dp))

            AboutSection(
                title = stringResource(R.string.about_institution_title),
                items = listOf(stringResource(R.string.about_institution)),
            )

            Spacer(Modifier.height(12.dp))

            AboutSection(
                title = stringResource(R.string.about_supervisor_title),
                items = listOf(stringResource(R.string.about_supervisor)),
            )

            Spacer(Modifier.height(12.dp))

            AboutSection(
                title = stringResource(R.string.about_tech_title),
                items = listOf(
                    stringResource(R.string.about_tech_1),
                    stringResource(R.string.about_tech_2),
                    stringResource(R.string.about_tech_3),
                    stringResource(R.string.about_tech_4),
                    stringResource(R.string.about_tech_5),
                ),
            )

            Spacer(Modifier.height(12.dp))

            AboutSection(
                title = stringResource(R.string.about_source_title),
                items = listOf(
                    stringResource(R.string.about_source_1),
                    stringResource(R.string.about_source_2),
                    stringResource(R.string.about_source_3),
                ),
            )

            Spacer(Modifier.height(24.dp))

            // Copyright
            Text(
                text = stringResource(R.string.about_copyright),
                style = MaterialTheme.typography.labelSmall,
                color = SapiSehatColors.TextSecondary,
                textAlign = TextAlign.Center,
            )

            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun AboutSection(title: String, items: List<String>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = SapiSehatColors.Primary,
            )
            Spacer(Modifier.height(8.dp))
            items.forEach { item ->
                Text(
                    text = "•  $item",
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
                Spacer(Modifier.height(4.dp))
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AboutRoutePreview() {
    SapiSehatTheme {
        AboutRoute(onBack = {})
    }
}
