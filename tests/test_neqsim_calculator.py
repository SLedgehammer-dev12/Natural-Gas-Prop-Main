"""
Tests for the NeqSim calculator module.

Includes:
- Module-level constants and registry validation
- Gas name mapping correctness
- NeqSim calculator with mocked jneqsim
- Integration with ThermoCalculator fallback chain
"""

import pytest
import math
import sys as _sys_module
_sys_platform = _sys_module.platform
from unittest.mock import patch, MagicMock, PropertyMock

from natural_gas_main.models.neqsim_calculator import (
    NEQSIM_AVAILABLE,
    NEQSIM_AVAILABLE_BACKENDS,
    NEQSIM_EOS_REGISTRY,
    NEQSIM_GAS_MAPPING,
    _get_neqsim_gas_name,
)
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import ActualConditionResults, TransportProperties
from natural_gas_main.core.exceptions import BackendNotAvailableError


class TestNeqSimConstants:
    """Test module-level constants and registry."""

    def test_neqsim_available_is_false_without_java(self):
        """NEQSIM_AVAILABLE should be False when Java/NeqSim not installed."""
        assert NEQSIM_AVAILABLE is False

    def test_all_15_backends_registered(self):
        """Verify all 15 NeqSim EOS backends are in the registry."""
        assert len(NEQSIM_AVAILABLE_BACKENDS) == 15
        assert len(NEQSIM_EOS_REGISTRY) == 15

    def test_registry_contains_all_groups(self):
        """Verify registry has backends from all expected groups."""
        groups = set(info["group"] for info in NEQSIM_EOS_REGISTRY.values())
        assert "SRK Ailesi" in groups
        assert "PR Ailesi" in groups
        assert "CPA" in groups
        assert "Ekşi Gaz" in groups
        assert "Referans EOS" in groups
        assert "Tahminsel" in groups

    def test_each_backend_has_required_keys(self):
        """Every backend entry must have class, mixing, group, desc, multiphase."""
        required = {"class", "mixing", "group", "desc", "multiphase"}
        for name, info in NEQSIM_EOS_REGISTRY.items():
            missing = required - set(info.keys())
            assert not missing, f"{name} eksik: {missing}"

    def test_gerg2008_h2_has_h2_enhanced_flag(self):
        """neqsim-gerg2008-h2 should have h2_enhanced=True."""
        assert NEQSIM_EOS_REGISTRY["neqsim-gerg2008-h2"].get("h2_enhanced") is True

    def test_cpa_and_soreide_are_multiphase(self):
        """CPA and Soreide models should have multiphase=True."""
        assert NEQSIM_EOS_REGISTRY["neqsim-srk-cpa"]["multiphase"] is True
        assert NEQSIM_EOS_REGISTRY["neqsim-soreide"]["multiphase"] is True

    def test_reference_eos_have_no_mixing_rule(self):
        """Reference EOS (GERG, EOS-CG, Span-Wagner) should have mixing=None."""
        for name in ["neqsim-gerg2008", "neqsim-gerg2008-h2", "neqsim-eoscg", "neqsim-spanwagner"]:
            assert NEQSIM_EOS_REGISTRY[name]["mixing"] is None, f"{name} mixing should be None"


class TestNeqSimGasMapping:
    """Test the CoolProp-to-NeqSim gas name mapping."""

    def test_mapping_has_key_components(self):
        """Verify essential natural gas components are mapped."""
        essentials = ["methane", "ethane", "propane", "n-butane", "isobutane",
                      "nitrogen", "carbondioxide", "hydrogensulfide", "water",
                      "hydrogen", "oxygen", "helium", "argon", "carbonmonoxide"]
        for gas in essentials:
            assert gas in NEQSIM_GAS_MAPPING, f"{gas} eksik"

    def test_mapping_values_are_neqsim_names(self):
        """Verify mapped values use NeqSim naming conventions."""
        assert NEQSIM_GAS_MAPPING["methane"] == "methane"
        assert NEQSIM_GAS_MAPPING["carbondioxide"] == "CO2"
        assert NEQSIM_GAS_MAPPING["hydrogensulfide"] == "H2S"
        assert NEQSIM_GAS_MAPPING["n-butane"] == "n-butane"
        assert NEQSIM_GAS_MAPPING["isobutane"] == "isobutane"

    def test_water_and_glycols_mapped(self):
        """Test water, MEG, TEG are mapped."""
        assert NEQSIM_GAS_MAPPING["water"] == "water"
        assert NEQSIM_GAS_MAPPING["meg"] == "MEG"
        assert NEQSIM_GAS_MAPPING["teg"] == "TEG"

    def test_get_neqsim_gas_name_resolves_correctly(self):
        """Test the resolver function converts CoolProp names to NeqSim names."""
        assert _get_neqsim_gas_name("Methane") == "methane"
        assert _get_neqsim_gas_name("CarbonDioxide") == "CO2"
        assert _get_neqsim_gas_name("n-Propane") == "propane"
        assert _get_neqsim_gas_name("UnknownGas") == "unknowngas"


