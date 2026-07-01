# Natural Gas Prop Main v1.7.1

**Tarih:** Temmuz 2026

## Önemli Değişiklikler

### Windows Onedir Dağıtım (Antivirüs Fix)
Windows için **onefile .exe** yerine **onedir klasör** dağıtımına geçildi. PyInstaller'ın runtime temp extraction davranışı kaldırıldı — bu, Trend Micro ve benzeri AV'lerin false positive engellemesini çözer. Kullanıcı ZIP'i indirip klasöre çıkarır, içindeki `.exe`'ye tıklar.

### macOS Pydantic Düzeltmesi
`optimize=2` Python bytecode optimizasyonu Pydantic v2'nin docstring bağımlılığını kırdığı için macOS `.app` çöküyordu. `optimize=1` ile düzeltildi.

### NeqSim 15 EOS — Temiz Arayüz
- Java 17/21 kuruluysa NeqSim otomatik algılanır, 15 EOS modeli aktif olur
- Java yoksa sadece CoolProp/AGA8 backend'leri gösterilir (temiz UI)
- Menüden "NeqSim Kurulum Bilgisi" ile Java kurulum talimatları alınabilir
- JAR dosyaları onedir klasöründe normal dosya olarak bulunur — AV tetiklemez

### AV-dostu Java Algılama
Runtime hook kaldırıldı. Java algılama artık `glob`/wildcard kullanmıyor — sadece `JAVA_HOME` env, `PATH` ve sabit bilinen dizinler.

## Build & Dağıtım

| Platform | Format | Boyut |
|----------|--------|-------|
| Windows | `.zip` (onedir klasör) | ~55 MB |
| macOS | `.dmg` (`.app` bundle) | ~55 MB |

## Test Altyapısı

| Metrik | v1.7.1 |
|--------|--------|
| Test sayısı | **610** |
| Coverage | **%91** |

---

# Natural Gas Prop Main v1.6.1

**Tarih:** Haziran 2026

## Hotfix Düzeltmeleri

| # | Hata | Etki |
|---|------|------|
| H1 | **AGA8 Panik → UI Kilitlenmesi** | pyaga8 `IterationFail` Rust paniği `BaseException` olarak yakalanıyor. UI donmuyor, Z-karşılaştırma tablosu AGA8 sütunu boş gösteriliyor. |
| H2 | **TclError Entry Temizleme** | Sıcaklık/basınç alanı silindiğinde konsola hata yağmıyor. |
| H3 | **DAK Geçersiz Aralık** | Tpr<1.0 için DAK hiç çalıştırılmıyor, gereksiz iterasyon önlendi. |
| H4 | **Tight Layout Uyarısı** | Küçük pencere boyutlarında matplotlib uyarısı bastırıldı. |
| H5 | **Koyu Mod Lejant Rengi** | Faz zarfı lejantı siyah→beyaz, okunabilirlik arttı. |
| H6 | **NeqSim ISO 6976 Sıcaklık** | Referans sıcaklığı kullanıcı seçimine göre dinamik. |
| H7 | **Hidrat NeqSim Ayrıştırma** | CPA modeli ampirik modellerden ayrı gösteriliyor (Önerilen). |

## Test Altyapısı

| Metrik | v1.6.0 | v1.6.1 |
|--------|--------|--------|
| Test sayısı | 641 | **641** |
| Coverage | %94.92 | **%94.94** |

---

# Natural Gas Prop Main v1.6.0

**Tarih:** Haziran 2026

## Yeni Özellikler

### NeqSim Termodinamik Motor Entegrasyonu (15 Yeni EOS)
Equinor'un açık kaynak NeqSim kütüphanesi entegre edildi. Artık CoolProp/pyaga8'ın yanında **15 farklı EOS** ile hesaplama yapılabilir.

| Grup | EOS Modeli | Açıklama |
|------|-----------|----------|
| **SRK Ailesi** | SRK, SRK-Peneloux, SRK-MC, SRK-TwuCoon | Kübik EOS varyantları |
| **PR Ailesi** | PR, PR-MC, PR-TwuCoon, PR-Danesh | Peng-Robinson varyantları |
| **CPA** | SRK-CPA (Equinor) | Su-hidrokarbon VLE, hidrat, glikol dehidrasyon |
| **Ekşi Gaz** | Søreide-Whitson | H₂S/CO₂ + tuzlu su sistemleri |
| **Referans** | GERG-2008, GERG-2008-H₂, EOS-CG, Span-Wagner | ISO 20765-2, CCS, saf CO₂ |
| **Tahminsel** | UMR-PRU | Etkileşim parametresi gerektirmez |

### Transport Properties Desteği
Viskozite (cP), termal iletkenlik (W/mK), Joule-Thomson katsayısı ve yüzey gerilimi artık hesaplanabiliyor ve UI/raporlarda gösteriliyor.

### NeqSim ISO 6976 Isıl Değer Hesaplaması
HHV/LHV/Wobbe hesabında CoolProp'tan önce NeqSim ISO 6976 standardı denecek (Stage 0). Başarısız olursa mevcut fallback zinciri çalışır.

### NeqSim CPA-tabanlı Hidrat Tahmini
Hammerschmidt/Motiee/Towler modellerine ek olarak NeqSim'in CPA-tabanlı van der Waals-Platteeuw hidrat modeli kullanılıyor (4. model).

### Backend Bilgi Gösterimi
UI'da seçilen EOS modeli hakkında kısa açıklama ve grup bilgisi gösteriliyor.

## Önemli Değişiklikler

### Varsayılan Backend: `neqsim-gerg2008`
Yeni kurulumlarda varsayılan hesaplama yöntemi NeqSim GERG-2008 olarak değiştirildi. NeqSim kurulu değilse otomatik olarak CoolProp/AGA8 fallback zinciri devreye girer.

### Fallback Zinciri (Yeni)
```
neqsim-gerg2008 → neqsim-eoscg → neqsim-srk-cpa → neqsim-srk-peneloux →
neqsim-pr-mc → neqsim-soreide → neqsim-umrpru → neqsim-srk → neqsim-pr →
GERG-2008(pyaga8) → HEOS → SRK → PR → Z-only(ANN10)
```

## Gereksinimler

| Bağımlılık | Versiyon | Zorunlu? | Açıklama |
|-----------|----------|----------|----------|
| Java | 11+ | **Evet** (NeqSim için) | Adoptium/Temurin JDK önerilir |
| neqsim | ≥3.6.1 | Hayır | `pip install neqsim` (CoolProp fallback çalışır) |
| CoolProp | ≥7.2.0 | **Evet** | Ana termodinamik motor (NeqSim yoksa) |
| pyaga8 | ≥0.1.16 | Hayır | AGA8/GERG-2008 (NeqSim yoksa) |

## Yükseltme

```bash
# Java 11+ kurulu değilse: https://adoptium.net/
pip install --upgrade natural-gas-prop-main
pip install neqsim>=3.6.1  # isteğe bağlı
```

## Test Altyapısı

| Metrik | v1.5.x | v1.6.0 |
|--------|--------|--------|
| Test sayısı | 545+ | **585+** |
| Yeni test dosyası | - | `test_neqsim_calculator.py` (24 test) |
| NeqSim mock test | - | 23 passed, 1 skip |

---

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
