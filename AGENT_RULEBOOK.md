# AGENT RULEBOOK

AI agents operating on this codebase must observe these rules. Violations are architectural debt.

---

## 1. PROHIBITED ACTIONS

| Rule | Specification |
|------|---------------|
| Documentation modification | Never modify documentation unless explicitly instructed. |
| Entity structure changes | Never change entity structure without an architecture version bump. |
| Business logic in frontend | Never define business logic in frontend code. |
| Model persistence outside services | Never call `model.save()` outside the service layer. |
| Client-side state transitions | Never implement state transitions client-side. |

---

## 2. REQUIRED ACTIONS

| Rule | Specification |
|------|---------------|
| State machine compliance | Follow `docs/03_STATE_MACHINE.md` strictly. |
| Financial operations | Wrap all financial operations in `transaction.atomic`. |
| View permissions | Enforce `permission_classes` in every view. |
| State-changing APIs | Implement idempotency for all state-changing APIs. |
| Mutation logging | Write logs for every mutation event. |

---

## 3. PROHIBITED ADDITIONS

| Rule | Specification |
|------|---------------|
| Dependencies | No new dependencies without approval. |
| Background tasks | No background tasks. |
| Microservices | No microservices. |
| Async complexity | No async complexity. |
| CI/CD beyond MVP | No CI/CD automation beyond MVP scope. |

---

## 4. CHANGE REQUIREMENTS

Every change must:

1. Pass `engineering_audit.py`
2. Maintain documentation alignment

---

## 5. SYSTEM CONTEXT

- Single-company usage
- Internal-use only

---

*This document is governance. Deviations require explicit approval.*
