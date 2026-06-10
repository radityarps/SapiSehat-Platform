package com.sapisehat.app.domain.model

/**
 * Coarse location data attached to a scan.
 * Stored locally only — never uploaded to the server by default.
 */
data class CoarseLocation(
    val latitude: Double,
    val longitude: Double,
    val source: LocationSource,
)

enum class LocationSource {
    /** User typed a location manually. */
    MANUAL,
    /** Obtained from device GPS/network with user permission. */
    GPS,
    /** No location captured. */
    NONE,
}
