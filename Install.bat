@echo off
setlocal

:: Auto elevate
net session >nul 2>&1
if not %errorlevel%==0 (
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Start-Process '%~f0' -Verb RunAs"
exit /b
)

:: Ask user for confirmation using Windows CMD dialog
::echo Welcome to ...
::echo " _______                  _ ________     ________ _             "
::echo "|__   __|                | |  ____\ \   / /  ____| |            "
::echo "   | |_ __ __ _ _ __  ___| | |__   \ \_/ /| |__  | |_ ___  _ __ "
::echo "   | | '__/ _` | '_ \/ __| |  __|   \   / |  __| | __/ _ \| '__|"
::echo "   | | | | (_| | | | \__ \ | |____   | |  | |____| || (_) | |   "
::echo "   |_|_|  \__,_|_| |_|___/_|______|  |_|  |______|\__\___/|_|   "
::echo.
::echo.

::echo WHAT IS IT?: This is an in-place multilingual screen translation app.
::echo.

::echo PRIVATE: The app is fully local and does not use the internet for anything other than installation. The two AI models it uses will be ran on your hardware without sending any data anywhere or connecting to the internet in any way.
::echo.

::echo REQUIREMENTS: Please make sure you have at least 15GB of free space before installing and are running either Windows 10 or 11. 
::echo.

::echo WHAT WILL THIS INSTALLER DO?: This installer will install TranslEYEtor and the following necessary dependencies: 
::echo - Python3.10 
::echo - PIP
::echo - MSVC Build Tools 2022 
::echo - Vulkan SDK (if AMD GPU present)
::echo - CMAKE
::echo - Llama-cpp-python
::echo - EasyOCR (OCR Model + Python library)
::echo - Hy-MT2 1.8B (translation AI model)
::echo - A TON of python packages.
::echo.

::choice /C YN /M "Do you want to proceed with the installation?"

::if %errorlevel%==2 (
::    echo.
::    echo Installation cancelled by user. Exiting...
::    exit /b
::)

cd /d "%~dp0"

echo ==========================================
echo Installing Python 3.10
echo ==========================================

winget install --id Python.Python.3.10 --exact --accept-package-agreements --accept-source-agreements

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
