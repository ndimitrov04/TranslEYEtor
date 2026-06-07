@echo off

:: Auto elevate
net session >nul 2>&1
if not %errorlevel%==0 (
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Start-Process '%~f0' -Verb RunAs"
exit /b
)

cd /d "%~dp0"

echo ==========================================
echo Installing WMI and PYWIN32 extensions
echo ==========================================

python -m pip install wmi pywin32

timeout /t 3 >nul

echo Cleaning up installation setup...

schtasks /Delete /TN "MainPyInit" /F >nul 2>&1


echo Starting TranslEYEtor for the first time...

start "" py -3.10 "%~dp0Main.py"
