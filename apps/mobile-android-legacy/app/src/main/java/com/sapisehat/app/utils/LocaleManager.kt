package com.sapisehat.app.utils

import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

object LocaleManager {
    fun applyLanguage(language: String) {
        val tags = when (language) {
            "en" -> "en"
            // Include legacy Indonesian tag (in) for broader Android compatibility.
            "id" -> "id-ID,in-ID,in"
            else -> ""
        }
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tags))
    }

    fun currentLanguageSetting(): String {
        val tags = AppCompatDelegate.getApplicationLocales().toLanguageTags()
        return when {
            tags.isBlank() -> "system"
            tags.startsWith("id", ignoreCase = true) || tags.startsWith("in", ignoreCase = true) -> "id"
            tags.startsWith("en", ignoreCase = true) -> "en"
            else -> "system"
        }
    }
}
