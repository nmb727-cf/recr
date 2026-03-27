from pathlib import Path

ROOT = Path.home() / "projects" / "SaaS_Project"
testing = ROOT / "sys_know" / "testing"
reports = ROOT / "sys_know" / "reports"

print("# Nightly Summary\n")

files = {
    "Pytest": testing / "pytest.log",
    "Schema": testing / "schema.log",
    "Schemathesis": testing / "schemathesis.log",
    "Vitest": testing / "vitest.log",
    "Playwright": testing / "playwright.log",
}

for name, path in files.items():
    print(f"## {name}")
    if path.exists():
        content = path.read_text(errors="ignore").splitlines()
        tail = content[-20:] if len(content) > 20 else content
        print("```")
        print("\n".join(tail))
        print("```")
    else:
        print("No log found.\n")
