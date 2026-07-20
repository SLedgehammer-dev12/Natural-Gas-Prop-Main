"""PyInstaller hook for neqsim (Java bridge via JPype).

neqsim ships a large JAR file (~52 MB) in neqsim/lib/ that must be
bundled for the Java backend to work at runtime.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import glob as _glob

hiddenimports = collect_submodules('neqsim')
hiddenimports = [h for h in hiddenimports if 'tests' not in h]

datas = collect_data_files('neqsim')
datas = [(src, dst) for src, dst in datas if 'tests' not in src]

# Explicitly collect JAR files
binaries = []
try:
    neqsim_dir = os.path.dirname(__import__('neqsim').__file__)
    lib_dir = os.path.join(neqsim_dir, 'lib')
    if os.path.isdir(lib_dir):
        for f in os.listdir(lib_dir):
            fp = os.path.join(lib_dir, f)
            if os.path.isfile(fp) and f.endswith('.jar'):
                binaries.append((fp, 'neqsim/lib'))
except Exception:
    pass
