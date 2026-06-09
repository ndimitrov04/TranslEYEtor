# TranslEYEtor
An automatic AI powered screen translator.

## Current Version
V0.4 - Alpha <br>
- Added basic GUI and tray app
- Added installer

## Version History
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
4. When the PC restarts, installation will continue and then finish. You might need to double click on either Main.py or the desktop shortcut if an error occurs.
### Clone
1. Clone the repo
2. Double-click on Install.bat
3. The installer will ask for your permission to restart the PC.
4. When the PC restarts, installation will continue and then finish. You might need to double click on either Main.py or the desktop shortcut if an error occurs.

## Roadmap
1. Better translation - Done
2. Options menu - Done
3. GUI - Done
4. Better screen capture UX - Done
5. OS hooks to show translated text on top of actual text - Done
6. Full screen captures - Done
7. GPU support - Done