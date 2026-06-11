package com.sapisehat.app.ui.settings

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import com.sapisehat.app.BuildConfig
import com.sapisehat.app.R
import com.sapisehat.app.data.local.SettingsDataStore
import com.sapisehat.app.data.repository.DetectionRepository
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.utils.LocaleManager
import androidx.core.content.ContextCompat
import javax.inject.Inject

// ════════════════════════════════════════════════════════════════════════════
// ViewModel
// ════════════════════════════════════════════════════════════════════════════

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsDataStore: SettingsDataStore,
    private val detectionRepository: DetectionRepository,
    private val purgeManager: com.sapisehat.app.data.repository.PurgeManager,
) : ViewModel() {

    val language: StateFlow<String> = settingsDataStore.language
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "system")

    val textSize: StateFlow<String> = settingsDataStore.textSize
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "system")

    val serverUrl: StateFlow<String> = settingsDataStore.serverUrl
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "")

    val uploadConsent: StateFlow<Boolean?> = settingsDataStore.uploadConsent
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val locationEnabled: StateFlow<Boolean> = settingsDataStore.locationEnabled
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), false)

    val crashReportingConsent: StateFlow<Boolean> = settingsDataStore.crashReportingConsent
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), false)

    private val _snackbarMessageRes = MutableStateFlow<Int?>(null)
    val snackbarMessageRes: StateFlow<Int?> = _snackbarMessageRes.asStateFlow()

    fun setLanguage(value: String) {
        viewModelScope.launch { settingsDataStore.setLanguage(value) }
    }

    fun setTextSize(value: String) {
        viewModelScope.launch { settingsDataStore.setTextSize(value) }
    }

    fun setServerUrl(url: String) {
        viewModelScope.launch { settingsDataStore.setServerUrl(url) }
    }

    fun setUploadConsent(value: Boolean) {
        viewModelScope.launch { settingsDataStore.setUploadConsent(value) }
    }

    fun setLocationEnabled(value: Boolean) {
        viewModelScope.launch { settingsDataStore.setLocationEnabled(value) }
    }

    fun setCrashReportingConsent(value: Boolean) {
        viewModelScope.launch { settingsDataStore.setCrashReportingConsent(value) }
    }

    fun purgeDeletedRecords() {
        viewModelScope.launch {
            runCatching { purgeManager.purgeExpired() }
            _snackbarMessageRes.value = R.string.settings_purge_done
        }
    }

    val manualLatitude: StateFlow<String?> = settingsDataStore.manualLatitude
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val manualLongitude: StateFlow<String?> = settingsDataStore.manualLongitude
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun setManualLocation(latitude: String?, longitude: String?) {
        viewModelScope.launch { settingsDataStore.setManualLocation(latitude, longitude) }
    }

    fun clearAllHistory() {
        // Policy: This is an immediate, permanent purge of ALL detection records
        // and their associated image files. Unlike soft-delete (which retains records
        // for 30 days), this action is irreversible and cannot be undone.
        viewModelScope.launch {
            detectionRepository.deleteAll()
            _snackbarMessageRes.value = R.string.settings_history_cleared
        }
    }

    fun resetOnboarding(context: Context) {
        context.getSharedPreferences(
            context.packageName + "_preferences",
            Context.MODE_PRIVATE,
        )
            .edit()
            .putBoolean("has_completed_onboarding", false)
            .apply()
        _snackbarMessageRes.value = R.string.settings_onboarding_reset
    }

    fun clearSnackbar() {
        _snackbarMessageRes.value = null
    }
}

