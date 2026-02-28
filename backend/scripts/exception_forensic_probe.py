import os
import django
import inspect

print("\n=== INITIALIZING DJANGO ===\n")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings  # noqa: E402
from rest_framework.settings import api_settings  # noqa: E402
from rest_framework.exceptions import ValidationError  # noqa: E402
from rest_framework.views import exception_handler as drf_default_handler  # noqa: E402
from rest_framework.response import Response  # noqa: E402

print("\n=== SETTINGS MODULE ===")
print("DJANGO_SETTINGS_MODULE:", os.environ.get("DJANGO_SETTINGS_MODULE"))
print("Loaded settings file:", settings.__file__)
print()

print("=== REST_FRAMEWORK CONFIG ===")
print(getattr(settings, "REST_FRAMEWORK", "NOT DEFINED"))
print()

print("=== DRF ACTIVE EXCEPTION HANDLER ===")
print(api_settings.EXCEPTION_HANDLER)
print("Handler source file:")
print(inspect.getsourcefile(api_settings.EXCEPTION_HANDLER))
print()

print("=== DOES CUSTOM HANDLER EXIST? ===")
try:
    from core.exceptions import domain_exception_handler

    print("domain_exception_handler FOUND at:")
    print(inspect.getsourcefile(domain_exception_handler))
except Exception as e:
    print("domain_exception_handler NOT found:", e)
print()

print("=== SIMULATING DRF ValidationError ===")
exc = ValidationError("Cannot create ADMIN users via API")

handler = api_settings.EXCEPTION_HANDLER
response = handler(exc, context={"request": None})

if isinstance(response, Response):
    print("Custom handler returned Response")
    print("Status Code:", response.status_code)
    print("Response Data:", response.data)
else:
    print("Handler did NOT return Response")
    print("Returned:", response)

print()

print("=== DRF DEFAULT HANDLER OUTPUT ===")
default_response = drf_default_handler(exc, context={"request": None})

if isinstance(default_response, Response):
    print("Default Status Code:", default_response.status_code)
    print("Default Data:", default_response.data)
else:
    print("Default handler returned:", default_response)

print()

print("=== CHECKING IF HANDLER IS OVERRIDDEN IN api_settings ===")
print(
    "api_settings.EXCEPTION_HANDLER == drf_default_handler ?",
    api_settings.EXCEPTION_HANDLER == drf_default_handler,
)

print("\n=== END FORENSIC REPORT ===\n")
