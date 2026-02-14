# IMPLEMENTATION PLAN

## Branch Strategy

main:
- Production ready only
- Protected
- No direct commits

develop:
- Integration branch
- All features merge here first

feature/<name>:
- One feature per branch
- Merge into develop via PR

hotfix/<issue>:
- Emergency fixes
- Merge into main and develop

## Enforcement

- All merges via Pull Request
- CI must pass
- engineering_audit.py must pass
- docs_check.py must pass
- Architecture frozen at tag v0.1.0-arch-freeze
