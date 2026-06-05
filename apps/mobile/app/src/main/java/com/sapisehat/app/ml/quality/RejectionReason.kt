package com.sapisehat.app.ml.quality

/**
 * Reasons why an image failed the quality gate.
 */
enum class RejectionReason {
    TOO_BLURRY,
    TOO_DARK,
    TOO_SMALL,
    UNREADABLE
}
