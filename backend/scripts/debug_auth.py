import os
import sys

# CRITICAL FIX: Add /app to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# CRITICAL FIX: Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.test import APIRequestFactory

User = get_user_model()


def debug_token(token_str):
    print("\n========== JWT TOKEN DEBUG ==========\n")

    # Step 1 — Raw decode
    try:
        token = AccessToken(token_str)
        print("✅ Token decoded successfully")
        print("Payload:")
        for key, value in token.payload.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print("❌ Token decode failed:", str(e))
        return

    # Step 2 — Check user exists
    user_id = token.payload.get("user_id")

    try:
        user = User.objects.get(id=user_id)
        print("\n✅ User exists in database")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  Active: {user.is_active}")
    except User.DoesNotExist:
        print("\n❌ User NOT FOUND in database")
        return

    # Step 3 — Test JWTAuthentication class
    print("\nTesting JWTAuthentication.authenticate()")

    factory = APIRequestFactory()
    request = factory.get("/")
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token_str}"

    auth = JWTAuthentication()

    try:
        result = auth.authenticate(request)

        if result is None:
            print("❌ Authentication returned None")
        else:
            user_obj, validated_token = result
            print("✅ Authentication SUCCESS")
            print(f"Authenticated user: {user_obj.username}")
            print(f"Role: {user_obj.role}")

    except Exception as e:
        print("❌ Authentication FAILED:", str(e))

    print("\n========== END DEBUG ==========\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("docker compose exec backend python scripts/debug_auth.py YOUR_TOKEN")
        sys.exit(1)

    token_input = sys.argv[1]
    debug_token(token_input)
