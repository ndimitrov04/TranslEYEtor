from app.startup.init import *
import json
from pathlib import Path

def app_initialization():
    # REGULAR RUN ->
    
    # Download/upgrade certificates required for installation
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "--upgrade", 
        "certifi"
    ])
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

    file_path = Path("config.json")
    if file_path.exists():
        print("Loading user config data...")
        with open("config.json", "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            return loaded_data['model_path'], loaded_data['gpu_availability']

    
    print("Initiating first time run procedure...")

    # FIRST TIME RUN -->>
    # Download and install required dependencies
    # ================================================================================

    # Llama subsystem (Compatible with CPU; AMD GPU; NVidia GPU)
    # --------------------------------------------------------------------------------
    # Detect GPU avalability and type; Install Llama.cpp for NVidia/AMD gpu (CUDA or Vulkan)
    # WARNING: Vulkan wheel requires VulkanSDK to be built: https://vulkan.lunarg.com/sdk/home
    # CUDA wheel is premade. Building Vulkan wheel may take a LONG time.
    install("torch-directml")
    import torch_directml
    install("cmake")
    import cmake
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
        time.sleep(1)
        import wmi
        for gpu in wmi.WMI().Win32_VideoController():
            name = gpu.name
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

                # If GPU is integrated, continue searching
                if not ("rx" in name or "pro" in name or "vii" in name or "r9" in name or "r7" in name):
                    print(gpu.name + " is an integrated GPU.")
                    continue    

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
                    "llama-cpp-python",
                    "--no-cache-dir"
                ], env=env)
                no_gpu = False

                break

            else:
                print("Unsupported GPU:", gpu.name)

    except Exception as gpu_fail:

        print("ERROR: " + str(gpu_fail))
        print("Error while installing llama with GPU support, falling back to CPU...")
        print("NOTICE: Building the CPU wheel may take a LONG time.")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--force-reinstall",
            "--no-cache-dir"
        ])


    if no_gpu:
        print("No compatible GPUs found.")
        install_cpu()

    # --------------------------------------------------------------------------------


    # Package installation
    # --------------------------------------------------------------------------------

    # Install required package
    # IMPORTANT: Due to the way PIP installs packages,
    # numpy<2 and numpy>2 will both be installed, resulting
    # in an error which PIP will be able to automatically fix
    # after a forced shell restart via retry_install().
    # This requires a better fix, but it works for now.
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
        retry_install()

    # Import installed dependencies
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

    # Download EasyOCR supported models
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
    
    gpu_availability = not no_gpu

    # Write first run var results to config.json file.
    # The contents of this file will be used to skip
    # dependecy checking and installation in future runs.
    config = {
        "gpu_availability": gpu_availability,
        "model_path": model_path
    }
    with open("config.json", "w", encoding="utf-8") as file:
        json.dump(config, file)

    return model_path, gpu_availability
    # --------------------------------------------------------------------------------
    # ================================================================================