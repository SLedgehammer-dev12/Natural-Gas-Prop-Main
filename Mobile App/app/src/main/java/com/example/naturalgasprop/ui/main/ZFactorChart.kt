package com.example.naturalgasprop.ui.main

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.naturalgasprop.theme.CyanPrimary
import com.example.naturalgasprop.theme.IndigoSecondary
import com.example.naturalgasprop.theme.VioletTertiary

@Composable
fun ZFactorChart(
    zComparison: List<ParsedZFactorComparison>,
    modifier: Modifier = Modifier
) {
    val textMeasurer = rememberTextMeasurer()
    val isDark = isSystemInDarkTheme()

    // Filter valid comparisons with non-null Z-factors
    val validList = zComparison.filter { it.valid && it.zFactor != null && it.zFactor > 0.0 }
    
    if (validList.isEmpty()) {
        return
    }

    // Determine scale bounds
    val zValues = validList.map { it.zFactor!! }
    val minZ = zValues.minOrNull() ?: 0.8
    val maxZ = zValues.maxOrNull() ?: 1.0

    // Add padding to bounds
    val range = maxZ - minZ
    val boundsMin = if (range < 0.01) minZ - 0.05 else minZ - range * 0.2
    val boundsMax = if (range < 0.01) maxZ + 0.05 else maxZ + range * 0.2

    val displayBoundsMin = Math.max(0.0, boundsMin)
    val displayBoundsMax = Math.min(2.0, boundsMax)

    val labelColor = if (isDark) Color(0xFF94A3B8) else Color(0xFF475569) // Slate 400 vs 600
    val gridColor = if (isDark) Color(0xFF334155) else Color(0xFFE2E8F0) // Slate 700 vs 200
    val cardBg = if (isDark) Color(0xFF1E293B) else Color(0xFFF1F5F9)
    val onSurfaceColor = MaterialTheme.colorScheme.onSurface

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(cardBg, RoundedCornerShape(12.dp))
            .padding(16.dp)
    ) {
        Text(
            text = "Z-Faktörü Karşılaştırması",
            style = TextStyle(
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = onSurfaceColor
            ),
            modifier = Modifier.padding(bottom = 12.dp)
        )

        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(140.dp)
        ) {
            val width = size.width
            val height = size.height

            val leftPadding = 120.dp.toPx()
            val rightPadding = 20.dp.toPx()
            val topPadding = 20.dp.toPx()
            val bottomPadding = 30.dp.toPx()

            val chartWidth = width - leftPadding - rightPadding
            val chartHeight = height - topPadding - bottomPadding

            // 1. Draw horizontal grid lines and ticks
            val tickCount = 4
            for (i in 0..tickCount) {
                val fraction = i.toFloat() / tickCount
                val x = leftPadding + fraction * chartWidth
                val zVal = displayBoundsMin + fraction * (displayBoundsMax - displayBoundsMin)

                // Grid Line
                drawLine(
                    color = gridColor,
                    start = Offset(x, topPadding),
                    end = Offset(x, topPadding + chartHeight),
                    strokeWidth = 1.dp.toPx()
                )

                // Grid label text
                val label = String.format("%.3f", zVal)
                val textLayoutResult = textMeasurer.measure(
                    text = label,
                    style = TextStyle(fontSize = 10.sp, color = labelColor)
                )
                drawText(
                    textMeasurer = textMeasurer,
                    text = label,
                    style = TextStyle(fontSize = 10.sp, color = labelColor),
                    topLeft = Offset(x - textLayoutResult.size.width / 2, topPadding + chartHeight + 4.dp.toPx())
                )
            }

            // 2. Draw each model as a row
            val rowCount = validList.size
            val rowHeight = chartHeight / rowCount

            validList.forEachIndexed { index, comp ->
                val z = comp.zFactor!!
                val y = topPadding + index * rowHeight + rowHeight / 2

                // Row Grid Line
                drawLine(
                    color = gridColor.copy(alpha = 0.5f),
                    start = Offset(leftPadding, y),
                    end = Offset(leftPadding + chartWidth, y),
                    strokeWidth = 1.dp.toPx()
                )

                // Draw model name
                val shortName = when {
                    comp.method.startsWith("neqsim-") -> comp.method.substring(7).uppercase()
                    else -> comp.method
                }
                val textLayoutResult = textMeasurer.measure(
                    text = shortName,
                    style = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Medium, color = labelColor)
                )
                drawText(
                    textMeasurer = textMeasurer,
                    text = shortName,
                    style = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Medium, color = labelColor),
                    topLeft = Offset(leftPadding - textLayoutResult.size.width - 8.dp.toPx(), y - textLayoutResult.size.height / 2)
                )

                // Map Z to X position
                val zFraction = (z - displayBoundsMin) / (displayBoundsMax - displayBoundsMin)
                val dotX = leftPadding + (zFraction * chartWidth).toFloat()

                // Draw dot color depending on position/method
                val dotColor = when (index % 3) {
                    0 -> CyanPrimary
                    1 -> IndigoSecondary
                    else -> VioletTertiary
                }

                // Draw point bar link
                drawLine(
                    color = dotColor.copy(alpha = 0.3f),
                    start = Offset(leftPadding, y),
                    end = Offset(dotX, y),
                    strokeWidth = 4.dp.toPx()
                )

                // Draw dot circle
                drawCircle(
                    color = dotColor,
                    radius = 6.dp.toPx(),
                    center = Offset(dotX, y)
                )

                // Draw dot circle outline (glow effect)
                drawCircle(
                    color = dotColor.copy(alpha = 0.4f),
                    radius = 10.dp.toPx(),
                    center = Offset(dotX, y),
                    style = Stroke(width = 2.dp.toPx())
                )
                
                // Draw value next to the dot if space allows
                val zLabel = String.format("%.4f", z)
                val valLayout = textMeasurer.measure(
                    text = zLabel,
                    style = TextStyle(fontSize = 9.sp, fontWeight = FontWeight.Bold, color = onSurfaceColor)
                )
                drawText(
                    textMeasurer = textMeasurer,
                    text = zLabel,
                    style = TextStyle(fontSize = 9.sp, fontWeight = FontWeight.Bold, color = onSurfaceColor),
                    topLeft = Offset(dotX + 8.dp.toPx(), y - valLayout.size.height / 2)
                )
            }

            // Draw Y-axis line
            drawLine(
                color = gridColor,
                start = Offset(leftPadding, topPadding),
                end = Offset(leftPadding, topPadding + chartHeight),
                strokeWidth = 2.dp.toPx()
            )
        }
    }
}