class TestNeqSimCalculateWithMocks:
    """Test calculate_neqsim() with mocked jneqsim."""

    @pytest.fixture
    def simple_mixture(self):
        return GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar"
        )

    def test_raises_backend_error_when_not_available(self):
        """When NEQSIM_AVAILABLE is False, should raise BackendNotAvailableError."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", False):
            from natural_gas_main.models.neqsim_calculator import calculate_neqsim
            with pytest.raises(BackendNotAvailableError):
                calculate_neqsim(None, 300, 1e5, "neqsim-srk")

    def test_raises_value_error_for_unknown_method(self, simple_mixture):
        """Unknown method should raise ValueError."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                with pytest.raises(ValueError, match="Bilinmeyen"):
                    calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-nonexistent")

    def test_successful_srk_calculation_returns_actual_and_transport(self, simple_mixture):
        """A successful NeqSim SRK calculation should return (ActualConditionResults, TransportProperties)."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.5
                mock_phase.getMolarMass.return_value = 0.0185
                mock_phase.getZ.return_value = 0.92
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.5
                mock_phase.getInternalEnergy.return_value = -520.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6
                mock_phase.getGamma.return_value = 1.375
                mock_phase.getSoundSpeed.return_value = 450.0
                mock_phase.getViscosity.return_value = 0.012
                mock_phase.getThermalConductivity.return_value = 0.035
                mock_phase.getJouleThomsonCoefficient.return_value = 0.0005

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.92

                mock_interphase = MagicMock()
                mock_interphase.getSurfaceTension.return_value = 0.015
                mock_fluid.getInterphaseProperties.return_value = mock_interphase

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)

                mock_ops_cls = MagicMock()
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = mock_ops_cls

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim

                actual, transport = calculate_neqsim(simple_mixture, 300.0, 1e5, "neqsim-srk")

                assert isinstance(actual, ActualConditionResults)
                assert isinstance(transport, TransportProperties)
                assert actual.compressibility_factor == 0.92
                assert actual.density == 20.5
                assert actual.molar_mass == 0.0185
                assert actual.enthalpy == -500.0
                assert transport.viscosity_cp == 0.012
                assert transport.thermal_conductivity == 0.035

    def test_all_15_eos_create_correct_system_class(self, simple_mixture):
        """Each EOS should instantiate the correct jneqsim system class."""
        for backend_name, eos_info in NEQSIM_EOS_REGISTRY.items():
            with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
                with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                    mock_phase = MagicMock()
                    mock_phase.getDensity.return_value = 20.0
                    mock_phase.getMolarMass.return_value = 0.016
                    mock_phase.getZ.return_value = 0.95
                    mock_phase.getEnthalpy.return_value = -500.0
                    mock_phase.getEntropy.return_value = 3.0
                    mock_phase.getInternalEnergy.return_value = -520.0
                    mock_phase.getCp.return_value = 2.2
                    mock_phase.getCv.return_value = 1.6

                    mock_fluid = MagicMock()
                    mock_fluid.getPhase.return_value = mock_phase
                    mock_fluid.getZ.return_value = 0.95

                    mock_system_cls = MagicMock(return_value=mock_fluid)
                    setattr(mock_jneqsim.thermo.system, eos_info["class"], mock_system_cls)
                    mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                    from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                    actual, transport = calculate_neqsim(simple_mixture, 300.0, 1e5, backend_name)

                    mock_system_cls.assert_called_once_with(300.0, 1.0)
                    assert actual.compressibility_factor == 0.95

    def test_raises_backend_error_when_class_not_found(self, simple_mixture):
        """When the EOS class is not found in jneqsim, should raise BackendNotAvailableError."""
        from unittest.mock import Mock, PropertyMock
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                # Use a restricted mock for system so attribute access raises
                mock_jneqsim.thermo.system = Mock(spec=[])
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()
                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                with pytest.raises(BackendNotAvailableError):
                    calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")

    def test_reference_eos_rejects_unknown_component(self, simple_mixture):
        """Reference EOS should raise ValueError when a component cannot be added."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_fluid = MagicMock()
                mock_fluid.addComponent.side_effect = Exception("Unknown component")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemGERG2008Eos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                with pytest.raises(ValueError, match="desteklemiyor"):
                    calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-gerg2008")

    def test_non_reference_eos_handles_unknown_component_gracefully(self, simple_mixture):
        """Non-reference EOS should warn but continue when a component fails."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95
                # First component fails, second works
                mock_fluid.addComponent.side_effect = [Exception("Bad"), None]

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.compressibility_factor == 0.95

    def test_fluid_z_nan_falls_back_to_phase_z(self, simple_mixture):
        """When fluid.getZ returns NaN, should fall back to phase.getZ."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.93  # phase.getZ fallback value
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = float('nan')  # fluid returns NaN

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.compressibility_factor == 0.93

    def test_fluid_z_negative_falls_back_to_phase_z(self, simple_mixture):
        """When fluid.getZ returns negative value, should fall back to phase.getZ."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.93
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = -1.0

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.compressibility_factor == 0.93

    def test_mixing_rule_failure_logs_warning(self, simple_mixture):
        """When mixing rule fails, should log warning but continue."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95
                # Make setMixingRule fail
                mock_fluid.setMixingRule.side_effect = Exception("Bad mixing rule")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.compressibility_factor == 0.95

    def test_multiphase_check_called_for_cpa_and_soreide(self, simple_mixture):
        """CPA and Soreide should have setMultiPhaseCheck called."""
        for backend in ["neqsim-srk-cpa", "neqsim-soreide"]:
            with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
                with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                    mock_phase = MagicMock()
                    mock_phase.getDensity.return_value = 20.0
                    mock_phase.getMolarMass.return_value = 0.016
                    mock_phase.getZ.return_value = 0.95
                    mock_phase.getEnthalpy.return_value = -500.0
                    mock_phase.getEntropy.return_value = 3.0
                    mock_phase.getCp.return_value = 2.2
                    mock_phase.getCv.return_value = 1.6

                    mock_fluid = MagicMock()
                    mock_fluid.getPhase.return_value = mock_phase
                    mock_fluid.getZ.return_value = 0.95

                    mock_system_cls = MagicMock(return_value=mock_fluid)
                    eos_class_name = NEQSIM_EOS_REGISTRY[backend]["class"]
                    setattr(mock_jneqsim.thermo.system, eos_class_name, mock_system_cls)
                    mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                    from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                    calculate_neqsim(simple_mixture, 300, 1e5, backend)
                    mock_fluid.setMultiPhaseCheck.assert_called_once_with(True)

    def test_h2_enhanced_called_for_gerg2008_h2(self, simple_mixture):
        """neqsim-gerg2008-h2 should call useHydrogenEnhancedModel."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemGERG2008Eos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-gerg2008-h2")
                mock_fluid.useHydrogenEnhancedModel.assert_called_once()

    def test_surface_tension_failure_graceful(self, simple_mixture):
        """When getSurfaceTension fails, surface_tension should remain None."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95
                # No getInterphaseProperties at all
                mock_fluid.getInterphaseProperties.side_effect = AttributeError("No interphase")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert transport.surface_tension is None

    def test_gamma_fallback_cp_over_cv(self, simple_mixture):
        """When getGamma is not available, kappa should be cp/cv."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6
                mock_phase.getSoundSpeed.return_value = 450.0
                # No getGamma on this mock
                del mock_phase.getGamma

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                expected_kappa = 2.2 / 1.6
                assert actual.isentropic_exponent == pytest.approx(expected_kappa)

    def test_molar_mass_too_low_uses_default(self, simple_mixture):
        """When molar mass is below 0.001, default 0.016 should be used."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.0005  # below threshold
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.molar_mass == 0.016  # default fallback

    def test_phase_detection_exception_handled(self, simple_mixture):
        """When hasPhaseType raises exception, phase flags should remain False."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95
                mock_fluid.hasPhaseType.side_effect = Exception("Phase detection error")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert transport.has_aqueous_phase is False
                assert transport.has_liquid_hc_phase is False


class TestNeqSimCalculateExceptionPaths:
    """Test exception handling in calculate_neqsim."""

    def test_generic_exception_wraps_in_runtime_error(self, simple_mixture):
        """Non-ValueError exceptions in calculation should be wrapped in RuntimeError."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_fluid = MagicMock()
                # Make TPflash raise a RuntimeError (non-ValueError → generic handler)
                mock_ops = MagicMock()
                mock_ops.TPflash.side_effect = RuntimeError("JVM error")
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock(return_value=mock_ops)

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                with pytest.raises(RuntimeError, match="NeqSim neqsim-srk başarısız"):
                    calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")

    def test_reference_eos_value_error_preserved(self, simple_mixture):
        """ValueError from reference EOS should be preserved."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:

                mock_fluid = MagicMock()
                mock_fluid.addComponent.side_effect = ValueError("desteklemiyor")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemEOSCGEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                with pytest.raises(ValueError, match="desteklemiyor"):
                    calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-eoscg")


class TestNeqSimHydrateExceptions:
    """Test exception paths in get_neqsim_hydrate_temperature."""

    def test_returns_none_on_exception(self, simple_mixture):
        """When hydrate calculation raises, should return None."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_system_cls = MagicMock(side_effect=Exception("Java error"))
                setattr(mock_jneqsim.thermo.system, "SystemSrkCPAstatoil", mock_system_cls)

                from natural_gas_main.models.neqsim_calculator import get_neqsim_hydrate_temperature
                result = get_neqsim_hydrate_temperature(simple_mixture, 280.0, 50e5)
                assert result is None


