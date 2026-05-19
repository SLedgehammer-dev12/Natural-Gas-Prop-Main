import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.core.exceptions import ValidationError


class TestGasComponent:
    def test_valid_component(self):
        comp = GasComponent(name="Methane", fraction=90.0)
        assert comp.name == "Methane"
        assert comp.fraction == 90.0
        assert comp.to_decimal() == pytest.approx(0.90)

    def test_fraction_above_100_raises(self):
        with pytest.raises(ValueError):
            GasComponent(name="Test", fraction=101.0)

    def test_fraction_negative_raises(self):
        with pytest.raises(ValueError):
            GasComponent(name="Test", fraction=-1.0)

    def test_fraction_zero_raises(self):
        with pytest.raises(ValueError):
            GasComponent(name="Test", fraction=0.0)

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            GasComponent(name="", fraction=50.0)

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError):
            GasComponent(name="   ", fraction=50.0)

    def test_name_is_stripped(self):
        comp = GasComponent(name="  Methane  ", fraction=50.0)
        assert comp.name == "Methane"


class TestGasMixture:
    def test_valid_mixture(self):
        comps = [
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ]
        mixture = GasMixture(components=comps)
        assert mixture.total_fraction == pytest.approx(100.0)
        mixture.validate_total()

    def test_total_not_100_raises(self):
        comps = [GasComponent(name="Methane", fraction=50.0)]
        mixture = GasMixture(components=comps)
        with pytest.raises(ValidationError):
            mixture.validate_total()

    def test_empty_components_raises(self):
        with pytest.raises(ValueError):
            GasMixture(components=[])

    def test_duplicate_names_raises(self):
        comps = [
            GasComponent(name="Methane", fraction=50.0),
            GasComponent(name="methane", fraction=50.0),
        ]
        with pytest.raises(ValueError):
            GasMixture(components=comps)

    def test_over_20_components_raises(self):
        comps = [GasComponent(name=f"Gas{i}", fraction=5.0) for i in range(21)]
        with pytest.raises(ValueError):
            GasMixture(components=comps)

    def test_total_tolerance_accepts_small_deviation(self):
        comps = [
            GasComponent(name="Methane", fraction=99.9999),
            GasComponent(name="Ethane", fraction=0.0001),
        ]
        mixture = GasMixture(components=comps)
        mixture.validate_total()

    def test_coolprop_string_methane_ethane(self):
        comps = [
            GasComponent(name="Methane", fraction=50.0),
            GasComponent(name="Ethane", fraction=50.0),
        ]
        mixture = GasMixture(components=comps)
        assert mixture.to_coolprop_string() == "Methane&Ethane"

    def test_coolprop_string_propane_alias(self):
        comps = [GasComponent(name="Propane", fraction=100.0)]
        mixture = GasMixture(components=comps)
        assert mixture.to_coolprop_string() == "n-Propane"

    def test_mass_fraction_type_accepted(self):
        comps = [GasComponent(name="Methane", fraction=100.0)]
        mixture = GasMixture(components=comps, fraction_type="mass")
        assert mixture.fraction_type == "mass"

    def test_invalid_fraction_type_raises(self):
        comps = [GasComponent(name="Methane", fraction=100.0)]
        with pytest.raises(ValueError):
            GasMixture(components=comps, fraction_type="volume")

    def test_get_gas_names(self):
        comps = [
            GasComponent(name="Methane", fraction=50.0),
            GasComponent(name="Ethane", fraction=50.0),
        ]
        mixture = GasMixture(components=comps)
        assert mixture.get_gas_names() == ["Methane", "Ethane"]

    def test_decimal_fractions(self):
        comps = [
            GasComponent(name="Methane", fraction=60.0),
            GasComponent(name="Ethane", fraction=40.0),
        ]
        mixture = GasMixture(components=comps)
        decimals = mixture.get_decimal_fractions()
        assert decimals == pytest.approx([0.6, 0.4])
