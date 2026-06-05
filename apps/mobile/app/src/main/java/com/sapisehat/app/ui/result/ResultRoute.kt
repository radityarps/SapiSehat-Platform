package com.sapisehat.app.ui.result

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
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
import coil.compose.AsyncImage
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sapisehat.app.R
import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.EarlyDetectionOutcome
import com.sapisehat.app.domain.model.ImageSource
import com.sapisehat.app.domain.model.InferenceMode
import com.sapisehat.app.domain.model.LocationSource
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.ui.theme.SapiSehatTheme
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date

// ════════════════════════════════════════════════════════════════════════
// Data helpers
// ════════════════════════════════════════════════════════════════════════

private data class ClassDisplayConfig(
    val labelKey: String,
    @param:StringRes val displayNameResId: Int,
    val icon: String,
    val color: Color,
    @param:StringRes val adviceResId: Int,
)

private val classConfigs = mapOf(
    "sehat" to ClassDisplayConfig("sehat", R.string.result_disease_sehat, "●", SapiSehatColors.Healthy, R.string.result_advice_sehat),
    "healthy" to ClassDisplayConfig("sehat", R.string.result_disease_sehat, "●", SapiSehatColors.Healthy, R.string.result_advice_sehat),
    "pmk" to ClassDisplayConfig("pmk", R.string.result_disease_fmd, "●", SapiSehatColors.DangerPMK, R.string.result_advice_fmd),
    "fmd" to ClassDisplayConfig("pmk", R.string.result_disease_fmd, "●", SapiSehatColors.DangerPMK, R.string.result_advice_fmd),
    "lsd" to ClassDisplayConfig("lsd", R.string.result_disease_lsd, "●", SapiSehatColors.WarningLSD, R.string.result_advice_lsd),
    "lato_lato" to ClassDisplayConfig("lsd", R.string.result_disease_lsd, "●", SapiSehatColors.WarningLSD, R.string.result_advice_lsd),
    "lumpy_skin_disease" to ClassDisplayConfig("lsd", R.string.result_disease_lsd, "●", SapiSehatColors.WarningLSD, R.string.result_advice_lsd),
)

private val defaultClassConfig = ClassDisplayConfig(
    "unknown", R.string.result_unknown, "●",
    SapiSehatColors.TextSecondary, R.string.result_advice_sehat,
)

private enum class ConfidenceLevel { HIGH, MEDIUM, LOW }

private fun confidenceLevel(value: Float): ConfidenceLevel = when {
    value >= 0.80f -> ConfidenceLevel.HIGH
    value >= 0.60f -> ConfidenceLevel.MEDIUM
    else -> ConfidenceLevel.LOW
}

@StringRes
private fun scoreDisplayNameRes(key: String): Int? = when (key.lowercase()) {
    "sehat", "healthy" -> R.string.result_disease_sehat
    "pmk", "fmd" -> R.string.result_disease_fmd
    "lsd", "lato_lato", "lumpy_skin_disease" -> R.string.result_disease_lsd
    else -> null
}

@StringRes
private fun modeLabelRes(mode: String): Int = when (mode.uppercase()) {
    "ONLINE" -> R.string.result_mode_online
    else -> R.string.result_mode_offline
}

private fun modeColor(mode: String): Color = if (mode.uppercase() == "ONLINE") {
    SapiSehatColors.Healthy
} else {
    SapiSehatColors.WarningLSD
}

