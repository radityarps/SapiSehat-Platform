package com.sapisehat.app

import android.app.Application
import com.sapisehat.app.data.repository.PurgeManager
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class SapiSehatApplication : Application() {

    @Inject lateinit var purgeManager: PurgeManager

    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        // Purge soft-deleted records older than 30 days on each app launch
        applicationScope.launch {
            runCatching { purgeManager.purgeExpired() }
        }
    }
}
