"""
Natural Gas Prop Main - Basit Başlatıcı

Bu dosyayı direkt çalıştırabilirsiniz:
    python run_app.py

veya çift tıklayın.
"""

import sys
import os
from pathlib import Path

import tempfile as _tempfile

# Write immediate startup marker for debugging
_STARTUP_LOG = os.path.join(_tempfile.gettempdir(), "ngp_startup.log")
try:
    with open(_STARTUP_LOG, "w") as f:
        f.write(f"BOOT: Natural Gas Prop Main\n")
        f.write(f"Python: {sys.version}\n")
except Exception:
    pass

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    with open(_STARTUP_LOG, "a") as f:
        f.write("IMPORT_MAIN: starting...\n")
except Exception:
    pass

# Import and run main
from natural_gas_main.main import main

if __name__ == "__main__":
    try:
        with open(_STARTUP_LOG, "a") as f:
            f.write("CALL_MAIN\n")
    except Exception:
        pass

    try:
        main()
    except BaseException as exc:
        import traceback as _traceback
        tb = _traceback.format_exc()
        try:
            with open(_STARTUP_LOG, "a") as f:
                f.write(f"FATAL: {exc}\n{tb}\n")
        except Exception:
            pass
        import tkinter as _tk
        try:
            _root = _tk.Tk()
            _root.withdraw()
            _tk.messagebox.showerror(
                "Beklenmeyen Hata",
                f"Uygulama başlatılırken hata oluştu:\n\n{exc}\n\n"
                f"Detaylar: {_STARTUP_LOG}"
            )
            _root.destroy()
        except Exception:
            pass
        sys.exit(1)
