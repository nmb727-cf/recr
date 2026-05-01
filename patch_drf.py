import re

with open('backend/apps/core/middleware.py', 'r') as f:
    content = f.read()

injection = """
                self.initial(request, *args, **kwargs)
                
                # --- Tenant Isolation Enforcement ---
                user = getattr(request, 'user', None)
                path = getattr(request, 'path', '')
                if user and getattr(user, 'is_authenticated', False) and path.startswith('/api/v1/'):
                    from shared.tenant_access import is_agency_user
                    is_agency = is_agency_user(user)
                    
                    # Define agency paths
                    is_agency_path = path.startswith('/api/v1/agency-candidates/')
                    
                    # Define company paths (strict)
                    is_company_path = path.startswith('/api/v1/jobs/') or \\
                                      path.startswith('/api/v1/candidates/') or \\
                                      path.startswith('/api/v1/pipeline/') or \\
                                      path.startswith('/api/v1/analytics/')
                    
                    # Allow candidates to use public job search
                    is_public = path.startswith('/api/v1/jobs/public') or path.startswith('/api/v1/jobs/search')
                    
                    if is_agency and is_company_path and not is_public:
                        from apps.core.responses import error_response
                        response = error_response("Agency users cannot access company modules.", status_code=403)
                        self.response = self.finalize_response(request, response, *args, **kwargs)
                        return self.response
                        
                    if not is_agency and is_agency_path:
                        from apps.core.responses import error_response
                        response = error_response("Company users cannot access agency modules.", status_code=403)
                        self.response = self.finalize_response(request, response, *args, **kwargs)
                        return self.response
                # ------------------------------------
"""

# We replace: self.initial(request, *args, **kwargs)
content = content.replace("                self.initial(request, *args, **kwargs)", injection)

with open('backend/apps/core/middleware.py', 'w') as f:
    f.write(content)
