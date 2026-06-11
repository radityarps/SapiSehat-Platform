package com.sapisehat.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "detection_records")
data class DetectionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestamp: Long,
    val imagePath: String?,
    val predictedClass: String,
    val displayLabel: String,
    val confidence: Float,
    val scoreHealthy: Float,
    val scoreFmd: Float,
    val scoreLsd: Float,
    val inferenceMode: String,
    val isReliable: Boolean,
    val processingMs: Int?,
    val title: String? = null,
    val description: String? = null,
    val consentStatus: String = "UNDECIDED",
    val appVersion: String? = null,
    val modelVersion: String? = null,
    val imageSource: String? = null,
    val preprocessingSummary: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val locationSource: String? = null,
    val deletedAt: Long? = null,
    val pdfCachePath: String? = null,
    val outcome: String = "DISEASE_CLASS",
)
