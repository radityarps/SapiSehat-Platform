package com.sapisehat.app.domain.model

sealed class ClassifyFailure(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class Network(message: String, cause: Throwable? = null) : ClassifyFailure(message, cause)
    class InvalidImage(message: String, cause: Throwable? = null) : ClassifyFailure(message, cause)
    class ServiceUnavailable(message: String, cause: Throwable? = null) : ClassifyFailure(message, cause)
    class Unknown(message: String, cause: Throwable? = null) : ClassifyFailure(message, cause)
}
