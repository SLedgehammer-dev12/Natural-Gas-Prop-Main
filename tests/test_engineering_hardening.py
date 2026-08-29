"""
Engineering hardening tests.

Covers the fixes from the engineering audit:
- Wichert-Aziz acid-gas alias normalization (1.1)
- Standard pressure kPa display (1.2)
- DAK Newton-Raphson solver (1.3)
- Hydrate model validity filtering (1.4)
- Transport property display from CoolProp (3.1)
- Zero-fraction components / schema validation (2.2 / 2.4)
- Clipboard composition parsing (4)
- CSV / XLSX export + comparison matrix in PDF (5)
- Updater SHA-256 awareness (7)
"""

import math
import json

import pytest

from natural_gas_main.models.z_factor import StandingKatzZFactor
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import (
    ActualConditionResults,
    StandardConditionResults,
    CalculationResult,
    TransportProperties,
)
from natural_gas_main.models.calculator import ThermoCalculator, COOLPROP_AVAILABLE
from natural_gas_main.utils.data_serializer import validate_loaded_data
from natural_gas_main.utils.report_generator import ReportGenerator


# ---------------------------------------------------------------------------
# 1.1 Wichert-Aziz normalization
# ---------------------------------------------------------------------------

class _FakeCoolProp:
    """Minimal CoolProp stub for pseudo-critical tests."""

    PROPS = {
        ("Tcrit", "Methane"): 190.564,
        ("pcrit", "Methane"): 4599200.0,
        ("M", "Methane"): 0.0160428,
        ("Tcrit", "HydrogenSulfide"): 373.6,
        ("pcrit", "HydrogenSulfide"): 8974000.0,
        ("M", "HydrogenSulfide"): 0.034081,
        ("Tcrit", "CarbonDioxide"): 304.1282,
        ("pcrit", "CarbonDioxide"): 7377300.0,
        ("M", "CarbonDioxide"): 0.04401,
        ("Tcrit", "Ethane"): 305.32,
        ("pcrit", "Ethane"): 4872000.0,
        ("M", "Ethane"): 0.030069,
    }

    @staticmethod
    def PropsSI(key, fluid):
        return _FakeCoolProp.PROPS[(key, fluid)]


def test_wichert_aziz_uses_coolprop_aliases():
    """H2S / CO2 aliases must trigger the Wichert-Aziz correction."""
    mixture = GasMixture(
        components=[
            GasComponent(name="H2S", fraction=10.0),
            GasComponent(name="CO2", fraction=10.0),
            GasComponent(name="Methane", fraction=80.0),
        ]
    )
    est = StandingKatzZFactor(_FakeCoolProp())
    pseudo = est.pseudo_critical(mixture)

    # Kay's rule without correction:
    kay_tpc = 0.1 * 373.6 + 0.1 * 304.1282 + 0.8 * 190.564
    # epsilon > 0 so corrected Tpc must be below the raw Kay rule value.
    assert pseudo.temperature_k < kay_tpc
    assert pseudo.pressure_pa < 0.1 * 8974000.0 + 0.1 * 7377300.0 + 0.8 * 4599200.0


def test_wichert_aziz_turkish_names_normalized():
    """Turkish aliases ('Hidrojen Sülfür' / 'Karbondioksit') must be honored."""
    mixture = GasMixture(
        components=[
            GasComponent(name="Hidrojen Sülfür", fraction=10.0),
            GasComponent(name="Karbondioksit", fraction=10.0),
            GasComponent(name="Metan", fraction=80.0),
        ]
    )
    est = StandingKatzZFactor(_FakeCoolProp())
    pseudo = est.pseudo_critical(mixture)
    kay_tpc = 0.1 * 373.6 + 0.1 * 304.1282 + 0.8 * 190.564
    assert pseudo.temperature_k < kay_tpc


def test_exact_coolprop_name_mapping():
    """Exact alias lookup for clipboard parsing (no fuzzy garbage)."""
    assert GasMixture._exact_coolprop_name("H2S") == "HydrogenSulfide"
    assert GasMixture._exact_coolprop_name("CO2") == "CarbonDioxide"
    assert GasMixture._exact_coolprop_name("Metan") == "Methane"
    assert GasMixture._exact_coolprop_name("N2") == "Nitrogen"
    assert GasMixture._exact_coolprop_name("bogus token 123") is None
    assert GasMixture._exact_coolprop_name("Methane") == "Methane"


# ---------------------------------------------------------------------------
# 1.2 Standard pressure display
# ---------------------------------------------------------------------------

