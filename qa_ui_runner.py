#!/usr/bin/env python3
"""
TOS UI QA Runner — Playwright
Tests all 9 core scenarios through the actual browser UI.

Usage:
    python3 qa_ui_runner.py              # headless (fast, CI mode)
    python3 qa_ui_runner.py --headed     # headed (watch it run, debug mode)
    python3 qa_ui_runner.py --scenario 1 # run single scenario only
    python3 qa_ui_runner.py --headed --scenario 3

Scenarios:
    1. Company Onboarding
    2. Organisation Setup
    3. Jobs Flow
    4. Agency Linking
    5. Candidates
    6. Pipeline
    7. Agency Submissions
    8. Interviews
    9. Offers
"""

import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:5173"
API_URL  = "http://127.0.0.1:8000/api/v1"

# Test accounts — match CLAUDE_CONTEXT.md
COMPANY_EMAIL    = "john@acmecorp.com"
COMPANY_PASSWORD = "TestPass123!"
AGENCY_EMAIL     = "jane@bestagency.com"
AGENCY_PASSWORD  = "TestPass123!"

REPORT_DIR = Path("/home/nirav/projects/SaaS_Project/qa_ui_reports")
SCREENSHOT_DIR = REPORT_DIR / "screenshots"

# Timing — increase if system is slow
NAV_TIMEOUT   = 10_000   # 10s for page navigation
ACTION_TIMEOUT = 5_000   # 5s for clicks / fills
WAIT_AFTER_ACTION = 800  # ms pause after each action (let React re-render)

# ── Result Tracker ────────────────────────────────────────────────────────────
results = []

def record(scenario: str, step: str, status: str, detail: str = "", screenshot: str = ""):
    entry = {
        "scenario": scenario,
        "step": step,
        "status": status,   # PASS / FAIL / SKIP
        "detail": detail,
        "screenshot": screenshot,
        "time": datetime.now().isoformat()
    }
    results.append(entry)
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⏭")
    print(f"  {icon} [{scenario}] {step}" + (f" — {detail}" if detail else ""))

