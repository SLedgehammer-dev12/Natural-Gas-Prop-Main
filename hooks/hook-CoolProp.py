"""PyInstaller hook for CoolProp.

CoolProp uses compiled C/C++ extensions (.pyd on Windows) and
dynamic imports that PyInstaller cannot detect automatically.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files
import os
import glob as _glob

hiddenimports = collect_submodules('CoolProp')

datas = collect_data_files('CoolProp')

binaries = []
coolprop_dir = os.path.dirname(__import__('CoolProp').__file__)
for pattern in ['*.pyd', '*.dll', '*.so']:
    for match in _glob.glob(os.path.join(coolprop_dir, pattern)):
        binaries.append((match, 'CoolProp'))
