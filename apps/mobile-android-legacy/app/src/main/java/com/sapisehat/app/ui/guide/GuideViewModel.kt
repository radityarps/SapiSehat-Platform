package com.sapisehat.app.ui.guide

import android.content.Context
import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.SharingStarted
import javax.inject.Inject

@HiltViewModel
class GuideViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
) : ViewModel() {

    private val _articles = MutableStateFlow<List<GuideArticle>>(emptyList())

    val searchQuery = MutableStateFlow("")
    val selectedCategory = MutableStateFlow<GuideCategory?>(null)

    val filteredArticles: StateFlow<List<GuideArticle>> = combine(
        _articles,
        searchQuery,
        selectedCategory,
    ) { articles, query, category ->
        articles.filter { article ->
            val matchesQuery = query.isBlank() ||
                article.title.contains(query, ignoreCase = true) ||
                article.summary.contains(query, ignoreCase = true) ||
                article.body.contains(query, ignoreCase = true)
            val matchesCategory = category == null || article.category == category
            matchesQuery && matchesCategory
        }
    }.stateIn(
        scope = kotlinx.coroutines.MainScope(),
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = emptyList(),
    )

    /**
     * Called from the composable with the Activity context (locale-aware).
     * This ensures guide articles use the correct language.
     */
    fun loadArticles(activityContext: Context) {
        _articles.value = GuideDataSource.articles(activityContext)
    }

    fun onSearchQueryChange(query: String) {
        searchQuery.value = query
    }

    fun onCategoryFilter(category: GuideCategory?) {
        selectedCategory.value = category
    }
}
