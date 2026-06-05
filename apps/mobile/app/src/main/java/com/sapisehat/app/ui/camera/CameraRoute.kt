package com.sapisehat.app.ui.camera

import android.Manifest
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.FlashAuto
import androidx.compose.material.icons.outlined.FlashOff
import androidx.compose.material.icons.outlined.FlashOn
import androidx.compose.material.icons.outlined.GridOn
import androidx.compose.material.icons.outlined.GridOff
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sapisehat.app.R
import com.sapisehat.app.ui.components.UploadConsentPanel
import com.sapisehat.app.ui.theme.SapiSehatColors
import org.json.JSONObject
import java.io.File
import java.util.UUID

@Composable
fun CameraRoute(
    onShowResult: (label: String, confidence: Float, mode: String, scoresJson: String, imageRef: String, timestamp: Long, detectionId: Long?) -> Unit,
    onOpenHistory: () -> Unit,
    navigationViewModel: com.sapisehat.app.ui.navigation.NavigationViewModel? = null,
    viewModel: CameraViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val updateDetectionId: Long? = navigationViewModel?.updateDetectionId?.collectAsStateWithLifecycle(null)?.value ?: null
    val context = LocalContext.current
    val activity = context as ComponentActivity

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        val permanentlyDenied = !granted && !ActivityCompat.shouldShowRequestPermissionRationale(
            activity, Manifest.permission.CAMERA,
        )
        viewModel.onPermissionResult(granted, permanentlyDenied)
    }

    val galleryLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent(),
    ) { uri ->
        uri?.let {
            viewModel.classify(it, updateDetectionId, isFromCamera = false) { result ->
                val scoresJson = JSONObject(result.allScores).toString()
                onShowResult(
                    result.label,
                    result.confidence,
                    result.inferenceMode.name,
                    scoresJson,
                    it.toString(),
                    System.currentTimeMillis(),
                    result.id,
                )
                navigationViewModel?.clearUpdateDetectionId()
            }
        }
    }

    LaunchedEffect(Unit) {
        viewModel.checkPermission()
        if (!state.hasCameraPermission && !state.permissionPermanentlyDenied) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    if (!state.hasCameraPermission) {
        CameraPermissionScreen(
            permanentlyDenied = state.permissionPermanentlyDenied,
            onRequestPermission = { permissionLauncher.launch(Manifest.permission.CAMERA) },
            onOpenSettings = {
                val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                    data = Uri.fromParts("package", context.packageName, null)
                }
                context.startActivity(intent)
            },
        )
    } else {
        CameraActiveScreen(
            state = state,
            onCapture = { uri ->
                viewModel.classify(uri, updateDetectionId, isFromCamera = true) { result ->
                    val scoresJson = JSONObject(result.allScores).toString()
                    onShowResult(
                        result.label,
                        result.confidence,
                        result.inferenceMode.name,
                        scoresJson,
                        uri.toString(),
                        System.currentTimeMillis(),
                        result.id,
                    )
                    navigationViewModel?.clearUpdateDetectionId()
                }
            },
            onCaptureError = { viewModel.onCaptureError(it) },
            onGalleryOpen = { galleryLauncher.launch("image/*") },
            onCycleFlash = viewModel::cycleFlashMode,
            onToggleGrid = viewModel::toggleGrid,
            onDismissError = viewModel::clearError,
            onConsentAllow = {
                viewModel.onConsentDecision(true) { result ->
                    val scoresJson = JSONObject(result.allScores).toString()
                    onShowResult(
                        result.label,
                        result.confidence,
                        result.inferenceMode.name,
                        scoresJson,
                        state.pendingImageUri?.toString().orEmpty(),
                        System.currentTimeMillis(),
                        result.id,
                    )
                    navigationViewModel?.clearUpdateDetectionId()
                }
            },
            onConsentDeny = {
                viewModel.onConsentDecision(false) { result ->
                    val scoresJson = JSONObject(result.allScores).toString()
                    onShowResult(
                        result.label,
                        result.confidence,
                        result.inferenceMode.name,
                        scoresJson,
                        state.pendingImageUri?.toString().orEmpty(),
                        System.currentTimeMillis(),
                        result.id,
                    )
                    navigationViewModel?.clearUpdateDetectionId()
                }
            },
            onRetake = { viewModel.clearQualityRejection() },
            onChooseAnother = {
                viewModel.clearQualityRejection()
                galleryLauncher.launch("image/*")
            },
        )
    }
}

// ════════════════════════════════════════════════════════════════════════════════
// Camera Active Screen
// ════════════════════════════════════════════════════════════════════════════════

