# Gemini Master Audit Index

| Module | Audit File | Status | Major Issues | Notes |
| :--- | :--- | :--- | :--- | :--- |
| accounts | `sys_know/reports/gemini/accounts_audit.md` | COMPLETED | 2 | Placeholder views (Reset Pass) and limited tests. |
| candidates | `sys_know/reports/gemini/candidates_audit.md` | COMPLETED | 1 | CRITICAL: No tests found in candidates module. |
| jobs | `sys_know/reports/gemini/jobs_audit.md` | COMPLETED | 2 | No tests found; data leak in serializer. |
| agencies | `sys_know/reports/gemini/agencies_audit.md` | COMPLETED | 2 | Missing governance endpoint; no tests found. |
| pipeline | `sys_know/reports/gemini/pipeline_audit.md` | COMPLETED | 2 | No tests found; insecure updates (protection bypass). |
| communications | `sys_know/reports/gemini/communications_audit.md` | COMPLETED | 1 | Enterprise email engine; no tests found. |
| interviews | `sys_know/reports/gemini/interviews_audit.md` | COMPLETED | 2 | Missing interview package/binding endpoints; no tests. |
| passport | `sys_know/reports/gemini/passport_audit.md` | COMPLETED | 1 | GDPR compliant; no tests found. |
| organisations | `sys_know/reports/gemini/organisations_audit.md` | COMPLETED | 1 | Structural profile management; no tests found. |
| documents | `sys_know/reports/gemini/documents_audit.md` | COMPLETED | 2 | No frontend API; no tests found; placeholder download logic. |
| rbac | `sys_know/reports/gemini/rbac_audit.md` | COMPLETED | 2 | Security backbone; no tests; cache invalidation bug. |
| talent_pools | `sys_know/reports/gemini/talent_pools_audit.md` | COMPLETED | 2 | Endpoint mismatch (/candidates/id/talent-pools/); no tests. |
| notifications | `sys_know/reports/gemini/notifications_audit.md` | COMPLETED | 1 | Logic residing in communications app; no tests found. |
| automation | `sys_know/reports/gemini/automation_audit.md` | COMPLETED | 2 | No management API; no tests found; missing execution logic. |
| translations | `sys_know/reports/gemini/translations_audit.md` | COMPLETED | 1 | Dynamic UI localization; no tests found. |
| analytics | `sys_know/reports/gemini/analytics_audit.md` | COMPLETED | 1 | Broken dept filter; no tests found. |
| cafe | `sys_know/reports/gemini/cafe_audit.md` | COMPLETED | 1 | Empty module; logic integrated into other apps. |
| marketplace | `sys_know/reports/gemini/marketplace_audit.md` | COMPLETED | 1 | Empty module; placeholder only. |
| tenants | `sys_know/reports/gemini/tenants_audit.md` | COMPLETED | 1 | Multi-tenancy layer; no tests found. |

**Audit Completed.**
