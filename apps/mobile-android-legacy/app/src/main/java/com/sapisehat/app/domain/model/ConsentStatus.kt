package com.sapisehat.app.domain.model

enum class ConsentStatus {
    UNDECIDED,
    ALLOWED,
    DENIED;

    companion object {
        fun fromBoolean(value: Boolean?): ConsentStatus = when (value) {
            true -> ALLOWED
            false -> DENIED
            null -> UNDECIDED
        }
    }
}
