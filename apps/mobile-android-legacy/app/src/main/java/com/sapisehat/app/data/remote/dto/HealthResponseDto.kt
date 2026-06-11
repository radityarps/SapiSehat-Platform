package com.sapisehat.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class HealthResponseDto(
    val status: String,
    @Json(name = "model_version")
    val modelVersion: String,
    @Json(name = "model_loaded")
    val modelLoaded: Boolean,
)
