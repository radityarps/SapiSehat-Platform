package com.sapisehat.app.ui.navigation

import android.net.Uri
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.sapisehat.app.R
import com.sapisehat.app.ui.theme.SapiSehatColors
import com.sapisehat.app.ui.theme.textSecondary
import com.sapisehat.app.ui.about.AboutRoute
import com.sapisehat.app.ui.camera.CameraRoute
import com.sapisehat.app.ui.guide.GuideDetailRoute
import com.sapisehat.app.ui.guide.GuideRoute
import com.sapisehat.app.ui.history.HistoryRoute
import com.sapisehat.app.ui.onboarding.OnboardingRoute
import com.sapisehat.app.ui.result.ResultRoute
import com.sapisehat.app.ui.settings.SettingsRoute
import com.sapisehat.app.ui.splash.SplashRoute

object Routes {
    const val Splash = "splash"
    const val Onboarding = "onboarding"
    const val Main = "main"
    const val Camera = "camera"
    const val Guide = "guide"
    const val History = "history"
    const val About = "about"
    const val Settings = "settings"
    const val Result = "result?label={label}&confidence={confidence}&mode={mode}&allScoresJson={allScoresJson}&imageRef={imageRef}&timestamp={timestamp}&detectionId={detectionId}&fromHistory={fromHistory}"
    const val GuideDetail = "guide_detail/{articleId}"

    fun result(
        label: String,
        confidence: Float,
        mode: String,
        scoresJson: String,
        imageRef: String,
        timestamp: Long,
        detectionId: Long? = null,
        fromHistory: Boolean = false,
    ): String {
        return buildString {
            append("result")
            append("?label=${Uri.encode(label)}")
            append("&confidence=$confidence")
            append("&mode=${Uri.encode(mode)}")
            append("&allScoresJson=${Uri.encode(scoresJson)}")
            append("&imageRef=${Uri.encode(imageRef)}")
            append("&timestamp=$timestamp")
            append("&detectionId=${detectionId ?: -1}")
            append("&fromHistory=$fromHistory")
        }
    }

    fun guideDetail(articleId: String): String = "guide_detail/$articleId"
}

data class TabItem(
    val route: String,
    val icon: ImageVector,
    val labelRes: Int,
)

val tabs = listOf(
    TabItem(Routes.Camera, Icons.Filled.CameraAlt, R.string.tab_periksa),
    TabItem(Routes.History, Icons.Filled.History, R.string.tab_riwayat),
    TabItem(Routes.Guide, Icons.Filled.MenuBook, R.string.tab_panduan),
    TabItem(Routes.About, Icons.Filled.Person, R.string.tab_lainnya),
)

