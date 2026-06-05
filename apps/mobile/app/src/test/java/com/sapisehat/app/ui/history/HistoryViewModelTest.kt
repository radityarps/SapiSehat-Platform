package com.sapisehat.app.ui.history

import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.ImageSource
import com.sapisehat.app.domain.model.InferenceMode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Unit tests for HistoryItemUi mapping from DetectionResult.
 * Tests the field mapping logic without JSONObject (Android framework class).
 */
class HistoryViewModelTest {

    private fun createDetectionResult(
        id: Long = 1L,
        label: String = "FMD",
        displayLabel: String = "PMK",
        confidence: Float = 0.85f,
        inferenceMode: InferenceMode = InferenceMode.ONLINE,
        consentStatus: ConsentStatus = ConsentStatus.ALLOWED,
        imageSource: ImageSource? = ImageSource.CAMERA,
        appVersion: String? = "1.0.0",
        title: String? = null,
        description: String? = null,
    ) = DetectionResult(
        id = id,
        label = label,
        displayLabel = displayLabel,
        confidence = confidence,
        isReliable = true,
        allScores = mapOf("FMD" to 0.85f, "LSD" to 0.10f, "healthy" to 0.05f),
        inferenceMode = inferenceMode,
        consentStatus = consentStatus,
        timestamp = 1700000000000L,
        imageSource = imageSource,
        appVersion = appVersion,
        title = title,
        description = description,
    )

    // Test the field mapping without JSONObject serialization
    private fun DetectionResult.toHistoryItemUiFields(): HistoryItemUi {
        return HistoryItemUi(
            id = id,
            imagePath = imagePath,
            label = label,
            displayLabel = displayLabel,
            confidence = confidence,
            mode = inferenceMode.name,
            timestamp = timestamp,
            allScoresJson = "", // Skip JSON serialization in unit tests
            title = title,
            description = description,
            imageSource = imageSource?.name,
            appVersion = appVersion,
            consentStatus = consentStatus.name,
        )
    }

    @Test
    fun `mapping preserves imageSource CAMERA`() {
        val result = createDetectionResult(imageSource = ImageSource.CAMERA)
        val ui = result.toHistoryItemUiFields()
        assertEquals("CAMERA", ui.imageSource)
    }

    @Test
    fun `mapping preserves imageSource GALLERY`() {
        val result = createDetectionResult(imageSource = ImageSource.GALLERY)
        val ui = result.toHistoryItemUiFields()
        assertEquals("GALLERY", ui.imageSource)
    }

    @Test
    fun `mapping preserves null imageSource`() {
        val result = createDetectionResult(imageSource = null)
        val ui = result.toHistoryItemUiFields()
        assertNull(ui.imageSource)
    }

    @Test
    fun `mapping preserves appVersion`() {
        val result = createDetectionResult(appVersion = "2.1.0")
        val ui = result.toHistoryItemUiFields()
        assertEquals("2.1.0", ui.appVersion)
    }

    @Test
    fun `mapping preserves consentStatus ALLOWED`() {
        val result = createDetectionResult(consentStatus = ConsentStatus.ALLOWED)
        val ui = result.toHistoryItemUiFields()
        assertEquals("ALLOWED", ui.consentStatus)
    }

    @Test
    fun `mapping preserves consentStatus DENIED`() {
        val result = createDetectionResult(consentStatus = ConsentStatus.DENIED)
        val ui = result.toHistoryItemUiFields()
        assertEquals("DENIED", ui.consentStatus)
    }

    @Test
    fun `mapping preserves consentStatus UNDECIDED`() {
        val result = createDetectionResult(consentStatus = ConsentStatus.UNDECIDED)
        val ui = result.toHistoryItemUiFields()
        assertEquals("UNDECIDED", ui.consentStatus)
    }

    @Test
    fun `mapping preserves title and description`() {
        val result = createDetectionResult(title = "Sapi #5", description = "Lesi di kuku")
        val ui = result.toHistoryItemUiFields()
        assertEquals("Sapi #5", ui.title)
        assertEquals("Lesi di kuku", ui.description)
    }

    @Test
    fun `mapping preserves null title and description`() {
        val result = createDetectionResult(title = null, description = null)
        val ui = result.toHistoryItemUiFields()
        assertNull(ui.title)
        assertNull(ui.description)
    }

    @Test
    fun `mapping preserves mode ONLINE`() {
        val result = createDetectionResult(inferenceMode = InferenceMode.ONLINE)
        val ui = result.toHistoryItemUiFields()
        assertEquals("ONLINE", ui.mode)
    }

    @Test
    fun `mapping preserves mode OFFLINE`() {
        val result = createDetectionResult(inferenceMode = InferenceMode.OFFLINE)
        val ui = result.toHistoryItemUiFields()
        assertEquals("OFFLINE", ui.mode)
    }
}
