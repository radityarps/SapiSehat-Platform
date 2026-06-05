package com.sapisehat.app.ui.settings

import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.data.repository.DetectionRepository
import com.sapisehat.app.data.repository.PurgeManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever
import org.mockito.kotlin.verify

/**
 * Unit tests for SettingsViewModel upload consent toggle functionality.
 *
 * Validates: Requirements 4.1, 4.2, 4.3
 */
@OptIn(ExperimentalCoroutinesApi::class)
class SettingsViewModelTest {

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var settingsDataStore: SettingsDataStore
    private lateinit var detectionRepository: DetectionRepository
    private lateinit var purgeManager: PurgeManager
    private lateinit var uploadConsentFlow: MutableStateFlow<Boolean?>

    private lateinit var viewModel: SettingsViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        settingsDataStore = mock()
        detectionRepository = mock()
        purgeManager = mock()

        // Set up flows for the mock
        uploadConsentFlow = MutableStateFlow(null)
        whenever(settingsDataStore.uploadConsent).thenReturn(uploadConsentFlow)
        whenever(settingsDataStore.language).thenReturn(MutableStateFlow("system"))
        whenever(settingsDataStore.textSize).thenReturn(MutableStateFlow("system"))
        whenever(settingsDataStore.serverUrl).thenReturn(MutableStateFlow(""))
        whenever(settingsDataStore.locationEnabled).thenReturn(MutableStateFlow(false))
        whenever(settingsDataStore.crashReportingConsent).thenReturn(MutableStateFlow(false))
        whenever(settingsDataStore.manualLatitude).thenReturn(MutableStateFlow(null))
        whenever(settingsDataStore.manualLongitude).thenReturn(MutableStateFlow(null))

        viewModel = SettingsViewModel(settingsDataStore, detectionRepository, purgeManager)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `uploadConsent initial state is null when undecided`() = runTest(testDispatcher) {
        // Start a collector to activate WhileSubscribed
        val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
        advanceUntilIdle()

        assertNull(viewModel.uploadConsent.value)
        job.cancel()
    }

    @Test
    fun `uploadConsent reflects true when consent is granted`() = runTest(testDispatcher) {
        // Start a collector to activate WhileSubscribed
        val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
        advanceUntilIdle()

        uploadConsentFlow.value = true
        advanceUntilIdle()

        assertEquals(true, viewModel.uploadConsent.value)
        job.cancel()
    }

    @Test
    fun `uploadConsent reflects false when consent is denied`() = runTest(testDispatcher) {
        // Start a collector to activate WhileSubscribed
        val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
        advanceUntilIdle()

        uploadConsentFlow.value = false
        advanceUntilIdle()

        assertEquals(false, viewModel.uploadConsent.value)
        job.cancel()
    }

    @Test
    fun `setUploadConsent true calls settingsDataStore setUploadConsent with true`() = runTest(testDispatcher) {
        viewModel.setUploadConsent(true)
        advanceUntilIdle()

        verify(settingsDataStore).setUploadConsent(true)
    }

    @Test
    fun `setUploadConsent false calls settingsDataStore setUploadConsent with false`() = runTest(testDispatcher) {
        viewModel.setUploadConsent(false)
        advanceUntilIdle()

        verify(settingsDataStore).setUploadConsent(false)
    }

    @Test
    fun `toggle from true to false updates consent correctly`() = runTest(testDispatcher) {
        // Start a collector to activate WhileSubscribed
        val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
        advanceUntilIdle()

        // Start with consent granted
        uploadConsentFlow.value = true
        advanceUntilIdle()
        assertEquals(true, viewModel.uploadConsent.value)

        // User disables consent via toggle
        viewModel.setUploadConsent(false)
        advanceUntilIdle()

        verify(settingsDataStore).setUploadConsent(false)

        // Simulate the data store updating the flow
        uploadConsentFlow.value = false
        advanceUntilIdle()

        assertEquals(false, viewModel.uploadConsent.value)
        job.cancel()
    }
}
