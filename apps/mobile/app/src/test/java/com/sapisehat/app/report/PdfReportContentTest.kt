package com.sapisehat.app.report

import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.EarlyDetectionOutcome
import com.sapisehat.app.domain.model.ImageSource
import com.sapisehat.app.domain.model.InferenceMode
import com.sapisehat.app.domain.model.LocationSource
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Tests verifying PDF report content requirements via [ReportContentBuilder]:
 * - Required fields are present
 * - Excluded fields (IMEI, serial, account ID, precise location) are absent
 * - Wording avoids diagnosis/certificate claims
 */
class PdfReportContentTest {

    private fun createResult() = DetectionResult(
        id = 1L,
        imagePath = "/images/test.jpg",
        label = "FMD",
        displayLabel = "Penyakit Mulut dan Kuku (FMD)",
        confidence = 0.92f,
        isReliable = true,
        allScores = mapOf("FMD" to 0.92f, "LSD" to 0.05f, "healthy" to 0.03f),
        inferenceMode = InferenceMode.ONLINE,
        consentStatus = ConsentStatus.ALLOWED,
        timestamp = 1700000000000L,
        appVersion = "1.0.0",
        modelVersion = "MobileNetV2-v3",
        preprocessingSummary = "EXIF correct, resize max 800px, JPEG 85%, then 224×224 /255 normalize",
        imageSource = ImageSource.CAMERA,
        latitude = -6.20,
        longitude = 106.85,
        locationSource = LocationSource.GPS,
    )

    private fun buildContent(result: DetectionResult = createResult()): String {
        val report = ReportContentBuilder.build(result, "1.0.0")
        return buildString {
            appendLine(report.title)
            appendLine(report.subtitle)
            report.resultLines.forEach { appendLine(it) }
            report.scoreLines.forEach { appendLine(it) }
            report.metadataLines.forEach { appendLine(it) }
            report.disclaimerLines.forEach { appendLine(it) }
        }
    }

    // ── Required fields present ───────────────────────────────────────

    @Test
    fun `report includes disease class`() {
        val content = buildContent()
        assertTrue(content.contains("Penyakit Mulut dan Kuku (FMD)"))
    }

    @Test
    fun `report includes confidence`() {
        val content = buildContent()
        assertTrue(content.contains("92%"))
    }

    @Test
    fun `report includes inference mode`() {
        val content = buildContent()
        assertTrue(content.contains("ONLINE"))
    }

    @Test
    fun `report includes class scores`() {
        val content = buildContent()
        assertTrue(content.contains("FMD: 92%"))
        assertTrue(content.contains("LSD: 5%"))
        assertTrue(content.contains("healthy: 3%"))
    }

    @Test
    fun `report includes app version`() {
        val content = buildContent()
        assertTrue(content.contains("App Version: 1.0.0"))
    }

    @Test
    fun `report includes model version`() {
        val content = buildContent()
        assertTrue(content.contains("Model Version: MobileNetV2-v3"))
    }

    @Test
    fun `report includes preprocessing summary`() {
        val content = buildContent()
        assertTrue(content.contains("Preprocessing:"))
    }

    @Test
    fun `report includes consent status`() {
        val content = buildContent()
        assertTrue(content.contains("Consent Status: ALLOWED"))
    }

    @Test
    fun `report includes coarse location with source`() {
        val content = buildContent()
        assertTrue(content.contains("Coarse Location: -6.20, 106.85 (GPS)"))
    }

    @Test
    fun `report includes disclaimer`() {
        val content = buildContent()
        assertTrue(content.contains("NOT a veterinary diagnosis"))
        assertTrue(content.contains("certificate"))
    }

    @Test
    fun `report describes insufficient visual evidence without negative diagnosis`() {
        val content = buildContent(
            createResult().copy(
                label = "INSUFFICIENT_VISUAL_EVIDENCE",
                displayLabel = "Insufficient visual evidence",
                confidence = 0.64f,
                isReliable = false,
                outcome = EarlyDetectionOutcome.INSUFFICIENT_VISUAL_EVIDENCE,
            )
        )

        assertTrue(content.contains("Insufficient visual evidence"))
        assertTrue(content.contains("Retake the photo"))
        assertFalse(content.contains("No disease"))
        assertFalse(content.contains("not infected"))
    }

    // ── Excluded fields ───────────────────────────────────────────────

    @Test
    fun `report does not contain IMEI`() {
        val content = buildContent()
        assertFalse(content.contains("IMEI"))
    }

    @Test
    fun `report does not contain serial number`() {
        val content = buildContent()
        assertFalse(content.contains("serial"))
    }

    @Test
    fun `report does not contain account ID`() {
        val content = buildContent()
        assertFalse(content.contains("account"))
    }

    // ── Wording ───────────────────────────────────────────────────────

    @Test
    fun `report uses Early Detection not Diagnosis in title`() {
        val content = buildContent()
        assertTrue(content.contains("Early Detection Report"))
        assertFalse(content.startsWith("Diagnosis Report"))
    }

    @Test
    fun `report uses Early Indication not Diagnosis for result`() {
        val content = buildContent()
        assertTrue(content.contains("Early Indication:"))
    }

    @Test
    fun `report states it is not a certificate`() {
        val content = buildContent()
        assertTrue(content.contains("NOT a veterinary diagnosis, certificate, or official document"))
    }

    // ── ReportContent structure ───────────────────────────────────────

    @Test
    fun `build returns correct title`() {
        val report = ReportContentBuilder.build(createResult(), "1.0.0")
        assertEquals("SapiSehat — Early Detection Report", report.title)
    }

    @Test
    fun `build returns scores sorted by value descending`() {
        val report = ReportContentBuilder.build(createResult(), "1.0.0")
        assertEquals(3, report.scoreLines.size)
        assertTrue(report.scoreLines[0].startsWith("FMD"))
        assertTrue(report.scoreLines[1].startsWith("LSD"))
        assertTrue(report.scoreLines[2].startsWith("healthy"))
    }

    @Test
    fun `build omits location when not available`() {
        val result = createResult().copy(latitude = null, longitude = null, locationSource = null)
        val report = ReportContentBuilder.build(result, "1.0.0")
        assertFalse(report.metadataLines.any { it.contains("Location") })
    }

    @Test
    fun `build includes generated by line in disclaimer`() {
        val report = ReportContentBuilder.build(createResult(), "2.5.0")
        assertTrue(report.disclaimerLines.any { it.contains("SapiSehat v2.5.0") })
    }
}
