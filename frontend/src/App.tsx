import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import enUS from 'antd/locale/en_US'
import hiIN from 'antd/locale/hi_IN'
import type { Locale } from 'antd/lib/locale'
import i18n from '@/i18n'

import { useAuthStore } from '@/store/authStore'
import ProtectedRoute from '@/components/common/ProtectedRoute'
import OnboardingGuard from '@/components/common/OnboardingGuard'
import AppLayout from '@/layouts/AppLayout'
import OnboardingLayout from '@/layouts/OnboardingLayout'

// Auth pages
import Login from '@/pages/auth/Login'
import RegisterCompany from '@/pages/auth/RegisterCompany'
import RegisterAgency from '@/pages/auth/RegisterAgency'
import RegisterCandidate from '@/pages/auth/RegisterCandidate'
import VerifyEmail from '@/pages/auth/VerifyEmail'
import Onboarding from '@/pages/candidate/Onboarding'
import OnboardingWizard from '@/pages/onboarding/OnboardingWizard'
import CompanyOnboarding from '@/pages/onboarding/CompanyOnboarding'
import AgencyOnboarding from '@/pages/onboarding/AgencyOnboarding'
import ApplyForm from '@/pages/public/ApplyForm'
import ClaimProfile from '@/pages/candidate/ClaimProfile'

// App pages
import Dashboard from '@/pages/dashboard/Dashboard'
import JobsList from '@/pages/jobs/JobsList'
import CandidatesList from '@/pages/candidates/CandidatesList'
import ActiveCandidatesPage from '@/pages/candidates/ActiveCandidatesPage'
import AllApplications from '@/pages/candidates/AllApplications'
import PipelineBoard from '@/pages/pipeline/PipelineBoard'
import InterviewsList from '@/pages/interviews/InterviewsList'
import Analytics from '@/pages/Analytics'
import CompanyAgencies from '@/pages/agencies/CompanyAgencies'
import AgencyClients from '@/pages/agencies/AgencyClients'
import MyJobs from '@/pages/agency/MyJobs'
import MySubmissions from '@/pages/agency/MySubmissions'
import SubmitCandidate from '@/pages/agency/SubmitCandidate'
import JobSearch from '@/pages/candidate/JobSearch'
import MyApplications from '@/pages/candidate/MyApplications'
import Settings from '@/pages/Settings'
import PassportPage from '@/pages/candidate/Passport'
import Messages from '@/pages/Messages'
import RBACDebugPage from '@/pages/RBACDebugPage'
import TalentPoolsList from '@/pages/talent-pools/TalentPoolsList'
import TalentPoolDetail from '@/pages/talent-pools/TalentPoolDetail'


// ─── React Query client ───────────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// ─── Ant Design theme ─────────────────────────────────────────────────────────
const antTheme = {
  token: {
    colorPrimary: '#1E40AF',
    colorBgBase: '#ffffff',
    borderRadius: 10,
    fontFamily:
      "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    colorBgLayout: '#f8fafc',
    colorText: '#0f172a',
    colorTextSecondary: '#64748b',
    colorBorder: '#e2e8f0',
  },
  components: {
    Layout: {
      siderBg: '#ffffff',
      headerBg: 'rgba(255, 255, 255, 0.8)',
      bodyBg: '#f8fafc',
    },
    Menu: {
      itemBorderRadius: 8,
      itemMarginInline: 8,
      itemSelectedBg: '#eff6ff',
      itemSelectedColor: '#1e40af',
    },
    Card: { 
      borderRadius: 12,
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    },
    Button: {
      borderRadius: 8,
      controlHeight: 38,
      fontWeight: 500,
    },
  },
}

// ─── Utility: wrap a page in AppLayout + ProtectedRoute ──────────────────────
function Protected({
  children,
  roles,
}: {
  children: React.ReactNode
  roles?: string[]
}) {
  return (
    <ProtectedRoute allowedRoles={roles as never}>
      <OnboardingGuard>
        <AppLayout>{children}</AppLayout>
      </OnboardingGuard>
    </ProtectedRoute>
  )
}

