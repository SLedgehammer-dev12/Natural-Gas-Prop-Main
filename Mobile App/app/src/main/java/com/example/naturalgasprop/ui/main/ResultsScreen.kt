package com.example.naturalgasprop.ui.main

import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import com.example.naturalgasprop.theme.CyanPrimary
import com.example.naturalgasprop.theme.ErrorRed
import com.example.naturalgasprop.theme.GlassBackgroundDark
import com.example.naturalgasprop.theme.IndigoSecondary
import com.example.naturalgasprop.theme.SuccessGreen
import com.example.naturalgasprop.theme.WarningOrange
import java.io.File

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ResultsScreen(
    state: CalculatorUiState,
    viewModel: CalculatorViewModel,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val context = LocalContext.current
    val isDark = isSystemInDarkTheme()

    val glassBg = if (isDark) Color(0xFF1E293B).copy(alpha = 0.8f) else Color(0xFFF1F5F9).copy(alpha = 0.8f)
    val dividerColor = if (isDark) Color(0xFF334155) else Color(0xFFE2E8F0)

    // Launch PDF viewer intent if path is populated
    LaunchedEffect(state.pdfFilePath) {
        state.pdfFilePath?.let { filePath ->
            openPdf(context, filePath)
            viewModel.resetPdfPath()
        }
    }

    val result = state.calculationResult

    if (result == null) {
        Box(
            modifier = modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    Icons.Default.Info,
                    contentDescription = null,
                    tint = CyanPrimary,
                    modifier = Modifier.size(48.dp)
                )
                Text(
                    text = "Henüz hesaplama yapılmadı.\nParametreleri girip 'Hesapla' butonuna basın.",
                    textAlign = TextAlign.Center,
                    color = labelColor(isDark),
                    fontSize = 14.sp
                )
            }
        }
        return
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(8.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Active Backend Header Info
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = glassBg),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, dividerColor, RoundedCornerShape(12.dp))
        ) {
            Row(
                modifier = Modifier.padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(Icons.Default.Info, contentDescription = null, tint = CyanPrimary)
                Text(
                    text = "Kullanılan Çözücü: ${result.backendUsed}",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
        }

        // Warning banner for ANN10 fallback
        if (result.zFallbackWarning != null) {
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = WarningOrange.copy(alpha = 0.15f)),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, WarningOrange.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Icon(Icons.Default.Warning, contentDescription = null, tint = WarningOrange)
                    Text(
                        text = result.zFallbackWarning,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        color = WarningOrange
                    )
                }
            }
        }

        // Hydrate formation hazard warning
        result.hydrate?.formationTemperatureK?.let { hydTempK ->
            val actualTempK = result.actual.temperatureK
            if (actualTempK <= hydTempK) {
                val hydTempC = hydTempK - 273.15
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = ErrorRed.copy(alpha = 0.15f)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, ErrorRed.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Icon(Icons.Default.Warning, contentDescription = null, tint = ErrorRed)
                        Text(
                            text = "HİDRAT OLUŞUM UYARISI: İşletme sıcaklığı (${String.format("%.2f", actualTempK - 273.15)}°C) hidrat oluşum sıcaklığının (${String.format("%.2f", hydTempC)}°C) altında! Gaz hattında hidrat donması riski mevcuttur.",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = ErrorRed
                        )
                    }
                }
            }
        }

        // 1. KPI Showcase Card (Z, Density, HHV, Molar Mass)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                KpiCard(
                    title = "Z-Faktörü",
                    value = String.format("%.5f", result.actual.compressibilityFactor),
                    unit = "",
                    modifier = Modifier.fillMaxWidth(),
                    isDark = isDark,
                    dividerColor = dividerColor
                )

                result.standard.densityStd?.let { rhoStd ->
                    KpiCard(
                        title = "Standart Yoğunluk",
                        value = String.format("%.4f", rhoStd),
                        unit = "kg/Sm³",
                        modifier = Modifier.fillMaxWidth(),
                        isDark = isDark,
                        dividerColor = dividerColor
                    )
                }
            }

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                KpiCard(
                    title = "Gerçek Yoğunluk",
                    value = String.format("%.4f", result.actual.density),
                    unit = "kg/m³",
                    modifier = Modifier.fillMaxWidth(),
                    isDark = isDark,
                    dividerColor = dividerColor
                )

                result.heating?.grossHeatingValueVol?.let { hhv ->
                    KpiCard(
                        title = "Isıl Değer (HHV)",
                        value = String.format("%.2f", hhv),
                        unit = "MJ/Sm³",
                        modifier = Modifier.fillMaxWidth(),
                        isDark = isDark,
                        dividerColor = dividerColor
                    )
                }
            }
        }

        // 2. Tabular Actual Conditions
        PropertySectionCard(
            title = "Gerçek Koşullar (Actual Properties)",
            properties = buildList {
                add("Sıcaklık" to Pair(String.format("%.2f", result.actual.temperatureK - 273.15), "°C"))
                add("Basınç" to Pair(String.format("%.4f", result.actual.pressurePa / 1e5), "bar a"))
                add("Z-Faktör (Sıkıştırılabilirlik)" to Pair(String.format("%.5f", result.actual.compressibilityFactor), ""))
                add("Gerçek Yoğunluk (ρ)" to Pair(String.format("%.4f", result.actual.density), "kg/m³"))
                add("Mol Kütlesi (M)" to Pair(String.format("%.4f", result.actual.molarMass * 1000.0), "g/mol"))
                
                result.actual.enthalpy?.let { add("Spesifik Entalpi (h)" to Pair(String.format("%.2f", it), "kJ/kg")) }
                result.actual.entropy?.let { add("Spesifik Entropi (s)" to Pair(String.format("%.4f", it), "kJ/kg·K")) }
                result.actual.cp?.let { add("Isı Kapasitesi (Cp)" to Pair(String.format("%.4f", it), "kJ/kg·K")) }
                result.actual.cv?.let { add("Isı Kapasitesi (Cv)" to Pair(String.format("%.4f", it), "kJ/kg·K")) }
                result.actual.isentropicExponent?.let { add("İzentropik Üs (κ)" to Pair(String.format("%.4f", it), "")) }
                result.actual.speedOfSound?.let { add("Ses Hızı" to Pair(String.format("%.2f", it), "m/s")) }
            },
            isDark = isDark,
            dividerColor = dividerColor
        )

        // 3. Tabular Standard Conditions
        PropertySectionCard(
            title = "Standart Koşullar (Standard Properties)",
            properties = buildList {
                add("Standart Yoğunluk" to Pair(result.standard.densityStd?.let { String.format("%.4f", it) } ?: "-", "kg/Sm³"))
                add("Bağıl Yoğunluk (Relative Density)" to Pair(result.standard.specificGravity?.let { String.format("%.4f", it) } ?: "-", ""))
                add("Referans Sıcaklık" to Pair(String.format("%.2f", result.standard.referenceTemperatureK - 273.15), "°C"))
                add("Referans Basınç" to Pair(String.format("%.3f", result.standard.referencePressurePa / 1000.0), "kPa a"))
            },
            isDark = isDark,
            dividerColor = dividerColor
        )

        // 4. Heating values if available
        result.heating?.let { heating ->
            PropertySectionCard(
                title = "Isıl Değerler (Heating Values)",
                properties = buildList {
                    add("Gross (Üst) Isıl Değer (Hacimsel)" to Pair(heating.grossHeatingValueVol?.let { String.format("%.2f", it) } ?: "-", "MJ/Sm³"))
                    add("Net (Alt) Isıl Değer (Hacimsel)" to Pair(heating.netHeatingValueVol?.let { String.format("%.2f", it) } ?: "-", "MJ/Sm³"))
                    add("Gross (Üst) Wobbe Endeksi" to Pair(heating.grossWobbeIndex?.let { String.format("%.2f", it) } ?: "-", "MJ/Sm³"))
                    add("Net (Alt) Wobbe Endeksi" to Pair(heating.netWobbeIndex?.let { String.format("%.2f", it) } ?: "-", "MJ/Sm³"))
                    add("Gross (Üst) Isıl Değer (Kütlesel)" to Pair(heating.grossHeatingValueMass?.let { String.format("%.2f", it) } ?: "-", "MJ/kg"))
                    add("Net (Alt) Isıl Değer (Kütlesel)" to Pair(heating.netHeatingValueMass?.let { String.format("%.2f", it) } ?: "-", "MJ/kg"))
                    add("Metod" to Pair(heating.methodUsed ?: "-", ""))
                },
                isDark = isDark,
                dividerColor = dividerColor
            )
        }

        // 5. Volume conversion if available
        result.volume?.let { vol ->
            PropertySectionCard(
                title = "Hacim & Kütle Dönüşümleri",
                properties = buildList {
                    add("Gerçek Hacim (Actual Volume)" to Pair(vol.actualVolume?.let { String.format("%.3f", it) } ?: "-", "m³"))
                    add("Kütle (Mass)" to Pair(vol.mass?.let { String.format("%.2f", it) } ?: "-", "kg"))
                    add("Standart Hacim (Standard Volume)" to Pair(vol.standardVolume?.let { String.format("%.3f", it) } ?: "-", "Sm³"))
                    add("Normal Hacim (Normal Volume)" to Pair(vol.normalVolume?.let { String.format("%.3f", it) } ?: "-", "Nm³"))
                },
                isDark = isDark,
                dividerColor = dividerColor
            )
        }

        // 6. Transport properties if available
        result.transport?.let { trans ->
            PropertySectionCard(
                title = "Ulaştırma Özellikleri (Transport Properties)",
                properties = buildList {
                    add("Viskozite (Viscosity)" to Pair(trans.viscosityCp?.let { String.format("%.6f", it) } ?: "-", "cP"))
                    add("Isıl İletkenlik (Thermal Cond.)" to Pair(trans.thermalConductivity?.let { String.format("%.6f", it) } ?: "-", "W/m·K"))
                    add("Joule-Thomson Katsayısı" to Pair(trans.jouleThomsonCoefficient?.let { String.format("%.4f", it) } ?: "-", "K/bar"))
                    add("Yüzey Gerilimi" to Pair(trans.surfaceTension?.let { String.format("%.6f", it) } ?: "-", "N/m"))
                    add("Aqueous Phase Exist?" to Pair(if (trans.hasAqueousPhase) "Yes (Sulu Faz)" else "No", ""))
                    add("Liquid Hydrocarbon Phase?" to Pair(if (trans.hasLiquidHcPhase) "Yes (Sıvı HC Fazı)" else "No", ""))
                },
                isDark = isDark,
                dividerColor = dividerColor
            )
        }

        // 7. Hydrate temperature predictions
        result.hydrate?.let { hyd ->
            PropertySectionCard(
                title = "Hidrat Oluşum Sıcaklıkları",
                properties = buildList {
                    add("CPA (Statoil CPA)" to Pair(hyd.formationTemperatureK?.let { String.format("%.2f", it - 273.15) } ?: "-", "°C"))
                    add("Hammerschmidt (1934)" to Pair(hyd.formationTempFHammerschmidt?.let { String.format("%.2f", (it - 32.0) * 5.0 / 9.0) } ?: "-", "°C"))
                    add("Motiee (1991)" to Pair(hyd.formationTempFMotiee?.let { String.format("%.2f", (it - 32.0) * 5.0 / 9.0) } ?: "-", "°C"))
                    add("Towler & Mokhatab (2005)" to Pair(hyd.formationTempFTowlerMokhatab?.let { String.format("%.2f", (it - 32.0) * 5.0 / 9.0) } ?: "-", "°C"))
                },
                isDark = isDark,
                dividerColor = dividerColor
            )
        }

        // 8. Custom drawn Z-Factor Chart comparison
        ZFactorChart(zComparison = result.zComparison, modifier = Modifier.fillMaxWidth())

        Spacer(modifier = Modifier.height(6.dp))

        // PDF Generation Action Button
        Button(
            onClick = { viewModel.generatePdfReport(context) },
            enabled = !state.isPdfGenerating,
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
            if (state.isPdfGenerating) {
                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(22.dp))
            } else {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(Icons.Default.Share, contentDescription = null, tint = Color.White, modifier = Modifier.size(20.dp))
                    Text("PDF RAPORU OLUŞTUR", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Color.White)
                }
            }
        }
    }
}

