#!/usr/bin/env bash
set -e

ROOT="$HOME/projects/SaaS_Project"
DATE="$(date +%F_%H-%M-%S)"

mkdir -p "$ROOT/sys_know/testing"
mkdir -p "$ROOT/sys_know/generated/openapi"
mkdir -p "$ROOT/sys_know/generated/test-results"
mkdir -p "$ROOT/sys_know/generated/coverage"
mkdir -p "$ROOT/sys_know/reports"

# Backend
cd "$ROOT"
source venv/bin/activate

echo "=== PYTEST ==="
pytest --cov=backend --cov-report=html:"$ROOT/sys_know/generated/coverage/htmlcov" \
  --cov-report=xml:"$ROOT/sys_know/generated/coverage/coverage.xml" \
  > "$ROOT/sys_know/testing/pytest.log" 2>&1 || true

echo "=== OPENAPI ==="
cd "$ROOT/backend"
python manage.py spectacular --file "$ROOT/sys_know/generated/openapi/schema.yaml" \
  > "$ROOT/sys_know/testing/schema.log" 2>&1 || true

cd "$ROOT/backend"
python manage.py runserver 127.0.0.1:8000 > "$ROOT/sys_know/testing/django_server.log" 2>&1 &
DJANGO_PID=$!
sleep 10

echo "=== SCHEMATHESIS ==="
schemathesis run http://127.0.0.1:8000/api/schema/ --wait-for-schema=30 > "$ROOT/sys_know/testing/schemathesis.log" 2>&1 || true

kill $DJANGO_PID 2>/dev/null || true
# Frontend
cd "$ROOT/frontend"

echo "=== VITEST ==="
npm run test -- --run > "$ROOT/sys_know/testing/vitest.log" 2>&1 || true

echo "=== PLAYWRIGHT ==="
npx playwright test > "$ROOT/sys_know/testing/playwright.log" 2>&1 || true

# Gap scripts
cd "$ROOT"
python tools/check_api_coverage.py > "$ROOT/sys_know/reports/backend_frontend_gap.md" 2>&1 || true
python tools/build_summary.py > "$ROOT/sys_know/reports/nightly_summary.md" 2>&1 || true

# Docs build
echo "=== MKDOCS BUILD ==="
mkdocs build -d "$ROOT/sys_know/site" > "$ROOT/sys_know/testing/mkdocs.log" 2>&1 || true

echo "Nightly run completed at $DATE"