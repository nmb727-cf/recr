# POST-MIGRATION RUNTIME OPEN ITEMS

| Item | Severity | Actor | Recommended Fix |
|------|----------|-------|-----------------|
| Full Frontend Build | High | All | Run `npm run build` to catch any remaining stale relative imports in leaf components. |
| Nested Component Audit | Medium | All | Grep for `@/pages/` in all `src/components/` files to ensure full coverage. |
| Asset Path Verification | Low | All | Ensure images/icons imported via relative paths in moved files are still resolving. |
