package com.example.naturalgasprop.ui.main

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.ui.text.TextStyle
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.naturalgasprop.theme.CyanPrimary
import com.example.naturalgasprop.theme.ErrorRed
import com.example.naturalgasprop.theme.SuccessGreen
import com.example.naturalgasprop.theme.WarningOrange

@Composable
fun CompositionScreen(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }
    var showSuggestions by remember { mutableStateOf(false) }

    val filteredSuggestions = remember(searchQuery) {
        if (searchQuery.isEmpty()) {
            emptyList()
        } else {
            viewModel.availableComponents.filter {
                it.contains(searchQuery, ignoreCase = true) &&
                state.components.none { comp -> comp.name.lowercase() == it.lowercase() }
            }.take(5)
        }
    }

    val totalColor = if (Math.abs(state.totalFraction - 100.0) < 1e-3) SuccessGreen else ErrorRed
    val isDark = isSystemInDarkTheme()

    val glassBg = if (isDark) Color(0xFF1E293B).copy(alpha = 0.8f) else Color(0xFFF1F5F9).copy(alpha = 0.8f)
    val dividerColor = if (isDark) Color(0xFF334155) else Color(0xFFE2E8F0)

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(8.dp)
    ) {
        // Search and Add Area
        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = glassBg),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, dividerColor, RoundedCornerShape(16.dp))
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                Text(
                    text = "Bileşen Ekle",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(6.dp))

                Box(modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = {
                            searchQuery = it
                            showSuggestions = it.isNotEmpty()
                        },
                        label = { Text("Gaz Ara (örn. Methane, CO2)", fontSize = 12.sp) },
                        leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, modifier = Modifier.size(20.dp)) },
                        trailingIcon = {
                            if (searchQuery.isNotEmpty()) {
                                IconButton(onClick = { searchQuery = ""; showSuggestions = false }) {
                                    Icon(Icons.Default.Clear, contentDescription = null, modifier = Modifier.size(20.dp))
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth().height(52.dp),
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = CyanPrimary,
                            unfocusedBorderColor = dividerColor
                        ),
                        textStyle = TextStyle(fontSize = 13.sp)
                    )

                    // Suggestion dropdown list overlay
                    if (showSuggestions && filteredSuggestions.isNotEmpty()) {
                        Card(
                            elevation = CardDefaults.cardElevation(8.dp),
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = if (isDark) Color(0xFF1E293B) else Color(0xFFFFFFFF)
                            ),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 58.dp)
                                .border(
                                    1.dp,
                                    if (isDark) Color(0xFF334155) else Color(0xFFCBD5E1),
                                    RoundedCornerShape(12.dp)
                                )
                                .heightIn(max = 200.dp)
                        ) {
                            LazyColumn {
                                items(filteredSuggestions) { suggestion ->
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clickable {
                                                viewModel.addOrUpdateComponent(suggestion, 0.0)
                                                searchQuery = ""
                                                showSuggestions = false
                                            }
                                            .padding(horizontal = 14.dp, vertical = 10.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Text(
                                            text = suggestion,
                                            fontSize = 13.sp,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                        Icon(
                                            Icons.Default.Add,
                                            contentDescription = "Add",
                                            tint = CyanPrimary,
                                            modifier = Modifier.size(16.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Mixture components list
        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = glassBg),
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .border(1.dp, dividerColor, RoundedCornerShape(16.dp))
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(12.dp)
            ) {
                Text(
                    text = "Mevcut Karışım Bileşenleri",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(6.dp))

                if (state.components.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Karışım boş. Yukarıdan aratarak gaz bileşenleri ekleyin.",
                            color = labelColor(isDark),
                            fontSize = 13.sp
                        )
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                        verticalArrangement = Arrangement.Top
                    ) {
                        items(state.components, key = { it.name }) { component ->
                            ComponentRow(
                                component = component,
                                onFractionChange = { newFrac ->
                                    viewModel.addOrUpdateComponent(component.name, newFrac)
                                },
                                onDelete = {
                                    viewModel.removeComponent(component.name)
                                },
                                isDark = isDark,
                                dividerColor = dividerColor
                            )
                        }
                    }
                }

                // Live total indicator & helper buttons
                Spacer(modifier = Modifier.height(6.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Toplam Yüzde",
                            fontSize = 11.sp,
                            color = labelColor(isDark)
                        )
                        Text(
                            text = "${String.format("%.4f", state.totalFraction)} %",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = totalColor
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        OutlinedButton(
                            onClick = { viewModel.clearMixture() },
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                            border = ButtonDefaults.outlinedButtonBorder(true),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = MaterialTheme.colorScheme.onSurface
                            ),
                            modifier = Modifier.height(36.dp)
                        ) {
                            Text("Temizle", fontSize = 11.sp)
                        }

                        OutlinedButton(
                            onClick = { viewModel.resetToDefaultMixture() },
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = MaterialTheme.colorScheme.onSurface
                            ),
                            modifier = Modifier.height(36.dp)
                        ) {
                            Text("Sıfırla", fontSize = 11.sp)
                        }

                        Button(
                            onClick = { viewModel.normalizeMixture() },
                            enabled = state.totalFraction > 0.0,
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = CyanPrimary,
                                contentColor = Color.White
                            ),
                            modifier = Modifier.height(36.dp)
                        ) {
                            Text("Normalleştir", fontSize = 11.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ComponentRow(
    component: GasComponentInput,
    onFractionChange: (Double) -> Unit,
    onDelete: () -> Unit,
    isDark: Boolean,
    dividerColor: Color
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text = component.name,
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.width(76.dp),
                maxLines = 1
            )

            Slider(
                value = component.fraction.toFloat(),
                onValueChange = { onFractionChange(it.toDouble()) },
                valueRange = 0f..100f,
                colors = SliderDefaults.colors(
                    activeTrackColor = CyanPrimary,
                    inactiveTrackColor = dividerColor,
                    thumbColor = CyanPrimary
                ),
                modifier = Modifier.weight(1f)
            )

            var textValue by remember(component.fraction) {
                mutableStateOf(String.format("%.4f", component.fraction))
            }

            OutlinedTextField(
                value = textValue,
                onValueChange = {
                    textValue = it
                    val parsed = it.toDoubleOrNull()
                    if (parsed != null && parsed >= 0.0 && parsed <= 100.0) {
                        onFractionChange(parsed)
                    }
                },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier
                    .width(75.dp)
                    .height(40.dp),
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyanPrimary,
                    unfocusedBorderColor = dividerColor
                ),
                textStyle = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface),
                singleLine = true
            )

            Text("%", fontSize = 12.sp, fontWeight = FontWeight.Bold)

            IconButton(
                onClick = onDelete,
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    Icons.Default.Delete,
                    contentDescription = "Delete",
                    tint = ErrorRed.copy(alpha = 0.8f),
                    modifier = Modifier.size(18.dp)
                )
            }
        }
        Spacer(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(dividerColor.copy(alpha = 0.2f))
        )
    }
}

private fun labelColor(isDark: Boolean) = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
