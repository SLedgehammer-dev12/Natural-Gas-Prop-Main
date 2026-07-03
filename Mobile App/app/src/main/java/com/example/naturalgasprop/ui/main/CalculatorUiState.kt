package com.example.naturalgasprop.ui.main

import org.json.JSONArray
import org.json.JSONObject

// Represents a single gas component input in UI
data class GasComponentInput(
    val name: String,
    val fraction: Double // Percentage (0-100)
)

enum class TemperatureUnit(val symbol: String) {
    CELSIUS("°C"),
    KELVIN("K"),
    FAHRENHEIT("°F");

    fun toKelvin(value: Double): Double {
        return when (this) {
            CELSIUS -> value + 273.15
            KELVIN -> value
            FAHRENHEIT -> (value - 32.0) * 5.0 / 9.0 + 273.15
        }
    }

    fun fromKelvin(value: Double): Double {
        return when (this) {
            CELSIUS -> value - 273.15
            KELVIN -> value
            FAHRENHEIT -> (value - 273.15) * 9.0 / 5.0 + 32.0
        }
    }
}

enum class PressureUnit(val symbol: String) {
    BAR("bar"),
    PA("Pa"),
    MPA("MPa"),
    PSI("psi"),
    KPA("kPa"),
    ATM("atm");

    fun toPascal(value: Double): Double {
        return when (this) {
            BAR -> value * 100000.0
            PA -> value
            MPA -> value * 1000000.0
            PSI -> value * 6894.75729
            KPA -> value * 1000.0
            ATM -> value * 101325.0
        }
    }

    fun fromPascal(value: Double): Double {
        return when (this) {
            BAR -> value / 100000.0
            PA -> value
            MPA -> value / 1000000.0
            PSI -> value / 6894.75729
            KPA -> value / 1000.0
            ATM -> value / 101325.0
        }
    }
}

enum class VolumeUnit(val symbol: String) {
    M3("m³"),
    SCF("scf");

    fun toM3(value: Double): Double {
        return when (this) {
            M3 -> value
            SCF -> value / 35.3146667
        }
    }

    fun fromM3(value: Double): Double {
        return when (this) {
            M3 -> value
            SCF -> value * 35.3146667
        }
    }
}

// Parsed Thermodynamics Calculation Results
data class ParsedActualResults(
    val temperatureK: Double,
    val pressurePa: Double,
    val density: Double,
    val molarMass: Double,
    val compressibilityFactor: Double,
    val internalEnergy: Double?,
    val enthalpy: Double?,
    val entropy: Double?,
    val cp: Double?,
    val cv: Double?,
    val isentropicExponent: Double?,
    val speedOfSound: Double?
)

data class ParsedStandardResults(
    val densityStd: Double?,
    val specificGravity: Double?,
    val referenceTemperatureK: Double,
    val referencePressurePa: Double,
    val standardName: String?
)

data class ParsedHeatingValues(
    val grossHeatingValueMass: Double?,
    val netHeatingValueMass: Double?,
    val grossHeatingValueVol: Double?,
    val netHeatingValueVol: Double?,
    val grossHeatingValueMolar: Double?,
    val netHeatingValueMolar: Double?,
    val grossWobbeIndex: Double?,
    val netWobbeIndex: Double?,
    val methodUsed: String?
)

data class ParsedVolumeConversion(
    val actualVolume: Double?,
    val mass: Double?,
    val standardVolume: Double?,
    val normalVolume: Double?
)

data class ParsedZFactorComparison(
    val method: String,
    val zFactor: Double?,
    val density: Double?,
    val molarMass: Double?,
    val enthalpy: Double?,
    val entropy: Double?,
    val cp: Double?,
    val cv: Double?,
    val ppr: Double?,
    val tpr: Double?,
    val valid: Boolean,
    val warning: String?
)

data class ParsedHydrateResults(
    val formationTemperatureK: Double?,
    val formationPressurePa: Double?,
    val formationTempFHammerschmidt: Double?,
    val formationTempFMotiee: Double?,
    val formationTempFTowlerMokhatab: Double?,
    val pressurePsia: Double?,
    val specificGravity: Double?
)

