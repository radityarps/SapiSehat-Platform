package com.sapisehat.app.di

import android.content.Context
import android.net.ConnectivityManager
import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.location.DefaultLocationProvider
import com.sapisehat.app.location.LocationProvider
import com.sapisehat.app.ml.DefaultNetworkChecker
import com.sapisehat.app.ml.ImageClassifier
import com.sapisehat.app.ml.ImagePreprocessor
import com.sapisehat.app.ml.NetworkChecker
import com.sapisehat.app.ml.OfflineInferenceEngine
import com.sapisehat.app.ml.OnlineInferenceClient
import com.sapisehat.app.ml.preprocessing.ClientPreprocessor
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    fun provideConnectivityManager(@ApplicationContext context: Context): ConnectivityManager {
        return context.getSystemService(ConnectivityManager::class.java)
    }

    @Provides
    @Singleton
    fun provideNetworkChecker(connectivityManager: ConnectivityManager): NetworkChecker {
        return DefaultNetworkChecker(connectivityManager)
    }

    @Provides
    @Singleton
    fun provideImagePreprocessor(clientPreprocessor: ClientPreprocessor): ImagePreprocessor {
        return clientPreprocessor
    }

    @Provides
    @Singleton
    @OnlineClassifier
    fun provideOnlineClassifier(onlineClient: OnlineInferenceClient): ImageClassifier {
        return onlineClient
    }

    @Provides
    @Singleton
    @OfflineClassifier
    fun provideOfflineClassifier(offlineEngine: OfflineInferenceEngine): ImageClassifier {
        return offlineEngine
    }

    @Provides
    @Singleton
    fun provideSettingsDataStore(
        @ApplicationContext context: Context
    ): SettingsDataStore {
        return SettingsDataStore(context)
    }

    @Provides
    @Singleton
    fun provideLocationProvider(defaultLocationProvider: DefaultLocationProvider): LocationProvider {
        return defaultLocationProvider
    }
}
