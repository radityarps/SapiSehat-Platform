package com.sapisehat.app.ml

import android.net.Uri

/**
 * Interface for image preprocessing to enable unit testing without
 * Android framework dependencies.
 */
interface ImagePreprocessor {
    fun process(imageUri: Uri): ByteArray
}
