# macOS Development Setup

> **Amac:** Bu skill macOS ortaminda Natural Gas Prop projesi icin gelistirme ortami kurar ve gunluk is akisini tanimlar.
>
> **Hedef platform:** macOS (Apple Silicon / Intel)
>
> **Kapsam:** Phase 1-5 arasi tum kurulum ve gelistirme adimlari

---

## Phase 1: Prerequisites (Ilk Kurulum)

> Bu adimlar **sadece bir kez** calistirilir. macOS'ta paketler brew ile kurulur.

### Check Item 1.1: Homebrew yuklu mu?

```bash
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Check Item 1.2: Python 3.12 kurulumu

```bash
# Kurulu degilse:
brew install python@3.12

# PATH'e ekle (gerekirse):
# Apple Silicon:
echo 'export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"' >> ~/.zshrc

# Intel:
echo 'export PATH="/usr/local/opt/python@3.12/libexec/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
```

### Check Item 1.3: Python dogrulamasi

```bash
python3.12 --version  # 3.12.x olmali
which python3.12
```

### Check Item 1.4: Java 17 (NeqSim icin, istege bagli)

```bash
# Kurulu degilse:
brew install --cask temurin@17

# Java home ayarla:
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 17)' >> ~/.zshrc
source ~/.zshrc

# Dogrula:
java -version  # "17.x.x" olmali
echo $JAVA_HOME  # bos olmamali
```

### Check Item 1.5: Git dogrulamasi

```bash
git --version  # 2.30+ olmali
```

---

## Phase 2: Clone & Environment (Ilk Kurulum)

> Projeyi klonla ve sanal ortami olustur.

### Check Item 2.1: Proje klonlama

```bash
# Hedef dizin:
mkdir -p ~/Projects/kompresor-pompa
cd ~/Projects/kompresor-pompa

# Henuz clone yapilmadiysa:
git clone https://github.com/SLedgehammer-dev12/Natural-Gas-Prop-Main.git
cd Natural-Gas-Prop-Main
```

### Check Item 2.2: Sanal ortam olustur

```bash
python3.12 -m venv .venv
source .venv/bin/activate

# Dogrula:
which python  # .venv/bin/python olmali
python --version
```

### Check Item 2.3: Bagimliliklari yukle

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Check Item 2.4: NeqSim + Java dogrulamasi

```bash
# NeqSim'i yukle:
pip install neqsim>=3.6.1

# Java JVM test:
python -c "import neqsim; print('NeqSim OK')" 2>&1
# Hata yoksa → basarili
# "JVMNotFoundException" varsa → JAVA_HOME kontrol et (Phase 1.4)
```

### Check Item 2.5: Gelistirme araclari

```bash
pip install -r requirements-dev.txt
pip install pyinstaller
```

---

## Phase 3: Verify (Ilk Kurulum)

> Kurulumun dogru oldugunu dogrula.

### Check Item 3.1: Testleri calistir

```bash
pytest -q
```

**Beklenen sonuc:** 630+ passed. Bazilari skip olabilir (JVM yoksa NeqSim testleri). Font testleri macOS'ta PASS almali.

**Hata alinan testler ve cozumleri:**

| Hata | Cozum |
|------|-------|
| `_tkinter` import error | `brew install python-tk@3.12` |
| `JVMNotFoundException` (NeqSim) | `echo $JAVA_HOME` bos mu kontrol et, Phase 1.4'u tekrarla |
| CoolProp import error | `pip install CoolProp --no-build-isolation --force-reinstall` |
| matplotlib backend error | `pip install matplotlib --force-reinstall` |

### Check Item 3.2: Coverage raporu

```bash
pytest --cov=natural_gas_main --cov-report=term
# Hedef: %70+ (CI threshold)
```

### Check Item 3.3: macOS build testi (.app bundle)

```bash
pip install pyinstaller
pyinstaller "Natural Gas Prop Main.spec" --clean --noconfirm

# .app olustugunu dogrula:
ls -d dist/Natural\ Gas\ Prop\ Main*/Natural\ Gas\ Prop\ Main*.app

# Uygulamayi test et (GUI):
open dist/Natural\ Gas\ Prop\ Main*/Natural\ Gas\ Prop\ Main*.app
```

### Check Item 3.4: .dmg olusturma testi

```bash
APP_DIR=$(ls -d dist/"Natural Gas Prop Main"*/ 2>/dev/null | head -1)
VERSION=$(python -c "import json; print(json.load(open('version.json'))['version'].lstrip('v'))")
hdiutil create -volname "Natural Gas Prop" \
  -srcfolder "$APP_DIR" \
  -ov -format UDZO \
  "dist/Natural-Gas-Prop-v${VERSION}.dmg"

# Dogrula:
ls -lh dist/Natural-Gas-Prop-v*.dmg
```

---

## Phase 4: Daily Workflow (Gunluk Calisma)

> Her gun tekrarlanacak is akisi.

### Check Item 4.1: Gun baslangici - Repoyu guncelle

```bash
cd ~/Projects/kompresor-pompa/Natural-Gas-Prop-Main
source .venv/bin/activate

git fetch origin
git checkout main
git pull origin main

# Son degisiklikleri gor:
git log --oneline -10
```

### Check Item 4.2: Yeni is icin feature branch ac

```bash
git checkout main
git pull origin main
git checkout -b feature/ozellik-adi

