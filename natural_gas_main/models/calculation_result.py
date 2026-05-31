"""
Calculation result models.

Defines structured data models for storing thermodynamic calculation results.
"""

from typing import Optional, Dict, List, Tuple, Any
import math
from pydantic import BaseModel, Field

from natural_gas_main.utils.result_unit_converter import ResultUnitConverter, UnitSystem
from natural_gas_main.core.converters import convert_temperature_from_K, convert_pressure_from_Pa


class ActualConditionResults(BaseModel):
    """Results at actual (operating) conditions."""
    temperature: float = Field(..., description="Operating temperature (K)")
    pressure: float = Field(..., description="Operating pressure (Pa)")
    density: float = Field(..., description="Mass density (kg/m³)")
    molar_mass: float = Field(..., description="Molar mass (kg/mol)")
    compressibility_factor: float = Field(..., description="Z-factor (dimensionless)")
    internal_energy: float = Field(..., description="Specific internal energy (kJ/kg)")
    enthalpy: float = Field(..., description="Specific enthalpy (kJ/kg)")
    entropy: float = Field(..., description="Specific entropy (kJ/kg·K)")
    cp: float = Field(..., description="Specific heat at constant pressure (kJ/kg·K)")
    cv: float = Field(..., description="Specific heat at constant volume (kJ/kg·K)")
    isentropic_exponent: Optional[float] = Field(None, description="k = Cp/Cv (dimensionless)")
    speed_of_sound: Optional[float] = Field(None, description="Speed of sound (m/s)")
    
    model_config = {"frozen": False}


class StandardConditionResults(BaseModel):
    """
    Results at standard conditions (e.g., 15°C, 101.325 kPa).
    
    Attributes:
        density_std: Density at standard conditions (kg/Sm³)
        specific_gravity: Specific gravity relative to air (dimensionless)
        reference_temperature: Reference temperature used (K)
        reference_pressure: Reference pressure used (Pa)
        standard_name: Name of the standard used
    """
    
    density_std: Optional[float] = Field(None, description="Density at standard conditions (kg/Sm³)")
    specific_gravity: Optional[float] = Field(None, description="Specific gravity relative to air (dimensionless)")
    
    # Metadata about the standard used
    reference_temperature: float = Field(..., description="Reference temperature used (K)")
    reference_pressure: float = Field(..., description="Reference pressure used (Pa)")
    standard_name: Optional[str] = Field(None, description="Name of the standard used")
    
    model_config = {
        "frozen": False,
        "validate_assignment": True
    }


class HeatingValues(BaseModel):
    """Heating value calculation results."""
    
    hhv_mass: float = Field(..., description="Higher heating value, mass basis (MJ/kg)")
    lhv_mass: float = Field(..., description="Lower heating value, mass basis (MJ/kg)")
    hhv_volume: float = Field(..., description="HHV, volumetric basis (MJ/Sm³)")
    lhv_volume: float = Field(..., description="LHV, volumetric basis (MJ/Sm³)")
    wobbe_index: float = Field(..., description="Wobbe index (MJ/Sm³)")
    hhv_btu_scf: float = Field(..., description="HHV in industrial units (Btu/SCF)")
    calculation_method: str = Field(..., description="Method used for calculation")
    
    model_config = {"frozen": False}


class VolumeConversion(BaseModel):
    """Volume conversion results."""
    
    actual_volume: float = Field(..., description="Actual volume (ACM) (m³)")
    mass: float = Field(..., description="Total mass (kg)")
    standard_volume: float = Field(..., description="Standard volume (SCM) (Sm³)")
    normal_volume: Optional[float] = Field(None, description="Normal volume (NCM) (Nm³)")
    normal_volume_error: Optional[str] = Field(None, description="Error message if normal volume calculation fails")
    
    model_config = {"frozen": False}


