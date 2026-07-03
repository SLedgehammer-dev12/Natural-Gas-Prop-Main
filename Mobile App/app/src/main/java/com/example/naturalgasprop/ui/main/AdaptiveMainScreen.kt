package com.example.naturalgasprop.ui.main

import androidx.activity.ComponentActivity
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.window.layout.FoldingFeature
import androidx.window.layout.WindowInfoTracker
import com.example.naturalgasprop.theme.CyanPrimary
import com.example.naturalgasprop.theme.DarkBackground
import com.example.naturalgasprop.theme.DarkSurface
import com.example.naturalgasprop.theme.LightBackground
import com.example.naturalgasprop.theme.LightSurface

@Composable
fun AdaptiveMainScreen(
    viewModel: CalculatorViewModel,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val activity = context as? ComponentActivity

    val configuration = LocalConfiguration.current
    val screenWidth = configuration.screenWidthDp

    val isDark = isSystemInDarkTheme()
    val bg = if (isDark) DarkBackground else LightBackground

    // 1. Observe Folding state from Jetpack WindowManager
    if (activity != null) {
        LaunchedEffect(activity) {
            WindowInfoTracker.getOrCreate(activity)
                .windowLayoutInfo(activity)
                .collect { layoutInfo ->
                    var isTabletop = false
                    var isBook = false
                    var hingePos = -1
                    
                    val foldingFeature = layoutInfo.displayFeatures
                        .filterIsInstance<FoldingFeature>()
                        .firstOrNull()
                    
                    if (foldingFeature != null) {
                        // Tabletop mode is when foldable device is folded horizontally like a laptop
                        if (foldingFeature.state == FoldingFeature.State.HALF_OPENED) {
                            if (foldingFeature.orientation == FoldingFeature.Orientation.HORIZONTAL) {
                                isTabletop = true
                            } else {
                                isBook = true
                            }
                        }
                        hingePos = if (foldingFeature.orientation == FoldingFeature.Orientation.HORIZONTAL) {
                            foldingFeature.bounds.top
                        } else {
                            foldingFeature.bounds.left
                        }
                    }
                    viewModel.updateFoldableState(isTabletop, isBook, hingePos)
                }
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(bg)
    ) {
        when {
            // A. Expanded Tablet Layout (screenWidth >= 840dp)
            screenWidth >= 840 -> {
                TabletExpandedLayout(state = state, viewModel = viewModel)
            }
            
            // B. Tabletop Foldable Layout (Split screen top-bottom halves)
            state.isTabletopMode -> {
                TabletopFoldableLayout(state = state, viewModel = viewModel)
            }
            
            // C. Medium Landscape or Book Mode Layout (screenWidth >= 600dp or Book posture)
            screenWidth >= 600 || state.isBookMode -> {
                MediumSplitLayout(state = state, viewModel = viewModel)
            }
            
            // D. Compact Layout (Standard portrait phones)
            else -> {
                CompactNavigationLayout(state = state, viewModel = viewModel)
            }
        }
    }
}

// 1. Compact Portrait Phones (Bottom tabs layout)
@Composable
fun CompactNavigationLayout(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val isDark = isSystemInDarkTheme()
    val navBarColor = if (isDark) DarkSurface else LightSurface

    Scaffold(
        bottomBar = {
            NavigationBar(
                containerColor = navBarColor,
                tonalElevation = 8.dp
            ) {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Icon(Icons.Default.List, contentDescription = null) },
                    label = { Text("Gaz Karışımı", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = CyanPrimary,
                        selectedTextColor = CyanPrimary,
                        indicatorColor = CyanPrimary.copy(alpha = 0.12f)
                    )
                )

                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Icon(Icons.Default.Settings, contentDescription = null) },
                    label = { Text("Parametreler", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = CyanPrimary,
                        selectedTextColor = CyanPrimary,
                        indicatorColor = CyanPrimary.copy(alpha = 0.12f)
                    )
                )

                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    icon = { Icon(Icons.Default.PlayArrow, contentDescription = null) },
                    label = { Text("Sonuçlar", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = CyanPrimary,
                        selectedTextColor = CyanPrimary,
                        indicatorColor = CyanPrimary.copy(alpha = 0.12f)
                    )
                )
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            when (selectedTab) {
                0 -> CompositionScreen(state = state, viewModel = viewModel)
                1 -> ParametersScreen(state = state, viewModel = viewModel)
                2 -> ResultsScreen(state = state, viewModel = viewModel)
            }
        }
    }
}

// 2. Medium Split Layout (Two equal columns for land phones and open foldables)
@Composable
fun MediumSplitLayout(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel
) {
    Row(modifier = Modifier.fillMaxSize()) {
        // Left pane: Input Forms (Scrollable layout of Composition and Parameters)
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight()
                .padding(8.dp)
        ) {
            Box(modifier = Modifier.weight(1.3f)) {
                CompositionScreen(state = state, viewModel = viewModel)
            }
            Box(modifier = Modifier.weight(1f)) {
                ParametersScreen(state = state, viewModel = viewModel)
            }
        }

        // Right pane: Results
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight()
        ) {
            ResultsScreen(state = state, viewModel = viewModel)
        }
    }
}

// 3. Tabletop Foldable Layout (Folded horizontally like laptop, top=results, bottom=inputs)
@Composable
fun TabletopFoldableLayout(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel
) {
    Column(modifier = Modifier.fillMaxSize()) {
        // Top half: Display results and Canvas plot
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
        ) {
            ResultsScreen(state = state, viewModel = viewModel)
        }

        // Bottom half: Input form
        Row(
            modifier = Modifier
                .weight(1.1f)
                .fillMaxWidth()
                .padding(8.dp)
        ) {
            Box(modifier = Modifier.weight(1.2f)) {
                CompositionScreen(state = state, viewModel = viewModel)
            }
            Box(modifier = Modifier.weight(1f)) {
                ParametersScreen(state = state, viewModel = viewModel)
            }
        }
    }
}

// 4. Tablet Expanded Layout (3 columns: comp, params, results)
@Composable
fun TabletExpandedLayout(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel
) {
    Row(modifier = Modifier.fillMaxSize()) {
        // Column 1: Gas mixture composition
        Box(
            modifier = Modifier
                .weight(0.30f)
                .fillMaxHeight()
        ) {
            CompositionScreen(state = state, viewModel = viewModel)
        }

        // Column 2: Parameters Form
        Box(
            modifier = Modifier
                .weight(0.30f)
                .fillMaxHeight()
        ) {
            ParametersScreen(state = state, viewModel = viewModel)
        }

        // Column 3: Results & Graph details
        Box(
            modifier = Modifier
                .weight(0.40f)
                .fillMaxHeight()
        ) {
            ResultsScreen(state = state, viewModel = viewModel)
        }
    }
}
