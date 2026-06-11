package com.sapisehat.app.ml.preprocessing

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ModelPreprocessor @Inject constructor() {
    companion object {
        const val INPUT_SIZE = 224
    }

    fun process(jpegBytes: ByteArray): ByteBuffer {
        val bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)
            ?: throw IllegalArgumentException("Unable to decode image bytes")
        val resized = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)

        val input = ByteBuffer.allocateDirect(4 * INPUT_SIZE * INPUT_SIZE * 3)
        input.order(ByteOrder.nativeOrder())

        val pixels = IntArray(INPUT_SIZE * INPUT_SIZE)
        resized.getPixels(pixels, 0, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE)

        // Simple rescale to [0, 1] — matches backend model_preprocessor.py
        // which uses: array = np.array(image, dtype=np.float32) / 255.0
        for (pixel in pixels) {
            input.putFloat((pixel shr 16 and 0xFF) / 255f)
            input.putFloat((pixel shr 8 and 0xFF) / 255f)
            input.putFloat((pixel and 0xFF) / 255f)
        }

        input.rewind()
        return input
    }
}