// ════════════════════════════════════════════════════════════════════════
// Main screen
// ════════════════════════════════════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultRoute(
    label: String,
    confidence: Float,
    mode: String,
    allScoresJson: String,
    imageRef: String,
    scanTimestamp: Long,
    detectionId: Long? = null,
    fromHistory: Boolean = false,
    appVersion: String? = null,
    modelVersion: String? = null,
    consentStatus: ConsentStatus = ConsentStatus.UNDECIDED,
    navigationViewModel: com.sapisehat.app.ui.navigation.NavigationViewModel? = null,
    onBack: () -> Unit,
    onRetake: () -> Unit,
    onNavigateToGuide: (String) -> Unit = {},
    viewModel: ResultViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val locale = LocalConfiguration.current.locales[0]
    val confidencePercent = (confidence.coerceIn(0f, 1f) * 100).toInt()
    val level = confidenceLevel(confidence)
    val selectedDetection by viewModel.selectedDetection.collectAsStateWithLifecycle()
    val routeHasInsufficientEvidence = label == "INSUFFICIENT_VISUAL_EVIDENCE"
    val selectedOutcome = selectedDetection?.outcome
    val hasInsufficientEvidence = selectedOutcome == EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE ||
        (selectedOutcome == null && routeHasInsufficientEvidence)
    val config = if (hasInsufficientEvidence) defaultClassConfig else classConfigs[label.lowercase()] ?: defaultClassConfig
    val scannedAt = if (scanTimestamp > 0L) Date(scanTimestamp) else Date()
    val scannedAtText = SimpleDateFormat("dd MMM yyyy, HH:mm", locale).format(scannedAt)
    val modeLabel = stringResource(modeLabelRes(mode))
    val displayName = if (hasInsufficientEvidence) {
        stringResource(R.string.result_insufficient_visual_evidence)
    } else {
        stringResource(config.displayNameResId)
    }
    val modeBadgeColor = modeColor(mode)

    val levelTextId = when (level) {
        ConfidenceLevel.HIGH -> R.string.result_confidence_high
        ConfidenceLevel.MEDIUM -> R.string.result_confidence_medium
        ConfidenceLevel.LOW -> R.string.result_confidence_low
    }
    val levelColor = when (level) {
        ConfidenceLevel.HIGH -> SapiSehatColors.Healthy
        ConfidenceLevel.MEDIUM -> SapiSehatColors.WarningLSD
        ConfidenceLevel.LOW -> SapiSehatColors.DangerPMK
    }
    val isUnreliable = confidence < 0.70f || hasInsufficientEvidence

    // Parse scores map
    val allScores: Map<String, Float> = remember(allScoresJson) {
        try {
            val json = JSONObject(allScoresJson)
            json.keys().asSequence().associate { key ->
                key to json.getDouble(key).toFloat()
            }
        } catch (_: Exception) {
            emptyMap()
        }
    }

    val snackbarHostState = androidx.compose.runtime.remember { SnackbarHostState() }
    val noteSaved by viewModel.noteSaved.collectAsStateWithLifecycle()
    val noteTitle = selectedDetection?.title?.takeIf { it.isNotBlank() }
    val noteDescription = selectedDetection?.description?.takeIf { it.isNotBlank() }
    // Resolve metadata from persisted detection when viewing from history
    val resolvedConsentStatus = selectedDetection?.consentStatus ?: consentStatus
    val resolvedAppVersion = selectedDetection?.appVersion ?: appVersion
    val resolvedModelVersion = selectedDetection?.modelVersion ?: modelVersion
    val resolvedPreprocessingSummary = selectedDetection?.preprocessingSummary
    val resolvedImageSource = selectedDetection?.imageSource
    val resolvedLatitude = selectedDetection?.latitude
    val resolvedLongitude = selectedDetection?.longitude
    val resolvedLocationSource = selectedDetection?.locationSource
    val savedMessage = stringResource(R.string.result_saved)

    // Build the DetectionResult used for PDF export/share. Prefer the persisted
    // detection (richest metadata); fall back to route params for a freshly
    // produced result that may not be loaded from the DB yet.
    fun buildExportResult(): DetectionResult {
        selectedDetection?.let { return it }
        return DetectionResult(
            id = detectionId ?: 0L,
            imagePath = imageRef.takeIf { it.isNotBlank() },
            label = label,
            displayLabel = displayName,
            confidence = confidence,
            isReliable = confidence >= 0.60f,
            outcome = if (hasInsufficientEvidence) {
                EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE
            } else {
                EarlyDetectionOutcome.DISEASE_CLASS
            },
            allScores = allScores,
            inferenceMode = runCatching { InferenceMode.valueOf(mode.uppercase()) }
                .getOrDefault(InferenceMode.OFFLINE),
            consentStatus = consentStatus,
            timestamp = if (scanTimestamp > 0L) scanTimestamp else System.currentTimeMillis(),
            appVersion = appVersion,
            modelVersion = modelVersion,
        )
    }
    LaunchedEffect(detectionId) {
        viewModel.setDetectionId(detectionId)
    }
    LaunchedEffect(noteSaved) {
        if (noteSaved) {
            snackbarHostState.showSnackbar(savedMessage)
            viewModel.consumeNoteSaved()
        }
    }

    val pdfPath by viewModel.pdfPath.collectAsStateWithLifecycle()
    val pdfError by viewModel.pdfError.collectAsStateWithLifecycle()
    val pdfExportedMessage = stringResource(R.string.result_pdf_exported)
    val pdfFailedMessage = stringResource(R.string.result_pdf_failed)

    LaunchedEffect(pdfPath) {
        pdfPath?.let { path ->
            // Share the generated PDF
            val file = java.io.File(path)
            if (file.exists()) {
                val uri = androidx.core.content.FileProvider.getUriForFile(
                    context, "${context.packageName}.fileprovider", file,
                )
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "application/pdf"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    putExtra(Intent.EXTRA_SUBJECT, context.getString(R.string.result_share_title))
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                runCatching {
                    context.startActivity(Intent.createChooser(intent, context.getString(R.string.result_share_chooser)))
                }
            }
            snackbarHostState.showSnackbar(pdfExportedMessage)
            viewModel.consumePdfPath()
        }
    }
    LaunchedEffect(pdfError) {
        if (pdfError) {
            snackbarHostState.showSnackbar(pdfFailedMessage)
            viewModel.consumePdfError()
        }
    }

    var showSaveDialog by rememberSaveable { mutableStateOf(false) }
    var saveTitle by rememberSaveable { mutableStateOf("") }
    var saveDesc by rememberSaveable { mutableStateOf("") }

    if (showSaveDialog) {
        AlertDialog(
            onDismissRequest = { showSaveDialog = false },
            title = {
                Text(
                    stringResource(
                        if (fromHistory) R.string.result_edit_dialog_title else R.string.result_save_dialog_title,
                    ),
                )
            },
            text = {
                Column {
                    OutlinedTextField(
                        value = saveTitle,
                        onValueChange = { saveTitle = it },
                        label = { Text(stringResource(R.string.result_save_hint_title)) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = saveDesc,
                        onValueChange = { saveDesc = it },
                        label = { Text(stringResource(R.string.result_save_hint_desc)) },
                        modifier = Modifier.fillMaxWidth(),
                        minLines = 3,
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    showSaveDialog = false
                    detectionId?.let { viewModel.saveNote(it, saveTitle, saveDesc) }
                }) {
                    Text(stringResource(if (fromHistory) R.string.result_btn_edit else R.string.result_btn_save))
                }
            },
            dismissButton = {
                TextButton(onClick = { showSaveDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        stringResource(R.string.result_diagnosis),
                        style = MaterialTheme.typography.titleLarge,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.nav_back))
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
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 8.dp),
        ) {
            // ── 1. Photo placeholder ──────────────────────────────────
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp),
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.surfaceVariant,
            ) {
                val model = resolveImageModel(imageRef)
                if (model != null) {
                    AsyncImage(
                        model = model,
                        contentDescription = stringResource(R.string.result_scan_image),
                        modifier = Modifier.fillMaxSize(),
                    )
                } else {
                    Box(contentAlignment = Alignment.Center) {
                        Text(config.icon, fontSize = 48.sp)
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            Surface(
                shape = RoundedCornerShape(12.dp),
                color = modeBadgeColor.copy(alpha = 0.15f),
            ) {
                Text(
                    text = modeLabel,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    style = MaterialTheme.typography.labelLarge,
                    color = modeBadgeColor,
                )
            }

            Spacer(Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.result_scanned_at, scannedAtText),
                style = MaterialTheme.typography.bodyMedium,
                color = SapiSehatColors.TextSecondary,
            )

            // Accessibility: full summary description for screen readers
            val accessibilitySummary = stringResource(
                R.string.result_accessibility_summary,
                displayName,
                confidencePercent,
                stringResource(levelTextId),
                modeLabel,
            )

            if (noteTitle != null || noteDescription != null) {
                Spacer(Modifier.height(16.dp))
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f),
                    ),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = stringResource(R.string.result_saved_note_title),
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                            color = SapiSehatColors.TextSecondary,
                        )
                        noteTitle?.let {
                            Spacer(Modifier.height(6.dp))
                            Text(
                                text = it,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = SapiSehatColors.TextPrimary,
                            )
                        }
                        noteDescription?.let {
                            Spacer(Modifier.height(6.dp))
                            Text(
                                text = it,
                                style = MaterialTheme.typography.bodyMedium,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))
            HorizontalDivider()
            Spacer(Modifier.height(16.dp))

            // ── 2. Confidence summary ─────────────────────────────────
            Text(
                text = displayName,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = config.color,
                modifier = Modifier.semantics {
                    heading()
                    contentDescription = accessibilitySummary
                },
            )

            Spacer(Modifier.height(4.dp))

            Text(
                text = "${stringResource(R.string.result_confidence)} ${confidencePercent}%",
                style = MaterialTheme.typography.titleMedium,
            )

            Text(
                text = stringResource(levelTextId),
                color = levelColor,
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(Modifier.height(12.dp))

            // ── 3. Confidence bar ─────────────────────────────────────
            ConfidenceBar(confidence = confidence, color = config.color)

            Spacer(Modifier.height(24.dp))

            // ── 4. All scores ─────────────────────────────────────────
            Text(
                text = stringResource(R.string.result_all_scores),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(Modifier.height(12.dp))

            val sortedScores = allScores.entries.sortedByDescending { it.value }
            if (sortedScores.isEmpty()) {
                Text(
                    text = "—",
                    color = SapiSehatColors.TextSecondary,
                    style = MaterialTheme.typography.bodyMedium,
                )
            } else {
                sortedScores.forEach { (key, score) ->
                    val isHighlighted = isLabelMatch(key, config.labelKey)
                    ScoreRow(
                        label = scoreDisplayNameRes(key)?.let { stringResource(it) } ?: key.replace("_", " "),
                        score = score,
                        isHighlighted = isHighlighted,
                        color = config.color,
                    )
                    Spacer(Modifier.height(8.dp))
                }
            }

            Spacer(Modifier.height(20.dp))

            Card(
                colors = CardDefaults.cardColors(
                    containerColor = SapiSehatColors.SecondaryContainer.copy(alpha = 0.5f),
                ),
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = stringResource(R.string.result_advice_title),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(Modifier.height(12.dp))
                    val adviceText = if (hasInsufficientEvidence) {
                        stringResource(R.string.result_advice_insufficient_visual_evidence)
                    } else {
                        stringResource(config.adviceResId)
                    }
                    adviceText.split("\n").forEach { line ->
                        Row(modifier = Modifier.padding(vertical = 4.dp)) {
                            Text(
                                "•  ",
                                color = config.color,
                                style = MaterialTheme.typography.bodyLarge,
                            )
                            Text(line, style = MaterialTheme.typography.bodyLarge)
                        }
                    }
                }
            }

            // "Learn More" cross-link to Guide
            if (!hasInsufficientEvidence) TextButton(
                onClick = {
                    // Use canonical label and fall back to substring matching for robustness
                    val canonicalLabel = (selectedDetection?.label ?: label).lowercase()
                    val guideArticleId = when {
                        canonicalLabel == "pmk" || canonicalLabel == "fmd" -> "fmd_1"
                        canonicalLabel == "lsd" || canonicalLabel == "lato_lato" -> "lsd_1"
                        canonicalLabel == "sehat" || canonicalLabel == "healthy" -> "healthy_1"
                        canonicalLabel.contains("fmd") || canonicalLabel.contains("pmk") -> "fmd_1"
                        canonicalLabel.contains("lsd") || canonicalLabel.contains("lato") -> "lsd_1"
                        canonicalLabel.contains("healthy") || canonicalLabel.contains("sehat") -> "healthy_1"
                        else -> "fmd_1"
                    }
                    onNavigateToGuide(guideArticleId)
                },
            ) {
                Text(
                    text = stringResource(R.string.result_learn_more),
                    style = MaterialTheme.typography.labelLarge,
                    color = config.color,
                )
            }

            if (level != ConfidenceLevel.HIGH) {
                Spacer(Modifier.height(12.dp))
                if (isUnreliable) {
                    // Low confidence: explicit unreliable state with retake prompt
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = SapiSehatColors.ErrorContainer,
                        ),
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = stringResource(R.string.result_unreliable_title),
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = SapiSehatColors.DangerPMK,
                            )
                            Spacer(Modifier.height(8.dp))
                            Text(
                                text = stringResource(R.string.result_unreliable_body),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            if (!fromHistory) {
                                Spacer(Modifier.height(12.dp))
                                Button(
                                    onClick = onRetake,
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = SapiSehatColors.DangerPMK,
                                    ),
                                ) {
                                    Text(stringResource(R.string.result_btn_retake_low))
                                }
                            }
                        }
                    }
                } else {
                    // Medium confidence: warning only
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = SapiSehatColors.WarningLSD.copy(alpha = 0.15f),
                        ),
                    ) {
                        Row(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = stringResource(R.string.result_warning_medium),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // ── Disclaimer ────────────────────────────────────────────
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f),
                ),
            ) {
                Text(
                    text = stringResource(R.string.result_disclaimer),
                    modifier = Modifier.padding(12.dp),
                    style = MaterialTheme.typography.bodySmall,
                    color = SapiSehatColors.TextSecondary,
                )
            }

            // ── Metadata section ──────────────────────────────────────
            val hasMetadata = resolvedAppVersion != null || resolvedModelVersion != null ||
                resolvedConsentStatus != ConsentStatus.UNDECIDED ||
                resolvedPreprocessingSummary != null || resolvedImageSource != null
            if (hasMetadata) {
                Spacer(Modifier.height(16.dp))
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                    ),
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = stringResource(R.string.result_metadata_title),
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold,
                            color = SapiSehatColors.TextSecondary,
                        )
                        Spacer(Modifier.height(8.dp))
                        resolvedAppVersion?.let {
                            Text(
                                text = stringResource(R.string.result_metadata_app_version, it),
                                style = MaterialTheme.typography.bodySmall,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                        resolvedModelVersion?.let {
                            Text(
                                text = stringResource(R.string.result_metadata_model_version, it),
                                style = MaterialTheme.typography.bodySmall,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                        resolvedPreprocessingSummary?.let {
                            Text(
                                text = stringResource(R.string.result_metadata_preprocessing, it),
                                style = MaterialTheme.typography.bodySmall,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                        resolvedImageSource?.let { source ->
                            val sourceLabel = if (source.name == "CAMERA")
                                stringResource(R.string.result_source_camera)
                            else
                                stringResource(R.string.result_source_gallery)
                            Text(
                                text = stringResource(R.string.result_metadata_source, sourceLabel),
                                style = MaterialTheme.typography.bodySmall,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                        if (resolvedLatitude != null && resolvedLongitude != null) {
                            val sourceLabel = when (resolvedLocationSource) {
                                LocationSource.GPS -> stringResource(R.string.result_location_source_gps)
                                LocationSource.MANUAL -> stringResource(R.string.result_location_source_manual)
                                else -> ""
                            }
                            val locationText = "%.2f, %.2f".format(resolvedLatitude, resolvedLongitude) +
                                if (sourceLabel.isNotEmpty()) " ($sourceLabel)" else ""
                            Text(
                                text = stringResource(R.string.result_metadata_location, locationText),
                                style = MaterialTheme.typography.bodySmall,
                                color = SapiSehatColors.TextSecondary,
                            )
                        }
                        val consentLabel = when (resolvedConsentStatus) {
                            ConsentStatus.ALLOWED -> stringResource(R.string.result_consent_allowed)
                            ConsentStatus.DENIED -> stringResource(R.string.result_consent_denied)
                            ConsentStatus.UNDECIDED -> stringResource(R.string.result_consent_undecided)
                        }
                        Text(
                            text = stringResource(R.string.result_metadata_consent, consentLabel),
                            style = MaterialTheme.typography.bodySmall,
                            color = SapiSehatColors.TextSecondary,
                        )
                    }
                }
            }

            Spacer(Modifier.height(24.dp))

            // ── 5. Action buttons ─────────────────────────────────────
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // Share now generates and shares a PDF report (not plain text)
                OutlinedButton(
                    onClick = {
                        selectedDetection?.let { viewModel.exportPdf(it) }
                    },
                    modifier = Modifier.weight(1f),
                    enabled = selectedDetection != null,
                ) {
                    Text(stringResource(R.string.result_btn_share))
                }
                if (detectionId != null) {
                    Button(
                        onClick = {
                            saveTitle = selectedDetection?.title.orEmpty()
                            saveDesc = selectedDetection?.description.orEmpty()
                            showSaveDialog = true
                        },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SapiSehatColors.Primary,
                        ),
                    ) {
                        Text(stringResource(if (fromHistory) R.string.result_btn_edit else R.string.result_btn_save))
                    }
                }
            }
            if (!fromHistory) {
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = onRetake,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = SapiSehatColors.Primary,
                    ),
                ) {
                    Text(stringResource(R.string.result_btn_retake))
                }
            }

            Spacer(Modifier.height(12.dp))

            Spacer(Modifier.height(16.dp))
        }
    }
}

