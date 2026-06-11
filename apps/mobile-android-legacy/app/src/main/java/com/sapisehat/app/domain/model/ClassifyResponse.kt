package com.sapisehat.app.domain.model

sealed interface ClassifyResponse {
    data class Success(val result: DetectionResult) : ClassifyResponse
    data object ConsentRequired : ClassifyResponse
}
