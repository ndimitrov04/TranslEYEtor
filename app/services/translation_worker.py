# Necessary Dependencies
# --------------------------------------------------------------------------------
# Custom
import app.globals as globals
from app.startup.init import *
from app.services.translation_server import translation_server
# AI
import easyocr
from llama_cpp import Llama
from PIL import Image
# Utilities
import pyautogui
import keyboard
# PyQt6 dependencies
from PyQt6.QtCore import (Qt, QObject, QThread, QSize, QTimer, 
                          QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox,
                             QLabel, QPushButton, QSystemTrayIcon, QMenu, QTextEdit)
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QAction

# AI Translation Module
# ================================================================================

class TranslationWorker(QObject):

    screenshot_ready = pyqtSignal(tuple, tuple)
    translation_ready = pyqtSignal(str, tuple, tuple, int)
    translation_finished = pyqtSignal()

    screenshot_pos = [-250, -250]

    def __init__(self):
        super().__init__()
        self.running = True
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

    def listener_thread(self, output_queue):

        while globals.translation_server_running:

            try:
                if not output_queue.empty():
                    result = output_queue.get(timeout=0.5)
                else:
                    continue
            except Exception:
                continue

            print(f"Main received from worker: {result}")
            response, bbox_top_left, bbox_bottom_right = result

            if response == "@EMPTY":
                globals.working = False
                self.translation_finished.emit()
            elif response == "@READY":
                globals.translation_server_ready = True
                print(f"Awaiting {globals.translation_hotkey}+shift press...")

            position = (self.screenshot_pos[0] + bbox_top_left[0], self.screenshot_pos[1] + bbox_top_left[1])
            textbox_width = bbox_bottom_right[0] - bbox_top_left[0]
            textbox_height = bbox_bottom_right[1] - bbox_top_left[1]
            character_count = len(response)
            font_size = int(((textbox_width * textbox_height) / (character_count * 0.9)) ** 0.5)

            # Print final output to screen
            self.translation_ready.emit(
                response, 
                position,
                (textbox_width, textbox_height),
                font_size
            )

            if output_queue.empty():
                globals.working = False
                self.translation_finished.emit()

    # Start translation model process, and then start listener thread
    def run(self):

        while self.running:

            globals.translation_server_running = True

            # Recreate queue (may be corrupted after kill())
            self.input_queue = multiprocessing.Queue()
            self.output_queue = multiprocessing.Queue()
            self.stop_event = multiprocessing.Event()

            # Restart listener (may be corrupted after kill())
            print("Starting server listener thread...")

            listener = threading.Thread(target=self.listener_thread, args=(self.output_queue,))
            listener.start()

            # Restart server
            print("Starting translation server...")

            server = multiprocessing.Process(
                target=translation_server,
                args=(
                    self.input_queue, 
                    self.output_queue, 
                    self.stop_event, 
                    globals.translation_model_path, 
                    globals.gpu_available, 
                    globals.lang_code, 
                    globals.native_language, 
                    globals.MAX_TOKENS
                )
            )
            server.daemon = True
            server.start()


            while globals.translation_server_running:
                try:
                    # Take input screenshot coordinates
                    # Poll for hotkey input
                    while globals.translation_server_running and not (keyboard.is_pressed(globals.translation_hotkey) and keyboard.is_pressed("shift")):
                        time.sleep(0.01)
                    if not globals.translation_server_running:
                        break
                    # When hotkey is pressed, capture top_left
                    top_left = pyautogui.position()
                    globals.top_left_sel = top_left
                    print(f"Keep pressing {globals.translation_hotkey} and drag your mouse over an area to select it...")
                    # Poll until hotkey is fully released
                    while keyboard.is_pressed(globals.translation_hotkey):
                        time.sleep(0.01)
                    # After key is released, capture bottom_right
                    bottom_right = pyautogui.position()
                    globals.bottom_right_sel = bottom_right

                    # Clear previous capture data
                    globals.top_left_sel = [0, 0]
                    globals.bottom_right_sel = [0, 0]
                    globals.windows.clear()
                    globals.frames.clear()
                    time.sleep(0.2)
                    self.screenshot_pos, capture_area = globals.capture_screen(globals.IMAGE_NAME, top_left, bottom_right)

                    self.screenshot_ready.emit(
                        (self.screenshot_pos[0], self.screenshot_pos[1]),
                        (capture_area[0], capture_area[1])
                    )

                    image_url = globals.IMAGE_NAME

                    # Add work to server queue
                    self.input_queue.put(image_url)
                    # Raise working flag
                    globals.working = True

                except Exception as e:
                    print(f"ERROR: {e}")
            
            if not globals.translation_server_running:
                print("Closing listener...")
                print("Closing translation server...")
                globals.translation_server_ready = False
                server.kill()

# ================================================================================