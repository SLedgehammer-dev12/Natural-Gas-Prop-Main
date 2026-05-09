import os

def replace_in_file(filepath, old_text, new_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"Could not find target text in {filepath}")

# 1. requirements.txt
with open("requirements.txt", 'a', encoding='utf-8') as f:
    f.write("\npyaga8>=0.1.16\n")

# 2. settings.py
replace_in_file(
    "natural_gas_main/config/settings.py",
    'default=["HEOS", "SRK", "PR"],',
    'default=["GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR"],'
)
replace_in_file(
    "natural_gas_main/config/settings.py",
    'default="HEOS",\n        description="Default CoolProp backend"',
    'default="GERG-2008",\n        description="Default CoolProp/AGA8 backend"'
)

# 3. ui/input_panel.py
# Update dropdown values dynamically - it already reads from config.AVAILABLE_BACKENDS
print("input_panel is dynamic, no changes needed for options.")

