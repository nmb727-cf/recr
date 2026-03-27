# QA Master Test Suite — Talent Operating System
# Version: 1.0 — Session 5
# Updated: March 20 2026
# Purpose: Complete test cases for every API endpoint, every user type, every edge case
# QA Agent must run ALL tests in this file before any code is merged

---

## HOW TO USE THIS FILE

Every session adds new test cases to this file.
QA agent runs the full file on every build.
Tests are grouped by module then by endpoint.
Each test has: Test ID, scenario, curl command, expected response, pass/fail criteria.

---

## TEST ENVIRONMENT SETUP

```bash
BASE_URL="http://127.0.0.1:8000"
CONTENT_TYPE="Content-Type: application/json"

# Run server before testing
cd /home/nirav/projects/SaaS_Project/backend
source ../venv/bin/activate
python3 manage.py runserver 0.0.0.0:8000
```

---

## MODULE 1: AUTHENTICATION

### ENDPOINT: POST /api/v1/auth/register/candidate/

#### TC-AUTH-001 — Happy Path: Valid registration
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "newuser@example.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 201
- `success: true`
- `data.user.email` = "newuser@example.com"
- `data.user.role` = "candidate"
- `data.access_token` exists and is a JWT string
- `data.refresh_token` exists and is a JWT string
- `data.user.email_verified` = false
- `data.user.id` is a valid UUID

---

#### TC-AUTH-002 — Duplicate email
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "newuser@example.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 400
- `success: false`
- `errors.email` contains "already exists"

---

#### TC-AUTH-003 — Missing required field: email
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "password": "TestPass123!"}'
```
**Expected:**
- Status: 400
- `success: false`
- `errors.email` exists

---

#### TC-AUTH-004 — Missing required field: password
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "another@example.com"}'
```
**Expected:**
- Status: 400
- `success: false`
- `errors.password` exists

---

#### TC-AUTH-005 — Weak password
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "weak@example.com", "password": "123"}'
```
**Expected:**
- Status: 400
- `success: false`
- `errors.password` contains password validation error

---

#### TC-AUTH-006 — Invalid email format
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "notanemail", "password": "TestPass123!"}'
```
**Expected:**
- Status: 400
- `success: false`
- `errors.email` exists

---

#### TC-AUTH-007 — Empty body
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{}'
```
**Expected:**
- Status: 400
- `success: false`
- Multiple field errors returned

---

#### TC-AUTH-008 — Email case insensitive (uppercase email should work)
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Test", "last_name": "User", "email": "CASE@EXAMPLE.COM", "password": "TestPass123!"}'
```
**Expected:**
- Status: 201
- `data.user.email` = "case@example.com" (lowercased)

---

### ENDPOINT: POST /api/v1/auth/register/company/

#### TC-AUTH-009 — Happy Path: Valid company registration
```bash
curl -X POST $BASE_URL/api/v1/auth/register/company/ \
  -H "$CONTENT_TYPE" \
  -d '{"name": "John Smith", "email": "john@acmecorp.com", "password": "TestPass123!", "company_name": "Acme Corp", "country_code": "IN"}'
```
**Expected:**
- Status: 201
- `success: true`
- `data.user.role` = "tenant_admin"
- `data.access_token` exists

---

#### TC-AUTH-010 — Missing company_name
```bash
curl -X POST $BASE_URL/api/v1/auth/register/company/ \
  -H "$CONTENT_TYPE" \
  -d '{"name": "John Smith", "email": "john2@acmecorp.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 400
- `errors.company_name` exists

---

### ENDPOINT: POST /api/v1/auth/register/agency/

#### TC-AUTH-011 — Happy Path: Valid agency registration
```bash
curl -X POST $BASE_URL/api/v1/auth/register/agency/ \
  -H "$CONTENT_TYPE" \
  -d '{"name": "Jane Doe", "email": "jane@bestagency.com", "password": "TestPass123!", "agency_name": "Best Agency", "country_code": "IN"}'
```
**Expected:**
- Status: 201
- `data.user.role` = "agency_owner"

---

### ENDPOINT: POST /api/v1/auth/login/

#### TC-AUTH-012 — Happy Path: Valid login
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 200
- `success: true`
- `data.access_token` exists
- `data.refresh_token` exists
- `data.user.last_login_at` is updated

---

#### TC-AUTH-013 — Wrong password
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "WrongPassword!"}'
```
**Expected:**
- Status: 401
- `success: false`
- `message` = "Invalid email or password."

---

#### TC-AUTH-014 — Non-existent email
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "ghost@example.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 401
- `success: false`
- `message` = "Invalid email or password."
- SECURITY: Same message as wrong password — no email enumeration

---

