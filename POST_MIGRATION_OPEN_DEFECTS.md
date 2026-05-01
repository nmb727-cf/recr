# POST-MIGRATION OPEN DEFECTS

| Severity | Actor | Page/Flow | Blocker Reason | Recommended Next Fix |
|----------|-------|-----------|----------------|----------------------|
| Medium | All | Mixed Imports in `App.tsx` | Some imports still rely on legacy wrappers. | Complete the transition of all `App.tsx` imports to direct actor paths. |
| Medium | All | Component internal imports | Potential for broken relative imports inside moved components. | Run a global frontend build check to identify missing modules. |
| Low | Admin | Admin Audit / Settings | Low-priority pages not yet verified for runtime stability. | Smoke test admin-specific actor flows. |
