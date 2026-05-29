#  _______                  _ ________     ________ _             
# |__   __|                | |  ____\ \   / /  ____| |            
#    | |_ __ __ _ _ __  ___| | |__   \ \_/ /| |__  | |_ ___  _ __ 
#    | | '__/ _` | '_ \/ __| |  __|   \   / |  __| | __/ _ \| '__|
#    | | | | (_| | | | \__ \ | |____   | |  | |____| || (_) | |   
#    |_|_|  \__,_|_| |_|___/_|______|  |_|  |______|\__\___/|_|   
                                                                                                                      

# This is an experimental screen translation app.
# This program uses a local AI OCR model to translate
# screen text in-place.

# How to use:
#    1. Mouse over any on screen text
#    2. Press CTRL
#    3. Wait
#    4. A translation will appear over your chosen text

# This program requires:
#    - Python 3.13
#    - PIP

import subprocess
import sys
import math
import time

print("Starting TranslEYEtor V0.2.5 Alpha...")

def abort_program():
    input("FAILURE: Press Enter to exit...")
    exit()

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Detect GPU avalability and type
subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi", "pywin32"])
import wmi
c = wmi.WMI()
gpu_found = False
for gpu in c.Win32_VideoController():
    name = gpu.Name
    name = name.lower()
    if "nvidia" in name:
        print("NVIDIA GPU:", gpu.name)
        print("Installing llama-cpp /w CUDA...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--extra-index-url",
            "https://abetlen.github.io/llama-cpp-python/whl/cu124"
        ])
        gpu_found = True
        break
    elif "amd" in name or "radeon" in name:
        print("AMD GPU:", gpu.name)
        print("Installing llama-cpp /w VULKAN...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--extra-index-url",
            "https://abetlen.github.io/llama-cpp-python/whl/vulkan"
        ])
        gpu_found = True
        break
    else:
        print("Unsupported GPU:", gpu.name)

if not gpu_found:
    print("No compatible GPUs found.")
    print("Installing llama-cpp for CPU infernece...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python"
    ])

# Install required packages
try:
    # AI Dependencies
    install("easyocr")
    # Utilities
    install("pyautogui")    # Mouse macros, screenshots
    install("keyboard")     # Keyboard macros and detection
    install("PyQt6")        # GUI library
    # ...
    print("All necessary dependencies are present...")
except Exception:
    print("Dependency installation failure!!!")
    abort_program()


# Import installed dependencies
# AI
import easyocr
from llama_cpp import Llama
from PIL import Image
# Utilities
import pyautogui
import keyboard
# PyQt6 dependencies
from PyQt6.QtCore import Qt, QObject, QThread, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QPainter, QPen, QColor

# System
import os       # For CWD
import ctypes   # For OS level window clickthrough

# Set current working directory to python script location
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define a permanent cache directory
MODEL_CACHE_DIR = ".model_cache"
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# Load Hy-MT2 - Text translation model
model_id = ".model_cache/Hy-MT2-1.8B-Q8_0.gguf"
try:
    translation_model = Llama(model_path=model_id, n_gpu_layers=0)
except Exception as e:
    # Abort program if model is not available online or offline
    print("Transformer text translation model not present and cannot be fetched from the web! (Check your internet connection.)")
    print("ERROR: " + str(e))
    abort_program()


# Options
# User options
native_language = "English"
translation_hotkey = "ctrl"
#capture_area = 240 # Capture 480p image
# System options
IMAGE_NAME = ".screenshot.png"
MAX_TOKENS = 256                # Small token size for testing
#TERMINATOR = f"</think>\n\n"    # Mini CPM output terminator;
                                # Anything before this is either AI thought or user input data

# Capture screen around current mouse position
def capture_screen(image_name, top_left, bottom_right):
    screenshot_pos = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
    capture_area = (bottom_right[0] - top_left[0], bottom_right[1] - top_left[1])
    pyautogui.screenshot(
        image_name,
        region=(
            top_left[0],
            top_left[1], 
            bottom_right[0] - top_left[0],
            bottom_right[1] - top_left[1]
            )
    )
    return screenshot_pos, capture_area

#print(f"How to use:\nPress {translation_hotkey} to translate a {capture_area} pixel area around your mouse cursor...")

frames = []
windows = []

