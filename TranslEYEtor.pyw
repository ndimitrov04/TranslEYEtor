import os, sys
os.execv(sys.executable, [sys.executable, "-m", "main"] + sys.argv[1:])