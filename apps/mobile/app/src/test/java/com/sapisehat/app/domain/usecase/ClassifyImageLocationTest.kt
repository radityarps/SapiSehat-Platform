package com.sapisehat.app.domain.usecase

import com.sapisehat.app.domain.model.CoarseLocation
import com.sapisehat.app.domain.model.LocationSource
import com.sapisehat.app.location.LocationResolver
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Tests the actual LocationResolver.resolve() production code.
 * Covers all acceptance criteria: no-location, manual, GPS-disabled, GPS-enabled.
 */
class ClassifyImageLocationTest {

    // ── No-location cases ─────────────────────────────────────────────

    @Test
    fun `GPS disabled and no manual produces no location`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = null,
            manualLatitude = null,
            manualLongitude = null,
        )
        assertNull(result.latitude)
        assertNull(result.longitude)
        assertNull(result.source)
    }

    @Test
    fun `GPS enabled but no GPS fix and no manual produces no location`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = true,
            gpsLocation = null,
            manualLatitude = null,
            manualLongitude = null,
        )
        assertNull(result.latitude)
        assertNull(result.longitude)
        assertNull(result.source)
    }

    // ── GPS-enabled cases ─────────────────────────────────────────────

    @Test
    fun `GPS enabled with fix returns GPS coordinates`() {
        val gps = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        val result = LocationResolver.resolve(
            gpsAssistEnabled = true,
            gpsLocation = gps,
            manualLatitude = null,
            manualLongitude = null,
        )
        assertEquals(-6.20, result.latitude!!, 0.001)
        assertEquals(106.85, result.longitude!!, 0.001)
        assertEquals(LocationSource.GPS, result.source)
    }

    @Test
    fun `GPS takes priority over manual when both available`() {
        val gps = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        val result = LocationResolver.resolve(
            gpsAssistEnabled = true,
            gpsLocation = gps,
            manualLatitude = -7.80,
            manualLongitude = 110.36,
        )
        assertEquals(-6.20, result.latitude!!, 0.001)
        assertEquals(106.85, result.longitude!!, 0.001)
        assertEquals(LocationSource.GPS, result.source)
    }

    // ── Manual location cases ─────────────────────────────────────────

    @Test
    fun `manual location used when GPS disabled`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = null,
            manualLatitude = -7.80,
            manualLongitude = 110.36,
        )
        assertEquals(-7.80, result.latitude!!, 0.001)
        assertEquals(110.36, result.longitude!!, 0.001)
        assertEquals(LocationSource.MANUAL, result.source)
    }

    @Test
    fun `manual location used when GPS enabled but no fix`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = true,
            gpsLocation = null,
            manualLatitude = -7.80,
            manualLongitude = 110.36,
        )
        assertEquals(-7.80, result.latitude!!, 0.001)
        assertEquals(110.36, result.longitude!!, 0.001)
        assertEquals(LocationSource.MANUAL, result.source)
    }

    @Test
    fun `partial manual latitude only produces no location`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = null,
            manualLatitude = -7.80,
            manualLongitude = null,
        )
        assertNull(result.latitude)
        assertNull(result.longitude)
        assertNull(result.source)
    }

    @Test
    fun `partial manual longitude only produces no location`() {
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = null,
            manualLatitude = null,
            manualLongitude = 110.36,
        )
        assertNull(result.latitude)
        assertNull(result.longitude)
        assertNull(result.source)
    }

    // ── GPS disabled does not use GPS even if somehow provided ─────────

    @Test
    fun `GPS disabled ignores GPS location`() {
        val gps = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = gps,
            manualLatitude = null,
            manualLongitude = null,
        )
        // GPS disabled means we don't use GPS, but manual is also null → no location
        assertNull(result.latitude)
        assertNull(result.longitude)
        assertNull(result.source)
    }

    @Test
    fun `GPS disabled with manual falls back to manual even if GPS provided`() {
        val gps = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        val result = LocationResolver.resolve(
            gpsAssistEnabled = false,
            gpsLocation = gps,
            manualLatitude = -7.80,
            manualLongitude = 110.36,
        )
        assertEquals(-7.80, result.latitude!!, 0.001)
        assertEquals(110.36, result.longitude!!, 0.001)
        assertEquals(LocationSource.MANUAL, result.source)
    }
}
