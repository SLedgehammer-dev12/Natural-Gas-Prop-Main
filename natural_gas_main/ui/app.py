"""
Main application window.

Coordinates between input panel, output panel, calculator, and user interactions.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import threading
import queue
import logging
import os
from pathlib import Path

from natural_gas_main.config.settings import config
from natural_gas_main.config import preferences
from natural_gas_main.models.calculator import ThermoCalculator, COOLPROP_AVAILABLE
from natural_gas_main.core.exceptions import (
    ValidationError,
    BackendNotAvailableError,
    ThermoCalculationError
)
from natural_gas_main.ui.input_panel import InputPanel
from natural_gas_main.ui.output_panel import OutputPanel
from natural_gas_main.ui import dialogs
from natural_gas_main.utils.report_generator import ReportGenerator
from natural_gas_main.utils.data_serializer import (
    save_inputs_to_file,
    load_inputs_from_file,
    validate_loaded_data,
    DataSerializationError,
    FILE_EXTENSION,
    FILE_TYPE_NAME
)
from natural_gas_main.utils.updater import UpdateChecker


class ThermoApp(ctk.CTk):
    """
    Main application window using CustomTkinter.
    
    Manages the GUI, user interactions, and calculation workflow.
    """
    
    def __init__(self):
        """Initialize main application window."""
        super().__init__()
        
        # Configure CustomTkinter appearance from preferences
        saved_mode = preferences.get_preference("ctk_appearance_mode", config.CTK_THEME)
        saved_theme = preferences.get_preference("ctk_color_theme", config.CTK_COLOR_THEME)
        
        ctk.set_appearance_mode(saved_mode)
        ctk.set_default_color_theme(saved_theme)
        
        self.title(config.WINDOW_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ThermoApp")
        
        # Load gas list
        self.gas_list = self._load_gas_list()

        # Initialize calculator
        self.calculator = ThermoCalculator()
        self._calc_lock = threading.Lock()
        self._is_calculating = False

        from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE as _neqsim_avail
        if _neqsim_avail:
            self.logger.info("NeqSim hazır: 15 EOS modeli kullanılabilir")
        else:
            self.logger.info("NeqSim kullanılamıyor [Java bulunamadı]. CoolProp/AGA8 backend'leri aktif.")

        self.result_queue = queue.Queue()

        
        # Create UI
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        self._check_queue()
        
        # Optional silent update check on startup (opt-in via Help menu)
        if preferences.get_preference("check_updates_on_startup", False):
            self.after(2000, self._check_for_updates_silent)
        
        # Show welcome message
        self.after(100, self._show_welcome)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_close(self):
        """Prompt before closing."""
        if messagebox.askyesno(
            "Çıkış",
            "Programdan çıkmak istediğinize emin misiniz?\n"
            "Kaydedilmemiş değişiklikler kaybolacaktır."
        ):
            # Unregister the log handler so the destroyed text widget is not
            # scheduled again (prevents TclError / handler leak).
            if hasattr(self, 'output_panel'):
                try:
                    self.output_panel.shutdown()
                except Exception:
                    pass
            self.quit()
    
    @staticmethod
    def _load_gas_list_from_coolprop():
        """Load gas list using CoolProp (split for testability)."""
        import CoolProp.CoolProp as CP
        fluids = CP.get_global_param_string("FluidsList")
        if fluids:
            all_gases = [f.strip() for f in fluids.split(',') if f.strip()]
            natural_gases = [g.lower() for g in config.NATURAL_GAS_FOCUS_LIST]
            gas_list = sorted([f for f in all_gases if f.lower() in natural_gases])
            display_aliases = {"n-Propane": "Propane"}
            gas_list = sorted({display_aliases.get(g, g) for g in gas_list})
            if gas_list:
                return gas_list
            return sorted(all_gases)
        return None

    def _load_gas_list(self) -> list:
        """
        Load gas list from CoolProp or use fallback.
        
        Returns:
            List of gas names
        """
        if COOLPROP_AVAILABLE:
            try:
                gas_list = self._load_gas_list_from_coolprop()
                if gas_list:
                    self.logger.info(f"Loaded {len(gas_list)} focused gases from CoolProp")
                    return gas_list
                fluids = CP.get_global_param_string("FluidsList")
                if fluids:
                    all_gases = [f.strip() for f in fluids.split(',') if f.strip()]
                    # Filter for natural gas focused components
                    natural_gases = [g.lower() for g in config.NATURAL_GAS_FOCUS_LIST]
                    gas_list = sorted([
                        f for f in all_gases
                        if f.lower() in natural_gases
                    ])

                    display_aliases = {
                        "n-Propane": "Propane",
                    }
                    gas_list = sorted({display_aliases.get(g, g) for g in gas_list})

                    if not gas_list: # Fallback if filter is too strict
                        gas_list = sorted(all_gases)

            except Exception as e:
                self.logger.error(f"Failed to load CoolProp gas list: {e}")
        
        # Fallback list
        self.logger.warning("Using fallback gas list")
        self.after(50, lambda: messagebox.showwarning(
            "CoolProp Uyarısı",
            "CoolProp akışkan listesi yüklenemedi.\n"
            "Kısıtlı yedek akışkan listesi kullanılıyor."
        ))
        return config.FALLBACK_GAS_LIST
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self)
        self.configure(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Aç...", command=self._on_load_data, accelerator="Ctrl+O")
        file_menu.add_command(label="Kaydet...", command=self._on_save_data, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Rapor Kaydet", command=self._on_save_report)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self._on_close)
        
        # Keyboard shortcuts
        self.bind("<Control-o>", lambda e: self._on_load_data())
        self.bind("<Control-s>", lambda e: self._on_save_data())
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Kullanım Kılavuzu", command=dialogs.show_user_guide_dialog)
        help_menu.add_separator()
        help_menu.add_command(label="Güncellemeleri Denetle", command=self._check_for_updates_manual)
        help_menu.add_command(label="Açılışta Sürüm Kontrolü (Aç/Kapat)", command=self._toggle_startup_update_check)
        help_menu.add_separator()
        help_menu.add_command(label="Mühendislik Sorumluluk Reddi", command=dialogs.show_engineering_disclaimer)
        help_menu.add_separator()
        help_menu.add_command(label="Hakkında", command=self._show_about)

        # NeqSim Java info (only when NeqSim is not available)
        from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE
        if not NEQSIM_AVAILABLE:
            help_menu.add_separator()
            help_menu.add_command(
                label="NeqSim Kurulum Bilgisi",
                command=lambda: dialogs.show_neqsim_java_info(parent=self)
            )
        
        # View menu (Appearance)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        
        # Appearance Mode
        mode_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Mod", menu=mode_menu)
        mode_menu.add_command(label="Sistem", command=lambda: self._change_appearance_mode("System"))
        mode_menu.add_command(label="Koyu", command=lambda: self._change_appearance_mode("Dark"))
        mode_menu.add_command(label="Açık", command=lambda: self._change_appearance_mode("Light"))
        
        # Color Theme
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Renk Teması", menu=theme_menu)
        theme_menu.add_command(label="Mavi (Standart)", command=lambda: self._change_color_theme("blue"))
        theme_menu.add_command(label="Yeşil", command=lambda: self._change_color_theme("green"))
        theme_menu.add_command(label="Koyu Mavi", command=lambda: self._change_color_theme("dark-blue"))
    
    def _create_main_layout(self):
        """Create main content layout with input and output panels."""
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.main_paned = tk.PanedWindow(
            main_content,
            orient=tk.HORIZONTAL,
            sashwidth=8,
            sashrelief=tk.RAISED,
            showhandle=True,
            bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#d9d9d9",
            bd=0
        )
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Input panel (left side)
        input_frame = ctk.CTkFrame(self.main_paned)
        self.main_paned.add(input_frame, minsize=430, stretch="never")
        
        self.input_panel = InputPanel(input_frame, self.gas_list, on_change=self._on_input_changed)
        self.input_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Calculate button frame with progress
        calc_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        calc_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.calc_button = ctk.CTkButton(
            calc_frame,
            text="Hesapla",
            command=self._on_calculate,
            fg_color="#4CAF50",
            hover_color="#45a049",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            cursor="hand2"
        )
        self.calc_button.pack(fill=tk.X)
        
        # Progress bar inside button frame (starts hidden)
        self.calc_progress = ctk.CTkProgressBar(calc_frame, mode='indeterminate')
        
        # Output panel (right side)
        output_frame = ctk.CTkFrame(self.main_paned)
        self.main_paned.add(output_frame, minsize=380, stretch="always")
        
        self.output_panel = OutputPanel(output_frame)
        self.output_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Report button
        report_button = ctk.CTkButton(
            output_frame,
            text="Profesyonel PDF Raporu Oluştur",
            command=self._on_save_report,
            fg_color="#1f538d",
            hover_color="#14375e",
            text_color="white",
            font=ctk.CTkFont(weight="bold")
        )
        report_button.pack(pady=10, padx=10, fill=tk.X)

        self.after(100, self._set_initial_panel_split)

    def _set_initial_panel_split(self):
        """Set a practical initial split while keeping the sash user-adjustable."""
        try:
            width = max(self.winfo_width(), config.WINDOW_WIDTH)
            input_width = min(560, max(430, int(width * 0.48)))
            self.main_paned.sash_place(0, input_width, 0)
        except tk.TclError:
            pass
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_var = tk.StringVar(value="Hazır.")
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # self.progress_bar removed — unused dead widget
    
    def _show_welcome(self):
        """Show welcome/new features message if not disabled."""
        should_show = preferences.get_preference("show_welcome_dismissed_version", "v1.0") != config.APP_VERSION
        if should_show:
            dialogs.show_new_features_info()

    def _show_about(self):
        """Show about dialog."""
        dialogs.show_about_dialog()
        
    def _change_appearance_mode(self, new_mode: str):
        """Change application appearance mode."""
        ctk.set_appearance_mode(new_mode)
        # Store preference
        preferences.set_preference("ctk_appearance_mode", new_mode)
        # Update plots and other theme-dependent elements
        if hasattr(self, 'output_panel'):
            self.output_panel._update_theme_colors()
            if self.output_panel.current_result is not None:
                self.output_panel._on_unit_change()
            
    def _change_color_theme(self, new_theme: str):
        """Change application color theme (requires restart for full effect)."""
        ctk.set_default_color_theme(new_theme)
        preferences.set_preference("ctk_color_theme", new_theme)
        messagebox.showinfo(
            "Tema Değişikliği",
            "Renk teması kaydedildi. Tamamen uygulanması için "
            "programı yeniden başlatmanız gerekmektedir."
        )
    
    # Event handlers
    
    def _on_input_changed(self):
        """Reset button from error state when user modifies any input."""
        if self.calc_button.cget("text") == "Hata! Tekrar Dene":
            self.calc_button.configure(fg_color="#4CAF50", text="Hesapla")
    
    def _on_calculate(self):
        """Handle calculate button click."""
        with self._calc_lock:
            if self._is_calculating:
                return
            self._is_calculating = True

        try:
            inputs = self.input_panel.get_all_inputs()
            std_T, std_P, std_name = self.input_panel.get_standard_conditions()

            # Augment with display strings and standard conditions
            inputs.update({
                "standard_T": std_T,
                "standard_P": std_P,
                "standard_name": std_name,
                "temperature_display": f"{self.input_panel.temp_var.get()} {self.input_panel.temp_unit_var.get()}",
                "pressure_display": f"{self.input_panel.press_var.get()} {self.input_panel.press_unit_var.get()}",
            })
            vol_str = self.input_panel.volume_entry.get().strip()
            inputs["volume_display"] = f"{vol_str} {self.input_panel.vol_unit_var.get()}" if vol_str else None

            # Show progress
            self.status_var.set("Hesaplanıyor...")
            self.calc_button.configure(state="disabled", fg_color="#FFA500", text="Hesaplanıyor...")
            self.calc_progress.pack(fill=tk.X, pady=(5, 0))
            self.calc_progress.start()

            # Run in thread
            thread = threading.Thread(
                target=self._run_calculation,
                args=(inputs,),
                daemon=True
            )
            thread.start()

        except ValidationError as e:
            dialogs.show_error("Giriş Hatası", str(e))
            self.calc_button.configure(state="normal", fg_color="#F44336", text="Hata! Tekrar Dene")
            with self._calc_lock:
                self._is_calculating = False
        except ThermoCalculationError as e:
            messagebox.showerror("Giriş Hatası", str(e))
            self.calc_button.configure(state="normal", fg_color="#F44336", text="Hata! Tekrar Dene")
            with self._calc_lock:
                self._is_calculating = False
        except Exception as e:
            messagebox.showerror("Hata", f"Beklenmeyen hata: {e}")
            logging.error(f"Input processing failed: {e}", exc_info=True)
            self.calc_button.configure(state="normal", fg_color="#F44336", text="Hata! Tekrar Dene")
            with self._calc_lock:
                self._is_calculating = False

    def _check_queue(self):
        """Check queue for calculation results."""
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                try:
                    if msg_type == "success":
                        result, used_backend, inputs = data
                        self._on_calculation_success(result, used_backend, inputs)
                    elif msg_type == "error":
                        self._on_calculation_error(data)
                except Exception as e:
                    self._on_calculation_error(e)
                finally:
                    self.result_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._check_queue)
            
    def _run_calculation(self, inputs: dict):
        """
        Run calculation in background thread.
        
        Args:
            inputs: Dictionary of validated inputs
        """
        try:
            # Extract inputs
            mixture = inputs["mixture"]
            temp_k = inputs["temperature_k"]
            press_pa = inputs["pressure_pa"]
            vol_m3 = inputs.get("volume_m3")
            
            # Calculate with backend fallback. HEOS can fail for some valid
            # natural-gas-like mixtures when binary interaction data is missing.
            result, used_backend = self.calculator.calculate_with_fallback(
                mixture=mixture,
                temperature_k=temp_k,
                pressure_pa=press_pa,
                preferred_backend=inputs["backend"],
                volume_m3=vol_m3,
                standard_T=inputs.get("standard_T", config.T_STANDARD),
                standard_P=inputs.get("standard_P", config.P_STANDARD),
                standard_name=inputs.get("standard_name")
            )

            # Send success to queue
            self.result_queue.put(("success", (result, used_backend, inputs)))
            
        except Exception as e:
            # Send error to queue
            self.result_queue.put(("error", e))
    
    def _on_calculation_success(self, result, used_backend: str, inputs: dict):
        """
        Handle successful calculation.
        
        Args:
            result: Calculation result
            used_backend: Backend that was used
            inputs: Original inputs
        """
        # Display results
        self.output_panel.display_results(result)
        
        # Store for report generation
        self.last_result = result
        self.last_inputs = inputs
        
        # Show warnings if applicable
        if result.heating:
            dialogs.show_heating_value_method_warning(result.heating.calculation_method)
        
        if used_backend != inputs['backend']:
            dialogs.show_backend_used_info(inputs['backend'], used_backend)
            self.status_var.set(
                f"Hesaplama tamamlandı. "
                f"({inputs['backend']} yerine {used_backend} kullanıldı)"
            )
        else:
            self.status_var.set("Hesaplama tamamlandı.")
        
        # Soft extrapolation warnings (do not block the result)
        try:
            extra_warnings = []
            if inputs['temperature_k'] > config.EXTRAPOLATION_TEMP_K:
                extra_warnings.append(
                    f"Sıcaklık {inputs['temperature_k']:.0f} K endüstriyel doğal gaz "
                    f"aralığının üzerinde (> {config.EXTRAPOLATION_TEMP_K:.0f} K). "
                    "Sonuçlar ekstrapolasyon içerir."
                )
            if inputs['pressure_pa'] > config.EXTRAPOLATION_PRESS_PA:
                extra_warnings.append(
                    f"Basınç {inputs['pressure_pa'] / 1e5:.0f} bar AGA8 tanım aralığının "
                    f"üzerinde (> {config.EXTRAPOLATION_PRESS_PA / 1e5:.0f} bar). "
                    "Sonuçlar ekstrapolasyon içerir."
                )
            if extra_warnings:
                dialogs.show_warning("Ekstrapolasyon Uyarısı", "\n".join(extra_warnings))
        except Exception as e:
            self.logger.debug(f"Extrapolation warning skipped: {e}")
        
        # Re-enable UI
        self.calc_progress.stop()
        self.calc_progress.pack_forget()
        self.calc_button.configure(state="normal", fg_color="#4CAF50", text="Hesapla")
        with self._calc_lock:
            self._is_calculating = False
    
    def _on_calculation_error(self, error: Exception):
        """
        Handle calculation error.
        
        Args:
            error: Exception that occurred
        """
        # Stop progress
        self.calc_progress.stop()
        self.calc_progress.pack_forget()
        
        # Re-enable UI
        self.calc_button.configure(state="normal", fg_color="#F44336", text="Hata! Tekrar Dene")
        with self._calc_lock:
            self._is_calculating = False
        
        # Get log lines
        log_lines = self._get_recent_log_lines(10)
        
        # Display error
        self.output_panel.display_error(str(error), log_lines)
        self.status_var.set("Hesaplama hatası oluştu.")
        
        # Show error dialog
        dialogs.show_error(
            "Hesaplama Hatası",
            f"Hesaplama sırasında bir hata oluştu:\n\n{str(error)}\n\n"
            "Detaylar için Sonuçlar Tablosunu kontrol edin."
        )
    
    def _get_recent_log_lines(self, count: int = 10) -> list:
        """
        Get recent lines from log file.
        
        Args:
            count: Number of lines to retrieve
            
        Returns:
            List of log lines
        """
        log_file = config.LOG_FILE
        
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-count:]]
        except Exception as e:
            self.logger.error(f"Could not read log file: {e}")
            return [f"Log okunamadı: {e}"]
    
    def _on_save_report(self):
        """Handle save report button click."""
        if not hasattr(self, 'last_result') or self.last_result is None:
            dialogs.show_warning("Rapor Hatası", "Önce bir hesaplama yapmalısınız.")
            return
        
        try:
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[
                    ("PDF Dosyaları", "*.pdf"),
                    ("Metin Dosyaları", "*.txt"),
                    ("Excel Çalışma Kitabı", "*.xlsx"),
                    ("CSV Dosyaları", "*.csv"),
                ],
                title="Raporu Kaydet"
            )
            
            if not file_path:
                return
            
            # Prepare input parameters for report
            inputs = self.last_inputs
            input_params = {
                'temperature': inputs['temperature_display'],
                'pressure': inputs['pressure_display'],
                'backend': self.last_result.backend_used,
                'volume': inputs.get('volume_display'),
                'fraction_type': inputs['mixture'].fraction_type
            }
            
            # Get gas composition
            gas_composition = [
                (comp.name, comp.fraction)
                for comp in inputs['mixture'].components
            ]
            
            # Get results
            results = self.output_panel.get_results_as_list()
            comparison_rows = self.output_panel.get_comparison_as_list()
            
            lower = file_path.lower()
            if lower.endswith(".xlsx"):
                ReportGenerator.export_excel(
                    input_params, results, gas_composition,
                    file_path, comparison_rows=comparison_rows
                )
            elif lower.endswith(".csv"):
                ReportGenerator.export_csv(
                    results, gas_composition, file_path,
                    comparison_rows=comparison_rows
                )
            elif lower.endswith(".pdf"):
                # Save plot to temp file
                import tempfile
                import os
                
                plot_img = None
                if self.last_result.phase_envelope:
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    if self.output_panel.save_phase_envelope_plot(temp_path):
                        plot_img = temp_path
                
                # Generate PDF
                ReportGenerator.generate_pdf_report(
                    input_params,
                    results,
                    gas_composition,
                    file_path,
                    plot_image_path=plot_img,
                    comparison_results=comparison_rows
                )
                
                # Cleanup temp file
                if plot_img and os.path.exists(plot_img):
                    try: os.remove(plot_img)
                    except Exception: pass
            else:
                # Fallback to Text
                ReportGenerator.generate_and_save(
                    input_params,
                    results,
                    gas_composition,
                    file_path,
                    log_file=config.LOG_FILE
                )
            
            dialogs.show_info("Başarılı", f"Rapor başarıyla kaydedildi:\n{file_path}")
            self.status_var.set(f"Rapor kaydedildi: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            dialogs.show_error("Rapor Hatası", f"Rapor kaydedilirken bir hata oluştu:\n{e}")

    def _on_save_data(self):
        """Handle save data menu item."""
        try:
            # Get data from input panel
            data = self.input_panel.get_save_data()
            
            # Check if there's any data to save
            if not data.get("composition"):
                dialogs.show_warning("Kaydetme Hatası", "Kaydedilecek gaz bileşeni yok.")
                return
            
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=FILE_EXTENSION,
                filetypes=[(FILE_TYPE_NAME, f"*{FILE_EXTENSION}"), ("Tüm Dosyalar", "*.*")],
                title="Verileri Kaydet"
            )
            
            if not file_path:
                return
            
            # Save to file
            save_inputs_to_file(data, file_path)
            
            dialogs.show_info("Başarılı", f"Veriler başarıyla kaydedildi:\n{file_path}")
            self.status_var.set(f"Kaydedildi: {file_path}")
            
        except DataSerializationError as e:
            dialogs.show_error("Kaydetme Hatası", str(e))
        except Exception as e:
            self.logger.error(f"Save data failed: {e}", exc_info=True)
            dialogs.show_error("Kaydetme Hatası", f"Beklenmeyen hata: {e}")

    def _on_load_data(self):
        """Handle load data menu item."""
        try:
            # Ask for file path
            file_path = filedialog.askopenfilename(
                defaultextension=FILE_EXTENSION,
                filetypes=[(FILE_TYPE_NAME, f"*{FILE_EXTENSION}"), ("Tüm Dosyalar", "*.*")],
                title="Verileri Aç"
            )
            
            if not file_path:
                return
            
            # Load from file
            data = load_inputs_from_file(file_path)
            
            # Validate data
            if not validate_loaded_data(data):
                dialogs.show_warning("Yükleme Uyarısı", "Dosya formatı beklenen şekilde değil. Bazı veriler yüklenemeyebilir.")
            
            # Apply to input panel
            self.input_panel.set_load_data(data)
            
            dialogs.show_info("Başarılı", f"Veriler başarıyla yüklendi:\n{file_path}")
            self.status_var.set(f"Yüklendi: {file_path}")
            
        except DataSerializationError as e:
            dialogs.show_error("Yükleme Hatası", str(e))
        except Exception as e:
            dialogs.show_error("Yükleme Hatası", f"Beklenmeyen hata: {e}")
            
    def _check_for_updates_manual(self):
        """Check for updates manually triggered by user (runs in background thread)."""
        self.status_var.set("Güncellemeler kontrol ediliyor...")
        self.configure(cursor="watch")

        def _check():
            try:
                checker = UpdateChecker()
                has_update, update_info, status_msg = checker.check_for_updates()
                self.after(0, self._on_update_check_result, has_update, update_info, status_msg)
            except Exception as e:
                self.after(0, self._on_update_check_error, e)

        threading.Thread(target=_check, daemon=True).start()

    def _toggle_startup_update_check(self):
        """Enable/disable the opt-in silent update check on startup."""
        current = bool(preferences.get_preference("check_updates_on_startup", False))
        preferences.set_preference("check_updates_on_startup", not current)
        messagebox.showinfo(
            "Güncelleme",
            "Açılışta sürüm kontrolü etkinleştirildi."
            if not current
            else "Açılışta sürüm kontrolü kapatıldı."
        )

    def _check_for_updates_silent(self):
        """Background update check that only updates the status bar."""
        def _check():
            try:
                checker = UpdateChecker()
                has_update, _, _ = checker.check_for_updates()
                self.after(0, self._on_silent_update_result, has_update)
            except Exception:
                self.after(0, self._on_silent_update_result, False)

        threading.Thread(target=_check, daemon=True).start()

    def _on_silent_update_result(self, has_update: bool) -> None:
        """Handle the silent update check result on the main thread."""
        if has_update:
            self.status_var.set("✨ Yeni sürüm mevcut: Yardım > Güncellemeleri Denetle")
        else:
            self.status_var.set("Hazır.")

    def _on_update_check_result(self, has_update, update_info, status_msg):
        """Handle update check result on main thread."""
        self.configure(cursor="")
        if has_update and update_info:
            msg = (
                f"✨ YENI SÜRÜM MEVCUT!\n\n"
                f"Versiyon: {update_info.get('version')}\n"
                f"Tarih: {update_info.get('date')}\n\n"
                f"Değişiklikler:\n{update_info.get('changelog', '-')}\n"
            )
            if update_info.get('sha256'):
                msg += f"\nSHA-256: {update_info['sha256']}\n"
            msg += "\nİndirme sayfasına gitmek ister misiniz?"
            if messagebox.askyesno("Güncelleme Mevcut", msg):
                UpdateChecker().open_download_page(update_info.get('download_url'))
            self.status_var.set("Hazır.")
        elif status_msg:
            messagebox.showinfo("Güncelleme", status_msg)
            self.status_var.set(status_msg)
        else:
            self.status_var.set("Hazır.")

    def _on_update_check_error(self, error: Exception):
        """Handle update check error on main thread."""
        self.configure(cursor="")
        self.logger.error(f"Manual update check failed: {error}")
        self.status_var.set("Güncelleme kontrolü başarısız.")
