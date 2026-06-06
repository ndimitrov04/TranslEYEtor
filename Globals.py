from Install import *

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

# Initialize EasyOCR with lang lists
print("Preparing EasyOCR latin dictionary...")
easy_reader_latin = easyocr.Reader(['en', 'fr', 'de', 'es', 'it'])
print("Preparing EasyOCR cyrillic dictionary...")
easy_reader_cyrillic = easyocr.Reader(["ru", "rs_cyrillic", "be", "bg", "uk", "mn", "en"])
print("Preparing EasyOCR arabic dictionary...")
easy_reader_arabic = easyocr.Reader(['ar', 'fa', 'ur', 'en'])
print("Preparing EasyOCR chinese dictionary...")
easy_reader_chinese = easyocr.Reader(['ch_sim', 'en'])
print("Preparing EasyOCR japanese dictionary...")
easy_reader_japanese = easyocr.Reader(['ja', 'en'])
print("Preparing EasyOCR korean dictionary...")
easy_reader_korean = easyocr.Reader(['ko', 'en'])

# Options
# --------------------------------------------------------------------------------
# User options
native_language = "English"
translation_hotkey = "ctrl"
# System options
IMAGE_NAME = ".screenshot.png"
MAX_TOKENS = 256    # Small token size for testing
easy_reader = easy_reader_latin
# --------------------------------------------------------------------------------

# Selection coordinates - used only for GUI. 
# Global so they can be recalled by all classes.
top_left_sel = [0, 0]
bottom_right_sel = [0, 0]

# Frames and windows of program. Must be global to be accessed by all classes.
frames = []
windows = []

# ================================================================================