package com.sapisehat.app.ui.splash

import android.content.Context
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.ui.theme.SapiSehatTheme
import kotlinx.coroutines.delay

@Composable
fun SplashRoute(onFinish: (hasOnboarded: Boolean) -> Unit) {
    val context = LocalContext.current
    val hasOnboarded = remember {
        context.getSharedPreferences(
            context.packageName + "_preferences",
            Context.MODE_PRIVATE,
        ).getBoolean("has_completed_onboarding", false)
    }

    LaunchedEffect(Unit) {
        delay(2000L)
        onFinish(hasOnboarded)
    }

    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { visible = true }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        SapiSehatColors.Primary,
                        SapiSehatColors.PrimaryLight,
                    ),
                ),
            ),
        contentAlignment = Alignment.Center,
    ) {
        AnimatedVisibility(
            visible = visible,
            enter = fadeIn() + slideInVertically(initialOffsetY = { it / 4 }),
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                // Logo mark — bold letter in a circle
                Box(
                    modifier = Modifier
                        .size(96.dp)
                        .clip(CircleShape)
                        .background(Color.White.copy(alpha = 0.15f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = "S",
                        fontSize = 44.sp,
                        fontWeight = FontWeight.Black,
                        color = Color.White,
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                // App name
                Text(
                    text = "SapiSehat",
                    style = MaterialTheme.typography.headlineLarge,
                    fontWeight = FontWeight.Black,
                    color = Color.White,
                    letterSpacing = (-1).sp,
                )

                Spacer(modifier = Modifier.height(6.dp))

                // Subtitle
                Text(
                    text = stringResource(R.string.splash_subtitle),
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.75f),
                )

                Spacer(modifier = Modifier.height(56.dp))

                // Loading indicator
                CircularProgressIndicator(
                    color = SapiSehatColors.Secondary,
                    strokeWidth = 2.5.dp,
                    modifier = Modifier.size(24.dp),
                )

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = stringResource(R.string.splash_loading),
                    style = MaterialTheme.typography.labelMedium,
                    color = Color.White.copy(alpha = 0.6f),
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun SplashRoutePreview() {
    SapiSehatTheme {
        SplashRoute(onFinish = {})
    }
}
