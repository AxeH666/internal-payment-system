import subprocess
import sys
from pathlib import Path

ROOT = Path(".").resolve()
DOCS = ROOT / "docs"
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

EXPECTED_BRANCHES = ["main", "develop"]
ARCH_TAG = "v0.1.0-arch-freeze"


# ======================================================
# Utility
# ======================================================


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def ok(msg):
    print(f"[OK] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def should_scan(path: Path):
    """Strict filter to exclude virtualenv and framework code"""
    path_str = str(path)
    if ".venv" in path_str or "site-packages" in path_str:
        return False
    if "__pycache__" in path_str:
        return False
    if "migrations" in path_str:
        return False
    return True


# ======================================================
# Git Checks
# ======================================================


def check_git_repo():
    if not (ROOT / ".git").exists():
        return fail("Not a git repository")
    ok("Git repository detected")
    return True


def check_branches():
    stdout, _, _ = run(["git", "branch"])
    branches = [b.strip().replace("* ", "") for b in stdout.splitlines()]
    missing = [b for b in EXPECTED_BRANCHES if b not in branches]
    if missing:
        return fail(f"Missing required branches: {missing}")
    ok("Required branches present")
    return True


def check_architecture_tag():
    stdout, _, _ = run(["git", "tag"])
    if ARCH_TAG not in stdout.split():
        warn("Architecture freeze tag missing")
    else:
        ok("Architecture freeze tag exists")
    return True


def check_clean_working_tree():
    stdout, _, _ = run(["git", "status", "--porcelain"])
    if stdout.strip():
        warn("Working directory is dirty (commit changes before release)")
    else:
        ok("Working directory clean")
    return True


# ======================================================
# Documentation
# ======================================================


def check_docs():
    required = [
        "01_PRD.md",
        "02_DOMAIN_MODEL.md",
        "03_STATE_MACHINE.md",
        "04_API_CONTRACT.md",
        "05_SECURITY_MODEL.md",
        "06_BACKEND_STRUCTURE.md",
        "07_APP_FLOW.md",
        "08_FRONTEND_GUIDELINES.md",
        "09_TECH_STACK.md",
        "10_IMPLEMENTATION_PLAN.md",
    ]

    missing = [f for f in required if not (DOCS / f).exists()]
    if missing:
        return fail(f"Missing documentation files: {missing}")

    ok("All architecture documents present")

    for f in required:
        if (DOCS / f).stat().st_size == 0:
            return fail(f"Empty documentation file: {f}")

    ok("Documentation files are non-empty")
    return True


# ======================================================
# Backend Checks
# ======================================================


def scan_backend_for_raw_save():
    if not BACKEND.exists():
        warn("Backend folder not yet initialized")
        return True

    issues = []

    for pyfile in BACKEND.rglob("*.py"):
        if not should_scan(pyfile):
            continue

        try:
            content = pyfile.read_text(errors="ignore")
            # Flag direct instance `.save(` usage outside service layer.
            # Structural model overrides legitimately call `super().save(...)` and
            # must not be flagged.
            if "service" in str(pyfile):
                continue

            for line in content.splitlines():
                if ".save(" not in line:
                    continue
                if "super().save(" in line:
                    continue
                issues.append(str(pyfile))
                break
        except Exception:
            continue

    if issues:
        return fail(f"Direct model save outside service layer: {issues}")

    ok("No unsafe direct model saves detected")
    return True


def scan_for_permission_classes():
    if not BACKEND.exists():
        return True

    issues = []

    for pyfile in BACKEND.rglob("views.py"):
        if not should_scan(pyfile):
            continue

        try:
            content = pyfile.read_text(errors="ignore")
            if "permission_classes" not in content:
                issues.append(str(pyfile))
        except Exception:
            continue

    if issues:
        return fail(f"Views missing permission_classes: {issues}")

    ok("Permission classes present in project views")
    return True


def scan_for_atomic_usage():
    if not BACKEND.exists():
        return True

    atomic_found = False

    for pyfile in BACKEND.rglob("*.py"):
        if not should_scan(pyfile):
            continue

        try:
            content = pyfile.read_text(errors="ignore")
            if "transaction.atomic" in content:
                atomic_found = True
                break
        except Exception:
            continue

    if not atomic_found:
        warn(
            "No transaction.atomic usage detected "
            "(expected after service layer implemented)"
        )
    else:
        ok("Atomic transaction usage detected")

    return True


# ======================================================
# Frontend Check
# ======================================================


def scan_frontend_for_state_logic():
    if not FRONTEND.exists():
        warn("Frontend folder not yet initialized")
        return True

    risky_patterns = ["APPROVED", "PAID", "HOLD", "CLOSED"]
    leaks = []

    for file in FRONTEND.rglob("*.tsx"):
        try:
            content = file.read_text(errors="ignore")
            for pattern in risky_patterns:
                if pattern in content:
                    leaks.append(str(file))
                    break
        except Exception:
            continue

    if leaks:
        return fail(f"Frontend contains business state logic: {leaks}")

    ok("No frontend business logic leakage detected")
    return True


# ======================================================
# Docker
# ======================================================


def check_docker():
    if not (ROOT / "docker-compose.yml").exists():
        warn("docker-compose.yml missing")
    else:
        ok("Docker configuration present")
    return True


# ======================================================
# MAIN
# ======================================================


def main():
    print("\n=== ENGINEERING SYSTEM AUDIT ===\n")

    checks = [
        check_git_repo,
        check_branches,
        check_architecture_tag,
        check_clean_working_tree,
        check_docs,
        check_docker,
        scan_backend_for_raw_save,
        scan_for_permission_classes,
        scan_for_atomic_usage,
        scan_frontend_for_state_logic,
    ]

    overall = True

    for check in checks:
        if not check():
            overall = False

    print("\n=== FINAL RESULT ===")

    if overall:
        print("SYSTEM IS STRUCTURALLY ROBUST AND AGENT-READY.")
        sys.exit(0)
    else:
        print("ENGINEERING RISKS DETECTED. FIX BEFORE PROCEEDING.")
        sys.exit(1)


if __name__ == "__main__":
    main()
