# Necessary Dependencies
# --------------------------------------------------------------------------------
# AI
import easyocr
# Utilities
import pyautogui

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
translation_model_path = None
gpu_available = False
# System options
IMAGE_NAME = ".screenshot.png"
MAX_TOKENS = 256    # Small token size for testing
lang_code = 0       # 0 - Latin; 1 - Cyrillic; 2 - Arabic; 3 - CH; 4 - JP; 5 - KO
translation_server_running = False # Setting this to false will stop and restart the server
translation_server_ready = False # This will be set to true when the server has given a ready response
working = False
# --------------------------------------------------------------------------------

# Selection coordinates - used only for GUI. 
# Global so they can be recalled by all classes.
top_left_sel = [0, 0]
bottom_right_sel = [0, 0]

# Frames and windows of program. Must be global to be accessed by all classes.
frames = []
windows = []

# ================================================================================