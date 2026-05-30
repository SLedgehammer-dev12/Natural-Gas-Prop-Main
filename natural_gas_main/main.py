"""
Natural Gas Prop Main - Ana Başlatıcı

Uygulamayı başlatır ve GUI'yi gösterir.
"""

import sys
import logging
from pathlib import Path

# Import from package
from natural_gas_main.utils.logger import setup_logging
from natural_gas_main.config.settings import config


def main():
    """
    Ana uygulama başlatıcı.
    
    1. Logging'i yapılandırır
    2. UI modüllerini import eder
    3. Ana pencereyi oluşturur ve başlatır
    """
    import os, tempfile

    # Write startup marker for debugging
    startup_log = os.path.join(tempfile.gettempdir(), "ngp_startup.log")
    try:
        with open(startup_log, "w") as f:
            f.write(f"STARTING Natural Gas Prop Main {config.APP_VERSION}\n")
            f.write(f"Python: {sys.version}\n")
    except Exception:
        pass

    try:
        # Setup logging
        setup_logging(config.LOG_FILE, config.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info(f"Natural Gas Prop Main {config.APP_VERSION} başlatılıyor...")
        logger.info(f"Python versiyonu: {sys.version}")
        logger.info("=" * 60)
        
        try:
            with open(startup_log, "a") as f:
                f.write("LOG_READY\n")
        except Exception:
            pass
        
        # Import UI (delayed to avoid import errors if tkinter not available)
        from natural_gas_main.ui.app import ThermoApp
        
        try:
            with open(startup_log, "a") as f:
                f.write("TKINTER_IMPORT_OK\n")
        except Exception:
            pass
        
        # Create and run application
        logger.info("GUI oluşturuluyor...")
        app = ThermoApp()
        
        try:
            with open(startup_log, "a") as f:
                f.write("GUI_CREATED\n")
        except Exception:
            pass
        
        logger.info("Uygulama başlatıldı - mainloop başlıyor")
        app.mainloop()
        
        logger.info("Uygulama kapatıldı")
        try:
            os.remove(startup_log)
        except Exception:
            pass
        
    except ImportError as e:
        try:
            with open(startup_log, "a") as f:
                f.write(f"IMPORT_ERROR: {e}\n")
        except Exception:
            pass
        print(f"HATA: Gerekli modül bulunamadı: {e}")
        print("Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.")
        sys.exit(1)
        
    except Exception as e:
        import traceback
        try:
            with open(startup_log, "a") as f:
                f.write(f"CRASH: {e}\n{traceback.format_exc()}\n")
        except Exception:
            pass
        print(f"HATA: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
