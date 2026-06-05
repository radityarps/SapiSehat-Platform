package com.sapisehat.app.ml

import android.net.Uri
import android.util.Log
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import com.sapisehat.app.domain.model.ClassifyResponse
import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.FieldReliabilityPolicy
import com.sapisehat.app.domain.model.InferenceMode

import com.sapisehat.app.di.OfflineClassifier
import com.sapisehat.app.di.OnlineClassifier

@Singleton
class InferenceRouter @Inject constructor(
    private val clientPreprocessor: ImagePreprocessor,
    @OnlineClassifier private val onlineClient: ImageClassifier,
    @OfflineClassifier private val offlineEngine: ImageClassifier,
    private val networkChecker: NetworkChecker
) {
    /**
     * Consent-aware classification that gates online inference behind user consent.
     *
     * Routing logic:
     * - Online + UNDECIDED → ConsentRequired (no preprocessing)
     * - Online + ALLOWED  → online with offline fallback on failure
     * - Offline OR DENIED → offline engine
     */
    suspend fun classify(imageUri: Uri, consentStatus: ConsentStatus): ClassifyResponse {
        Log.d("SapiSehat", "InferenceRouter: classify() started, uri=$imageUri, consent=$consentStatus")

        val online = networkChecker.isOnline()
        Log.d("SapiSehat", "InferenceRouter: isOnline=$online")

        // When online and consent is undecided, signal that consent is required
        // without performing any preprocessing or network upload.
        if (online && consentStatus == ConsentStatus.UNDECIDED) {
            Log.d("SapiSehat", "InferenceRouter: consent undecided while online, returning ConsentRequired")
            return ClassifyResponse.ConsentRequired
        }

        val jpegBytes = withContext(Dispatchers.IO) {
            clientPreprocessor.process(imageUri)
        }
        Log.d("SapiSehat", "InferenceRouter: preprocessed image — ${jpegBytes.size} bytes")

        return classifyPreprocessed(jpegBytes, consentStatus, online)
    }

    /**
     * Classifies already-preprocessed JPEG bytes.
     * Use this when upstream code must inspect the exact inference input first
     * (for example, the image quality gate).
     */
    suspend fun classifyPreprocessed(
        jpegBytes: ByteArray,
        consentStatus: ConsentStatus
    ): ClassifyResponse {
        val online = networkChecker.isOnline()
        Log.d("SapiSehat", "InferenceRouter: classifyPreprocessed() started, consent=$consentStatus, isOnline=$online")

        if (online && consentStatus == ConsentStatus.UNDECIDED) {
            Log.d("SapiSehat", "InferenceRouter: consent undecided while online, returning ConsentRequired")
            return ClassifyResponse.ConsentRequired
        }

        return classifyPreprocessed(jpegBytes, consentStatus, online)
    }

    private suspend fun classifyPreprocessed(
        jpegBytes: ByteArray,
        consentStatus: ConsentStatus,
        online: Boolean
    ): ClassifyResponse {
        val result = if (online && consentStatus == ConsentStatus.ALLOWED) {
            Log.d("SapiSehat", "InferenceRouter: routing to ONLINE (consent ALLOWED)")
            try {
                onlineClient.classify(jpegBytes)
            } catch (e: Exception) {
                Log.e("SapiSehat", "InferenceRouter: online failed, falling back to offline", e)
                offlineEngine.classify(jpegBytes)
                    .copy(inferenceMode = InferenceMode.OFFLINE_FALLBACK)
            }
        } else {
            // !isOnline() OR consentStatus == DENIED
            Log.d("SapiSehat", "InferenceRouter: routing to OFFLINE (online=$online, consent=$consentStatus)")
            offlineEngine.classify(jpegBytes)
        }

        return ClassifyResponse.Success(
            FieldReliabilityPolicy.apply(result.copy(consentStatus = consentStatus))
        )
    }

    /**
     * Legacy classify method for backward compatibility during migration.
     * Assumes consent is ALLOWED (old callers did not have consent gating).
     */
    suspend fun classify(imageUri: Uri): DetectionResult {
        Log.d("SapiSehat", "InferenceRouter: classify() started, uri=$imageUri")
        val jpegBytes = withContext(Dispatchers.IO) {
            clientPreprocessor.process(imageUri)
        }
        Log.d("SapiSehat", "InferenceRouter: preprocessed image — ${jpegBytes.size} bytes")

        val online = networkChecker.isOnline()
        Log.d("SapiSehat", "InferenceRouter: isOnline=$online, routing to ${if (online) "ONLINE" else "OFFLINE"}")

        return if (online) {
            try {
                FieldReliabilityPolicy.apply(onlineClient.classify(jpegBytes))
            } catch (e: Exception) {
                Log.e("SapiSehat", "InferenceRouter: online failed, falling back to offline", e)
                FieldReliabilityPolicy.apply(
                    offlineEngine.classify(jpegBytes).copy(inferenceMode = InferenceMode.OFFLINE_FALLBACK)
                )
            }
        } else {
            FieldReliabilityPolicy.apply(offlineEngine.classify(jpegBytes))
        }
    }
}
