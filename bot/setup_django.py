import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
django.setup()