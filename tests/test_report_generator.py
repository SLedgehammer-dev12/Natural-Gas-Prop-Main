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
