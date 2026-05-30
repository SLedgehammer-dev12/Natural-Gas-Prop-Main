import pytest
import math
from natural_gas_main.models.calculator import ThermoCalculator, COOLPROP_AVAILABLE
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import HydrateResults, CalculationResult
from natural_gas_main.core.converters import convert_temperature_to_K, convert_pressure_to_Pa

pytestmark = pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp is not installed")


def test_hydrate_calculation_typical_gas():
    # Setup typical natural gas mixture
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=95.0),
            GasComponent(name="Ethane", fraction=3.0),
            GasComponent(name="Propane", fraction=2.0),
        ]
    )

    # Perform calculations using ThermoCalculator
    calc = ThermoCalculator()
    result = calc.calculate_properties(
        mixture=mixture,
        temperature_k=275.15,  # 2 °C
        pressure_pa=4.0e6,      # 40 bar
        backend="SRK"
    )

    assert result.hydrate is not None
    assert result.hydrate.specific_gravity > 0.5
    assert result.hydrate.operating_temperature == 275.15
    assert result.hydrate.operating_pressure == 4.0e6

    # Verify predicted temperatures are in reasonable thermodynamic ranges (typically between 240K and 295K)
    assert 240.0 < result.hydrate.t_hydrate_hammerschmidt < 295.0
    assert 240.0 < result.hydrate.t_hydrate_motiee < 295.0
    assert 240.0 < result.hydrate.t_hydrate_towler_mokhatab < 295.0
    assert 240.0 < result.hydrate.t_hydrate_average < 295.0


def test_hydrate_calculation_values():
    calc = ThermoCalculator()
    
    # Let's test with a pressure of 1e6 Pa (~145 psia) and specific gravity of 0.60
    # and operating temp of 280 K
    temp_k = 280.0
    pres_pa = 1000000.0
    sg = 0.60
    
    res = calc._calculate_hydrate_formation(temp_k, pres_pa, sg)
    
    assert res is not None
    assert res.specific_gravity == pytest.approx(sg)
    assert res.operating_temperature == pytest.approx(temp_k)
    assert res.operating_pressure == pytest.approx(pres_pa)

    # Let's verify our hand calculated values:
    # 1. Hammerschmidt
    # p_psia = 1e6 / 6894.757 = 145.0377
    # t_f_hamm = 8.9 * (145.0377^0.285) - 38.2 = -1.2952 °F
    # t_k_hamm = (-1.2952 - 32) * 5/9 + 273.15 = 254.65 K
    assert res.t_hydrate_hammerschmidt == pytest.approx(254.65, abs=0.5)

    # 2. Motiee
    # t_f_motiee = 27.075 °F -> t_k_motiee = 270.41 K
    assert res.t_hydrate_motiee == pytest.approx(270.41, abs=0.5)

    # 3. Towler & Mokhatab
    # t_f_towler_mokhatab = 33.443 °F -> t_k_towler_mokhatab = 273.95 K
    assert res.t_hydrate_towler_mokhatab == pytest.approx(273.95, abs=0.5)


def test_hydrate_risk_assessment():
    calc = ThermoCalculator()
    pres_pa = 2.0e6  # ~290 psia
    sg = 0.65

    # Run calculation with a very warm operating temperature (310 K = ~37 °C)
    # This should yield no hydrate risk
    warm_res = calc._calculate_hydrate_formation(310.0, pres_pa, sg)
    assert warm_res is not None
    assert not warm_res.risk_hammerschmidt
    assert not warm_res.risk_motiee
    assert not warm_res.risk_towler_mokhatab
    assert not warm_res.risk_average

    # Run calculation with a very cold operating temperature (250 K = -23 °C)
    # This should yield high risk across all models
    cold_res = calc._calculate_hydrate_formation(250.0, pres_pa, sg)
    assert cold_res is not None
    assert cold_res.risk_hammerschmidt
    assert cold_res.risk_motiee
    assert cold_res.risk_towler_mokhatab
    assert cold_res.risk_average


def test_hydrate_invalid_inputs():
    calc = ThermoCalculator()
    
    # 0 or negative pressure
    assert calc._calculate_hydrate_formation(280.0, 0.0, 0.6) is None
    assert calc._calculate_hydrate_formation(280.0, -1000.0, 0.6) is None
    
    # 0 or negative specific gravity
    assert calc._calculate_hydrate_formation(280.0, 1e5, 0.0) is None
    assert calc._calculate_hydrate_formation(280.0, 1e5, -0.6) is None


def test_hydrate_to_display_list():
    hydrate_res = HydrateResults(
        specific_gravity=0.62,
        operating_temperature=285.15,
        operating_pressure=3.0e6,
        t_hydrate_hammerschmidt=268.15,
        t_hydrate_motiee=278.15,
        t_hydrate_towler_mokhatab=280.15,
        t_hydrate_average=275.48,
        risk_hammerschmidt=False,
        risk_motiee=True,
        risk_towler_mokhatab=True,
        risk_average=True
    )

    # Mock standard properties to satisfy model validation
    from natural_gas_main.models.calculation_result import (
        ActualConditionResults, StandardConditionResults
    )
    
    actual = ActualConditionResults(
        temperature=285.15,
        pressure=3.0e6,
        density=25.0,
        molar_mass=0.018,
        compressibility_factor=0.90,
        internal_energy=10.0,
        enthalpy=15.0,
        entropy=2.0,
        cp=2.5,
        cv=1.8
    )

    standard = StandardConditionResults(
        density_std=0.80,
        specific_gravity=0.62,
        reference_temperature=288.15,
        reference_pressure=101325.0
    )

    result = CalculationResult(
        backend_used="SRK",
        actual=actual,
        standard=standard,
        hydrate=hydrate_res
    )

    # Test display list in SI
    display_list_si = result.to_display_list(unit_system="SI")
    
    # Ensure header exists
    has_header = any("- HİDRAT OLUŞUM ANALİZİ -" in row[0] for row in display_list_si)
    assert has_header

    # Ensure operating condition is formatted and contains correct SI units
    op_temp_row = next(row for row in display_list_si if "İşletme Sıcaklığı" in row[0])
    assert op_temp_row[2] == "°C"
    # 285.15 K = 12.0 °C
    assert op_temp_row[1] == "12.00"

    op_pres_row = next(row for row in display_list_si if "İşletme Basıncı" in row[0])
    assert op_pres_row[2] == "bar(a)"
    # 3.0e6 Pa = 30.0 bar
    assert op_pres_row[1] == "30.000"

    # Ensure risks are displayed in Turkish
    risk_motiee_row = next(row for row in display_list_si if "Motiee Riski" in row[0])
    assert risk_motiee_row[1] == "RİSK VAR"

    risk_hamm_row = next(row for row in display_list_si if "Hammerschmidt Riski" in row[0])
    assert risk_hamm_row[1] == "GÜVENLİ"
