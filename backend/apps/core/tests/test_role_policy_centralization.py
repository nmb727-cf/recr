import re
from pathlib import Path

from django.test import SimpleTestCase


class RolePolicyCentralizationTests(SimpleTestCase):
    """
    Guardrail test:
    Prevent reintroducing ad-hoc hardcoded role-list checks in critical modules.
    Keep scope narrow so teams can still iterate in non-critical areas.
    """

    ROOT = Path(__file__).resolve().parents[3]
    CRITICAL_FILES = [
        "apps/agencies/views.py",
        "apps/analytics/views.py",
        "apps/automation/views.py",
        "apps/candidates/views.py",
        "apps/candidates/crm_views.py",
        "apps/communications/views.py",
        "apps/interviews/views.py",
        "apps/jobs/views.py",
        "apps/pipeline/views.py",
    ]

    FORBIDDEN_PATTERNS = [
        re.compile(r"request\.user\.role\s+in\s+\["),
        re.compile(r"request\.user\.role\s+not\s+in\s+\["),
        re.compile(r"role__in\s*=\s*\["),
        re.compile(r"allowed_roles\s*=\s*\["),
    ]

    def test_critical_modules_avoid_hardcoded_role_lists(self):
        violations = []
        for rel_path in self.CRITICAL_FILES:
            content = (self.ROOT / rel_path).read_text(encoding="utf-8")
            for line_no, line in enumerate(content.splitlines(), start=1):
                for pattern in self.FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        violations.append(f"{rel_path}:{line_no}: {line.strip()}")

        self.assertEqual(
            violations,
            [],
            msg=(
                "Found hardcoded role-list checks in critical modules. "
                "Use shared.actor_access constants/helpers instead.\n"
                + "\n".join(violations)
            ),
        )

