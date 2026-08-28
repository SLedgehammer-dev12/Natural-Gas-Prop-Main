#!/usr/bin/env python3
"""
sync_mobile_core.py - Synchronize desktop core modules into the Android project.

Copies the shared computation engine (natural_gas_main/models, core, config,
utils) into the Chaquopy Python source directory of the Android app so the
mobile build stays in sync with the desktop codebase.

The mobile app must NOT receive UI code (customtkinter/tkinter) or the
desktop entry points (main.py, __main__.py) because those do not run under
Chaquopy/Android.

Usage:
    python scripts/sync_mobile_core.py
    python scripts/sync_mobile_core.py --target "path/to/app/src/main/python"
    python scripts/sync_mobile_core.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

DESKTOP_PKG = Path(__file__).resolve().parents[1] / "natural_gas_main"
DEFAULT_TARGET = (
    Path(__file__).resolve().parents[1]
    / "Mobile App"
    / "app"
    / "src"
    / "main"
    / "python"
)

# Desktop-only code that must never be shipped to Android.
EXCLUDED_SUBDIRS = {"ui"}
EXCLUDED_FILES = {"main.py", "__main__.py"}


def sync(source: Path, target: Path, dry_run: bool = False) -> int:
    """Copy core .py files from the desktop package into the mobile source dir."""
    if not source.is_dir():
        print(f"HATA: Kaynak paket bulunamadı: {source}")
        return 1

    copied = 0
    for py_file in sorted(source.rglob("*.py")):
        rel = py_file.relative_to(source)
        if any(part in EXCLUDED_SUBDIRS for part in rel.parts):
            continue
        if rel.parts[-1] in EXCLUDED_FILES:
            continue
        dest = target / rel
        if dry_run:
            print(f"[dry-run] {rel} -> {dest}")
            copied += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py_file, dest)
        copied += 1

    print(
        f"Senkronize edildi: {copied} dosya {'(dry-run)' if dry_run else ''} -> {target}"
    )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Hedef Android Chaquopy Python kaynak dizini",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kopyalamadan yalnızca kopyalanacak dosyaları listele",
    )
    args = parser.parse_args(argv)
    return sync(DESKTOP_PKG, args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())