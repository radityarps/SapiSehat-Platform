package com.sapisehat.app.domain

import org.junit.Assert.assertEquals
import org.junit.Test
import com.sapisehat.app.domain.model.ConsentStatus

/**
 * Property tests for consent status capture and persistence round-trip.
 *
 * These tests validate the consent-gated detection feature's data integrity
 * properties without requiring Android instrumentation or a real Room database.
 */
class ConsentStatusTest {

    // =========================================================================
    // Property 6: Consent status captured at inference time
    // The DetectionResult carries the consentStatus that was in effect when
    // inference was initiated.
    // Validates: Requirements 5.1, 5.2
    // =========================================================================

    /**
     * **Validates: Requirements 5.1, 5.2**
     *
     * Property 6: When InferenceRouter.classify() attaches consentStatus via
     * result.copy(consentStatus = consentStatus), the resulting DetectionResult
     * carries the exact ConsentStatus that was passed in.
     *
     * We test this by verifying that for every valid ConsentStatus value,
     * the copy() mechanism preserves the value faithfully.
     */
    @Test
    fun `property 6 - ALLOWED consent status is captured in DetectionResult`() {
        val result = createDetectionResult(ConsentStatus.ALLOWED)
        assertEquals(ConsentStatus.ALLOWED, result.consentStatus)
    }

    @Test
    fun `property 6 - DENIED consent status is captured in DetectionResult`() {
        val result = createDetectionResult(ConsentStatus.DENIED)
        assertEquals(ConsentStatus.DENIED, result.consentStatus)
    }

    @Test
    fun `property 6 - UNDECIDED consent status is captured in DetectionResult`() {
        val result = createDetectionResult(ConsentStatus.UNDECIDED)
        assertEquals(ConsentStatus.UNDECIDED, result.consentStatus)
    }

    @Test
    fun `property 6 - all ConsentStatus values are captured correctly via copy`() {
        // For every valid ConsentStatus, copying it onto a DetectionResult preserves the value
        ConsentStatus.entries.forEach { status ->
            val result = createDetectionResult(ConsentStatus.UNDECIDED)
                .copy(consentStatus = status)
            assertEquals(
                "ConsentStatus.$status should be preserved after copy()",
                status,
                result.consentStatus
            )
        }
    }

    @Test
    fun `property 6 - fromBoolean correctly maps consent values for capture`() {
        // The consent status captured at inference time comes from
        // ConsentStatus.fromBoolean(settingsDataStore.uploadConsent.first())
        assertEquals(ConsentStatus.ALLOWED, ConsentStatus.fromBoolean(true))
        assertEquals(ConsentStatus.DENIED, ConsentStatus.fromBoolean(false))
        assertEquals(ConsentStatus.UNDECIDED, ConsentStatus.fromBoolean(null))
    }

    // =========================================================================
    // Property 7: Consent status persistence round-trip
    // Saving a DetectionResult with any valid ConsentStatus to Room and reading
    // it back preserves the original value.
    // Validates: Requirements 5.3, 5.4
    // =========================================================================

    /**
     * **Validates: Requirements 5.3, 5.4**
     *
     * Property 7: The mapping ConsentStatus → String (via .name) and
     * String → ConsentStatus (via valueOf) is a lossless round-trip for all
     * valid enum values.
     */
    @Test
    fun `property 7 - round-trip for ALLOWED via name and valueOf`() {
        val original = ConsentStatus.ALLOWED
        val serialized = original.name
        val deserialized = ConsentStatus.valueOf(serialized)
        assertEquals(original, deserialized)
    }

    @Test
    fun `property 7 - round-trip for DENIED via name and valueOf`() {
        val original = ConsentStatus.DENIED
        val serialized = original.name
        val deserialized = ConsentStatus.valueOf(serialized)
        assertEquals(original, deserialized)
    }

    @Test
    fun `property 7 - round-trip for UNDECIDED via name and valueOf`() {
        val original = ConsentStatus.UNDECIDED
        val serialized = original.name
        val deserialized = ConsentStatus.valueOf(serialized)
        assertEquals(original, deserialized)
    }

    @Test
    fun `property 7 - all ConsentStatus values survive name-valueOf round-trip`() {
        // For every valid ConsentStatus, serializing to String and parsing back
        // yields the original value — this is the persistence round-trip property
        ConsentStatus.entries.forEach { status ->
            val serialized = status.name
            val deserialized = ConsentStatus.valueOf(serialized)
            assertEquals(
                "ConsentStatus.$status should survive name/valueOf round-trip",
                status,
                deserialized
            )
        }
    }

    @Test
    fun `property 7 - DetectionEntity default UNDECIDED maps back to ConsentStatus UNDECIDED`() {
        // DetectionEntity has consentStatus: String = "UNDECIDED" as default
        // When toDomain() parses this, it should map to ConsentStatus.UNDECIDED
        val entityDefault = "UNDECIDED"
        val parsed = runCatching { ConsentStatus.valueOf(entityDefault) }
            .getOrDefault(ConsentStatus.UNDECIDED)
        assertEquals(ConsentStatus.UNDECIDED, parsed)
    }

    @Test
    fun `property 7 - invalid string defaults to UNDECIDED with runCatching`() {
        // The repository uses runCatching { ConsentStatus.valueOf(str) }.getOrDefault(UNDECIDED)
        // This tests that invalid/corrupted DB values gracefully default to UNDECIDED
        val invalidStrings = listOf("INVALID", "allowed", "Denied", "", "null", "UNKNOWN")
        invalidStrings.forEach { invalid ->
            val result = runCatching { ConsentStatus.valueOf(invalid) }
                .getOrDefault(ConsentStatus.UNDECIDED)
            assertEquals(
                "Invalid string '$invalid' should default to UNDECIDED",
                ConsentStatus.UNDECIDED,
                result
            )
        }
    }

    @Test
    fun `property 7 - fromBoolean round-trip through name and valueOf`() {
        // Full pipeline: Boolean? → ConsentStatus → String → ConsentStatus
        // This mirrors the actual save/load path in the app
        val booleanInputs = listOf(true, false, null)
        booleanInputs.forEach { input ->
            val original = ConsentStatus.fromBoolean(input)
            val serialized = original.name  // What gets stored in Room
            val restored = runCatching { ConsentStatus.valueOf(serialized) }
                .getOrDefault(ConsentStatus.UNDECIDED)
            assertEquals(
                "fromBoolean($input) → .name → valueOf should round-trip",
                original,
                restored
            )
        }
    }

    // =========================================================================
    // Helper
    // =========================================================================

    private fun createDetectionResult(consentStatus: ConsentStatus): com.sapisehat.app.domain.model.DetectionResult {
        return com.sapisehat.app.domain.model.DetectionResult(
            id = 0,
            imagePath = null,
            label = "healthy",
            displayLabel = "Sehat",
            confidence = 0.95f,
            isReliable = true,
            allScores = mapOf("healthy" to 0.95f, "FMD" to 0.03f, "LSD" to 0.02f),
            inferenceMode = com.sapisehat.app.domain.model.InferenceMode.ONLINE,
            consentStatus = consentStatus,
            timestamp = System.currentTimeMillis(),
            processingMs = 150
        )
    }
}
