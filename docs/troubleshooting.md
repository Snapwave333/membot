---
layout: default
title: Troubleshooting Index
---

# Troubleshooting Index

Below are common issues encountered during development, packaging, or running the desktop app, with quick diagnosis and fixes.

<details>
  <summary>Table of Contents</summary>

- [Electron launcher ENOENT (cannot find python.exe)](#electron-launcher-enoent-cannot-find-pythonexe)
- [Dependency resolution conflicts (pip pins)](#dependency-resolution-conflicts-pip-pins)
- [Electron Forge EBUSY under OneDrive sync](#electron-forge-ebusy-under-onedrive-sync)
- [Python version incompatibilities (3.13)](#python-version-incompatibilities-313)
- [Quick checks](#quick-checks)
- [Logs & diagnostics](#logs--diagnostics)

</details>

## Electron launcher ENOENT (cannot find python.exe)

Symptoms:
- Error shows `spawn ... python.exe ENOENT` when starting via Electron or installer

Likely causes:
- No virtual environment present at expected path
- Path mismatch between dev and installed app
- Incorrect `PYTHONPATH`/working directory

Fix (development):
```powershell
# From repo root
py -3.12 -m venv venv  # or py -3.11
venv\Scripts\pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt
```
Ensure Electron launcher expects `../venv/Scripts/python.exe` relative to `electron/` when running `npm start`.

Fix (installed app v1.0.x):
```powershell
# Create venv under installed resources
$AppVer = '1.0.1'  # match your installed version
$AppRoot = "$env:LOCALAPPDATA\NeoMemeMarkets\app-$AppVer\resources"
python -m venv "$AppRoot\venv"
& "$AppRoot\venv\Scripts\pip" install -r "$env:USERPROFILE\Downloads\requirements.txt"
```
Alternatively, consider shipping a bundled Python runtime via PyInstaller and adding it to Forge `extraResources`.

## Dependency resolution conflicts (pip pins)

Symptoms:
- Build failures compiling `solders/solana`, websocket version mismatches

Recommended pins:
```text
solana==0.32.0
solders==0.20.0
websockets==11.0
```

Additional steps:
```bash
pip install --upgrade pip setuptools wheel
# If using Python 3.13, downgrade to Python 3.12 or 3.11
```

## Electron Forge EBUSY under OneDrive sync

Symptoms:
- Packaging fails with `EBUSY: resource busy or locked` on rename/copy

Cause:
- OneDrive file sync interferes with Forge temporary files

Fix:
- Build outside OneDrive-managed folders, e.g., `C:\membot-build\electron`
- Exclude the project path from OneDrive sync

## Python version incompatibilities (3.13)

Symptoms:
- CFFI and native package build errors on Python 3.13

Fix:
- Prefer Python 3.12 or 3.11
- Create versioned venv explicitly:
```powershell
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Quick checks

- `python --version` returns 3.11/3.12
- `pip list` shows `solana`, `solders`, `websockets` with recommended versions
- Electron launcher points to the correct venv path
- `.env` exists and contains expected keys (for live mode)

## Logs & diagnostics

- App logs: `logs/` under repo or installed app data dir
- Electron logs: `electron/logs/`
- Windows Event Viewer for installer runtime issues

If problems persist, open an issue with logs and system details.
