# TranslEYEtor

An experimental private in-place translation
tool made with Python. Leverages 2 local LLMs
for OCR + Translation. High local AI performance,
compatible with CPU only systems
as well as AMD GPUs and NVidia GPUs.

Fully local. Everything happens on your system.
(Internet connection required only for first time use, LLM and OCR models must be downloaded to system to use entirely offline.)

Simply hold CTRL+SHIFT and drag your mouse over any area of your screen - Images, Video Frames, Text - and watch it be translated!

![alt text](https://cdn.prod.website-files.com/6605a1208312719eb249cef4/6a27b837a2786d96aa8e557e_transleyetor.png)

## Current Version
V0.5.5 - Alpha <br>
- App fully reworked
- TranslEYEtor now support multiprocessing
- Translation now runs on a seperate server
- Users can now interrupt translations
- App startup speed greatly increased
- Added tray indicator light for translation state
(in progress, ready, unavailable)
- Installation is now a one-click operation

## Version History
V0.4 - Alpha <br>
- Added basic GUI and tray app
- Added installer

V0.3 - Alpha <br>
- Translator is now literally 500% faster!
- Program now has both AMD and NVidia GPU support for text translation
- Uses EasyOCR (CPU; NVidia GPU only) for OCR
- Uses Hy-MT2 1.8B Q4_K_M via Llama.cpp (CPU; AMD GPU; NVidia GPU) for AI translation
- User can now select screen capture area precisely

V0.2 - Alpha <br>
- Translated text is now visualized on screen around the chosen translation area.
- App now attempts to cache model weights and load them locally.
- Model is now cached near the python script in .model_cache.

V0.1 - Alpha <br>
- Added basic 480p screen capture on CTRL press.

## Notice
App has been tested on a CPU only machine and on an AMD GPU machine.
NVidia GPUs are supported on paper but the program has not been tested with any yet.

## System Requirements
- Windows 10/11
- 10-15GB Free storage space
- Any AVX2 compatible CPU
- Integrated graphics (Optional GPU for faster translation)

## Required Dependencies
- Winget

## How To Install
### Installer
1. Download the release package and run the installer.
2. Install the program anywhere where there are free write permissions. (Do not install to ProgramFiles or C)
3. The installer will ask for your permission to restart the PC.
4. When the PC restarts, installation will continue and then finish.
### Clone
1. Clone the repo
2. Double-click on /scripts/install.bat.
3. The installer will ask for your permission to restart the PC.
4. When the PC restarts, installation will continue and then finish.

