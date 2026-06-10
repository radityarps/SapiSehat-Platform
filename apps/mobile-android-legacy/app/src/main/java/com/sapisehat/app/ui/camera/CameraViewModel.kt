package com.sapisehat.app.ui.camera

import android.Manifest
import android.content.Context
import android.net.Uri
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import com.sapisehat.app.R
import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.domain.model.ClassifyResponse
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.usecase.ClassifyImageUseCase
import com.sapisehat.app.ml.preprocessing.ClientPreprocessor
import com.sapisehat.app.ml.quality.ImageQualityGate
import com.sapisehat.app.ml.quality.QualityResult
import com.sapisehat.app.ml.quality.RejectionReason

enum class FlashMode { AUTO, ON, OFF }

data class CameraUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val progressText: String? = null,
    val hasCameraPermission: Boolean = false,
    val permissionPermanentlyDenied: Boolean = false,
    val flashMode: FlashMode = FlashMode.AUTO,
    val showGrid: Boolean = false,
    val showConsentPanel: Boolean = false,
    val pendingImageUri: Uri? = null,
    val qualityRejection: Set<RejectionReason>? = null,
    val rejectedImageIsFromCamera: Boolean = true,
)

@HiltViewModel
class CameraViewModel @Inject constructor(
    @ApplicationContext private val appContext: Context,
    private val classifyImageUseCase: ClassifyImageUseCase,
    private val settingsDataStore: SettingsDataStore,
    private val clientPreprocessor: ClientPreprocessor,
) : ViewModel() {
    private val _uiState = MutableStateFlow(CameraUiState())
    val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

    private val qualityGate = ImageQualityGate()

    // Track detection ID for retake/update scenario
    private val _updateDetectionId = MutableStateFlow<Long?>(null)
    val updateDetectionId: StateFlow<Long?> = _updateDetectionId.asStateFlow()

    fun setUpdateDetectionId(id: Long?) {
        _updateDetectionId.value = id
    }

    fun checkPermission() {
        val hasPermission = ContextCompat.checkSelfPermission(
            appContext, Manifest.permission.CAMERA
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        _uiState.value = _uiState.value.copy(hasCameraPermission = hasPermission)
    }

    fun onPermissionResult(granted: Boolean, permanentlyDenied: Boolean = false) {
        _uiState.value = _uiState.value.copy(
            hasCameraPermission = granted,
            permissionPermanentlyDenied = !granted && permanentlyDenied,
        )
    }

    fun classify(imageUri: Uri, updateDetectionId: Long? = null, isFromCamera: Boolean = true, onResult: (DetectionResult) -> Unit) {
        Log.d("SapiSehat", "ViewModel: classify() called with uri=$imageUri, updateDetectionId=$updateDetectionId, isFromCamera=$isFromCamera")
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                error = null,
                qualityRejection = null,
                progressText = appContext.getString(R.string.camera_processing),
            )

            // 1. Run ClientPreprocessor (EXIF correction + resize) then decode for quality gate
            val preprocessedJpegBytes: ByteArray
            val preprocessedBitmap: Bitmap = try {
                preprocessedJpegBytes = clientPreprocessor.process(imageUri)
                BitmapFactory.decodeByteArray(preprocessedJpegBytes, 0, preprocessedJpegBytes.size)
                    ?: throw IllegalStateException("Failed to decode preprocessed image")
            } catch (e: Exception) {
                Log.e("SapiSehat", "ViewModel: Preprocessing failed for quality gate", e)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    progressText = null,
                    error = appContext.getString(R.string.quality_error_load),
                )
                return@launch
            }

            // 2. Extract pixels from preprocessed bitmap and evaluate quality gate
            val qualityResult = try {
                val width = preprocessedBitmap.width
                val height = preprocessedBitmap.height
                val pixels = IntArray(width * height)
                preprocessedBitmap.getPixels(pixels, 0, width, 0, 0, width, height)
                preprocessedBitmap.recycle()
                qualityGate.evaluate(pixels, width, height)
            } catch (e: Exception) {
                Log.e("SapiSehat", "ViewModel: Quality gate evaluation failed", e)
                preprocessedBitmap.recycle()
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    progressText = null,
                    error = appContext.getString(R.string.quality_error_check),
                )
                return@launch
            }

            // 3. Handle quality gate result
            when (qualityResult) {
                is QualityResult.Pass -> {
                    // Proceed with existing inference flow
                    runCatching { classifyImageUseCase.classifyPreprocessed(preprocessedJpegBytes, imageUri, updateDetectionId, isFromCamera) }
                        .onSuccess { response ->
                            when (response) {
                                is ClassifyResponse.ConsentRequired -> {
                                    Log.d("SapiSehat", "ViewModel: classify() consent required")
                                    _uiState.value = _uiState.value.copy(
                                        showConsentPanel = true,
                                        pendingImageUri = imageUri,
                                        isLoading = false,
                                        progressText = null,
                                    )
                                }
                                is ClassifyResponse.Success -> {
                                    val result = response.result
                                    Log.d("SapiSehat", "ViewModel: classify() success — label=${result.label}, confidence=${result.confidence}, mode=${result.inferenceMode}")
                                    _uiState.value = _uiState.value.copy(
                                        isLoading = false,
                                        progressText = null,
                                    )
                                    onResult(result)
                                }
                            }
                        }
                        .onFailure { throwable ->
                            Log.e("SapiSehat", "ViewModel: classify() failed", throwable)
                            _uiState.value = _uiState.value.copy(
                                isLoading = false,
                                progressText = null,
                                error = throwable.message
                                    ?: appContext.getString(R.string.camera_processing),
                            )
                        }
                }
                is QualityResult.Reject -> {
                    Log.d("SapiSehat", "ViewModel: Quality gate rejected image with reasons=${qualityResult.reasons}")
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        progressText = null,
                        qualityRejection = qualityResult.reasons,
                        rejectedImageIsFromCamera = isFromCamera,
                    )
                }
            }
        }
    }

    fun clearQualityRejection() {
        _uiState.value = _uiState.value.copy(qualityRejection = null)
    }

    fun setFlashMode(mode: FlashMode) {
        _uiState.value = _uiState.value.copy(flashMode = mode)
    }

    fun onConsentDecision(allowed: Boolean, onResult: (DetectionResult) -> Unit) {
        viewModelScope.launch {
            settingsDataStore.setUploadConsent(allowed)
            _uiState.value = _uiState.value.copy(showConsentPanel = false)
            // Re-trigger classification with the pending image
            _uiState.value.pendingImageUri?.let { uri ->
                classify(uri, updateDetectionId = _updateDetectionId.value, onResult = onResult)
            }
        }
    }

    fun cycleFlashMode() {
        val next = when (_uiState.value.flashMode) {
            FlashMode.AUTO -> FlashMode.ON
            FlashMode.ON -> FlashMode.OFF
            FlashMode.OFF -> FlashMode.AUTO
        }
        _uiState.value = _uiState.value.copy(flashMode = next)
    }

    fun toggleGrid() {
        _uiState.value = _uiState.value.copy(showGrid = !_uiState.value.showGrid)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun onCaptureError(message: String) {
        _uiState.value = _uiState.value.copy(error = message)
    }
}
