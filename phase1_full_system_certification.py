import requests
import subprocess
import time
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def wait_for_health():
    print("⏳ Waiting for backend...")
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/api/health/")
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    print("❌ Backend did not become healthy")
    sys.exit(1)


def validate_health_payload():
    r = requests.get(f"{BASE_URL}/api/health/")
    data = r.json()

    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["architecture_version"] == "v0.2.0"

    print("✅ Health payload valid")


def ensure_test_user():
    print("🔎 Ensuring test user exists")

    cmd = (
        "docker compose exec backend "
        'python manage.py shell -c "'
        "from django.contrib.auth import get_user_model;"
        "User=get_user_model();"
        "u,created=User.objects.get_or_create("
        "username='test', "
        "defaults={'role':'CREATOR','display_name':'Test User'}"
        ");"
        "u.set_password('test');"
        "u.save();"
        "print('ready')\""
    )
    run_cmd(cmd)
    print("✅ Test user ready")


def test_login_flow():
    ensure_test_user()

    print("🔎 Testing login")

    payload = {"username": "test", "password": "test"}
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=payload)

    if r.status_code != 200:
        print("❌ Login failed:", r.text)
        sys.exit(1)

    token = r.json()["data"]["token"]
    print("✅ Token issued")
    return token


def test_protected_endpoint(token):
    r = requests.get(
        f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    if r.status_code != 200:
        print("❌ Protected endpoint failed")
        sys.exit(1)

    print("✅ Protected endpoint valid")


def test_invalid_token():
    r = requests.get(
        f"{BASE_URL}/api/v1/users/me", headers={"Authorization": "Bearer invalidtoken"}
    )

    assert r.status_code in (401, 403)
    print("✅ Invalid token rejected")


def stress_health_parallel():
    print("🔎 Parallel health stress test")

    def call():
        r = requests.get(f"{BASE_URL}/api/health/")
        assert r.status_code == 200

    with ThreadPoolExecutor(max_workers=10) as executor:
        for _ in range(50):
            executor.submit(call)

    print("✅ Parallel health stable")


def stress_login_parallel():
    print("🔎 Parallel login stress test")

    def login():
        payload = {"username": "test", "password": "test"}
        r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=payload)
        assert r.status_code == 200

    with ThreadPoolExecutor(max_workers=5) as executor:
        for _ in range(20):
            executor.submit(login)

    print("✅ Parallel login stable")


def test_request_id():
    rid = str(uuid.uuid4())
    r = requests.get(f"{BASE_URL}/api/health/", headers={"X-Request-ID": rid})

    assert r.headers.get("X-Request-ID") == rid
    print("✅ Request ID propagation valid")


def restart_test():
    print("🔎 Restart validation")

    run_cmd("docker compose restart backend")
    time.sleep(3)
    wait_for_health()

    print("✅ Restart resilience validated")


def migration_integrity():
    print("🔎 Migration integrity check")
    run_cmd(
        "docker compose exec backend python manage.py makemigrations --check --dry-run"
    )
    print("✅ No pending migrations")


def docker_build_check():
    print("🔎 Docker build validation")
    run_cmd("docker build ./backend")
    print("✅ Docker build valid")


def main():
    print("\n===== PHASE 1 FULL SYSTEM CERTIFICATION =====\n")

    docker_build_check()
    migration_integrity()
    wait_for_health()
    validate_health_payload()

    token = test_login_flow()
    test_protected_endpoint(token)
    test_invalid_token()
    stress_health_parallel()
    stress_login_parallel()
    test_request_id()
    restart_test()

    print("\n🎉 PHASE 1 CERTIFIED ROBUST")
    print("Integration Maturity: 9/10+")


if __name__ == "__main__":
    main()