#### TC-AUTH-015 — Missing email
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"password": "TestPass123!"}'
```
**Expected:**
- Status: 400
- `errors.email` exists

---

#### TC-AUTH-016 — Empty password
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": ""}'
```
**Expected:**
- Status: 400
- `success: false`

---

#### TC-AUTH-017 — SQL injection attempt in email
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "test@example.com OR 1=1--", "password": "anything"}'
```
**Expected:**
- Status: 400 or 401
- No SQL error exposed
- No data leaked

---

#### TC-AUTH-018 — Login with uppercase email (should work)
```bash
curl -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "NEWUSER@EXAMPLE.COM", "password": "TestPass123!"}'
```
**Expected:**
- Status: 200
- Login succeeds (email is case insensitive)

---

### ENDPOINT: POST /api/v1/auth/refresh/

#### TC-AUTH-019 — Happy Path: Valid refresh token
```bash
# First login to get tokens
REFRESH=$(curl -s -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['refresh_token'])")

curl -X POST $BASE_URL/api/v1/auth/refresh/ \
  -H "$CONTENT_TYPE" \
  -d "{\"refresh_token\": \"$REFRESH\"}"
```
**Expected:**
- Status: 200
- New `access_token` returned
- New `refresh_token` returned (rotation)

---

#### TC-AUTH-020 — Invalid refresh token
```bash
curl -X POST $BASE_URL/api/v1/auth/refresh/ \
  -H "$CONTENT_TYPE" \
  -d '{"refresh_token": "thisisnotavalidtoken"}'
```
**Expected:**
- Status: 401
- `success: false`

---

### ENDPOINT: GET /api/v1/auth/me/

#### TC-AUTH-021 — Happy Path: Valid token
```bash
ACCESS=$(curl -s -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -X GET $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: Bearer $ACCESS"
```
**Expected:**
- Status: 200
- `data.user.email` = "newuser@example.com"
- Password hash NOT in response
- `mfa_secret` NOT in response

---

#### TC-AUTH-022 — No token provided
```bash
curl -X GET $BASE_URL/api/v1/auth/me/
```
**Expected:**
- Status: 401
- Authentication credentials not provided

---

#### TC-AUTH-023 — Expired/invalid token
```bash
curl -X GET $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.token"
```
**Expected:**
- Status: 401
- Token not valid

---

#### TC-AUTH-024 — Malformed Authorization header
```bash
curl -X GET $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: NotBearer sometoken"
```
**Expected:**
- Status: 401

---

### ENDPOINT: PUT /api/v1/auth/me/

#### TC-AUTH-025 — Happy Path: Update profile
```bash
ACCESS=$(curl -s -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -X PUT $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "Updated", "last_name": "Name", "phone": "+919876543210"}'
```
**Expected:**
- Status: 200
- `data.user.first_name` = "Updated"
- `data.user.phone` = "+919876543210"

---

#### TC-AUTH-026 — Cannot update email via PUT /me/
```bash
curl -X PUT $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"email": "hacker@evil.com"}'
```
**Expected:**
- Status: 200 but email unchanged
- OR Status: 400 if email field rejected
- SECURITY: email must not change

---

#### TC-AUTH-027 — Cannot update role via PUT /me/
```bash
curl -X PUT $BASE_URL/api/v1/auth/me/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"role": "super_admin"}'
```
**Expected:**
- Status: 200 but role unchanged
- SECURITY: role must not change via self-update

---

### ENDPOINT: POST /api/v1/auth/logout/

#### TC-AUTH-028 — Happy Path: Valid logout
```bash
TOKENS=$(curl -s -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}')

ACCESS=$(echo $TOKENS | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
REFRESH=$(echo $TOKENS | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['refresh_token'])")

curl -X POST $BASE_URL/api/v1/auth/logout/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d "{\"refresh_token\": \"$REFRESH\"}"
```
**Expected:**
- Status: 200
- `message` = "Logged out successfully."

---

#### TC-AUTH-029 — Refresh token blacklisted after logout
```bash
# After TC-AUTH-028, try to use the refresh token
curl -X POST $BASE_URL/api/v1/auth/refresh/ \
  -H "$CONTENT_TYPE" \
  -d "{\"refresh_token\": \"$REFRESH\"}"
```
**Expected:**
- Status: 401
- Token is blacklisted — cannot refresh after logout
- SECURITY CRITICAL: This must fail

---

#### TC-AUTH-030 — Logout without auth token
```bash
curl -X POST $BASE_URL/api/v1/auth/logout/ \
  -H "$CONTENT_TYPE" \
  -d '{"refresh_token": "sometoken"}'
```
**Expected:**
- Status: 401

---

### ENDPOINT: POST /api/v1/auth/change-password/

#### TC-AUTH-031 — Happy Path: Valid password change
```bash
ACCESS=$(curl -s -X POST $BASE_URL/api/v1/auth/login/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com", "password": "TestPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -X POST $BASE_URL/api/v1/auth/change-password/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"current_password": "TestPass123!", "new_password": "NewPass456!"}'
```
**Expected:**
- Status: 200
- Can login with new password
- Cannot login with old password

---

#### TC-AUTH-032 — Wrong current password
```bash
curl -X POST $BASE_URL/api/v1/auth/change-password/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"current_password": "WrongCurrent!", "new_password": "NewPass456!"}'
```
**Expected:**
- Status: 400
- `message` = "Current password is incorrect."

---

#### TC-AUTH-033 — New password same as current (weak check)
```bash
curl -X POST $BASE_URL/api/v1/auth/change-password/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "$CONTENT_TYPE" \
  -d '{"current_password": "NewPass456!", "new_password": "NewPass456!"}'
