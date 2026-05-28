import os
import re
import ast
import json
from pathlib import Path

FRONTEND_DIR = Path("frontend/src")
BACKEND_DIR = Path("backend/apps")

report = {
    "frontend": [],
    "backend": [],
    "empty_modules": []
}

# Frontend Analysis
def analyze_frontend():
    if not FRONTEND_DIR.exists():
        return
        
    for root, _, files in os.walk(FRONTEND_DIR):
        for file in files:
            if not file.endswith(".tsx") and not file.endswith(".ts"):
                continue
                
            filepath = Path(root) / file
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            issues = []
            
            # 1. Look for 'any' types
            if "any" in content:
                any_count = len(re.findall(r'\bany\b', content))
                if any_count > 0:
                    issues.append(f"Uses 'any' type ({any_count} times)")
                    
            # 2. Look for buttons without onClick or type=submit
            # Simple regex heuristic
            buttons = re.findall(r'<[Bb]utton[^>]*>', content)
            for btn in buttons:
                if "onClick" not in btn and "submit" not in btn.lower() and "type=" not in btn:
                    issues.append("Found disconnected button (no onClick or submit type)")
                    
            # 3. Look for TODOs or Hardcoded mocks
            if re.search(r'TODO|FIXME|mockData|dummy', content, re.IGNORECASE):
                issues.append("Contains TODOs or mock data")
                
            # 4. Form inputs without validation/state binding
            inputs = re.findall(r'<[Ii]nput[^>]*>', content)
            for inp in inputs:
                if "value=" not in inp and "{...register" not in inp and "onChange=" not in inp and "defaultValue=" not in inp:
                    issues.append("Found uncontrolled/unvalidated input field")
                    
            if issues:
                report["frontend"].append({
                    "file": str(filepath.relative_to(FRONTEND_DIR)),
                    "issues": issues
                })

# Backend Analysis
def analyze_backend():
    if not BACKEND_DIR.exists():
        return
        
    for app_dir in BACKEND_DIR.iterdir():
        if not app_dir.is_dir() or app_dir.name == "__pycache__":
            continue
            
        views_file = app_dir / "views.py"
        models_file = app_dir / "models.py"
        
        is_empty = True
        
        # Check if views.py has actual logic
        if views_file.exists():
            is_empty = False
            with open(views_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            issues = []
            if "pass" in content:
                issues.append("Contains 'pass' blocks (unimplemented views)")
            
            # Find hardcoded responses
            if re.search(r'Response\(\s*\{.*"dummy"|"mock"|TODO', content, re.IGNORECASE):
                issues.append("Contains hardcoded API responses instead of DB logic")
                
            if issues:
                report["backend"].append({
                    "module": app_dir.name,
                    "file": "views.py",
                    "issues": issues
                })
                
        # Check if models.py has actual logic
        if models_file.exists():
            is_empty = False
            with open(models_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            issues = []
            if "pass" in content:
                issues.append("Contains empty models ('pass')")
                
            if issues:
                report["backend"].append({
                    "module": app_dir.name,
                    "file": "models.py",
                    "issues": issues
                })
                
        if is_empty:
            report["empty_modules"].append(app_dir.name)

if __name__ == "__main__":
    analyze_frontend()
    analyze_backend()
    
    with open("granular_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Audit complete. Found {len(report['frontend'])} frontend files with issues, {len(report['backend'])} backend files with issues, and {len(report['empty_modules'])} empty modules.")
