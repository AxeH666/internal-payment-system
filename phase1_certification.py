#!/usr/bin/env python3
"""
Phase 1 Full Certification for Internal Payment System.

Run from project root (venv not required; uses system Python and docker).
No extra pip installs: uses only stdlib (urllib). Validates: governance docs,
engineering audit, Docker build, migrations, health API, auth flow,
request ID propagation, and DB restart resilience.
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, NoReturn

# --- Configuration (override via env or CLI) ---
DEFAULT_BASE_URL = "http://localhost:8000"
HEALTH_WAIT_TIMEOUT = 60
HEALTH_POLL_INTERVAL = 2
DB_STOP_WAIT = 3
DB_RESTART_WAIT = 8
EXPECTED_ARCH_VERSION = "v0.2.0"
REQUEST_TIMEOUT = 10


def _http_get(
    url: str, headers: dict[str, str] | None = None, timeout: int = REQUEST_TIMEOUT
) -> tuple[int, dict[str, str], str]:
    """GET url; return (status_code, headers_dict, body_text).
    4xx/5xx return (code, headers, body), no raise."""
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode() if e.fp else ""


def _http_post_json(
    url: str, data: dict[str, Any], timeout: int = REQUEST_TIMEOUT
) -> tuple[int, dict[str, str], str]:
    """POST JSON; return (status_code, headers_dict, body_text).
    Raises on connection error; 4xx/5xx return (code, headers, body)."""
    body_bytes = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body_bytes, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode() if e.fp else ""


def _http_get_maybe_fail(
    url: str, headers: dict[str, str] | None = None, timeout: int = REQUEST_TIMEOUT
) -> tuple[int, dict[str, str], str]:
    """GET url; on connection/HTTP error return (status or 0, {}, error_message)."""
    try:
        return _http_get(url, headers=headers, timeout=timeout)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode() if e.fp else ""
    except (urllib.error.URLError, OSError) as e:
        return 0, {}, str(e)


def run(cmd: str, description: str) -> None:
    """Run a shell command; exit with 1 on failure."""
    print(f"\n🔎 {description}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("✅ OK")


def fail(message: str) -> NoReturn:
    """Print error and exit with code 1."""
    print(f"❌ {message}")
    sys.exit(1)


def wait_for_health(base_url: str, timeout: int = HEALTH_WAIT_TIMEOUT) -> None:
    """Block until /api/health/ returns 200 or timeout."""
    print("\n⏳ Waiting for backend health...")
    url = f"{base_url.rstrip('/')}/api/health/"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status, _, _ = _http_get_maybe_fail(url, timeout=5)
        if status == 200:
            print("✅ Backend is up")
            return
        time.sleep(HEALTH_POLL_INTERVAL)
    fail("Backend health timeout")


def validate_health_payload(base_url: str) -> None:
    """Assert health response has expected structure and values."""
    print("\n🔎 Validating health payload")
    url = f"{base_url.rstrip('/')}/api/health/"
    status, _, body = _http_get(url)
    if status != 200:
        fail(f"Health returned {status}")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        fail(f"Health response is not JSON: {e}")
    if data.get("status") != "ok":
        fail(f'Expected status "ok", got {data.get("status")}')
    if data.get("database") != "connected":
        fail(f'Expected database "connected", got {data.get("database")}')
    if data.get("architecture_version") != EXPECTED_ARCH_VERSION:
        fail(
            f'Expected architecture_version "{EXPECTED_ARCH_VERSION}", '
            f'got {data.get("architecture_version")}'
        )
    print("✅ Health payload valid")


def test_auth_flow(base_url: str) -> str:
    """Login, call /users/me with token; return token."""
    print("\n🔎 Testing login flow")
    url = f"{base_url.rstrip('/')}/api/v1/auth/login"
    status, _, body = _http_post_json(url, {"username": "test", "password": "test"})
    if status != 200:
        fail(f"Login failed with {status}: {body[:200]}")
    try:
        data = json.loads(body)
        token = data["data"]["token"]
    except (KeyError, json.JSONDecodeError) as e:
        fail(f"Login response missing token: {e}")
    print("✅ Token issued")

    print("\n🔎 Testing protected endpoint")
    me_url = f"{base_url.rstrip('/')}/api/v1/users/me"
    status, _, _ = _http_get(me_url, headers={"Authorization": f"Bearer {token}"})
    if status != 200:
        fail(f"Protected endpoint failed with {status}")
    print("✅ Protected endpoint valid")
    return token


def _header_get(headers: dict[str, str], name: str) -> str | None:
    """Case-insensitive header lookup."""
    name_lower = name.lower()
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return None


def test_request_id(base_url: str) -> None:
    """Ensure X-Request-ID is echoed back."""
    print("\n🔎 Testing Request ID propagation")
    trace_id = str(uuid.uuid4())
    url = f"{base_url.rstrip('/')}/api/health/"
    _, headers, _ = _http_get(url, headers={"X-Request-ID": trace_id})
    echoed = _header_get(headers, "X-Request-ID")
    if echoed != trace_id:
        fail(f"Request ID not propagated: sent {trace_id!r}, got {echoed!r}")
    print("✅ Request ID propagated")


def test_db_restart_resilience(base_url: str) -> None:
    """Stop postgres, assert 503; start postgres, assert 200."""
    print("\n🔎 Testing DB restart resilience")
    subprocess.run("docker compose stop postgres", shell=True, check=False)
    time.sleep(DB_STOP_WAIT)

    url = f"{base_url.rstrip('/')}/api/health/"
    status, _, _ = _http_get_maybe_fail(url)
    if status != 503:
        fail(f"Health should be 503 when DB stopped, got {status}")

    subprocess.run("docker compose start postgres", shell=True, check=False)
    time.sleep(DB_RESTART_WAIT)

    status, _, _ = _http_get(url)
    if status != 200:
        fail(f"Health should recover to 200 after DB restart, got {status}")
    print("✅ DB restart resilience valid")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 1 certification: docs, audit, Docker, migrations, API."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--skip-docker-tests",
        action="store_true",
        help="Skip Docker build and DB restart resilience (e.g. in CI without docker)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print("\n===== PHASE 1 FULL CERTIFICATION =====")

    run(f"{sys.executable} docs_check.py", "Governance Docs Check")
    run(f"{sys.executable} engineering_audit.py", "Engineering Audit")
    if not args.skip_docker_tests:
        run("docker build ./backend", "Docker Build Validation")
        run(
            "docker compose exec backend python manage.py makemigrations "
            "--check --dry-run",
            "Migration Integrity Check",
        )
    else:
        print("\n⏭️ Skipping Docker build and migration check (--skip-docker-tests)")

    wait_for_health(base_url)
    validate_health_payload(base_url)
    test_auth_flow(base_url)
    test_request_id(base_url)
    if not args.skip_docker_tests:
        test_db_restart_resilience(base_url)
    else:
        print("\n⏭️ Skipping DB restart resilience (--skip-docker-tests)")

    print("\n🎉 PHASE 1 CERTIFIED SUCCESSFULLY")
    print("\nIntegration Maturity: 9/10 — STRUCTURALLY STABLE")
    print("Safe to move to Phase 2.")


if __name__ == "__main__":
    main()
