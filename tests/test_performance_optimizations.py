"""
Tests for calculation speed and performance optimizations.

Validates caching behavior, thread pool parallelization, and result consistency.
"""

import time
import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculator import ThermoCalculator


def create_sample_mixture():
    """Create a standard natural gas mixture."""
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=5.0),
            GasComponent(name="Propane", fraction=2.0),
            GasComponent(name="Nitrogen", fraction=2.0),
            GasComponent(name="CarbonDioxide", fraction=1.0),
        ],
        fraction_type="molar"
    )


def test_gas_name_formatting_cached():
    """Test that gas name formatting uses lru_cache."""
    res1 = GasMixture._format_gas_name_for_coolprop("methane")
    res2 = GasMixture._format_gas_name_for_coolprop("methane")
    assert res1 == "Methane"
    assert res1 == res2
    assert hasattr(GasMixture._format_gas_name_for_coolprop, "cache_info")
    info = GasMixture._format_gas_name_for_coolprop.cache_info()
    assert info.hits >= 1


def test_air_density_cached():
    """Test that air density lookup is cached on calculator instance."""
    calc = ThermoCalculator()
    calc._air_density_cache.clear()
    assert len(calc._air_density_cache) == 0

    rho1 = calc._air_density(101325.0, 288.15)
    assert len(calc._air_density_cache) == 1

    rho2 = calc._air_density(101325.0, 288.15)
    assert rho1 == rho2
    assert rho1 > 1.0
    assert len(calc._air_density_cache) == 1


def test_molar_mass_cached():
    """Test that component molar mass is cached on calculator instance."""
    calc = ThermoCalculator()
    calc._molar_mass_cache.clear()
    assert len(calc._molar_mass_cache) == 0

    m1 = calc._get_molar_mass("Methane")
    assert abs(m1 - 0.01604) < 0.001
    assert len(calc._molar_mass_cache) == 1

    m2 = calc._get_molar_mass("Methane")
    assert m1 == m2
    assert len(calc._molar_mass_cache) == 1


def test_phase_envelope_cached():
    """Test that phase envelope is cached by mixture, skipping recomputation on second run."""
    calc = ThermoCalculator()
    mixture = create_sample_mixture()

    calc._phase_envelope_cache.clear()
    assert len(calc._phase_envelope_cache) == 0

    res1 = calc.calculate_properties(
        mixture=mixture,
        temperature_k=293.15,
        pressure_pa=3000000.0,
        backend="SRK"
    )
    assert res1.phase_envelope is not None
    assert len(calc._phase_envelope_cache) == 1

    t_start = time.perf_counter()
    res2 = calc.calculate_properties(
        mixture=mixture,
        temperature_k=300.0,
        pressure_pa=4000000.0,
        backend="SRK"
    )
    t_duration = time.perf_counter() - t_start

    assert res2.phase_envelope is not None
    assert len(calc._phase_envelope_cache) == 1
    assert res1.phase_envelope.temperature_k == res2.phase_envelope.temperature_k
    assert res1.phase_envelope.pressure_pa == res2.phase_envelope.pressure_pa
    assert res1.phase_envelope.critical_t == res2.phase_envelope.critical_t
    assert t_duration < 0.5


def test_repeated_calculation_consistency():
    """Ensure that cached calculations produce identical thermodynamic properties."""
    calc = ThermoCalculator()
    mixture = create_sample_mixture()

    res1 = calc.calculate_properties(mixture, 290.0, 2500000.0, "SRK")
    res2 = calc.calculate_properties(mixture, 290.0, 2500000.0, "SRK")

    assert res1.actual.density == res2.actual.density
    assert res1.actual.compressibility_factor == res2.actual.compressibility_factor
    assert res1.actual.enthalpy == res2.actual.enthalpy
    assert res1.standard.density_std == res2.standard.density_std
    assert res1.heating.hhv_mass == res2.heating.hhv_mass
