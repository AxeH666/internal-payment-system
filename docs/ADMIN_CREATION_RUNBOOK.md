# Admin Creation Runbook

**Phase 2.** How to create the first (or additional) ADMIN user. No API or UI can create or upgrade to ADMIN.

---

## Prerequisites

- Backend environment with Django and database (e.g. `backend/.venv` activated, or Docker).
- Database migrations applied: `python manage.py migrate` (from `backend/`).

---

## Create an ADMIN user via shell

1. From the project root, go to the backend directory and ensure your environment is active (e.g. virtualenv, or use `python` from the venv).

2. Open a Django shell:

   ```bash
   cd backend
   python manage.py shell
   ```

3. In the shell, create an ADMIN user using the same service used by Django’s `createsuperuser` semantics (role set to ADMIN):

   ```python
   from apps.users.models import User

   User.objects.create_superuser(
       username="admin",
       password="your-secure-password",
   )
   ```

   This creates a user with `role=ADMIN`. No other roles are set by `create_superuser`; the user is an administrator.

4. Exit the shell (`exit()` or Ctrl+D).

5. Use the credentials to log in via the API (`POST /api/v1/auth/login`) or the frontend.

---

## Important

- **Do not** create ADMIN users via `POST /api/v1/users/` with `role=ADMIN`. The API rejects this with 400 and the message “Cannot create ADMIN users via API”.
- **Do not** rely on the UI to create ADMIN users; the UI only calls the same API, which does not allow ADMIN.
- Ensure at least one ADMIN exists before relying on admin-only operations (ledger CRUD, user creation). There is no “at least one ADMIN” database constraint; operational procedures should ensure an ADMIN is always available.
