package com.sapisehat.app.ml

/**
 * Abstraction over network connectivity checks to enable unit testing
 * without Android framework dependencies.
 */
interface NetworkChecker {
    fun isOnline(): Boolean
}
