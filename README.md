# Natural Gas Prop Main

**Modern, modüler termodinamik gaz karışımı hesaplama uygulaması**

![Version](https://img.shields.io/badge/version-v1.5.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

## 🎯 Özellikler

- ✅ **Kapsamlı Hesaplamalar:** Z-faktörü, yoğunluk, entalpi, entropi, Cp, Cv, k, ses hızı, HHV/LHV, Wobbe indeksi
- ✅ **Çoklu Backend:** HEOS, SRK, PR termodinamik modelleri
- ✅ **Otomatik Fallback:** Hesaplama başarısız olursa alternatif backend'lere geçiş
- ✅ **Type Safety:** Pydantic modelleri ile tip güvenli veri yapıları
- ✅ **Modüler Mimari:** Kolay test, bakım ve genişletme
- ✅ **Detaylı Loglama:** Tüm hesaplamalar ve hatalar kaydedilir

## 📋 Gereksinimler

- Python 3.10 veya üzeri
- CoolProp >= 7.2.0
- Pydantic >= 2.0.0

## 🚀 Kurulum

### 1. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 2. (Opsiyonel) Geliştirme Araçlarını Yükleyin

```bash
pip install -r requirements-dev.txt
```

## 💻 Kullanım

### GUI Uygulaması

```bash
python -m natural_gas_main.main
```

### Python API (Gelecek Sürüm)

```python
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculator import ThermoCalculator

# Karışım tanımla
mixture = GasMixture(
    components=[
        GasComponent(name="Methane", fraction=90.0),
        GasComponent(name="Ethane", fraction=5.0),
        GasComponent(name="Nitrogen", fraction=5.0)
    ],
    fraction_type="molar"
)

# Hesapla
calc = ThermoCalculator(backend="HEOS")
result = calc.calculate_properties(
    mixture=mixture,
    temperature_k=298.15,  # 25°C
    pressure_pa=101325.0   # 1 atm
)

print(f"Yoğunluk: {result.actual.density:.4f} kg/m³")
print(f"Z-faktörü: {result.actual.compressibility_factor:.5f}")
```

## 📁 Proje Yapısı

```
Natural Gas Prop Main/
├── natural_gas_main/          # Ana paket
│   ├── config/              # Konfigürasyon
│   ├── core/                # Core utilities
│   ├── models/              # Data modelleri ve hesaplama
│   ├── ui/                  # Kullanıcı arayüzü
│   └── utils/               # Yardımcı fonksiyonlar
├── tests/                   # Test dosyaları
├── requirements.txt         # Bağımlılıklar
└── README.md               # Bu dosya
```

## 🔧 Konfigürasyon

Ayarlar `natural_gas_main/config/settings.py` dosyasında merkezi olarak yönetilir:

- Fiziksel sabitler (atmosferik basınç, standart koşullar)
- Hesaplama limitleri (min/max sıcaklık, basınç)
- UI ayarları (pencere boyutu, tema)
- Loglama yapılandırması

## 📊 Desteklenen Birimler

### Sıcaklık
- Kelvin (K)
- Celsius (°C)
- Fahrenheit (°F)

### Basınç  
- Kilopascal (kPa)
- Bar absolute (bar(a))
- Bar gauge (bar(g))
- PSI absolute (psi(a))
- PSI gauge (psi(g))
- Megapascal (MPa)
- Atmosphere (atm)

## 🧪 Test

```bash
# Tüm testleri çalıştır
pytest

# Coverage raporu ile
pytest --cov=natural_gas_main --cov-report=html

# Tek bir test dosyası
pytest tests/test_calculator.py -v
```

## 📝 Değişiklik Geçmişi

### Sürüm v1.5.0 (2026-05-30)
- 🔥 **Wichert-Aziz Asit Gaz Düzeltmesi:** H₂S ve CO₂ içeren gazlar için Z-faktörü hesabı
- 📐 **ISO 6976:2016 Isıl Değer Modülü:** Uluslararası standart uyumlu HHV/LHV
- 📊 **Sutton(1985) Korelasyonu:** SG'den pseudo-kritik özellik tahmini
- 🐛 **Kritik Düzeltmeler:** Isıl değer mol/kütle kesri, AGA8 normalizasyon, standart koşul gösterimi
- 🍎 **macOS .dmg:** Self-contained kurulum paketi
- 🪟 **Windows .exe:** GitHub Actions otomatik build
- 🧪 **278 test, %78 coverage** (+126 test, 6 yeni dosya)
- ⚡ CoolProp 7.2.0, thread safety, performans iyileştirmeleri

### Sürüm v1.4.1 (2026-05-18)
- Kod temizliği: God method ayrıştırması, bare except temizliği, Pydantic v2 uyumu
- Hata yönetimi: Sessiz except blokları loglamalı hale getirildi
- Performans: PropsSI cache, pie chart throttle, Z-only fallback optimizasyonu
- Güvenlik: Download URL GitHub-only doğrulaması
- UI: Başarı popup kaldırıldı, buton state kurtarma, log filtresi Türkçeleştirildi
- Test: 133 test, kapsamlı test altyapısı

## 🤝 Katkıda Bulunma

Bu proje Kompresör Pompa tarafından geliştirilmektedir.

## 📄 Lisans

Tescilli yazılım - Kompresör Pompa

## 📧 İletişim

Sorular ve destek için lütfen proje yöneticisi ile iletişime geçin.

---

**Not:** v1.0, G4.9.1'in tüm özelliklerini korurken modern Python best practices ile yeniden yazılmıştır.
