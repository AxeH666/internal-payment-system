# Branch Protection Policy

This document describes the branch protection and merge discipline for this repository. **No code changes** are implied; this is governance documentation only.

## Requirements

- **Require PR before merge** — All changes to protected branches must land via a Pull Request. No direct commits to `main` (or other protected branches) from the local repo.
- **Require Backend CI to pass** — The Backend CI workflow (`.github/workflows/backend-ci.yml`) must succeed on the PR before merge. This includes: Black check, Flake8, Django tests, and the Deep Invariant Probe.
- **No force pushes** — Force pushes to protected branches are disallowed. History must not be rewritten on shared branches.
- **Require linear history** — Merges should preserve a linear history where applicable (e.g. squash or rebase before merge, per team policy).
- **No direct push to main** — The `main` branch (and any other designated default branch) must not accept direct pushes; all updates must come from merged PRs.

## Summary

| Rule                    | Description                                              |
|-------------------------|----------------------------------------------------------|
| PR required             | All merges go through a Pull Request.                    |
| Backend CI must pass    | Backend CI workflow must be green before merge.          |
| No force pushes         | No `--force` (or equivalent) on protected branches.     |
| Linear history         | Prefer squash/rebase so history remains linear.         |
| No direct push to main | `main` is updated only by merging approved PRs.         |

Configure these rules in the repository’s **Branch protection rules** (e.g. on GitHub: Settings → Branches → Branch protection rules) for `main` and any other protected branches (e.g. `phase-2-ledger`).
