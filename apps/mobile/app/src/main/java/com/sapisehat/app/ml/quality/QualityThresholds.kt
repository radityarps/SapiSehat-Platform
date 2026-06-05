package com.sapisehat.app.ml.quality

/**
 * Configurable thresholds for the image quality gate.
 *
 * @param blurThreshold Minimum Laplacian variance for sharpness (default 100.0)
 * @param brightnessThreshold Minimum mean luminance 0–255 (default 40.0)
 * @param minWidth Minimum image width in pixels (default 224)
 * @param minHeight Minimum image height in pixels (default 224)
 */
data class QualityThresholds(
    val blurThreshold: Double = 100.0,
    val brightnessThreshold: Double = 40.0,
    val minWidth: Int = 224,
    val minHeight: Int = 224,
)
