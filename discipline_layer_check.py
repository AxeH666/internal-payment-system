import os
import sys
from pathlib import Path
import subprocess

ROOT = Path(".")
GIT = ROOT / ".git"
HOOK = GIT / "hooks" / "pre-commit"

REQUIRED_GITIGNORE_LINES = [
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".env",
    "backend/.env",
    "backend/.venv/",
    ".venv/",
    ".vscode/",
    ".idea/",
    ".DS_Store",
    "*.log",
]


def ok(msg):
    print(f"[OK] {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def warn(msg):
    print(f"[WARN] {msg}")


def check_gitignore():
    path = ROOT / ".gitignore"
    if not path.exists():
        return fail(".gitignore missing")

    content = path.read_text()
    missing = [line for line in REQUIRED_GITIGNORE_LINES if line not in content]

    if missing:
        return fail(f".gitignore missing entries: {missing}")

    ok(".gitignore contains required entries")
    return True


def check_pre_commit():
    if not HOOK.exists():
        return fail("pre-commit hook missing")

    # Check executable
    if not os.access(HOOK, os.X_OK):
        return fail("pre-commit hook is not executable")

    content = HOOK.read_text()

    required_checks = [
        "docs_check.py",
        "engineering_audit.py",
        "black --check",
        "flake8",
        "Direct commits to main are forbidden",
    ]

    missing = [c for c in required_checks if c not in content]

    if missing:
        return fail(f"pre-commit missing required checks: {missing}")

    ok("pre-commit hook exists and is properly configured")
    return True


def check_editorconfig():
    path = ROOT / ".editorconfig"
    if not path.exists():
        return fail(".editorconfig missing")

    ok(".editorconfig present")
    return True


def check_black_config():
    path = ROOT / "pyproject.toml"
    if not path.exists():
        return fail("pyproject.toml missing")

    content = path.read_text()
    if "[tool.black]" not in content:
        return fail("Black config missing in pyproject.toml")

    ok("Black configuration present")
    return True


def check_flake8():
    path = ROOT / ".flake8"
    if not path.exists():
        return fail(".flake8 config missing")

    ok(".flake8 config present")
    return True


def check_tools_installed():
    tools = ["black", "flake8"]
    all_ok = True

    for tool in tools:
        result = subprocess.run(
            ["which", tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            fail(f"{tool} not installed")
            all_ok = False
        else:
            ok(f"{tool} installed")

    return all_ok


def main():
    print("\n=== DISCIPLINE LAYER VERIFICATION ===\n")

    checks = [
        check_gitignore,
        check_pre_commit,
        check_editorconfig,
        check_black_config,
        check_flake8,
        check_tools_installed,
    ]

    overall = True

    for check in checks:
        if not check():
            overall = False

    print("\n=== FINAL RESULT ===")

    if overall:
        print("DISCIPLINE LAYER FULLY ENFORCED.")
        sys.exit(0)
    else:
        print("DISCIPLINE LAYER INCOMPLETE. FIX BEFORE PROCEEDING.")
        sys.exit(1)


if __name__ == "__main__":
    main()
