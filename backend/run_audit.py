import os
import re
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, 'backend')
FRONTEND = os.path.join(ROOT, 'frontend')
SYS_KNOW = os.path.join(ROOT, 'sys_know')
REPORTS = os.path.join(SYS_KNOW, 'reports', 'gemini')

os.makedirs(REPORTS, exist_ok=True)

backend_urls = []
frontend_apis = []
frontend_pages = []
tests = []

# 1. Discover Backend Endpoints
def extract_backend_routes():
    # Very basic regex scanning for path() and router.register()
    url_files = []
    for root, _, files in os.walk(os.path.join(BACKEND, 'apps')):
        for file in files:
            if file.endswith('urls.py'):
                url_files.append(os.path.join(root, file))
    
    routes = []
    for filepath in url_files:
        app_name = os.path.basename(os.path.dirname(filepath))
        with open(filepath, 'r') as f:
            content = f.read()
            # router.register(r'agencies', AgencyViewSet)
            routers = re.findall(r"router\.register\(\s*r['\"]([^'\"]+)['\"]\s*,", content)
            paths = re.findall(r"path\(\s*['\"]([^'\"]*)['\"]\s*,", content)
            
            for r in routers:
                routes.append(f"/{app_name}/{r}")
            for p in paths:
                routes.append(f"/{app_name}/{p}")
    return routes

# 2. Discover Frontend API Calls
def extract_frontend_apis():
    api_dir = os.path.join(FRONTEND, 'src', 'api')
    if not os.path.exists(api_dir):
        return []
    
    api_calls = []
    for root, _, files in os.walk(api_dir):
        for file in files:
            if file.endswith('.ts') or file.endswith('.js'):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    # Look for things like `api.get('/agencies')`
                    calls = re.findall(r"api\.(get|post|put|patch|delete|request)\(\s*[`'\"]([^`'\"]+)[`'\"]", content)
                    for method, url in calls:
                        api_calls.append(url)
    return api_calls

# 3. Discover Frontend Pages
def extract_frontend_pages():
    pages_dir = os.path.join(FRONTEND, 'src', 'pages')
    if not os.path.exists(pages_dir):
        return []
    
    pages = []
    for root, _, files in os.walk(pages_dir):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.jsx') or file.endswith('.vue'):
                rel_path = os.path.relpath(os.path.join(root, file), pages_dir)
                pages.append(rel_path)
    return pages

# 4. Discover Tests
def extract_tests():
    test_files = []
    for root, _, files in os.walk(os.path.join(BACKEND, 'apps')):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return test_files

# Execute extraction
b_routes = extract_backend_routes()
f_apis = extract_frontend_apis()
f_pages = extract_frontend_pages()
b_tests = extract_tests()

with open(os.path.join(REPORTS, 'debug_info.json'), 'w') as f:
    json.dump({
        'backend_routes': b_routes,
        'frontend_apis': f_apis,
        'frontend_pages': f_pages,
        'backend_tests': b_tests
    }, f, indent=2)

print("Extraction complete. Check sys_know/reports/gemini/debug_info.json")