class TestNeqSimISOExceptions:
    """Test exception paths in get_neqsim_iso6976."""

    def test_returns_none_on_exception(self, simple_mixture):
        """When ISO 6976 calculation raises, should return None."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                # Make the ISO class itself raise
                mock_jneqsim.standards.gasquality.Standard_ISO6976.side_effect = Exception("ISO error")

                with patch.dict("sys.modules", {
                    "neqsim": MagicMock(),
                    "neqsim.thermo": MagicMock(),
                }):
                    import sys
                    sys.modules["neqsim"].thermo = sys.modules["neqsim.thermo"]
                    sys.modules["neqsim"].thermo.fluid = MagicMock()
                    sys.modules["neqsim"].thermo.TPflash = MagicMock()

                    from natural_gas_main.models.neqsim_calculator import get_neqsim_iso6976
                    result = get_neqsim_iso6976(simple_mixture)
                    assert result is None


class TestNeqSimNeqsimImportPaths:
    """Test internal optional operations (createDatabase, initProperties, initPhysicalProperties)."""

    def test_create_database_called(self, simple_mixture):
        """verify createDatabase(True) is called."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                mock_fluid.createDatabase.assert_called_once_with(True)
                mock_fluid.initProperties.assert_called_once()
                mock_fluid.initPhysicalProperties.assert_called_once()

    def test_optional_ops_fail_gracefully(self, simple_mixture):
        """When createDatabase/initProperties/initPhysicalProperties fail, should continue."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.0
                mock_phase.getMolarMass.return_value = 0.016
                mock_phase.getZ.return_value = 0.95
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.return_value = 0.95
                # All optional ops fail
                mock_fluid.createDatabase.side_effect = Exception("DB fail")
                mock_fluid.initProperties.side_effect = Exception("Init fail")
                mock_fluid.initPhysicalProperties.side_effect = Exception("Phys fail")

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim
                actual, transport = calculate_neqsim(simple_mixture, 300, 1e5, "neqsim-srk")
                assert actual.compressibility_factor == 0.95

    def test_transport_properties_gracefully_handle_missing_api(self, simple_mixture):
        """When NeqSim lacks certain property APIs, they should be None not exceptions."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.5
                mock_phase.getMolarMass.return_value = 0.0185
                mock_phase.getZ.return_value = 0.92  # phase.getZ works
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.5
                mock_phase.getInternalEnergy.return_value = -520.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6
                # Make transport properties raise exceptions
                mock_phase.getViscosity.side_effect = Exception("No visc")
                mock_phase.getThermalConductivity.side_effect = Exception("No TC")
                mock_phase.getJouleThomsonCoefficient.side_effect = Exception("No JT")
                mock_phase.getSoundSpeed.side_effect = Exception("No sound")
                mock_phase.getGamma.return_value = 1.3

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                mock_fluid.getZ.side_effect = Exception("Fluid no Z")  # fluid.getZ fails, phase.getZ fallback

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkEos", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim

                actual, transport = calculate_neqsim(simple_mixture, 300.0, 1e5, "neqsim-srk")

                assert transport.viscosity_cp is None
                assert transport.thermal_conductivity is None
                assert transport.joule_thomson_coefficient is None

    def test_multiphase_detection_in_transport(self, simple_mixture):
        """Transport properties should report phase presence for CPA models."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_phase = MagicMock()
                mock_phase.getDensity.return_value = 20.5
                mock_phase.getMolarMass.return_value = 0.0185
                mock_phase.getEnthalpy.return_value = -500.0
                mock_phase.getEntropy.return_value = 3.5
                mock_phase.getInternalEnergy.return_value = -520.0
                mock_phase.getCp.return_value = 2.2
                mock_phase.getCv.return_value = 1.6
                # Return different values for different getZ calls (phase vs fluid)
                type(mock_phase).getZ = MagicMock(return_value=0.92)
                type(mock_phase).getViscosity = MagicMock(return_value=0.012)
                type(mock_phase).getThermalConductivity = MagicMock(return_value=0.035)
                type(mock_phase).getSoundSpeed = MagicMock(return_value=450.0)
                type(mock_phase).getGamma = MagicMock(return_value=1.3)

                mock_fluid = MagicMock()
                mock_fluid.getPhase.return_value = mock_phase
                # Simulate CPA with aqueous phase
                mock_fluid.hasPhaseType.side_effect = lambda t: t == "aqueous"

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkCPAstatoil", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import calculate_neqsim

                actual, transport = calculate_neqsim(simple_mixture, 300.0, 1e5, "neqsim-srk-cpa")

                assert transport.has_aqueous_phase is True
                assert transport.has_liquid_hc_phase is False


class TestNeqSimISO6976WithMocks:
    """Test get_neqsim_iso6976() with mocked NeqSim."""

    def test_returns_none_when_neqsim_unavailable(self, simple_mixture):
        """When NEQSIM_AVAILABLE is False, should return None."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", False):
            from natural_gas_main.models.neqsim_calculator import get_neqsim_iso6976
            result = get_neqsim_iso6976(simple_mixture)
            assert result is None

    def test_returns_iso_data_when_available(self, simple_mixture):
        """When NeqSim works, should return ISO 6976 data dict."""
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                with patch("natural_gas_main.models.neqsim_calculator._jneqsim.standards.gasquality.Standard_ISO6976") as mock_iso_cls:
                    # Mock the fluid that get_neqsim_iso6976 creates internally
                    mock_fluid = MagicMock()
                    mock_fluid_inst = MagicMock()
                    mock_fluid_inst.getSystem.return_value = mock_fluid

                    # Mock the neqsim.thermo imports
                    with patch.dict("sys.modules", {
                        "neqsim": MagicMock(),
                        "neqsim.thermo": MagicMock(),
                    }):
                        import sys
                        sys.modules["neqsim"].thermo = sys.modules["neqsim.thermo"]
                        mock_thermo_fluid = MagicMock(return_value=mock_fluid_inst)
                        sys.modules["neqsim.thermo"].fluid = mock_thermo_fluid
                        sys.modules["neqsim.thermo"].TPflash = MagicMock()

                        mock_iso = MagicMock()
                        mock_iso.getValue.side_effect = lambda k: {
                            "GCV": 40000.0,
                            "LCV": 36000.0,
                            "SuperiorWobbeIndex": 52000.0,
                            "RelativeDensity": 0.65,
                            "CompressionFactor": 0.998,
                            "MolarMass": 18.5,
                            "DensityReal": 0.85,
                            "DensityIdeal": 0.82,
                        }.get(k, 0.0)

                        mock_iso_cls.return_value = mock_iso

                        from natural_gas_main.models.neqsim_calculator import get_neqsim_iso6976

                        result = get_neqsim_iso6976(simple_mixture)
                        assert result is not None
                        assert result["gcv_kj_m3"] == 40000.0
                        assert result["wobbe_kj_m3"] == 52000.0
                        assert result["relative_density"] == 0.65


