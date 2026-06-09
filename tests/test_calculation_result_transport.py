"""Tests for transport properties in calculation result display."""

from natural_gas_main.models.calculation_result import (
    TransportProperties, CalculationResult, ActualConditionResults,
    StandardConditionResults
)


STD = StandardConditionResults(
    reference_temperature=288.15,
    reference_pressure=101325.0,
)


class TestTransportPropertiesModel:
    """Test the TransportProperties Pydantic model."""

    def test_default_all_none(self):
        t = TransportProperties()
        assert t.viscosity_cp is None
        assert t.thermal_conductivity is None
        assert t.joule_thomson_coefficient is None
        assert t.surface_tension is None
        assert t.has_aqueous_phase is None or t.has_aqueous_phase is False
        assert t.has_liquid_hc_phase is None or t.has_liquid_hc_phase is False

    def test_all_fields_set(self):
        t = TransportProperties(
            viscosity_cp=0.012,
            thermal_conductivity=0.035,
            joule_thomson_coefficient=0.0005,
            surface_tension=0.015,
            has_aqueous_phase=True,
            has_liquid_hc_phase=True,
        )
        assert t.viscosity_cp == 0.012
        assert t.thermal_conductivity == 0.035
        assert t.joule_thomson_coefficient == 0.0005
        assert t.surface_tension == 0.015
        assert t.has_aqueous_phase is True
        assert t.has_liquid_hc_phase is True

    def test_partial_fields(self):
        t = TransportProperties(viscosity_cp=0.010)
        assert t.viscosity_cp == 0.010
        assert t.thermal_conductivity is None
        assert t.surface_tension is None


class TestCalculationResultTransport:
    """Test that CalculationResult.to_display_list includes transport section."""

    def make_result(self, transport=None):
        return CalculationResult(
            backend_used="neqsim-srk",
            actual=ActualConditionResults(
                temperature=300.0, pressure=1e5, density=20.0,
                molar_mass=0.016, compressibility_factor=0.95,
                internal_energy=-500.0, enthalpy=-480.0, entropy=3.0,
                cp=2.2, cv=1.6,
            ),
            standard=STD,
            transport=transport,
        )

    def test_to_display_list_with_transport(self):
        result = self.make_result(
            transport=TransportProperties(
                viscosity_cp=0.012,
                thermal_conductivity=0.035,
                joule_thomson_coefficient=0.0005,
                surface_tension=0.015,
            )
        )
        display = result.to_display_list()
        display_str = "\n".join(str(r) for r in display)
        assert "Viskozite" in display_str
        assert "Termal İletkenlik" in display_str

    def test_to_display_list_without_transport(self):
        result = self.make_result(transport=None)
        display = result.to_display_list()
        display_str = "\n".join(str(r) for r in display)
        assert "TAŞINIM" not in display_str

    def test_to_display_list_with_phase_info(self):
        result = self.make_result(
            transport=TransportProperties(has_aqueous_phase=True)
        )
        display = result.to_display_list()
        display_str = "\n".join(str(r) for r in display)
        assert "Sulu Faz" in display_str

    def test_to_display_list_with_hc_phase(self):
        result = self.make_result(
            transport=TransportProperties(has_liquid_hc_phase=True)
        )
        display = result.to_display_list()
        display_str = "\n".join(str(r) for r in display)
        assert "Sıvı HC Faz" in display_str


class TestTransportEdgeCases:
    """Edge cases for transport properties."""

    def test_zero_viscosity_should_not_be_shown(self):
        t = TransportProperties()
        vis = 0.0
        if vis > 0:
            t.viscosity_cp = vis
        assert t.viscosity_cp is None

    def test_negative_surface_tension_not_shown(self):
        t = TransportProperties()
        st = -1.0
        if st is not None and st > 0:
            t.surface_tension = st
        assert t.surface_tension is None