data class ParsedTransportProperties(
    val viscosityCp: Double?,
    val thermalConductivity: Double?,
    val jouleThomsonCoefficient: Double?,
    val surfaceTension: Double?,
    val hasAqueousPhase: Boolean,
    val hasLiquidHcPhase: Boolean
)

data class ParsedCalculationResult(
    val backendUsed: String,
    val actual: ParsedActualResults,
    val standard: ParsedStandardResults,
    val heating: ParsedHeatingValues?,
    val volume: ParsedVolumeConversion?,
    val zComparison: List<ParsedZFactorComparison>,
    val hydrate: ParsedHydrateResults?,
    val transport: ParsedTransportProperties?,
    val zFallbackWarning: String?
) {
    companion object {
        fun fromJson(jsonStr: String): ParsedCalculationResult {
            val root = JSONObject(jsonStr)
            if (root.getString("status") != "success") {
                throw Exception(root.optString("error_message", "Calculation failed"))
            }
            val resObj = root.getJSONObject("result")
            val backend = resObj.getString("backend_used")
            
            // Actual
            val actObj = resObj.getJSONObject("actual")
            val actual = ParsedActualResults(
                temperatureK = actObj.getDouble("temperature"),
                pressurePa = actObj.getDouble("pressure"),
                density = actObj.getDouble("density"),
                molarMass = actObj.getDouble("molar_mass"),
                compressibilityFactor = actObj.getDouble("compressibility_factor"),
                internalEnergy = actObj.optDoubleOrNull("internal_energy"),
                enthalpy = actObj.optDoubleOrNull("enthalpy"),
                entropy = actObj.optDoubleOrNull("entropy"),
                cp = actObj.optDoubleOrNull("cp"),
                cv = actObj.optDoubleOrNull("cv"),
                isentropicExponent = actObj.optDoubleOrNull("isentropic_exponent"),
                speedOfSound = actObj.optDoubleOrNull("speed_of_sound")
            )

            // Standard
            val stdObj = resObj.getJSONObject("standard")
            val standard = ParsedStandardResults(
                densityStd = stdObj.optDoubleOrNull("density_std"),
                specificGravity = stdObj.optDoubleOrNull("specific_gravity"),
                referenceTemperatureK = stdObj.getDouble("reference_temperature"),
                referencePressurePa = stdObj.getDouble("reference_pressure"),
                standardName = stdObj.optStringOrNull("standard_name")
            )

            // Heating
            val heatObj = resObj.optJSONObject("heating")
            val heating = heatObj?.let {
                ParsedHeatingValues(
                    grossHeatingValueMass = it.optDoubleOrNull("gross_heating_value_mass"),
                    netHeatingValueMass = it.optDoubleOrNull("net_heating_value_mass"),
                    grossHeatingValueVol = it.optDoubleOrNull("gross_heating_value_vol"),
                    netHeatingValueVol = it.optDoubleOrNull("net_heating_value_vol"),
                    grossHeatingValueMolar = it.optDoubleOrNull("gross_heating_value_molar"),
                    netHeatingValueMolar = it.optDoubleOrNull("net_heating_value_molar"),
                    grossWobbeIndex = it.optDoubleOrNull("gross_wobbe_index"),
                    netWobbeIndex = it.optDoubleOrNull("net_wobbe_index"),
                    methodUsed = it.optStringOrNull("method_used")
                )
            }

            // Volume Conversion
            val volObj = resObj.optJSONObject("volume_conversion")
            val volume = volObj?.let {
                ParsedVolumeConversion(
                    actualVolume = it.optDoubleOrNull("actual_volume"),
                    mass = it.optDoubleOrNull("mass"),
                    standardVolume = it.optDoubleOrNull("standard_volume"),
                    normalVolume = it.optDoubleOrNull("normal_volume")
                )
            }

            // Z Comparison
            val zCompList = mutableListOf<ParsedZFactorComparison>()
            val zCompArr = resObj.optJSONArray("z_factor_comparison")
            if (zCompArr != null) {
                for (i in 0 until zCompArr.length()) {
                    val it = zCompArr.getJSONObject(i)
                    zCompList.add(
                        ParsedZFactorComparison(
                            method = it.getString("method"),
                            zFactor = it.optDoubleOrNull("z_factor"),
                            density = it.optDoubleOrNull("density"),
                            molarMass = it.optDoubleOrNull("molar_mass"),
                            enthalpy = it.optDoubleOrNull("enthalpy"),
                            entropy = it.optDoubleOrNull("entropy"),
                            cp = it.optDoubleOrNull("cp"),
                            cv = it.optDoubleOrNull("cv"),
                            ppr = it.optDoubleOrNull("ppr"),
                            tpr = it.optDoubleOrNull("tpr"),
                            valid = it.optBoolean("valid", true),
                            warning = it.optStringOrNull("warning")
                        )
                    )
                }
            }

            // Hydrate
            val hydObj = resObj.optJSONObject("hydrate")
            val hydrate = hydObj?.let {
                ParsedHydrateResults(
                    formationTemperatureK = it.optDoubleOrNull("formation_temperature_k"),
                    formationPressurePa = it.optDoubleOrNull("formation_pressure_pa"),
                    formationTempFHammerschmidt = it.optDoubleOrNull("formation_temperature_f_hammerschmidt"),
                    formationTempFMotiee = it.optDoubleOrNull("formation_temperature_f_motiee"),
                    formationTempFTowlerMokhatab = it.optDoubleOrNull("formation_temperature_f_towler_mokhatab"),
                    pressurePsia = it.optDoubleOrNull("pressure_psia"),
                    specificGravity = it.optDoubleOrNull("specific_gravity")
                )
            }

            // Transport Properties
            val trnObj = resObj.optJSONObject("transport")
            val transport = trnObj?.let {
                ParsedTransportProperties(
                    viscosityCp = it.optDoubleOrNull("viscosity_cp"),
                    thermalConductivity = it.optDoubleOrNull("thermal_conductivity"),
                    jouleThomsonCoefficient = it.optDoubleOrNull("joule_thomson_coefficient"),
                    surfaceTension = it.optDoubleOrNull("surface_tension"),
                    hasAqueousPhase = it.optBoolean("has_aqueous_phase", false),
                    hasLiquidHcPhase = it.optBoolean("has_liquid_hc_phase", false)
                )
            }

            val warning = resObj.optStringOrNull("z_fallback_warning")

            return ParsedCalculationResult(
                backendUsed = backend,
                actual = actual,
                standard = standard,
                heating = heating,
                volume = volume,
                zComparison = zCompList,
                hydrate = hydrate,
                transport = transport,
                zFallbackWarning = warning
            )
        }

        private fun JSONObject.optDoubleOrNull(key: String): Double? {
            if (isNull(key)) return null
            val d = optDouble(key, Double.NaN)
            return if (d.isNaN()) null else d
        }

        private fun JSONObject.optStringOrNull(key: String): String? {
            if (isNull(key)) return null
            val s = optString(key, "")
            return if (s.isEmpty()) null else s
        }
    }
}

