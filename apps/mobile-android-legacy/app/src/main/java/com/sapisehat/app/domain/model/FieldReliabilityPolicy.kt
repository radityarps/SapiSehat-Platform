package com.sapisehat.app.domain.model

object FieldReliabilityPolicy {
    const val MIN_CONFIDENCE = 0.70f
    const val MIN_TOP_CLASS_MARGIN = 0.15f
    const val INSUFFICIENT_EVIDENCE_LABEL = "INSUFFICIENT_VISUAL_EVIDENCE"

    fun apply(result: DetectionResult): DetectionResult {
        if (result.outcome == EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE) return result

        val margin = topClassMargin(result.allScores)
        val hasEnoughEvidence = result.confidence >= MIN_CONFIDENCE && margin >= MIN_TOP_CLASS_MARGIN

        return if (hasEnoughEvidence) {
            result.copy(isReliable = result.isReliable && hasEnoughEvidence)
        } else {
            result.copy(
                label = INSUFFICIENT_EVIDENCE_LABEL,
                displayLabel = "Insufficient visual evidence",
                isReliable = false,
                outcome = EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE,
            )
        }
    }

    fun topClassMargin(scores: Map<String, Float>): Float {
        val sorted = scores.values.sortedDescending()
        if (sorted.size < 2) return 1f
        return sorted[0] - sorted[1]
    }

    fun isFalseConfidentResult(expectedLabel: String, result: DetectionResult): Boolean {
        if (result.outcome == EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE) return false
        return !result.label.equals(expectedLabel, ignoreCase = true) &&
            result.confidence >= MIN_CONFIDENCE &&
            topClassMargin(result.allScores) >= MIN_TOP_CLASS_MARGIN
    }
}

