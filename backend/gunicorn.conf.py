import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

# Disable Gunicorn's default handlers (stdout/stderr); logconfig_dict replaces them
errorlog = "-"
accesslog = "-"
loglevel = "info"
capture_output = True

# Gunicorn applies dictConfig; Django's LOGGING replaces its handlers
logconfig_dict = settings.LOGGING
