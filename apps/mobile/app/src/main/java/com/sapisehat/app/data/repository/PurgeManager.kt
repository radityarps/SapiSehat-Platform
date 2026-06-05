package com.sapisehat.app.data.repository

import com.sapisehat.app.data.local.dao.DetectionDao
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Purges soft-deleted records older than 30 days.
 * Cleans up associated local image and PDF cache files.
 * Called on app startup — no WorkManager dependency needed for this simple case.
 */
@Singleton
class PurgeManager @Inject constructor(
    private val detectionDao: DetectionDao,
) {
    companion object {
        /** 30 days in milliseconds. */
        const val PURGE_THRESHOLD_MS = 30L * 24 * 60 * 60 * 1000
    }

    /**
     * Purges all soft-deleted records older than 30 days.
     * Deletes associated image and PDF files from local storage.
     */
    suspend fun purgeExpired() {
        val cutoff = System.currentTimeMillis() - PURGE_THRESHOLD_MS
        val expired = detectionDao.findExpiredSoftDeleted(cutoff)

        // Delete associated files
        expired.forEach { entity ->
            entity.imagePath?.let { deleteFileIfExists(it) }
            entity.pdfCachePath?.let { deleteFileIfExists(it) }
        }

        // Remove DB records
        detectionDao.purgeExpiredSoftDeleted(cutoff)
    }

    private fun deleteFileIfExists(path: String) {
        runCatching {
            val file = File(path)
            if (file.exists()) file.delete()
        }
    }
}
