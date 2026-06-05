package com.sapisehat.app.location

import com.sapisehat.app.domain.model.CoarseLocation
import com.sapisehat.app.domain.model.LocationSource

/**
 * Pure function that resolves the final location to attach to a scan result.
 *
 * Priority:
 * 1. GPS location (if GPS assist enabled and location obtained)
 * 2. Manual location (always available, no permission needed)
 * 3. No location
 *
 * This is a pure function with no side effects, enabling direct unit testing.
 */
object LocationResolver {

    data class Result(
        val latitude: Double?,
        val longitude: Double?,
        val source: LocationSource?,
    )

    /**
     * Resolves the location to persist with a scan.
     *
     * @param gpsAssistEnabled Whether the GPS assist toggle is on (requires permission)
     * @param gpsLocation The GPS location obtained from the provider, or null
     * @param manualLatitude Manual latitude from settings, or null
     * @param manualLongitude Manual longitude from settings, or null
     */
    fun resolve(
        gpsAssistEnabled: Boolean,
        gpsLocation: CoarseLocation?,
        manualLatitude: Double?,
        manualLongitude: Double?,
    ): Result {
        // 1. GPS takes priority when enabled and available
        if (gpsAssistEnabled && gpsLocation != null) {
            return Result(
                latitude = gpsLocation.latitude,
                longitude = gpsLocation.longitude,
                source = gpsLocation.source,
            )
        }

        // 2. Manual location is always available (no permission needed)
        if (manualLatitude != null && manualLongitude != null) {
            return Result(
                latitude = manualLatitude,
                longitude = manualLongitude,
                source = LocationSource.MANUAL,
            )
        }

        // 3. No location
        return Result(latitude = null, longitude = null, source = null)
    }
}
