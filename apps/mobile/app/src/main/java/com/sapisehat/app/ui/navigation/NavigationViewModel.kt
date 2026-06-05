package com.sapisehat.app.ui.navigation

import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject

@HiltViewModel
class NavigationViewModel @Inject constructor() : ViewModel() {
    // Tracks the detection ID to update on retake
    private val _updateDetectionId = MutableStateFlow<Long?>(null)
    val updateDetectionId: StateFlow<Long?> = _updateDetectionId.asStateFlow()

    // Flag to trigger navigation to camera on retake
    private val _shouldNavigateToCamera = MutableStateFlow(false)
    val shouldNavigateToCamera: StateFlow<Boolean> = _shouldNavigateToCamera.asStateFlow()

    fun setUpdateDetectionId(id: Long?) {
        _updateDetectionId.value = id
    }

    fun clearUpdateDetectionId() {
        _updateDetectionId.value = null
    }

    fun triggerNavigateToCamera() {
        _shouldNavigateToCamera.value = true
    }

    fun clearNavigateToCamera() {
        _shouldNavigateToCamera.value = false
    }
}