@Composable
fun KpiCard(
    title: String,
    value: String,
    unit: String,
    modifier: Modifier = Modifier,
    isDark: Boolean,
    dividerColor: Color
) {
    val cardBg = if (isDark) Color(0xFF1E293B) else Color(0xFFFFFFFF)
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = cardBg),
        modifier = modifier.border(1.dp, dividerColor.copy(alpha = 0.5f), RoundedCornerShape(12.dp)),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(text = title, fontSize = 11.sp, color = labelColor(isDark), textAlign = TextAlign.Center)
            Spacer(modifier = Modifier.height(2.dp))
            Text(text = value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = CyanPrimary, textAlign = TextAlign.Center)
            if (unit.isNotEmpty()) {
                Spacer(modifier = Modifier.height(1.dp))
                Text(text = unit, fontSize = 9.sp, color = labelColor(isDark))
            }
        }
    }
}

@Composable
fun PropertySectionCard(
    title: String,
    properties: List<Pair<String, Pair<String, String>>>,
    isDark: Boolean,
    dividerColor: Color
) {
    val cardBg = if (isDark) Color(0xFF1E293B).copy(alpha = 0.8f) else Color(0xFFFFFFFF)

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = cardBg),
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
                text = title,
                fontWeight = FontWeight.Bold,
                fontSize = 13.sp,
                color = CyanPrimary
            )
            Spacer(modifier = Modifier.height(6.dp))

            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                properties.forEach { (name, data) ->
                    val (value, unit) = data
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 1.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = name,
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.85f),
                            modifier = Modifier.weight(0.55f)
                        )

                        Row(
                            modifier = Modifier.weight(0.45f),
                            horizontalArrangement = Arrangement.End,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = value,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            if (unit.isNotEmpty()) {
                                Spacer(modifier = Modifier.width(3.dp))
                                Text(
                                    text = unit,
                                    fontSize = 9.sp,
                                    color = labelColor(isDark)
                                )
                            }
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
        }
    }
}

private fun openPdf(context: Context, filePath: String) {
    try {
        val file = File(filePath)
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/pdf")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
        Toast.makeText(context, "PDF Raporu başarıyla açıldı", Toast.LENGTH_SHORT).show()
    } catch (e: Exception) {
        Toast.makeText(context, "PDF okuyucu uygulaması bulunamadı. Rapor buraya kaydedildi: $filePath", Toast.LENGTH_LONG).show()
    }
}

private fun labelColor(isDark: Boolean) = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569)
