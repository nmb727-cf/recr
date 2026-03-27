from __future__ import annotations
from pathlib import Path
import re
import yaml

ROOT = Path.home() / "projects" / "SaaS_Project"
testing = ROOT / "sys_know" / "testing"
reports = ROOT / "sys_know" / "reports"

files = {
    "pytest": testing / "pytest.log",
    "schema": testing / "schema.log",
    "schemathesis": testing / "schemathesis.log",
    "vitest": testing / "vitest.log",
    "playwright": testing / "playwright.log",
    "mkdocs": testing / "mkdocs.log",
}

print("# Nightly Summary\n")

for name, path in files.items():
    print(f"## {name}")
    if path.exists():
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = lines[-20:] if len(lines) > 20 else lines
        print("```")
        print("\n".join(tail))
        print("```")
    else:
        print("Missing log file.\n")
ROOT = Path.home() / "projects" / "SaaS_Project"
FRONTEND = ROOT / "frontend" / "src"
REGISTRY = ROOT / "sys_know" / "testing" / "scenario_registry.yaml"
OUTPUT = ROOT / "sys_know" / "reports" / "ui_coverage_gap.md"


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {"scenarios": []}
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {"scenarios": []}


def discover_pages() -> list[str]:
    pages = []
    pages_dir = FRONTEND / "pages"
    if not pages_dir.exists():
        return pages
    for path in pages_dir.rglob("*"):
        if path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"}:
            rel = path.relative_to(FRONTEND).as_posix()
            pages.append(rel)
    return sorted(pages)


def discover_api_calls() -> list[str]:
    api_calls: set[str] = set()
    pattern = re.compile(r'["\'`](\/api\/[^"\'`\s]+)["\'`]')
    for path in FRONTEND.rglob("*"):
        if path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"}:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for match in pattern.findall(text):
                api_calls.add(match)
    return sorted(api_calls)


def covered_pages(registry: dict) -> set[str]:
    covered: set[str] = set()
    for scenario in registry.get("scenarios", []):
        for page in scenario.get("pages", []):
            covered.add(page)
    return covered


def covered_apis(registry: dict) -> set[str]:
    covered: set[str] = set()
    for scenario in registry.get("scenarios", []):
        for api in scenario.get("api_endpoints", []):
            covered.add(api)
    return covered


def main() -> None:
    registry = load_registry()
    pages = discover_pages()
    apis = discover_api_calls()

    scenario_pages = covered_pages(registry)
    scenario_apis = covered_apis(registry)

    uncovered_pages = [p for p in pages if all(token not in p for token in ("test", "__tests__")) and p not in scenario_pages]
    uncovered_apis = [a for a in apis if a not in scenario_apis]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# UI Coverage Gap Report\n\n")

        f.write("## Registered Scenarios\n")
        for s in registry.get("scenarios", []):
            f.write(f"- {s.get('id')} ({s.get('module')}) [{s.get('status')}]\n")

        f.write("\n## Discovered Frontend Pages\n")
        for p in pages:
            f.write(f"- {p}\n")

        f.write("\n## Discovered Frontend API Calls\n")
        for a in apis:
            f.write(f"- {a}\n")

        f.write("\n## Uncovered Pages\n")
        if uncovered_pages:
            for p in uncovered_pages:
                f.write(f"- {p}\n")
        else:
            f.write("- None\n")

        f.write("\n## Uncovered API Calls\n")
        if uncovered_apis:
            for a in uncovered_apis:
                f.write(f"- {a}\n")
        else:
            f.write("- None\n")

        f.write("\n## Next Action\n")
        f.write("- Add new scenarios for uncovered pages and API calls.\n")


if __name__ == "__main__":
    main()        