def test_standard_pressure_displayed_in_kpa():
    result = CalculationResult(
        backend_used="SRK",
        actual=ActualConditionResults(
            temperature=300.0, pressure=1e5, density=20.0, molar_mass=0.016,
            compressibility_factor=0.95, internal_energy=-500.0, enthalpy=-480.0,
            entropy=3.0, cp=2.2, cv=1.6,
        ),
        standard=StandardConditionResults(
            density_std=0.80, specific_gravity=0.62,
            reference_temperature=288.15, reference_pressure=101325.0,
        ),
    )
    rows = result.to_display_list("SI")
    row = next(r for r in rows if r[0] == "Standart Koşullar")
    assert "101.325 kPa" in row[1]
    assert "101325" not in row[1]


# ---------------------------------------------------------------------------
# 1.3 DAK Newton-Raphson
# ---------------------------------------------------------------------------

def test_dak_newton_converges_and_out_of_range_raises():
    est = StandingKatzZFactor(_FakeCoolProp())
    z = est.dak(10.0, 2.0)
    assert math.isfinite(z)
    assert z > 0
    # DAK extreme input must raise (range guard), not silently return a value
    with pytest.raises(ValueError):
        est.dak(1000.0, 0.1)


def test_dak_critical_region_converges():
    """Near-critical region (Tpr~1.05-1.2, Ppr>1.5) must converge with Newton."""
    est = StandingKatzZFactor(_FakeCoolProp())
    for tpr in (1.05, 1.1, 1.2):
        for ppr in (1.5, 2.0, 3.0):
            z = est.dak(ppr, tpr)
            assert math.isfinite(z) and z > 0


# ---------------------------------------------------------------------------
# 1.4 Hydrate model validity filtering
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp not installed")
class TestHydrateValidity:
    def test_valid_sg_keeps_all_models(self):
        calc = ThermoCalculator()
        res = calc._calculate_hydrate_formation(280.0, 1e6, 0.65)
        assert res is not None
        assert res.model_validity_warnings == []
        expected = (res.t_hydrate_hammerschmidt + res.t_hydrate_motiee
                    + res.t_hydrate_towler_mokhatab) / 3.0
        assert res.t_hydrate_average == pytest.approx(expected)

    def test_out_of_range_sg_excludes_models(self):
        calc = ThermoCalculator()
        # SG=0.95: Hammerschmidt (<=0.70) and Motiee (<=0.90) out of range
        res = calc._calculate_hydrate_formation(280.0, 1e6, 0.95)
        assert res is not None
        assert any("Hammerschmidt modeli geçerlilik dışı" in w for w in res.model_validity_warnings)
        assert any("Motiee modeli geçerlilik dışı" in w for w in res.model_validity_warnings)
        # Average must be based only on Towler-Mokhatab
        assert res.t_hydrate_average == pytest.approx(res.t_hydrate_towler_mokhatab)

    def test_out_of_range_pressure_flagged(self):
        calc = ThermoCalculator()
        # 2900 psia > 1500 psia limit for all models
        res = calc._calculate_hydrate_formation(280.0, 2.0e7, 0.65)
        assert res is not None
        assert len(res.model_validity_warnings) >= 3


# ---------------------------------------------------------------------------
# 2.2 / 2.4 Zero fractions and schema validation
# ---------------------------------------------------------------------------

def test_zero_fraction_component_allowed_and_filtered():
    comp = GasComponent(name="Oxygen", fraction=0.0)
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=95.0),
            GasComponent(name="Oxygen", fraction=5.0),
            GasComponent(name="Helium", fraction=0.0),
        ]
    )
    assert comp.fraction == 0.0
    assert [c.name for c in mixture.effective_components()] == ["Methane", "Oxygen"]
    # CoolProp string excludes the zero-fraction gas and stays aligned
    assert mixture.to_coolprop_string() == "Methane&Oxygen"
    assert len(mixture.get_decimal_fractions()) == 2


def test_validate_loaded_data_rejects_bad_fractions():
    assert not validate_loaded_data({
        "composition": [{"name": "Methane", "fraction": -5.0}],
        "fraction_type": "molar",
    })
    assert not validate_loaded_data({
        "composition": [{"name": "Methane", "fraction": "abc"}],
        "fraction_type": "molar",
    })
    assert not validate_loaded_data({
        "composition": [{"name": "Methane", "fraction": 50.0}],
        "fraction_type": "kg",  # invalid enum
    })
    assert validate_loaded_data({
        "composition": [
            {"name": "Methane", "fraction": 90.0},
            {"name": "Ethane", "fraction": 10.0},
        ],
        "fraction_type": "molar",
    })


