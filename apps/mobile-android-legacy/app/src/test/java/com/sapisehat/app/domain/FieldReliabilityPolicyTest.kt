package com.sapisehat.app.domain

import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.EarlyDetectionOutcome
import com.sapisehat.app.domain.model.FieldReliabilityPolicy
import com.sapisehat.app.domain.model.InferenceMode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FieldReliabilityPolicyTest {
    private fun result(
        label: String = "FMD",
        confidence: Float = 0.90f,
        scores: Map<String, Float> = mapOf("FMD" to 0.90f, "LSD" to 0.05f, "healthy" to 0.05f),
    ) = DetectionResult(
        label = label,
        displayLabel = label,
        confidence = confidence,
        isReliable = true,
        allScores = scores,
        inferenceMode = InferenceMode.OFFLINE,
    )

    @Test
    fun `confidence below 70 percent becomes insufficient visual evidence`() {
        val updated = FieldReliabilityPolicy.apply(
            result(confidence = 0.69f, scores = mapOf("FMD" to 0.69f, "LSD" to 0.16f, "healthy" to 0.15f))
        )

        assertEquals(EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE, updated.outcome)
        assertEquals(FieldReliabilityPolicy.INSUFFICIENT_EVIDENCE_LABEL, updated.label)
        assertFalse(updated.isReliable)
    }

    @Test
    fun `top class margin below 15 percentage points becomes insufficient visual evidence`() {
        val updated = FieldReliabilityPolicy.apply(
            result(confidence = 0.76f, scores = mapOf("FMD" to 0.76f, "LSD" to 0.62f, "healthy" to 0.02f))
        )

        assertEquals(EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE, updated.outcome)
        assertFalse(updated.isReliable)
    }

    @Test
    fun `enough confidence and margin keeps disease class result`() {
        val updated = FieldReliabilityPolicy.apply(
            result(confidence = 0.76f, scores = mapOf("FMD" to 0.76f, "LSD" to 0.60f, "healthy" to 0.01f))
        )

        assertEquals(EarlyDetectionOutcome.DISEASE_CLASS, updated.outcome)
        assertEquals("FMD", updated.label)
        assertTrue(updated.isReliable)
    }

    @Test
    fun `false confident result excludes insufficient visual evidence outcomes`() {
        val insufficient = FieldReliabilityPolicy.apply(
            result(label = "healthy", confidence = 0.60f, scores = mapOf("healthy" to 0.60f, "FMD" to 0.30f, "LSD" to 0.10f))
        )

        assertFalse(FieldReliabilityPolicy.isFalseConfidentResult("FMD", insufficient))
    }

    @Test
    fun `false confident result requires wrong label confidence and margin`() {
        val confidentWrong = result(
            label = "healthy",
            confidence = 0.82f,
            scores = mapOf("healthy" to 0.82f, "FMD" to 0.10f, "LSD" to 0.08f),
        )

        assertTrue(FieldReliabilityPolicy.isFalseConfidentResult("FMD", confidentWrong))
    }
}

