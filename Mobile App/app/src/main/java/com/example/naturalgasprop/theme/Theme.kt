package com.example.naturalgasprop.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = CyanPrimary,
    secondary = IndigoSecondary,
    tertiary = VioletTertiary,
    background = DarkBackground,
    surface = DarkSurface,
    onPrimary = OnDarkPrimary,
    onSecondary = OnDarkSecondary,
    onBackground = OnDarkPrimary,
    onSurface = OnDarkPrimary,
    error = ErrorRed
)

private val LightColorScheme = lightColorScheme(
    primary = CyanDark,
    secondary = IndigoDark,
    tertiary = VioletTertiary,
    background = LightBackground,
    surface = LightSurface,
    onPrimary = OnLightPrimary,
    onSecondary = OnLightSecondary,
    onBackground = OnLightPrimary,
    onSurface = OnLightPrimary,
    error = ErrorRed
)

@Composable
fun NaturalGasPropTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
