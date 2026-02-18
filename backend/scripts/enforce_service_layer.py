"""
Engineering audit: Enforce service layer pattern.
Scans code and fails if PaymentRequest model operations detected outside services.py
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    "PaymentRequest.objects.create(",
    "PaymentRequest.objects.update(",
    "PaymentRequest.objects.filter(",
]

ALLOWED_PATH = "apps/payments/services.py"


def scan_file(filepath):
    """Scan Python file for forbidden patterns."""
    if ALLOWED_PATH in str(filepath):
        return []  # Skip services.py

    issues = []
    try:
        content = filepath.read_text()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in content:
                issues.append(f"{filepath}: Found {pattern}")
    except Exception:
        pass
    return issues


def main():
    backend = Path("backend")
    all_issues = []

    for pyfile in backend.rglob("*.py"):
        if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
            continue
        issues = scan_file(pyfile)
        all_issues.extend(issues)

    if all_issues:
        print("ERROR: Direct PaymentRequest operations detected outside services.py:")
        for issue in all_issues:
            print(f"  {issue}")
        sys.exit(1)

    print("OK: No direct PaymentRequest operations outside service layer")


if __name__ == "__main__":
    main()
