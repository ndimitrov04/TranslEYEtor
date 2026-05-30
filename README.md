# TranslEYEtor
An automatic AI powered screen translator.

## Current Version
V0.3 - Alpha <br>
- Translator is now literally 500% faster!
- Program now has both AMD and NVidia GPU support for text translation
- Uses EasyOCR (CPU; NVidia GPU only) for OCR
- Uses Hy-MT2 1.8B Q4_K_M via Llama.cpp (CPU; AMD GPU; NVidia GPU) for AI translation
- User can now select screen capture area precisely

## Version History
V0.2 - Alpha <br>
- Translated text is now visualized on screen around the chosen translation area.
- App now attempts to cache model weights and load them locally.
- Model is now cached near the python script in .model_cache.

V0.1 - Alpha <br>
- Added basic 480p screen capture on CTRL press.

## System Requirements
- Windows 10/11
- Any CPU
- Integrated graphics

## Required Dependencies
- Python 3.13 (on PATH)
- Pip (on PATH)

## How To Use
1. Download and run the Python 3.13 script.
2. Move your mouse over the top-left of an area you want translated and press CTRL.
3. Move your mouse over the bottom-right of an area you want translated and press CTRL again.
4. Wait 5-10 seconds.
5. The text in the image will be translated to English.

## Roadmap
1. Better translation - DONE
2. Options menu
3. GUI
4. Better screen capture UX - In Progress
5. OS hooks to show translated text on top of actual text - DONE
6. Full screen captures - DONE
7. GPU support - In Progress