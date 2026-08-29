# Natural Gas Prop Main v1.8.1

**Tarih:** 28 Ağustos 2026

## Hotfix: macOS Güncelleme SSL Hatası

### Sorun
macOS'ta "Güncellemeleri Denetle" çalıştırıldığında:

```
[WARNING] natural_gas_main.utils.updater: Network error checking updates:
<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate (_ssl.c:1032)>
```

### Kök Neden
- macOS python.org Python kurulumlarında varsayılan CA sertifika dosyası
  (`etc/openssl/cert.pem`) bulunmuyor (yalnızca "Install Certificates.command"
  çalıştırılırsa oluşturulur).
- PyInstaller ile paketlenmiş `.app` içindeki Python'da da hiçbir CA bundle
  yok; uygulama kendi `libssl`'ini taşıyor ama güven kökü dosyası eksik.
- `certifi` bağımlılığı tanımlı değildi → taşınabilir CA bundle yok.

### Çözüm
- `certifi` bağımlılığı `pyproject.toml` ve `requirements.txt`'e eklendi.
- `updater.py` artık `ssl.create_default_context(cafile=certifi.where())`
  ile TLS context oluşturuyor; **doğrulama asla devre dışı bırakılmıyor**.
- PyInstaller `hiddenimports`'a `certifi` eklendi → `hook-certifi.py`
  `cacert.pem`'i `.app` paketine gömüyor.
- `URLError` mesajı gerçek sebebi (`e.reason`) gösteriyor (diagnostik).

### Doğrulama
- Geliştirme ortamında gerçek `UpdateChecker.check_for_updates()` GitHub'a
  karşı başarılı (200 OK).
- Yeni SSL testleri: certifi CA kullanımı + certifi yokken güvenli fallback.

## Test Altyapısı

| Metrik | v1.8.1 |
|--------|--------|
| Test sayısı | **728** |
| Coverage | **%94** |

---

# Natural Gas Prop Main v1.8.0

**Tarih:** 28 Ağustos 2026

## Mühendislik Güçlendirme Seti

### Doğruluk Düzeltmeleri

| # | Düzeltme | Etki |
|---|----------|------|
| D1 | **Standart Basınç Birim Hatası** | Standart koşullar satırı artık `101.325 kPa` doğru gösteriliyor (önceden `101325.000 kPa` basılıyordu). |
| D2 | **Wichert-Aziz İsim Eşleme** | Asit gaz düzeltmesi artık `H2S`, `CO2`, `Metan`, `Hidrojen Sülfür` gibi takma adlarla da çalışıyor; ekşi gaz Z değerleri doğru düzeltiliyor. |
| D3 | **DAK Yakınsama** | Sabit-nokta iterasyonu yerine analitik türevli Newton-Raphson + 0.5 damping. Kritik bölgede (Tpr≈1.05-1.2, Ppr>1.5) salınım giderildi; yakınsamayan sonuç artık geçersiz işaretleniyor. |
| D4 | **Hidrat Model Geçerliliği** | Hammerschmidt/Motiee/Towler-Mokhatab modelleri SG ve basınç aralıklarıyla filtreleniyor; sınır dışı modeller ortalamadan çıkarılıp kullanıcıya uyarı gösteriliyor. |
| D5 | **NCM Fallback** | Normal hacim hesabı `[seçilen, SRK, PR, HEOS]` zinciriyle deneniyor; yanıltıcı "yoğuşma" mesajı netleştirildi. |

### Girdi Güvenliği

- Türkçe virgül (`,`) girişi sıcaklık, basınç ve hacim alanlarında destekleniyor
- `%0.00` bileşenler (kromatograf şablonlarında tespit edilmeyen gazlar) artık geçerli ve hesaba katılmadan filtreleniyor
- `.ngp` dosya doğrulaması Pydantic `GasMixture` modeliyle güçlendirildi (negatif oran / geçersiz tip engellenir)
- >1000 K veya >700 bar girişlerde **Ekstrapolasyon Uyarısı**

### Robustness

- CoolProp taşınım özellikleri (viskozite, iletkenlik, JT, yüzey gerilimi) artık hesaplanıp **gösteriliyor**; hesaplanamayanlar "Model Desteklemiyor" olarak işaretleniyor
- AGA8 stderr yönlendirmesi thread-lock ile serileştirildi (paralel hesapta fd bozulması önlendi)
- Log handler pencere kapanışında temizleniyor (TclError / kaynak sızıntısı giderildi)
- Fallback nedeni sonuç tablosunda şeffaf gösteriliyor

### UX & Raporlama