# Ornek branch isimleri:
# feature/iso6976-module
# fix/aga8-panic
# chore/dependency-update
# test/new-hydrate-tests
```

### Check Item 4.3: Kod gelistirme dongusu

```bash
# 1. Kodu yaz

# 2. Testleri calistir (her degisiklikte):
pytest -q

# 3. Belirli test dosyasi icin:
pytest tests/test_calculator.py -v

# 4. Coverage kontrol:
pytest --cov=natural_gas_main --cov-report=term | grep TOTAL

# 5. Commit'le:
git add -A
git commit -m "feat: ozellik aciklamasi"
```

### Check Item 4.4: Commit turleri

| Prefix | Kullanim |
|--------|----------|
| `feat:` | Yeni ozellik |
| `fix:` | Hata duzeltme |
| `chore:` | Bakim isleri |
| `test:` | Test ekleme/duzeltme |
| `build:` | Build/deploy isleri |
| `docs:` | Dokumantasyon |
| `style:` | Kod formati |
| `refactor:` | Yeniden duzenleme |

### Check Item 4.5: Is bitimi - Push et

```bash
# Tum degisiklikleri commit'le ve push'la:
git add -A
git commit -m "feat: ozellik aciklamasi"
git push -u origin feature/ozellik-adi
```

### Check Item 4.6: Cihaz degistirme (macOS → Windows gecisi)

```bash
# macOS'ta:
git push  # her seyi push et

# Windows'ta sonra:
git fetch origin
git checkout feature/ozellik-adi
git pull origin feature/ozellik-adi
```

---

## Phase 5: Build & Release (Surum Cikarma)

> macOS icin .app ve .dmg olusturma.

### Check Item 5.1: Sifirdan temiz build

```bash
# .venv aktif olsun
source .venv/bin/activate

# Eski dist temizle:
rm -rf build dist

# Build:
pyinstaller "Natural Gas Prop Main.spec" --clean --noconfirm
```

### Check Item 5.2: .app'i test et

```bash
# Karantina bayragini temizle (macOS gatekeeper):
xattr -cr dist/Natural\ Gas\ Prop\ Main*/Natural\ Gas\ Prop\ Main*.app

# Calistir:
open dist/Natural\ Gas\ Prop\ Main*/Natural\ Gas\ Prop\ Main*.app
```

### Check Item 5.3: .dmg paketle

```bash
VERSION=$(python -c "import json; print(json.load(open('version.json'))['version'].lstrip('v'))")
APP_DIR=$(ls -d dist/Natural\ Gas\ Prop\ Main*/ 2>/dev/null | head -1)

hdiutil create -volname "Natural Gas Prop" \
  -srcfolder "$APP_DIR" \
  -ov -format UDZO \
  "dist/Natural-Gas-Prop-v${VERSION}.dmg"

ls -lh dist/Natural-Gas-Prop-v${VERSION}.dmg
```

### Check Item 5.4: Surum bump ve release (CI trigger)

```bash
# Yeni surum:
python scripts/bump_version.py 1.7.1

# Cikan degisiklikleri kontrol et:
git diff

# Commit, tag ve push:
git add -A
git commit -m "build: bump to v1.7.1"
git tag v1.7.1
git push origin main --tags

# CI otomatik olarak:
# - Windows .exe build eder
# - macOS .dmg build eder
# - GitHub Release'e ekler
```

---

## Troubleshooting (Genel)

| Sorun | Belirti | Cozum |
|-------|---------|-------|
| `brew` bulunamiyor | `command not found: brew` | Homebrew'u kur: Phase 1.1 |
| `_tkinter` import error | `ModuleNotFoundError: No module named '_tkinter'` | `brew install python-tk@3.12` |
| Java JVM bulunamiyor | `JVMNotFoundException` | `echo $JAVA_HOME` kontrol et, Phase 1.4 tekrarla |
| CoolProp derleme hatasi | `error: command 'gcc' failed` | `brew install cmake gcc`, sonra `pip install CoolProp --no-build-isolation` |
| `.app` acilmiyor | "app cannot be opened because it is from an unidentified developer" | `xattr -cr dist/NGP.app` veya System Preferences → Security |
| `git push` reddedildi | `Permission denied` | `git remote -v` kontrol et, HTTPS token veya SSH key ekle |
| Line ending uyarisi | `git diff` tum dosyayi degismis gosteriyor | `git add --renormalize . && git commit -m "chore: normalize line endings"` |
| Sanal ortam calismiyor | `.venv/bin/activate` bulunamiyor | `python3.12 -m venv .venv` ile yeniden olustur |
| opencode config tutarsiz | Iki makinede farkli davranis | `.opencode/` git'te takip ediliyor, `git pull` ile guncelle |
| pip cache sorunu | `pip install` eski paket | `pip cache purge && pip install -r requirements.txt` |

---

## Hizli Referans

```bash
# Gun baslangici
git checkout main && git pull origin main

# Yeni is
git checkout -b feature/xxx

# Kod → test → commit
pytest -q && git add -A && git commit -m "type: desc"

# Push
git push -u origin feature/xxx

# macOS build
pyinstaller "Natural Gas Prop Main.spec" --clean --noconfirm
hdiutil create -volname "NGP" -srcfolder "dist/NGP..." -ov -format UDZO "dist/NGP.dmg"
```
