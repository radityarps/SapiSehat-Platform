package com.sapisehat.app.ui.camera

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.sapisehat.app.R
import com.sapisehat.app.ml.quality.RejectionReason
import com.sapisehat.app.ui.theme.SapiSehatColors

/**
 * Displays a quality warning overlay when an image is rejected by the quality gate.
 *
 * Shows a warning icon, title, localized descriptions for each rejection reason,
 * and a contextual action button (Retake for camera, Choose Another for gallery).
 *
 * Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.6
 */
@Composable
fun ImageQualityWarning(
    reasons: Set<RejectionReason>,
    isFromCamera: Boolean,
    onRetake: () -> Unit,
    onChooseAnother: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(SapiSehatColors.OnBackground.copy(alpha = 0.6f)),
        contentAlignment = Alignment.Center,
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(
                containerColor = SapiSehatColors.Surface,
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                // Warning icon
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .clip(CircleShape)
                        .background(SapiSehatColors.ErrorContainer),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Warning,
                        contentDescription = null,
                        modifier = Modifier.size(32.dp),
                        tint = SapiSehatColors.Error,
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Title
                Text(
                    text = stringResource(R.string.quality_warning_title),
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    color = SapiSehatColors.TextPrimary,
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Rejection reason descriptions
                for (reason in reasons) {
                    Text(
                        text = reasonToString(reason),
                        style = MaterialTheme.typography.bodyMedium,
                        color = SapiSehatColors.TextSecondary,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Action button
                if (isFromCamera) {
                    Button(
                        onClick = onRetake,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SapiSehatColors.Primary,
                            contentColor = SapiSehatColors.OnPrimary,
                        ),
                    ) {
                        Text(
                            text = stringResource(R.string.quality_retake),
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                } else {
                    Button(
                        onClick = onChooseAnother,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SapiSehatColors.Primary,
                            contentColor = SapiSehatColors.OnPrimary,
                        ),
                    ) {
                        Text(
                            text = stringResource(R.string.quality_choose_another),
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }
        }
    }
}

/**
 * Maps a [RejectionReason] to its localized string resource.
 */
@Composable
private fun reasonToString(reason: RejectionReason): String {
    return when (reason) {
        RejectionReason.TOO_BLURRY -> stringResource(R.string.quality_too_blurry)
        RejectionReason.TOO_DARK -> stringResource(R.string.quality_too_dark)
        RejectionReason.TOO_SMALL -> stringResource(R.string.quality_too_small)
        RejectionReason.UNREADABLE -> stringResource(R.string.quality_unreadable)
    }
}
