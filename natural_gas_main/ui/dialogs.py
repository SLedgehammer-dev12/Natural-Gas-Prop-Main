"""
Dialog windows and user prompts.

Provides reusable dialog functions for user interaction.
"""

from tkinter import messagebox
from typing import List, Optional
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from natural_gas_main.config import preferences


def show_heos_compatibility_warning(
    incompatible_gases: List[str],
    heos_supported_gases: List[str]
) -> bool:
    """
    Show HEOS compatibility warning and ask user if they want to switch to SRK.
    
    Args:
        incompatible_gases: List of incompatible gas names
        heos_supported_gases: List of HEOS-compatible gases
        
    Returns:
        True if user wants to switch to SRK, False otherwise
    """
    gases_str = ", ".join(incompatible_gases)
    
    message = (
        f"HEOS Uyumluluk Uyarısı\n\n"
        f"Seçilen karışım HEOS yöntemi için tam karışım desteğine sahip değil.\n"
        f"Uyumsuz gazlar: {gases_str}\n\n"
        f"KRİTİK UYARI: HEOS ile devam etmek hatalı sonuçlara yol açabilir.\n\n"
        f"Doğruluk için SRK yöntemine otomatik geçiş yapılsın mı?\n"
        f"(ÖNERİLİR)"
    )
    
    result = messagebox.askyesno(
        "HEOS Uyumluluk Uyarısı",
        message,
        icon='warning'
    )
    
    if result:
        messagebox.showinfo(
            "Yöntem Değişikliği",
            "Hesaplama HEOS yerine SRK yöntemi ile devam edecek."
        )
    else:
        messagebox.showwarning(
            "Risk Kabul Edildi",
            "HEOS ile devam etme riskini kabul ettiniz. "
            "Hesaplama başarısız olabilir."
        )
    
    return result


def show_heating_value_method_warning(method: str) -> None:
    """
    Show warning when heating values are calculated using component-based method.
    
    Args:
        method: Calculation method used
    """
    if method == "Bileşen bazlı":
        messagebox.showwarning(
        "Isıl Değer Hesaplama Uyarısı",
        "CoolProp yerleşik modeli ısıl değerleri doğrudan hesaplayamadığı için,\n"
        "daha sağlam 'Bileşen Bazlı Toplama' yöntemi kullanılmıştır.\n\n"
        "Bu yöntem karışım etkileşimlerini ihmal eder ve CoolProp yerleşik\n"
        "hesabına göre daha düşük doğrulukta olabilir.\n\n"
        "Sonuçları mühendislik onayı ile kullanınız."
        )


def show_backend_fallback_info(error_message: str, failed_backend: str) -> None:
    """
    Show information when backend fallback occurs.
    
    Args:
        error_message: Error message from failed backend
        failed_backend: Name of the backend that failed
    """
    messagebox.showwarning(
        "Yöntem Değişikliği",
        f"{failed_backend} yöntemi başarısız oldu:\n\n"
        f"CoolProp Hatası: {error_message}\n\n"
        f"Program otomatik olarak alternatif bir yöntem deneyecek."
    )


def show_backend_used_info(requested_backend: str, used_backend: str) -> None:
    """
    Show info when different backend was used than requested.
    
    Args:
        requested_backend: Backend user requested
        used_backend: Backend actually used
    """
    if requested_backend != used_backend:
        messagebox.showinfo(
            "Yöntem Değişikliği",
            f"Hesaplama {used_backend} yöntemi ile tamamlandı.\n"
            f"(İstenilen: {requested_backend})"
        )


def show_about_dialog() -> None:
    """Show application about information."""
    from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE
    neqsim_status = "Hazır" if NEQSIM_AVAILABLE else "Java/NeqSim gerekli"
    about_text = (
        "Termodinamik Gaz Karışımı Hesaplayıcı\n"
        "Sürüm v1.7.1 - Profesyonel Sürüm\n\n"
        "v1.7.1 sürümü: NeqSim 15 EOS modeli, Java 21 desteği,\n"
        "JAR bundle, frozen .exe'de JVM auto-detect.\n\n"
        "© 2026 Kompresör Pompa"
    )
    messagebox.showinfo("Hakkında", about_text)