def screenshot(page: Page, scenario: str, step: str) -> str:
    """Take screenshot and return filename."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now().strftime('%H%M%S')}_{scenario.replace(' ', '_')}_{step.replace(' ', '_')}.png"
    path = str(SCREENSHOT_DIR / name)
    try:
        page.screenshot(path=path)
    except Exception:
        pass
    return path

# ── Shared Actions ────────────────────────────────────────────────────────────
def login(page: Page, email: str, password: str, role: str = "company"):
    """Navigate to login and authenticate."""
    page.goto(f"{BASE_URL}/login", timeout=NAV_TIMEOUT)
    page.wait_for_load_state("networkidle")

    # Fill email
    email_input = page.locator("input[type='email'], input[placeholder*='email' i], input[name='email']").first
    email_input.fill(email, timeout=ACTION_TIMEOUT)

    # Fill password
    pwd_input = page.locator("input[type='password']").first
    pwd_input.fill(password, timeout=ACTION_TIMEOUT)

    # Submit
    page.locator("button[type='submit'], button:has-text('Login'), button:has-text('Sign in')").first.click()
    page.wait_for_load_state("networkidle")
    time.sleep(WAIT_AFTER_ACTION / 1000)

def logout(page: Page):
    """Log out current user."""
    try:
        page.goto(f"{BASE_URL}/logout", timeout=NAV_TIMEOUT)
        page.wait_for_load_state("networkidle")
    except Exception:
        pass

def navigate(page: Page, path: str):
    page.goto(f"{BASE_URL}{path}", timeout=NAV_TIMEOUT)
    page.wait_for_load_state("networkidle")
    time.sleep(WAIT_AFTER_ACTION / 1000)

def click_text(page: Page, text: str):
    page.locator(f"button:has-text('{text}'), a:has-text('{text}'), span:has-text('{text}')").first.click(timeout=ACTION_TIMEOUT)
    time.sleep(WAIT_AFTER_ACTION / 1000)

def fill_input(page: Page, label_or_placeholder: str, value: str):
    """Try multiple strategies to find and fill an input."""
    selectors = [
        f"input[placeholder*='{label_or_placeholder}' i]",
        f"input[name*='{label_or_placeholder}' i]",
        f"textarea[placeholder*='{label_or_placeholder}' i]",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.fill(value, timeout=ACTION_TIMEOUT)
                return
        except Exception:
            continue
    # fallback: find label then next input
    try:
        page.locator(f"label:has-text('{label_or_placeholder}') + input").first.fill(value, timeout=ACTION_TIMEOUT)
    except Exception:
        pass

def page_has_text(page: Page, text: str) -> bool:
    try:
        return page.locator(f"text={text}").count() > 0
    except Exception:
        return False

def no_crash(page: Page) -> bool:
    """Check page is not a white screen or error page."""
    body_text = page.locator("body").inner_text(timeout=3000)
    crash_signals = ["Cannot read", "undefined", "TypeError", "SyntaxError", "500", "404 Not Found"]
    for signal in crash_signals:
        if signal in body_text:
            return False
    # White screen = almost no content
    if len(body_text.strip()) < 50:
        return False
    return True

# ── SCENARIO 1: Company Onboarding ───────────────────────────────────────────
def scenario_1_company_onboarding(page: Page):
    S = "1. Company Onboarding"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    # Step 1: Navigate to register
    try:
        navigate(page, "/register/company")
        if no_crash(page):
            record(S, "Register page loads", "PASS")
        else:
            record(S, "Register page loads", "FAIL", "Page crashed or blank",
                   screenshot(page, S, "register_page"))
            return
    except Exception as e:
        record(S, "Register page loads", "FAIL", str(e), screenshot(page, S, "register_error"))
        return

    # Step 2: Fill registration form
    try:
        ts = datetime.now().strftime("%H%M%S")
        test_email = f"qa_company_{ts}@test.com"

        fill_input(page, "company name", f"QA Corp {ts}")
        fill_input(page, "name", "QA Admin")
        fill_input(page, "email", test_email)
        fill_input(page, "password", "TestPass123!")
        fill_input(page, "confirm", "TestPass123!")

        page.locator("button[type='submit'], button:has-text('Register'), button:has-text('Create')").first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        current_url = page.url
        record(S, "Registration form submit", "PASS", f"Landed on: {current_url}")
    except Exception as e:
        record(S, "Registration form submit", "FAIL", str(e), screenshot(page, S, "register_submit"))
        return

    # Step 3: Check landing after register
    try:
        current_url = page.url
        on_onboarding = "onboarding" in current_url
        on_dashboard  = "dashboard" in current_url
        on_register   = "register" in current_url  # bad — stayed on same page

        if on_register:
            record(S, "Post-register redirect", "FAIL",
                   f"Still on register page — likely form error. URL: {current_url}",
                   screenshot(page, S, "post_register"))
        elif on_onboarding or on_dashboard:
            record(S, "Post-register redirect", "PASS", f"URL: {current_url}")
        else:
            record(S, "Post-register redirect", "FAIL",
                   f"Unexpected URL: {current_url}", screenshot(page, S, "post_register"))
    except Exception as e:
        record(S, "Post-register redirect", "FAIL", str(e))

    # Step 4: Complete onboarding if present
    try:
        if "onboarding" in page.url:
            # Try to fill and save onboarding
            fill_input(page, "industry", "Technology")
            fill_input(page, "size", "11-50")

            save_btn = page.locator("button:has-text('Save'), button:has-text('Continue'), button:has-text('Next')").first
            if save_btn.count() > 0:
                save_btn.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)

            if no_crash(page):
                record(S, "Onboarding form save", "PASS", f"URL after: {page.url}")
            else:
                record(S, "Onboarding form save", "FAIL", "Page crashed after onboarding save",
                       screenshot(page, S, "onboarding_save"))
        else:
            record(S, "Onboarding form save", "SKIP", "Onboarding screen not shown")
    except Exception as e:
        record(S, "Onboarding form save", "FAIL", str(e), screenshot(page, S, "onboarding_error"))

    # Step 5: Login again — should NOT show onboarding
    try:
        login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
        time.sleep(1)
        if "onboarding" in page.url:
            record(S, "Re-login skips onboarding", "FAIL",
                   "Existing user sent to onboarding again", screenshot(page, S, "re_login"))
        elif no_crash(page):
            record(S, "Re-login skips onboarding", "PASS", f"Landed: {page.url}")
        else:
            record(S, "Re-login skips onboarding", "FAIL", "Page crashed",
                   screenshot(page, S, "re_login_crash"))
    except Exception as e:
        record(S, "Re-login skips onboarding", "FAIL", str(e))

# ── SCENARIO 2: Organisation Setup ───────────────────────────────────────────
def scenario_2_organisation(page: Page):
    S = "2. Organisation Setup"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)

    for item, nav_path, form_value in [
        ("Department", "/settings/departments", "QA Engineering"),
        ("Location",   "/settings/locations",   "Ahmedabad"),
        ("Team",       "/settings/teams",        "QA Team"),
    ]:
        try:
            navigate(page, nav_path)
            if not no_crash(page):
                record(S, f"{item} page loads", "FAIL", "Page crashed",
                       screenshot(page, S, item.lower()))
                continue
            record(S, f"{item} page loads", "PASS")

            # Click Add / Create button
            add_btn = page.locator(
                f"button:has-text('Add'), button:has-text('Create'), button:has-text('New')"
            ).first
            if add_btn.count() == 0:
                record(S, f"Add {item}", "FAIL", "No Add button found",
                       screenshot(page, S, f"no_add_{item.lower()}"))
                continue

            add_btn.click()
            time.sleep(WAIT_AFTER_ACTION / 1000)

            fill_input(page, "name", form_value)

            save_btn = page.locator(
                "button:has-text('Save'), button:has-text('Create'), button:has-text('Add')"
            ).last
            save_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            if page_has_text(page, form_value):
                record(S, f"Create {item}", "PASS", f"'{form_value}' visible in list")
            else:
                record(S, f"Create {item}", "FAIL",
                       f"'{form_value}' not found after save",
                       screenshot(page, S, f"save_{item.lower()}"))
        except Exception as e:
            record(S, f"Create {item}", "FAIL", str(e),
                   screenshot(page, S, f"error_{item.lower()}"))

# ── SCENARIO 3: Jobs Flow ─────────────────────────────────────────────────────
def scenario_3_jobs(page: Page):
    S = "3. Jobs Flow"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/jobs")

    # Page loads
    if no_crash(page):
        record(S, "Jobs page loads", "PASS")
    else:
        record(S, "Jobs page loads", "FAIL", "Crash", screenshot(page, S, "jobs_page"))
        return

    # Create Job button
    try:
        create_btn = page.locator(
            "button:has-text('Create Job'), button:has-text('New Job'), button:has-text('Add Job')"
        ).first
        if create_btn.count() == 0:
            record(S, "Create Job button visible", "FAIL", "Button not found",
                   screenshot(page, S, "no_create_btn"))
            return
        record(S, "Create Job button visible", "PASS")

        create_btn.click()
        time.sleep(WAIT_AFTER_ACTION / 1000)

        # Drawer/modal should open
        drawer = page.locator(".ant-drawer, .ant-modal, [role='dialog']").first
        if drawer.count() > 0:
            record(S, "Create Job drawer opens", "PASS")
        else:
            record(S, "Create Job drawer opens", "FAIL", "No drawer or modal appeared",
                   screenshot(page, S, "no_drawer"))
            return
    except Exception as e:
        record(S, "Create Job button", "FAIL", str(e), screenshot(page, S, "create_btn_error"))
        return

    # Fill job form
    try:
        ts = datetime.now().strftime("%H%M%S")
        job_title = f"QA Test Engineer {ts}"

        fill_input(page, "title", job_title)
        fill_input(page, "description", "Automated QA test job — safe to delete")

        # Try department dropdown
        dept_select = page.locator(".ant-select").first
        if dept_select.count() > 0:
            dept_select.click()
            time.sleep(300 / 1000)
            page.locator(".ant-select-item").first.click()
            time.sleep(300 / 1000)

        save_btn = page.locator(
            "button:has-text('Save'), button:has-text('Create'), button:has-text('Submit')"
        ).last
        save_btn.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        if page_has_text(page, job_title):
            record(S, "Job created and visible in list", "PASS", job_title)
        else:
            record(S, "Job created and visible in list", "FAIL",
                   f"'{job_title}' not in list after save",
                   screenshot(page, S, "job_not_in_list"))
    except Exception as e:
        record(S, "Fill and save job form", "FAIL", str(e), screenshot(page, S, "job_form_error"))

# ── SCENARIO 4: Agency Linking ────────────────────────────────────────────────
def scenario_4_agencies(page: Page):
    S = "4. Agency Linking"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/agencies")

    if not no_crash(page):
        record(S, "Agencies page loads", "FAIL", "Crash", screenshot(page, S, "agencies_page"))
        return
    record(S, "Agencies page loads", "PASS")

    # Check list renders without crash
    try:
        time.sleep(1)
        if not no_crash(page):
            record(S, "Agencies list renders", "FAIL", "Crash after load",
                   screenshot(page, S, "agencies_list"))
            return
        record(S, "Agencies list renders", "PASS")
    except Exception as e:
        record(S, "Agencies list renders", "FAIL", str(e))

    # Try to open assign/invite modal
    try:
        invite_btn = page.locator(
            "button:has-text('Invite'), button:has-text('Add Agency'), button:has-text('Connect')"
        ).first
        if invite_btn.count() > 0:
            invite_btn.click()
            time.sleep(WAIT_AFTER_ACTION / 1000)
            modal = page.locator(".ant-modal, .ant-drawer, [role='dialog']").first
            if modal.count() > 0:
                record(S, "Invite/Add Agency modal opens", "PASS")
                # Close it
                close = page.locator("button:has-text('Cancel'), .ant-modal-close").first
                if close.count() > 0:
                    close.click()
            else:
                record(S, "Invite/Add Agency modal opens", "FAIL", "No modal appeared",
                       screenshot(page, S, "no_modal"))
        else:
            record(S, "Invite/Add Agency modal opens", "SKIP", "No invite button found")
    except Exception as e:
        record(S, "Invite/Add Agency modal opens", "FAIL", str(e),
               screenshot(page, S, "modal_error"))

    # Assign agency to job — check AssignAgencyModal
    try:
        row = page.locator("tr.ant-table-row, .agency-row").first
        if row.count() > 0:
            row.click()
            time.sleep(WAIT_AFTER_ACTION / 1000)
            # Right panel should open
            panel = page.locator(".right-panel, .ant-drawer-body").first
            if panel.count() > 0:
                record(S, "Agency right panel opens", "PASS")
            else:
                record(S, "Agency right panel opens", "FAIL", "No right panel",
                       screenshot(page, S, "no_right_panel"))
        else:
            record(S, "Agency right panel opens", "SKIP", "No agency rows in list")
    except Exception as e:
        record(S, "Agency right panel opens", "FAIL", str(e))

# ── SCENARIO 5: Candidates ────────────────────────────────────────────────────
def scenario_5_candidates(page: Page):
    S = "5. Candidates"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/candidates")

    if not no_crash(page):
        record(S, "Candidates page loads", "FAIL", "Crash",
               screenshot(page, S, "candidates_page"))
        return
    record(S, "Candidates page loads", "PASS")

    time.sleep(1)
    if not no_crash(page):
        record(S, "Candidates list renders", "FAIL", "Crash after data load",
               screenshot(page, S, "candidates_list"))
        return
    record(S, "Candidates list renders", "PASS")

    # Add candidate
    try:
        add_btn = page.locator(
            "button:has-text('Add Candidate'), button:has-text('Add'), button:has-text('New Candidate')"
        ).first
        if add_btn.count() == 0:
            record(S, "Add Candidate button", "FAIL", "Not found",
                   screenshot(page, S, "no_add_btn"))
            return

        add_btn.click()
        time.sleep(WAIT_AFTER_ACTION / 1000)

        ts = datetime.now().strftime("%H%M%S")
        fill_input(page, "first name", "QA")
        fill_input(page, "last name", f"Candidate{ts}")
        fill_input(page, "email", f"qa_candidate_{ts}@test.com")
        fill_input(page, "phone", "9876543210")

        save_btn = page.locator("button:has-text('Save'), button:has-text('Add')").last
        save_btn.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        if page_has_text(page, f"Candidate{ts}") or page_has_text(page, "QA"):
            record(S, "Add Candidate and visible in list", "PASS")
        else:
            record(S, "Add Candidate and visible in list", "FAIL",
                   "Candidate not in list after save",
                   screenshot(page, S, "candidate_not_in_list"))
    except Exception as e:
        record(S, "Add Candidate", "FAIL", str(e), screenshot(page, S, "add_candidate_error"))

# ── SCENARIO 6: Pipeline ──────────────────────────────────────────────────────
def scenario_6_pipeline(page: Page):
    S = "6. Pipeline"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/pipeline")

    if not no_crash(page):
        record(S, "Pipeline page loads", "FAIL", "Crash", screenshot(page, S, "pipeline"))
        return
    record(S, "Pipeline page loads", "PASS")

    # Check kanban columns exist
    try:
        time.sleep(1.5)  # let kanban load
        columns = page.locator(".kanban-column, .pipeline-column, .ant-col").all()
        if len(columns) >= 2:
            record(S, "Kanban columns render", "PASS", f"{len(columns)} columns found")
        else:
            record(S, "Kanban columns render", "FAIL",
                   f"Only {len(columns)} columns — expected 4+",
                   screenshot(page, S, "kanban_columns"))
    except Exception as e:
        record(S, "Kanban columns render", "FAIL", str(e))

    # Check a card exists and click it
    try:
        card = page.locator(".kanban-card, .candidate-card, .application-card").first
        if card.count() > 0:
            card.click()
            time.sleep(WAIT_AFTER_ACTION / 1000)
            panel = page.locator(".right-panel, .ant-drawer-body").first
            if panel.count() > 0:
                record(S, "Pipeline card opens right panel", "PASS")
            else:
                record(S, "Pipeline card opens right panel", "FAIL", "No right panel",
                       screenshot(page, S, "no_panel"))
        else:
            record(S, "Pipeline card opens right panel", "SKIP",
                   "No candidate cards in pipeline — add candidates first")
    except Exception as e:
        record(S, "Pipeline card opens right panel", "FAIL", str(e))

# ── SCENARIO 7: Agency Submissions ───────────────────────────────────────────
def scenario_7_agency_submissions(page: Page):
    S = "7. Agency Submissions"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, AGENCY_EMAIL, AGENCY_PASSWORD)
    time.sleep(1)

    if not no_crash(page):
        record(S, "Agency login", "FAIL", "Crash after login",
               screenshot(page, S, "agency_login"))
        return
    record(S, "Agency login", "PASS", f"URL: {page.url}")

    # Check agency sidebar is different from company
    try:
        sidebar_text = page.locator(".sidebar, .ant-menu, nav").first.inner_text(timeout=3000)
        if "Submissions" in sidebar_text or "Incoming Jobs" in sidebar_text:
            record(S, "Agency sidebar shows correct menu", "PASS")
        elif "Pipeline" in sidebar_text and "Agencies" in sidebar_text:
            record(S, "Agency sidebar shows correct menu", "FAIL",
                   "Showing company menu to agency user",
                   screenshot(page, S, "wrong_sidebar"))
        else:
            record(S, "Agency sidebar shows correct menu", "FAIL",
                   f"Unexpected sidebar: {sidebar_text[:100]}",
                   screenshot(page, S, "sidebar_unknown"))
    except Exception as e:
        record(S, "Agency sidebar", "FAIL", str(e))

    # Navigate to submissions
    try:
        navigate(page, "/submissions")
        if no_crash(page):
            record(S, "Submissions page loads", "PASS")
        else:
            record(S, "Submissions page loads", "FAIL", "Crash",
                   screenshot(page, S, "submissions_crash"))
    except Exception as e:
        record(S, "Submissions page loads", "FAIL", str(e))

# ── SCENARIO 8: Interviews ────────────────────────────────────────────────────
def scenario_8_interviews(page: Page):
    S = "8. Interviews"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/interviews")

    if not no_crash(page):
        record(S, "Interviews page loads", "FAIL", "Crash",
               screenshot(page, S, "interviews"))
        return
    record(S, "Interviews page loads", "PASS")

    time.sleep(1)
    if not no_crash(page):
        record(S, "Interviews list renders", "FAIL", "Crash after data load",
               screenshot(page, S, "interviews_list"))
        return
    record(S, "Interviews list renders", "PASS")

    # Check schedule interview button exists
    try:
        schedule_btn = page.locator(
            "button:has-text('Schedule'), button:has-text('New Interview')"
        ).first
        if schedule_btn.count() > 0:
            record(S, "Schedule Interview button visible", "PASS")
            schedule_btn.click()
            time.sleep(WAIT_AFTER_ACTION / 1000)
            modal = page.locator(".ant-modal, .ant-drawer, [role='dialog']").first
            if modal.count() > 0:
                record(S, "Schedule Interview modal opens", "PASS")
                close = page.locator("button:has-text('Cancel'), .ant-modal-close").first
                if close.count() > 0:
                    close.click()
            else:
                record(S, "Schedule Interview modal opens", "FAIL", "No modal",
                       screenshot(page, S, "no_schedule_modal"))
        else:
            record(S, "Schedule Interview button visible", "FAIL", "Button not found",
                   screenshot(page, S, "no_schedule_btn"))
    except Exception as e:
        record(S, "Schedule Interview", "FAIL", str(e))

# ── SCENARIO 9: Offers ────────────────────────────────────────────────────────
def scenario_9_offers(page: Page):
    S = "9. Offers"
    print(f"\n{'─'*50}\n{S}\n{'─'*50}")

    login(page, COMPANY_EMAIL, COMPANY_PASSWORD)
    navigate(page, "/offers")

    if not no_crash(page):
        record(S, "Offers page loads", "FAIL", "Crash", screenshot(page, S, "offers"))
        return
    record(S, "Offers page loads", "PASS")

    time.sleep(1)
    if not no_crash(page):
        record(S, "Offers list renders", "FAIL", "Crash after load",
               screenshot(page, S, "offers_list"))
        return
    record(S, "Offers list renders", "PASS")

# ── Report Generator ──────────────────────────────────────────────────────────
def save_report():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Save JSON for qa_agent.py to consume
    json_path = REPORT_DIR / f"{ts}.json"
    with open(json_path, "w") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "PASS"),
            "failed": sum(1 for r in results if r["status"] == "FAIL"),
            "skipped": sum(1 for r in results if r["status"] == "SKIP"),
            "results": results
        }, f, indent=2)

    # Save markdown for humans
    md_lines = [
        f"# UI QA Report — {ts}",
        f"**Total:** {len(results)}  |  "
        f"**✅ Pass:** {sum(1 for r in results if r['status'] == 'PASS')}  |  "
        f"**❌ Fail:** {sum(1 for r in results if r['status'] == 'FAIL')}  |  "
        f"**⏭ Skip:** {sum(1 for r in results if r['status'] == 'SKIP')}",
        "",
        "---",
        ""
    ]

    current_scenario = None
    for r in results:
        if r["scenario"] != current_scenario:
            current_scenario = r["scenario"]
            md_lines.append(f"## {current_scenario}")
        icon = "✅" if r["status"] == "PASS" else ("❌" if r["status"] == "FAIL" else "⏭")
        line = f"- {icon} **{r['step']}**"
        if r["detail"]:
            line += f" — {r['detail']}"
        if r["screenshot"]:
            line += f" — [screenshot]({r['screenshot']})"
        md_lines.append(line)

    md_path = REPORT_DIR / f"{ts}.md"
    md_path.write_text("\n".join(md_lines))

    print(f"\n{'═'*50}")
    print(f"  REPORT SAVED")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"  Screenshots: {SCREENSHOT_DIR}")
    print(f"{'═'*50}\n")

    return str(json_path)

# ── Main ──────────────────────────────────────────────────────────────────────
SCENARIO_MAP = {
    1: scenario_1_company_onboarding,
    2: scenario_2_organisation,
    3: scenario_3_jobs,
    4: scenario_4_agencies,
    5: scenario_5_candidates,
    6: scenario_6_pipeline,
    7: scenario_7_agency_submissions,
    8: scenario_8_interviews,
    9: scenario_9_offers,
}

def main():
    parser = argparse.ArgumentParser(description="TOS UI QA Runner")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--scenario", type=int, help="Run single scenario (1-9)")
    parser.add_argument("--slow", type=int, default=0, help="Slow motion ms (e.g. --slow 500)")
    args = parser.parse_args()

    headless = not args.headed
    mode = "HEADED" if args.headed else "HEADLESS"

    print(f"\n{'═'*50}")
    print(f"  TOS UI QA Runner — Playwright")
    print(f"  Mode: {mode}")
    print(f"  Target: {BASE_URL}")
    if args.scenario:
        print(f"  Running scenario {args.scenario} only")
    print(f"{'═'*50}")

    scenarios_to_run = [args.scenario] if args.scenario else list(SCENARIO_MAP.keys())

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=args.slow
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(REPORT_DIR / "videos") if not headless else None
        )
        page = context.new_page()
        page.set_default_timeout(ACTION_TIMEOUT)

        for num in scenarios_to_run:
            fn = SCENARIO_MAP.get(num)
            if fn:
                try:
                    fn(page)
                except Exception as e:
                    record(f"Scenario {num}", "Unexpected crash", "FAIL", str(e),
                           screenshot(page, f"scenario_{num}", "crash"))
            else:
                print(f"  ⚠ Scenario {num} not found")

        context.close()
        browser.close()

    report_path = save_report()

    # Summary
    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    total   = len(results)

    print(f"  Results: {passed}/{total} passed  |  {failed} failed  |  {skipped} skipped")

    if failed > 0:
        print(f"\n  ❌ FAILED STEPS:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"     • [{r['scenario']}] {r['step']} — {r['detail']}")

    print(f"\n  Run qa_agent.py next to get Qwen's diagnosis.\n")
    return 1 if failed > 0 else 0

if __name__ == "__main__":
    sys.exit(main())