@echo off
setlocal
cd /d "%~dp0"
title SSL Certificate Toolkit v3.4.2 - Windows Build

echo ======================================================
echo   SSL Certificate Toolkit v3.4.2 - EXE Builder
echo ======================================================
echo.
echo Windows x64 + Python 3.12 recommended.
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher 'py' was not found.
  echo Install Python 3.12 x64 with the launcher enabled.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] Creating virtual environment...
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 (
    echo Python 3.12 was not found; trying the default Python.
    py -m venv .venv
  )
  if errorlevel 1 goto :error
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

echo [2/5] Installing dependencies... (internet required for first install)
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/5] Checking Qt installation...
python -c "import PySide6.QtWidgets; import cryptography; print('PySide6 and cryptography available')"
if errorlevel 1 goto :error

echo [4/5] Running certificate logic tests...
python -m unittest discover -s tests -q
if errorlevel 1 goto :error

echo [5/5] Building standalone Windows EXE with UI assets...
python -m PyInstaller --noconfirm --clean --onefile --windowed --add-data "assets;assets" --version-file windows_version_info.txt --name SSL_Certificate_Toolkit_v3.4.2 app.py
if errorlevel 1 goto :error

echo.
echo BUILD SUCCESSFUL
echo   %CD%\dist\SSL_Certificate_Toolkit_v3.4.2.exe
echo.
echo Test the EXE on Windows and verify a non-production certificate chain before production use.
pause
exit /b 0

:error
echo.
echo BUILD FAILED: see the error messages above.
pause
exit /b 1
