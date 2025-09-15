import os
import sys
from pathlib import Path

# adjust this if your Django project is in a different path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # project-root/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Make sure DJANGO_SETTINGS_MODULE is set to your settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laundry_pos.settings")

import django
django.setup()
