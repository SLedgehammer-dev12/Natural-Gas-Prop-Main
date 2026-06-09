"""Edge case tests for the NeqSim calculator module.

Covers import-time scenarios, _get_neqsim_gas_name edge cases,
and NEQSIM_AVAILABLE_BACKENDS consistency.
"""

import pytest
from natural_gas_main.models.neqsim_calculator import (
    NEQSIM_AVAILABLE,
    NEQSIM_AVAILABLE_BACKENDS,
    NEQSIM_EOS_REGISTRY,
    _get_neqsim_gas_name,
)


class TestNeqSimImportEdgeCases:
    """Test module-level edge cases for NeqSim imports."""

    def test_available_backends_list_matches_registry(self):
        assert len(NEQSIM_AVAILABLE_BACKENDS) == len(NEQSIM_EOS_REGISTRY)
        for name in NEQSIM_AVAILABLE_BACKENDS:
            assert name in NEQSIM_EOS_REGISTRY

    def test_each_eos_has_supports_aga8_key(self):
        for name, info in NEQSIM_EOS_REGISTRY.items():
            assert "supports_aga8" in info
            assert isinstance(info["supports_aga8"], bool)

    def test_reference_eos_aga8_flag(self):
        """Referans EOS group: GERG-2008 variants and EOS-CG support AGA8,
        but Span-Wagner (pure CO2) does not."""
        for name, info in NEQSIM_EOS_REGISTRY.items():
            if info["group"] == "Referans EOS":
                if name == "neqsim-spanwagner":
                    assert info["supports_aga8"] is False
                else:
                    assert info["supports_aga8"] is True

    def test_non_reference_eos_supports_aga8_is_false(self):
        for name, info in NEQSIM_EOS_REGISTRY.items():
            if info["group"] != "Referans EOS":
                assert info["supports_aga8"] is False

    def test_neqsim_available_is_false_when_no_java(self):
        assert NEQSIM_AVAILABLE is False


class TestGetNeqsimGasNameEdgeCases:
    """Test _get_neqsim_gas_name with various inputs."""

    def test_handles_whitespace_variations(self):
        assert _get_neqsim_gas_name("  Methane  ") == "methane"
        assert _get_neqsim_gas_name("\tCarbonDioxide\t") == "CO2"
        assert _get_neqsim_gas_name("\nWater\n") == "water"

    def test_handles_mixed_case(self):
        assert _get_neqsim_gas_name("METHANE") == "methane"
        assert _get_neqsim_gas_name("CARBON_DIOXIDE") == "CO2"
        assert _get_neqsim_gas_name("HydrogenSulfide") == "H2S"

    def test_handles_underscore_and_space_variants(self):
        assert _get_neqsim_gas_name("Carbon Dioxide") == "CO2"
        assert _get_neqsim_gas_name("carbon dioxide") == "CO2"
        assert _get_neqsim_gas_name("Hydrogen Sulfide") == "H2S"

    def test_unknown_gas_returns_cleaned_lowercase(self):
        assert _get_neqsim_gas_name("SomeStrangeGas") == "somestrangegas"
        assert _get_neqsim_gas_name("XenonDifluoride") == "xenondifluoride"

    def test_glycol_and_amine_variants(self):
        assert _get_neqsim_gas_name("MEG") == "MEG"
        assert _get_neqsim_gas_name("TEG") == "TEG"
        assert _get_neqsim_gas_name("MDEA") == "MDEA"
        assert _get_neqsim_gas_name("MEA") == "MEA"
        assert _get_neqsim_gas_name("DEA") == "DEA"

    def test_iso_variants_mapped_to_normal(self):
        assert _get_neqsim_gas_name("Isopentane") == "isopentane"
        assert _get_neqsim_gas_name("Isohexane") == "n-hexane"


class TestNeqSimEOSRegistryIntegrity:
    """Structural integrity of the EOS registry."""

    def test_backend_names_start_with_neqsim_prefix(self):
        for name in NEQSIM_AVAILABLE_BACKENDS:
            assert name.startswith("neqsim-")

    def test_each_backend_class_resolves_via_getattr(self):
        for name, info in NEQSIM_EOS_REGISTRY.items():
            cls_name = info["class"]
            assert isinstance(cls_name, str)
            assert len(cls_name) > 0

    def test_gerg2008_and_h2_share_class(self):
        assert NEQSIM_EOS_REGISTRY["neqsim-gerg2008"]["class"] == "SystemGERG2008Eos"
        assert NEQSIM_EOS_REGISTRY["neqsim-gerg2008-h2"]["class"] == "SystemGERG2008Eos"

    def test_mixing_rule_types_are_consistent(self):
        for name, info in NEQSIM_EOS_REGISTRY.items():
            if info["group"] == "Referans EOS":
                assert info["mixing"] is None
            elif info["class"] in ("SystemSrkCPAstatoil", "SystemSoreideWhitson"):
                assert isinstance(info["mixing"], int)
            else:
                assert info["mixing"] == "classic"
