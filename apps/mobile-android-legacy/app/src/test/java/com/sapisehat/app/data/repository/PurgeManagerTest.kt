package com.sapisehat.app.data.repository

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sapisehat.app.data.local.AppDatabase
import com.sapisehat.app.data.local.dao.DetectionDao
import com.sapisehat.app.data.local.entity.DetectionEntity
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Tests for PurgeManager: verifies 30-day purge removes expired records
 * and preserves recent soft-deleted records.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class PurgeManagerTest {

    private lateinit var db: AppDatabase
    private lateinit var dao: DetectionDao
    private lateinit var purgeManager: PurgeManager

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = db.detectionDao()
        purgeManager = PurgeManager(dao)
    }

    @After
    fun teardown() {
        db.close()
    }

    private fun createEntity(id: Long = 0) = DetectionEntity(
        id = id,
        timestamp = System.currentTimeMillis(),
        imagePath = null,
        predictedClass = "FMD",
        displayLabel = "PMK",
        confidence = 0.9f,
        scoreHealthy = 0.05f,
        scoreFmd = 0.9f,
        scoreLsd = 0.05f,
        inferenceMode = "ONLINE",
        isReliable = true,
        processingMs = 200,
    )

    @Test
    fun `purgeExpired removes records deleted more than 30 days ago`() = runTest {
        val id = dao.insert(createEntity())
        // Soft-delete with timestamp 31 days ago
        val thirtyOneDaysAgo = System.currentTimeMillis() - (31L * 24 * 60 * 60 * 1000)
        dao.softDelete(id, thirtyOneDaysAgo)

        purgeManager.purgeExpired()

        assertNull(dao.findById(id))
    }

    @Test
    fun `purgeExpired preserves records deleted less than 30 days ago`() = runTest {
        val id = dao.insert(createEntity())
        // Soft-delete with timestamp 5 days ago
        val fiveDaysAgo = System.currentTimeMillis() - (5L * 24 * 60 * 60 * 1000)
        dao.softDelete(id, fiveDaysAgo)

        purgeManager.purgeExpired()

        assertNotNull(dao.findById(id))
    }

    @Test
    fun `purgeExpired does not affect non-deleted records`() = runTest {
        val id = dao.insert(createEntity())

        purgeManager.purgeExpired()

        assertNotNull(dao.findById(id))
    }

    @Test
    fun `purgeExpired handles multiple expired records`() = runTest {
        val id1 = dao.insert(createEntity())
        val id2 = dao.insert(createEntity())
        val id3 = dao.insert(createEntity())

        val oldTimestamp = System.currentTimeMillis() - (60L * 24 * 60 * 60 * 1000)
        dao.softDelete(id1, oldTimestamp)
        dao.softDelete(id2, oldTimestamp)
        // id3 not deleted

        purgeManager.purgeExpired()

        assertNull(dao.findById(id1))
        assertNull(dao.findById(id2))
        assertNotNull(dao.findById(id3))
    }

    @Test
    fun `purgeExpired with no expired records does nothing`() = runTest {
        val id = dao.insert(createEntity())
        val recentDelete = System.currentTimeMillis() - (1L * 24 * 60 * 60 * 1000)
        dao.softDelete(id, recentDelete)

        val countBefore = dao.findById(id)
        purgeManager.purgeExpired()
        val countAfter = dao.findById(id)

        assertEquals(countBefore?.id, countAfter?.id)
    }
}