// ════════════════════════════════════════════════════════════════════════
// Sub-composables
// ════════════════════════════════════════════════════════════════════════

@Composable
private fun ConfidenceBar(confidence: Float, color: Color, modifier: Modifier = Modifier) {
    val fraction = confidence.coerceIn(0f, 1f)
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(12.dp)
            .clip(RoundedCornerShape(6.dp))
            .background(Color.Gray.copy(alpha = 0.15f)),
    ) {
        Spacer(
            modifier = Modifier
                .fillMaxWidth(fraction)
                .height(12.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(
                    Brush.horizontalGradient(
                        colors = listOf(color.copy(alpha = 0.6f), color),
                    ),
                ),
        )
    }
}

private fun resolveImageModel(imageRef: String): Any? {
    if (imageRef.isBlank()) return null
    return when {
        imageRef.startsWith("content://") || imageRef.startsWith("file://") -> Uri.parse(imageRef)
        else -> {
            val file = File(imageRef)
            if (file.exists()) file else null
        }
    }
}

@Composable
private fun ScoreRow(label: String, score: Float, isHighlighted: Boolean, color: Color) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Highlighted / normal circle
        Text(
            text = if (isHighlighted) "●" else "○",
            color = if (isHighlighted) color else SapiSehatColors.TextSecondary,
            fontSize = 14.sp,
        )
        Spacer(Modifier.width(8.dp))

        // Class label — fixed width for alignment
        Text(
            text = label,
            modifier = Modifier.width(80.dp),
            style = MaterialTheme.typography.bodyMedium,
            maxLines = 1,
        )
        Spacer(Modifier.width(8.dp))

        // Progress bar
        LinearProgressIndicator(
            progress = { score.coerceIn(0f, 1f) },
            modifier = Modifier
                .weight(1f)
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp)),
            color = if (isHighlighted) color else SapiSehatColors.TextSecondary,
            trackColor = Color.Gray.copy(alpha = 0.15f),
        )
        Spacer(Modifier.width(8.dp))

        // Percentage
        Text(
            text = "${(score * 100).toInt()}%",
            style = MaterialTheme.typography.labelMedium,
            modifier = Modifier.width(38.dp),
            textAlign = TextAlign.End,
        )
    }
}

