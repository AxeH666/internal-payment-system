import os
import subprocess
import sys

REQUIRED_DOCS = [
    "docs/01_PRD.md",
    "docs/02_DOMAIN_MODEL.md",
    "docs/03_STATE_MACHINE.md",
    "docs/04_API_CONTRACT.md",
    "docs/05_SECURITY_MODEL.md",
    "docs/06_BACKEND_STRUCTURE.md",
    "docs/07_APP_FLOW.md",
    "docs/08_FRONTEND_GUIDELINES.md",
    "docs/09_TECH_STACK.md",
    "docs/10_IMPLEMENTATION_PLAN.md",
]

REQUIRED_DIRS = [
    "backend",
    "frontend",
    "docs",
]

REQUIRED_FILES = [
    "docs_check.py",
    "README.md",
    ".gitignore",
]


def check_git():
    print("\nChecking Git status...")
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            print("  [FAIL] Working directory is NOT clean")
            print(result.stdout)
            return False
        else:
            print("  [OK] Working directory clean")
            return True
    except Exception:
        print("  [FAIL] Git not initialized or not accessible")
        return False


def check_paths(paths):
    all_ok = True
    for path in paths:
        if not os.path.exists(path):
            print(f"  [FAIL] Missing: {path}")
            all_ok = False
        else:
            print(f"  [OK] Found: {path}")
    return all_ok


def check_non_empty(files):
    all_ok = True
    for file in files:
        if not os.path.exists(file):
            continue
        if os.path.getsize(file) == 0:
            print(f"  [FAIL] Empty file: {file}")
            all_ok = False
        else:
            print(f"  [OK] Non-empty: {file}")
    return all_ok


def main():
    print("\n=== FULL PROJECT INTEGRITY CHECK ===")

    overall = True

    print("\nChecking required directories...")
    if not check_paths(REQUIRED_DIRS):
        overall = False

    print("\nChecking required documentation files...")
    if not check_paths(REQUIRED_DOCS):
        overall = False

    print("\nChecking required root files...")
    if not check_paths(REQUIRED_FILES):
        overall = False

    print("\nChecking documentation files are non-empty...")
    if not check_non_empty(REQUIRED_DOCS):
        overall = False

    if not check_git():
        overall = False

    print("\n=== RESULT ===")
    if overall:
        print("ALL SYSTEM CHECKS PASSED.")
        sys.exit(0)
    else:
        print("PROJECT INTEGRITY ISSUES DETECTED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
