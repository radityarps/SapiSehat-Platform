package com.sapisehat.app.location

import com.sapisehat.app.domain.model.CoarseLocation

/**
 * Provides coarse location for scan history.
 * Location is stored locally only and never uploaded by default.
 */
interface LocationProvider {
    /**
     * Attempts to get the current coarse location.
     * Returns null if location is unavailable or permission not granted.
     * Implementations should timeout quickly (≤5s) to avoid blocking inference.
     */
    suspend fun getCoarseLocation(): CoarseLocation?

    /** Whether the app currently has location permission. */
    fun hasPermission(): Boolean
}
