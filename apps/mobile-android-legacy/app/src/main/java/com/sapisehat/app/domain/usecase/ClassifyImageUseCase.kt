package com.sapisehat.app.domain.usecase

import android.net.Uri
import javax.inject.Inject
import kotlinx.coroutines.flow.first
import com.sapisehat.app.BuildConfig
import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.data.repository.DetectionRepository
import com.sapisehat.app.domain.model.ClassifyResponse
import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.ImageSource
import com.sapisehat.app.location.LocationProvider
import com.sapisehat.app.location.LocationResolver
import com.sapisehat.app.ml.InferenceRouter

class ClassifyImageUseCase @Inject constructor(
    private val inferenceRouter: InferenceRouter,
    private val detectionRepository: DetectionRepository,
    private val settingsDataStore: SettingsDataStore,
    private val locationProvider: LocationProvider,
) {
    suspend operator fun invoke(
        imageUri: Uri,
        updateDetectionId: Long? = null,
        isFromCamera: Boolean = true,
    ): ClassifyResponse {
        val consentValue = settingsDataStore.uploadConsent.first()
        val consentStatus = ConsentStatus.fromBoolean(consentValue)

        val response = inferenceRouter.classify(imageUri, consentStatus)
        return saveSuccessfulResponse(response, imageUri, updateDetectionId, isFromCamera)
    }

    suspend fun classifyPreprocessed(
        jpegBytes: ByteArray,
        sourceImageUri: Uri,
        updateDetectionId: Long? = null,
        isFromCamera: Boolean = true,
    ): ClassifyResponse {
        val consentValue = settingsDataStore.uploadConsent.first()
        val consentStatus = ConsentStatus.fromBoolean(consentValue)

        val response = inferenceRouter.classifyPreprocessed(jpegBytes, consentStatus)
        return saveSuccessfulResponse(response, sourceImageUri, updateDetectionId, isFromCamera)
    }

    private suspend fun saveSuccessfulResponse(
        response: ClassifyResponse,
        imageUri: Uri,
        updateDetectionId: Long?,
        isFromCamera: Boolean,
    ): ClassifyResponse {
        if (response is ClassifyResponse.Success) {
            // Resolve location: GPS assist (if enabled) → manual fallback → none
            val gpsAssistEnabled = settingsDataStore.locationEnabled.first()
            val gpsLocation = if (gpsAssistEnabled) locationProvider.getCoarseLocation() else null
            val manualLat = settingsDataStore.manualLatitude.first()?.toDoubleOrNull()
            val manualLng = settingsDataStore.manualLongitude.first()?.toDoubleOrNull()

            val location = LocationResolver.resolve(
                gpsAssistEnabled = gpsAssistEnabled,
                gpsLocation = gpsLocation,
                manualLatitude = manualLat,
                manualLongitude = manualLng,
            )

            val resultWithMetadata = response.result.copy(
                appVersion = BuildConfig.VERSION_NAME,
                imageSource = ImageSource.fromBoolean(isFromCamera),
                preprocessingSummary = PREPROCESSING_SUMMARY,
                latitude = location.latitude,
                longitude = location.longitude,
                locationSource = location.source,
            )
            val savedId = detectionRepository.saveDetection(
                resultWithMetadata, imageUri, updateDetectionId
            )
            return ClassifyResponse.Success(resultWithMetadata.copy(id = savedId))
        }

        return response
    }

    companion object {
        /** Stable description of the current preprocessing pipeline. */
        const val PREPROCESSING_SUMMARY = "EXIF correct, resize max 800px, JPEG 85%, then 224×224 /255 normalize"
    }
}
