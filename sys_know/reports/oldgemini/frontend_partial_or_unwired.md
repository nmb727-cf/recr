# Confirmed Frontend-Only or Unwired Areas

## Authentication Path Mismatch
- **Frontend**: Expects `/auth/*` (e.g., `/auth/login/`)
- **Backend**: Exposes `/accounts/*` (e.g., `/accounts/login/`)
- **Impact**: Without proxy rewrites, all auth is broken.

## Organisation vs Organisations
- **Frontend**: `api/organisation.ts` calls `/organisation/profile/`, `/organisation/users/`
- **Backend**: Exposes `/organisations/profile/`, `/organisations/users/`
- **Impact**: 404 Not Found on all org management pages.

## Pipeline vs Applications Prefix
- **Frontend**: calls `/applications/` directly for standard pipeline stages.
- **Backend**: Exposes `/pipeline/applications/`
- **Impact**: 404 Not Found on pipeline drag-and-drop and stage moving.

## Messages & Notifications Prefix
- **Frontend**: calls `/messages/threads/` and `/notifications/`
- **Backend**: Exposes `/communications/messages/threads/` and `/communications/notifications/`
- **Impact**: In-app chat and notifications will fail.
