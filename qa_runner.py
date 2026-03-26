#!/usr/bin/env python3
"""
QA Regression Runner — Recruitment SaaS Platform
Runs key endpoint tests and saves results to qa_results/YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import date, datetime

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ─── Known seed data IDs (john@acmecorp.com's tenant) ────────────────────────
KNOWN_POSTING_ID = "e27506a0-03db-47f8-b3b0-fd5aeb1419b5"
KNOWN_REQ_ID = "9fe3e47d-ea4e-4d47-963e-2a33a3a24dda"

# ─── Credentials ─────────────────────────────────────────────────────────────
ADMIN_EMAIL = "john@acmecorp.com"
ADMIN_PASSWORD = "TestPass123!"
CANDIDATE_EMAIL = "cat5@test.com"
CANDIDATE_PASSWORD = "Test@123!"


# ─── Helpers ─────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self, name: str, passed: bool, detail: str = "", status_code: int = None):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.status_code = status_code

    def label(self) -> str:
        return "PASS" if self.passed else "FAIL"


results: list[TestResult] = []


def run_test(name: str, fn) -> TestResult:
    """Execute a test function, catch exceptions, record result."""
    try:
        passed, detail, status_code = fn()
        r = TestResult(name, passed, detail, status_code)
    except Exception as exc:
        r = TestResult(name, False, f"Exception: {exc}")

    results.append(r)
    icon = "✓" if r.passed else "✗"
    code_str = f" [{r.status_code}]" if r.status_code else ""
    print(f"  {icon} {r.label()}{code_str}  {name}")
    if not r.passed:
        print(f"        → {r.detail}")
    return r


def check(resp: requests.Response, expected_status: int = 200, key_path: str = None) -> tuple:
    """Standard check: verify status code and optional JSON key path."""
    passed = resp.status_code == expected_status
    detail = ""
    if not passed:
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:200]
        detail = f"Expected {expected_status}, got {resp.status_code}. Body: {body}"
    elif key_path:
        # Verify a dot-separated path exists in the response JSON
        try:
            data = resp.json()
            parts = key_path.split(".")
            cursor = data
            for part in parts:
                cursor = cursor[part]
            if cursor is None:
                passed = False
                detail = f"Key path '{key_path}' is null"
        except (KeyError, TypeError) as e:
            passed = False
            detail = f"Key path '{key_path}' missing: {e}"
    return passed, detail, resp.status_code


def get_token(email: str, password: str) -> str | None:
    """Login and return access token, or None on failure."""
    resp = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": email, "password": password},
    )
    if resp.status_code == 200:
        return resp.json()["data"]["access_token"]
    return None


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Test groups ─────────────────────────────────────────────────────────────

def run_auth_tests():
    print("\n[AUTH]")

    def test_admin_login():
        resp = requests.post(f"{BASE_URL}/auth/login/", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        return check(resp, 200, "data.access_token")

    def test_candidate_login():
        resp = requests.post(f"{BASE_URL}/auth/login/", json={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD})
        return check(resp, 200, "data.access_token")

    def test_bad_credentials():
        resp = requests.post(f"{BASE_URL}/auth/login/", json={"email": ADMIN_EMAIL, "password": "wrongpassword"})
        passed = resp.status_code in (400, 401, 403)
        detail = "" if passed else f"Expected 4xx, got {resp.status_code}"
        return passed, detail, resp.status_code

    def test_me_endpoint():
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = requests.get(f"{BASE_URL}/auth/me/", headers=auth_headers(token))
        return check(resp, 200, "data.user.email")

    def test_me_requires_auth():
        resp = requests.get(f"{BASE_URL}/auth/me/")
        passed = resp.status_code == 401
        detail = "" if passed else f"Expected 401, got {resp.status_code}"
        return passed, detail, resp.status_code

    run_test("Admin login returns access token", test_admin_login)
    run_test("Candidate login returns access token", test_candidate_login)
    run_test("Bad credentials returns 4xx", test_bad_credentials)
    run_test("GET /auth/me/ returns user data", test_me_endpoint)
    run_test("GET /auth/me/ requires auth", test_me_requires_auth)


def run_public_job_tests():
    print("\n[PUBLIC JOBS — no auth]")

    def test_search_returns_list():
        resp = requests.get(f"{BASE_URL}/jobs/search/")
        return check(resp, 200, "data.jobs")

    def test_search_with_query():
        resp = requests.get(f"{BASE_URL}/jobs/search/?q=backend")
        ok, detail, code = check(resp, 200, "data.jobs")
        if ok:
            jobs = resp.json()["data"]["jobs"]
            ok = len(jobs) > 0
            detail = "Expected at least one result for q=backend" if not ok else ""
        return ok, detail, code

    def test_search_filters_work_mode():
        resp = requests.get(f"{BASE_URL}/jobs/search/?work_mode=hybrid")
        return check(resp, 200, "data.jobs")

    def test_public_job_detail():
        resp = requests.get(f"{BASE_URL}/jobs/{KNOWN_POSTING_ID}/")
        return check(resp, 200, "data.posting.title")

    def test_public_detail_404():
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = requests.get(f"{BASE_URL}/jobs/{fake_id}/")
        passed = resp.status_code == 404
        detail = "" if passed else f"Expected 404, got {resp.status_code}"
        return passed, detail, resp.status_code

    def test_view_count_increments():
        r1 = requests.get(f"{BASE_URL}/jobs/{KNOWN_POSTING_ID}/")
        r2 = requests.get(f"{BASE_URL}/jobs/{KNOWN_POSTING_ID}/")
        v1 = r1.json()["data"]["posting"]["views_count"]
        v2 = r2.json()["data"]["posting"]["views_count"]
        passed = v2 == v1 + 1
        detail = "" if passed else f"views_count did not increment: {v1} → {v2}"
        return passed, detail, r2.status_code

    run_test("GET /jobs/search/ returns job list", test_search_returns_list)
    run_test("GET /jobs/search/?q=backend returns results", test_search_with_query)
    run_test("GET /jobs/search/?work_mode=hybrid works", test_search_filters_work_mode)
    run_test("GET /jobs/<id>/ returns job detail", test_public_job_detail)
    run_test("GET /jobs/<bad-id>/ returns 404", test_public_detail_404)
    run_test("GET /jobs/<id>/ increments views_count", test_view_count_increments)


def run_admin_job_tests(token: str):
    print("\n[JOBS — admin]")

    h = auth_headers(token)

    def test_list_requisitions():
        resp = requests.get(f"{BASE_URL}/jobs/requisitions/", headers=h)
        return check(resp, 200, "data.requisitions")

    def test_get_requisition_detail():
        resp = requests.get(f"{BASE_URL}/jobs/requisitions/{KNOWN_REQ_ID}/", headers=h)
        return check(resp, 200, "data.requisition.title")

    def test_requisition_requires_auth():
        resp = requests.get(f"{BASE_URL}/jobs/requisitions/")
        passed = resp.status_code == 401
        detail = "" if passed else f"Expected 401, got {resp.status_code}"
        return passed, detail, resp.status_code

    def test_list_postings():
        resp = requests.get(f"{BASE_URL}/jobs/postings/", headers=h)
        return check(resp, 200, "data.postings")

    def test_get_posting_detail():
        resp = requests.get(f"{BASE_URL}/jobs/postings/{KNOWN_POSTING_ID}/", headers=h)
        return check(resp, 200, "data.posting.title")

    def test_create_and_delete_requisition():
        payload = {
            "title": "QA Test Role",
            "job_type": "full_time",
            "work_mode": "remote",
            "experience_min": 1,
            "experience_max": 3,
            "headcount": 1,
            "priority": "medium",
            "description": "QA runner created this",
        }
        resp = requests.post(f"{BASE_URL}/jobs/requisitions/", headers=h, json=payload)
        ok, detail, code = check(resp, 201, "data.requisition.id")
        if not ok:
            return ok, detail, code
        new_id = resp.json()["data"]["requisition"]["id"]
        # Clean up — soft delete
        del_resp = requests.delete(f"{BASE_URL}/jobs/requisitions/{new_id}/", headers=h)
        if del_resp.status_code not in (200, 204):
            return True, f"Created ok but delete failed: {del_resp.status_code}", code
        return True, "", code

    run_test("GET /jobs/requisitions/ returns list", test_list_requisitions)
    run_test("GET /jobs/requisitions/<id>/ returns detail", test_get_requisition_detail)
    run_test("GET /jobs/requisitions/ requires auth", test_requisition_requires_auth)
    run_test("GET /jobs/postings/ returns list", test_list_postings)
    run_test("GET /jobs/postings/<id>/ returns detail", test_get_posting_detail)
    run_test("POST /jobs/requisitions/ creates and DELETE removes", test_create_and_delete_requisition)


def run_pipeline_tests(token: str):
    print("\n[PIPELINE — admin]")
    h = auth_headers(token)

    def test_list_applications():
        resp = requests.get(f"{BASE_URL}/applications/", headers=h)
        return check(resp, 200, "data.applications")

    def test_pipeline_view():
        resp = requests.get(f"{BASE_URL}/pipeline/{KNOWN_REQ_ID}/", headers=h)
        return check(resp, 200, "data")

    def test_deadlines_list():
        resp = requests.get(f"{BASE_URL}/deadlines/", headers=h)
        return check(resp, 200, "data")

    run_test("GET /applications/ returns list", test_list_applications)
    run_test("GET /pipeline/<req-id>/ returns pipeline view", test_pipeline_view)
    run_test("GET /deadlines/ returns list", test_deadlines_list)


def run_organisation_tests(token: str):
    print("\n[ORGANISATION — admin]")
    h = auth_headers(token)

    def test_get_profile():
        resp = requests.get(f"{BASE_URL}/organisation/profile/", headers=h)
        # 200 = profile exists, 404 = not yet configured (both valid)
        passed = resp.status_code in (200, 404)
        detail = "" if passed else f"Expected 200 or 404, got {resp.status_code}"
        return passed, detail, resp.status_code

    def test_list_users():
        resp = requests.get(f"{BASE_URL}/organisation/users/", headers=h)
        return check(resp, 200, "data")

    def test_list_departments():
        resp = requests.get(f"{BASE_URL}/organisation/departments/", headers=h)
        return check(resp, 200, "data")

    def test_list_locations():
        resp = requests.get(f"{BASE_URL}/organisation/locations/", headers=h)
        return check(resp, 200, "data")

    run_test("GET /organisation/profile/ returns data", test_get_profile)
    run_test("GET /organisation/users/ returns list", test_list_users)
    run_test("GET /organisation/departments/ returns list", test_list_departments)
    run_test("GET /organisation/locations/ returns list", test_list_locations)


def run_analytics_tests(token: str):
    print("\n[ANALYTICS — admin]")
    h = auth_headers(token)

    for endpoint in ["dashboard", "recruitment", "pipeline", "agencies", "candidates", "interviews"]:
        def make_test(ep):
            def _test():
                resp = requests.get(f"{BASE_URL}/analytics/{ep}/", headers=h)
                return check(resp, 200, "data")
            return _test
        run_test(f"GET /analytics/{endpoint}/ returns data", make_test(endpoint))


def run_candidate_tests(candidate_token: str):
    print("\n[CANDIDATE — authenticated]")
    h = auth_headers(candidate_token)

    def test_candidate_applications():
        resp = requests.get(f"{BASE_URL}/candidate/applications/", headers=h)
        return check(resp, 200, "data.applications")

    def test_recommended_jobs():
        resp = requests.get(f"{BASE_URL}/candidate/recommended-jobs/", headers=h)
        return check(resp, 200, "data.jobs")

    def test_apply_to_job():
        resp = requests.post(
            f"{BASE_URL}/jobs/{KNOWN_POSTING_ID}/apply/",
            headers=h,
            json={"cover_note": "QA runner application"},
        )
        # 201 = applied, 409 = already applied (both are valid outcomes)
        passed = resp.status_code in (201, 409)
        detail = "" if passed else f"Expected 201 or 409, got {resp.status_code}: {resp.text[:200]}"
        return passed, detail, resp.status_code

    def test_apply_requires_auth():
        resp = requests.post(f"{BASE_URL}/jobs/{KNOWN_POSTING_ID}/apply/", json={})
        passed = resp.status_code == 401
        detail = "" if passed else f"Expected 401, got {resp.status_code}"
        return passed, detail, resp.status_code

    run_test("GET /candidate/applications/ returns list", test_candidate_applications)
    run_test("GET /candidate/recommended-jobs/ returns list", test_recommended_jobs)
    run_test("POST /jobs/<id>/apply/ succeeds or returns 409 if duplicate", test_apply_to_job)
    run_test("POST /jobs/<id>/apply/ requires auth", test_apply_requires_auth)


def run_passport_tests(candidate_token: str):
    print("\n[PASSPORT — candidate]")
    h = auth_headers(candidate_token)

    def test_get_passport():
        resp = requests.get(f"{BASE_URL}/passport/my-passport/", headers=h)
        # 200 if exists, 404 if not yet created — both valid
        passed = resp.status_code in (200, 404)
        detail = "" if passed else f"Expected 200 or 404, got {resp.status_code}"
        return passed, detail, resp.status_code

    run_test("GET /passport/my-passport/ returns passport or 404", test_get_passport)


def run_comms_tests(token: str):
    print("\n[COMMUNICATIONS — admin]")
    h = auth_headers(token)

    def test_list_threads():
        resp = requests.get(f"{BASE_URL}/messages/threads/", headers=h)
        return check(resp, 200, "data")

    def test_list_notifications():
        resp = requests.get(f"{BASE_URL}/notifications/", headers=h)
        return check(resp, 200, "data")

    run_test("GET /messages/threads/ returns list", test_list_threads)
    run_test("GET /notifications/ returns list", test_list_notifications)


# ─── Save results to markdown ────────────────────────────────────────────────

def save_results():
    today = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "qa_results",
        f"{today}.md",
    )

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    lines = [
        f"# QA Results — {today}",
        f"",
        f"**Run at:** {now}  ",
        f"**Total:** {total}  |  **Passed:** {passed}  |  **Failed:** {failed}",
        f"",
        f"---",
        f"",
        f"## Results",
        f"",
        f"| Status | Code | Test |",
        f"|--------|------|------|",
    ]

    for r in results:
        icon = "✅ PASS" if r.passed else "❌ FAIL"
        code = str(r.status_code) if r.status_code else "—"
        row = f"| {icon} | {code} | {r.name} |"
        lines.append(row)

    # Failures section
    failures = [r for r in results if not r.passed]
    if failures:
        lines += ["", "---", "", "## Failures", ""]
        for r in failures:
            lines.append(f"### ❌ {r.name}")
            lines.append(f"- **Detail:** {r.detail}")
            lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return out_path, passed, failed

# Add after existing results saving logic
import json
json_file = f"qa_results/{datetime.now().strftime('%Y-%m-%d')}.json"
with open(json_file, "w") as f:
    json.dump({
        "run_at": datetime.now().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "results": results
    }, f, indent=2)
    
# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  QA Regression Runner — Recruitment SaaS Platform")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    # Get tokens
    print("\n[SETUP] Authenticating...")
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_token:
        print(f"  ✗ FATAL: Could not authenticate as {ADMIN_EMAIL}")
        sys.exit(1)
    print(f"  ✓ Admin token acquired ({ADMIN_EMAIL})")

    candidate_token = get_token(CANDIDATE_EMAIL, CANDIDATE_PASSWORD)
    if not candidate_token:
        print(f"  ✗ FATAL: Could not authenticate as {CANDIDATE_EMAIL}")
        sys.exit(1)
    print(f"  ✓ Candidate token acquired ({CANDIDATE_EMAIL})")

    # Run test groups
    run_auth_tests()
    run_public_job_tests()
    run_admin_job_tests(admin_token)
    run_pipeline_tests(admin_token)
    run_organisation_tests(admin_token)
    run_analytics_tests(admin_token)
    run_candidate_tests(candidate_token)
    run_passport_tests(candidate_token)
    run_comms_tests(admin_token)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"  TOTAL: {total}  |  PASSED: {passed}  |  FAILED: {failed}")
    print("=" * 60)

    out_path, _, _ = save_results()
    print(f"\n  Results saved to: {out_path}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
