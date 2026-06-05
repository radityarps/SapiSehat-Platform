package com.sapisehat.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow
import com.sapisehat.app.data.local.entity.DetectionEntity

@Dao
interface DetectionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: DetectionEntity): Long

    @Query("UPDATE detection_records SET title = :title, description = :description WHERE id = :id")
    suspend fun updateNote(id: Long, title: String?, description: String?)

    @Query("SELECT * FROM detection_records WHERE deletedAt IS NULL ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<DetectionEntity>>

    @Query("SELECT * FROM detection_records ORDER BY timestamp DESC")
    fun observeAllIncludingDeleted(): Flow<List<DetectionEntity>>

    @Query("DELETE FROM detection_records WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("DELETE FROM detection_records")
    suspend fun deleteAll()

    @Query("SELECT * FROM detection_records WHERE id = :id LIMIT 1")
    suspend fun findById(id: Long): DetectionEntity?

    @Query("SELECT * FROM detection_records WHERE id = :id LIMIT 1")
    fun observeById(id: Long): Flow<DetectionEntity?>

    @Query("SELECT imagePath FROM detection_records WHERE imagePath IS NOT NULL")
    suspend fun findAllImagePaths(): List<String>

    @Query("SELECT pdfCachePath FROM detection_records WHERE pdfCachePath IS NOT NULL")
    suspend fun findAllPdfPaths(): List<String>

    @Query("SELECT * FROM detection_records WHERE predictedClass = :classFilter AND deletedAt IS NULL ORDER BY timestamp DESC")
    fun observeByClass(classFilter: String): Flow<List<DetectionEntity>>

    @Query("SELECT * FROM detection_records WHERE inferenceMode = :modeFilter AND deletedAt IS NULL ORDER BY timestamp DESC")
    fun observeByMode(modeFilter: String): Flow<List<DetectionEntity>>

    @Query("UPDATE detection_records SET deletedAt = :deletedAt WHERE id = :id")
    suspend fun softDelete(id: Long, deletedAt: Long)

    @Query("UPDATE detection_records SET deletedAt = NULL WHERE id = :id")
    suspend fun restoreDeleted(id: Long)

    @Query("SELECT * FROM detection_records WHERE deletedAt IS NOT NULL AND deletedAt < :cutoff")
    suspend fun findExpiredSoftDeleted(cutoff: Long): List<DetectionEntity>

    @Query("DELETE FROM detection_records WHERE deletedAt IS NOT NULL AND deletedAt < :cutoff")
    suspend fun purgeExpiredSoftDeleted(cutoff: Long)

    @Query("UPDATE detection_records SET pdfCachePath = :path WHERE id = :id")
    suspend fun updatePdfCachePath(id: Long, path: String)
}
