@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    echo Python virtual environment is missing. Run build_windows.bat first.
)
echo.
echo Application exited. Press any key to close this debug window.
pause >nul
