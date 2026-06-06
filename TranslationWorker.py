import Globals
from Install import *

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

        print("\n\nTranslEYEtor ONLINE.\n")

        print("Click and drag a bounding box over the area you want translated...")

        while self.running:

            print(f"Awaiting {Globals.translation_hotkey}+shift press...")

            try:
                # Capture screen top_left on press
                keyboard.wait((Globals.translation_hotkey + "+shift"), False, False)
                top_left = pyautogui.position()
                Globals.top_left_sel = top_left
                print(f"Keep pressing {Globals.translation_hotkey} and drag your mouse over an area to select it...")
                # Poll until hotkey is fully released
                while keyboard.is_pressed(Globals.translation_hotkey):
                    time.sleep(0.01)  # Prevent 100% CPU usage
                # After key is released, capture bottom_right
                bottom_right = pyautogui.position()
                Globals.bottom_right_sel = bottom_right

                # Clear previous capture data
                Globals.top_left_sel = [0, 0]
                Globals.bottom_right_sel = [0, 0]
                Globals.windows.clear()
                Globals.frames.clear()
                time.sleep(0.2)
                screenshot_pos, capture_area = Globals.capture_screen(Globals.IMAGE_NAME, top_left, bottom_right)

                self.screenshot_ready.emit(
                    (screenshot_pos[0], screenshot_pos[1]),
                    (capture_area[0], capture_area[1])
                )

                image_url = Globals.IMAGE_NAME

                start_time = time.time()

                print("EasyOCR /// Captured image. Parsing...")

                # Convert image text to text via EasyOCR
                ocr_output = Globals.easy_reader.readtext(Globals.IMAGE_NAME, paragraph=True)

                print(f"EasyOCR /// Image parsed in {time.time() - start_time} seconds.")

                # Pass on answer to translation model
                for text_item in ocr_output:

                    source_text = text_item[1]

                    print(f"Hy-MT2-1.8B-Q4_K_M /// Translating text chunk to {Globals.native_language}...")
                    translation_prompt = f"Translate without explanation to {Globals.native_language}: {source_text}"
                    full_response = translation_model(translation_prompt, max_tokens=Globals.MAX_TOKENS)
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