def show_user_guide_dialog() -> None:
    """Show user guide information."""
    from natural_gas_main.config.settings import config
    from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE
    
    neqsim_note = ""
    if not NEQSIM_AVAILABLE:
        neqsim_note = (
            "\n⚠ NEQSIM UYARISI:\n"
            "   NeqSim kullanılamıyor (Java 11+ gerekli).\n"
            "   Java kurulumu: https://adoptium.net/\n"
            "   pip install neqsim>=3.6.1\n"
        )
    
    guide_text = (
        "KULLANIM KILAVUZU - Natural Gas Prop Main\n\n"
        "1. GAZ KOMPOZİSYONU:\n"
        "   • Yüzde toplamı tam 100% olmalıdır\n"
        "   • Maksimum 20 gaz bileşeni eklenebilir\n"
        "   • Arama kutusu ile gaz seçimi hızlandırılabilir\n\n"
        "2. BASINÇ GİRİŞİ:\n"
        f"   • Gauge (g) basınçları için atmosferik basınç ({config.P_ATM_BAR} bar) referans alınır\n"
        "   • Absolute (a) basınçlar doğrudan kullanılır\n\n"
        "3. HESAPLAMA YÖNTEMİ:\n"
        "   • NeqSim (15 EOS): GERG-2008, SRK/PR ailesi, CPA, Søreide-Whitson, UMR-PRU\n"
        "   • CoolProp (HEOS/SRK/PR): Klasik termodinamik hesaplamalar\n"
        "   • pyaga8 (GERG-2008/AGA8-Detail): ISO 20765-2 standardı\n"
        "   • Uyumsuzluk durumunda otomatik geçiş yapılır\n"
        f"{neqsim_note}"
        "4. ISIL DEĞER GÜVENİLİRLİĞİ (KRİTİK):\n"
        "   • 'NeqSim ISO 6976': En doğru (ISO standardı)\n"
        "   • 'CoolProp yerleşik': Yüksek doğruluk\n"
        "   • 'Bileşen bazlı': Yedekleme yöntemi\n"
        "   • Uyarı mesajları dikkate alınmalıdır\n\n"
        "5. SONUÇLAR:\n"
        "   • Gerçek koşullar (girilen T ve P'de)\n"
        "   • Standart koşullar (15°C, 101.325 kPa)\n"
        "   • Isıl değerler (HHV, LHV, Wobbe)\n"
        "   • Taşınım özellikleri (viskozite, termal iletkenlik)\n"
        "   • Hacim dönüşümü (isteğe bağlı)"
    )
    messagebox.showinfo("Kullanım Kılavuzu", guide_text)


def show_neqsim_unavailable_warning(selected_backend: str) -> None:
    """
    Show warning when a NeqSim EOS is selected but Java/NeqSim is not available.
    
    Args:
        selected_backend: The NeqSim EOS name that was selected
    """
    messagebox.showwarning(
        "NeqSim Kullanılamıyor",
        f"'{selected_backend}' seçildi ancak NeqSim kullanılamıyor.\n\n"
        "Gereksinimler:\n"
        "• Java 11+ Runtime (JRE) kurulu olmalı\n"
        "  https://adoptium.net/\n\n"
        "• neqsim Python paketi yüklenmeli:\n"
        "  pip install neqsim>=3.6.1\n\n"
        "CoolProp/AGA8 fallback zinciri kullanılacak."
    )


