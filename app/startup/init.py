import multiprocessing
import threading
import subprocess
import sys
import math
import time
import os
import ctypes

os.chdir(os.path.dirname(__file__))

def abort_program():
    print("WARNING: A dependency issue has been encountered, restarting the program from Main.py might fix the issue.")
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
        "--no-cache-dir"
    ])

def retry_install():
    print("NOTICE: Minor dependency instalation error, automaticall restarting shell to fix issue...")
    print("(This will not impact installation in any way.)")
    os.execv(sys.executable, [sys.executable] + sys.argv)

version = "0.5.7"