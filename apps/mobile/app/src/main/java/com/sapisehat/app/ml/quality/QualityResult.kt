package com.sapisehat.app.ml.quality

/**
 * Result of the image quality gate evaluation.
 */
sealed class QualityResult {
    data object Pass : QualityResult()
    data class Reject(val reasons: Set<RejectionReason>) : QualityResult()
}
