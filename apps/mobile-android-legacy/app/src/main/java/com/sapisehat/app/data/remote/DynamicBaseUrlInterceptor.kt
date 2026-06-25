package com.sapisehat.app.data.remote

import com.sapisehat.app.data.local.SettingsDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

class DynamicBaseUrlInterceptor(
    private val settingsDataStore: SettingsDataStore
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val originalUrl = originalRequest.url

        // Get the server URL from DataStore (blocking, but only for the request)
        val serverUrl = runBlocking { settingsDataStore.serverUrl.first() }
        val baseUrl = if (serverUrl.isNotBlank()) serverUrl else null

        return if (baseUrl != null) {
            val httpUrl = baseUrl.toHttpUrlOrNull()
            if (httpUrl != null) {
                val newUrl = originalUrl
                    .newBuilder()
                    .scheme(httpUrl.scheme)
                    .host(httpUrl.host)
                    .port(httpUrl.port)
                    .build()
                val newRequest = originalRequest.newBuilder().url(newUrl).build()
                chain.proceed(newRequest)
            } else {
                chain.proceed(originalRequest)
            }
        } else {
            chain.proceed(originalRequest)
        }
    }
}