- **"100%'e Normalleştir"** butonu
- **"Panodan Yapıştır"**: Excel/kromatograf verisi tek tıkla tabloya aktarılır (Türkçe/İngilizce isimler desteklenir)
- **Özel şablon yönetimi**: Kuyu/hat kompozisyonları isim vererek kaydedilip silinebilir
- **Molar ↔ Kütlesel %** otomatik dönüşüm
- Çift-tık ile gaz ekleme, oran kutusunda Enter ile sonraki satıra geçme
- **Excel (.xlsx) ve CSV** dışa aktarma; sonuç tablosuna sağ-tık "Tabloyu Kopyala"
- **PDF raporuna model karşılaştırma matrisi** eklendi
- **Mühendislik Sorumluluk Reddi** (Engineering Disclaimer) tüm raporlara ve Hakkında penceresine eklendi

### Performans & Güvenlik

- Z-karşılaştırma matrisi CoolProp/AGA8 için paralelleştirildi (`ThreadPoolExecutor`); NeqSim (JPype) güvenliği için seri kaldı
- Güncelleyici: açılışta sessiz sürüm kontrolü (opt-in) ve SHA-256 bütünlük farkındalığı; GitHub dışı indirme URL'leri engelleniyor

### Mobil

- `scripts/sync_mobile_core.py`: masaüstü çekirdek modülleri Android Chaquopy kaynağına senkronize eden betik (UI hariç)

## Build & Dağıtım

| Platform | Format |
|----------|--------|
| Windows | `.exe` / `.zip` (onedir) |
| macOS | `.app` (`.dmg`) |

## Test Altyapısı

| Metrik | v1.8.0 |
|--------|--------|
| Test sayısı | **672** |
| Coverage | **%94** |

---

# Natural Gas Prop Main v1.7.2

**Tarih:** 3 Temmuz 2026

## Önemli Değişiklikler

### Windows Antivirüs ve Kısıtlı Kullanıcı Uyumlaştırması (AV & Non-Admin Fix)
- **Official Gömülü Python Sürümü (`win64-portable`)**: Kurumsal bilgisayarlarda admin yetkisi olmadan ve antivirüs engeline takılmadan çalışabilmesi için resmi imzalı Python gömülü dağıtımı ve arka planda sessizce başlatan `Natural Gas Prop.vbs` başlatıcısı eklendi.
- **Klasör Yapılı PyInstaller Sürümü (`win64-folder`)**: PyInstaller tek dosya (`onefile`) paketlemesinden kaynaklanan geçici dizin (`%TEMP%`) yetki ve antivirüs engellemelerini aşmak için klasör yapılı (`onedir`) dağıtım seçeneği eklendi.

### Sürüm ve Mobil Senkronizasyonu
- Mobil uygulama (Chaquopy/Gradle yapılandırmaları) ve tüm konfigürasyon dosyaları masaüstü sürümüyle senkronize edilerek `v1.7.2` sürümüne yükseltildi.

## Build & Dağıtım

| Platform | Format | Boyut | Açıklama |
|----------|--------|-------|----------|
| Windows | `.zip` (gömülü portable Python) | ~70 MB | Kurumsal / AV korumalı / Sessiz VBS |
| Windows | `.zip` (onedir klasör) | ~65 MB | Standart klasör yapılı derleme |
| macOS | `.dmg` (`.app` bundle) | ~55 MB | Standart macOS sürümü | 5574e03 (feat(v1.8.0): engineering hardening + UX/reporting overhaul)

---

# Natural Gas Prop Main v1.7.1

**Tarih:** Temmuz 2026

## Önemli Değişiklikler

### Onefile .exe (Antivirüs Fix)
**onedir** denemesi sonrası **onefile .exe**'ye dönüldü. JAR gömme ve runtime hook'lar kaldırıldı — Trend Micro false positive'inin kaynağı buydu. Tek dosya `.exe`, temiz build.

### macOS Pydantic Düzeltmesi
`optimize=2` Python bytecode optimizasyonu Pydantic v2'nin docstring bağımlılığını kırdığı için macOS `.app` çöküyordu. `optimize=1` ile düzeltildi.

### NeqSim 15 EOS — Temiz Arayüz
- Java 17/21 kuruluysa NeqSim otomatik algılanır, 15 EOS modeli aktif olur
- Java yoksa sadece CoolProp/AGA8 backend'leri gösterilir (temiz UI)
- Menüden "NeqSim Kurulum Bilgisi" ile Java kurulum talimatları alınabilir
- JAR gömme kaldırıldı — NeqSim için kullanıcı `pip install neqsim` ile kendi kurar

### AV-dostu Java Algılama
Runtime hook kaldırıldı. Java algılama artık `glob`/wildcard kullanmıyor — sadece `JAVA_HOME` env, `PATH` ve sabit bilinen dizinler.

## Build & Dağıtım

| Platform | Format | Boyut |
|----------|--------|-------|
| Windows | `.zip` (onefile `.exe`) | ~55 MB |
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
