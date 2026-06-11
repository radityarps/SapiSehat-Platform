package com.sapisehat.app.ml

import android.net.Uri
import com.sapisehat.app.domain.model.ClassifyResponse
import com.sapisehat.app.domain.model.ConsentStatus
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.domain.model.InferenceMode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

/**
 * Property-based style tests for InferenceRouter consent routing logic.
 *
 * Since the project does not include Kotest Property or mockk, we use simple
 * fake implementations of the interfaces and parameterized test cases covering
 * all consent × connectivity combinations to validate universal properties.
 *
 * **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 2.4, 2.5, 3.1, 3.2**
 */
@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
class InferenceRouterTest {

    private val testDispatcher = UnconfinedTestDispatcher()

    // --- Fakes ---

    /** Fake preprocessor that records whether it was called. */
    private class FakePreprocessor : ImagePreprocessor {
        var processCallCount = 0
        override fun process(imageUri: Uri): ByteArray {
            processCallCount++
            return byteArrayOf(0x01, 0x02, 0x03)
        }
    }

    /** Fake online classifier that returns a deterministic ONLINE result or throws. */
    private class FakeOnlineClassifier(
        private val shouldThrow: Boolean = false
    ) : ImageClassifier {
        override suspend fun classify(jpegBytes: ByteArray): DetectionResult {
            if (shouldThrow) throw RuntimeException("Simulated online failure")
            return DetectionResult(
                label = "healthy",
                displayLabel = "Sapi Sehat",
                confidence = 0.95f,
                isReliable = true,
                allScores = mapOf("FMD" to 0.02f, "LSD" to 0.03f, "healthy" to 0.95f),
                inferenceMode = InferenceMode.ONLINE
            )
        }
    }

    /** Fake offline classifier that returns a deterministic OFFLINE result. */
    private class FakeOfflineClassifier : ImageClassifier {
        override suspend fun classify(jpegBytes: ByteArray): DetectionResult {
            return DetectionResult(
                label = "FMD",
                displayLabel = "Penyakit Mulut dan Kuku (FMD)",
                confidence = 0.80f,
                isReliable = true,
                allScores = mapOf("FMD" to 0.80f, "LSD" to 0.10f, "healthy" to 0.10f),
                inferenceMode = InferenceMode.OFFLINE
            )
        }
    }

    /** Fake NetworkChecker that reports configurable online/offline state. */
    private class FakeNetworkChecker(private val online: Boolean) : NetworkChecker {
        override fun isOnline(): Boolean = online
    }

    // --- Test image URIs (property: "for any image URI") ---
    private val testUris = listOf(
        Uri.parse("content://media/external/images/1"),
        Uri.parse("content://media/external/images/999"),
        Uri.parse("file:///storage/emulated/0/DCIM/photo.jpg"),
        Uri.parse("content://com.sapisehat.fileprovider/images/capture_001.jpg"),
        Uri.parse("content://media/external/images/12345")
    )

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun createRouter(
        online: Boolean,
        onlineThrows: Boolean = false
    ): Pair<InferenceRouter, FakePreprocessor> {
        val preprocessor = FakePreprocessor()
        val router = InferenceRouter(
            clientPreprocessor = preprocessor,
            onlineClient = FakeOnlineClassifier(shouldThrow = onlineThrows),
            offlineEngine = FakeOfflineClassifier(),
            networkChecker = FakeNetworkChecker(online)
        )
        return router to preprocessor
    }

    // =========================================================================
    // Property 1: Consent-gated online routing
    // For any image URI, when online AND consent ALLOWED, router returns
    // Success with ONLINE mode.
    // **Validates: Requirements 6.1, 2.4**
    // =========================================================================
    @Test
    fun `Property 1 - online with consent ALLOWED routes to online inference`() = runTest {
        val (router, _) = createRouter(online = true)

        for (uri in testUris) {
            val response = router.classify(uri, ConsentStatus.ALLOWED)

            assertTrue(
                "Expected ClassifyResponse.Success for uri=$uri, got $response",
                response is ClassifyResponse.Success
            )
            val result = (response as ClassifyResponse.Success).result
            assertEquals(
                "Expected ONLINE inference mode for uri=$uri",
                InferenceMode.ONLINE,
                result.inferenceMode
            )
            assertEquals(
                "Expected consentStatus ALLOWED attached to result for uri=$uri",
                ConsentStatus.ALLOWED,
                result.consentStatus
            )
        }
    }

