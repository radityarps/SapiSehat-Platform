package com.sapisehat.app.ml

import android.util.Log
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import com.sapisehat.app.data.remote.api.InferenceApiService
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.InferenceMode

@Singleton
open class OnlineInferenceClient @Inject constructor(
    private val apiService: InferenceApiService
) : ImageClassifier {
    open override suspend fun classify(jpegBytes: ByteArray): DetectionResult = withContext(Dispatchers.IO) {
        Log.d("SapiSehat", "OnlineInferenceClient: sending predict request (${jpegBytes.size} bytes)")
        val body = jpegBytes.toRequestBody("image/jpeg".toMediaType())
        val part = MultipartBody.Part.createFormData("image", "photo.jpg", body)
        val response = apiService.predict(part)
        Log.d("SapiSehat", "OnlineInferenceClient: response received — status=${response.status}, prediction=${response.prediction.diseaseClass}")
        val prediction = response.prediction

        DetectionResult(
            label = prediction.diseaseClass,
            displayLabel = prediction.displayLabelKey,
            confidence = prediction.confidence,
            isReliable = prediction.isReliable,
            allScores = prediction.scores,
            inferenceMode = InferenceMode.ONLINE,
            processingMs = response.processingTimeMs,
            modelVersion = response.modelInfo.version,
        )
    }
}
