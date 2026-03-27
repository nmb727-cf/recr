# Broken Flows

## Authentication Login/Register
Status: FIXED
UI Found: src/pages/auth/
API Found: src/api/auth.ts (calls /auth/)
Backend Found: apps/accounts/urls.py (exposes /accounts/)
Issues: Route prefix mismatch will cause 404s.
Risk: HIGH

## Organization Management
Status: FIXED
UI Found: None / Minimal
API Found: src/api/organisation.ts (calls /organisation/)
Backend Found: apps/organisations/urls.py (exposes /organisations/)
Issues: Mismatched pluralization.
Risk: HIGH