// Master UI State for the Calculator view
data class CalculatorUiState(
    val components: List<GasComponentInput> = listOf(
        GasComponentInput("Methane", 90.0),
        GasComponentInput("Ethane", 5.0),
        GasComponentInput("Propane", 3.0),
        GasComponentInput("Nitrogen", 1.0),
        GasComponentInput("CarbonDioxide", 1.0)
    ),
    val temperatureStr: String = "15.0",
    val temperatureUnit: TemperatureUnit = TemperatureUnit.CELSIUS,
    val pressureStr: String = "1.01325",
    val pressureUnit: PressureUnit = PressureUnit.BAR,
    val volumeStr: String = "",
    val volumeUnit: VolumeUnit = VolumeUnit.M3,
    val selectedBackend: String = "neqsim-gerg2008",
    val standardConditionName: String = "ISO 13443 (15°C, 1 atm)",
    val customStandardTStr: String = "288.15",
    val customStandardPStr: String = "101325.0",
    
    val calculationResult: ParsedCalculationResult? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    
    val pdfFilePath: String? = null,
    val isPdfGenerating: Boolean = false,
    
    val isTabletopMode: Boolean = false,
    val isBookMode: Boolean = false,
    val hingePositionDp: Int = -1
) {
    val totalFraction: Double
        get() = components.sumOf { it.fraction }
}
