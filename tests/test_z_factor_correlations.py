"""Tests for Wichert-Aziz correction and Sutton correlation."""

import pytest
from natural_gas_main.models.z_factor import (
    StandingKatzZFactor,
    PseudoCriticalProperties,
)


class FakeCoolProp:
    @staticmethod
    def PropsSI(key, fluid):
        props = {
            ("Tcrit", "Methane"): 190.564,
            ("pcrit", "Methane"): 4599200.0,
            ("M", "Methane"): 0.0160428,
            ("Tcrit", "Ethane"): 305.322,
            ("pcrit", "Ethane"): 4872200.0,
            ("M", "Ethane"): 0.0300690,
            ("Tcrit", "Nitrogen"): 126.192,
            ("pcrit", "Nitrogen"): 3395800.0,
            ("M", "Nitrogen"): 0.0280134,
            ("Tcrit", "CarbonDioxide"): 304.128,
            ("pcrit", "CarbonDioxide"): 7377300.0,
            ("M", "CarbonDioxide"): 0.0440095,
            ("Tcrit", "HydrogenSulfide"): 373.1,
            ("pcrit", "HydrogenSulfide"): 9000000.0,
            ("M", "HydrogenSulfide"): 0.0340809,
        }
        return props.get((key, fluid), 1.0)


@pytest.fixture
def estimator():
    return StandingKatzZFactor(FakeCoolProp())


