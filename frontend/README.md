# Internal Payment Workflow System - Frontend

Frontend implementation for the Internal Payment Workflow System (MVP v1).

## Technology Stack

- React 18.2.0
- React Router DOM 6.28.0
- Axios 1.7.7
- Vite 5.4.10

## Architecture Principles

This frontend strictly follows the frozen specifications:

1. **No business logic** - All validation and state transitions occur server-side
2. **No client-side state transitions** - UI displays server state only
3. **State-based visibility** - Buttons disabled based on backend state flags only
4. **Standardized error handling** - All errors follow API contract format
5. **Token handling** - Follows SECURITY_MODEL.md specifications

## Setup

1. Install dependencies:
```bash
npm ci
```

2. Create `.env` file (optional):
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Routes

- `/login` - Login screen (unauthenticated only)
- `/` - Home (redirects based on role)
- `/batches` - Batches list
- `/batches/new` - Create batch (CREATOR only)
- `/batches/:batchId` - Batch detail
- `/batches/:batchId/requests/:requestId` - Request detail (from batch context)
- `/requests` - Pending requests list (APPROVER only)
- `/requests/:requestId` - Request detail (from approval queue, APPROVER only)
- `/audit` - Audit log

## Implementation Notes

- All API calls use the standardized error format
- Token is stored in localStorage
- 401 errors trigger automatic redirect to login
- 409 CONFLICT errors trigger data reload
- Button visibility is determined by state visibility utility functions
- No role-based logic is hardcoded - all permissions come from backend
