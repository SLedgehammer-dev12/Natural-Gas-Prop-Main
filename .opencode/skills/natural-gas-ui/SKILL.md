---
name: natural-gas-ui
description: "Expert skill for the Natural Gas Prop Main UI layer. Covers the customtkinter application window (ThermoApp), input panel (gas composition, presets, pie chart, conditions), output panel (TreeView results, KPI dashboard, Z-factor comparison table, phase envelope plot, log viewer), dialogs (HEOS warnings, heating value warnings, about, update dialogs), and report generator (PDF/text). USE FOR: modifying app.py, input_panel.py, output_panel.py, dialogs.py; fixing UI bugs; adding UI features; changing layout; working with CTk widgets; matplotlib figure embedding; TreeView configuration; theme/appearance changes; PDF report customization. DO NOT USE FOR: calculation engine changes (hand off to natural-gas-calc), writing tests (hand off to natural-gas-test), build/release tasks (hand off to natural-gas-build)."
license: Proprietary - Kompresör Pompa
metadata:
  author: Kompresör Pompa
  version: "1.4.0"
---

# Natural Gas Prop UI Development

CustomTkinter-based GUI with PanedWindow layout, KPI dashboard, TreeView results, matplotlib phase envelope, and PDF report generation.

## Quick Reference

| Property | Description |
|----------|-------------|
| **Framework** | customtkinter 5.2+ with tkinter fallbacks |
| **Layout** | `tk.PanedWindow` (horizontal split, user-adjustable sash) |
| **Panels** | InputPanel (left), OutputPanel (right, CTkTabview tabs) |
| **Charts** | Pie chart (input panel), Phase envelope (output panel) |
| **Reports** | PDF (fpdf2) + Text, with Unicode font support |
| **Themes** | System/Dark/Light + blue/green/dark-blue color themes |

## When to Use This Skill

- ✅ Modifying `app.py` (ThermoApp) — the main 658-line window class
- ✅ Working with `input_panel.py` (792 lines) — gas composition, pie chart, conditions
- ✅ Working with `output_panel.py` (704 lines) — results, KPI, comparison, phase, logs
- ✅ Modifying `dialogs.py` (277 lines) — HEOS warnings, about, update dialogs
- ✅ Adding/removing KPI dashboard cards
- ✅ Changing TreeView column layouts or dynamic resize logic
- ✅ Fixing matplotlib figure embedding or responsive resize
- ✅ Customizing PDF report layout via `report_generator.py` (391 lines)
- ✅ Adding new theme/mode options
- ✅ Changing unit system display logic

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `natural_gas_main/ui/app.py` | Main ThermoApp window | 658 |
| `natural_gas_main/ui/input_panel.py` | Gas composition + conditions | 792 |
| `natural_gas_main/ui/output_panel.py` | Results display + charts | 704 |
| `natural_gas_main/ui/dialogs.py` | Dialog windows | 277 |
| `natural_gas_main/utils/report_generator.py` | PDF/Text report generation | 391 |
| `natural_gas_main/utils/data_serializer.py` | Save/load .ngp files | 123 |
| `natural_gas_main/utils/updater.py` | GitHub update checker | 68 |
| `natural_gas_main/config/preferences.py` | User preference persistence | 59 |
| `natural_gas_main/config/settings.py` | UI constants (window size, themes) | 231 |

## Layout Architecture

```
ThermoApp (ctk.CTk)
├── Menu bar (Dosya, Görünüm, Yardım)
├── tk.PanedWindow (horizontal)
│   ├── LEFT: InputPanel (minsize=430)
│   │   ├── 1. Gaz Kompozisyonu (PanedWindow: list + rows + pie)
│   │   ├── 2. Referans Standart Koşullar
│   │   ├── 3. İşletme Koşulları (T, P)
│   │   ├── 4. Hacim ve Metot
│   │   └── [Hesapla] button + ProgressBar
│   └── RIGHT: OutputPanel (minsize=380, stretch="always")
│       ├── CTkTabview
│       │   ├── Tab "Sonuçlar"
│       │   │   ├── KPI Dashboard (4 cards: Z, ρ, M, HHV)
│       │   │   ├── Unit System ComboBox
│       │   │   ├── Results TreeView (Özellik | Değer | Birim)
│       │   │   └── Comparison TreeView (9 columns)
│       │   ├── Tab "Faz Diyagramı"
│       │   │   └── Matplotlib Phase Envelope + Toolbar
│       │   └── Tab "Loglar"
│       │       └── Filtered log viewer
│       └── [Profesyonel PDF Raporu Oluştur] button
└── Status bar (StringVar, ProgressBar)
```

## UI State Machine

```
Button States:
  IDLE      → state=normal, text="Hesapla",     color=#4CAF50 (green)
  RUNNING   → state=disabled, text="Hesaplanıyor...", color=#FFA500 (orange)
  ERROR     → state=normal,  text="Hata! Tekrar Dene", color=#F44336 (red)
  └─ Auto-reset to IDLE when user modifies any input field
```

## Matplotlib Configuration

- **Pie chart:** `Figure(figsize=(3, 3), dpi=80)` with `<Configure>` responsive resize
- **Phase envelope:** `Figure(figsize=(5, 4), dpi=100)` with responsive resize
- **Throttling:** Pie chart redraws are throttled to max 60ms intervals (`self.after(60, ...)`)
- **Theme:** Both figures auto-update background/text colors on appearance mode change

## Handoff

- **Calculation engine changes** → [natural-gas-calc](../natural-gas-calc/SKILL.md)
- **Writing/running tests** → [natural-gas-test](../natural-gas-test/SKILL.md)
- **Build & release** → [natural-gas-build](../natural-gas-build/SKILL.md)