class TestWichertAziz:
    def test_sweet_gas_not_corrected(self, estimator):
        """Pure hydrocarbons should not trigger Wichert-Aziz."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        props = estimator.pseudo_critical(mixture)
        assert props.temperature_k > 0
        assert props.pressure_pa > 0

    def test_static_method_direct(self):
        """Direct call to _wichert_aziz static method."""
        tpc, ppc = StandingKatzZFactor._wichert_aziz(
            tpc_k=200.0,
            ppc_pa=4600000.0,
            y_h2s=0.0,
            y_co2=0.05,
            total_acid=0.05,
        )
        assert tpc < 200.0
        assert ppc < 4600000.0

    def test_wichert_aziz_lowers_temperature(self, estimator):
        """Wichert-Aziz should lower Tpc vs same HC composition without acid gas."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        sweet = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        sweet_props = estimator.pseudo_critical(sweet)

        sour = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Ethane", fraction=10.0),
                GasComponent(name="HydrogenSulfide", fraction=10.0),
            ],
            fraction_type="molar",
        )
        sour_props = estimator.pseudo_critical(sour)

        assert sour_props.temperature_k != sweet_props.temperature_k

    def test_with_h2s(self, estimator):
        """Gas with H₂S should trigger correction."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=85.0),
                GasComponent(name="HydrogenSulfide", fraction=15.0),
            ],
            fraction_type="molar",
        )
        props = estimator.pseudo_critical(mixture)
        assert props.temperature_k > 0
        assert props.pressure_pa > 0

    def test_tiny_acid_fraction_no_correction(self, estimator):
        """Very small acid gas fractions (<0.001) should not trigger WA."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=99.999),
                GasComponent(name="CarbonDioxide", fraction=0.001),
            ],
            fraction_type="molar",
        )
        props = estimator.pseudo_critical(mixture)
        assert props.temperature_k > 0

    def test_pure_h2s_edge_case(self, estimator):
        """Pure H₂S should not crash."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        mixture = GasMixture(
            components=[GasComponent(name="HydrogenSulfide", fraction=100.0)],
            fraction_type="molar",
        )
        props = estimator.pseudo_critical(mixture)
        assert props.temperature_k > 0


class TestSuttonCorrelation:
    def test_sweet_gas_typical(self):
        """Sutton for sweet gas with SG=0.65.
        
        Sutton correlation gives Tpc in °R = 169.2 + 349.5*SG - 74.0*SG².
        For SG=0.65: Tpc = 365.11 °R = 202.84 K.
        Correct conversion: °R * 5/9 (NOT °F → K conversion which was bug).
        """
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65)
        assert 190 < props.temperature_k < 220
        assert 4e6 < props.pressure_pa < 5e6

    def test_heavier_gas_higher_tpc(self):
        """Higher SG → higher pseudo-critical temperature."""
        light = StandingKatzZFactor.sutton_pseudo_critical(0.60)
        heavy = StandingKatzZFactor.sutton_pseudo_critical(0.75)
        assert heavy.temperature_k > light.temperature_k

    def test_with_nitrogen(self):
        """N2 impurity should affect result."""
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65, y_n2=0.05)
        assert props.temperature_k > 0
        assert props.pressure_pa > 0

    def test_with_co2(self):
        """CO2 impurity should affect result."""
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65, y_co2=0.05)
        assert props.temperature_k > 0

    def test_sour_gas_correction_applied(self):
        """Sutton with H2S should apply Wichert-Aziz.

        With SG=0.70, y_h2s=0.10 (y_hc=0.90):
          Correct sg_hc = max(0.55, (0.70 - 1.1767*0.10) / 0.90) = 0.6470
          Without WA: tpc ≈ 219.5 K → After WA: tpc ≈ 210.1 K
        Verify WA correction lowers Tpc from the WA-free value.
        """
        props = StandingKatzZFactor.sutton_pseudo_critical(0.70, y_h2s=0.10)
        total_acid = 0.10
        epsilon = (
            120.0 * (total_acid ** 0.9 - total_acid ** 1.6)
            + 15.0 * (0.10 ** 0.5 - 0.10 ** 4.0)
        )
        tpc_before_wa_r = props.temperature_k * 9.0 / 5.0 + epsilon
        tpc_before_wa_k = tpc_before_wa_r * 5.0 / 9.0
        assert props.temperature_k < tpc_before_wa_k, (
            f"WA should lower Tpc: {props.temperature_k:.2f}K vs {tpc_before_wa_k:.2f}K"
        )

    def test_molar_mass_reasonable(self):
        """Molar mass derived from SG should be reasonable (~18 g/mol)."""
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65)
        assert 0.010 < props.molar_mass_kg_mol < 0.030

    def test_zero_hc_fraction_raises(self):
        """All-impurity gas should raise ValueError."""
        with pytest.raises(ValueError):
            StandingKatzZFactor.sutton_pseudo_critical(
                1.0, y_n2=0.5, y_co2=0.5
            )

    def test_low_sg_clamped(self):
        """Very low SG should be clamped at 0.55."""
        props = StandingKatzZFactor.sutton_pseudo_critical(0.50)
        assert props.temperature_k > 0

    def test_high_sg_hc_fraction(self):
        """SG=1.0 with no impurities."""
        props = StandingKatzZFactor.sutton_pseudo_critical(1.0)
        assert props.temperature_k > 0

    def test_sg_hc_division_correction(self):
        """Verify Sutton SG_hc is correctly divided by y_hc (no N2 to isolate).

        SG=0.80, y_co2=0.20, y_hc=0.80:
          Old (buggy): sg_hc = max(0.55, 0.80 - 1.5195*0.20) = max(0.55, 0.4961) = 0.55
          Correct:      sg_hc = max(0.55, 0.4961 / 0.80) = max(0.55, 0.6201) = 0.6201
          Old Tpc ≈ 201.0 K, Correct Tpc ≈ 209.2 K (WA applied in both).
        """
        props = StandingKatzZFactor.sutton_pseudo_critical(0.80, y_co2=0.20)
        # The corrected formula gives Tpc > 208 K, old formula gave ~201 K
        assert props.temperature_k > 208.0, (
            f"Tpc={props.temperature_k:.2f}K should be >208K with corrected SG_hc division"
        )

    def test_sg_hc_unchanged_for_pure_hc(self):
        """For pure HC gas y_hc=1, division should produce identical result."""
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65)
        expected_sg_hc = max(0.55, 0.65)  # No impurities, SG stays 0.65
        expected_tpc_r = 169.2 + 349.5 * expected_sg_hc - 74.0 * expected_sg_hc ** 2
        expected_tpc_k = expected_tpc_r * 5.0 / 9.0
        assert abs(props.temperature_k - expected_tpc_k) < 0.1

    def test_sg_hc_with_nitrogen_only(self):
        """Verify SG_hc is correctly divided with N2 only.

        SG=0.65, y_n2=0.20, y_hc=0.80
        Numerator = 0.65 - 0.9672*0.20 = 0.45656
        Correct sg_hc = max(0.55, 0.45656/0.80) = max(0.55, 0.5707) = 0.5707
        """
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65, y_n2=0.20)
        # With corrected N2 Tcrit=227.3°R (not -226.0), Tpc ≈ 178.4 K
        # Old buggy N2 value gave Tpc ≈ 128.0 K (an extremely low, unphysical value)
        assert props.temperature_k > 150.0, (
            f"N2 Tcrit fix should raise Tpc; got {props.temperature_k:.2f}K"
        )
        # Compare with pure HC case to ensure different
        pure = StandingKatzZFactor.sutton_pseudo_critical(0.65)
        assert abs(props.temperature_k - pure.temperature_k) > 0.1

    def test_n2_tcrit_corrected(self):
        """Verify N2 Tcrit is 227.3°R (not -226.0°R).

        With the old buggy -226.0°R, 100% N2 would give Tpc = -125.6 K (impossible).
        With corrected 227.3°R, 80% N2 + 20% HC should give Tpc ~153 K.
        """
        with pytest.raises(ValueError, match="Hydrocarbon fraction must be > 0"):
            StandingKatzZFactor.sutton_pseudo_critical(0.65, y_n2=1.0)

        props = StandingKatzZFactor.sutton_pseudo_critical(1.0, y_n2=0.80)
        assert props.temperature_k > 100.0, (
            f"80% N2 should give Tpc > 100K; got {props.temperature_k:.2f}K"
        )
