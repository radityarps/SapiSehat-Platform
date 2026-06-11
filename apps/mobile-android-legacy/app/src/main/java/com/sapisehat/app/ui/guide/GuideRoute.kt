package com.sapisehat.app.ui.guide

import android.app.Activity
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.core.graphics.ColorUtils
import androidx.core.view.WindowCompat
import androidx.compose.ui.res.stringResource
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GuideRoute(
    onOpenArticle: (articleId: String) -> Unit,
    viewModel: GuideViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    // Load articles with the Activity context so strings resolve to the user's preferred locale
    androidx.compose.runtime.LaunchedEffect(context) {
        viewModel.loadArticles(context)
    }

    val searchQuery by viewModel.searchQuery.collectAsStateWithLifecycle()
    val selectedCategory by viewModel.selectedCategory.collectAsStateWithLifecycle()
    val articles by viewModel.filteredArticles.collectAsStateWithLifecycle()

    var searchVisible by remember { mutableStateOf(false) }
    var filterVisible by remember { mutableStateOf(false) }
    val searchFocusRequester = remember { FocusRequester() }
    val view = LocalView.current
    val statusBarColorArgb = MaterialTheme.colorScheme.surface.toArgb()
    val isLightStatusBar = ColorUtils.calculateLuminance(statusBarColorArgb) > 0.5

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = statusBarColorArgb
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = isLightStatusBar
        }
    }

    Scaffold(
        topBar = {
            Column(
                modifier = Modifier
                    .background(MaterialTheme.colorScheme.surface),
            ) {
                TopAppBar(
                    title = {
                        Text(
                            text = stringResource(R.string.guide_title),
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            color = SapiSehatColors.TextPrimary,
                        )
                    },
                    actions = {
                        // Search button — highlighted if active
                        IconButton(onClick = {
                            searchVisible = !searchVisible
                            if (!searchVisible) viewModel.onSearchQueryChange("")
                        }) {
                            Icon(
                                Icons.Filled.Search,
                                contentDescription = stringResource(R.string.guide_action_search),
                                tint = if (searchVisible || searchQuery.isNotEmpty())
                                    MaterialTheme.colorScheme.primary
                                else
                                    SapiSehatColors.TextSecondary,
                            )
                        }
                        // Filter button — highlighted if a filter is active
                        IconButton(onClick = { filterVisible = !filterVisible }) {
                            Icon(
                                Icons.Filled.FilterList,
                                contentDescription = stringResource(R.string.guide_action_filter),
                                tint = if (filterVisible || selectedCategory != null)
                                    MaterialTheme.colorScheme.primary
                                else
                                    SapiSehatColors.TextSecondary,
                            )
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                    windowInsets = TopAppBarDefaults.windowInsets.only(WindowInsetsSides.Horizontal),
                )

                // Search bar — slides in/out below TopAppBar
                AnimatedVisibility(
                    visible = searchVisible,
                    enter = expandVertically(),
                    exit = shrinkVertically(),
                ) {
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = viewModel::onSearchQueryChange,
                        placeholder = {
                            Text(
                                stringResource(R.string.guide_search_placeholder),
                                color = SapiSehatColors.TextSecondary,
                            )
                        },
                        leadingIcon = {
                            Icon(Icons.Filled.Search, contentDescription = null, tint = SapiSehatColors.TextSecondary)
                        },
                        trailingIcon = {
                            if (searchQuery.isNotEmpty()) {
                                IconButton(onClick = { viewModel.onSearchQueryChange("") }) {
                                    Icon(
                                        Icons.Filled.Clear,
                                        contentDescription = stringResource(R.string.guide_action_clear),
                                        tint = SapiSehatColors.TextSecondary,
                                    )
                                }
                            }
                        },
                        singleLine = true,
                        shape = RoundedCornerShape(12.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = SapiSehatColors.Outline,
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                            .focusRequester(searchFocusRequester),
                    )
                }

                // Filter chips — slides in/out below search bar
                AnimatedVisibility(
                    visible = filterVisible,
                    enter = expandVertically(),
                    exit = shrinkVertically(),
                ) {
                    LazyRow(
                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        item {
                            FilterChip(
                                selected = selectedCategory == null,
                                onClick = { viewModel.onCategoryFilter(null) },
                                label = { Text(stringResource(R.string.history_filter_all)) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = MaterialTheme.colorScheme.primary,
                                    selectedLabelColor = MaterialTheme.colorScheme.onPrimary,
                                ),
                            )
                        }
                        items(GuideCategory.entries) { category ->
                            FilterChip(
                                selected = selectedCategory == category,
                                onClick = { viewModel.onCategoryFilter(category) },
                                label = { Text(stringResource(category.titleRes)) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = category.color,
                                    selectedLabelColor = Color.White,
                                ),
                            )
                        }
                    }
                }
            }
        },
    ) { innerPadding ->
        if (articles.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(R.string.guide_empty_not_found),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiSehatColors.TextSecondary,
                )
            }
        } else {
            LazyColumn(
                contentPadding = PaddingValues(
                    start = 16.dp,
                    end = 16.dp,
                    top = innerPadding.calculateTopPadding() + 8.dp,
                    bottom = innerPadding.calculateBottomPadding() + 8.dp,
                ),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                items(articles, key = { it.id }) { article ->
                    GuideArticleCard(
                        article = article,
                        onClick = { onOpenArticle(article.id) },
                    )
                }
                item { Spacer(Modifier.height(8.dp)) }
            }
        }
    }
}

@Composable
private fun GuideArticleCard(
    article: GuideArticle,
    onClick: () -> Unit,
) {
    Card(
        onClick = onClick,
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier.fillMaxWidth(),
    ) {
        // Colored top banner
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(80.dp)
                .background(article.category.color),
        )

        // Article body
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = article.title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                color = SapiSehatColors.TextPrimary,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = article.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = SapiSehatColors.TextSecondary,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Surface(
                    shape = RoundedCornerShape(999.dp),
                    color = article.category.color.copy(alpha = 0.14f),
                ) {
                    Text(
                        text = stringResource(article.category.titleRes),
                        style = MaterialTheme.typography.labelSmall,
                        color = article.category.color,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
                    )
                }
                Text(
                    text = stringResource(R.string.guide_read_more),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.SemiBold,
                )
            }
        }
    }
}
