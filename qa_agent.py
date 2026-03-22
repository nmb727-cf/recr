#!/usr/bin/env python3
"""
TOS Local QA Agent
Uses Ollama + qwen2.5-coder:7b to analyze test failures and suggest fixes.
Run after qa_runner.py generates results.
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
BACKEND_PATH = "/home/nirav/projects/SaaS_Project/backend"
QA_RESULTS_PATH = "/home/nirav/projects/SaaS_Project/qa_results"
REPORT_PATH = "/home/nirav/projects/SaaS_Project/qa_agent_reports"

# ── Helpers ──────────────────────────────────────────────────────────────────
def ask_qwen(prompt: str) -> str:
    """Send prompt to local Qwen model, return response."""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 1024}
        }, timeout=120)
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"ERROR: Could not reach Ollama — {e}"


def read_file(path: str) -> str:
    """Read a file, return content or error string."""
    try:
        return Path(path).read_text()
    except Exception as e:
        return f"FILE NOT FOUND: {path} — {e}"


def get_latest_qa_results() -> dict:
    """Load the most recent qa_runner output."""
    results_dir = Path(QA_RESULTS_PATH)
    if not results_dir.exists():
        return {}
    files = sorted(results_dir.glob("*.json"))
    if not files:
        # Try markdown files
        files = sorted(results_dir.glob("*.md"))
        if not files:
            return {}
        return {"raw_md": files[-1].read_text(), "source": str(files[-1])}
    return json.loads(files[-1].read_text())


def run_qa_runner() -> str:
    """Run qa_runner.py and capture output."""
    print("▶ Running qa_runner.py...")
    result = subprocess.run(
        ["python3", "qa_runner.py"],
        cwd="/home/nirav/projects/SaaS_Project",
        capture_output=True, text=True, timeout=120
    )
    return result.stdout + result.stderr


# ── Scenario Test Runner ─────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "Company Onboarding",
        "endpoints": [
            "POST /api/v1/auth/register/company/",
            "POST /api/v1/organisation/onboarding/",
            "GET  /api/v1/organisation/profile/",
        ],
        "files": [
            "apps/accounts/views.py",
            "apps/organisations/views.py",
        ]
    },
    {
        "name": "Jobs Flow",
        "endpoints": [
            "POST /api/v1/jobs/requisitions/",
            "GET  /api/v1/jobs/requisitions/",
            "POST /api/v1/jobs/requisitions/{id}/submit/",
            "POST /api/v1/jobs/requisitions/{id}/approve/",
            "POST /api/v1/jobs/requisitions/{id}/publish/",
        ],
        "files": [
            "apps/jobs/views.py",
            "apps/jobs/models.py",
        ]
    },
    {
        "name": "Agency Linking",
        "endpoints": [
            "GET  /api/v1/agencies/",
            "POST /api/v1/agencies/relationships/",
            "POST /api/v1/agencies/relationships/{id}/activate/",
        ],
        "files": [
            "apps/agencies/views.py",
            "apps/agencies/models.py",
        ]
    },
    {
        "name": "Candidates",
        "endpoints": [
            "POST /api/v1/candidates/",
            "GET  /api/v1/candidates/",
            "GET  /api/v1/candidates/{id}/",
        ],
        "files": [
            "apps/candidates/views.py",
            "apps/candidates/models.py",
        ]
    },
    {
        "name": "Pipeline",
        "endpoints": [
            "GET  /api/v1/pipeline/kanban/",
            "POST /api/v1/applications/{id}/move-stage/",
            "POST /api/v1/applications/{id}/reject/",
        ],
        "files": [
            "apps/pipeline/views.py",
            "apps/pipeline/models.py",
        ]
    },
    {
        "name": "Interviews",
        "endpoints": [
            "POST /api/v1/interviews/",
            "GET  /api/v1/interviews/",
            "POST /api/v1/interviews/{id}/feedback/",
        ],
        "files": [
            "apps/interviews/views.py",
        ]
    },
    {
        "name": "Offers",
        "endpoints": [
            "POST /api/v1/documents/offer-letters/",
            "POST /api/v1/documents/offer-letters/{id}/send/",
            "POST /api/v1/documents/offer-letters/{id}/respond/",
        ],
        "files": [
            "apps/documents/views.py",
        ]
    },
]


def analyze_scenario(scenario: dict, qa_output: str) -> dict:
    """Ask Qwen to analyze one scenario against QA output."""

    # Read relevant backend files
    file_contents = ""
    for f in scenario["files"]:
        full_path = f"{BACKEND_PATH}/{f}"
        content = read_file(full_path)
        file_contents += f"\n\n### {f}\n{content[:3000]}"  # cap at 3000 chars per file

    prompt = f"""You are a senior Django backend engineer reviewing a recruitment platform.

SCENARIO: {scenario['name']}

ENDPOINTS THIS SCENARIO USES:
{chr(10).join(scenario['endpoints'])}

RECENT QA TEST OUTPUT:
{qa_output[:2000]}

RELEVANT BACKEND CODE:
{file_contents}

Your job:
1. Based on the QA output, is this scenario PASSING, FAILING, or UNKNOWN?
2. If FAILING — what is the exact problem? Reference the specific view, model field, or logic.
3. What is the one-line fix needed?
4. Which file needs to be changed?

Be specific. No vague answers. If you cannot determine the issue from the information given, say UNKNOWN and explain what information you need.

Format your response as:
STATUS: PASSING / FAILING / UNKNOWN
PROBLEM: [exact description or N/A]
FIX: [exact fix or N/A]
FILE: [file path or N/A]
"""

    response = ask_qwen(prompt)
    return {
        "scenario": scenario["name"],
        "analysis": response
    }


# ── Report Generator ─────────────────────────────────────────────────────────
def generate_report(results: list, qa_output: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# QA Agent Report — {today}",
        f"Model: {MODEL}",
        "---",
        "",
        "## QA Runner Raw Output",
        "```",
        qa_output[:1000],
        "```",
        "",
        "## Scenario Analysis",
        ""
    ]

    for r in results:
        lines.append(f"### {r['scenario']}")
        lines.append(r["analysis"])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  TOS Local QA Agent — powered by Qwen2.5-coder:7b")
    print("=" * 60)

    # Step 1: Run qa_runner
    qa_output = run_qa_runner()
    print(qa_output[:500])

    # Step 2: Analyze each scenario
    print("\n▶ Analyzing scenarios with Qwen...")
    results = []
    for scenario in SCENARIOS:
        print(f"  → {scenario['name']}...")
        result = analyze_scenario(scenario, qa_output)
        results.append(result)

        # Print quick status
        first_line = result["analysis"].split("\n")[0] if result["analysis"] else "?"
        print(f"     {first_line}")

    # Step 3: Generate report
    report = generate_report(results, qa_output)

    # Step 4: Save report
    Path(REPORT_PATH).mkdir(parents=True, exist_ok=True)
    report_file = f"{REPORT_PATH}/{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    Path(report_file).write_text(report)

    print(f"\n✅ Report saved to: {report_file}")
    print("\n" + "=" * 60)
    print(report[:1000])


if __name__ == "__main__":
    main()