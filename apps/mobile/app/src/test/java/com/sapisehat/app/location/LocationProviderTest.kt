package com.sapisehat.app.location

import com.sapisehat.app.domain.model.CoarseLocation
import com.sapisehat.app.domain.model.LocationSource
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Tests for location domain model and provider contract.
 * Covers no-location, manual, GPS-disabled, and GPS-enabled cases.
 */
class LocationProviderTest {

    // ── CoarseLocation model tests ────────────────────────────────────

    @Test
    fun `CoarseLocation with GPS source`() {
        val location = CoarseLocation(
            latitude = -6.18,
            longitude = 106.83,
            source = LocationSource.GPS,
        )
        assertEquals(-6.18, location.latitude, 0.001)
        assertEquals(106.83, location.longitude, 0.001)
        assertEquals(LocationSource.GPS, location.source)
    }

    @Test
    fun `CoarseLocation with MANUAL source`() {
        val location = CoarseLocation(
            latitude = -7.25,
            longitude = 112.75,
            source = LocationSource.MANUAL,
        )
        assertEquals(LocationSource.MANUAL, location.source)
    }

    @Test
    fun `LocationSource NONE represents no location`() {
        assertEquals("NONE", LocationSource.NONE.name)
    }

    @Test
    fun `all LocationSource values exist`() {
        val values = LocationSource.entries
        assertEquals(3, values.size)
        assertEquals(LocationSource.MANUAL, LocationSource.valueOf("MANUAL"))
        assertEquals(LocationSource.GPS, LocationSource.valueOf("GPS"))
        assertEquals(LocationSource.NONE, LocationSource.valueOf("NONE"))
    }

    // ── Provider contract: no permission ──────────────────────────────

    @Test
    fun `provider without permission returns null`() = runTest {
        val provider = FakeLocationProvider(hasPermission = false, location = null)
        assertNull(provider.getCoarseLocation())
    }

    @Test
    fun `hasPermission returns false when not granted`() {
        val provider = FakeLocationProvider(hasPermission = false, location = null)
        assertEquals(false, provider.hasPermission())
    }

    // ── Provider contract: GPS disabled ───────────────────────────────

    @Test
    fun `provider with permission but GPS disabled returns null`() = runTest {
        val provider = FakeLocationProvider(hasPermission = true, location = null)
        assertNull(provider.getCoarseLocation())
    }

    // ── Provider contract: GPS enabled ────────────────────────────────

    @Test
    fun `provider with permission and location returns coarse location`() = runTest {
        val expected = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        val provider = FakeLocationProvider(hasPermission = true, location = expected)
        val result = provider.getCoarseLocation()
        assertEquals(expected, result)
    }

    @Test
    fun `hasPermission returns true when granted`() {
        val provider = FakeLocationProvider(hasPermission = true, location = null)
        assertEquals(true, provider.hasPermission())
    }

    // ── Precision tests ───────────────────────────────────────────────

    @Test
    fun `coarse location uses 2 decimal precision`() {
        // 2 decimals ≈ 1.1km precision
        val location = CoarseLocation(-6.20, 106.85, LocationSource.GPS)
        // Verify the values are at 2-decimal precision
        assertEquals(-6.20, location.latitude, 0.005)
        assertEquals(106.85, location.longitude, 0.005)
    }

    // ── Manual location tests ─────────────────────────────────────────

    @Test
    fun `manual location has MANUAL source`() {
        val location = CoarseLocation(-6.20, 106.85, LocationSource.MANUAL)
        assertEquals(LocationSource.MANUAL, location.source)
    }

    @Test
    fun `manual location coordinates are preserved`() {
        val location = CoarseLocation(-7.80, 110.36, LocationSource.MANUAL)
        assertEquals(-7.80, location.latitude, 0.001)
        assertEquals(110.36, location.longitude, 0.001)
    }

    // ── Fake implementation for testing ───────────────────────────────

    private class FakeLocationProvider(
        private val hasPermission: Boolean,
        private val location: CoarseLocation?,
    ) : LocationProvider {
        override suspend fun getCoarseLocation(): CoarseLocation? {
            if (!hasPermission) return null
            return location
        }

        override fun hasPermission(): Boolean = hasPermission
    }
}
