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

print("Starting TranslEYEtor V0.2.2 Alpha...")

def abort_program():
    input("FAILURE: Press Enter to exit...")
    exit()

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# Install required packages
try:
    # AI Dependencies
    install("torch[cpu]")
    install("torchvision")
    install("torchcodec")
    install("transformers[torch]")
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
import torch
from transformers import (
    AutoModelForImageTextToText,
    AutoProcessor,
    TextStreamer,
    AutoModelForCausalLM,
    AutoTokenizer
)
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

# Load MiniCPM V4.6 - Image-text to text model
model_id = "openbmb/MiniCPM-V-4.6"
try:
    # Attempt to load model from cache
    print(f"Trying to load {model_id} from offline cache...")

    processor = AutoProcessor.from_pretrained(
        model_id,
        cache_dir=MODEL_CACHE_DIR,
        local_files_only=True
    )

    ocr_model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        cache_dir=MODEL_CACHE_DIR,
        local_files_only=True,
        torch_dtype=torch.float32,
        device_map="cpu"
    )
    print(f"Loaded {model_id} from local cache.")
except Exception:
    # If model is not available locally, attempt to download
    print(f"Model [{model_id}] is not available offline.")
    print("Attempting to download from huggingface...")
    try:
        processor = AutoProcessor.from_pretrained(
            model_id,
            cache_dir=MODEL_CACHE_DIR
        )
        ocr_model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        print("Download complete.")
    except Exception as e:
        # Abort program if model is not available online or offline
        print("Transformer Image-text-to-text model not present and cannot be fetched from the web! (Check your internet connection.)")
        abort_program()

# Load Hy-MT2 - Text translation model
model_id = "tencent/Hy-MT2-1.8B"
try:
    # Attempt to load model from cache
    print(f"Trying to load {model_id} from offline cache...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, 
        trust_remote_code=True,
        cache_dir=MODEL_CACHE_DIR,
        local_files_only=True
    )
    trans_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        cache_dir=MODEL_CACHE_DIR,
        local_files_only=True,
    )
    trans_model.to("cpu")
    trans_model.eval()
    print(f"Loaded {model_id} from local cache.")
except Exception:
    # If model is not available locally, attempt to download
    print(f"Model [{model_id}] is not available offline.")
    print("Attempting to download from huggingface...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, 
            trust_remote_code=True,
            cache_dir=MODEL_CACHE_DIR
        )
        trans_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            cache_dir=MODEL_CACHE_DIR
        )
        #trans_model.to("cpu")
        trans_model.eval()
        print("Download complete.")
    except Exception as e:
        # Abort program if model is not available online or offline
        print("Transformer text translation model not present and cannot be fetched from the web! (Check your internet connection.)")
        abort_program()


# Options
# User options
native_language = "English"
translation_hotkey = "ctrl"
capture_area = 240 # Capture 480p image
# System options
IMAGE_NAME = ".screenshot.png"
MAX_TOKENS = 64                 # Small token size for testing
TERMINATOR = f"</think>\n\n"    # Mini CPM output terminator;
                                # Anything before this is either AI thought or user input data

# Capture screen around current mouse position
def capture_screen(image_name):
    global screenshot_pos
    screenshot_pos = pyautogui.position()
    pyautogui.screenshot(
        image_name,
        region=(
            screenshot_pos[0] - capture_area,
            screenshot_pos[1] - capture_area, 
            capture_area * 2,
            capture_area * 2
            )
    )

print(f"How to use:\nPress {translation_hotkey} to translate a {capture_area} pixel area around your mouse cursor...")

