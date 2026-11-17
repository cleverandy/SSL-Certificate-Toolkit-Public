@echo off
setlocal
cd /d "%~dp0"
rem Launch the GUI detached from the command prompt (no console dependency).
if exist ".venv\Scripts\pythonw.exe" (
    start "" /D "%~dp0" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py"
    exit /b 0
)
echo Python virtual environment is missing.
echo Run build_windows.bat first, or install requirements.txt in .venv.
echo For console diagnostics, use run_debug_windows.bat.
pause
exit /b 1
