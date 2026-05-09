# -*- mode: python ; coding: utf-8 -*-

import pathlib
import customtkinter

customtkinter_path = pathlib.Path(customtkinter.__file__).parent

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[(str(customtkinter_path), 'customtkinter/'), ('natural_gas_main', 'natural_gas_main/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Natural Gas Prop Main',
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