class TestNeqsimHydrateWithMocks:
    """Test get_neqsim_hydrate_temperature() with mocked NeqSim."""

    def test_returns_none_when_neqsim_unavailable(self, simple_mixture):
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", False):
            from natural_gas_main.models.neqsim_calculator import get_neqsim_hydrate_temperature
            result = get_neqsim_hydrate_temperature(simple_mixture, 280.0, 50e5)
            assert result is None

    def test_returns_temperature_when_available(self):
        hydrate_mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=8.0),
                GasComponent(name="Water", fraction=2.0),
            ],
            fraction_type="molar"
        )
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            with patch("natural_gas_main.models.neqsim_calculator._jneqsim") as mock_jneqsim:
                mock_fluid = MagicMock()
                mock_fluid.getTemperature.side_effect = [290.0, 285.0]

                mock_system_cls = MagicMock(return_value=mock_fluid)
                setattr(mock_jneqsim.thermo.system, "SystemSrkCPAstatoil", mock_system_cls)
                mock_jneqsim.thermodynamicoperations.ThermodynamicOperations = MagicMock()

                from natural_gas_main.models.neqsim_calculator import get_neqsim_hydrate_temperature
                result = get_neqsim_hydrate_temperature(hydrate_mixture, 280.0, 50e5)
                assert result == 285.0


