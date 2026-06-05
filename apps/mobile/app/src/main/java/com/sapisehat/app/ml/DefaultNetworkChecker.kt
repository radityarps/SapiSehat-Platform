package com.sapisehat.app.ml

import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DefaultNetworkChecker @Inject constructor(
    private val connectivityManager: ConnectivityManager
) : NetworkChecker {
    override fun isOnline(): Boolean {
        val caps = connectivityManager.getNetworkCapabilities(
            connectivityManager.activeNetwork ?: return false
        ) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
}
