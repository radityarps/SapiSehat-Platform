package com.sapisehat.app.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import org.json.JSONObject
import com.sapisehat.app.data.repository.DetectionRepository
import com.sapisehat.app.domain.model.DetectionResult
import javax.inject.Inject

data class HistoryItemUi(
    val id: Long,
    val imagePath: String?,
    val label: String,
    val displayLabel: String,
    val confidence: Float,
    val mode: String,
    val timestamp: Long,
    val allScoresJson: String,
    val title: String?,
    val description: String?,
    val imageSource: String?,
    val appVersion: String?,
    val consentStatus: String,
)

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val repository: DetectionRepository
) : ViewModel() {

    val classFilter = MutableStateFlow<String?>(null)
    val modeFilter = MutableStateFlow<String?>(null)

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    private val _lastDeletedId = MutableStateFlow<Long?>(null)
    val lastDeletedId: StateFlow<Long?> = _lastDeletedId

    @OptIn(ExperimentalCoroutinesApi::class)
    val filteredRows: StateFlow<List<HistoryItemUi>> = combine(
        classFilter, modeFilter
    ) { classF, modeF -> classF to modeF }
        .flatMapLatest { (classF, modeF) ->
            repository.observeHistoryFiltered(classF, modeF)
        }
        .map { rows -> rows.map { it.toHistoryItemUi() } }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun setClassFilter(label: String?) {
        classFilter.value = label
    }

    fun setModeFilter(label: String?) {
        modeFilter.value = label
    }

    fun deleteItem(id: Long) {
        viewModelScope.launch {
            repository.softDelete(id)
            _lastDeletedId.value = id
        }
    }

    fun undoDelete() {
        viewModelScope.launch {
            _lastDeletedId.value?.let { id ->
                repository.restoreDeleted(id)
                _lastDeletedId.value = null
            }
        }
    }

    fun clearLastDeleted() {
        _lastDeletedId.value = null
    }

    fun deleteAll() {
        viewModelScope.launch {
            repository.deleteAll()
        }
    }

    fun clearError() {
        _error.value = null
    }

    private fun DetectionResult.toHistoryItemUi(): HistoryItemUi {
        val json = JSONObject()
        allScores.forEach { (key, value) ->
            json.put(key, value.toDouble())
        }
        return HistoryItemUi(
            id = id,
            imagePath = imagePath,
            label = label,
            displayLabel = displayLabel,
            confidence = confidence,
            mode = inferenceMode.name,
            timestamp = timestamp,
            allScoresJson = json.toString(),
            title = title,
            description = description,
            imageSource = imageSource?.name,
            appVersion = appVersion,
            consentStatus = consentStatus.name,
        )
    }
}