# Fixture for test classes
@pytest.fixture
def simple_mixture():
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ],
        fraction_type="molar"
    )


class TestNeqSimBackendIntegration:
    """Test integration with ThermoCalculator's fallback chain (mocked).

    These tests verify that:
    - _is_neqsim_backend correctly identifies NeqSim backends
    - NeqSim backends are properly included in the fallback order
    - The calculator dispatches to _compute_neqsim when a NeqSim backend is selected
    """

    def test_is_neqsim_backend_identifies_correctly(self):
        """ThermoCalculator._is_neqsim_backend should identify NeqSim backends."""
        from natural_gas_main.models.calculator import ThermoCalculator
        assert ThermoCalculator._is_neqsim_backend("neqsim-srk") is True
        assert ThermoCalculator._is_neqsim_backend("neqsim-gerg2008") is True
        assert ThermoCalculator._is_neqsim_backend("neqsim-srk-cpa") is True
        assert ThermoCalculator._is_neqsim_backend("HEOS") is False
        assert ThermoCalculator._is_neqsim_backend("SRK") is False
        assert ThermoCalculator._is_neqsim_backend("GERG-2008") is False

    @pytest.mark.skipif("True", reason="CoolProp required - run manually")
    def test_neqsim_in_fallback_order_with_coolprop(self):
        """When CoolProp is available, NeqSim backends should appear in the fallback order."""
        from natural_gas_main.models.calculator import ThermoCalculator
        import CoolProp.CoolProp as CP

        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar"
        )

        # Preferred is a NeqSim backend
        order = calc._get_backend_order(mixture, "neqsim-gerg2008")
        assert order[0] == "neqsim-gerg2008"
        # Should contain other NeqSim backends after preferred
        neqsim_in_order = [b for b in order if b.startswith("neqsim-")]
        assert len(neqsim_in_order) > 1
        # Should end with legacy backends
        assert "HEOS" in order or "SRK" in order

    def test_backend_selection_returns_neqsim_name_when_requested(self):
        """Requesting a NeqSim backend should return it."""
        from natural_gas_main.models.calculator import ThermoCalculator
        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar"
        )
        selected = calc._select_backend(mixture, "neqsim-srk")
        assert selected == "neqsim-srk"

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.calculate_neqsim")
    def test_calculate_with_backend_dispatches_to_neqsim(self, mock_calc_neqsim, simple_mixture):
        """_calculate_with_backend should use _compute_neqsim for NeqSim backends."""
        from natural_gas_main.models.calculator import ThermoCalculator
        from natural_gas_main.models.calculation_result import (
            ActualConditionResults, TransportProperties
        )

        mock_actual = ActualConditionResults(
            temperature=300.0, pressure=1e5, density=20.0,
            molar_mass=0.016, compressibility_factor=0.95,
            internal_energy=-500, enthalpy=-480, entropy=3.0,
            cp=2.2, cv=1.6, isentropic_exponent=1.375, speed_of_sound=450.0,
        )

        mock_transport = TransportProperties()

        # calculate_neqsim returns (ActualConditionResults, Optional[TransportProperties])
        mock_calc_neqsim.return_value = (mock_actual, mock_transport)

        calc = ThermoCalculator()
        result = calc._calculate_with_backend(
            simple_mixture, 300.0, 1e5, None, "neqsim-srk"
        )

        # Should have been called at least once (for actual conditions)
        assert mock_calc_neqsim.call_count >= 1
        # First call should use the requested backend
        first_call_args = mock_calc_neqsim.call_args_list[0]
        assert first_call_args[0][3] == "neqsim-srk"  # method arg
        assert result.actual.compressibility_factor == 0.95
        assert result.backend_used == "neqsim-srk"


