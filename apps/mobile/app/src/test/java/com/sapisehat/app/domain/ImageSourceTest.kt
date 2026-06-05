package com.sapisehat.app.domain

import com.sapisehat.app.domain.model.ImageSource
import org.junit.Assert.assertEquals
import org.junit.Test

class ImageSourceTest {

    @Test
    fun `fromBoolean true returns CAMERA`() {
        assertEquals(ImageSource.CAMERA, ImageSource.fromBoolean(true))
    }

    @Test
    fun `fromBoolean false returns GALLERY`() {
        assertEquals(ImageSource.GALLERY, ImageSource.fromBoolean(false))
    }

    @Test
    fun `CAMERA name is CAMERA`() {
        assertEquals("CAMERA", ImageSource.CAMERA.name)
    }

    @Test
    fun `GALLERY name is GALLERY`() {
        assertEquals("GALLERY", ImageSource.GALLERY.name)
    }

    @Test
    fun `valueOf CAMERA returns CAMERA`() {
        assertEquals(ImageSource.CAMERA, ImageSource.valueOf("CAMERA"))
    }

    @Test
    fun `valueOf GALLERY returns GALLERY`() {
        assertEquals(ImageSource.GALLERY, ImageSource.valueOf("GALLERY"))
    }
}
