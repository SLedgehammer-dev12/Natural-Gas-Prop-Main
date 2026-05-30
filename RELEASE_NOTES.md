# Natural Gas Prop Main v1.5.0

**Tarih:** 30 Mayıs 2026

## Yeni Özellikler (New Features)

### Wichert-Aziz Asit Gaz Düzeltmesi
H₂S ve CO₂ içeren asit gaz karışımları için Standing-Katz Z-faktörü hesabında Wichert-Aziz (1972) düzeltmesi eklendi. Pseudo-kritik sıcaklık ve basınç otomatik olarak düzeltiliyor.

### ISO 6976:2016 Isıl Değer Modülü
Uluslararası ISO 6976:2016 standardına uygun, 16 doğal gaz bileşeni için stokiyometrik yanma tabanlı HHV/LHV hesaplama modülü (`iso6976.py`).

### Sutton(1985) Pseudo-Kritik Korelasyonu
`StandingKatzZFactor.sutton_pseudo_critical()` – Tam gaz kompozisyonu bilinmediğinde, sadece SG ve N₂/CO₂/H₂S mol kesirlerinden pseudo-kritik özellik tahmini.

### Faz Zarfı Kritik Nokta Tespiti
CoolProp v7.2.0 ile faz zarfı kritik nokta (`critical_t`, `critical_p`) çıkarımı ve cricondenbar doğru endeksleme.

## Kritik Hata Düzeltmeleri

| # | Hata | Açıklama |
|---|------|----------|
| H1 | Isıl Değer Mol/Kütle Kesri | `_calculate_heating_values_component_based` artık `_get_heating_value_mass_weights()` kullanarak mol kesrini kütle kesrine çeviriyor |
| H2 | AGA8 Normalizasyon | Tanınmayan gazlar listeleniyor, eşik 0.99→0.95, eksik bileşenler WARNING ile loglanıyor |
| H3 | AGA8 SG Default | `StandardConditionResults` default SG=1.0 → None. Tüm downstream kontroller eklendi |
| H4 | HEOS/SRK Faz Zarfı | Ters mantık düzeltildi: HEOS uyumluysa HEOS kullanılır |
| H5 | packaging Bağımlılık | `pyproject.toml`'a `packaging>=21.0` eklendi |
| H6 | Standart Koşul Gösterimi | Sabit `"288.15 K, 101.325 kPa"` → Dinamik `reference_temperature/pressure` |
| H7 | DAK Converjans | Yakınsama sağlanamazsa WARNING loglanıyor |

## İyileştirmeler

- **PDF Raporlama:** macOS font (Helvetica, Arial) ve Linux font (DejaVu, Liberation) fallback desteği
- **Performans:** `preferences.py` in-memory cache, `output_panel.py` log-records deque(maxlen=2000)
- **Thread Safety:** `_is_calculating` flag + `_calc_lock` ile çift tıklama koruması
- **UI:** Welcome dialog dismiss düzeltildi, kapatma onay dialogu eklendi
- **Pie Chart:** `_pie_chart_scheduled` class değişkeni → instance değişkeni

## Build & Dağıtım

- **macOS:** Self-contained `.dmg` (`.app` bundle, tek dosya)
- **Windows:** Standalone `.exe` (GitHub Actions ile otomatik build)
- **pip:** `natural_gas_prop_main-1.5.0-py3-none-any.whl`
- **CoolProp:** `>=7.2.0` minimum versiyon
- **Entry point:** `natural-gas-prop` komutu ile CLI başlatma
- **MANIFEST.in:** Eksik dosyalar eklendi, cache dizinleri exclude
- **PyInstaller:** `hiddenimports` dolduruldu, gereksiz data kopyası kaldırıldı
- **version_info.txt:** Türkçe dil kodu (`041f04B0`)

## Test Altyapısı

| Metrik | v1.4.1 | v1.5.0 |
|--------|--------|--------|
| Test sayısı | 133 | **278** |
| Coverage | ~%50 | **%77.6** |
| Test dosyası | 12 | **21** |

**Yeni test dosyaları:**
- `conftest.py` – Shared fixtures
- `test_validators.py` – 9 validasyon fonksiyonu (%0→%100 coverage)
- `test_result_unit_converter.py` – 8 dönüşüm metodu (%63→%90)
- `test_preferences.py` + `test_preferences_edge.py` – In-memory cache
- `test_iso6976.py` + `test_iso6976_extended.py` – ISO 6976 modülü
- `test_z_factor_correlations.py` – Wichert-Aziz + Sutton korelasyonları
- `test_heating_value_weights.py` – Kütle ağırlıklandırma doğrulaması
- `test_phase_envelope.py` – Faz zarfı kritik nokta
- `test_aga8_extended.py` – AGA8 mapping + edge case'ler
- `test_release_readiness.py` – Dinamik versiyon karşılaştırma (düzeltildi)

## Yükseltme

```bash
pip install --upgrade natural-gas-prop-main==1.5.0
```

## İndirme

| Platform | Dosya |
|----------|-------|
| macOS | `Natural Gas Prop Main v1.5.0.dmg` |
| Windows | `Natural Gas Prop Main.exe` |
| pip | `natural_gas_prop_main-1.5.0-py3-none-any.whl` |
