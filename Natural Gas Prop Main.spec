# -*- mode: python ; coding: utf-8 -*-

import pathlib
import sys
import re
import customtkinter
import importlib.util as _importlib_util

customtkinter_path = pathlib.Path(customtkinter.__file__).parent

_neqsim_datas = []
_neqsim_spec = _importlib_util.find_spec("neqsim")
if _neqsim_spec is not None and _neqsim_spec.submodule_search_locations:
    for _loc in _neqsim_spec.submodule_search_locations:
        _jar_dir = pathlib.Path(_loc) / "lib"
        if _jar_dir.is_dir():
            for _jar_file in sorted(_jar_dir.glob("*.jar")):
                _neqsim_datas.append((str(_jar_file), "neqsim/lib"))
            break

# Read version from version_info.txt for output naming
_version = "unknown"
_version_info_path = pathlib.Path("version_info.txt")
if _version_info_path.exists():
    _vtext = _version_info_path.read_text(encoding="utf-8")
    _m = re.search(r"FileVersion',\s*'([^']+)'", _vtext)
    if _m:
        _version = _m.group(1)
    else:
        _m = re.search(r"filevers=\((\d+),\s*(\d+),\s*(\d+)", _vtext)
        if _m:
            _version = f"v{_m.group(1)}.{_m.group(2)}.{_m.group(3)}"

_exe_name = f"Natural Gas Prop Main {_version}" if _version != "unknown" else "Natural Gas Prop Main"

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[(str(customtkinter_path), 'customtkinter/')] + list(_neqsim_datas),
    hiddenimports=[
        'CoolProp.CoolProp',
        'matplotlib.backends.backend_tkagg',
        'PIL',
        'fpdf',
        'pyaga8',
        'customtkinter',
        'packaging',
        'pydantic',
        'neqsim',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

# Common: onedir bootstrap EXE (Windows + macOS)
_exe_kwargs = dict(
    pyz=pyz,
    scripts=a.scripts,
    additional_args=[],
    exclude_binaries=True,
    name=_exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
if sys.platform != 'darwin':
    _exe_kwargs['version'] = 'version_info.txt'
exe = EXE(**_exe_kwargs)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=_exe_name,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{_exe_name}.app',
        icon=None,
        bundle_identifier='com.kompresorpompa.naturalgasprop',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.7.1',
            'CFBundleVersion': '1.7.1.0',
            'CFBundleName': 'Natural Gas Prop Main',
            'CFBundleDisplayName': 'Natural Gas Prop Main',
            'LSMinimumSystemVersion': '10.15',
        },
    )
