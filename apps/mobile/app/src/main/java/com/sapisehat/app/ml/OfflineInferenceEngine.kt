package com.sapisehat.app.ml

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import com.sapisehat.app.BuildConfig
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.InferenceMode
import com.sapisehat.app.ml.preprocessing.ModelPreprocessor
import java.nio.ByteBuffer
import java.nio.ByteOrder

@Singleton
open class OfflineInferenceEngine @Inject constructor(
    @ApplicationContext private val context: Context,
    private val modelPreprocessor: ModelPreprocessor
) : ImageClassifier {
    companion object {
        private const val MODEL_FILE = "cattle_disease.tflite"
        /** Offline model version identifier. Updated when the .tflite asset is replaced. */
        const val MODEL_VERSION = "cattle-disease-mobilenetv2-v20260601-s42-dynamic-range"
        // Canonical labels matching backend class_names.json: {"0": "FMD", "1": "LSD", "2": "healthy"}
        private val LABELS = listOf("FMD", "LSD", "healthy")
        private val LABEL_DISPLAY = mapOf(
            "FMD" to "Penyakit Mulut dan Kuku (FMD)",
            "LSD" to "Penyakit Lumpy Skin (LSD)",
            "healthy" to "Sapi Sehat"
        )
    }

    private val interpreter: Interpreter by lazy {
        val bytes = context.assets.open(MODEL_FILE).use { it.readBytes() }
        val modelBuffer = ByteBuffer.allocateDirect(bytes.size).apply {
            order(ByteOrder.nativeOrder())
            put(bytes)
        }
        modelBuffer.rewind()
        Interpreter(modelBuffer, Interpreter.Options().apply { numThreads = 4 })
    }

    open override suspend fun classify(jpegBytes: ByteArray): DetectionResult = withContext(Dispatchers.Default) {
        val inputBuffer = modelPreprocessor.process(jpegBytes)
        val output = Array(1) { FloatArray(3) }
        interpreter.run(inputBuffer, output)

        val scores = output[0]
        val maxIdx = scores.indices.maxByOrNull { scores[it] } ?: 0
        val label = LABELS[maxIdx]

        DetectionResult(
            label = label,
            displayLabel = LABEL_DISPLAY[label] ?: label,
            confidence = scores[maxIdx],
            isReliable = scores[maxIdx] >= BuildConfig.CONFIDENCE_THRESHOLD,
            allScores = mapOf(
                "FMD" to scores[0],
                "LSD" to scores[1],
                "healthy" to scores[2]
            ),
            inferenceMode = InferenceMode.OFFLINE,
            modelVersion = MODEL_VERSION,
        )
    }
}
