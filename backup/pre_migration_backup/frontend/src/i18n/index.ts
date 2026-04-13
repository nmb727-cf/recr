/**
 * i18next configuration.
 *
 * Architecture:
 * - Static JSON files (locales/) are the source of truth for shipped translations.
 * - DB-backed TranslationOverride records layer on top for runtime corrections
 *   and tenant-custom labels (loaded separately via /api/v1/translations/overrides/).
 * - Namespaces map 1:1 to modules: common, candidates, auth, jobs, ...
 * - Language is driven by user.language from the auth store (see AuthBootstrap in App.tsx).
 *
 * Adding a new language:
 *   1. Create src/locales/<code>/<namespace>.json files
 *   2. Import and register them below
 *   3. Add to SUPPORTED_LANGUAGES
 *   4. Add the language code to Settings.tsx language options
 *   5. Run seed_translations to add DB records
 *
 * Adding a new namespace:
 *   1. Create src/locales/en/<namespace>.json (and other languages)
 *   2. Import and register below
 *   3. Use with: const { t } = useTranslation('<namespace>')
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

// ── English ────────────────────────────────────────────────────────────────
import enCommon from '@/locales/en/common.json'
import enCandidates from '@/locales/en/candidates.json'
import enAuth from '@/locales/en/auth.json'
import enDashboard from '@/locales/en/dashboard.json'
import enJobs from '@/locales/en/jobs.json'
import enPipeline from '@/locales/en/pipeline.json'
import enSettings from '@/locales/en/settings.json'

// ── Hindi ──────────────────────────────────────────────────────────────────
import hiCommon from '@/locales/hi/common.json'
import hiCandidates from '@/locales/hi/candidates.json'
import hiAuth from '@/locales/hi/auth.json'
import hiDashboard from '@/locales/hi/dashboard.json'
import hiJobs from '@/locales/hi/jobs.json'
import hiPipeline from '@/locales/hi/pipeline.json'
import hiSettings from '@/locales/hi/settings.json'

export const SUPPORTED_LANGUAGES: Array<{ code: string; label: string; nativeLabel: string }> = [
  { code: 'en', label: 'English',  nativeLabel: 'English' },
  { code: 'hi', label: 'Hindi',    nativeLabel: 'हिंदी' },
  { code: 'mr', label: 'Marathi',  nativeLabel: 'मराठी' },
  { code: 'fr', label: 'French',   nativeLabel: 'Français' },
  { code: 'de', label: 'German',   nativeLabel: 'Deutsch' },
  { code: 'es', label: 'Spanish',  nativeLabel: 'Español' },
  { code: 'ar', label: 'Arabic',   nativeLabel: 'العربية' },
  { code: 'zh', label: 'Chinese',  nativeLabel: '中文' },
]

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        common: enCommon,
        candidates: enCandidates,
        auth: enAuth,
        dashboard: enDashboard,
        jobs: enJobs,
        pipeline: enPipeline,
        settings: enSettings,
      },
      hi: {
        common: hiCommon,
        candidates: hiCandidates,
        auth: hiAuth,
        dashboard: hiDashboard,
        jobs: hiJobs,
        pipeline: hiPipeline,
        settings: hiSettings,
      },
    },

    lng: 'en',           // default; overridden by user.language in AuthBootstrap
    fallbackLng: 'en',   // always falls back to English if a key is missing
    defaultNS: 'common',

    interpolation: {
      escapeValue: false, // React already escapes
    },
  })

export default i18n