@Composable
private fun CameraActiveScreen(
    state: CameraUiState,
    onCapture: (Uri) -> Unit,
    onCaptureError: (String) -> Unit,
    onGalleryOpen: () -> Unit,
    onCycleFlash: () -> Unit,
    onToggleGrid: () -> Unit,
    onDismissError: () -> Unit,
    onConsentAllow: () -> Unit,
    onConsentDeny: () -> Unit,
    onRetake: () -> Unit,
    onChooseAnother: () -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val captureFailedMessage = stringResource(R.string.camera_error_capture_failed)
    val cameraNotReadyMessage = stringResource(R.string.camera_error_not_ready)

    val imageCapture = remember {
        ImageCapture.Builder()
            .setFlashMode(ImageCapture.FLASH_MODE_AUTO)
            .build()
    }
    val cameraProviderRef = remember { mutableStateOf<ProcessCameraProvider?>(null) }

    LaunchedEffect(state.flashMode) {
        imageCapture.flashMode = when (state.flashMode) {
            FlashMode.AUTO -> ImageCapture.FLASH_MODE_AUTO
            FlashMode.ON -> ImageCapture.FLASH_MODE_ON
            FlashMode.OFF -> ImageCapture.FLASH_MODE_OFF
        }
    }

    DisposableEffect(Unit) {
        onDispose { cameraProviderRef.value?.unbindAll() }
    }

    fun takePhoto() {
        Log.d("SapiSehat", "Camera: takePhoto() triggered")
        val photoFile = File(context.cacheDir, "camera_${UUID.randomUUID()}.jpg")
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
        try {
            imageCapture.takePicture(
                outputOptions,
                ContextCompat.getMainExecutor(context),
                object : ImageCapture.OnImageSavedCallback {
                    override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                        Log.d("SapiSehat", "Camera: image saved successfully, uri=$photoFile")
                        onCapture(Uri.fromFile(photoFile))
                    }
                    override fun onError(exc: ImageCaptureException) {
                        Log.e("SapiSehat", "Camera: capture error", exc)
                        onCaptureError(exc.message ?: captureFailedMessage)
                    }
                },
            )
        } catch (e: Exception) {
            Log.e("SapiSehat", "Camera: takePicture() threw", e)
            onCaptureError(e.message ?: cameraNotReadyMessage)
        }
    }

    // ── UI ──────────────────────────────────────────────────────────────────

    Scaffold(
        snackbarHost = {
            SnackbarHost(hostState = rememberSnackbarHostStateForError(state.error, onDismissError))
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            // Camera preview
            AndroidView(
                factory = { ctx ->
                    PreviewView(ctx).also { previewView ->
                        previewView.implementationMode = PreviewView.ImplementationMode.COMPATIBLE
                        val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                        cameraProviderFuture.addListener({
                            val cameraProvider = cameraProviderFuture.get()
                            cameraProviderRef.value = cameraProvider
                            val preview = Preview.Builder().build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }
                            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
                            try {
                                cameraProvider.unbindAll()
                                cameraProvider.bindToLifecycle(
                                    lifecycleOwner,
                                    cameraSelector,
                                    preview,
                                    imageCapture,
                                )
                                Log.d("SapiSehat", "Camera: binding successful")
                            } catch (e: Exception) {
                                Log.e("SapiSehat", "Camera: binding failed", e)
                                onCaptureError(context.getString(R.string.camera_error_access, e.message.orEmpty()))
                            }
                        }, ContextCompat.getMainExecutor(ctx))
                    }
                },
                modifier = Modifier.fillMaxSize(),
            )

            // Grid overlay
            if (state.showGrid) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val w = size.width
                    val h = size.height
                    val lineColor = Color.White.copy(alpha = 0.3f)
                    val strokeW = 1.dp.toPx()
                    drawLine(lineColor, Offset(0f, h / 3), Offset(w, h / 3), strokeWidth = strokeW)
                    drawLine(lineColor, Offset(0f, 2 * h / 3), Offset(w, 2 * h / 3), strokeWidth = strokeW)
                    drawLine(lineColor, Offset(w / 3, 0f), Offset(w / 3, h), strokeWidth = strokeW)
                    drawLine(lineColor, Offset(2 * w / 3, 0f), Offset(2 * w / 3, h), strokeWidth = strokeW)
                }
            }

            // Guidance label — top center
            Surface(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(top = 48.dp)
                    .statusBarsPadding(),
                shape = RoundedCornerShape(20.dp),
                color = Color.Black.copy(alpha = 0.6f),
            ) {
                Text(
                    text = stringResource(R.string.camera_guidance),
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 10.dp),
                    color = Color.White,
                    style = MaterialTheme.typography.labelLarge,
                )
            }

            // Top-right controls — proper icons
            Column(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(top = 48.dp, end = 12.dp)
                    .statusBarsPadding(),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                // Flash toggle
                IconButton(
                    onClick = onCycleFlash,
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(Color.Black.copy(alpha = 0.4f)),
                ) {
                    Icon(
                        imageVector = when (state.flashMode) {
                            FlashMode.AUTO -> Icons.Outlined.FlashAuto
                            FlashMode.ON -> Icons.Outlined.FlashOn
                            FlashMode.OFF -> Icons.Outlined.FlashOff
                        },
                        contentDescription = stringResource(R.string.camera_flash_toggle),
                        tint = Color.White,
                        modifier = Modifier.size(22.dp),
                    )
                }

                // Grid toggle
                IconButton(
                    onClick = onToggleGrid,
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(Color.Black.copy(alpha = 0.4f)),
                ) {
                    Icon(
                        imageVector = if (state.showGrid) Icons.Outlined.GridOn else Icons.Outlined.GridOff,
                        contentDescription = stringResource(R.string.camera_grid_toggle),
                        tint = Color.White,
                        modifier = Modifier.size(22.dp),
                    )
                }
            }

            // ── Bottom controls ─────────────────────────────────────────────

            Row(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(bottom = 40.dp, start = 32.dp, end = 32.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                // Gallery button
                IconButton(
                    onClick = onGalleryOpen,
                    modifier = Modifier
                        .size(52.dp)
                        .clip(CircleShape)
                        .background(Color.Black.copy(alpha = 0.4f)),
                ) {
                    Icon(
                        imageVector = Icons.Outlined.PhotoLibrary,
                        contentDescription = stringResource(R.string.camera_gallery),
                        tint = Color.White,
                        modifier = Modifier.size(26.dp),
                    )
                }

                // Shutter button — bold green ring
                Box(
                    modifier = Modifier
                        .size(76.dp)
                        .border(4.dp, Color.White, CircleShape)
                        .padding(4.dp)
                        .clickable { takePhoto() },
                    contentAlignment = Alignment.Center,
                ) {
                    Box(
                        modifier = Modifier
                            .size(62.dp)
                            .clip(CircleShape)
                            .background(SapiSehatColors.Primary),
                    )
                }

                // Spacer for symmetry
                Spacer(modifier = Modifier.size(52.dp))
            }

            // Loading overlay (hidden when quality warning is shown)
            if (state.isLoading && state.qualityRejection == null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.7f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator(
                            color = SapiSehatColors.Secondary,
                            strokeWidth = 3.dp,
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        state.progressText?.let { text ->
                            Text(
                                text = text,
                                color = Color.White,
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                    }
                }
            }

            // Consent panel overlay
            if (state.showConsentPanel) {
                UploadConsentPanel(
                    onAllow = onConsentAllow,
                    onDeny = onConsentDeny,
                    modifier = Modifier.fillMaxSize(),
                )
            }

            // Quality warning overlay
            if (state.qualityRejection != null) {
                ImageQualityWarning(
                    reasons = state.qualityRejection,
                    isFromCamera = state.rejectedImageIsFromCamera,
                    onRetake = onRetake,
                    onChooseAnother = onChooseAnother,
                    modifier = Modifier.fillMaxSize(),
                )
            }
        }
    }
}

