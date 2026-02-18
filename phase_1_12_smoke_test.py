import subprocess
import sys
import time

import requests

BASE_URL = "http://localhost:8000"
USERNAME = "test"
PASSWORD = "test"


def run_command(command, description):
    print(f"\n🔎 {description}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print(f"❌ FAILED: {description}")
        sys.exit(1)
    print("✅ OK")


def wait_for_health():
    print("\n⏳ Waiting for backend health...")
    for _ in range(20):
        try:
            r = requests.get(f"{BASE_URL}/api/health/", timeout=2)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(1)
    print("❌ Backend did not become healthy.")
    sys.exit(1)


def validate_health(payload):
    print("\n🔎 Validating health payload")
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"
    assert payload["architecture_version"] == "v0.2.0"
    print("✅ Health valid")


def login():
    print("\n🔎 Testing login")
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=5,
    )
    if r.status_code != 200:
        print(r.text)
        print("❌ Login failed")
        sys.exit(1)

    data = r.json()["data"]
    token = data["token"]
    print("✅ Token issued")
    return token


def test_protected(token):
    print("\n🔎 Testing protected endpoint /users/me")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers, timeout=5)
    if r.status_code != 200:
        print(r.text)
        print("❌ Protected endpoint failed")
        sys.exit(1)
    print("✅ Protected endpoint valid")


def main():
    print("\n===== PHASE 1.12 FULL SMOKE TEST =====")

    # Governance checks
    run_command("python3 docs_check.py", "Running docs_check.py")
    run_command("python3 engineering_audit.py", "Running engineering_audit.py")

    # Migration integrity
    run_command(
        "docker compose exec backend python manage.py makemigrations --check --dry-run",
        "Migration integrity check",
    )

    # Runtime checks
    health_payload = wait_for_health()
    validate_health(health_payload)

    token = login()
    test_protected(token)

    print("\n🎉 PHASE 1.12 VALIDATED SUCCESSFULLY\n")


if __name__ == "__main__":
    main()