# AI Translation Module
class TranslationWorker(QObject):

    screenshot_ready = pyqtSignal(tuple)
    translation_ready = pyqtSignal(str, tuple)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:

            print(f"Awaiting {translation_hotkey} press...")

            try:
                # Capture screen
                keyboard.wait(translation_hotkey)
                capture_screen(IMAGE_NAME)

                self.screenshot_ready.emit((screenshot_pos[0] - capture_area, 
                                            screenshot_pos[1] - capture_area))

                image_url = IMAGE_NAME

                start_time = time.time()

                print("Captured image. Parsing...")

                # Convert image text to text via MiniCPM
                image = Image.open(image_url).convert("RGB")
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": image
                            },
                            {
                                "type": "text",
                                "text": f"Output ONLY the text in the image. Do not output anything else. No explanations.",
                            },
                        ],
                    }
                ]

                print(f"{ocr_model.name_or_path}///Preparing inputs...")
                inputs = processor.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_dict=True,
                    return_tensors="pt",
                    downsample_mode="16x",
                    max_slice_nums=3
                )

                # Output text word by word (debug)
                print(f"{ocr_model.name_or_path}///Converting image-text to plaintext...\n")
                streamer = TextStreamer(
                    processor.tokenizer,
                    skip_prompt=True,
                    skip_special_tokens=True,
                )
                with torch.inference_mode():
                    output = ocr_model.generate(
                        **inputs,
                        streamer=streamer,
                        max_new_tokens=MAX_TOKENS,
                        do_sample=False
                    )
                print(f"{ocr_model.name_or_path}///Text conversion complete.")

                decoded_output = processor.tokenizer.decode(output[0], skip_special_tokens=True)
                terminator_pos = decoded_output.find(TERMINATOR)
                source_text = decoded_output[terminator_pos + len(TERMINATOR) : ]

                # Pass on answer to translation model
                print(f"{trans_model.name_or_path}///Preparing inputs...")
                translation_prompt = f"Translate: {source_text} to {native_language}."
                messages = [{"role": "user", "content": translation_prompt}]
                inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(trans_model.device)

                print(f"{trans_model.name_or_path}///Translating image-text to {native_language}...")
                with torch.no_grad():
                    outputs = trans_model.generate(
                        **inputs,
                        max_new_tokens=MAX_TOKENS
                    )
                print(f"{trans_model.name_or_path}///Translation complete.")

                response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)

                print(response)

                # Print final output to screen
                self.translation_ready.emit(response, 
                                            (screenshot_pos[0] - capture_area, 
                                             screenshot_pos[1] - capture_area)
                                            )

                print(f"Finished in {time.time() - start_time} seconds.")

                # All of this takes around 38 seconds for like 16 tokens on a Ryzen 5 5600X. 
                # Not good...

            except Exception as e:
                print(e)




# GUI Setup
# Windows API constants - Ensure window is clickthrough at OS level
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

# GUI Text Window Module
class TranslationWindow(QWidget):
    def __init__(self, text):
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
        label.setFixedWidth((capture_area * 2) - 20)
        label.move(0, 0)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)
        # White text on black translucent background
        label.setStyleSheet("""
            color: white;
            background: rgba(0, 0, 0, 160);
            padding: 4px;
            border-radius: 6px;
        """)
        label.adjustSize()
    
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

        self.resize(capture_area*2, capture_area*2)

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
frames = []
windows = []

# Called from TranslationWorker thread via screenhot_ready signal
# Shows captured screen area
def show_frame(coords):
    frames.clear()                     # Destroy previous windows
    frame = ScreenshotFrame()
    frame.move(coords[0], coords[1])
    frame.show()
    frames.append(frame)

# Called from TranslationWorker thread via translation_ready signal
# Shows translated text in a new window near the captured screenshot
def show_translation(text, coords):
    windows.clear()
    frames[len(frames) - 1].start_fade_out()
    window = TranslationWindow(text)
    window.move(coords[0], coords[1])
    window.show()
    windows.append(window)

# Initialize worker & thread
worker = TranslationWorker()
thread = QThread()
worker.moveToThread(thread)

# Connect signal to GUI slot
worker.screenshot_ready.connect(show_frame)
worker.translation_ready.connect(show_translation)
thread.started.connect(worker.run)

# Start the background loop
thread.start()

# Start Qt Event Loop (this runs until app.quit())
sys.exit(app.exec())