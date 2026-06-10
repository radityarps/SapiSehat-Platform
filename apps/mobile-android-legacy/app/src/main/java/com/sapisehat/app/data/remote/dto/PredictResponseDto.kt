package com.sapisehat.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PredictResponseDto(
    val status: String,
    val prediction: PredictionDto,
    @Json(name = "model_info")
    val modelInfo: ModelInfoDto,
    @Json(name = "processing_time_ms")
    val processingTimeMs: Int,
    @Json(name = "preprocessing_time_ms")
    val preprocessingTimeMs: Int,
    @Json(name = "inference_time_ms")
    val inferenceTimeMs: Int,
)

@JsonClass(generateAdapter = true)
data class PredictionDto(
    @Json(name = "disease_class")
    val diseaseClass: String,
    @Json(name = "display_label_key")
    val displayLabelKey: String,
    val confidence: Float,
    @Json(name = "is_reliable")
    val isReliable: Boolean,
    val scores: Map<String, Float>,
)

@JsonClass(generateAdapter = true)
data class ModelInfoDto(
    val version: String,
)
