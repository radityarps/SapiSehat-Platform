package com.sapisehat.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ErrorResponseDto(
    val status: String,
    @Json(name = "error_code")
    val errorCode: String,
    val message: String,
)
