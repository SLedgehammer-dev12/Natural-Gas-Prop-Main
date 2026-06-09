# -*- mode: python ; coding: utf-8 -*-

import pathlib
import sys
import re
import customtkinter

customtkinter_path = pathlib.Path(customtkinter.__file__).parent

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
    datas=[(str(customtkinter_path), 'customtkinter/')],
    hiddenimports=[
        'CoolProp.CoolProp',
        'matplotlib.backends.backend_tkagg',
        'PIL',
        'fpdf',
        'pyaga8',
        'customtkinter',
        'packaging',
        'neqsim',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    # macOS: onedir + COLLECT + BUNDLE (.app bundle)
    exe = EXE(
        pyz,
        a.scripts,
        [],
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
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=_exe_name,
    )
    app = BUNDLE(
        coll,
        name=f'{_exe_name}.app',
        icon=None,
        bundle_identifier='com.kompresorpompa.naturalgasprop',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.6.0',
            'CFBundleVersion': '1.6.0.0',
            'CFBundleName': 'Natural Gas Prop Main',
            'CFBundleDisplayName': 'Natural Gas Prop Main',
            'LSMinimumSystemVersion': '10.15',
        },
    )
else:
    # Windows/Linux: onefile EXE (standalone)
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=_exe_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        version='version_info.txt',
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