// ════════════════════════════════════════════════════════════════════════════
// UI
// ════════════════════════════════════════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsRoute(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val language by viewModel.language.collectAsStateWithLifecycle()
    val textSize by viewModel.textSize.collectAsStateWithLifecycle()
    val serverUrl by viewModel.serverUrl.collectAsStateWithLifecycle()
    val uploadConsent by viewModel.uploadConsent.collectAsStateWithLifecycle()
    val locationEnabled by viewModel.locationEnabled.collectAsStateWithLifecycle()
    val crashReportingConsent by viewModel.crashReportingConsent.collectAsStateWithLifecycle()
    val snackbarMessageRes by viewModel.snackbarMessageRes.collectAsStateWithLifecycle()

    var showLanguageDialog by remember { mutableStateOf(false) }
    var showTextSizeDialog by remember { mutableStateOf(false) }
    var showServerUrlDialog by remember { mutableStateOf(false) }
    var showClearHistoryDialog by remember { mutableStateOf(false) }
    var showResetOnboardingDialog by remember { mutableStateOf(false) }
    var showPurgeDialog by remember { mutableStateOf(false) }

    val snackbarHostState = remember { SnackbarHostState() }

    snackbarMessageRes?.let { messageRes ->
        val snackbarText = stringResource(messageRes)
        LaunchedEffect(messageRes) {
            snackbarHostState.showSnackbar(snackbarText)
            viewModel.clearSnackbar()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.settings_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.nav_back))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            // Language
            PreferenceRow(
                title = stringResource(R.string.settings_language),
                value = languageDisplayName(language),
                onClick = { showLanguageDialog = true },
            )

            // Text size
            PreferenceRow(
                title = stringResource(R.string.settings_text_size),
                value = textSizeDisplayName(textSize),
                onClick = { showTextSizeDialog = true },
            )

            // Server URL
            PreferenceRow(
                title = stringResource(R.string.settings_server_url),
                value = serverUrl.ifEmpty { stringResource(R.string.settings_server_url_title) },
                onClick = { showServerUrlDialog = true },
            )

            // Upload consent toggle
            UploadConsentRow(
                checked = uploadConsent == true,
                onCheckedChange = { viewModel.setUploadConsent(it) },
            )

            // Crash reporting consent toggle
            CrashReportingRow(
                checked = crashReportingConsent,
                onCheckedChange = { viewModel.setCrashReportingConsent(it) },
            )

            // Location toggle
            LocationRow(
                enabled = locationEnabled,
                onEnabledChange = { viewModel.setLocationEnabled(it) },
            )

            // Manual location entry (always available, no permission needed)
            ManualLocationRow(viewModel = viewModel)

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // Clear all history
            PreferenceRow(
                title = stringResource(R.string.settings_clear_history),
                onClick = { showClearHistoryDialog = true },
                titleColor = SapiSehatColors.DangerPMK,
            )

            // Purge deleted records
            PreferenceRow(
                title = stringResource(R.string.settings_purge_deleted),
                value = stringResource(R.string.settings_purge_deleted_description),
                onClick = { showPurgeDialog = true },
                titleColor = SapiSehatColors.DangerPMK,
            )

            // Reset onboarding
            PreferenceRow(
                title = stringResource(R.string.settings_reset_onboarding),
                onClick = { showResetOnboardingDialog = true },
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // App version (read-only)
            PreferenceRow(
                title = stringResource(R.string.settings_app_version),
                value = BuildConfig.VERSION_NAME,
                enabled = false,
            )

            // Model version (read-only)
            PreferenceRow(
                title = stringResource(R.string.settings_model_version),
                value = com.sapisehat.app.ml.OfflineInferenceEngine.MODEL_VERSION,
                enabled = false,
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // Privacy section
            Text(
                text = stringResource(R.string.settings_privacy_title),
                style = MaterialTheme.typography.titleMedium,
                color = SapiSehatColors.TextPrimary,
            )
            Spacer(Modifier.height(8.dp))
            listOf(
                R.string.settings_privacy_exif,
                R.string.settings_privacy_no_retention,
                R.string.settings_privacy_local_history,
                R.string.settings_privacy_offline,
                R.string.settings_privacy_location,
            ).forEach { resId ->
                Text(
                    text = "• ${stringResource(resId)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                    modifier = Modifier.padding(vertical = 2.dp),
                )
            }
        }
    }

    // ── Dialogs ──────────────────────────────────────────────────────

    if (showLanguageDialog) {
        SelectionDialog(
            title = stringResource(R.string.settings_language),
            options = listOf(
                "system" to stringResource(R.string.settings_language_system),
                "id" to stringResource(R.string.settings_language_id),
                "en" to stringResource(R.string.settings_language_en),
            ),
            selected = language,
            onSelect = {
                val shouldApplyLanguage = it != LocaleManager.currentLanguageSetting()
                viewModel.setLanguage(it)
                if (shouldApplyLanguage) {
                    LocaleManager.applyLanguage(it)
                    context.findActivity()?.recreate()
                }
                showLanguageDialog = false
            },
            onDismiss = { showLanguageDialog = false },
        )
    }

    if (showTextSizeDialog) {
        SelectionDialog(
            title = stringResource(R.string.settings_text_size),
            options = listOf(
                "system" to stringResource(R.string.settings_text_size_system),
                "small" to stringResource(R.string.settings_text_size_small),
                "medium" to stringResource(R.string.settings_text_size_medium),
                "large" to stringResource(R.string.settings_text_size_large),
            ),
            selected = textSize,
            onSelect = {
                viewModel.setTextSize(it)
                showTextSizeDialog = false
            },
            onDismiss = { showTextSizeDialog = false },
        )
    }

    if (showServerUrlDialog) {
        var editedUrl by remember(serverUrl) { mutableStateOf(serverUrl) }
        AlertDialog(
            onDismissRequest = { showServerUrlDialog = false },
            title = { Text(stringResource(R.string.settings_server_url_title)) },
            text = {
                OutlinedTextField(
                    value = editedUrl,
                    onValueChange = { editedUrl = it },
                    label = { Text(stringResource(R.string.settings_server_url_label)) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.setServerUrl(editedUrl.trim())
                    showServerUrlDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerUrlDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    if (showClearHistoryDialog) {
        AlertDialog(
            onDismissRequest = { showClearHistoryDialog = false },
            title = { Text(stringResource(R.string.settings_clear_history)) },
            text = { Text(stringResource(R.string.settings_clear_history_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.clearAllHistory()
                    showClearHistoryDialog = false
                }) {
                    Text(stringResource(R.string.btn_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearHistoryDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    if (showPurgeDialog) {
        AlertDialog(
            onDismissRequest = { showPurgeDialog = false },
            title = { Text(stringResource(R.string.settings_purge_deleted)) },
            text = { Text(stringResource(R.string.settings_purge_deleted_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.purgeDeletedRecords()
                    showPurgeDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = { showPurgeDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    if (showResetOnboardingDialog) {
        AlertDialog(
            onDismissRequest = { showResetOnboardingDialog = false },
            title = { Text(stringResource(R.string.settings_reset_onboarding)) },
            text = { Text(stringResource(R.string.settings_reset_onboarding_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.resetOnboarding(context)
                    showResetOnboardingDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetOnboardingDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }
}

private fun Context.findActivity(): Activity? {
    var current: Context? = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}

// ════════════════════════════════════════════════════════════════════════════
// Sub-composables
// ════════════════════════════════════════════════════════════════════════════

@Composable
private fun PreferenceRow(
    title: String,
    value: String? = null,
    enabled: Boolean = true,
    titleColor: Color? = null,
    onClick: () -> Unit = {},
) {
    val finalColor = titleColor ?: MaterialTheme.colorScheme.onSurface
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (enabled) finalColor else finalColor.copy(alpha = 0.5f),
                )
                if (value != null) {
                    Text(
                        text = value,
                        style = MaterialTheme.typography.bodyMedium,
                        color = SapiSehatColors.TextSecondary,
                    )
                }
            }
            if (enabled) {
                Text(
                    "›",
                    color = SapiSehatColors.TextSecondary,
                    style = MaterialTheme.typography.titleMedium,
                )
            }
        }
    }
}

@Composable
private fun SelectionDialog(
    title: String,
    options: List<Pair<String, String>>,
    selected: String,
    onSelect: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column {
                options.forEach { (key, label) ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelect(key) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = selected == key, onClick = { onSelect(key) })
                        Spacer(Modifier.width(12.dp))
                        Text(label, style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.btn_cancel))
            }
        },
    )
}

@Composable
private fun UploadConsentRow(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.settings_upload_consent),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = stringResource(R.string.settings_upload_consent_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange,
            )
        }
    }
}

@Composable
private fun CrashReportingRow(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.settings_crash_reporting),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = stringResource(R.string.settings_crash_reporting_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange,
            )
        }
    }
}

@Composable
private fun LocationRow(
    enabled: Boolean,
    onEnabledChange: (Boolean) -> Unit,
) {
    val context = LocalContext.current
    val hasPermission = remember(enabled) {
        ContextCompat.checkSelfPermission(
            context, Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            onEnabledChange(true)
        } else {
            // Permission denied — keep toggle off
            onEnabledChange(false)
        }
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.settings_location_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = stringResource(R.string.settings_location_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
                val statusText: String
                val statusColor: Color
                when {
                    !enabled -> {
                        statusText = stringResource(R.string.settings_location_status_disabled)
                        statusColor = SapiSehatColors.TextSecondary
                    }
                    hasPermission -> {
                        statusText = stringResource(R.string.settings_location_status_granted)
                        statusColor = SapiSehatColors.Healthy
                    }
                    else -> {
                        statusText = stringResource(R.string.settings_location_status_denied)
                        statusColor = SapiSehatColors.WarningLSD
                    }
                }
                Text(
                    text = statusText,
                    style = MaterialTheme.typography.bodySmall,
                    color = statusColor,
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = enabled,
                onCheckedChange = { newValue ->
                    if (newValue && !hasPermission) {
                        // Request permission before enabling
                        permissionLauncher.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                    } else {
                        onEnabledChange(newValue)
                    }
                },
            )
        }
    }
}

@Composable
private fun ManualLocationRow(viewModel: SettingsViewModel) {
    val manualLat by viewModel.manualLatitude.collectAsStateWithLifecycle()
    val manualLng by viewModel.manualLongitude.collectAsStateWithLifecycle()

    var showDialog by remember { mutableStateOf(false) }
    val currentDisplay = if (manualLat != null && manualLng != null) {
        "$manualLat, $manualLng"
    } else {
        null
    }

    PreferenceRow(
        title = stringResource(R.string.settings_location_manual_title),
        value = currentDisplay ?: stringResource(R.string.settings_location_manual_desc),
        onClick = { showDialog = true },
    )

    if (showDialog) {
        var editLat by remember { mutableStateOf(manualLat ?: "") }
        var editLng by remember { mutableStateOf(manualLng ?: "") }

        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text(stringResource(R.string.settings_location_manual_title)) },
            text = {
                Column {
                    OutlinedTextField(
                        value = editLat,
                        onValueChange = { editLat = it },
                        label = { Text(stringResource(R.string.settings_location_lat_hint)) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = editLng,
                        onValueChange = { editLng = it },
                        label = { Text(stringResource(R.string.settings_location_lng_hint)) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                    )
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val lat = editLat.trim().takeIf { it.isNotEmpty() }
                    val lng = editLng.trim().takeIf { it.isNotEmpty() }
                    viewModel.setManualLocation(lat, lng)
                    showDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    viewModel.setManualLocation(null, null)
                    showDialog = false
                }) {
                    Text(stringResource(R.string.btn_delete))
                }
            },
        )
    }
}

@Composable
private fun languageDisplayName(code: String): String = when (code) {
    "id" -> stringResource(R.string.settings_language_id)
    "en" -> stringResource(R.string.settings_language_en)
    else -> stringResource(R.string.settings_language_system)
}

@Composable
private fun textSizeDisplayName(code: String): String = when (code) {
    "small" -> stringResource(R.string.settings_text_size_small)
    "medium" -> stringResource(R.string.settings_text_size_medium)
    "large" -> stringResource(R.string.settings_text_size_large)
    else -> stringResource(R.string.settings_text_size_system)
}
