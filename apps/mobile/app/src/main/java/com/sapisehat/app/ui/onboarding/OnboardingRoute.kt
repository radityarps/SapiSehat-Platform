package com.sapisehat.app.ui.onboarding

import android.content.Context
import androidx.annotation.StringRes
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.layout.ContentScale
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import coil.decode.SvgDecoder
import coil.request.ImageRequest
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.ui.theme.SapiSehatTheme
import kotlinx.coroutines.launch

data class OnboardingSlide(
    val illustrationAsset: String,
    @StringRes val titleRes: Int,
    @StringRes val bodyRes: Int,
)

val slides = listOf(
    OnboardingSlide("onboarding/veterinary-clinic.svg", R.string.onboarding_title_1, R.string.onboarding_body_1),
    OnboardingSlide("onboarding/undraw_no-signal_nqfa.svg", R.string.onboarding_title_2, R.string.onboarding_body_2),
    OnboardingSlide("onboarding/undraw_correct-answer_vjt7.svg", R.string.onboarding_title_3, R.string.onboarding_body_3),
)

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun OnboardingRoute(onFinish: () -> Unit) {
    val context = LocalContext.current
    val pagerState = rememberPagerState(pageCount = { slides.size })
    val coroutineScope = rememberCoroutineScope()
    val currentPage = pagerState.currentPage
    val isLastPage = currentPage == slides.lastIndex

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SapiSehatColors.Background),
    ) {
        // Header logo and skip button
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp, start = 20.dp, end = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Image(
                    painter = painterResource(R.drawable.logo),
                    contentDescription = stringResource(R.string.app_name),
                    modifier = Modifier.size(40.dp),
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.app_name),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = SapiSehatColors.Primary,
                )
            }
            TextButton(onClick = onFinish) {
                Text(
                    text = stringResource(R.string.onboarding_skip),
                    color = SapiSehatColors.TextSecondary,
                )
            }
        }

        // Horizontal pager
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.weight(1f),
        ) { page ->
            SlideContent(slide = slides[page])
        }

        // Pill-shaped page indicator
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 24.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            repeat(slides.size) { index ->
                val isActive = index == currentPage
                val color by animateColorAsState(
                    targetValue = if (isActive) SapiSehatColors.Primary
                    else SapiSehatColors.Outline,
                    label = "dotColor",
                )
                val width by animateDpAsState(
                    targetValue = if (isActive) 24.dp else 8.dp,
                    label = "dotWidth",
                )

                Box(
                    modifier = Modifier
                        .padding(horizontal = 4.dp)
                        .height(8.dp)
                        .width(width)
                        .clip(RoundedCornerShape(4.dp))
                        .background(color),
                )
            }
        }

        // CTA button
        Button(
            onClick = {
                if (isLastPage) {
                    context.getSharedPreferences(
                        context.packageName + "_preferences",
                        Context.MODE_PRIVATE,
                    )
                        .edit()
                        .putBoolean("has_completed_onboarding", true)
                        .apply()
                    onFinish()
                } else {
                    coroutineScope.launch {
                        pagerState.animateScrollToPage(currentPage + 1)
                    }
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .padding(horizontal = 24.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = SapiSehatColors.Primary,
                contentColor = SapiSehatColors.OnPrimary,
            ),
        ) {
            Text(
                text = stringResource(
                    if (isLastPage) R.string.onboarding_start
                    else R.string.onboarding_next,
                ),
                style = MaterialTheme.typography.labelLarge,
            )
        }

        Spacer(modifier = Modifier.height(32.dp))
    }
}

@Composable
private fun SlideContent(slide: OnboardingSlide) {
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        AsyncImage(
            model = ImageRequest.Builder(context)
                .data("file:///android_asset/${slide.illustrationAsset}")
                .decoderFactory(SvgDecoder.Factory())
                .build(),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.36f),
        )

        Spacer(modifier = Modifier.height(32.dp))

        Text(
            text = stringResource(slide.titleRes),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center,
            color = SapiSehatColors.TextPrimary,
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = stringResource(slide.bodyRes),
            style = MaterialTheme.typography.bodyLarge,
            color = SapiSehatColors.TextSecondary,
            textAlign = TextAlign.Center,
            lineHeight = MaterialTheme.typography.bodyLarge.lineHeight,
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun OnboardingRoutePreview() {
    SapiSehatTheme {
        OnboardingRoute(onFinish = {})
    }
}