// ════════════════════════════════════════════════════════════════════════
// Helpers
// ════════════════════════════════════════════════════════════════════════

private fun isLabelMatch(key: String, targetKey: String): Boolean {
    val k = key.lowercase()
    val t = targetKey.lowercase()
    if (k == t) return true
    // Handle known aliases
    if (t == "pmk" && (k == "pmk" || k == "fmd")) return true
    if (t == "lsd" && (k == "lsd" || k == "lato_lato" || k == "lumpy_skin_disease")) return true
    if (t == "sehat" && (k == "sehat" || k == "healthy")) return true
    return false
}

@Composable
private fun remember(key: Any, block: () -> Map<String, Float>): Map<String, Float> {
    // Simple cache helper to avoid recomputing scores on every recomposition.
    // We inline this so we don't add an extra dependency.
    return androidx.compose.runtime.remember(key) { block() }
}

// ════════════════════════════════════════════════════════════════════════
// Preview
// ════════════════════════════════════════════════════════════════════════

@Preview(showBackground = true)
@Composable
private fun ResultRoutePreview() {
    SapiSehatTheme {
        ResultRoute(
            label = "PMK",
            confidence = 0.87f,
            mode = "ONLINE",
            allScoresJson = """{"PMK":0.87,"Sehat":0.08,"Lato-Lato":0.05}""",
            imageRef = "",
            scanTimestamp = System.currentTimeMillis(),
            appVersion = "1.0.0",
            modelVersion = "MobileNetV2-v3",
            consentStatus = ConsentStatus.ALLOWED,
            onBack = {},
            onRetake = {},
        )
    }
}
