#!/usr/bin/env python3
"""
Documentation Integrity Checker for Internal Payment Workflow System.
Deterministic structural validation of docs; not semantic AI checking.
"""

import os
import re
import sys

DOCS_DIR = "docs"

REQUIRED_FILES = [
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

FORBIDDEN_TERMS = [
    "multi-tenant",
    "multi tenancy",
    "ledger",
    "gst",
    "SaaS",
    "external integration",
    "bank integration",
    "mobile app",
    "etc.",
    "may include",
    "future phase",
]

REQUIRED_SECTIONS = {
    "01_PRD.md": [
        "Purpose",
        "Problem Statement",
        "Core Capabilities",
        "Explicit Non-Goals",
        "System Invariants",
        "Definition of Done",
        "Scope Freeze Declaration",
    ],
    "02_DOMAIN_MODEL.md": [
        "Core Entities",
        "Structural Invariants",
        "Immutability",
        "Domain Freeze Declaration",
    ],
    "03_STATE_MACHINE.md": [
        "PaymentRequest State Machine",
        "PaymentBatch State Machine",
        "SOAVersion",
        "Transition Invariants",
        "State Machine Freeze Declaration",
    ],
    "04_API_CONTRACT.md": [
        "General API Principles",
        "Authentication Requirements",
        "Standard Error Format",
        "Endpoint Definitions",
        "Idempotency",
        "API Freeze Declaration",
    ],
    "05_SECURITY_MODEL.md": [
        "Security Objectives",
        "Authentication Model",
        "Authorization Model",
        "Security Invariants",
        "Security Freeze Declaration",
    ],
    "06_BACKEND_STRUCTURE.md": [
        "Project Structure",
        "Model Definitions",
        "Transaction Boundary Mapping",
        "Audit Integration",
        "Service Layer",
        "Backend Freeze Declaration",
    ],
    "07_APP_FLOW.md": [
        "Route Registry",
        "Screen Definitions",
        "Action-to-API Mapping",
        "State-Based UI Visibility",
        "Application Flow Freeze Declaration",
    ],
    "08_FRONTEND_GUIDELINES.md": [
        "Frontend Architecture Principles",
        "Error Rendering Rules",
        "Concurrency Conflict UI Handling",
    ],
    "09_TECH_STACK.md": [
        "Runtime Environment",
        "Backend Stack",
        "Frontend Stack",
        "Version Locking Policy",
        "Stack Freeze Declaration",
    ],
    "10_IMPLEMENTATION_PLAN.md": [
        "Branch Strategy",
        "Merge",
        "Hardening",
        "Implementation Guardrails",
        "Implementation Freeze",
    ],
}

IMPLEMENTATION_PLAN_REQUIRED_CONTENT = [
    ("Branch strategy introduction timing", ["Branch Strategy", "develop", "Phase 2"]),
    ("Architecture freeze tag", ["architecture freeze", "arch-freeze", "Tag"]),
    ("Feature branch workflow", ["feature branch", "Feature branch"]),
    (
        "Hardening tests explicitly listed",
        [
            "Concurrency",
            "Duplicate",
            "Permission",
            "Closed batch",
            "Paid mutation",
            "SOA",
        ],
        4,
    ),
    (
        "Guardrails explicit and strict",
        ["Guardrails", "No new entity", "No new endpoint", "No permission bypass"],
    ),
    ("No skipping layers", ["No skipping", "skipping layers", "Bottom-up"]),
]

IMPLEMENTATION_PLAN_FORBIDDEN_TERMS = [
    "jenkins",
    "gitlab ci",
    "github actions",
    "circleci",
    "travis",
]

TECH_STACK_FORBIDDEN_TERMS = [
    "latest",
    "aws",
    "gcp",
    "kubernetes",
    "microservice",
]

TECH_STACK_VAGUE_PHRASES = [
    "x.x.x",
    "x.x",
    "x.y.z",
    "or similar",
]

TECH_STACK_REQUIRED_CONTENT = [
    ("Exact versions appear", ["3.11", "5.0", "18.2", "16.4", "pinned"]),
    (
        "No unnecessary monitoring stack",
        ["no third-party", "no Datadog", "No third-party", "out of scope"],
    ),
]

FRONTEND_GUIDELINES_REQUIRED_CONTENT = [
    (
        "No business logic in frontend",
        ["business logic", "frontend", "server", "backend"],
    ),
    (
        "No state transitions defined client-side",
        ["state transition", "client-side", "client", "server"],
    ),
    ("UI disables CLOSED/PAID actions", ["CLOSED", "PAID", "disabled", "disable"]),
    ("Error rendering standardized", ["error", "standardized", "standard", "format"]),
    ("Concurrency reload defined", ["concurrency", "reload", "409", "CONFLICT"]),
    (
        "No visual styling specifics",
        ["no color", "no branding", "no visual", "exclude styling", "avoid branding"],
    ),
]

APP_FLOW_REQUIRED_CONTENT = [
    (
        "All Phase 1.3 screens exist",
        ["/login", "/batches", "/batches/new", "/audit", "/requests"],
        5,
    ),
    (
        "No screen allows illegal state transition",
        [
            "State-Based UI Visibility",
            "Hidden",
            "DRAFT",
            "PENDING_APPROVAL",
            "APPROVED",
        ],
    ),
    (
        "Every action maps to API endpoint",
        ["Action-to-API Mapping", "API Endpoint", "/api/v1"],
    ),
    (
        "No business logic assumed client-side",
        ["No client-side business logic", "server", "source of truth"],
    ),
    (
        "CLOSED batch disables actions",
        ["CLOSED batch", "COMPLETED", "CANCELLED", "disabled"],
    ),
    ("HOLD to RESUBMIT path exists", ["HOLD", "RESUBMIT"]),
    ("FINAL SOA locks UI", ["Upload SOA", "DRAFT", "Hidden"], 2),
]

BACKEND_STRUCTURE_REQUIRED_CONTENT = [
    ("Clear Django app layout", ["apps/", "users", "payments", "audit", "auth"]),
    ("Model fields listed clearly", ["Model Definitions", "Field", "Type", "Nullable"]),
    (
        "Unique constraint for (payment_request, version_number)",
        ["payment_request", "version_number", "UniqueConstraint"],
        2,
    ),
    ("transaction.atomic for approve", ["approve_request", "transaction.atomic"], 2),
    ("transaction.atomic for mark paid", ["mark_paid", "transaction.atomic"], 2),
    ("transaction.atomic for generate SOA", ["upload_soa", "transaction.atomic"], 2),
    ("transaction.atomic for close batch", ["cancel_batch", "transaction.atomic"], 2),
    ("select_for_update requirement", ["select_for_update"]),
    (
        "Audit integration clearly defined",
        ["Audit Integration", "AuditLog", "create_audit"],
    ),
    ("Service layer separation from views", ["service layer", "views"]),
    (
        "No direct model mutation from API view",
        ["direct model", "bypassing service", "Model.save", "never call"],
    ),
    ("JSON logging structure defined", ["JSON", "logging", "structured"]),
]

SECURITY_MODEL_REQUIRED_CONTENT = [
    ("JWT expiry", ["expiry", "expir", "lifetime", "15 minutes"]),
    ("Refresh rotation invalidation", ["refresh token", "invalidate", "rotation"]),
    ("Atomic transaction requirement", ["atomic", "atomic transaction"]),
    ("Row-level locking requirement", ["row-level lock", "row level lock"]),
    ("No DEBUG in prod", ["debug", "production", "disabled"]),
    ("No stack trace exposure", ["stack trace", "stack traces"]),
    ("SuperAdmin override logging", ["superadmin", "override", "logging"]),
    ("Backup restore test requirement", ["restore", "test", "quarterly"]),
]


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_required_sections(filename, content):
    missing = []
    for section in REQUIRED_SECTIONS.get(filename, []):
        if section not in content:
            missing.append(section)
    return missing


def get_content_excluding_sections(content, section_headers):
    """Return content with exclusion sections removed for forbidden-term checking."""
    lines = content.split("\n")
    result = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            in_exclusion = any(header in line for header in section_headers)
            skip = in_exclusion
        if skip:
            continue
        result.append(line)
    return "\n".join(result)


EXCLUSION_CONTEXT = (
    "exclude",
    "no ",
    "without",
    "out of scope",
    "not in scope",
    "non-goal",
    "non-goals",
)


def check_forbidden_terms(content):
    exclusion_sections = [
        "Explicit Non-Goals",
        "Explicit Domain Exclusions",
    ]
    content_to_check = get_content_excluding_sections(content, exclusion_sections)
    found = []
    lower_content = content_to_check.lower()
    lower_lines = content_to_check.split("\n")
    for term in FORBIDDEN_TERMS:
        term_lower = term.lower()
        if term_lower not in lower_content:
            continue
        for i, line in enumerate(lower_lines):
            if term_lower in line:
                in_exclusion_context = any(ctx in line for ctx in EXCLUSION_CONTEXT)
                if not in_exclusion_context:
                    found.append(term)
                    break
    return found


def check_numbered_invariants(content):
    pattern = re.compile(r"\n\d+\.\s")
    matches = pattern.findall(content)
    return len(matches) >= 3


def check_state_transitions(content):
    lower = content.lower()
    return (
        "→" in content
        or "allowed transitions" in lower
        or "disallowed transitions" in lower
        or ("from state" in lower and "to state" in lower)
    )


def check_idempotency(content):
    return "Idempotency" in content or "idempotent" in content.lower()


def check_security_model_content(content):
    """Verify 05_SECURITY_MODEL.md includes required security architecture items."""
    lower = content.lower()
    missing = []
    for topic_name, keywords in SECURITY_MODEL_REQUIRED_CONTENT:
        if not any(kw.lower() in lower for kw in keywords):
            missing.append(topic_name)
    return missing


def check_security_invariants_numbered(content):
    """Verify Security Invariants section has numbered items (SI-1, SI-2, etc.)."""
    return (
        "SI-1" in content or "SI-2" in content or re.search(r"\d+\.\s+\*\*SI-", content)
    )


def check_backend_structure_content(content):
    """Verify 06_BACKEND_STRUCTURE.md includes required backend architecture items."""
    lower = content.lower()
    missing = []
    for item in BACKEND_STRUCTURE_REQUIRED_CONTENT:
        if len(item) == 2:
            topic_name, keywords = item
            min_matches = 1
        else:
            topic_name, keywords, min_matches = item
        matches = sum(1 for kw in keywords if kw.lower() in lower)
        if matches < min_matches:
            missing.append(topic_name)
    return missing


def check_app_flow_content(content):
    """Verify 07_APP_FLOW.md includes required application flow items."""
    lower = content.lower()
    missing = []
    for item in APP_FLOW_REQUIRED_CONTENT:
        if len(item) == 2:
            topic_name, keywords = item
            min_matches = 1
        else:
            topic_name, keywords, min_matches = item
        matches = sum(1 for kw in keywords if kw.lower() in lower)
        if matches < min_matches:
            missing.append(topic_name)
    return missing


def check_frontend_guidelines_content(content):
    """Verify 08_FRONTEND_GUIDELINES.md includes required frontend guideline items."""
    lower = content.lower()
    missing = []
    for topic_name, keywords in FRONTEND_GUIDELINES_REQUIRED_CONTENT:
        if not any(kw.lower() in lower for kw in keywords):
            missing.append(topic_name)
    return missing


def check_tech_stack_forbidden(content):
    """Verify 09_TECH_STACK.md has no forbidden terms."""
    lower = content.lower()
    found = []
    for term in TECH_STACK_FORBIDDEN_TERMS:
        if term in lower:
            found.append(term)
    return found


def check_tech_stack_vague(content):
    """Verify 09_TECH_STACK.md has no vague placeholder phrases."""
    lower = content.lower()
    found = []
    for phrase in TECH_STACK_VAGUE_PHRASES:
        if phrase in lower:
            found.append(phrase)
    return found


def check_tech_stack_versions(content):
    """Verify 09_TECH_STACK.md has exact versions (X.Y.Z pattern), not placeholders."""
    version_pattern = re.compile(r"\d+\.\d+\.\d+")
    matches = version_pattern.findall(content)
    return len(matches) >= 5


def check_tech_stack_content(content):
    """Verify 09_TECH_STACK.md includes required tech stack items."""
    lower = content.lower()
    missing = []
    for topic_name, keywords in TECH_STACK_REQUIRED_CONTENT:
        if not any(kw.lower() in lower for kw in keywords):
            missing.append(topic_name)
    return missing


def check_implementation_plan_content(content):
    """Verify 10_IMPLEMENTATION_PLAN.md includes required implementation plan items."""
    lower = content.lower()
    missing = []
    for item in IMPLEMENTATION_PLAN_REQUIRED_CONTENT:
        if len(item) == 2:
            topic_name, keywords = item
            min_matches = 1
        else:
            topic_name, keywords, min_matches = item
        matches = sum(1 for kw in keywords if kw.lower() in lower)
        if matches < min_matches:
            missing.append(topic_name)
    return missing


def check_implementation_plan_forbidden(content):
    """Verify 10_IMPLEMENTATION_PLAN.md has no CI/CD complexity beyond MVP."""
    lower = content.lower()
    found = []
    for term in IMPLEMENTATION_PLAN_FORBIDDEN_TERMS:
        if term in lower:
            found.append(term)
    return found


def run_checks():
    print("\n=== Documentation Integrity Check ===\n")
    all_passed = True

    for filename in REQUIRED_FILES:
        path = os.path.join(DOCS_DIR, filename)

        if not os.path.exists(path):
            print(f"[ERROR] Missing file: {filename}")
            all_passed = False
            continue

        content = read_file(path)
        print(f"\nChecking {filename}...")

        # Section check
        missing_sections = check_required_sections(filename, content)
        if missing_sections:
            print(f"  [FAIL] Missing sections: {missing_sections}")
            all_passed = False
        else:
            print("  [OK] Required sections present")

        # Forbidden terms
        forbidden_found = check_forbidden_terms(content)
        if forbidden_found:
            print(f"  [FAIL] Forbidden terms found: {forbidden_found}")
            all_passed = False
        else:
            print("  [OK] No forbidden terms")

        # Invariants check
        if filename in [
            "01_PRD.md",
            "02_DOMAIN_MODEL.md",
            "03_STATE_MACHINE.md",
            "05_SECURITY_MODEL.md",
        ]:
            if not check_numbered_invariants(content):
                print("  [FAIL] Numbered invariants missing or insufficient")
                all_passed = False
            else:
                print("  [OK] Numbered invariants detected")

        # State transitions check
        if filename == "03_STATE_MACHINE.md":
            if not check_state_transitions(content):
                print("  [FAIL] State transitions not clearly defined")
                all_passed = False
            else:
                print("  [OK] State transitions detected")

        # Idempotency check
        if filename == "04_API_CONTRACT.md":
            if not check_idempotency(content):
                print("  [FAIL] Idempotency rules missing")
                all_passed = False
            else:
                print("  [OK] Idempotency rules detected")

        # Security model checks
        if filename == "05_SECURITY_MODEL.md":
            security_missing = check_security_model_content(content)
            if security_missing:
                print(f"  [FAIL] Missing security architecture: {security_missing}")
                all_passed = False
            else:
                print("  [OK] Security architecture items present")
            if not check_security_invariants_numbered(content):
                print("  [FAIL] Security invariants not numbered (SI-1, SI-2, etc.)")
                all_passed = False
            else:
                print("  [OK] Security invariants numbered")

        # Backend structure checks
        if filename == "06_BACKEND_STRUCTURE.md":
            backend_missing = check_backend_structure_content(content)
            if backend_missing:
                print(f"  [FAIL] Missing backend architecture: {backend_missing}")
                all_passed = False
            else:
                print("  [OK] Backend architecture items present")

        # App flow checks
        if filename == "07_APP_FLOW.md":
            app_flow_missing = check_app_flow_content(content)
            if app_flow_missing:
                print(f"  [FAIL] Missing app flow requirements: {app_flow_missing}")
                all_passed = False
            else:
                print("  [OK] App flow requirements present")

        # Frontend guidelines checks
        if filename == "08_FRONTEND_GUIDELINES.md":
            frontend_missing = check_frontend_guidelines_content(content)
            if frontend_missing:
                print(f"  [FAIL] Missing frontend guidelines: {frontend_missing}")
                all_passed = False
            else:
                print("  [OK] Frontend guidelines present")

        # Tech stack checks
        if filename == "09_TECH_STACK.md":
            tech_forbidden = check_tech_stack_forbidden(content)
            if tech_forbidden:
                print(f"  [FAIL] Forbidden tech stack terms: {tech_forbidden}")
                all_passed = False
            else:
                print("  [OK] No forbidden tech stack terms")
            tech_vague = check_tech_stack_vague(content)
            if tech_vague:
                print(f"  [FAIL] Vague placeholder phrases: {tech_vague}")
                all_passed = False
            else:
                print("  [OK] No vague placeholders")
            if not check_tech_stack_versions(content):
                print("  [FAIL] Insufficient exact versions (need 5+ X.Y.Z)")
                all_passed = False
            else:
                print("  [OK] Exact versions present")
            tech_missing = check_tech_stack_content(content)
            if tech_missing:
                print(f"  [FAIL] Missing tech stack requirements: {tech_missing}")
                all_passed = False
            else:
                print("  [OK] Tech stack requirements present")

        # Implementation plan checks
        if filename == "10_IMPLEMENTATION_PLAN.md":
            impl_forbidden = check_implementation_plan_forbidden(content)
            if impl_forbidden:
                print(f"  [FAIL] CI/CD complexity beyond MVP: {impl_forbidden}")
                all_passed = False
            else:
                print("  [OK] No CI/CD complexity beyond MVP")
            impl_missing = check_implementation_plan_content(content)
            if impl_missing:
                print(
                    f"  [FAIL] Missing implementation plan requirements: {impl_missing}"
                )
                all_passed = False
            else:
                print("  [OK] Implementation plan requirements present")

    print("\n=== RESULT ===")
    if all_passed:
        print("All documentation integrity checks PASSED.")
    else:
        print("Documentation integrity issues detected.")
        sys.exit(1)


if __name__ == "__main__":
    run_checks()
