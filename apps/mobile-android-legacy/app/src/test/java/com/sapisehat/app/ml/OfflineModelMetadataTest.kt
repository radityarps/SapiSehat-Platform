package com.sapisehat.app.ml

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineModelMetadataTest {
    @Test
    fun `offline model version matches selected dynamic range artifact`() {
        assertEquals(
            "cattle-disease-mobilenetv2-v20260601-s42-dynamic-range",
            OfflineInferenceEngine.MODEL_VERSION
        )
    }

    @Test
    fun `offline model version preserves base model traceability`() {
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("mobilenetv2"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("v20260601"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("s42"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("dynamic-range"))
    }
}