@Composable
fun SapiSehatNavHost() {
    val rootNavController = rememberNavController()
    val navigationViewModel: NavigationViewModel = hiltViewModel()

    NavHost(
        navController = rootNavController,
        startDestination = Routes.Splash
    ) {
        composable(Routes.Splash) {
            SplashRoute(
                onFinish = { hasOnboarded ->
                    val dest = if (hasOnboarded) Routes.Main else Routes.Onboarding
                    rootNavController.navigate(dest) {
                        popUpTo(Routes.Splash) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.Onboarding) {
            OnboardingRoute(
                onFinish = {
                    rootNavController.navigate(Routes.Main) {
                        popUpTo(Routes.Onboarding) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.Main) {
            MainTabScreen(rootNavController = rootNavController, navigationViewModel = navigationViewModel)
        }
        composable(
            route = Routes.Result,
            arguments = listOf(
                navArgument("label") { type = NavType.StringType },
                navArgument("confidence") { type = NavType.StringType },
                navArgument("mode") { type = NavType.StringType },
                navArgument("allScoresJson") { type = NavType.StringType },
                navArgument("imageRef") {
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("timestamp") {
                    type = NavType.LongType
                    defaultValue = 0L
                },
                navArgument("detectionId") {
                    type = NavType.LongType
                    defaultValue = -1L
                },
                navArgument("fromHistory") {
                    type = NavType.BoolType
                    defaultValue = false
                },
            )
        ) { backStackEntry ->
            val label = backStackEntry.arguments?.getString("label") ?: "UNKNOWN"
            val confidence = backStackEntry.arguments?.getString("confidence")?.toFloatOrNull() ?: 0f
            val mode = backStackEntry.arguments?.getString("mode") ?: "OFFLINE"
            val allScoresJson = backStackEntry.arguments?.getString("allScoresJson") ?: "{}"
            val imageRef = backStackEntry.arguments?.getString("imageRef") ?: ""
            val timestamp = backStackEntry.arguments?.getLong("timestamp") ?: 0L
            val detectionId = backStackEntry.arguments?.getLong("detectionId") ?: -1L
            val fromHistory = backStackEntry.arguments?.getBoolean("fromHistory") ?: false
            ResultRoute(
                label = label,
                confidence = confidence,
                mode = mode,
                allScoresJson = allScoresJson,
                imageRef = imageRef,
                scanTimestamp = timestamp,
                detectionId = if (detectionId >= 0) detectionId else null,
                fromHistory = fromHistory,
                appVersion = com.sapisehat.app.BuildConfig.VERSION_NAME,
                navigationViewModel = navigationViewModel,
                onBack = { rootNavController.popBackStack() },
                onRetake = {
                    // If this is an update scenario (viewing existing scan), set updateDetectionId
                    if (detectionId >= 0) {
                        navigationViewModel.setUpdateDetectionId(detectionId)
                    }
                    rootNavController.popBackStack()
                    navigationViewModel.triggerNavigateToCamera()
                },
                onNavigateToGuide = { articleId ->
                    rootNavController.navigate(Routes.GuideDetail.replace("{articleId}", articleId))
                },
            )
        }
        composable(Routes.About) {
            AboutRoute(
                onBack = { rootNavController.popBackStack() },
                onNavigateToSettings = { rootNavController.navigate(Routes.Settings) },
            )
        }
        composable(Routes.Settings) {
            SettingsRoute(onBack = { rootNavController.popBackStack() })
        }
        composable(
            route = Routes.GuideDetail,
            arguments = listOf(navArgument("articleId") { type = NavType.StringType }),
        ) { backStackEntry ->
            val articleId = backStackEntry.arguments?.getString("articleId") ?: ""
            GuideDetailRoute(
                articleId = articleId,
                onBack = { rootNavController.popBackStack() },
            )
        }
    }
}

@Composable
fun MainTabScreen(rootNavController: NavHostController, navigationViewModel: NavigationViewModel) {
    val tabNavController = rememberNavController()
    val shouldNavigateToCamera by navigationViewModel.shouldNavigateToCamera.collectAsStateWithLifecycle()

    // Watch for retake navigation trigger
    LaunchedEffect(shouldNavigateToCamera) {
        if (shouldNavigateToCamera) {
            tabNavController.navigate(Routes.Camera) {
                popUpTo(tabNavController.graph.startDestinationId) {
                    inclusive = false
                }
                launchSingleTop = false
            }
            navigationViewModel.clearNavigateToCamera()
        }
    }

    val navBackStackEntry by tabNavController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val rootBackStackEntry by rootNavController.currentBackStackEntryAsState()
    val isOnRootScreen = rootBackStackEntry?.destination?.route in listOf(
        Routes.Settings,
        Routes.GuideDetail,
    )

    Scaffold(
        bottomBar = {
            NavigationBar(
                tonalElevation = 0.dp,
                containerColor = SapiSehatColors.Surface,
            ) {
                tabs.forEach { tab ->
                    val selected = !isOnRootScreen && currentRoute == tab.route
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            tabNavController.navigate(tab.route) {
                                popUpTo(tabNavController.graph.startDestinationId) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = stringResource(tab.labelRes)) },
                        label = {
                            Text(
                                text = stringResource(tab.labelRes),
                                style = MaterialTheme.typography.labelSmall,
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = SapiSehatColors.Primary,
                            selectedTextColor = SapiSehatColors.Primary,
                            unselectedIconColor = SapiSehatColors.TextSecondary,
                            unselectedTextColor = SapiSehatColors.TextSecondary,
                            indicatorColor = SapiSehatColors.PrimaryContainer,
                        ),
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = tabNavController,
            startDestination = Routes.Camera,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(Routes.Camera) {
                CameraRoute(
                    navigationViewModel = navigationViewModel,
                    onShowResult = { label, confidence, mode, scoresJson, imageRef, timestamp, detectionId ->
                        rootNavController.navigate(
                            Routes.result(label, confidence, mode, scoresJson, imageRef, timestamp, detectionId)
                        )
                    },
                    onOpenHistory = {
                        tabNavController.navigate(Routes.History) {
                            popUpTo(tabNavController.graph.startDestinationId) {
                                saveState = true
                            }
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                )
            }
            composable(Routes.History) {
                HistoryRoute(
                    onOpenDetail = { label, confidence, mode, scoresJson, imageRef, timestamp, detectionId ->
                        rootNavController.navigate(
                            Routes.result(label, confidence, mode, scoresJson, imageRef, timestamp, detectionId, fromHistory = true)
                        )
                    },
                )
            }
            composable(Routes.Guide) {
                GuideRoute(
                    onOpenArticle = { articleId ->
                        rootNavController.navigate(Routes.guideDetail(articleId))
                    },
                )
            }
            composable(Routes.About) {
                AboutRoute(
                    onBack = { tabNavController.popBackStack() },
                    onNavigateToSettings = { rootNavController.navigate(Routes.Settings) },
                )
            }
        }
    }
}
