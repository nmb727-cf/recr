# UX Logic Issues

## Orphaned Pages
`RBACDebugPage.tsx` is exposed but shouldn't be in production navigation.

## Missing Error Toasts
API errors from `src/api/` are not consistently caught and displayed as toasts in the UI, leading to silent failures on 400/500 responses.