# ---------------------------------------------------------------------------
# 3.1 Transport display from CoolProp
# ---------------------------------------------------------------------------

def test_coolprop_transport_values_displayed():
    actual = ActualConditionResults(
        temperature=300.0, pressure=1e5, density=20.0, molar_mass=0.016,
        compressibility_factor=0.95, internal_energy=-500.0, enthalpy=-480.0,
        entropy=3.0, cp=2.2, cv=1.6,
        viscosity=0.012,
        thermal_conductivity=0.035,
    )
    result = CalculationResult(
        backend_used="HEOS",
        actual=actual,
        standard=StandardConditionResults(
            density_std=0.80, specific_gravity=0.62,
            reference_temperature=288.15, reference_pressure=101325.0,
        ),
    )
    rows = result.to_display_list("SI")
    text = "\n".join(str(r) for r in rows)
    assert "TAŞINIM ÖZELLİKLERİ" in text
    assert "CoolProp" in text  # source label
    assert "Viskozite" in text


def test_transport_missing_shows_model_not_supported():
    actual = ActualConditionResults(
        temperature=300.0, pressure=1e5, density=20.0, molar_mass=0.016,
        compressibility_factor=0.95, internal_energy=-500.0, enthalpy=-480.0,
        entropy=3.0, cp=2.2, cv=1.6,
    )
    result = CalculationResult(
        backend_used="HEOS",
        actual=actual,
        standard=StandardConditionResults(
            density_std=0.80, specific_gravity=0.62,
            reference_temperature=288.15, reference_pressure=101325.0,
        ),
        transport=TransportProperties(),  # NeqSim present but empty values
    )
    rows = result.to_display_list("SI")
    text = "\n".join(str(r) for r in rows)
    assert "Model Desteklemiyor" in text


# ---------------------------------------------------------------------------
# 4 Clipboard composition parsing
# ---------------------------------------------------------------------------

def test_parse_composition_from_clipboard():
    from natural_gas_main.ui.input_panel import InputPanel

    text = "Metan 92.5\nCO2\t0.5\nH2S 0.2\n92.5 Etan\nAzot 0.3\n"
    parsed = InputPanel._parse_composition_text(None, text)
    names = [n for n, _ in parsed]
    assert "Methane" in names
    assert "CarbonDioxide" in names
    assert "HydrogenSulfide" in names
    assert "Ethane" in names
    assert "Nitrogen" in names

    # Unparseable garbage is ignored, not fuzzy-matched into bogus gases
    garbage = InputPanel._parse_composition_text(None, "totally random words\n")
    assert garbage == []


# ---------------------------------------------------------------------------
# 5 Reporting: CSV / XLSX / PDF comparison matrix
# ---------------------------------------------------------------------------

def test_export_csv(tmp_path):
    out = tmp_path / "rapor.csv"
    ReportGenerator.export_csv(
        [("Z-Faktörü", "0.83735", "-")],
        [("Methane", 94.6)],
        str(out),
        comparison_results=[["Özellik", "HEOS"], ["Z", "0.84"]],
    )
    assert out.exists()
    content = out.read_text(encoding="utf-8-sig")
    assert "Methane" in content
    assert "0.83735" in content


