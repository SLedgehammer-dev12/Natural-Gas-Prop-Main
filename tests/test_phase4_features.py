"""Tests for Phase 4 new features.

Covers:
- Fraction auto-normalization (GasMixture.normalize_fractions)
- Gas name fuzzy matching (_fuzzy_match_gas_name)
"""

import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture, COOLPROP_NAME_MAP


class TestNormalizeFractions:
    def test_normalize_already_100(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        normalized = mixture.normalize_fractions()
        assert normalized.total_fraction == pytest.approx(100.0)
        assert normalized.components[0].fraction == pytest.approx(90.0)

    def test_normalize_sums_to_200(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Ethane", fraction=100.0),
            ],
            fraction_type="molar",
        )
        normalized = mixture.normalize_fractions()
        assert normalized.total_fraction == pytest.approx(100.0)
        assert normalized.components[0].fraction == pytest.approx(400.0 / 9)
        assert normalized.components[1].fraction == pytest.approx(500.0 / 9)

    def test_normalize_sums_to_50(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=30.0),
                GasComponent(name="Ethane", fraction=20.0),
            ],
            fraction_type="molar",
        )
        normalized = mixture.normalize_fractions()
        assert normalized.total_fraction == pytest.approx(100.0)
        assert normalized.components[0].fraction == pytest.approx(60.0)
        assert normalized.components[1].fraction == pytest.approx(40.0)

    def test_normalize_does_not_mutate_original(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=50.0),
                GasComponent(name="Ethane", fraction=50.0),
            ],
            fraction_type="molar",
        )
        original_total = mixture.total_fraction
        mixture.normalize_fractions()
        assert mixture.total_fraction == original_total

    def test_normalize_preserves_fraction_type(self):
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="mass",
        )
        normalized = mixture.normalize_fractions()
        assert normalized.fraction_type == "mass"


class TestFuzzyNameMatch:
    def test_butane_matches_n_butane(self):
        result = GasMixture._fuzzy_match_gas_name("butane")
        assert result == "n-Butane"

    def test_methne_matches_methane(self):
        result = GasMixture._fuzzy_match_gas_name("methne")
        assert result == "Methane"

    def test_nitrogen_typo(self):
        result = GasMixture._fuzzy_match_gas_name("nitrogen")
        assert result == "Nitrogen"

    def test_carbon_dioxide_matches(self):
        result = GasMixture._fuzzy_match_gas_name("carbondioxide")
        assert result == "CarbonDioxide"

    def test_completely_unrelated_returns_original(self):
        result = GasMixture._fuzzy_match_gas_name("xyzzy")
        assert result == "xyzzy"

    def test_format_gas_name_uses_fuzzy_fallback(self):
        result = GasMixture._format_gas_name_for_coolprop("Butane")
        assert result == "n-Butane"

    def test_format_gas_name_common_alias(self):
        result = GasMixture._format_gas_name_for_coolprop("n-butane")
        assert result == "n-Butane"
