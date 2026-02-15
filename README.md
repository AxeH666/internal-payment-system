# Internal Payment Workflow System

## Branch Governance Model

### Branch Structure

#### `main`
- **Purpose:** Production-ready code only
- **Status:** Protected branch
- **Rules:**
  - No direct commits allowed
  - Only receives merges from `develop` or `hotfix/*` branches
  - All merges must be via Pull Request
  - Must pass all integrity checks before merge

#### `develop`
- **Purpose:** Active integration branch
- **Status:** Default development branch
- **Rules:**
  - Receives merges from `feature/*` branches
  - All merges must be via Pull Request
  - Must pass `docs_check.py` before merge
  - Must pass `engineering_audit.py` before merge
  - Merged to `main` only after full testing and approval

#### `feature/<ticket-name>`
- **Purpose:** One feature per branch
- **Rules:**
  - Created from `develop`
  - Merged back into `develop` via Pull Request
  - Must pass integrity checks before merge
  - Deleted after successful merge

#### `hotfix/<issue>`
- **Purpose:** Emergency production fixes
- **Rules:**
  - Created from `main`
  - Merged into both `main` and `develop`
  - Must pass integrity checks before merge
  - Deleted after successful merge

### Workflow Rules

1. **No direct commits to main**
   - All changes to `main` must come through Pull Requests
   - Direct pushes to `main` are blocked

2. **All merges via Pull Request**
   - No force merges
   - All PRs require review
   - All PRs must pass CI/CD checks

3. **develop branch requirements**
   - Must pass `docs_check.py` validation
   - Must pass `engineering_audit.py` validation
   - All tests must pass

4. **Branch naming conventions**
   - Features: `feature/<ticket-name>` (e.g., `feature/PROJ-123-payment-api`)
   - Hotfixes: `hotfix/<issue>` (e.g., `hotfix/PROJ-456-security-patch`)

### Architecture Freeze

**Tag:** `v0.1.0-arch-freeze`

Architecture is frozen at this tag. All changes requiring architecture modifications must go through formal change control process.

---

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for setup instructions.

## Infrastructure

See [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) for infrastructure documentation.
