package com.sapisehat.app.di

import javax.inject.Qualifier

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class OnlineClassifier

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class OfflineClassifier
