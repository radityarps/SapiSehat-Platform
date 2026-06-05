package com.sapisehat.app.data.local

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sapisehat.app.data.local.dao.DetectionDao
import com.sapisehat.app.data.local.entity.DetectionEntity
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Real Room DAO tests using in-memory database via Robolectric.
 * Covers save/read/update notes/filters/soft-delete acceptance criteria.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class DetectionDaoTest {

    private lateinit var db: AppDatabase
    private lateinit var dao: DetectionDao

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = db.detectionDao()
    }

    @After
    fun teardown() {
        db.close()
    }

    private fun createEntity(
        id: Long = 0,
        predictedClass: String = "FMD",
        inferenceMode: String = "ONLINE",
        consentStatus: String = "ALLOWED",
        appVersion: String? = "1.0.0",
        modelVersion: String? = "MobileNetV2-v3",
        imageSource: String? = "CAMERA",
        preprocessingSummary: String? = "EXIF correct, resize, normalize",
        latitude: Double? = null,
        longitude: Double? = null,
        deletedAt: Long? = null,
        pdfCachePath: String? = null,
        title: String? = null,
        description: String? = null,
    ) = DetectionEntity(
        id = id,
        timestamp = System.currentTimeMillis(),
        imagePath = "/images/test.jpg",
        predictedClass = predictedClass,
        displayLabel = "PMK",
        confidence = 0.92f,
        scoreHealthy = 0.03f,
        scoreFmd = 0.92f,
        scoreLsd = 0.05f,
        inferenceMode = inferenceMode,
        isReliable = true,
        processingMs = 200,
        title = title,
        description = description,
        consentStatus = consentStatus,
        appVersion = appVersion,
        modelVersion = modelVersion,
        imageSource = imageSource,
        preprocessingSummary = preprocessingSummary,
        latitude = latitude,
        longitude = longitude,
        deletedAt = deletedAt,
        pdfCachePath = pdfCachePath,
    )

    // ── Save and read metadata roundtrip ──────────────────────────────

    @Test
    fun `save and read preserves all metadata fields`() = runTest {
        val entity = createEntity(
            appVersion = "2.0.0",
            modelVersion = "v3-tflite",
            imageSource = "GALLERY",
            preprocessingSummary = "resize 224x224",
            latitude = -6.2,
            longitude = 106.8,
            pdfCachePath = "/cache/report.pdf",
            consentStatus = "DENIED",
        )
        val id = dao.insert(entity)

        val loaded = dao.findById(id)
        assertNotNull(loaded)
        assertEquals("2.0.0", loaded!!.appVersion)
        assertEquals("v3-tflite", loaded.modelVersion)
        assertEquals("GALLERY", loaded.imageSource)
        assertEquals("resize 224x224", loaded.preprocessingSummary)
        assertEquals(-6.2, loaded.latitude!!, 0.001)
        assertEquals(106.8, loaded.longitude!!, 0.001)
        assertEquals("/cache/report.pdf", loaded.pdfCachePath)
        assertEquals("DENIED", loaded.consentStatus)
    }

    @Test
    fun `save and read preserves null optional fields`() = runTest {
        val entity = createEntity(
            appVersion = null,
            modelVersion = null,
            imageSource = null,
            preprocessingSummary = null,
            latitude = null,
            longitude = null,
            pdfCachePath = null,
        )
        val id = dao.insert(entity)

        val loaded = dao.findById(id)
        assertNotNull(loaded)
        assertNull(loaded!!.appVersion)
        assertNull(loaded.modelVersion)
        assertNull(loaded.imageSource)
        assertNull(loaded.preprocessingSummary)
        assertNull(loaded.latitude)
        assertNull(loaded.longitude)
        assertNull(loaded.pdfCachePath)
    }

    // ── Update notes ──────────────────────────────────────────────────

    @Test
    fun `updateNote changes title and description`() = runTest {
        val id = dao.insert(createEntity(title = null, description = null))

        dao.updateNote(id, "Sapi #3", "Lesi di mulut")

        val loaded = dao.findById(id)
        assertEquals("Sapi #3", loaded!!.title)
        assertEquals("Lesi di mulut", loaded.description)
    }

    @Test
    fun `updateNote can clear title and description`() = runTest {
        val id = dao.insert(createEntity(title = "Old", description = "Old desc"))

        dao.updateNote(id, null, null)

        val loaded = dao.findById(id)
        assertNull(loaded!!.title)
        assertNull(loaded.description)
    }

    // ── Filters ───────────────────────────────────────────────────────

    @Test
    fun `observeByClass returns only matching class`() = runTest {
        dao.insert(createEntity(predictedClass = "FMD"))
        dao.insert(createEntity(predictedClass = "LSD"))
        dao.insert(createEntity(predictedClass = "FMD"))

        val fmdRows = dao.observeByClass("FMD").first()
        assertEquals(2, fmdRows.size)
        assertTrue(fmdRows.all { it.predictedClass == "FMD" })
    }

    @Test
    fun `observeByMode returns only matching mode`() = runTest {
        dao.insert(createEntity(inferenceMode = "ONLINE"))
        dao.insert(createEntity(inferenceMode = "OFFLINE"))
        dao.insert(createEntity(inferenceMode = "ONLINE"))

        val onlineRows = dao.observeByMode("ONLINE").first()
        assertEquals(2, onlineRows.size)
        assertTrue(onlineRows.all { it.inferenceMode == "ONLINE" })
    }

    // ── Soft-delete ───────────────────────────────────────────────────

    @Test
    fun `soft-deleted rows excluded from observeAll`() = runTest {
        val id1 = dao.insert(createEntity())
        dao.insert(createEntity())

        dao.softDelete(id1, System.currentTimeMillis())

        val rows = dao.observeAll().first()
        assertEquals(1, rows.size)
        assertTrue(rows.none { it.id == id1 })
    }

    @Test
    fun `soft-deleted rows excluded from observeByClass`() = runTest {
        val id1 = dao.insert(createEntity(predictedClass = "FMD"))
        dao.insert(createEntity(predictedClass = "FMD"))

        dao.softDelete(id1, System.currentTimeMillis())

        val rows = dao.observeByClass("FMD").first()
        assertEquals(1, rows.size)
    }

    @Test
    fun `soft-deleted rows excluded from observeByMode`() = runTest {
        val id1 = dao.insert(createEntity(inferenceMode = "ONLINE"))
        dao.insert(createEntity(inferenceMode = "ONLINE"))

        dao.softDelete(id1, System.currentTimeMillis())

        val rows = dao.observeByMode("ONLINE").first()
        assertEquals(1, rows.size)
    }

    @Test
    fun `restoreDeleted makes row visible again`() = runTest {
        val id = dao.insert(createEntity())
        dao.softDelete(id, System.currentTimeMillis())

        assertEquals(0, dao.observeAll().first().size)

        dao.restoreDeleted(id)

        assertEquals(1, dao.observeAll().first().size)
    }

    @Test
    fun `purgeExpiredSoftDeleted removes old soft-deleted rows`() = runTest {
        val id1 = dao.insert(createEntity())
        val id2 = dao.insert(createEntity())

        // Soft-delete both with old timestamp
        dao.softDelete(id1, 1000L)
        dao.softDelete(id2, 2000L)

        // Purge anything deleted before cutoff 3000
        dao.purgeExpiredSoftDeleted(3000L)

        // Both should be gone from DB entirely
        assertNull(dao.findById(id1))
        assertNull(dao.findById(id2))
    }

    @Test
    fun `purgeExpiredSoftDeleted does not remove recent soft-deleted rows`() = runTest {
        val id = dao.insert(createEntity())
        dao.softDelete(id, 5000L)

        // Purge with cutoff before the deletedAt
        dao.purgeExpiredSoftDeleted(3000L)

        // Should still exist
        assertNotNull(dao.findById(id))
    }

    // ── observeById ───────────────────────────────────────────────────

    @Test
    fun `observeById returns entity with all fields`() = runTest {
        val id = dao.insert(createEntity(
            title = "Test Title",
            description = "Test Desc",
            imageSource = "CAMERA",
            consentStatus = "ALLOWED",
        ))

        val loaded = dao.observeById(id).first()
        assertNotNull(loaded)
        assertEquals("Test Title", loaded!!.title)
        assertEquals("Test Desc", loaded.description)
        assertEquals("CAMERA", loaded.imageSource)
        assertEquals("ALLOWED", loaded.consentStatus)
    }
}
