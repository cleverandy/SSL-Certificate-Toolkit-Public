@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (set "PYTHON=py -3") else (set "PYTHON=python")

echo [1/2] Preview and validate source files...
%PYTHON% github_publisher.py
if errorlevel 1 goto failed
echo.
echo WARNING: Current GitHub Actions can AUTO-PUBLISH a public Release when main is updated.
echo Only continue after approving that effect.
choice /M "Publish to GitHub main and allow its automated Release"
if errorlevel 2 goto canceled
if errorlevel 1 (
 echo [2/2] Publishing to GitHub...
 %PYTHON% github_publisher.py --publish --allow-auto-release
 if errorlevel 1 goto failed
)
echo.
echo GitHub publish completed. Inspect GitHub Actions for build status.
pause
exit /b 0
:failed
echo.
echo Publishing stopped; see error above. Do not assume main changed.
pause
exit /b 1
:canceled
echo.
echo Cancelled; no changes published.
pause
exit /b 0
