import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_file(path, description):
    if path.exists():
        print(f"[OK] {description}")
        return True
    else:
        print(f"[MISSING] {description}")
        return False


def check_git_tag(tag_name):
    try:
        result = subprocess.run(
            ["git", "tag"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = result.stdout.splitlines()
        if tag_name in tags:
            print(f"[OK] Architecture freeze tag '{tag_name}' exists")
            return True
        else:
            print(f"[MISSING] Architecture freeze tag '{tag_name}'")
            return False
    except Exception:
        print("[ERROR] Unable to check git tags")
        return False


def check_git_default_branch():
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        if "main" in result.stdout:
            print("[OK] Default branch is main")
            return True
        else:
            print("[WARNING] Default branch is not main")
            return False
    except Exception:
        print("[WARNING] Could not determine default branch")
        return False


def check_env_wiring():
    env_candidates = [
        BASE_DIR / ".env",  # preferred for docker compose (project root)
        BASE_DIR / "backend" / ".env",  # common for local backend runs
    ]
    env_path = next((p for p in env_candidates if p.exists()), None)
    if env_path is None:
        print("[MISSING] .env (project root) or backend/.env")
        return False

    required_vars = [
        "SECRET_KEY",
        "DEBUG",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    ]

    content = env_path.read_text()
    missing = []

    for var in required_vars:
        if var not in content:
            missing.append(var)

    if not missing:
        print(f"[OK] {env_path} contains required variables")
        return True
    else:
        print(f"[MISSING] {env_path} missing variables: {missing}")
        return False


def check_gitignore():
    gitignore = BASE_DIR / ".gitignore"
    if not gitignore.exists():
        print("[MISSING] .gitignore")
        return False

    content = gitignore.read_text()

    checks = {
        ".env": ".env ignored",
        "backend/.venv": "backend/.venv ignored",
    }

    all_ok = True

    for key, description in checks.items():
        if key in content:
            print(f"[OK] {description}")
        else:
            print(f"[MISSING] {description}")
            all_ok = False

    return all_ok


def main():
    print_header("GOVERNANCE AUDIT — PHASE 1.6 → 1.10")

    # 1.6
    print_header("1.6 — Branch Governance Documentation")
    check_file(BASE_DIR / "README.md", "README.md exists")
    check_file(
        BASE_DIR / "10_IMPLEMENTATION_PLAN.md", "10_IMPLEMENTATION_PLAN.md exists"
    )
    check_git_default_branch()

    # 1.7
    print_header("1.7 — Local Discipline Layer")
    check_file(BASE_DIR / ".editorconfig", ".editorconfig exists")
    check_file(BASE_DIR / "engineering_audit.py", "engineering_audit.py exists")
    check_file(BASE_DIR / "docs_check.py", "docs_check.py exists")
    check_gitignore()

    # 1.8
    print_header("1.8 — CI Stub")
    check_file(
        BASE_DIR / ".github" / "workflows" / "ci.yml",
        "CI workflow (.github/workflows/ci.yml) exists",
    )

    # 1.9
    print_header("1.9 — Architecture Freeze Lock")
    check_file(BASE_DIR / ".github" / "CODEOWNERS", "CODEOWNERS file exists")
    check_git_tag("v0.1.0-arch-freeze")

    # 1.10
    print_header("1.10 — Environment Readiness")
    check_file(BASE_DIR / "docker-compose.yml", "docker-compose.yml exists")
    check_env_wiring()
    check_file(
        BASE_DIR / "backend" / "core" / "settings.py",
        "Django settings wired (backend/core/settings.py exists)",
    )

    print_header("AUDIT COMPLETE")
    print("Review any [MISSING] entries above.")
    print("Phase 2 must NOT start until all are [OK].")


if __name__ == "__main__":
    main()
