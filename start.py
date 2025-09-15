import os
import webbrowser
import time

# OPTIONAL: Set port here
PORT = 8000

# 📂 Dynamically get the folder where start.py is
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

print("🚀 Starting Django server from", PROJECT_DIR)

# ✅ Change to that folder
os.chdir(PROJECT_DIR)

# 🖥️ Open browser after server starts
def open_browser():
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{PORT}")

# 🚀 Start server
os.system(f"start cmd /k python manage.py runserver {PORT}")
open_browser()
