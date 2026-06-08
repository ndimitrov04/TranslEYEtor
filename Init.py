import subprocess
import sys
import math
import time
import os
import ctypes

os.chdir(os.path.dirname(__file__))

def abort_program():
    print("NOTICE: A dependency issue has been encountered, restarting the program from Main.py might fix the issue.")
    x = input("FAILURE: Press Enter to exit...")
    x = " "
    print(x)
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

version = "0.4.0"

# Download/upgrade certificates required for installation
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "--upgrade", 
    "certifi"
])
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()