// ─── Placeholder for sections not yet built ───────────────────────────────────
function ComingSoon({ label }: { label: string }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: 320,
        background: '#fff',
        borderRadius: 12,
        color: '#8c8c8c',
        gap: 12,
      }}
    >
      <span style={{ fontSize: 56 }}>🚧</span>
      <p style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{label}</p>
      <p style={{ fontSize: 13, margin: 0 }}>This section is under construction</p>
    </div>
  )
}

function Unauthorized() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        gap: 12,
        color: '#8c8c8c',
      }}
    >
      <span style={{ fontSize: 56 }}>🔒</span>
      <p style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Access denied</p>
      <p style={{ fontSize: 13, margin: 0 }}>You don't have permission to view this page.</p>
    </div>
  )
}

// Maps language codes to Ant Design locale objects.
// Add new locales here as support is expanded.
const ANT_LOCALES: Record<string, Locale> = {
  en: enUS,
  hi: hiIN,
}

// Refreshes the persisted user on every app load (keeps permissions/language fresh)
// and syncs the active i18next language with the user's stored preference.
function AuthBootstrap() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const language = useAuthStore((s) => s.user?.language)

  useEffect(() => {
    if (isAuthenticated) fetchMe()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (language && i18n.language !== language) {
      i18n.changeLanguage(language)
    }
  }, [language])

  return null
}