# AI Translation Module
class TranslationWorker(QObject):

    screenshot_ready = pyqtSignal(tuple, tuple)
    translation_ready = pyqtSignal(str, tuple, tuple, int)
    translation_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):

        # Example language list
        lang_list=["ru","rs_cyrillic","be","bg","uk","mn","en"]
        easy_reader = easyocr.Reader(lang_list)

        while self.running:

            print(f"Awaiting {translation_hotkey} press...")

            try:
                # Capture screen top_left
                keyboard.wait(translation_hotkey)
                top_left = pyautogui.position()
                print("Captured top-left; Awaiting CTRL press...")
                # Capture screen bottom_right
                keyboard.wait(translation_hotkey)
                bottom_right = pyautogui.position()
                windows.clear()
                frames.clear()
                time.sleep(0.2)
                screenshot_pos, capture_area = capture_screen(IMAGE_NAME, top_left, bottom_right)

                self.screenshot_ready.emit(
                    (screenshot_pos[0], screenshot_pos[1]),
                    (capture_area[0], capture_area[1])
                )

                image_url = IMAGE_NAME

                start_time = time.time()

                print("Captured image. Parsing...")

                # Convert image text to text via EasyOCR
                ocr_output = easy_reader.readtext(IMAGE_NAME, paragraph=True)

                # Pass on answer to translation model
                for text_item in ocr_output:

                    source_text = text_item[1]

                    print(f"Hy-MT2-1.8B-Q8_0.gguf /// Translating text chunk to {native_language}...")
                    translation_prompt = f"Translate without explanation to {native_language}: {source_text}"
                    full_response = translation_model(translation_prompt, max_tokens=MAX_TOKENS)
                    response = full_response["choices"][0]["text"].strip()
                    print(response)
                    
                    top_left = text_item[0][0]
                    bottom_right = text_item[0][2]

                    position = (screenshot_pos[0] + top_left[0], screenshot_pos[1] + top_left[1])
                    textbox_width = bottom_right[0] - top_left[0]
                    textbox_height = bottom_right[1] - top_left[1]
                    character_count = len(response)
                    font_size = int(((textbox_width * textbox_height) / (character_count * 0.9)) ** 0.5)

                    # Print final output to screen
                    self.translation_ready.emit(
                        response, 
                        position,
                        (textbox_width, textbox_height),
                        font_size
                    )

                self.translation_finished.emit()

                print(f"Finished in {time.time() - start_time} seconds.")

            except Exception as e:
                print(e)




# GUI Setup
# Windows API constants - Ensure window is clickthrough at OS level
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

# GUI Text Window Module
class TranslationWindow(QWidget):
    def __init__(self, text, dimensions, font_size):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)
    
        label = QLabel(text, self)
        label.setWordWrap(True)
        label.setFixedWidth(dimensions[0] + 8)
        label.setFixedHeight(dimensions[1] + 8)
        label.move(0, 0)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)
        # White text on black translucent background
        label.setStyleSheet(f"""
            color: white;
            font-size: {font_size+1}px;
            background: rgba(0, 0, 0, 160);
            padding: 4px;
            border-radius: 6px;
        """)

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )

# GUI Screenshot Outline Module
class ScreenshotFrame(QWidget):
    def __init__(self, capture_area):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)

        self.resize(capture_area[0], capture_area[1])

        # Loading indicator via pulsing effect, updates every 50ms
        self._pulse_factor = 0.9
        self._pulsing = True
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )

    # Pulsing effect logic
    @pyqtProperty(float)
    def pulse_factor(self):
        return self._pulse_factor
    @pulse_factor.setter
    def pulse_factor(self, value):
        self._pulse_factor = max(0.3, min(1.0, value))
        self.update()
    def update_pulse(self):
        if self._pulsing:
            # Cycle from 0.3 to 1.0 and back using sine wave
            self._pulse_factor = 0.6 + 0.4 * math.sin(time.time() * 4)
            self.update()
    
    # Draw rect and apply pulsing effect to rect pen
    def paintEvent(self, event):
        painter = QPainter(self)

        base_color = QColor(70, 140, 255)
        base_color.setAlphaF(self._pulse_factor) # Apply pulsing effect
        
        pen = QPen(base_color, 3)
        painter.setPen(pen)
        painter.drawRect(3, 3, self.width() - 6, self.height() - 6)
        painter.end()

    # Fade out frame
    def start_fade_out(self):
        # Stop pulsing
        self._pulsing = False
        self.pulse_timer.stop()
        self._pulse_factor = 1.0
        self.update()

        # Create animation for the "windowOpacity" property
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(2500)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
        # Connect finished signal to close or cleanup if needed
        self.animation.finished.connect(self.cleanup)
    
        self.animation.start()

    def cleanup(self):
        self.close()



# Main App

app = QApplication(sys.argv)

# Called from TranslationWorker thread via screenhot_ready signal
# Shows captured screen area
def show_frame(coords, capture_area):
    frame = ScreenshotFrame(capture_area)
    frame.move(coords[0], coords[1])
    frame.show()
    frames.append(frame)

# Called from TranslationWorker thread via translation_ready signal
# Shows translated text in a new window near the captured screenshot
def show_translation(text, coords, dimensions, font_size):
    window = TranslationWindow(text, dimensions, font_size)
    try:
        window.move(coords[0], coords[1])
    except Exception as e:
        print(e)
    window.show()
    windows.append(window)

def translation_done():
    if len(frames) > 0:
        frames[0].start_fade_out()

# Initialize worker & thread
worker = TranslationWorker()
thread = QThread()
worker.moveToThread(thread)

# Connect signal to GUI slot
worker.screenshot_ready.connect(show_frame)
worker.translation_ready.connect(show_translation)
worker.translation_finished.connect(translation_done)
thread.started.connect(worker.run)

# Start the background loop
thread.start()

# Start Qt Event Loop (this runs until app.quit())
sys.exit(app.exec())