package com.sapisehat.app.domain.model

enum class ImageSource {
    CAMERA,
    GALLERY;

    companion object {
        fun fromBoolean(isFromCamera: Boolean): ImageSource =
            if (isFromCamera) CAMERA else GALLERY
    }
}
