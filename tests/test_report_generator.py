import logging
from pathlib import Path

from natural_gas_main.utils.report_generator import ReportGenerator


def test_pdf_report_supports_turkish_unicode_characters(tmp_path):
    output_path = tmp_path / "rapor.pdf"

    ReportGenerator.generate_pdf_report(
        input_params={
            "temperature": "15 °C",
            "pressure": "80 bar(a)",
            "backend": "HEOS",
            "fraction_type": "molar",
            "volume": "10 m³",
        },
        results=[
            ("- GERÇEK KOŞULLAR SONUÇLARI -", "", ""),
            ("Sıkıştırılabilirlik Faktörü (Z)", "0.83735", "-"),
            ("Yoğunluk (Gerçek - ρ)", "70.1234", "kg/m³"),
            ("İç Enerji (u)", "Hesaplanamadı", "kJ/kg"),
        ],
        gas_composition=[
            ("Methane", 94.6),
            ("Carbon Dioxide", 0.3),
        ],
        file_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 1000


def test_log_extraction_with_default_log():
    """Log extraction with default (None) log_file and include_full=False."""
    extracted = ReportGenerator._get_calculation_log(None, include_full=False)
    assert isinstance(extracted, list)


def test_log_extraction_with_full_log():
    """Full log extraction should return a list."""
    extracted = ReportGenerator._get_calculation_log(None, include_full=True)
    assert isinstance(extracted, list)


def test_log_extraction_with_nonexistent_file():
    """Log extraction with a nonexistent log file should not crash."""
    extracted = ReportGenerator._get_calculation_log("/nonexistent/path.log", include_full=True)
    # Should gracefully handle missing file
    assert isinstance(extracted, list)


def test_text_report_generation():
    """Text report should generate without error."""
    result = ReportGenerator.generate_text_report(
        input_params={"temperature": "15 °C", "pressure": "80 bar(a)"},
        results=[("Z-Faktörü", "0.83735", "-")],
        gas_composition=[("Methane", 94.6)],
    )

    assert isinstance(result, str)
    assert len(result) > 50
    assert "Z-Faktörü" in result
    assert "0.83735" in result