class PhaseEnvelopeData(BaseModel):
    """Phase envelope (dew point and bubble point curve) data."""

    temperature_k: List[float] = Field(..., description="Temperatures in Kelvin")
    pressure_pa: List[float] = Field(..., description="Pressures in Pascals")
    cricondentherm_t: Optional[float] = Field(None, description="Maximum temperature on the envelope")
    cricondenbar_p: Optional[float] = Field(None, description="Maximum pressure on the envelope")
    cricondenbar_t: Optional[float] = Field(None, description="Temperature at cricondenbar pressure")
    critical_t: Optional[float] = Field(None, description="Critical point temperature")
    critical_p: Optional[float] = Field(None, description="Critical point pressure")

    model_config = {"frozen": False}


class ZFactorComparison(BaseModel):
    """Optional engineering Z-factor estimate for comparison/fallback."""

    method: str = Field(..., description="Z-factor estimation method")
    z_factor: Optional[float] = Field(None, description="Estimated Z-factor")
    density: Optional[float] = Field(None, description="Mass density (kg/m³)")
    molar_mass: Optional[float] = Field(None, description="Molar mass (kg/mol)")
    enthalpy: Optional[float] = Field(None, description="Specific enthalpy (kJ/kg)")
    entropy: Optional[float] = Field(None, description="Specific entropy (kJ/kg·K)")
    cp: Optional[float] = Field(None, description="Specific heat at constant pressure (kJ/kg·K)")
    cv: Optional[float] = Field(None, description="Specific heat at constant volume (kJ/kg·K)")
    ppr: float = Field(..., description="Pseudo-reduced pressure")
    tpr: float = Field(..., description="Pseudo-reduced temperature")
    valid: bool = Field(..., description="True if within method validity range")
    warning: Optional[str] = Field(None, description="Validity or calculation warning")

    model_config = {"frozen": False}


class HydrateResults(BaseModel):
    """Hydrate analysis results and predictions."""
    specific_gravity: float = Field(..., description="Gas specific gravity (dimensionless)")
    operating_temperature: float = Field(..., description="Operating temperature (K)")
    operating_pressure: float = Field(..., description="Operating pressure (Pa)")
    
    # Predicted hydrate formation temperatures in Kelvin
    t_hydrate_hammerschmidt: float = Field(..., description="Hammerschmidt predicted temperature (K)")
    t_hydrate_motiee: float = Field(..., description="Motiee predicted temperature (K)")
    t_hydrate_towler_mokhatab: float = Field(..., description="Towler-Mokhatab predicted temperature (K)")
    
    # Average of the three predictions
    t_hydrate_average: float = Field(..., description="Average predicted temperature (K)")
    
    # Hydrate formation risk assessment
    risk_hammerschmidt: bool = Field(..., description="Risk of hydrate formation using Hammerschmidt")
    risk_motiee: bool = Field(..., description="Risk of hydrate formation using Motiee")
    risk_towler_mokhatab: bool = Field(..., description="Risk of hydrate formation using Towler-Mokhatab")
    risk_average: bool = Field(..., description="Risk of hydrate formation based on average temperature")
    
    model_config = {"frozen": False}


