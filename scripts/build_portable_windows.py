import os
import urllib.request
import zipfile
import subprocess
import shutil
import sys

def build_portable():
    print("=== Natural Gas Prop - Portable Windows Build System ===")
    
    # 1. Define paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(root_dir, "dist")
    portable_dir = os.path.join(dist_dir, "Natural-Gas-Prop-Portable")
    python_dir = os.path.join(portable_dir, "python")
    
    # 2. Recreate clean directory structure
    if os.path.exists(portable_dir):
        print(f"Cleaning existing portable directory: {portable_dir}")
        shutil.rmtree(portable_dir)
    os.makedirs(python_dir, exist_ok=True)
    
    # 3. Download official Python Embeddable package (Python 3.11.9, 64-bit)
    embed_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    zip_path = os.path.join(dist_dir, "python-embed.zip")
    
    print(f"Downloading Python embeddable package from: {embed_url}")
    urllib.request.urlretrieve(embed_url, zip_path)
    
    print("Extracting Python embeddable package...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(python_dir)
    os.remove(zip_path)
    
    # 4. Modify python311._pth to enable site-packages and search paths
    pth_file = os.path.join(python_dir, "python311._pth")
    print(f"Configuring python paths in {pth_file}...")
    
    pth_content = """python311.zip
.
..
import site
"""
    with open(pth_file, "w", encoding="utf-8") as f:
        f.write(pth_content)
        
    # 5. Bootstrap pip inside the embedded environment
    pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = os.path.join(python_dir, "get-pip.py")
    print(f"Downloading get-pip.py from: {pip_url}")
    urllib.request.urlretrieve(pip_url, get_pip_path)
    
    python_exe = os.path.join(python_dir, "python.exe")
    print("Bootstrapping pip inside embedded Python...")
    subprocess.run([python_exe, get_pip_path, "--no-warn-script-location"], check=True)
    os.remove(get_pip_path)
    
    # 6. Install application dependencies
    dependencies = [
        "CoolProp>=7.2.0",
        "pydantic>=2.0.0",
        "customtkinter>=5.2.2",
        "matplotlib>=3.10.0",
        "fpdf2>=2.8.0",
        "pyaga8>=0.1.16",
        "packaging>=21.0"
    ]
    print("Installing application dependencies via pip...")
    # Run pip install inside the embedded environment
    subprocess.run([python_exe, "-m", "pip", "install", "--no-cache-dir"] + dependencies, check=True)
    
    # 7. Copy application source files
    print("Copying application source files...")
    app_src = os.path.join(root_dir, "natural_gas_main")
    app_dest = os.path.join(portable_dir, "natural_gas_main")
    
    # Clean copy tree excluding cache files
    shutil.copytree(
        app_src, 
        app_dest, 
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")
    )
    
    # Copy root run-app files and metadata
    shutil.copy2(os.path.join(root_dir, "run_app.py"), portable_dir)
    shutil.copy2(os.path.join(root_dir, "version.json"), portable_dir)
    shutil.copy2(os.path.join(root_dir, "version_info.txt"), portable_dir)
    
    release_notes = os.path.join(root_dir, "RELEASE_NOTES.md")
    if os.path.exists(release_notes):
        shutil.copy2(release_notes, portable_dir)
        
    # 8. Create VBScript launcher (silent startup, no cmd prompt)
    vbs_path = os.path.join(portable_dir, "Natural Gas Prop.vbs")
    print("Creating silent VBScript launcher...")
    
    vbs_content = """Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run "python\\python.exe run_app.py", 0, False
"""
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
        
    print("=== Portable Windows Bundle Built Successfully ===")
    print(f"Location: {portable_dir}")

if __name__ == "__main__":
    build_portable()