// ════════════════════════════════════════════════════════════════════════════════
// Helpers
// ════════════════════════════════════════════════════════════════════════════════

@Composable
private fun rememberSnackbarHostStateForError(
    error: String?,
    onDismiss: () -> Unit,
): SnackbarHostState {
    val snackbarHostState = remember { SnackbarHostState() }
    val okLabel = stringResource(R.string.btn_ok)

    LaunchedEffect(error) {
        error?.let { message ->
            snackbarHostState.showSnackbar(
                message = message,
                actionLabel = okLabel,
                duration = SnackbarDuration.Long,
            )
            onDismiss()
        }
    }

    return snackbarHostState
}

// ── Permission screen ──────────────────────────────────────────────────────────

@Composable
private fun CameraPermissionScreen(
    permanentlyDenied: Boolean,
    onRequestPermission: () -> Unit,
    onOpenSettings: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SapiSehatColors.Background)
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        // Icon instead of nothing
        Box(
            modifier = Modifier
                .size(80.dp)
                .clip(CircleShape)
                .background(SapiSehatColors.PrimaryContainer),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Outlined.PhotoLibrary,
                contentDescription = null,
                modifier = Modifier.size(36.dp),
                tint = SapiSehatColors.Primary,
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = stringResource(R.string.camera_permission_title),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center,
            color = SapiSehatColors.TextPrimary,
        )
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = if (permanentlyDenied) stringResource(R.string.camera_permission_denied)
            else stringResource(R.string.camera_permission_desc),
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
            color = SapiSehatColors.TextSecondary,
        )
        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = if (permanentlyDenied) onOpenSettings else onRequestPermission,
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
                text = stringResource(
                    if (permanentlyDenied) R.string.settings_title
                    else R.string.camera_permission_grant,
                ),
                style = MaterialTheme.typography.labelLarge,
            )
        }
    }
}