def show_new_features_info() -> None:
    """Show new features information for current version with do not show again option."""
    from natural_gas_main.config.settings import config
    version = config.APP_VERSION
    dialog = ctk.CTkToplevel()
    dialog.title(f"Yenilikler - Sürüm {version}")
    dialog.geometry("620x560")
    dialog.resizable(False, False)
    
    dialog.transient()
    dialog.grab_set()
    
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    ctk.CTkLabel(
        frame, 
        text=f"🚀 DOĞAL GAZ PROP - SÜRÜM {version}",
        font=ctk.CTkFont(size=15, weight="bold")
    ).pack(pady=(0, 15))
    
    if version == "v1.7.0":
        info_text = (
            "📋 BU SÜRÜMDEKİ DÜZELTMELER:\n\n"
            "• Exception Güvenliği: Tüm 'except BaseException' ve 'except: pass'\n"
            "  yapıları temizlendi. Ctrl+C artık çalışır durumda.\n\n"
            "• Thread Güvenliği: Update checker arka plan thread'inde çalışıyor,\n"
            "  UI donma sorunu giderildi. Logger thread-safe hale getirildi.\n\n"
            "• CI Kalitesi: GitHub Actions pipeline'ına test adımı eklendi,\n"
            "  pip önbellekleme ile build süresi ~5 dk kısaltıldı.\n\n"
            "• Termodinamik: isohexane → 2-methylpentane mapping düzeltildi.\n"
            "  ISO 6976 artık SRK yerine GERG-2008 kullanıyor.\n\n"
            "• Çok Loblu Faz Zarfı: Birden fazla lobu olan faz diyagramlarında\n"
            "  cricondenbar/cricondentherm doğru tespit ediliyor.\n\n"
            "• Hidrat Modeli: Yakınsama kontrolü eklendi.\n\n"
            "• AGA8 Eser Bileşen: %95+ eşlenmiş bileşen varsa eser bileşenler\n"
            "  tolere ediliyor, hata yerine rescale yapılıyor.\n\n"
            "• Kod Kalitesi: 4x tekrar eden hava yoğunluğu helper'a çekildi.\n"
            "  Sutton SG_hc clamp uyarısı loglanıyor.\n\n"
            "• Tema/Style: Pasta grafiği, TreeView stilleri tema değişince\n"
            "  otomatik güncelleniyor. Ölü widget'lar temizlendi.\n\n"
            "• Coverage threshold %70'e yükseltildi.\n\n"
            "Detaylı notlar için RELEASE_NOTES.md dosyasına bakın."
        )
    elif version in ("v1.6.0", "v1.6"):
        info_text = (
            "📋 BU SÜRÜMDEKİ YENİLİKLER:\n\n"
            "• NeqSim Entegrasyonu: Equinor NeqSim ile 15 yeni EOS modeli.\n"
            "  - SRK/PR ailesi (8 model), CPA, Søreide-Whitson\n"
            "  - GERG-2008, EOS-CG, Span-Wagner, UMR-PRU\n\n"
            "• Transport Properties: Viskozite, termal iletkenlik,\n"
            "  Joule-Thomson katsayısı, yüzey gerilimi.\n\n"
            "• NeqSim ISO 6976: HHV/LHV/Wobbe için ISO standardı (Stage 0).\n\n"
            "• CPA Hidrat Modeli: vdW-Platteeuw (4. model).\n\n"
            "• Gerçek Zamanlı Hata Yükleme: crash gönderme (CurseForge/mail).\n\n"
            "Gereksinim: Java 11+ ve pip install neqsim>=3.6.1\n"
            "Detaylı notlar için RELEASE_NOTES.md dosyasına bakın."
        )
    elif version == "v1.5.2":
        info_text = (
            "📋 BU SÜRÜMDEKİ DEĞİŞİKLİKLER:\n\n"
            "• Kapsamlı Test Coverage: %73→%95 (545 test, 11 modül ≥%92).\n"
            "• Test Aşama 1: exceptions, heating_value_db, result_unit_converter,\n"
            "  settings, calculation_result → %100 coverage.\n"
            "• Test Aşama 2: converters, z_factor, iso6976, preferences,\n"
            "  gas_data → mock ile edge case testleri.\n"
            "• Test Aşama 3: logger (%18→%98), updater (%40→%96),\n"
            "  aga8_calculator (%79→%96).\n"
            "• Test Aşama 4: calculator (%76→%93) — FakeAbstractState ile.\n"
            "• report_generator: %80→%92 — font fallback, PDF hata yönetimi.\n"
            "• Tüm modüllerde edge case ve exception yolu testleri.\n\n"
            "🔧 ÖNCEKİ SÜRÜMDEN (v1.5.1) DEVAM EDEN:\n"
            "• HEOS/SRK backend seçimi ters mantık düzeltildi.\n"
            "• Sutton Sıcaklık Dönüşümü: °R→K dönüşüm hatası giderildi.\n"
            "• H₂S Isıl Değer: %7.6 hata düzeltildi (ISO 6976:2016 uyumlu).\n"
            "• ISO 6976:2016 Modülü: 8 yeni bileşen eklendi.\n"
            "• Fraksiyon Normalizasyonu, Thread Güvenliği, Gaz Adı Eşleme.\n\n"
            "Detaylı sürüm notları için RELEASE_NOTES.md dosyasına bakın."
        )
    else:
        info_text = f"Sürüm {version} yayında. Detaylı değişiklik listesi için RELEASE_NOTES.md dosyasına bakın."
    
    text_area = ctk.CTkTextbox(frame, wrap=tk.WORD, height=280, width=540, font=ctk.CTkFont(size=12))
    text_area.insert("1.0", info_text)
    text_area.configure(state="disabled")
    text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Checkbox
    dont_show_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(
        frame, 
        text="Bu pencereyi bir daha gösterme", 
        variable=dont_show_var
    ).pack(anchor="w", pady=(0, 15))
    
    # Close Logic
    def on_close():
        if dont_show_var.get():
            preferences.set_preference("show_welcome_dismissed_version", config.APP_VERSION)
        dialog.destroy()
    
    # Button
    ctk.CTkButton(
        frame, 
        text="Tamam, Başlayalım!", 
        command=on_close,
        width=200
    ).pack(anchor="center")
    
    # Handle window close button (X)
    dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    # Center on screen
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')


def confirm_calculation_start() -> bool:
    """
    Ask user confirmation before starting heavy calculation (if needed).
    
    Returns:
        True if user confirms, False otherwise
    """
    # For now, always return True (no confirmation needed)
    # Can be extended for very large calculations
    return True


def show_error(title: str, message: str) -> None:
    """
    Show error message dialog.
    
    Args:
        title: Dialog title
        message: Error message
    """
    messagebox.showerror(title, message)


def show_warning(title: str, message: str) -> None:
    """
    Show warning message dialog.
    
    Args:
        title: Dialog title
        message: Warning message
    """
    messagebox.showwarning(title, message)


def show_info(title: str, message: str) -> None:
    """
    Show information message dialog.
    
    Args:
        title: Dialog title
        message: Information message
    """
    messagebox.showinfo(title, message)
