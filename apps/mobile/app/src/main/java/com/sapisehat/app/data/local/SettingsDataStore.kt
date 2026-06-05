package com.sapisehat.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Singleton

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

@Singleton
class SettingsDataStore(
    @ApplicationContext private val context: Context
) {
    companion object Keys {
        val KEY_LANGUAGE = stringPreferencesKey("language")
        val KEY_TEXT_SIZE = stringPreferencesKey("text_size")
        val KEY_SERVER_URL = stringPreferencesKey("server_url")
        val KEY_UPLOAD_CONSENT = booleanPreferencesKey("upload_consent")
        val KEY_LOCATION_ENABLED = booleanPreferencesKey("location_enabled")
        val KEY_MANUAL_LATITUDE = stringPreferencesKey("manual_latitude")
        val KEY_MANUAL_LONGITUDE = stringPreferencesKey("manual_longitude")
        val KEY_CRASH_REPORTING = booleanPreferencesKey("crash_reporting_consent")
    }

    val language: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_LANGUAGE] ?: "system"
    }

    val textSize: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_TEXT_SIZE] ?: "system"
    }

    val serverUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_SERVER_URL] ?: ""
    }

    suspend fun setLanguage(value: String) {
        context.dataStore.edit { prefs -> prefs[KEY_LANGUAGE] = value }
    }

    suspend fun setTextSize(value: String) {
        context.dataStore.edit { prefs -> prefs[KEY_TEXT_SIZE] = value }
    }

    suspend fun setServerUrl(value: String) {
        context.dataStore.edit { prefs -> prefs[KEY_SERVER_URL] = value }
    }

    val uploadConsent: Flow<Boolean?> = context.dataStore.data.map { prefs ->
        if (prefs.contains(KEY_UPLOAD_CONSENT)) prefs[KEY_UPLOAD_CONSENT] else null
    }

    suspend fun setUploadConsent(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_UPLOAD_CONSENT] = value }
    }

    val locationEnabled: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_LOCATION_ENABLED] ?: false
    }

    suspend fun setLocationEnabled(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_LOCATION_ENABLED] = value }
    }

    val manualLatitude: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_MANUAL_LATITUDE]
    }

    val manualLongitude: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_MANUAL_LONGITUDE]
    }

    suspend fun setManualLocation(latitude: String?, longitude: String?) {
        context.dataStore.edit { prefs ->
            if (latitude != null) prefs[KEY_MANUAL_LATITUDE] = latitude
            else prefs.remove(KEY_MANUAL_LATITUDE)
            if (longitude != null) prefs[KEY_MANUAL_LONGITUDE] = longitude
            else prefs.remove(KEY_MANUAL_LONGITUDE)
        }
    }

    val crashReportingConsent: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_CRASH_REPORTING] ?: false
    }

    suspend fun setCrashReportingConsent(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_CRASH_REPORTING] = value }
    }
}
