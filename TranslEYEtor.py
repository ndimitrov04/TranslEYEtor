#  _______                  _ ________     ________ _             
# |__   __|                | |  ____\ \   / /  ____| |            
#    | |_ __ __ _ _ __  ___| | |__   \ \_/ /| |__  | |_ ___  _ __ 
#    | | '__/ _` | '_ \/ __| |  __|   \   / |  __| | __/ _ \| '__|
#    | | | | (_| | | | \__ \ | |____   | |  | |____| || (_) | |   
#    |_|_|  \__,_|_| |_|___/_|______|  |_|  |______|\__\___/|_|   
                                                                                                                      

# This is an experimental screen translation app.
# This program uses two local AI models (OCR + TranslationLLM)
# in order to translate screen text in-place.

# How to use:
#    1. Mouse over any on screen text
#    2. Press CTRL
#    3. Wait
#    4. A translation will appear over your chosen text

# This program requires:
#    - Windows 10/11
#    - Python 3.10
#    - CMAKE
#    - PIP

# This program will automatically download:
#   - Vulkan SDK (if AMD GPU is detected)
#   - Llama.cpp
#   - The Hy-MT2 text translation model from huggingface
#   - A TON of python packages

import subprocess
import sys
import math
import time
import os
import ctypes

print("Starting TranslEYEtor V0.3.2 Alpha...")

def abort_program():
    input("FAILURE: Press Enter to exit...")
    exit()

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def install_cpu():
    print("Installing llama-cpp for CPU infernece...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--extra-index-url",
        "https://abetlen.github.io/llama-cpp-python/whl/cpu"
    ])


# Download and install required dependencies
# ================================================================================

# Llama subsystem (Compatible with CPU; AMD GPU; NVidia GPU)
# --------------------------------------------------------------------------------
# Detect GPU avalability and type; Install Llama.cpp for NVidia/AMD gpu (CUDA or Vulkan)
# WARNING: Vulkan wheel requires VulkanSDK to be built: https://vulkan.lunarg.com/sdk/home
# CUDA wheel is premade. Building Vulkan wheel may take a LONG time.
install("torch-directml")
import torch_directml
print(torch_directml.device_name(0))
print(torch_directml.device_name(1))
no_gpu = True
try:
    # WARNING: Importing WMI might fail on first run. If no GPU is found, close and reopen the program.
    print("WARNING: Importing WMI might fail on first run. If no GPU is found, close and reopen the program.")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "wmi", 
        "pywin32"
    ])
    import wmi
    c = wmi.WMI()
    for gpu in c.Win32_VideoController():
        name = gpu.Name
        name = name.lower()
        if "nvidia" in name:
            # NVidia always has it easy, wheel is premade and ready to use...
            print("NVIDIA GPU:", gpu.name)
            print("Installing llama-cpp /w CUDA...")
            print("Fetching CUDA wheel...")

            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "llama-cpp-python",
                "--extra-index-url",
                "https://abetlen.github.io/llama-cpp-python/whl/cu124"
            ])
            no_gpu = False

            break

        elif "amd" in name or "radeon" in name:
            # This requires the vulkan SDK, wheel needs to be built from scartch. NOT GOOD.
            # This process may take a long time.
            # https://vulkan.lunarg.com/sdk/home
            print("AMD GPU:", gpu.name)

            # Get VulkanSDK
            PACKAGE_ID = "KhronosGroup.VulkanSDK"
            print("Installing llama-cpp /w VULKAN...")
            print("Checking if VulkanSDK is present...")
            result = subprocess.run(
                ["winget", "list", "--id", PACKAGE_ID, "-e"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0 or PACKAGE_ID not in result.stdout:
                print("Fetching VulkanSDK (required to build Vulkan wheel)...")
                subprocess.check_call([
                    "winget", "install", "-e", "--id", PACKAGE_ID
                ])
            print("VulkanSDK present...")

            # Build Vulkan Wheel for AMD GPU
            print("NOTICE: Building the Vulkan wheel may take a LONG time.")
            env = os.environ.copy()
            env["CMAKE_ARGS"] = "-DGGML_VULKAN=ON"
            env["FORCE_CMAKE"] = "1"
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--no-cache-dir",
                "llama-cpp-python"
            ], env=env)
            no_gpu = False

            break

        else:
            print("Unsupported GPU:", gpu.name)

except Exception as gpu_fail:

    print("ERROR: " + str(gpu_fail))
    print("Error while installing llama with GPU support, falling back to CPU...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--extra-index-url",
        "https://abetlen.github.io/llama-cpp-python/whl/cpu",
        "--force-reinstall"
    ])


if no_gpu:
    print("No compatible GPUs found.")
    install_cpu()

