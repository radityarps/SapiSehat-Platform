package com.sapisehat.app.ui.result

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.launch
import com.sapisehat.app.data.repository.DetectionRepository
import com.sapisehat.app.domain.model.DetectionResult
import com.sapisehat.app.report.PdfReportGenerator
import javax.inject.Inject

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class ResultViewModel @Inject constructor(
    private val repository: DetectionRepository,
    private val pdfReportGenerator: PdfReportGenerator,
) : ViewModel() {

    private val _noteSaved = MutableStateFlow(false)
    val noteSaved: StateFlow<Boolean> = _noteSaved.asStateFlow()

    private val _pdfPath = MutableStateFlow<String?>(null)
    val pdfPath: StateFlow<String?> = _pdfPath.asStateFlow()

    private val _pdfError = MutableStateFlow(false)
    val pdfError: StateFlow<Boolean> = _pdfError.asStateFlow()

    private val selectedDetectionId = MutableStateFlow<Long?>(null)

    val selectedDetection: StateFlow<DetectionResult?> = selectedDetectionId
        .flatMapLatest { id ->
            if (id == null || id <= 0L) flowOf(null) else repository.observeDetection(id)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun setDetectionId(detectionId: Long?) {
        selectedDetectionId.value = detectionId?.takeIf { it > 0L }
    }

    fun saveNote(detectionId: Long, title: String?, description: String?) {
        viewModelScope.launch {
            runCatching {
                repository.updateNote(
                    id = detectionId,
                    title = title?.trim()?.takeIf { it.isNotEmpty() },
                    description = description?.trim()?.takeIf { it.isNotEmpty() },
                )
            }
            _noteSaved.value = true
        }
    }

    fun consumeNoteSaved() {
        _noteSaved.value = false
    }

    fun exportPdf(result: DetectionResult) {
        viewModelScope.launch {
            val path = pdfReportGenerator.generate(result)
            if (path != null) {
                _pdfPath.value = path
                if (result.id > 0) {
                    runCatching { repository.updatePdfCachePath(result.id, path) }
                }
            } else {
                _pdfError.value = true
            }
        }
    }

    fun consumePdfPath() {
        _pdfPath.value = null
    }

    fun consumePdfError() {
        _pdfError.value = false
    }
}
