#!/usr/bin/env python3
"""
Version bump script for Natural Gas Prop Main.

Updates all version references across the project to ensure consistency.

Usage:
    python scripts/bump_version.py v1.5.3
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def error(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_version(v: str) -> tuple:
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", v)
    if not m:
        error(f"Invalid version format '{v}'. Expected e.g. v1.5.3 or 1.5.3")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_settings(v: str, v_no_v: str):
    path = ROOT / "natural_gas_main" / "config" / "settings.py"
    text = path.read_text("utf-8")

    text = re.sub(
        r'(APP_VERSION:\s*str\s*=\s*Field\(\s*default\s*=\s*)"[^"]*"',
        f'\\1"{v}"',
        text,
    )
    text = re.sub(
        r'(WINDOW_TITLE:\s*str\s*=\s*Field\(\s*default\s*=\s*)"[^"]*"',
        f'\\1"Termodinamik Gaz Karışımı Hesaplayıcı (Sürüm {v} - Modüler)"',
        text,
    )

    path.write_text(text, "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def bump_pyproject(v_no_v: str):
    path = ROOT / "pyproject.toml"
    text = path.read_text("utf-8")

    text = re.sub(
        r'^version\s*=\s*"[^"]*"',
        f'version = "{v_no_v}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )

    path.write_text(text, "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def bump_version_json(v: str):
    path = ROOT / "version.json"
    data = json.loads(path.read_text("utf-8"))

    data["version"] = v
    data["date"] = date.today().isoformat()
    data["download_url"] = (
        f"https://github.com/SLedgehammer-dev12/Natural-Gas-Prop-Main/releases/tag/{v}"
    )

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def bump_version_info(v: str, vi: tuple):
    path = ROOT / "version_info.txt"
    text = path.read_text("utf-8")

    text = re.sub(
        r"filevers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)",
        f"filevers=({vi[0]}, {vi[1]}, {vi[2]}, 0)",
        text,
    )
    text = re.sub(
        r"prodvers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)",
        f"prodvers=({vi[0]}, {vi[1]}, {vi[2]}, 0)",
        text,
    )
    text = re.sub(
        r"(FileVersion',\s*')[^']*'",
        f"\\1{v}'",
        text,
    )
    text = re.sub(
        r"(ProductVersion',\s*')[^']*'",
        f"\\1{v}'",
        text,
    )

    path.write_text(text, "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def bump_spec(v: str, vi: tuple):
    path = ROOT / "Natural Gas Prop Main.spec"
    text = path.read_text("utf-8")

    text = re.sub(
        r"CFBundleShortVersionString',\s*'[^']*'",
        f"CFBundleShortVersionString', '{vi[0]}.{vi[1]}.{vi[2]}'",
        text,
    )
    text = re.sub(
        r"CFBundleVersion',\s*'[^']*'",
        f"CFBundleVersion', '{vi[0]}.{vi[1]}.{vi[2]}.0'",
        text,
    )

    path.write_text(text, "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def bump_dialogs(v: str):
    path = ROOT / "natural_gas_main" / "ui" / "dialogs.py"
    text = path.read_text("utf-8")

    # Update about dialog version text
    text = re.sub(
        r"Sürüm v[\d.]+ - Profesyonel Sürüm",
        f"Sürüm {v} - Profesyonel Sürüm",
        text,
    )
    text = re.sub(
        r"v[\d.]+ sürümü:",
        f"{v} sürümü:",
        text,
    )

    # Update show_new_features_info title and version reference
    text = re.sub(
        r'dialog\.title\(f"Yenilikler - Sürüm [^"]*"\)',
        f'dialog.title(f"Yenilikler - Sürüm {v}")',
        text,
    )
    text = re.sub(
        r'f"🚀 DOĞAL GAZ PROP - SÜRÜM [^"]*"',
        f'f"🚀 DOĞAL GAZ PROP - SÜRÜM {v}"',
        text,
    )
    text = re.sub(
        r'if version == "[^"]*":',
        f'if version == "{v}":',
        text,
    )

    path.write_text(text, "utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py v1.5.3")
        sys.exit(1)

    new_version = sys.argv[1].strip()
    if not new_version.startswith("v"):
        error("Version must start with 'v', e.g. v1.5.3")

    vi = parse_version(new_version)
    v_no_v = new_version.lstrip("v")

    print(f"\nBumping version to {new_version} ({v_no_v})\n")

    bump_settings(new_version, v_no_v)
    bump_pyproject(v_no_v)
    bump_version_json(new_version)
    bump_version_info(new_version, vi)
    bump_spec(new_version, vi)
    bump_dialogs(new_version)

    print(f"\n✅ All version references updated to {new_version}")
    print("⚠  Update RELEASE_NOTES.md and show_new_features_info content manually.")
    print("   Then commit, tag, and push:\n")
    print(f"    git add -A")
    print(f'    git commit -m "chore: bump version to {new_version}"')
    print(f"    git tag {new_version}")
    print(f"    git push && git push --tags\n")


if __name__ == "__main__":
    main()