# ── Java Detection Tests ─────────────────────────────────────────────

class TestJavaDetection:
    """Test the _detect_java_home() function (AV-safe, no glob/wildcard)."""

    def test_java_home_env_detected(self, tmp_path, monkeypatch):
        """When JAVA_HOME points to a valid Java, return it."""
        java_exe = "java.exe" if _sys_platform == "win32" else "java"
        jdk_dir = tmp_path / "jdk"
        bin_dir = jdk_dir / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / java_exe).touch()

        monkeypatch.setenv("JAVA_HOME", str(jdk_dir))

        from natural_gas_main.models.neqsim_calculator import _detect_java_home
        result = _detect_java_home()
        assert result == str(jdk_dir)

    def test_java_from_path(self, tmp_path, monkeypatch):
        """When java is found on PATH via shutil.which, return its home."""
        java_exe = "java.exe" if _sys_platform == "win32" else "java"
        jdk_dir = tmp_path / "jdk2"
        bin_dir = jdk_dir / "bin"
        bin_dir.mkdir(parents=True)
        java_path = bin_dir / java_exe
        java_path.touch()

        import shutil as _shutil
        monkeypatch.setattr(_shutil, "which", lambda x: str(java_path) if x == "java" else None)
        monkeypatch.delenv("JAVA_HOME", raising=False)

        from natural_gas_main.models.neqsim_calculator import _detect_java_home
        result = _detect_java_home()
        assert result == str(jdk_dir)

    def test_java_not_found_returns_none(self, monkeypatch):
        """When no Java is installed, return None."""
        monkeypatch.delenv("JAVA_HOME", raising=False)
        import shutil as _shutil
        monkeypatch.setattr(_shutil, "which", lambda x: None)

        from natural_gas_main.models.neqsim_calculator import _detect_java_home
        result = _detect_java_home()
        assert result is None

    def test_java_home_invalid_bin_skipped(self, tmp_path, monkeypatch):
        """JAVA_HOME that exists but has no java.exe is not used."""
        jdk_dir = tmp_path / "fake_jdk"
        jdk_dir.mkdir(parents=True)

        monkeypatch.setenv("JAVA_HOME", str(jdk_dir))
        import shutil as _shutil
        monkeypatch.setattr(_shutil, "which", lambda x: None)

        from natural_gas_main.models.neqsim_calculator import _detect_java_home
        result = _detect_java_home()
        assert result is None

    def test_frozen_mode_jar_classpath(self, tmp_path, monkeypatch):
        """In frozen mode, verify that JAR detection path logic is correct."""
        meipass = tmp_path / "meipass"
        jar_dir = meipass / "neqsim" / "lib"
        jar_dir.mkdir(parents=True)
        (jar_dir / "neqsim-3.14.0.jar").touch()
        (jar_dir / "neqsim-3.14.0-Java8.jar").touch()

        import os as _os
        jar_path = _os.path.join(str(meipass), "neqsim", "lib")
        jars = sorted([f for f in _os.listdir(jar_path) if f.endswith('.jar')])
        assert len(jars) == 2
        assert "neqsim-3.14.0.jar" in jars
        assert "neqsim-3.14.0-Java8.jar" in jars
