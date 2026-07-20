"""PyInstaller hook for CoolProp.

CoolProp uses compiled C/C++ extensions (.pyd on Windows) that depend on
MSVC runtime DLLs shipped in the coolprop.libs package directory.
"""

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_dynamic_libs,
    collect_data_files,
)
import os
import glob as _glob

hiddenimports = collect_submodules('CoolProp')
hiddenimports = [h for h in hiddenimports if 'tests' not in h and 'Plots' not in h and 'GUI' not in h]

binaries = collect_dynamic_libs('CoolProp')

# Collect coolprop.libs DLLs (MSVC runtime etc.) — critical for .pyd loading
_coolprop_parent = os.path.dirname(os.path.dirname(__import__('CoolProp').__file__))
_libs_dir = os.path.join(_coolprop_parent, 'coolprop.libs')
if os.path.isdir(_libs_dir):
    for _f in os.listdir(_libs_dir):
        _fp = os.path.join(_libs_dir, _f)
        if os.path.isfile(_fp) and _f.endswith(('.dll', '.pyd', '.so')):
            binaries.append((_fp, '.'))

datas = collect_data_files('CoolProp')
datas = [(src, dst) for src, dst in datas if 'tests' not in src and 'Plots' not in src]
