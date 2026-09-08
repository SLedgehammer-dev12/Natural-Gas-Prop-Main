# 🚀 Natural Gas Prop Main - Yenilikler & Değişiklikler (What's New)

## 📌 Sürüm v1.8.3 (8 Eylül 2026)

### ⚡ 1. Hesaplama Hızlandırma & Akıllı Önbellekleme (Caching)
* **Faz Zarfı (Phase Envelope) Karışım Önbelleği (300 ms $\rightarrow$ 0 ms):**
  * Faz zarfı sınırları ($P$-$T$ çiğ/kabarcık noktası eğrisi) işletme sıcaklık ve basıncından bağımsızdır, yalnızca karışım kompozisyonuna ve modele bağlıdır.
  * Karışım kompozisyonu bazlı `_phase_envelope_cache` entegre edildi.
  * Aynı gaz karışımı üzerinde sıcaklık veya basınç değiştirildiğinde pahalı `build_phase_envelope` hesaplaması sıfıra indirildi (**0 ms**).
* **Hava Yoğunluğu & Saf Bileşen Molar Kütle Önbelleği:**
  * Standart ve normal şart dönüşümlerinde hava yoğunluğu `_air_density_cache` ile önbelleklendi.
  * Isıl değer kütle ağırlıklandırmasında her bileşen için tekrarlanan molekül ağırlığı hesapları `_molar_mass_cache` ile hızlandırıldı.
* **Gaz Adı Normalizasyonu & Kromatografi Eşleme:**
  * `GasMixture._format_gas_name_for_coolprop` ve `_fuzzy_match_gas_name` metotları `@lru_cache(maxsize=256)` ile donatılarak ad dönüşümleri anlık ($O(1)$) yapıldı.

### 🚀 2. Paralel Hesaplama & Arayüz Tepki Süresi
* **11 EOS Karşılaştırma Matrisi Havuz Genişletmesi:**
  * `_calculate_z_factor_comparison` içindeki `ThreadPoolExecutor` iş parçacığı sayısı `min(5, (os.cpu_count() or 4))` olarak optimize edilerek 5 bağımsız model (`GERG-2008`, `AGA8-Detail`, `HEOS`, `SRK`, `PR`) çok çekirdekli işlemcide tam eşzamanlı çalıştırılıyor.
* **Arayüz Kuyruk Tepki Süresi:**
  * UI kuyruk kontrol periyodu 100 ms'den **40 ms**'ye indirilerek hesaplama tamamlandığında sonuçların ekranda görünme gecikmesi 2.5 kat hızlandırıldı.
* **Raporlama Düzeltmesi:**
  * `ReportGenerator.export_excel` ve `export_csv` çağrılarında parametre adı uyumsuzluğu giderildi (`comparison_results` / `comparison_rows`).

### 🧪 3. Test ve Doğrulama
* Yeni performans optimizasyon test paketi eklendi (`tests/test_performance_optimizations.py`).
* Toplam test sayısı: **733 geçen test**, 10 atlanan (opsiyonel Java/dfont), 0 hata.
* Test kapsamı: **%93.93**.

---

## 📌 Sürüm v1.8.2 (29 Ağustos 2026)
* **Tematik Uygulama İkonu:** Basınç göstergesi ve doğal gaz alevi motifli macOS (.icns) ve Windows (.ico) ikonları eklendi.
* **Sürümlü Çalıştırma Dosyası:** Executable/app adı her zaman sürüm numarasıyla sonlanıyor (örn. `Natural Gas Prop Main v1.8.2`).

---

## 📌 Sürüm v1.8.1 (28 Ağustos 2026)
* **macOS Güncelleme SSL Düzeltmesi:** macOS `CERTIFICATE_VERIFY_FAILED` hatası `certifi` CA paketi ile giderildi.

---

## 📌 Sürüm v1.8.0 (28 Ağustos 2026)
* **Mühendislik Güçlendirmesi:**
  * Standart basınç birim hatası düzeltildi (101.325 kPa).
  * Wichert-Aziz asit gaz düzeltmesi isim normalizasyonu yapıldı.
  * DAK (Dranchuk-Abou-Kassem) çözücü Newton-Raphson yöntemine geçirildi.
  * Hidrat modelleri sınır şartı kontrolü eklendi.
  * %0.00 kromatografi bileşen desteği ve Türkçe klavye virgül (,) toleransı eklendi.
  * "100%'e Normalleştir", "Panodan Yapıştır" ve özel şablon yöneticisi eklendi.
  * Excel (.xlsx), CSV (.csv) ve zenginleştirilmiş PDF raporlama eklendi.