# --------------------------------------------------------------------------------


# Package installation
# --------------------------------------------------------------------------------

# Install required packages
try:
    # AI Dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "easyocr", "numpy<2"])
    # Utilities
    install("huggingface_hub")  # AI model downloading
    install("pyautogui")        # Mouse macros, screenshots
    install("keyboard")         # Keyboard macros and detection
    install("PyQt6")            # GUI library
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

# --------------------------------------------------------------------------------


# Set up local filesystem
# --------------------------------------------------------------------------------

# Set current working directory to python script location
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define a permanent cache directory
MODEL_CACHE_DIR = ".model_cache"
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# Download Hy-MT2 - Text translation model
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="tencent/Hy-MT2-1.8B-GGUF",
    filename="Hy-MT2-1.8B-Q4_K_M.gguf",
    cache_dir=".model_cache"
)
# Load Hy-MT2
try:
    translation_model = Llama(model_path=model_path, verbose=False, n_gpu_layers=-1)
except Exception as e:
    # Abort program if model is not available online or offline
    print("Transformer text translation model not present and cannot be fetched from the web! (Check your internet connection.)")
    print("ERROR: " + str(e))
    abort_program()
# --------------------------------------------------------------------------------
# ================================================================================


# Global Functions
# ================================================================================

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

# ================================================================================


# Global Vars
# ================================================================================

# Options
# --------------------------------------------------------------------------------
# User options
native_language = "English"
translation_hotkey = "ctrl"
# System options (const)
IMAGE_NAME = ".screenshot.png"
MAX_TOKENS = 256                # Small token size for testing
# --------------------------------------------------------------------------------

# Selection coordinates - used only for GUI. 
# Global so they can be recalled by all classes.
top_left_sel = [0, 0]
bottom_right_sel = [0, 0]

# Frames and windows of program. Must be global to be accessed by all classes.
frames = []
windows = []

# ================================================================================


# AI Translation Module
# ================================================================================

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

        print("\n\nTranslEYEtor ONLINE.\n")

        print("Click and drag a bounding box over the area you want translated...")

        while self.running:

            print(f"Awaiting {translation_hotkey} press...")

            try:
                # Capture screen top_left on press
                keyboard.wait(translation_hotkey, False, False)
                top_left = pyautogui.position()
                global top_left_sel
                top_left_sel = top_left
                print("Captured top-left; Awaiting CTRL press...")
                # Poll until hotkey is fully released
                while keyboard.is_pressed(translation_hotkey):
                    time.sleep(0.01)  # Prevent 100% CPU usage
                # After key is released, capture bottom_right
                bottom_right = pyautogui.position()
                global bottom_right_sel
                bottom_right_sel = bottom_right

                # Clear previous capture data
                top_left_sel = [0, 0]
                bottom_right_sel = [0, 0]
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

                print("EasyOCR /// Captured image. Parsing...")

                # Convert image text to text via EasyOCR
                ocr_output = easy_reader.readtext(IMAGE_NAME, paragraph=True)

                print(f"EasyOCR /// Image parsed in {time.time() - start_time} seconds.")

                # Pass on answer to translation model
                for text_item in ocr_output:

                    source_text = text_item[1]

                    print(f"Hy-MT2-1.8B-Q4_K_M /// Translating text chunk to {native_language}...")
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

# ================================================================================


# GUI Setup
# ================================================================================
# Windows API constants - Ensure window is clickthrough at OS level
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
# ================================================================================


# GUI Classes
# ================================================================================

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

# GUI Screen-selection Overlay Window
class SelectionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)

        screen = app.primaryScreen()

        self.resize(screen.size().width(), screen.size().height())

    # Draw screen selection rect
    def paintEvent(self, event):
        painter = QPainter(self)

        base_color = QColor(255, 0, 0)
        
        pen = QPen(base_color, 3)
        painter.setPen(pen)

        global top_left_sel
        global bottom_right_sel
        if top_left_sel != [0, 0]:
            bottom_right_sel = pyautogui.position()

        painter.drawRect(top_left_sel[0], top_left_sel[1], bottom_right_sel[0] - top_left_sel[0], bottom_right_sel[1] - top_left_sel[1])
        QTimer.singleShot(16, self.update) # ~62FPS (1000ms/16ms = ~62f/s)
        painter.end()

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_TRANSPARENT
        )

# ================================================================================



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
# --------------------------------------------------------------------------------


# App initialization
# --------------------------------------------------------------------------------
# Start app
app = QApplication(sys.argv)

# Initialize selection window (For dragging GUI)
selection_window = []
selection_window.append(SelectionWindow())
selection_window[0].show()
selection_window[0].move(0,0)

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