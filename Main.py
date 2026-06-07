#  _______                  _ ________     ________ _             
# |__   __|                | |  ____\ \   / /  ____| |            
#    | |_ __ __ _ _ __  ___| | |__   \ \_/ /| |__  | |_ ___  _ __ 
#    | | '__/ _` | '_ \/ __| |  __|   \   / |  __| | __/ _ \| '__|
#    | | | | (_| | | | \__ \ | |____   | |  | |____| || (_) | |   
#    |_|_|  \__,_|_| |_|___/_|______|  |_|  |______|\__\___/|_|   
                                                                                                                      

# WARNING! - DO NOT RUN THIS FILE BEFORE RUNNING INSTALL.BAT FOR THE FIRST TIME!

# This is an experimental screen translation app.
# This program uses two local AI models (OCR + TranslationLLM)
# in order to translate screen text in-place.

# How to use:
#   - Hold CTRL+SHIFT and drag your mouse over an area you want translated.

# This program requires:
#    - Windows 10/11
#    - Winget
#    - At least 15GB of free storage space

# This program will automatically download:
#   - Python 3.10
#   - PIP
#   - MSVC Build Tools 2022
#   - Vulkan SDK (if AMD GPU is detected)
#   - CMAKE
#   - Llama.cpp
#   - The Hy-MT2 1.8B text translation model from huggingface
#   - A TON of python packages


# Create a safe from name overflow temp location (%appdata% -> path too long)
# --------------------------------------------------------------------------------
import os
import tempfile
SAFE_TEMP = r"C:\temp"
os.makedirs(SAFE_TEMP, exist_ok=True)
os.environ["TEMP"] = SAFE_TEMP
os.environ["TMP"] = SAFE_TEMP
tempfile.tempdir = SAFE_TEMP
# --------------------------------------------------------------------------------

import Init

print(f"Starting TranslEYEtor V{Init.version} Alpha...")

import Globals
from Install import *
from TranslationWorker import *
from GUI import *

# Main App
# ================================================================================

# App functions
# --------------------------------------------------------------------------------
# Called from TranslationWorker thread via screenhot_ready signal
# Shows captured screen area
def show_frame(coords, capture_area):
    frame = ScreenshotFrame(capture_area)
    frame.move(coords[0], coords[1])
    frame.show()
    Globals.frames.append(frame)

# Called from TranslationWorker thread via translation_ready signal
# Shows translated text in a new window near the captured screenshot
def show_translation(text, coords, dimensions, font_size):
    window = TranslationWindow(text, dimensions, font_size)
    try:
        window.move(coords[0], coords[1])
    except Exception as e:
        print(e)
    window.show()
    Globals.windows.append(window)

def translation_done():
    if len(Globals.frames) > 0:
        Globals.frames[0].start_fade_out()
# --------------------------------------------------------------------------------


# App initialization
# --------------------------------------------------------------------------------
# Start app
app = QApplication(sys.argv)
main_windows = []

# Initialize selection window (For dragging GUI)
main_windows.append(SelectionWindow())
main_windows[0].show()
main_windows[0].move(0,0)
# Resize window so it is fullscreen
screen = app.primaryScreen()
main_windows[0].resize(screen.size().width(), screen.size().height())

# Initialize option window (tray)
main_windows.append(TrayApp())
main_windows[1].show()

# Initialize worker & thread
worker = TranslationWorker()
worker_thread = QThread()
worker.moveToThread(worker_thread)

# Connect signal to GUI slot
worker.screenshot_ready.connect(show_frame)
worker.translation_ready.connect(show_translation)
worker.translation_finished.connect(translation_done)
worker_thread.started.connect(worker.run)

# Start the background loop
worker_thread.start()

# Start Qt Event Loop (this runs until app.quit())
sys.exit(app.exec())
# --------------------------------------------------------------------------------
# ================================================================================
