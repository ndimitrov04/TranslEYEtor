import subprocess
import sys
import math
import time
import os
import ctypes

def abort_program():
    input("FAILURE: Press Enter to exit...")
    exit()

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def install_cpu():
    print("Installing llama-cpp for CPU infernece...")
    print("NOTICE: Building the CPU wheel may take a LONG time.")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--extra-index-url",
        "--no-cache-dir"
    ])

version = "0.3.4"