```
**Expected:**
- Status: 400 ideally (same password)
- OR Status: 200 (acceptable but not ideal)
- NOTE: Add same-password check in future

---

### ENDPOINT: POST /api/v1/auth/forgot-password/

#### TC-AUTH-034 — Existing email
```bash
curl -X POST $BASE_URL/api/v1/auth/forgot-password/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "newuser@example.com"}'
```
**Expected:**
- Status: 200
- Generic success message (no indication if email exists)

---

#### TC-AUTH-035 — Non-existent email
```bash
curl -X POST $BASE_URL/api/v1/auth/forgot-password/ \
  -H "$CONTENT_TYPE" \
  -d '{"email": "ghost@nowhere.com"}'
```
**Expected:**
- Status: 200
- SAME message as TC-AUTH-034
- SECURITY: Must not reveal if email exists

---

---

## SECURITY TEST SUITE

### SEC-001 — Rate limiting on login (brute force protection)
```bash
for i in {1..20}; do
  curl -s -X POST $BASE_URL/api/v1/auth/login/ \
    -H "$CONTENT_TYPE" \
    -d '{"email": "newuser@example.com", "password": "WrongPass!"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))"
done
```
**Expected:**
- After multiple failures, Status: 429 Too Many Requests
- NOTE: Rate limiting not yet implemented — add to backlog

---

### SEC-002 — JWT token cannot be used after expiry
**Expected:**
- Access token expires after 15 minutes (per SIMPLE_JWT config)
- Expired token returns 401

---

### SEC-003 — Sensitive fields never in response
Check these fields are NEVER returned in any API response:
- `password`
- `password_hash`
- `mfa_secret`
- `refresh_token_hash`

---

### SEC-004 — CORS headers
```bash
curl -X OPTIONS $BASE_URL/api/v1/auth/login/ \
  -H "Origin: http://evil.com" \
  -v 2>&1 | grep -i "access-control"
```
**Expected:**
- CORS not allowing all origins in production
- NOTE: Configure CORS properly before deployment

---

### SEC-005 — XSS in input fields
```bash
curl -X POST $BASE_URL/api/v1/auth/register/candidate/ \
  -H "$CONTENT_TYPE" \
  -d '{"first_name": "<script>alert(1)</script>", "last_name": "User", "email": "xss@example.com", "password": "TestPass123!"}'
```
**Expected:**
- Status: 201 (registration succeeds)
- `data.user.first_name` stored as-is (sanitize on output, not input)
- Script tag NOT executed in API response

---

---

## REGRESSION CHECKLIST

Run before every deployment:

| Test ID | Endpoint | Result |
|---------|----------|--------|
| TC-AUTH-001 | Register candidate | |
| TC-AUTH-002 | Duplicate email rejected | |
| TC-AUTH-012 | Login success | |
| TC-AUTH-013 | Wrong password rejected | |
| TC-AUTH-014 | Non-existent email — no enumeration | |
| TC-AUTH-019 | Token refresh works | |
| TC-AUTH-021 | Get profile with valid token | |
| TC-AUTH-022 | No token rejected | |
| TC-AUTH-028 | Logout works | |
| TC-AUTH-029 | Token blacklisted after logout | |
| TC-AUTH-031 | Password change works | |
| SEC-003 | Sensitive fields not in response | |

---

## BACKLOG — Tests to Add Next Session

- Organisation endpoints (departments, locations, teams)
- Multi-tenant isolation tests (tenant A cannot see tenant B data)
- Job endpoints
- Candidate endpoints
- Pipeline endpoints
- Agency endpoints
- Rate limiting once implemented
- Email verification flow once implemented

---

## QA NOTES

- All tests assume public tenant exists with localhost and 127.0.0.1 domains
- Reset test data between full test runs if needed
- Token expiry is 15 minutes — run time-sensitive tests quickly
- Password reset and email verify endpoints are stubbed (TODO) — test will pass with any token for now
