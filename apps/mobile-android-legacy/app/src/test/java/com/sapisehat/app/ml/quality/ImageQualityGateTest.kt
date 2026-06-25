package com.sapisehat.app.ml.quality

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

/**
 * Unit tests for ImageQualityGate covering accept/reject/composite/preconditions.
 *
 * Validates: Requirements 2.2, 2.3, 3.2, 3.3, 4.3, 4.4, 5.1, 5.2, 8.3, 8.4, 8.5
 */
class ImageQualityGateTest {

    private val gate = ImageQualityGate()

    // --- Helper functions ---

    /** Creates a uniform-color pixel array (low blur score). */
    private fun uniformPixels(width: Int, height: Int, color: Int = 0xFF808080.toInt()): IntArray {
        return IntArray(width * height) { color }
    }

    /** Creates a sharp image with high-frequency edges (high blur score). */
    private fun sharpPixels(width: Int, height: Int): IntArray {
        return IntArray(width * height) { i ->
            val x = i % width
            val y = i / width
            // Checkerboard pattern creates high Laplacian variance
            if ((x + y) % 2 == 0) 0xFFFFFFFF.toInt() else 0xFF000000.toInt()
        }
    }

    /** Creates a bright image (high brightness score). */
    private fun brightPixels(width: Int, height: Int): IntArray {
        return IntArray(width * height) { 0xFFCCCCCC.toInt() } // ~204 luminance
    }

    /** Creates a dark image (low brightness score). */
    private fun darkPixels(width: Int, height: Int): IntArray {
        return IntArray(width * height) { 0xFF101010.toInt() } // ~16 luminance
    }

    /** Creates a valid image that passes all checks: sharp, bright, large enough. */
    private fun validImage(width: Int = 300, height: Int = 300): IntArray {
        return sharpPixels(width, height)
    }

    // --- Default thresholds ---

    @Test
    fun `default thresholds are correctly set`() {
        val thresholds = QualityThresholds()
        assertEquals(100.0, thresholds.blurThreshold, 0.001)
        assertEquals(40.0, thresholds.brightnessThreshold, 0.001)
        assertEquals(224, thresholds.minWidth)
        assertEquals(224, thresholds.minHeight)
    }

    // --- Pass cases ---

    @Test
    fun `sharp bright large image passes all checks`() {
        val pixels = validImage(300, 300)
        val result = gate.evaluate(pixels, 300, 300)
        assertEquals(QualityResult.Pass, result)
    }

    @Test
    fun `image exactly at minimum resolution passes`() {
        val pixels = sharpPixels(224, 224)
        val result = gate.evaluate(pixels, 224, 224)
        assertEquals(QualityResult.Pass, result)
    }

    // --- Reject: TOO_BLURRY ---

