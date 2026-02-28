# Deep Scan Issues Report
**Generated:** 2026-02-18  
**System:** Internal Payment System

---

## 🔴 CRITICAL ISSUES

### 1. Migration State Inconsistency (BLOCKING)
**Severity:** CRITICAL  
**Status:** Backend service cannot start

**Problem:**
- `users` app migrations are **NOT recorded** in `django_migrations` table
- Database has `users` table with ADMIN role constraint already applied
- `payments.0001_initial` depends on `AUTH_USER_MODEL` (users), creating dependency conflict
- Backend service crashes on startup with: `InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency users.0001_initial`

**Evidence:**
```sql
-- django_migrations shows NO users migrations:
SELECT app, name FROM django_migrations WHERE app = 'users';
-- Returns: (0 rows)

-- But users table exists with ADMIN constraint:
\d users
-- Shows: valid_role CHECK (role IN ('ADMIN', 'CREATOR', 'APPROVER', 'VIEWER'))
```

**Impact:**
- Backend service cannot start
- Cannot run migrations
- Cannot deploy

**Fix Required:**
1. Insert users migrations into `django_migrations` table manually OR
2. Fake-apply users migrations: `python manage.py migrate users --fake`
3. Ensure migration dependencies are correct

---

### 2. Backend Service Not Running
**Severity:** CRITICAL  
**Status:** Service crashed

**Problem:**
- Backend container exits immediately on startup
- Error: Migration dependency inconsistency (see Issue #1)

**Evidence:**
```bash
docker compose ps
# Shows: Only postgres running, backend not running

docker compose logs backend
# Shows: InconsistentMigrationHistory error
```

**Impact:**
- API endpoints unavailable
- System non-functional

**Fix Required:**
- Resolve migration issue first (Issue #1)
- Then restart backend: `docker compose restart backend`

---

## 🟡 HIGH PRIORITY ISSUES

### 3. Test Tokens Not Configured
**Severity:** HIGH  
**Status:** Tests will fail

**Problem:**
- `CREATOR_TOKEN` and `APPROVER_TOKEN` are placeholders: `"NEW_TOKEN_HERE"`
- Only `ADMIN_TOKEN` is configured

**Location:**
- `backend/tests/full_system_invariant_test.py` lines 37-38

**Impact:**
- Tests requiring CREATOR or APPROVER roles will fail
- Cannot run full test suite

**Fix Required:**
- Generate tokens for CREATOR and APPROVER users
- Update test file with real tokens

---

### 4. Migration File vs Model Mismatch
**Severity:** MEDIUM  
**Status:** Code inconsistency

**Problem:**
- Model uses `Role.TextChoices` enum (correct)
- Migration `0001_initial.py` hardcodes choices list without ADMIN
- Migration `0002_add_admin_role.py` adds ADMIN via constraint update
- This creates confusion about when ADMIN was added

**Evidence:**
```python
# models.py - Uses TextChoices (correct)
class Role(models.TextChoices):
    ADMIN = "ADMIN"
    CREATOR = "CREATOR"
    ...

# migrations/0001_initial.py - Hardcoded list (outdated)
choices=[
    ("CREATOR", "Creator"),
    ("APPROVER", "Approver"),
    ("VIEWER", "Viewer"),
]
```

**Impact:**
- Code inconsistency
- Future developers may be confused
- Migration history doesn't match model evolution

**Fix Required:**
- Consider updating migration 0001 to include ADMIN (if recreating migrations)
- Or document that ADMIN was added in 0002

---

## 🟢 MEDIUM PRIORITY ISSUES

### 5. Missing Migration Record for Users App
**Severity:** MEDIUM  
**Status:** Database inconsistency

**Problem:**
- Users table exists and is functional
- Constraint includes ADMIN role
- But migrations are not recorded in `django_migrations`

**Evidence:**
```sql
-- Migration files exist:
backend/apps/users/migrations/0001_initial.py
backend/apps/users/migrations/0002_add_admin_role.py

-- But not recorded in database:
SELECT * FROM django_migrations WHERE app = 'users';
-- Returns: (0 rows)
```

**Impact:**
- Django thinks migrations haven't been applied
- Cannot track migration history
- May cause issues when adding new migrations

**Fix Required:**
- Insert migration records manually OR
- Use `--fake` flag to mark as applied

---

### 6. Role Enum Usage Inconsistency
**Severity:** LOW  
**Status:** Code quality

**Problem:**
- Model defines `Role.TextChoices` enum
- But code uses string literals `"ADMIN"` instead of `Role.ADMIN`
- Inconsistent usage pattern

**Evidence:**
```python
# models.py defines:
class Role(models.TextChoices):
    ADMIN = "ADMIN"
    ...

# But services use string literals:
if admin.role != "ADMIN":  # Should be Role.ADMIN
```

**Locations:**
- `backend/apps/ledger/services.py` (multiple instances)
- `backend/apps/payments/services.py` (multiple instances)
- `backend/apps/users/services.py`

**Impact:**
- Code maintainability
- Risk of typos
- Not leveraging enum benefits

**Fix Required:**
- Refactor to use `Role.ADMIN`, `Role.CREATOR`, etc.
- Or document why string literals are preferred

---

## 📋 SUMMARY

### Critical Blockers (Must Fix Immediately)
1. ✅ Migration state inconsistency (prevents backend startup)
2. ✅ Backend service not running

### High Priority (Fix Soon)
3. ⚠️ Test tokens not configured
4. ⚠️ Migration/model mismatch

### Medium/Low Priority (Nice to Have)
5. ⚠️ Missing migration records
6. ⚠️ Role enum usage inconsistency

---

## 🔧 RECOMMENDED FIX ORDER

1. **Fix migration state** (Issue #1)
   - Insert users migrations into django_migrations OR fake-apply them
   
2. **Restart backend** (Issue #2)
   - Verify service starts successfully
   
3. **Configure test tokens** (Issue #3)
   - Generate CREATOR and APPROVER tokens
   - Update test file
   
4. **Document/cleanup** (Issues #4, #5, #6)
   - Update migration comments
   - Consider refactoring role checks

---

## ✅ VERIFIED WORKING

- ✅ Database schema is correct (users table exists with ADMIN constraint)
- ✅ Model code uses Role.TextChoices correctly
- ✅ ADMIN role is functional (1 admin user exists in database)
- ✅ URL routing includes ledger endpoints
- ✅ JWT token lifetime extended to 24 hours
- ✅ System introspection script created

---

**Next Steps:**
1. Fix migration state to unblock backend startup
2. Verify backend starts successfully
3. Run full test suite
4. Address remaining issues in priority order