// Wraps children in a ConfigProvider whose locale tracks the user's language.
// Must be inside QueryClientProvider so it can read from the auth store.
function LocaleProvider({ children }: { children: React.ReactNode }) {
  const language = useAuthStore((s) => s.user?.language ?? 'en')
  const antLocale = ANT_LOCALES[language] ?? enUS
  return (
    <ConfigProvider theme={antTheme} locale={antLocale}>
      {children}
    </ConfigProvider>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LocaleProvider>
        <AntApp>
          <BrowserRouter>
            <AuthBootstrap />
            <Routes>
              {/* ── Public / auth ─────────────────────────────────── */}
              <Route path="/login" element={<Login />} />
              <Route path="/register/company" element={<RegisterCompany />} />
              <Route path="/register/agency" element={<RegisterAgency />} />
              <Route path="/register/candidate" element={<RegisterCandidate />} />
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route path="/apply/:token" element={<ApplyForm />} />
              {/* Claim flow: recruiter-added candidates follow this link to claim/link their profile */}
              <Route path="/candidate/claim/:token" element={<ClaimProfile />} />

              {/* ── Onboarding wizard (no AppLayout, no OnboardingGuard) ── */}
              <Route path="/onboarding/wizard" element={
                <ProtectedRoute allowedRoles={['tenant_admin', 'recruiter', 'hiring_manager', 'agency_owner', 'agency_admin', 'agency_recruiter']}>
                  <OnboardingWizard />
                </ProtectedRoute>
              } />

              {/* ── Onboarding (Outside AppLayout) ──────────────── */}
              <Route
                path="/onboarding"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <OnboardingLayout
                      title="Complete your profile"
                      subtitle="Help us find the best opportunities for you"
                    >
                      <Onboarding />
                    </OnboardingLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/company-onboarding"
                element={
                  <ProtectedRoute allowedRoles={['tenant_admin', 'recruiter', 'hiring_manager']}>
                    <OnboardingLayout
                      title="Organisation Setup"
                      subtitle="Configure your organisation profile."
                    >
                      <CompanyOnboarding />
                    </OnboardingLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/agency-onboarding"
                element={
                  <ProtectedRoute allowedRoles={['agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <OnboardingLayout
                      title="Agency Setup"
                      subtitle="Configure your agency profile."
                    >
                      <AgencyOnboarding />
                    </OnboardingLayout>
                  </ProtectedRoute>
                }
              />

              {/* ── Root redirect ─────────────────────────────────── */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

              {/* ── Protected app pages ───────────────────────────── */}
              <Route
                path="/dashboard"
                element={
                  <Protected>
                    <Dashboard />
                  </Protected>
                }
              />

              <Route
                path="/jobs"
                element={
                  <Protected>
                    <JobsList />
                  </Protected>
                }
              />

              <Route
                path="/candidates"
                element={
                  <Protected>
                    <CandidatesList />
                  </Protected>
                }
              />

              <Route
                path="/candidates/active"
                element={
                  <Protected>
                    <ActiveCandidatesPage />
                  </Protected>
                }
              />

              <Route
                path="/candidates/pools"
                element={
                  <Protected>
                    <TalentPoolsList />
                  </Protected>
                }
              />

              <Route
                path="/candidates/pools/:id"
                element={
                  <Protected>
                    <TalentPoolDetail />
                  </Protected>
                }
              />

              <Route
                path="/applications"
                element={
                  <Protected roles={['tenant_admin', 'super_admin', 'recruiter', 'hiring_manager']}>
                    <AllApplications />
                  </Protected>
                }
              />

              <Route
                path="/pipeline"
                element={
                  <Protected>
                    <PipelineBoard />
                  </Protected>
                }
              />

              <Route
                path="/interviews"
                element={
                  <Protected>
                    <InterviewsList />
                  </Protected>
                }
              />

              <Route
                path="/approvals"
                element={
                  <Protected>
                    <ComingSoon label="Approvals" />
                  </Protected>
                }
              />

              <Route
                path="/offers"
                element={
                  <Protected>
                    <Navigate to="/interviews?tab=offers" replace />
                  </Protected>
                }
              />

              <Route
                path="/agencies"
                element={
                  <Protected roles={['tenant_admin', 'super_admin', 'recruiter']}>
                    <CompanyAgencies />
                  </Protected>
                }
              />

              <Route
                path="/agencies/my-jobs"
                element={
                  <Protected roles={['agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <MyJobs />
                  </Protected>
                }
              />
              <Route
                path="/agencies/my-submissions"
                element={
                  <Protected roles={['agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <MySubmissions />
                  </Protected>
                }
              />
              <Route
                path="/agencies/my-clients"
                element={
                  <Protected roles={['agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <AgencyClients />
                  </Protected>
                }
              />
              <Route
                path="/agencies/submit-candidate"
                element={
                  <Protected roles={['agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <SubmitCandidate />
                  </Protected>
                }
              />

              <Route
                path="/analytics"
                element={
                  <Protected roles={['tenant_admin', 'super_admin', 'recruiter', 'hiring_manager', 'agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <Analytics />
                  </Protected>
                }
              />

              <Route
                path="/activity-log"
                element={
                  <Protected>
                    <ComingSoon label="Activity Log" />
                  </Protected>
                }
              />

              <Route
                path="/workflow-templates"
                element={
                  <Protected roles={['tenant_admin', 'super_admin', 'agency_owner', 'agency_admin']}>
                    <ComingSoon label="Workflow Templates" />
                  </Protected>
                }
              />

              <Route
                path="/candidate/jobs"
                element={
                  <Protected roles={['candidate', 'tenant_admin', 'super_admin']}>
                    <JobSearch />
                  </Protected>
                }
              />

              <Route
                path="/candidate/applications"
                element={
                  <Protected roles={['candidate', 'tenant_admin', 'super_admin']}>
                    <MyApplications />
                  </Protected>
                }
              />

              <Route
                path="/settings"
                element={
                  <Protected roles={['tenant_admin', 'super_admin', 'agency_owner', 'agency_admin', 'agency_recruiter']}>
                    <Settings />
                  </Protected>
                }
              />

              <Route
                path="/rbac-debug"
                element={
                  <Protected>
                    <RBACDebugPage />
                  </Protected>
                }
              />

              <Route
                path="/passport"
                element={
                  <Protected roles={['candidate']}>
                    <PassportPage />
                  </Protected>
                }
              />

              <Route
                path="/messages"
                element={
                  <Protected>
                    <Messages />
                  </Protected>
                }
              />

              <Route
                path="/notifications"
                element={
                  <Protected>
                    <ComingSoon label="Notifications" />
                  </Protected>
                }
              />

              {/* ── Misc ──────────────────────────────────────────── */}
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </AntApp>
      </LocaleProvider>
    </QueryClientProvider>
  )
}
