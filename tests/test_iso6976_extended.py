"""Extended tests for ISO 6976:2016 heating value module."""

import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models import iso6976


class TestIso6976Values:
    def test_methane_absolute_value(self):
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv == pytest.approx(55.575, rel=0.01)
        assert lhv == pytest.approx(50.046, rel=0.01)
        assert hhv > lhv

    def test_ethane_absolute_value(self):
        mixture = GasMixture(
            components=[GasComponent(name="Ethane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv == pytest.approx(51.951, rel=0.01)
        assert lhv == pytest.approx(47.521, rel=0.01)

    def test_propane_via_n_propane_alias(self):
        """Propane names are mapped via _COOLPROP_TO_ISO."""
        mixture = GasMixture(
            components=[GasComponent(name="Propane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv is not None
        assert lhv is not None

    def test_hydrogen_hhv_highest(self):
        mixture = GasMixture(
            components=[GasComponent(name="Hydrogen", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv > 100

    def test_co_no_latent_heat(self):
        """CO produces no water, so HHV == LHV."""
        mixture = GasMixture(
            components=[GasComponent(name="CarbonMonoxide", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv == lhv

    def test_nitrogen_zero_heating_value(self):
        mixture = GasMixture(
            components=[GasComponent(name="Nitrogen", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv == 0.0
        assert lhv == 0.0

    def test_carbon_dioxide_inert(self):
        mixture = GasMixture(
            components=[GasComponent(name="CarbonDioxide", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv == 0.0


class TestIso6976Mixtures:
    def test_two_component_mixture(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert 50 < hhv < 56
        assert 45 < lhv < 55

    def test_mixture_with_inerts(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Nitrogen", fraction=20.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv is not None
        assert hhv < 55.575

    def test_mass_fraction_consistency(self):
        """Mass fraction input should work and produce consistent results."""
        molar = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        hhv_molar, _ = iso6976.calculate_iso6976_heating_values(molar)

        mass = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=86.63),
                GasComponent(name="Ethane", fraction=13.37),
            ],
            fraction_type="mass",
        )
        hhv_mass, _ = iso6976.calculate_iso6976_heating_values(mass)

        assert hhv_molar == pytest.approx(hhv_mass, rel=0.05)

    def test_all_known_gases_compatible(self):
        """All gases in ISO6976_DATA should be compatible."""
        for iso_name in iso6976.ISO6976_DATA:
            for coolprop_name, mapped in iso6976._COOLPROP_TO_ISO.items():
                if mapped == iso_name:
                    import CoolProp.CoolProp as CP
                    from natural_gas_main.models.gas_data import GasMixture as GM
                    cp_formatted = GM._format_gas_name_for_coolprop(iso_name)
                    mixture = GasMixture(
                        components=[GasComponent(name=iso_name, fraction=100.0)],
                        fraction_type="molar",
                    )
                    assert iso6976.is_iso6976_compatible(mixture)
                    break


class TestIso6976EdgeCases:
    def test_unknown_component_returns_none(self):
        mixture = GasMixture(
            components=[GasComponent(name="Neon", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv is None

    def test_partial_unknown_returns_none(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Neon", fraction=10.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
        assert hhv is None

    def test_temperature_correction_not_applied_to_mass_based(self):
        """T_ref should NOT change mass-based HHV/LHV (ISO 6976:2016 §8.3).
        
        Mass-based calorific values are independent of reference temperature.
        Temperature correction applies only to volume-based values.
        """
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv_default, _ = iso6976.calculate_iso6976_heating_values(mixture)
        hhv_hot, _ = iso6976.calculate_iso6976_heating_values(
            mixture, T_ref=400.0
        )
        assert abs(hhv_hot - hhv_default) < 0.001, (
            "Mass-based HHV should NOT change with T_ref"
        )

    def test_compatibility_check_false(self):
        mixture = GasMixture(
            components=[GasComponent(name="Neon", fraction=100.0)],
            fraction_type="molar",
        )
        assert iso6976.is_iso6976_compatible(mixture) is False

    def test_compatibility_check_h2s(self):
        mixture = GasMixture(
            components=[GasComponent(name="HydrogenSulfide", fraction=100.0)],
            fraction_type="molar",
        )
        assert iso6976.is_iso6976_compatible(mixture) is True
