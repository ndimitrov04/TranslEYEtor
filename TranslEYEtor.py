import subprocess
import sys

print("Starting TranslEYEtor V0.1 Alpha...")

def abort_program():
    input("FAILURE: Press any key to exit...")
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
    install("pyautogui")
    install("keyboard")
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
    TextStreamer
)
from PIL import Image
# Utilities
import pyautogui
import keyboard


# Load MiniCPM V4.6
model_id = "openbmb/MiniCPM-V-4.6"
try:
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        device_map="cpu"
    )
except Exception:
    print("Transformer model not present and cannot be fetched from the web! (Check your internet connection.)")
    abort_program()

# Options
NATIVE_LANGUAGE = "English"
TRANSLATION_HOTKEY = "ctrl"
CAPTURE_AREA = 240 # Capture 480p image
IMAGE_NAME = "screenshot.png"

# Set current working directory to python script location
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


# Capture screen around current mouse position
def capture_screen(image_name):
    mousePos = pyautogui.position()
    pyautogui.screenshot(
        image_name,
        region=(
            mousePos[0] - CAPTURE_AREA,
            mousePos[1] - CAPTURE_AREA, 
            CAPTURE_AREA * 2,
            CAPTURE_AREA * 2
            )
    )

print(f"How to use:\nPress {TRANSLATION_HOTKEY} to translate a {CAPTURE_AREA} pixel area around your mouse cursor...")

# DEBUG - Test image inference code:
while (True):

    print(f"Awaiting {TRANSLATION_HOTKEY} press...")

    try:
        keyboard.wait(TRANSLATION_HOTKEY)
        capture_screen(IMAGE_NAME)

        image_url = IMAGE_NAME
        #print("///Input an image URL")
        #image_url = input("> ")

        print("Captured image. Parsing...")

        image = Image.open(image_url).convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image
                        #"url": image_url
                    },
                    {
                        "type": "text",
                        "text": f"Translate all of the text on the image to {NATIVE_LANGUAGE}. Output only the translated text. No comments or explanations. Any text outside the translation is forbidden.",
                    },
                ],
            }
        ]

        print("Preparing inputs...")
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            downsample_mode="16x",
            max_slice_nums=1
        )

        print("///Generating...\n")
        streamer = TextStreamer(
            processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                streamer=streamer,
                max_new_tokens=256,
                do_sample=False
            )
        print("/// END")

    except Exception as e:
        print(e)


input("Press enter to exit...")