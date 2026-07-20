package com.example.naturalgasprop.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.naturalgasprop.theme.CyanPrimary
import com.example.naturalgasprop.theme.ErrorRed
import com.example.naturalgasprop.theme.IndigoSecondary
import com.example.naturalgasprop.theme.WarningOrange

@Composable
fun ParametersScreen(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val isDark = isSystemInDarkTheme()

    val glassBg = if (isDark) Color(0xFF1E293B).copy(alpha = 0.8f) else Color(0xFFF1F5F9).copy(alpha = 0.8f)
    val dividerColor = if (isDark) Color(0xFF334155) else Color(0xFFE2E8F0)

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(8.dp)
            .verticalScroll(scrollState)
    ) {
        // Calculation Error Banner
        AnimatedWarningBanner(state.errorMessage)

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
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = "Hesaplama Parametreleri",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )

                // 1. Temperature field
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Sıcaklık",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        OutlinedTextField(
                            value = state.temperatureStr,
                            onValueChange = { viewModel.updateTemperature(it) },
                            placeholder = { Text("Sıcaklık değeri girin", fontSize = 12.sp) },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                            modifier = Modifier.fillMaxWidth().height(48.dp),
                            shape = RoundedCornerShape(10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = CyanPrimary,
                                unfocusedBorderColor = dividerColor
                            ),
                            textStyle = TextStyle(fontSize = 13.sp),
                            singleLine = true
                        )
                    }

                    UnitSelectorDropdown(
                        selectedUnit = state.temperatureUnit.symbol,
                        units = TemperatureUnit.values().map { it.symbol },
                        onUnitSelected = { symbol ->
                            val unit = TemperatureUnit.values().first { it.symbol == symbol }
                            viewModel.updateTemperatureUnit(unit)
                        },
                        isDark = isDark,
                        dividerColor = dividerColor
                    )
                }

                // 2. Pressure field
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Basınç",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        OutlinedTextField(
                            value = state.pressureStr,
                            onValueChange = { viewModel.updatePressure(it) },
                            placeholder = { Text("Basınç değeri girin", fontSize = 12.sp) },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                            modifier = Modifier.fillMaxWidth().height(48.dp),
                            shape = RoundedCornerShape(10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = CyanPrimary,
                                unfocusedBorderColor = dividerColor
                            ),
                            textStyle = TextStyle(fontSize = 13.sp),
                            singleLine = true
                        )
                    }

                    UnitSelectorDropdown(
                        selectedUnit = state.pressureUnit.symbol,
                        units = PressureUnit.values().map { it.symbol },
                        onUnitSelected = { symbol ->
                            val unit = PressureUnit.values().first { it.symbol == symbol }
                            viewModel.updatePressureUnit(unit)
                        },
                        isDark = isDark,
                        dividerColor = dividerColor
                    )
                }

                // 3. Volume field
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Hacim (Opsiyonel)",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        OutlinedTextField(
                            value = state.volumeStr,
                            onValueChange = { viewModel.updateVolume(it) },
                            placeholder = { Text("Hacim değeri girin", fontSize = 12.sp) },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                            modifier = Modifier.fillMaxWidth().height(48.dp),
                            shape = RoundedCornerShape(10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = CyanPrimary,
                                unfocusedBorderColor = dividerColor
                            ),
                            textStyle = TextStyle(fontSize = 13.sp),
                            singleLine = true
                        )
                    }

                    UnitSelectorDropdown(
                        selectedUnit = state.volumeUnit.symbol,
                        units = VolumeUnit.values().map { it.symbol },
                        onUnitSelected = { symbol ->
                            val unit = VolumeUnit.values().first { it.symbol == symbol }
                            viewModel.updateVolumeUnit(unit)
                        },
                        isDark = isDark,
                        dividerColor = dividerColor
                    )
                }

                // 4. Backend thermodynamic selector
                var backendExpanded by remember { mutableStateOf(false) }
                val currentBackendLabel = viewModel.availableBackends.firstOrNull { it.first == state.selectedBackend }?.second ?: state.selectedBackend

                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = "Termodinamik Eşitlik (EOS)",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                            .background(
                                if (isDark) Color(0xFF0F172A) else Color(0xFFFFFFFF),
                                RoundedCornerShape(10.dp)
                            )
                            .border(1.dp, dividerColor, RoundedCornerShape(10.dp))
                            .clickable { backendExpanded = true }
                            .padding(horizontal = 12.dp),
                        contentAlignment = Alignment.CenterStart
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = currentBackendLabel, fontSize = 13.sp)
                            Icon(Icons.Default.ArrowDropDown, contentDescription = null, modifier = Modifier.size(20.dp))
                        }

                        DropdownMenu(
                            expanded = backendExpanded,
                            onDismissRequest = { backendExpanded = false },
                            modifier = Modifier.fillMaxWidth(0.85f)
                        ) {
                            viewModel.availableBackends.forEach { (id, label) ->
                                DropdownMenuItem(
                                    text = { Text(label) },
                                    onClick = {
                                        viewModel.updateBackend(id)
                                        backendExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                // 5. Standard reference conditions selector
                var stdCondExpanded by remember { mutableStateOf(false) }

                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = "Referans Standart Şartlar",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                            .background(
                                if (isDark) Color(0xFF0F172A) else Color(0xFFFFFFFF),
                                RoundedCornerShape(10.dp)
                            )
                            .border(1.dp, dividerColor, RoundedCornerShape(10.dp))
                            .clickable { stdCondExpanded = true }
                            .padding(horizontal = 12.dp),
                        contentAlignment = Alignment.CenterStart
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = state.standardConditionName, fontSize = 13.sp)
                            Icon(Icons.Default.ArrowDropDown, contentDescription = null, modifier = Modifier.size(20.dp))
                        }

                        DropdownMenu(
                            expanded = stdCondExpanded,
                            onDismissRequest = { stdCondExpanded = false },
                            modifier = Modifier.fillMaxWidth(0.85f)
                        ) {
                            viewModel.standardConditions.keys.forEach { name ->
                                DropdownMenuItem(
                                    text = { Text(name) },
                                    onClick = {
                                        viewModel.updateStandardCondition(name)
                                        stdCondExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                // Action calculate button
                Button(
                    onClick = { viewModel.calculate() },
                    enabled = !state.isLoading,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .background(
                            Brush.horizontalGradient(listOf(CyanPrimary, IndigoSecondary)),
                            RoundedCornerShape(10.dp)
                        ),
                    elevation = ButtonDefaults.buttonElevation(defaultElevation = 2.dp)
                ) {
                    if (state.isLoading) {
                        CircularProgressIndicator(
                            color = Color.White,
                            modifier = Modifier.size(24.dp)
                        )
                    } else {
                        Text(
                            text = "HESAPLA",
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            color = Color.White
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun UnitSelectorDropdown(
    selectedUnit: String,
    units: List<String>,
    onUnitSelected: (String) -> Unit,
    isDark: Boolean,
    dividerColor: Color
) {
    var expanded by remember { mutableStateOf(false) }

    Box(
        modifier = Modifier
            .width(80.dp)
            .height(48.dp)
            .background(
                if (isDark) Color(0xFF0F172A) else Color(0xFFFFFFFF),
                RoundedCornerShape(10.dp)
            )
            .border(1.dp, dividerColor, RoundedCornerShape(10.dp))
            .clickable { expanded = true }
            .padding(horizontal = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(2.dp)
        ) {
            Text(
                text = selectedUnit,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Icon(
                Icons.Default.ArrowDropDown,
                contentDescription = null,
                modifier = Modifier.size(16.dp)
            )
        }

        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            units.forEach { unit ->
                DropdownMenuItem(
                    text = { Text(unit, fontWeight = FontWeight.Bold) },
                    onClick = {
                        onUnitSelected(unit)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
fun AnimatedWarningBanner(message: String?) {
    if (message != null) {
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(
                containerColor = ErrorRed.copy(alpha = 0.15f)
            ),
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp)
                .border(1.dp, ErrorRed.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
        ) {
            Row(
                modifier = Modifier.padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Icon(
                    Icons.Default.Warning,
                    contentDescription = null,
                    tint = ErrorRed,
                    modifier = Modifier.size(24.dp)
                )
                Text(
                    text = message,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    color = ErrorRed
                )
            }
        }
    }
}