    @Test
    fun `uniform pixel image fails blur check`() {
        // Uniform pixels have zero Laplacian variance
        val pixels = uniformPixels(300, 300)
        val result = gate.evaluate(pixels, 300, 300)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_BLURRY",
            RejectionReason.TOO_BLURRY in (result as QualityResult.Reject).reasons
        )
    }

    // --- Reject: TOO_DARK ---

    @Test
    fun `all-black image fails brightness check`() {
        val pixels = IntArray(300 * 300) { 0xFF000000.toInt() }
        val result = gate.evaluate(pixels, 300, 300)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_DARK",
            RejectionReason.TOO_DARK in (result as QualityResult.Reject).reasons
        )
    }

    @Test
    fun `dark image below threshold fails brightness check`() {
        val pixels = darkPixels(300, 300)
        val result = gate.evaluate(pixels, 300, 300)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_DARK",
            RejectionReason.TOO_DARK in (result as QualityResult.Reject).reasons
        )
    }

    // --- Reject: TOO_SMALL ---

    @Test
    fun `100x100 image fails resolution check`() {
        val pixels = sharpPixels(100, 100)
        val result = gate.evaluate(pixels, 100, 100)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_SMALL",
            RejectionReason.TOO_SMALL in (result as QualityResult.Reject).reasons
        )
    }

    @Test
    fun `image with width below minimum fails`() {
        val pixels = sharpPixels(200, 300)
        val result = gate.evaluate(pixels, 200, 300)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_SMALL",
            RejectionReason.TOO_SMALL in (result as QualityResult.Reject).reasons
        )
    }

    @Test
    fun `image with height below minimum fails`() {
        val pixels = sharpPixels(300, 200)
        val result = gate.evaluate(pixels, 300, 200)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        assertTrue(
            "Expected TOO_SMALL",
            RejectionReason.TOO_SMALL in (result as QualityResult.Reject).reasons
        )
    }

    // --- Composite rejection ---

    @Test
    fun `dark blurry small image returns all three reasons`() {
        // Dark + uniform (blurry) + small
        val pixels = IntArray(100 * 100) { 0xFF050505.toInt() }
        val result = gate.evaluate(pixels, 100, 100)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        val reasons = (result as QualityResult.Reject).reasons
        assertTrue("Expected TOO_BLURRY", RejectionReason.TOO_BLURRY in reasons)
        assertTrue("Expected TOO_DARK", RejectionReason.TOO_DARK in reasons)
        assertTrue("Expected TOO_SMALL", RejectionReason.TOO_SMALL in reasons)
    }

    @Test
    fun `dark and blurry but large enough returns two reasons`() {
        val pixels = IntArray(300 * 300) { 0xFF050505.toInt() }
        val result = gate.evaluate(pixels, 300, 300)
        assertTrue("Expected Reject", result is QualityResult.Reject)
        val reasons = (result as QualityResult.Reject).reasons
        assertTrue("Expected TOO_BLURRY", RejectionReason.TOO_BLURRY in reasons)
        assertTrue("Expected TOO_DARK", RejectionReason.TOO_DARK in reasons)
        assertEquals("Expected exactly 2 reasons", 2, reasons.size)
    }

    // --- Preconditions ---

    @Test(expected = IllegalArgumentException::class)
    fun `mismatched pixel array size throws`() {
        val pixels = IntArray(100) // Wrong size for 10x20
        gate.evaluate(pixels, 10, 20)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `zero width throws`() {
        gate.evaluate(IntArray(0), 0, 10)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `zero height throws`() {
        gate.evaluate(IntArray(0), 10, 0)
    }

    // --- Blur score properties ---

    @Test
    fun `blur score is non-negative for random images`() {
        val random = Random(42)
        repeat(50) {
            val w = random.nextInt(10, 100)
            val h = random.nextInt(10, 100)
            val pixels = IntArray(w * h) { random.nextInt() or 0xFF000000.toInt() }
            val score = gate.computeBlurScore(pixels, w, h)
            assertTrue("Blur score should be non-negative, got $score", score >= 0.0)
            assertTrue("Blur score should be finite", score.isFinite())
        }
    }

    // --- Brightness score properties ---

    @Test
    fun `brightness score is bounded 0 to 255 for random images`() {
        val random = Random(42)
        repeat(50) {
            val size = random.nextInt(10, 500)
            val pixels = IntArray(size) { random.nextInt() or 0xFF000000.toInt() }
            val score = gate.computeBrightnessScore(pixels)
            assertTrue("Brightness should be >= 0, got $score", score >= 0.0)
            assertTrue("Brightness should be <= 255, got $score", score <= 255.0)
        }
    }

    @Test
    fun `brightness of all-white image is approximately 255`() {
        val pixels = IntArray(100) { 0xFFFFFFFF.toInt() }
        val score = gate.computeBrightnessScore(pixels)
        assertTrue("Expected ~255, got $score", score > 254.0)
    }

    @Test
    fun `brightness of all-black image is 0`() {
        val pixels = IntArray(100) { 0xFF000000.toInt() }
        val score = gate.computeBrightnessScore(pixels)
        assertEquals(0.0, score, 0.001)
    }

    // --- Custom thresholds ---

    @Test
    fun `custom thresholds are respected`() {
        val lenientGate = ImageQualityGate(
            QualityThresholds(blurThreshold = 0.0, brightnessThreshold = 0.0, minWidth = 1, minHeight = 1)
        )
        // Even a 1x1 dark pixel should pass with lenient thresholds
        val result = lenientGate.evaluate(intArrayOf(0xFF000000.toInt()), 1, 1)
        assertEquals(QualityResult.Pass, result)
    }

    // --- Property: valid inputs always pass ---

    @Test
    fun `property - images meeting all thresholds always pass`() {
        val random = Random(123)
        repeat(50) {
            val w = random.nextInt(224, 500)
            val h = random.nextInt(224, 500)
            // Checkerboard ensures high blur score, bright colors ensure brightness
            val pixels = IntArray(w * h) { i ->
                val x = i % w
                val y = i / w
                if ((x + y) % 2 == 0) 0xFFFFFFFF.toInt() else 0xFF808080.toInt()
            }
            val result = gate.evaluate(pixels, w, h)
            assertEquals("Expected Pass for ${w}x${h} sharp bright image", QualityResult.Pass, result)
        }
    }
}
