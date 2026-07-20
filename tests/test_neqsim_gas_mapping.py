"""Tests for NeqSim gas name mapping correctness."""

import pytest
from natural_gas_main.models.neqsim_calculator import (
    NEQSIM_GAS_MAPPING,
    _get_neqsim_gas_name,
    NEQSIM_AVAILABLE,
)


class TestNeqSimGasMapping:
    """Verify all gas name mappings resolve to valid NeqSim component names."""

    def test_isobutane_maps_to_i_butane(self):
        assert _get_neqsim_gas_name("isobutane") == "i-butane"

    def test_isopentane_maps_to_i_pentane(self):
        assert _get_neqsim_gas_name("isopentane") == "i-pentane"

    def test_cyclopentane_maps_to_c_c5(self):
        assert _get_neqsim_gas_name("cyclopentane") == "c-C5"

    def test_cyclohexane_maps_to_c_hexane(self):
        assert _get_neqsim_gas_name("cyclohexane") == "c-hexane"

    def test_methane_maps_correctly(self):
        assert _get_neqsim_gas_name("methane") == "methane"

    def test_carbondioxide_maps_to_CO2(self):
        assert _get_neqsim_gas_name("carbondioxide") == "CO2"

    def test_hydrogensulfide_maps_to_H2S(self):
        assert _get_neqsim_gas_name("hydrogensulfide") == "H2S"

    def test_case_variation_handled(self):
        assert _get_neqsim_gas_name("Methane") == "methane"

    def test_spaces_stripped(self):
        assert _get_neqsim_gas_name(" methane ") == "methane"

    def test_unknown_returns_lowercase_clean(self):
        assert _get_neqsim_gas_name("FakeGas") == "fakegas"


@pytest.mark.skipif(not NEQSIM_AVAILABLE, reason="NeqSim not available")
class TestNeqSimAddComponent:
    """Verify mapped names actually work with NeqSim's addComponent."""

    @pytest.fixture(autouse=True)
    def _check_neqsim(self):
        from neqsim import jneqsim
        self.jneqsim = jneqsim

    def _try_add(self, name):
        s = self.jneqsim.thermo.system.SystemSrkEos(300, 1e5)
        s.addComponent(name, 1.0)
        return True

    def test_i_butane_adds_successfully(self):
        assert self._try_add("i-butane")

    def test_i_pentane_adds_successfully(self):
        assert self._try_add("i-pentane")

    def test_c_c5_adds_successfully(self):
        assert self._try_add("c-C5")

    def test_c_hexane_adds_successfully(self):
        assert self._try_add("c-hexane")

    def test_isobutane_via_mapping_adds_successfully(self):
        """Full chain: display name -> mapping -> NeqSim addComponent."""
        name = _get_neqsim_gas_name("isobutane")
        assert name == "i-butane"
        assert self._try_add(name)

    def test_mapped_names_work_with_all_eos(self):
        """Mapped names should work with SRK, PR, and GERG-2008."""
        names = [
            _get_neqsim_gas_name("isobutane"),
            _get_neqsim_gas_name("isopentane"),
            _get_neqsim_gas_name("cyclopentane"),
            _get_neqsim_gas_name("cyclohexane"),
        ]
        for cls_name in ["SystemSrkEos", "SystemPrEos", "SystemGERG2008Eos"]:
            for name in names:
                cls = getattr(self.jneqsim.thermo.system, cls_name)
                s = cls(300, 1e5)
                try:
                    s.addComponent(name, 0.01)
                except Exception as e:
                    pytest.fail(f"{cls_name}.addComponent({name!r}) failed: {e}")