    // =========================================================================
    // Property 2: Denied consent forces offline routing
    // For any image URI and any connectivity, when consent DENIED, router
    // returns Success with OFFLINE mode.
    // **Validates: Requirements 6.2, 2.5, 3.1, 3.2**
    // =========================================================================
    @Test
    fun `Property 2 - denied consent forces offline routing regardless of connectivity`() = runTest {
        for (online in listOf(true, false)) {
            val (router, _) = createRouter(online = online)

            for (uri in testUris) {
                val response = router.classify(uri, ConsentStatus.DENIED)

                assertTrue(
                    "Expected ClassifyResponse.Success for uri=$uri, online=$online",
                    response is ClassifyResponse.Success
                )
                val result = (response as ClassifyResponse.Success).result
                assertEquals(
                    "Expected OFFLINE inference mode for uri=$uri, online=$online",
                    InferenceMode.OFFLINE,
                    result.inferenceMode
                )
                assertEquals(
                    "Expected consentStatus DENIED attached to result for uri=$uri",
                    ConsentStatus.DENIED,
                    result.consentStatus
                )
            }
        }
    }

    // =========================================================================
    // Property 3: Undecided consent suspends classification
    // For any image URI, when online AND consent UNDECIDED, router returns
    // ConsentRequired without preprocessing.
    // **Validates: Requirements 6.3, 2.1**
    // =========================================================================
    @Test
    fun `Property 3 - undecided consent while online returns ConsentRequired without preprocessing`() = runTest {
        val (router, preprocessor) = createRouter(online = true)

        for (uri in testUris) {
            preprocessor.processCallCount = 0
            val response = router.classify(uri, ConsentStatus.UNDECIDED)

            assertEquals(
                "Expected ConsentRequired for uri=$uri",
                ClassifyResponse.ConsentRequired,
                response
            )
            assertEquals(
                "Expected no preprocessing for uri=$uri when consent is undecided",
                0,
                preprocessor.processCallCount
            )
        }
    }

    // =========================================================================
    // Property 4: Offline network forces offline inference
    // For any image URI and any consent status, when offline, router returns
    // Success with OFFLINE mode.
    // **Validates: Requirements 6.4**
    // =========================================================================
    @Test
    fun `Property 4 - offline network forces offline inference for any consent status`() = runTest {
        val (router, _) = createRouter(online = false)

        for (consent in ConsentStatus.entries) {
            for (uri in testUris) {
                val response = router.classify(uri, consent)

                // When offline + UNDECIDED, the router should still go offline
                // (the UNDECIDED check only triggers when online)
                assertTrue(
                    "Expected ClassifyResponse.Success for uri=$uri, consent=$consent",
                    response is ClassifyResponse.Success
                )
                val result = (response as ClassifyResponse.Success).result
                assertEquals(
                    "Expected OFFLINE inference mode for uri=$uri, consent=$consent",
                    InferenceMode.OFFLINE,
                    result.inferenceMode
                )
                assertEquals(
                    "Expected consent=$consent attached to result for uri=$uri",
                    consent,
                    result.consentStatus
                )
            }
        }
    }

    // =========================================================================
    // Property 5: Online failure triggers fallback
    // For any image URI, when online AND consent ALLOWED AND online throws,
    // router returns Success with OFFLINE_FALLBACK mode.
    // **Validates: Requirements 6.5**
    // =========================================================================
    @Test
    fun `Property 5 - online failure with consent ALLOWED triggers offline fallback`() = runTest {
        val (router, _) = createRouter(online = true, onlineThrows = true)

        for (uri in testUris) {
            val response = router.classify(uri, ConsentStatus.ALLOWED)

            assertTrue(
                "Expected ClassifyResponse.Success for uri=$uri after online failure",
                response is ClassifyResponse.Success
            )
            val result = (response as ClassifyResponse.Success).result
            assertEquals(
                "Expected OFFLINE_FALLBACK inference mode for uri=$uri",
                InferenceMode.OFFLINE_FALLBACK,
                result.inferenceMode
            )
            assertEquals(
                "Expected consentStatus ALLOWED attached to result for uri=$uri",
                ConsentStatus.ALLOWED,
                result.consentStatus
            )
        }
    }
}
