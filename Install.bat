@echo off
setlocal

:: Auto elevate
net session >nul 2>&1
if not %errorlevel%==0 (
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Start-Process '%~f0' -Verb RunAs"
exit /b
)

cd /d "%~dp0"

echo ==========================================
echo Installing Python 3.10
echo ==========================================

winget install --id Python.Python.3.10 --exact --accept-package-agreements --accept-source-agreements

echo ==========================================
echo Installing WMI and PYWIN32 extensions
echo ==========================================

python -m pip install wmi pywin32

echo.
echo ==========================================
echo Installing Visual Studio Build Tools
echo ==========================================

winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --override "--wait --passive --includeRecommended --add Microsoft.VisualStudio.Workload.VCTools" --accept-package-agreements --accept-source-agreements

echo.
echo ==========================================
echo Installing VS Code extensions
echo ==========================================

where code >nul 2>&1

if %errorlevel%==0 (
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
code --install-extension ms-vscode.cpptools
code --install-extension eamodio.gitlens
)

echo.
echo ==========================================
echo Preparing PC for restart...
echo ==========================================

schtasks /Create ^
/TN "MainPyInit" ^
/SC ONLOGON ^
/RL HIGHEST ^
/TR ""%~dp0initialize.bat"" ^
/F

echo.
echo ==========================================
echo Installation complete.
echo Press any key to restart your PC and complete the installation.
echo ==========================================

pause

shutdown /r /t 5 /c "Restarting in 5 sec to complete installation"
