"""PyInstaller hook for CoolProp.

CoolProp uses compiled C/C++ extensions (.pyd on Windows) and
dynamic imports that PyInstaller cannot detect automatically.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

hiddenimports = collect_submodules('CoolProp')
hiddenimports = [h for h in hiddenimports if 'tests' not in h and 'Plots' not in h and 'GUI' not in h]

binaries = collect_dynamic_libs('CoolProp')

datas = collect_data_files('CoolProp')
datas = [(src, dst) for src, dst in datas if 'tests' not in src and 'Plots' not in src]
