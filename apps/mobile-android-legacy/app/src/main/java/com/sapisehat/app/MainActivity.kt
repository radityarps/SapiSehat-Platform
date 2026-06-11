package com.sapisehat.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.data.local.dataStore
import dagger.hilt.android.AndroidEntryPoint
import com.sapisehat.app.ui.navigation.SapiSehatNavHost
import com.sapisehat.app.ui.theme.SapiSehatTheme
import com.sapisehat.app.utils.LocaleManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val savedLanguage = runBlocking {
            applicationContext.dataStore.data
                .map { prefs -> prefs[SettingsDataStore.KEY_LANGUAGE] ?: "system" }
                .first()
        }
        LocaleManager.applyLanguage(savedLanguage)

        super.onCreate(savedInstanceState)

        enableEdgeToEdge()
        setContent {
            val textSizeMode by applicationContext.dataStore.data
                .map { prefs -> prefs[SettingsDataStore.KEY_TEXT_SIZE] ?: "system" }
                .collectAsStateWithLifecycle(initialValue = "system")

            SapiSehatTheme(textSizeMode = textSizeMode) {
                SapiSehatNavHost()
            }
        }
    }
}
