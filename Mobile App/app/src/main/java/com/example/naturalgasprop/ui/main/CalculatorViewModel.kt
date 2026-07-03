package com.example.naturalgasprop.ui.main

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.naturalgasprop.PythonBridge
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class CalculatorViewModel : ViewModel() {
    private val TAG = "CalculatorViewModel"

    private val _uiState = MutableStateFlow(CalculatorUiState())
    val uiState: StateFlow<CalculatorUiState> = _uiState.asStateFlow()

    // Preloaded natural gas components
    val availableComponents = listOf(
        "Methane", "Ethane", "Propane", "n-Butane", "IsoButane",
        "n-Pentane", "Isopentane", "Neopentane", "n-Hexane", "Isohexane",
        "n-Heptane", "n-Octane", "n-Nonane", "n-Decane", "n-Undecane", "n-Dodecane",
        "Nitrogen", "CarbonDioxide", "HydrogenSulfide", "CarbonylSulfide", "SulfurDioxide",
        "Water", "Oxygen", "Argon", "Hydrogen", "CarbonMonoxide", "Helium", "Ethylene",
        "Propylene", "1-Butene", "IsoButene", "cis-2-Butene", "trans-2-Butene",
        "CycloPropane", "Cyclopentane", "CycloHexane", "Ammonia", "Neon", "Krypton", "Xenon",
        "Air", "Methanol", "MEG", "TEG"
    )

    // Preloaded thermodynamic backends (NeqSim offline focus)
    val availableBackends = listOf(
        "neqsim-gerg2008" to "GERG-2008 (Ref. EOS)",
        "neqsim-srk" to "SRK (Standard)",
        "neqsim-pr" to "Peng-Robinson (Standard)",
        "neqsim-srk-cpa" to "CPA (Hydrate/Water)",
        "neqsim-soreide" to "Søreide-Whitson (Sour Gas)",
        "neqsim-gerg2008-h2" to "GERG-2008 + H2",
        "neqsim-eoscg" to "EOS-CG (CCS/CO2)",
        "neqsim-spanwagner" to "Span-Wagner (Pure CO2)",
        "neqsim-umrpru" to "UMR-PRU (Predictive)",
        "neqsim-srk-peneloux" to "SRK + Peneloux",
        "neqsim-srk-mc" to "SRK + Mathias-Copeman",
        "neqsim-srk-twucoon" to "SRK + Twu-Coon",
        "neqsim-pr-mc" to "PR + Mathias-Copeman",
        "neqsim-pr-twucoon" to "PR + Twu-Coon",
        "neqsim-pr-danesh" to "PR + Danesh correction"
    )

    // Preloaded standard conditions mapping
    val standardConditions = mapOf(
        "ISO 13443 (15°C, 1 atm)" to Pair(288.15, 101325.0),
        "GPA 2172 (60°F, 14.696 psi)" to Pair(288.706, 101325.0),
        "API MPMS (60°F, 14.73 psi)" to Pair(288.706, 101560.0),
        "EPDK (15°C, 1.01325 bar)" to Pair(288.15, 101325.0),
        "GOST 2939 (20°C, 1 atm)" to Pair(293.15, 101325.0),
        "Normal Şartlar (0°C, 1 atm)" to Pair(273.15, 101325.0)
    )

    fun addOrUpdateComponent(name: String, fraction: Double) {
        _uiState.update { state ->
            val updated = state.components.toMutableList()
            val existingIdx = updated.indexOfFirst { it.name.lowercase() == name.lowercase() }
            if (existingIdx != -1) {
                updated[existingIdx] = GasComponentInput(name, fraction)
            } else {
                updated.add(GasComponentInput(name, fraction))
            }
            state.copy(components = updated)
        }
    }

    fun removeComponent(name: String) {
        _uiState.update { state ->
            val updated = state.components.filterNot { it.name.lowercase() == name.lowercase() }
            state.copy(components = updated)
        }
    }

    fun clearMixture() {
        _uiState.update { state ->
            state.copy(components = emptyList())
        }
    }

    fun resetToDefaultMixture() {
        _uiState.update { state ->
            state.copy(components = listOf(
                GasComponentInput("Methane", 90.0),
                GasComponentInput("Ethane", 5.0),
                GasComponentInput("Propane", 3.0),
                GasComponentInput("Nitrogen", 1.0),
                GasComponentInput("CarbonDioxide", 1.0)
            ))
        }
    }

    fun normalizeMixture() {
        _uiState.update { state ->
            val total = state.totalFraction
            if (total <= 0.0) return@update state
            val scale = 100.0 / total
            val normalized = state.components.map {
                GasComponentInput(it.name, Math.round(it.fraction * scale * 10000.0) / 10000.0)
            }
            state.copy(components = normalized)
        }
    }

    fun updateTemperature(value: String) {
        _uiState.update { it.copy(temperatureStr = value) }
    }

    fun updateTemperatureUnit(unit: TemperatureUnit) {
        _uiState.update { it.copy(temperatureUnit = unit) }
    }

    fun updatePressure(value: String) {
        _uiState.update { it.copy(pressureStr = value) }
    }

    fun updatePressureUnit(unit: PressureUnit) {
        _uiState.update { it.copy(pressureUnit = unit) }
    }

    fun updateVolume(value: String) {
        _uiState.update { it.copy(volumeStr = value) }
    }

    fun updateVolumeUnit(unit: VolumeUnit) {
        _uiState.update { it.copy(volumeUnit = unit) }
    }

    fun updateBackend(backend: String) {
        _uiState.update { it.copy(selectedBackend = backend) }
    }

    fun updateStandardCondition(standardName: String) {
        _uiState.update { it.copy(standardConditionName = standardName) }
    }

    fun updateFoldableState(isTabletop: Boolean, isBook: Boolean, hingePosition: Int) {
        _uiState.update { it.copy(
            isTabletopMode = isTabletop,
            isBookMode = isBook,
            hingePositionDp = hingePosition
        )}
    }

    fun calculate() {
        val state = _uiState.value
        val tempVal = state.temperatureStr.toDoubleOrNull()
        val pressVal = state.pressureStr.toDoubleOrNull()
        val volVal = if (state.volumeStr.isEmpty()) null else state.volumeStr.toDoubleOrNull()

        if (state.components.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Lütfen gaz karışımına en az bir bileşen ekleyin.") }
            return
        }

        if (Math.abs(state.totalFraction - 100.0) > 1e-3) {
            _uiState.update { it.copy(errorMessage = "Bileşenlerin toplam yüzdesi 100 olmalıdır. Normalleştir butonunu kullanabilirsiniz. (Toplam: ${String.format("%.3f", state.totalFraction)}%)") }
            return
        }

        if (tempVal == null || tempVal <= -273.15) {
            _uiState.update { it.copy(errorMessage = "Geçersiz sıcaklık girdisi.") }
            return
        }

        if (pressVal == null || pressVal <= 0.0) {
            _uiState.update { it.copy(errorMessage = "Geçersiz basınç girdisi. Basınç sıfırdan büyük olmalıdır.") }
            return
        }

        _uiState.update { it.copy(isLoading = true, errorMessage = null, calculationResult = null) }

        viewModelScope.launch(Dispatchers.Default) {
            try {
                // Convert parameters
                val tempK = state.temperatureUnit.toKelvin(tempVal)
                val pressPa = state.pressureUnit.toPascal(pressVal)
                val volumeM3 = volVal?.let { state.volumeUnit.toM3(it) }

                val stdCond = standardConditions[state.standardConditionName] ?: Pair(288.15, 101325.0)

                // Build input JSON
                val inputObj = JSONObject().apply {
                    val compArr = JSONArray()
                    state.components.forEach { comp ->
                        compArr.put(JSONObject().apply {
                            put("name", comp.name)
                            put("fraction", comp.fraction)
                        })
                    }
                    put("components", compArr)
                    put("fraction_type", "molar")
                    put("temperature_k", tempK)
                    put("pressure_pa", pressPa)
                    put("backend", state.selectedBackend)
                    if (volumeM3 != null) {
                        put("volume_m3", volumeM3)
                    }
                    put("standard_T", stdCond.first)
                    put("standard_P", stdCond.second)
                    put("standard_name", state.standardConditionName)
                }

                Log.d(TAG, "Executing calculation with input: $inputObj")
                val jsonResult = PythonBridge.calculateProperties(inputObj.toString())
                
                val parsed = ParsedCalculationResult.fromJson(jsonResult)
                
                _uiState.update { it.copy(
                    calculationResult = parsed,
                    isLoading = false,
                    errorMessage = null
                ) }
            } catch (e: Exception) {
                Log.e(TAG, "Calculation execution error", e)
                _uiState.update { it.copy(
                    isLoading = false,
                    errorMessage = e.localizedMessage ?: "Hesaplama motoru hatası."
                ) }
            }
        }
    }

    fun generatePdfReport(context: Context) {
        val state = _uiState.value
        val result = state.calculationResult ?: return
        
        val tempVal = state.temperatureStr.toDoubleOrNull() ?: return
        val pressVal = state.pressureStr.toDoubleOrNull() ?: return
        val volVal = if (state.volumeStr.isEmpty()) null else state.volumeStr.toDoubleOrNull()
        
        _uiState.update { it.copy(isPdfGenerating = true, pdfFilePath = null) }
        
        viewModelScope.launch(Dispatchers.Default) {
            try {
                val tempK = state.temperatureUnit.toKelvin(tempVal)
                val pressPa = state.pressureUnit.toPascal(pressVal)
                val volumeM3 = volVal?.let { state.volumeUnit.toM3(it) }
                
                val stdCond = standardConditions[state.standardConditionName] ?: Pair(288.15, 101325.0)
                
                // Construct parameters JSON
                val inputObj = JSONObject().apply {
                    val compArr = JSONArray()
                    state.components.forEach { comp ->
                        compArr.put(JSONObject().apply {
                            put("name", comp.name)
                            put("fraction", comp.fraction)
                        })
                    }
                    put("components", compArr)
                    put("fraction_type", "molar")
                    put("temperature_k", tempK)
                    put("pressure_pa", pressPa)
                    put("backend", state.selectedBackend)
                    if (volumeM3 != null) {
                        put("volume_m3", volumeM3)
                    }
                    put("standard_T", stdCond.first)
                    put("standard_P", stdCond.second)
                    put("standard_name", state.standardConditionName)
                    put("unit_system", "SI")
                    put("temp_unit_str", state.temperatureUnit.symbol)
                    put("press_unit_str", state.pressureUnit.symbol)
                    put("temp_val_str", state.temperatureStr)
                    put("press_val_str", state.pressureStr)
                }
                
                // Destination file
                val reportsDir = File(context.getExternalFilesDir(null), "Reports")
                if (!reportsDir.exists()) {
                    reportsDir.mkdirs()
                }
                val outputFile = File(reportsDir, "Dogal_Gaz_Raporu_${System.currentTimeMillis()}.pdf")
                
                Log.d(TAG, "Generating PDF to path: ${outputFile.absolutePath}")
                val jsonResult = PythonBridge.generatePdfReport(inputObj.toString(), outputFile.absolutePath)
                
                val root = JSONObject(jsonResult)
                if (root.getString("status") == "success") {
                    _uiState.update { it.copy(
                        isPdfGenerating = false,
                        pdfFilePath = outputFile.absolutePath
                    ) }
                } else {
                    throw Exception(root.optString("error_message", "PDF generation failed"))
                }
            } catch (e: Exception) {
                Log.e(TAG, "PDF generation execution error", e)
                _uiState.update { it.copy(
                    isPdfGenerating = false,
                    errorMessage = "PDF Raporu oluşturulamadı: ${e.localizedMessage ?: "Bilinmeyen hata"}"
                ) }
            }
        }
    }
    
    fun resetPdfPath() {
        _uiState.update { it.copy(pdfFilePath = null) }
    }
}
