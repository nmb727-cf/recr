# Confirmed Backend-Only Areas

## Documents & Offers
- **Path**: `/documents/`, `/documents/offers/`
- **Features**: Document generation, offer creation, approval workflow (`/documents/offers/<uuid:pk>/approve/`).
- **Frontend Status**: No `api/documents.ts` exists. No pages found for offer generation.

## Communication Webhooks & Email Audit
- **Path**: `/communications/communications/email-webhooks/<str:provider>`, `/communications/communications/email-audit/`
- **Features**: Tracking email deliveries, bounces, opens.
- **Frontend Status**: Handled transparently by backend, no UI exposed for audits.

## Translations & Overrides
- **Path**: `/translations/overrides/`
- **Features**: Dynamic string replacement/i18n.
- **Frontend Status**: No frontend admin UI for translation overrides.
