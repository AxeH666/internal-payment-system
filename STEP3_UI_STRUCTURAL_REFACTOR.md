# STEP 3 — UI Structural Refactor

**Phase 2 Controlled Execution Plan — Verification Artifact**

**Date:** 2025-02-20

---

## 1. Route config and layout

**Route config file:** [frontend/src/config/routes.js](frontend/src/config/routes.js)

- Single array `routeConfig` with entries: `{ path, allowedRoles?, component }`.
- Paths: `/`, `/batches`, `/batches/new`, `/batches/:batchId`, `/batches/:batchId/requests/:requestId`, `/requests`, `/requests/:requestId`, `/audit`.
- allowedRoles match previous App.jsx: same arrays for each path (null for Home).

**Layout file:** [frontend/src/components/AppLayout.jsx](frontend/src/components/AppLayout.jsx)

- Renders header: “Welcome, {displayName} ({role})” and Logout button.
- Renders `<Outlet />` for child route content.
- Uses `getCurrentUser` and `logout` from auth; no new permission logic.

---

## 2. Files changed

| File | Change |
|------|--------|
| frontend/src/config/routes.js | **Added.** Centralized route config. |
| frontend/src/components/AppLayout.jsx | **Added.** Shared layout with header + Outlet. |
| frontend/src/App.jsx | **Modified.** Uses routeConfig; protected routes (except Home) wrapped in AppLayout; routes generated from config. |
| frontend/src/pages/BatchesList.jsx | **Modified.** Removed header div (Welcome, Logout) and handleLogout; kept page content and user state for “Create Batch” visibility. |
| frontend/src/pages/PendingRequestsList.jsx | **Modified.** Removed header div and handleLogout; kept user state. |
| frontend/src/pages/AuditLog.jsx | **Modified.** Removed header div and handleLogout; kept user state and filters. |

BatchDetail, RequestDetail, RequestDetailApprovalQueue, CreateBatch: no layout chrome removed (they did not have the duplicated header). stateVisibility.js unchanged.

---

## 3. Paths and allowedRoles unchanged

- Path set: `/`, `/login`, `/batches`, `/batches/new`, `/batches/:batchId`, `/batches/:batchId/requests/:requestId`, `/requests`, `/requests/:requestId`, `/audit`, `*`.
- allowedRoles per route match original App.jsx (e.g. BatchesList: CREATOR, APPROVER, VIEWER, ADMIN; CreateBatch: CREATOR, ADMIN; etc.).

---

## 4. Behavior check

- **Build:** `npm run build` (frontend) completed successfully (exit 0).
- **No backend changes.** No new UI-driven permission logic; RoleBasedRoute and ProtectedRoute behavior unchanged.
- **Layout:** One shared layout (AppLayout) used for all protected routes except Home; Home remains ProtectedRoute-only with no layout chrome.
- **Login and catch-all:** Login at `/login` and `*` → Navigate to `/` unchanged.

---

## 5. Final declaration

**PASS**

All routes defined in one config. One layout (AppLayout) used for protected routes. No route path or allowedRoles changed. No backend change. Existing behavior preserved (build succeeds). Artifact complete.
