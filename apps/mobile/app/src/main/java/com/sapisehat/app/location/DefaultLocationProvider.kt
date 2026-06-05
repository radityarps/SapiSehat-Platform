package com.sapisehat.app.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import androidx.core.content.ContextCompat
import com.sapisehat.app.domain.model.CoarseLocation
import com.sapisehat.app.domain.model.LocationSource
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

/**
 * Default location provider using Android LocationManager with NETWORK_PROVIDER only.
 * Uses ACCESS_COARSE_LOCATION permission — never requests fine/precise location.
 * Rounds to 2 decimal places (~1.1km precision) for privacy.
 * Times out after 5 seconds to avoid blocking the scan flow.
 */
@Singleton
class DefaultLocationProvider @Inject constructor(
    @ApplicationContext private val context: Context,
) : LocationProvider {

    override fun hasPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context, Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }

    override suspend fun getCoarseLocation(): CoarseLocation? {
        if (!hasPermission()) return null

        return withTimeoutOrNull(5_000L) {
            getLastKnownOrRequest()
        }
    }

    @Suppress("MissingPermission")
    private suspend fun getLastKnownOrRequest(): CoarseLocation? {
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
            ?: return null

        // Use NETWORK_PROVIDER only for coarse location
        if (!locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
            return null
        }

        // Try last known location first (fast path)
        val lastKnown = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)

        if (lastKnown != null && isRecent(lastKnown)) {
            return lastKnown.toCoarseLocation()
        }

        // Request a single update with timeout
        return requestSingleUpdate(locationManager)
    }

    @Suppress("MissingPermission")
    private suspend fun requestSingleUpdate(locationManager: LocationManager): CoarseLocation? {
        return suspendCancellableCoroutine { continuation ->
            val listener = object : android.location.LocationListener {
                override fun onLocationChanged(location: Location) {
                    locationManager.removeUpdates(this)
                    if (continuation.isActive) {
                        continuation.resume(location.toCoarseLocation())
                    }
                }

                @Deprecated("Deprecated in API")
                override fun onStatusChanged(provider: String?, status: Int, extras: android.os.Bundle?) {}
                override fun onProviderEnabled(provider: String) {}
                override fun onProviderDisabled(provider: String) {
                    if (continuation.isActive) {
                        continuation.resume(null)
                    }
                }
            }

            locationManager.requestSingleUpdate(
                LocationManager.NETWORK_PROVIDER,
                listener,
                android.os.Looper.getMainLooper(),
            )

            continuation.invokeOnCancellation {
                locationManager.removeUpdates(listener)
            }
        }
    }

    private fun isRecent(location: Location): Boolean {
        val ageMs = System.currentTimeMillis() - location.time
        return ageMs < 10 * 60 * 1000 // 10 minutes
    }

    private fun Location.toCoarseLocation(): CoarseLocation {
        // Round to 2 decimal places ≈ 1.1km precision for privacy
        val roundedLat = Math.round(latitude * 100.0) / 100.0
        val roundedLng = Math.round(longitude * 100.0) / 100.0
        return CoarseLocation(
            latitude = roundedLat,
            longitude = roundedLng,
            source = LocationSource.GPS,
        )
    }
}