class CalculationResult(BaseModel):
    """
    Complete calculation results container.
    
    Aggregates all results from thermodynamic calculations.
    """
    
    backend_used: str = Field(..., description="Thermodynamic backend used (HEOS, SRK, PR)")
    actual: ActualConditionResults = Field(..., description="Actual condition results")
    standard: StandardConditionResults = Field(..., description="Standard condition results")
    heating: Optional[HeatingValues] = Field(None, description="Heating values (if calculable)")
    volume_conversion: Optional[VolumeConversion] = Field(None, description="Volume conversion (if provided)")
    phase_envelope: Optional[PhaseEnvelopeData] = Field(None, description="Phase envelope data for plotting")
    z_factor_comparison: List[ZFactorComparison] = Field(default_factory=list, description="Standing-Katz/DAK Z estimates")
    z_fallback_warning: Optional[str] = Field(None, description="Warning if result is Z-only fallback")
    hydrate: Optional[HydrateResults] = Field(None, description="Hydrate analysis results")
    
    def to_display_list(self, unit_system: str = "SI") -> List[Tuple[str, str, str]]:
        """
        Convert results to display format for UI TreeView.
        
        Args:
            unit_system: Unit system for display ("SI", "Imperial", or "Mixed")
        
        Returns:
            List of (property_name, value, unit_string) tuples
        """
        results = []
        
        # Get unit preferences based on system
        try:
            unit_sys = UnitSystem(unit_system)
        except ValueError:
            unit_sys = UnitSystem.SI
        
        prefs = ResultUnitConverter.get_unit_preferences(unit_sys)
        
        # Header - Actual Conditions
        results.append(("- GERÇEK KOŞULLAR SONUÇLARI -", "", ""))
        results.append(("Hesaplama Yöntemi (Termo)", self.backend_used, ""))
        if self.z_fallback_warning:
            results.append(("Sınırlı Fallback Uyarısı", self.z_fallback_warning, ""))
        
        # Density
        density_val, density_unit = ResultUnitConverter.convert_density(
            self.actual.density, prefs['density']
        )
        results.append(("Yoğunluk (Gerçek - ρ)", self._format_float(density_val, 4), density_unit))
        
        results.append(("Mol Kütlesi (Karışım - M)", self._format_float(self.actual.molar_mass, 4), "kg/mol"))
        results.append(("Sıkıştırılabilirlik Faktörü (Z)", self._format_float(self.actual.compressibility_factor, 5), "-"))

        # Energy properties
        u_val, u_unit = ResultUnitConverter.convert_energy_mass(
            self.actual.internal_energy, prefs['energy_mass']
        )
        h_val, h_unit = ResultUnitConverter.convert_energy_mass(
            self.actual.enthalpy, prefs['energy_mass']
        )
        s_val, s_unit = ResultUnitConverter.convert_entropy(
            self.actual.entropy, prefs['entropy']
        )
        cp_val, cp_unit = ResultUnitConverter.convert_entropy(
            self.actual.cp, prefs['entropy']
        )
        cv_val, cv_unit = ResultUnitConverter.convert_entropy(
            self.actual.cv, prefs['entropy']
        )
        
        results.append(("İç Enerji (u)", self._format_float(u_val, 4), u_unit))
        results.append(("Entalpi (h)", self._format_float(h_val, 4), h_unit))
        results.append(("Entropi (s)", self._format_float(s_val, 4), s_unit))
        results.append(("Cp", self._format_float(cp_val, 4), cp_unit))
        results.append(("Cv", self._format_float(cv_val, 4), cv_unit))
        
        if self.actual.isentropic_exponent is not None:
            results.append(("İzotropik Üs (k)", self._format_float(self.actual.isentropic_exponent, 4), "-"))
        else:
            results.append(("İzotropik Üs (k)", "Hesaplanamadı", "-"))
        
        if self.actual.speed_of_sound is not None:
            speed_val, speed_unit = ResultUnitConverter.convert_speed(
                self.actual.speed_of_sound, prefs['speed']
            )
            results.append(("Ses Hızı (a)", self._format_float(speed_val, 2), speed_unit))
        else:
            results.append(("Ses Hızı (a)", "Hesaplanamadı", "-"))
        
        # Header - Standard Conditions
        std_t_k = self.standard.reference_temperature
        std_p_pa = self.standard.reference_pressure
        results.append(("- STANDART ÇEVRİM BİLGİLERİ -", "", ""))
        results.append(("Standart Koşullar", f"{std_t_k:.2f} K, {std_p_pa:.3f} kPa", "-"))
        
        # Standard density
        if self.standard.density_std is not None:
            std_density_val, std_density_unit = ResultUnitConverter.convert_density(
                self.standard.density_std, prefs['density']
            )
            results.append(("Yoğunluk (SCM - ρ_std)", f"{std_density_val:.4f}", std_density_unit.replace('m³', 'Sm³') if 'm³' in std_density_unit else std_density_unit))
        else:
            results.append(("Yoğunluk (SCM - ρ_std)", "Hesaplanamadı", "-"))
        if self.standard.specific_gravity is not None:
            results.append(("Bağıl Yoğunluk (SG - Hava=1)", f"{self.standard.specific_gravity:.4f}", "-"))
        else:
            results.append(("Bağıl Yoğunluk (SG - Hava=1)", "Hesaplanamadı", "-"))
        
        # Header - Heating Values
        if self.heating:
            results.append(("- ISIL DEĞERLER (SCM) -", "", ""))
            results.append(("Hesaplama Yöntemi (HHV/LHV)", self.heating.calculation_method, ""))
            
            # Mass-based heating values
            hhv_m_val, hhv_m_unit = ResultUnitConverter.convert_heating_value_mass(
                self.heating.hhv_mass, prefs['heating_value_mass']
            )
            lhv_m_val, lhv_m_unit = ResultUnitConverter.convert_heating_value_mass(
                self.heating.lhv_mass, prefs['heating_value_mass']
            )
            
            results.append(("Üst Isıl Değer (HHV)", f"{hhv_m_val:.4f}", hhv_m_unit))
            results.append(("Alt Isıl Değer (LHV)", f"{lhv_m_val:.4f}", lhv_m_unit))
            
            # Volume-based heating values
            hhv_v_val, hhv_v_unit = ResultUnitConverter.convert_heating_value_volume(
                self.heating.hhv_volume, prefs['heating_value_volume']
            )
            wobbe_val, wobbe_unit = ResultUnitConverter.convert_heating_value_volume(
                self.heating.wobbe_index, prefs['heating_value_volume']
            )
            
            results.append(("HHV (Hacimsel)", f"{hhv_v_val:.4f}", hhv_v_unit))
            results.append(("Wobbe İndeksi", f"{wobbe_val:.2f}", wobbe_unit))
            
            # Always show Btu/SCF for reference if not already in that unit
            if prefs['heating_value_volume'] != 'Btu/SCF':
                results.append(("HHV (Endüstriyel)", f"{self.heating.hhv_btu_scf:.2f}", "Btu/SCF"))
        else:
            results.append(("- ISIL DEĞERLER (SCM) -", "", ""))
            results.append(("Hesaplama Yöntemi (HHV/LHV)", "Veri/Yöntem Yok", ""))
            results.append(("Üst Isıl Değer (HHV)", "Hesaplanamadı", "-"))
            results.append(("Alt Isıl Değer (LHV)", "Hesaplanamadı", "-"))
            results.append(("Wobbe İndeksi", "Hesaplanamadı", "-"))
            results.append(("HHV (Endüstriyel)", "Hesaplanamadı", "-"))
        
        # Header - Volume Conversion
        if self.volume_conversion:
            results.append(("- HACİM DÖNÜŞÜMÜ -", "", ""))
            
            vol_act_val, vol_act_unit = ResultUnitConverter.convert_volume(
                self.volume_conversion.actual_volume, prefs['volume']
            )
            mass_val, mass_unit = ResultUnitConverter.convert_mass(
                self.volume_conversion.mass, prefs['mass']
            )
            vol_std_val, vol_std_unit = ResultUnitConverter.convert_volume(
                self.volume_conversion.standard_volume, prefs['volume']
            )
            
            # Add 'S' prefix for standard volume if using m³
            if 'm³' in vol_std_unit:
                vol_std_unit = vol_std_unit.replace('m³', 'Sm³')
            elif 'ft³' in vol_std_unit:
                vol_std_unit = vol_std_unit.replace('ft³', 'SCF')
            
            results.append(("Girilen Hacim (ACM)", f"{vol_act_val:.4f}", vol_act_unit))
            results.append(("Toplam Kütle", f"{mass_val:.4f}", mass_unit))
            results.append(("Standart Hacim (SCM)", f"{vol_std_val:.4f}", vol_std_unit))
            
            # Normal Volume (NCM)
            if self.volume_conversion.normal_volume is not None:
                vol_norm_val, vol_norm_unit = ResultUnitConverter.convert_volume(
                    self.volume_conversion.normal_volume, prefs['volume']
                )
                if 'm³' in vol_norm_unit:
                    vol_norm_unit = 'Nm³'
                
                results.append(("Normal Hacim (NCM)", f"{vol_norm_val:.4f}", vol_norm_unit))
                results.append(("", f"@ 0°C, 101.325 kPa", "(Normal)"))
            elif self.volume_conversion.normal_volume_error:
                results.append(("Normal Hacim (NCM)", "Hesaplanamadı", "-"))
                results.append(("Hata Detayı", self.volume_conversion.normal_volume_error, ""))
        
        # Hydrate Analysis
        if self.hydrate:
            results.append(("- HİDRAT OLUŞUM ANALİZİ -", "", ""))
            
            # Decide units based on unit system
            if unit_sys == UnitSystem.IMPERIAL:
                t_unit = "°F"
                p_unit = "psi(a)"
            else:
                t_unit = "°C"
                p_unit = "bar(a)"
                
            # Convert values
            op_temp_disp = convert_temperature_from_K(self.hydrate.operating_temperature, t_unit)
            op_pres_disp = convert_pressure_from_Pa(self.hydrate.operating_pressure, p_unit)
            
            t_hamm_disp = convert_temperature_from_K(self.hydrate.t_hydrate_hammerschmidt, t_unit)
            t_mot_disp = convert_temperature_from_K(self.hydrate.t_hydrate_motiee, t_unit)
            t_towl_disp = convert_temperature_from_K(self.hydrate.t_hydrate_towler_mokhatab, t_unit)
            t_avg_disp = convert_temperature_from_K(self.hydrate.t_hydrate_average, t_unit)
            
            results.append(("İşletme Sıcaklığı", self._format_float(op_temp_disp, 2), t_unit))
            results.append(("İşletme Basıncı", self._format_float(op_pres_disp, 3), p_unit))
            results.append(("Bağıl Yoğunluk (SG)", f"{self.hydrate.specific_gravity:.4f}", "-"))
            
            results.append(("Hammerschmidt Limit Sıcaklığı", self._format_float(t_hamm_disp, 2), t_unit))
            results.append(("Motiee Limit Sıcaklığı", self._format_float(t_mot_disp, 2), t_unit))
            results.append(("Towler-Mokhatab Limit Sıcaklığı", self._format_float(t_towl_disp, 2), t_unit))
            results.append(("Ortalama Limit Sıcaklığı", self._format_float(t_avg_disp, 2), t_unit))
            
            # Risk messages
            def format_risk(risk_bool: bool) -> str:
                return "RİSK VAR" if risk_bool else "GÜVENLİ"
                
            results.append(("Hammerschmidt Riski", format_risk(self.hydrate.risk_hammerschmidt), ""))
            results.append(("Motiee Riski", format_risk(self.hydrate.risk_motiee), ""))
            results.append(("Towler-Mokhatab Riski", format_risk(self.hydrate.risk_towler_mokhatab), ""))
            results.append(("Hidrat Oluşum Riski (Ortalama)", format_risk(self.hydrate.risk_average), ""))
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.
        
        Returns:
            Dictionary representation of all results
        """
        return self.model_dump()

    @staticmethod
    def _format_float(value: float, decimals: int) -> str:
        """Format finite floats and hide unavailable fallback-only properties."""
        if value is None or not math.isfinite(value):
            return "Hesaplanamadı"
        return f"{value:.{decimals}f}"
    
    model_config = {"frozen": False}
