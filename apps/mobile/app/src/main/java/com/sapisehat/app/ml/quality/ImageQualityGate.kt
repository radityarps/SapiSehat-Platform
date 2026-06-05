package com.sapisehat.app.ml.quality

/**
 * Pure-function image quality gate that evaluates blur, brightness, and resolution.
 *
 * No Android framework dependencies — operates on raw ARGB pixel arrays.
 * Testable in standard JVM unit tests without instrumentation.
 *
 * @param thresholds Configurable quality thresholds (defaults tuned for cattle photography)
 */
class ImageQualityGate(
    private val thresholds: QualityThresholds = QualityThresholds()
) {
    /**
     * Evaluates image quality against configured thresholds.
     *
     * All checks run regardless of individual results (composite rejection).
     *
     * @param pixels ARGB pixel array (size must equal width * height)
     * @param width  Image width in pixels
     * @param height Image height in pixels
     * @return QualityResult.Pass if all checks pass, or QualityResult.Reject with all failure reasons
     */
    fun evaluate(pixels: IntArray, width: Int, height: Int): QualityResult {
        require(pixels.size == width * height) {
            "Pixel array size (${pixels.size}) must equal width * height ($width * $height = ${width * height})"
        }
        require(width > 0 && height > 0) { "Dimensions must be positive (got ${width}x${height})" }

        val reasons = mutableSetOf<RejectionReason>()

        if (computeBlurScore(pixels, width, height) < thresholds.blurThreshold) {
            reasons.add(RejectionReason.TOO_BLURRY)
        }
        if (computeBrightnessScore(pixels) < thresholds.brightnessThreshold) {
            reasons.add(RejectionReason.TOO_DARK)
        }
        if (width < thresholds.minWidth || height < thresholds.minHeight) {
            reasons.add(RejectionReason.TOO_SMALL)
        }

        return if (reasons.isEmpty()) QualityResult.Pass
        else QualityResult.Reject(reasons)
    }

    /**
     * Computes blur score using Laplacian variance on grayscale.
     * Higher values = sharper image. Returns 0.0 for images smaller than 3x3.
     */
    internal fun computeBlurScore(pixels: IntArray, width: Int, height: Int): Double {
        if (width < 3 || height < 3) return 0.0

        // Convert to grayscale luminance (ITU-R BT.601)
        val gray = IntArray(pixels.size) { i ->
            val pixel = pixels[i]
            val r = (pixel shr 16) and 0xFF
            val g = (pixel shr 8) and 0xFF
            val b = pixel and 0xFF
            (0.299 * r + 0.587 * g + 0.114 * b).toInt()
        }

        // Apply 3x3 Laplacian kernel: [0,1,0; 1,-4,1; 0,1,0]
        // Compute variance of Laplacian response
        var sum = 0.0
        var sumSq = 0.0
        var count = 0

        for (y in 1 until height - 1) {
            for (x in 1 until width - 1) {
                val idx = y * width + x
                val laplacian = (
                    gray[idx - width] +
                    gray[idx - 1] +
                    gray[idx + 1] +
                    gray[idx + width] -
                    4 * gray[idx]
                )
                sum += laplacian
                sumSq += laplacian.toDouble() * laplacian
                count++
            }
        }

        if (count == 0) return 0.0
        val mean = sum / count
        return (sumSq / count) - (mean * mean) // variance
    }

    /**
     * Computes mean luminance (0–255) across all pixels.
     * Returns 0.0 for empty pixel arrays.
     */
    internal fun computeBrightnessScore(pixels: IntArray): Double {
        if (pixels.isEmpty()) return 0.0
        var sum = 0L
        for (pixel in pixels) {
            val r = (pixel shr 16) and 0xFF
            val g = (pixel shr 8) and 0xFF
            val b = pixel and 0xFF
            sum += (0.299 * r + 0.587 * g + 0.114 * b).toLong()
        }
        return sum.toDouble() / pixels.size
    }
}