def test_export_excel(tmp_path):
    out = tmp_path / "rapor.xlsx"
    ReportGenerator.export_excel(
        {"temperature": "15 °C", "pressure": "80 bar(a)", "backend": "HEOS",
         "fraction_type": "molar", "volume": "10 m³"},
        [("Z-Faktörü", "0.83735", "-")],
        [("Methane", 94.6)],
        str(out),
        comparison_results=[["Özellik", "HEOS"], ["Z", "0.84"]],
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_pdf_report_includes_comparison_and_disclaimer(tmp_path):
    out = tmp_path / "rapor.pdf"
    ReportGenerator.generate_pdf_report(
        input_params={"temperature": "15 °C", "pressure": "80 bar(a)",
                      "backend": "HEOS", "fraction_type": "molar"},
        results=[("- SONUÇLAR -", "", ""), ("Z-Faktörü", "0.83735", "-")],
        gas_composition=[("Methane", 94.6)],
        file_path=str(out),
        comparison_results=[
            ["Özellik", "Birim", "HEOS", "SRK"],
            ["Z-Faktörü", "-", "0.84", "0.85"],
        ],
    )
    assert out.exists()
    assert out.stat().st_size > 1000


# ---------------------------------------------------------------------------
# 6 Fallback transparency
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp not installed")
def test_backend_fallback_info_populated(monkeypatch):
    """Failed backends must be surfaced in backend_fallback_info."""
    calc = ThermoCalculator()
    mixture = GasMixture(components=[GasComponent(name="Methane", fraction=100.0)])

    def fake_order(self, mixture, preferred):
        return ["HEOS", "SRK"]

    def fake_calc(self, mixture, temperature_k, pressure_pa, volume_m3, backend,
                  standard_T, standard_P, standard_name):
        if backend == "HEOS":
            raise ValueError("HEOS failed (test)")
        actual = ActualConditionResults(
            temperature=temperature_k, pressure=pressure_pa, density=20.0,
            molar_mass=0.016, compressibility_factor=0.95, internal_energy=-500.0,
            enthalpy=-480.0, entropy=3.0, cp=2.2, cv=1.6,
        )
        standard = StandardConditionResults(
            density_std=0.80, specific_gravity=0.62,
            reference_temperature=standard_T, reference_pressure=standard_P,
        )
        return CalculationResult(backend_used=backend, actual=actual, standard=standard)

    monkeypatch.setattr(ThermoCalculator, "_get_backend_order", fake_order)
    monkeypatch.setattr(ThermoCalculator, "_calculate_with_backend", fake_calc)
    monkeypatch.setattr(ThermoCalculator, "_calculate_z_factor_comparison",
                        lambda self, *a, **kw: [])

    result, used = calc.calculate_with_fallback(mixture, 300.0, 1e5, preferred_backend="HEOS")
    assert used == "SRK"
    assert result.backend_fallback_info is not None
    assert "HEOS" in result.backend_fallback_info
    assert "SRK" not in result.backend_fallback_info  # only failures listed


# ---------------------------------------------------------------------------
# 7 Updater: SSL context, SHA-256 awareness, URL validation
# ---------------------------------------------------------------------------

def test_updater_exposes_sha256_and_validates_url(monkeypatch):
    import ssl
    import urllib.request
    from natural_gas_main.utils.updater import UpdateChecker

    class _FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({
                "version": "v99.0.0",
                "date": "2026-01-01",
                "download_url": "https://github.com/user/repo/releases/tag/v99.0.0",
                "sha256": "abc123def456",
            }).encode("utf-8")

    seen = {}
    def fake_urlopen(url, timeout, context=None, **kw):
        seen["context"] = context
        return _FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    checker = UpdateChecker()
    has_update, info, msg = checker.check_for_updates()
    assert has_update
    assert info["sha256"] == "abc123def456"
    # HTTPS request must use a verifiable TLS context (certifi CA bundle)
    assert seen["context"] is not None
    assert seen["context"].verify_mode == ssl.CERT_REQUIRED


def test_updater_blocks_non_github_download_url(monkeypatch):
    import urllib.request
    from natural_gas_main.utils.updater import UpdateChecker

    class _FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({
                "version": "v99.0.0",
                "download_url": "https://evil.example.com/malware.zip",
            }).encode("utf-8")

    monkeypatch.setattr(
        urllib.request, "urlopen",
        lambda url, timeout=5, context=None, **kw: _FakeResp()
    )

    checker = UpdateChecker()
    has_update, info, _ = checker.check_for_updates()
    assert has_update
    assert "github.com" in info["download_url"]


def test_updater_ssl_context_uses_certifi_ca(monkeypatch):
    """The update TLS context must be built from the certifi CA bundle and verify peers."""
    import ssl
    import certifi
    from natural_gas_main.utils import updater

    captured = {}
    real_create = ssl.create_default_context

    def fake_create_default_context(**kwargs):
        captured["kwargs"] = kwargs
        return real_create(**kwargs)

    monkeypatch.setattr(ssl, "create_default_context", fake_create_default_context)

    ctx = updater._build_ssl_context()
    assert captured["kwargs"].get("cafile") == certifi.where()
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_updater_ssl_context_fallback_without_certifi(monkeypatch):
    """If certifi is unavailable, fall back to the default trust store (still verified)."""
    import builtins
    import ssl
    from natural_gas_main.utils import updater

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "certifi":
            raise ImportError("certifi unavailable (test)")
        return real_import(name, *args, **kwargs)

    captured = {}
    real_create = ssl.create_default_context

    def fake_create_default_context(**kwargs):
        captured["kwargs"] = kwargs
        return real_create(**kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(ssl, "create_default_context", fake_create_default_context)

    ctx = updater._build_ssl_context()
    assert "cafile" not in captured["kwargs"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED