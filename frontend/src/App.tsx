// TalentOS Main Application Entry
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
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
import PublicPassportPage from '@/pages/public/PublicPassportPage'
import ClaimProfile from '@/pages/candidate/ClaimProfile'
import PortalAcceptPage from '@/pages/portal/PortalAcceptPage'

// App pages
import Dashboard from '@/pages/dashboard/Dashboard'
import HiringCommandCenter from '@/pages/dashboard/HiringCommandCenter'
import JobsList from '@/pages/jobs/JobsList'
import JobSetupStudio from '@/pages/jobs/JobSetupStudio'
import JobTemplates from '@/pages/jobs/JobTemplates'
import CandidateDatabase from '@/pages/candidates/CandidateDatabase'
import CandidateRelations from '@/pages/candidates/CandidateRelations'
import AllApplications from '@/pages/candidates/AllApplications'
import PipelineBoard from '@/pages/pipeline/PipelineBoard'
import PipelineBoardV2 from '@/pages/pipeline/PipelineBoardV2'
import OfferManagement from '@/pages/offers/OfferManagement'
import InterviewsList from '@/pages/interviews/InterviewsList'
import InterviewCommandCenter from '@/pages/interviews/InterviewCommandCenter'
import InterviewLiveCenter from '@/pages/interviews/InterviewLiveCenter'
import InterviewTypes from '@/pages/interviews/InterviewTypes'
import InterviewTypeConfig from '@/pages/interviews/InterviewTypeConfig'
import InterviewTemplates from '@/pages/interviews/InterviewTemplates'
import InterviewScorecards from '@/pages/interviews/InterviewScorecards'
import InterviewKit from '@/pages/interviews/InterviewKit'
import InterviewFeedbackSubmit from '@/pages/interviews/InterviewFeedbackSubmit'
import InterviewDecisionPanel from '@/pages/interviews/InterviewDecisionPanel'
import RecruiterInterviewDashboard from '@/pages/interviews/RecruiterInterviewDashboard'
import InterviewSchedulingEngine from '@/pages/interviews/InterviewSchedulingEngine'
import RecruiterBulkScheduling from '@/pages/interviews/RecruiterBulkScheduling'
import RecruiterInterviewQueue from '@/pages/interviews/RecruiterInterviewQueue'
import RecruiterProductivityTools from '@/pages/interviews/RecruiterProductivityTools'
import CandidateSelfSchedule from '@/pages/interviews/CandidateSelfSchedule'
import InterviewAutomation from '@/pages/interviews/InterviewAutomation'
import InterviewIntegrations from '@/pages/interviews/InterviewIntegrations'
import InterviewQuestionBank from '@/pages/interviews/InterviewQuestionBank'
import InterviewAIEngine from '@/pages/interviews/InterviewAIEngine'
import InterviewTechnicalEngine from '@/pages/interviews/InterviewTechnicalEngine'
import InterviewHumanEngine from '@/pages/interviews/InterviewHumanEngine'
import InterviewVideoEngine from '@/pages/interviews/InterviewVideoEngine'
import InterviewGroupDiscussionEngine from '@/pages/interviews/InterviewGroupDiscussionEngine'
import InterviewPresentationEngine from '@/pages/interviews/InterviewPresentationEngine'
import InterviewPortfolioReviewEngine from '@/pages/interviews/InterviewPortfolioReviewEngine'
import InterviewAssessmentEngine from '@/pages/interviews/InterviewAssessmentEngine'
import InterviewSequentialRoundEngine from '@/pages/interviews/InterviewSequentialRoundEngine'
import InterviewBarRaiserEngine from '@/pages/interviews/InterviewBarRaiserEngine'
import InterviewPrequalificationEngine from '@/pages/interviews/InterviewPrequalificationEngine'
import InterviewRolePlayEngine from '@/pages/interviews/InterviewRolePlayEngine'
import InterviewAssessmentCenterEngine from '@/pages/interviews/InterviewAssessmentCenterEngine'
import InterviewCampusHiringEngine from '@/pages/interviews/InterviewCampusHiringEngine'
import InterviewMockEngine from '@/pages/interviews/InterviewMockEngine'
import InterviewWalkinDriveEngine from '@/pages/interviews/InterviewWalkinDriveEngine'
import InterviewWhiteboardEngine from '@/pages/interviews/InterviewWhiteboardEngine'
import InterviewScreeningEngine from '@/pages/interviews/InterviewScreeningEngine'
import Analytics from '@/pages/Analytics'
import HiringAIBrainDashboard from '@/pages/analytics/HiringAIBrainDashboard'
import HiringIntelligenceDashboard from '@/pages/analytics/HiringIntelligenceDashboard'
import RecruiterIntelligenceDashboard from '@/pages/analytics/RecruiterIntelligenceDashboard'
import AgencyEventTriggers from '@/pages/workflows/AgencyEventTriggers'
import AgencyOrchestrationEngine from '@/pages/workflows/AgencyOrchestrationEngine'
import AgencyIntelligenceDashboard from '@/pages/analytics/AgencyIntelligenceDashboard'
import UnifiedOperationsDashboard from '@/pages/analytics/UnifiedOperationsDashboard'
import ExecutiveDecisionCenter from '@/pages/analytics/ExecutiveDecisionCenter'
import TalentControlTower from '@/pages/analytics/TalentControlTower'
import SystemIntelligenceMemory from '@/pages/analytics/SystemIntelligenceMemory'
import GovernanceCenter from '@/pages/intelligence/GovernanceCenter'
import AutomationAnalytics from '@/pages/intelligence/AutomationAnalytics'
import IntegrationHub from '@/pages/organisation/IntegrationHub'
import AutonomousHiringEngine from '@/pages/analytics/AutonomousHiringEngine'
import CompanyAgencies from '@/pages/agencies/CompanyAgencies'
import AgencyClients from '@/pages/agencies/AgencyClients'
import MyJobs from '@/pages/agency/MyJobs'
import MySubmissions from '@/pages/agency/MySubmissions'
import SubmitCandidate from '@/pages/agency/SubmitCandidate'
import JobSearch from '@/pages/candidate/JobSearch'
import MyApplications from '@/pages/candidate/MyApplications'
import CandidateCommandCenter from '@/pages/candidate/CandidateCommandCenter'
import CandidateInterviewDashboard from '@/pages/candidate/CandidateInterviewDashboard'
import CandidateInterviewInstructions from '@/pages/candidate/CandidateInterviewInstructions'
import CandidateInterviewHelp from '@/pages/candidate/CandidateInterviewHelp'
import CandidateInterviewNotifications from '@/pages/candidate/CandidateInterviewNotifications'
import CandidateInterviewPreparation from '@/pages/candidate/CandidateInterviewPreparation'
import CandidateInterviewExperience from '@/pages/candidate/CandidateInterviewExperience'
import CandidateInterviewFeedback from '@/pages/candidate/CandidateInterviewFeedback'
import CandidateInterviewResults from '@/pages/candidate/CandidateInterviewResults'
import CandidateInterviewRuntime from '@/pages/candidate/CandidateInterviewRuntime'
import CandidatePrequalification from '@/pages/candidate/CandidatePrequalification'
import CandidateInterviewTimeline from '@/pages/candidate/CandidateInterviewTimeline'
import CandidateInterviewStatus from '@/pages/candidate/CandidateInterviewStatus'
import CandidateInterviewBlocked from '@/pages/candidate/CandidateInterviewBlocked'
import CandidateInterviewExpired from '@/pages/candidate/CandidateInterviewExpired'
import Settings from '@/pages/Settings'
import PassportPage from '@/pages/candidate/Passport'
import CommunicationsPage from '@/pages/communications/CommunicationsPage'
import NotificationsPage from '@/pages/notifications/NotificationsPage'
import TalentPoolsList from '@/pages/talent-pools/TalentPoolsList'
import TalentPoolDetail from '@/pages/talent-pools/TalentPoolDetail'
import PrequalificationList from '@/pages/prequalification/PrequalificationList'
import PrequalificationBuilder from '@/pages/prequalification/PrequalificationBuilder'
import HiringDecisionWorkspace from '@/pages/hdc/HiringDecisionWorkspace'
import IntelligenceHubWorkspace from '@/pages/intelligence/IntelligenceHubWorkspace'
import WorkflowSystemWorkspace from './pages/workflows/WorkflowSystemWorkspace'
import GuidedWorkflowBuilder from './pages/workflows/GuidedWorkflowBuilder'
import AdvancedWorkflowBuilder from './pages/workflows/AdvancedWorkflowBuilder'
import OrchestrationEngine from './pages/workflows/OrchestrationEngine'

import WorkflowTemplatesPage from '@/pages/system/WorkflowTemplatesPage'
import GlobalAutomationOrchestrator from '@/pages/system/GlobalAutomationOrchestrator'
import NotificationsCenterPage from '@/pages/system/NotificationsCenterPage' // legacy demo page
import NotificationControlCenter from '@/pages/settings/NotificationControlCenter'
import CommunicationControlCenter from '@/pages/settings/CommunicationControlCenter'
import ActivityLogPage from '@/pages/system/ActivityLogPage'
import ModuleReadiness from '@/pages/qa/ModuleReadiness'
import AutomationCommandCenter from '@/pages/automation/AutomationCommandCenter'
import AutomationPermissions from '@/pages/intelligence/AutomationPermissions'
import AutomationNotifications from '@/pages/intelligence/AutomationNotifications'
import AutomationTasks from '@/pages/intelligence/AutomationTasks'
import MasterAdminDashboard from '@/pages/admin/MasterAdminDashboard'
import MasterAdminTenants from '@/pages/admin/MasterAdminTenants'
import MasterAdminTenantDetail from '@/pages/admin/MasterAdminTenantDetail'
import MasterAdminSettings from '@/pages/admin/MasterAdminSettings'
import MasterAdminAudit from '@/pages/admin/MasterAdminAudit'
import GlobalSearch from '@/pages/search/GlobalSearch'
import {
  ADMIN_ONLY_ROLES,
  AGENCY_ROLES,
  CANDIDATE_ROLES,
  COMPANY_HIRING_ROLES,
  COMPANY_HR_HIRING_ROLES,
  COMPANY_HR_ROLES,
  COMPANY_ROLES,
  COMPANY_AND_AGENCY_RECRUITER_ROLES,
  NON_CANDIDATE_ROLES,
  RECRUITER_OPERATIONAL_ROLES,
  TENANT_OR_AGENCY_ADMIN_ROLES,
} from '@/config/routeAccess'

// Redirect /prequalification/forms/:id/builder → /interviews/prequalification/forms/:id/builder
function PrequalBuilderRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/interviews/prequalification/forms/${id}/builder`} replace />
}


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
  requireMasterAdmin,
}: {
  children: React.ReactNode
  roles?: string[]
  requireMasterAdmin?: boolean
}) {
  return (
    <ProtectedRoute allowedRoles={roles as never} requireMasterAdmin={requireMasterAdmin}>
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
  const hasHydrated = useAuthStore((s) => s.hasHydrated)
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const language = useAuthStore((s) => s.user?.language)

  useEffect(() => {
    if (hasHydrated && isAuthenticated) fetchMe()
  }, [hasHydrated, isAuthenticated, fetchMe])

  useEffect(() => {
    if (hasHydrated && !isAuthenticated) {
      queryClient.clear()
    }
  }, [hasHydrated, isAuthenticated])

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
              {/* Public passport share link — no auth required */}
              <Route path="/passport/public/:token" element={<PublicPassportPage />} />
              {/* Claim flow: recruiter-added candidates follow this link to claim/link their profile */}
              <Route path="/candidate/claim/:token" element={<ClaimProfile />} />
              <Route path="/portal/accept/:token" element={<PortalAcceptPage />} />

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
                  <ProtectedRoute allowedRoles={AGENCY_ROLES}>
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
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <Dashboard />
                  </Protected>
                }
              />

              <Route
                path="/hiring-command-center"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <HiringCommandCenter />
                  </Protected>
                }
              />
              <Route 
                path="/hiring-ai" 
                element={ 
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}> 
                    <HiringAIBrainDashboard /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/executive-decision" 
                element={ 
                  <Protected roles={COMPANY_HR_ROLES}> 
                    <ExecutiveDecisionCenter /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/control-tower" 
                element={ 
                  <Protected roles={COMPANY_HR_HIRING_ROLES}> 
                    <TalentControlTower /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/system-intelligence" 
                element={ 
                  <Protected roles={COMPANY_HR_ROLES}> 
                    <SystemIntelligenceMemory /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/governance" 
                element={ 
                  <Protected roles={COMPANY_HR_ROLES}> 
                    <GovernanceCenter /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/automation-analytics" 
                element={ 
                  <Protected roles={COMPANY_HR_ROLES}> 
                    <AutomationAnalytics /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/integrations" 
                element={ 
                  <Protected roles={COMPANY_HR_ROLES}> 
                    <IntegrationHub /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/autonomous-hiring" 
                element={ 
                  <Protected roles={COMPANY_HR_HIRING_ROLES}> 
                    <AutonomousHiringEngine /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/unified-operations" 
                element={ 
                  <Protected roles={COMPANY_HR_HIRING_ROLES}> 
                    <UnifiedOperationsDashboard /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/hiring-intelligence" 
                element={ 
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}> 
                    <HiringIntelligenceDashboard /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/agency-intelligence" 
                element={ 
                  <Protected roles={COMPANY_HR_HIRING_ROLES}> 
                    <AgencyIntelligenceDashboard /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/workflows/event-triggers" 
                element={ 
                  <Protected roles={TENANT_OR_AGENCY_ADMIN_ROLES}> 
                    <AgencyEventTriggers /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/workflows/orchestration" 
                element={ 
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}> 
                    <AgencyOrchestrationEngine /> 
                  </Protected> 
                } 
              />
              <Route 
                path="/recruiter-intelligence" 
                element={ 
                  <Protected roles={COMPANY_HIRING_ROLES}> 
                    <RecruiterIntelligenceDashboard /> 
                  </Protected> 
                } 
              />

              <Route
                path="/jobs"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <JobsList />
                  </Protected>
                }
              />

              <Route
                path="/jobs/create"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <JobSetupStudio />
                  </Protected>
                }
              />

              <Route
                path="/jobs/:id/setup"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <JobSetupStudio />
                  </Protected>
                }
              />

              <Route
                path="/jobs/templates"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <JobTemplates />
                  </Protected>
                }
              />

              <Route
                path="/candidates"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <CandidateDatabase />
                  </Protected>
                }
              />

              <Route
                path="/candidates/database"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <CandidateDatabase />
                  </Protected>
                }
              />

              <Route
                path="/candidates/active"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <CandidateDatabase />
                  </Protected>
                }
              />

              <Route
                path="/candidates/leads"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <CandidateRelations />
                  </Protected>
                }
              />

              <Route
                path="/candidates/pools"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <CandidateDatabase />
                  </Protected>
                }
              />

              <Route
                path="/candidates/pools/:id"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <TalentPoolDetail />
                  </Protected>
                }
              />

              <Route
                path="/applications"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <AllApplications />
                  </Protected>
                }
              />

              <Route
                path="/pipeline"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <PipelineBoard />
                  </Protected>
                }
              />

              <Route
                path="/pipeline/v2"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <PipelineBoardV2 />
                  </Protected>
                }
              />

              <Route
                path="/offers"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <OfferManagement />
                  </Protected>
                }
              />

              <Route
                path="/interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewCommandCenter />
                  </Protected>
                }
              />
              <Route
                path="/interviews/dashboard"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <RecruiterInterviewDashboard />
                  </Protected>
                }
              />
              <Route
                path="/interviews/queue"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <RecruiterInterviewQueue />
                  </Protected>
                }
              />
              <Route
                path="/interviews/bulk-scheduling"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <RecruiterBulkScheduling />
                  </Protected>
                }
              />
              <Route
                path="/interviews/productivity"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <RecruiterProductivityTools />
                  </Protected>
                }
              />

              <Route
                path="/interviews/registry"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewsList />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/:id/config"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypeConfig />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/ai-interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/technical-interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/human-interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/screening-interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/sequential-round"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/group-discussion"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/bar-raiser"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/role-play"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/presentation-interview"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/portfolio-review"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/assessment-center"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/campus-hiring"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/mock-interview"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/walkin-drive"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/video-interviews"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/whiteboard-interview"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/assessments"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/prequalification"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTypes />
                  </Protected>
                }
              />
              <Route
                path="/interviews/ai"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewAIEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/technical"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTechnicalEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/human"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewHumanEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/screening"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewScreeningEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/sequential-round"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewSequentialRoundEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/group-discussion"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewGroupDiscussionEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/bar-raiser"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewBarRaiserEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/role-play"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewRolePlayEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/presentation-interview"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewPresentationEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/portfolio-review"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewPortfolioReviewEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/assessment-center"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewAssessmentCenterEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/campus-hiring"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewCampusHiringEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/mock-interview"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewMockEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/walkin-drive"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewWalkinDriveEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/video"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewVideoEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/whiteboard"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewWhiteboardEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/assessments"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewAssessmentEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/prequalification"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewPrequalificationEngine />
                  </Protected>
                }
              />
              <Route
                path="/interviews/types/scorecards"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <Navigate to="/interviews/scorecards" replace />
                  </Protected>
                }
              />

              <Route
                path="/interviews/templates"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewTemplates />
                  </Protected>
                }
              />

              <Route
                path="/interviews/scorecards"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewScorecards />
                  </Protected>
                }
              />

              <Route
                path="/interviews/:id/kit"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewKit />
                  </Protected>
                }
              />

              <Route
                path="/interviews/:id/feedback"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewFeedbackSubmit />
                  </Protected>
                }
              />
              <Route
                path="/interviews/:id/decision"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewDecisionPanel />
                  </Protected>
                }
              />

              <Route
                path="/interviews/scheduling"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewSchedulingEngine />
                  </Protected>
                }
              />

              <Route
                path="/interviews/live"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewLiveCenter />
                  </Protected>
                }
              />

              <Route
                path="/interviews/analytics"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewCommandCenter />
                  </Protected>
                }
              />

              <Route
                path="/interviews/automation"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewAutomation />
                  </Protected>
                }
              />

              <Route
                path="/interviews/integrations"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewIntegrations />
                  </Protected>
                }
              />

              <Route
                path="/interviews/questions"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <InterviewQuestionBank />
                  </Protected>
                }
              />

              <Route path="/interviews/scheduling/self/:token" element={<CandidateSelfSchedule />} />

              {/* Pre-Qualification lives inside the Interviews namespace */}
              <Route
                path="/interviews/prequalification/forms/:id/builder"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <PrequalificationBuilder />
                  </Protected>
                }
              />

              {/* Legacy redirects — keep old URLs working */}
              <Route
                path="/prequalification"
                element={<Navigate to="/interviews?s=prequalification" replace />}
              />
              <Route
                path="/prequalification/forms/:id/builder"
                element={<PrequalBuilderRedirect />}
              />

              <Route
                path="/approvals"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <Navigate to="/hiring-decisions/approvals" replace />
                  </Protected>
                }
              />

              <Route
                path="/offers"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <Navigate to="/hiring-decisions/offer-release" replace />
                  </Protected>
                }
              />

              <Route
                path="/hiring-decisions"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <HiringDecisionWorkspace />
                  </Protected>
                }
              />

              <Route
                path="/hiring-decisions/:section"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <HiringDecisionWorkspace />
                  </Protected>
                }
              />

              <Route
                path="/intelligence"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <IntelligenceHubWorkspace />
                  </Protected>
                }
              />

              <Route
                path="/intelligence/:section"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <IntelligenceHubWorkspace />
                  </Protected>
                }
              />

              <Route
                path="/workflows/:section"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <WorkflowSystemWorkspace />
                  </Protected>
                }
              />
              <Route
                path="/workflows"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <WorkflowSystemWorkspace />
                  </Protected>
                }
              />
              <Route
                path="/workflows/guided-builder"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <GuidedWorkflowBuilder />
                  </Protected>
                }
              />
              <Route
                path="/workflows/advanced-builder"
                element={
                  <Protected roles={ADMIN_ONLY_ROLES}>
                    <AdvancedWorkflowBuilder />
                  </Protected>
                }
              />
              <Route
                path="/workflows/advanced-builder/:id"
                element={
                  <Protected roles={ADMIN_ONLY_ROLES}>
                    <AdvancedWorkflowBuilder />
                  </Protected>
                }
              />

              <Route
                path="/automation-center"
                element={
                  <Protected roles={COMPANY_ROLES}>
                    <AutomationCommandCenter />
                  </Protected>
                }
              />

              <Route
                path="/automation-center/:section"
                element={
                  <Protected roles={COMPANY_ROLES}>
                    <AutomationCommandCenter />
                  </Protected>
                }
              />

              <Route
                path="/automation-permissions"
                element={
                  <Protected roles={COMPANY_HR_ROLES}>
                    <AutomationPermissions />
                  </Protected>
                }
              />

              <Route
                path="/automation-notifications"
                element={
                  <Protected roles={COMPANY_HR_ROLES}>
                    <AutomationNotifications />
                  </Protected>
                }
              />

              <Route
                path="/automation-tasks"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <AutomationTasks />
                  </Protected>
                }
              />

              <Route
                path="/agencies"
                element={
                  <Protected roles={RECRUITER_OPERATIONAL_ROLES}>
                    <CompanyAgencies />
                  </Protected>
                }
              />

              <Route
                path="/agencies/my-jobs"
                element={
                  <Protected roles={AGENCY_ROLES}>
                    <MyJobs />
                  </Protected>
                }
              />
              <Route
                path="/agencies/my-submissions"
                element={
                  <Protected roles={AGENCY_ROLES}>
                    <MySubmissions />
                  </Protected>
                }
              />
              <Route
                path="/agencies/my-clients"
                element={
                  <Protected roles={AGENCY_ROLES}>
                    <AgencyClients />
                  </Protected>
                }
              />
              <Route
                path="/agencies/submit-candidate"
                element={
                  <Protected roles={AGENCY_ROLES}>
                    <SubmitCandidate />
                  </Protected>
                }
              />

              <Route
                path="/analytics"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <Analytics />
                  </Protected>
                }
              />

              <Route
                path="/activity-log"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <ActivityLogPage />
                  </Protected>
                }
              />

              <Route
                path="/qa/module-readiness"
                element={
                  <Protected roles={ADMIN_ONLY_ROLES}>
                    <ModuleReadiness />
                  </Protected>
                }
              />

              <Route
                path="/automation-orchestrator"
                element={
                  <Protected roles={COMPANY_HIRING_ROLES}>
                    <GlobalAutomationOrchestrator />
                  </Protected>
                }
              />

              <Route
                path="/admin"
                element={
                  <Protected requireMasterAdmin>
                    <MasterAdminDashboard />
                  </Protected>
                }
              />
              <Route
                path="/admin/tenants"
                element={
                  <Protected requireMasterAdmin>
                    <MasterAdminTenants />
                  </Protected>
                }
              />
              <Route
                path="/admin/tenants/:id"
                element={
                  <Protected requireMasterAdmin>
                    <MasterAdminTenantDetail />
                  </Protected>
                }
              />
              <Route
                path="/admin/settings"
                element={
                  <Protected requireMasterAdmin>
                    <MasterAdminSettings />
                  </Protected>
                }
              />
              <Route
                path="/admin/audit"
                element={
                  <Protected requireMasterAdmin>
                    <MasterAdminAudit />
                  </Protected>
                }
              />

              <Route
                path="/workflow-templates"
                element={
                  <Protected roles={TENANT_OR_AGENCY_ADMIN_ROLES}>
                    <WorkflowTemplatesPage />
                  </Protected>
                }
              />

              <Route
                path="/candidate/dashboard"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateCommandCenter />
                  </Protected>
                }
              />

              <Route
                path="/candidate/jobs"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <JobSearch />
                  </Protected>
                }
              />

              <Route
                path="/candidate/applications"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <MyApplications />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewDashboard />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/:id/instructions"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewInstructions />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/results"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewResults />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/notifications"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewNotifications />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/help"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewHelp />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/feedback"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewFeedback />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/experience"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewExperience />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/preparation"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewPreparation />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/timeline"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewTimeline />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/:id/runtime"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewRuntime />
                  </Protected>
                }
              />

              <Route
                path="/candidate/prequalification"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidatePrequalification />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/:id/status"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewStatus />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/blocked"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewBlocked />
                  </Protected>
                }
              />

              <Route
                path="/candidate/interviews/expired"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <CandidateInterviewExpired />
                  </Protected>
                }
              />

              <Route
                path="/settings"
                element={
                  <Protected roles={COMPANY_AND_AGENCY_RECRUITER_ROLES}>
                    <Settings />
                  </Protected>
                }
              />

              <Route
                path="/settings/notification-control"
                element={
                  <Protected roles={ADMIN_ONLY_ROLES}>
                    <NotificationControlCenter />
                  </Protected>
                }
              />

              <Route
                path="/settings/communication-control"
                element={
                  <Protected roles={ADMIN_ONLY_ROLES}>
                    <CommunicationControlCenter />
                  </Protected>
                }
              />

              <Route
                path="/passport"
                element={
                  <Protected roles={CANDIDATE_ROLES}>
                    <PassportPage />
                  </Protected>
                }
              />

              <Route
                path="/messages"
                element={<Navigate to="/communications" replace />}
              />

              <Route
                path="/communications"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <CommunicationsPage />
                  </Protected>
                }
              />

              <Route
                path="/notifications"
                element={
                  <Protected roles={NON_CANDIDATE_ROLES}>
                    <NotificationsPage />
                  </Protected>
                }
              />

              {/* ── Misc ──────────────────────────────────────────── */}
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route path="/search" element={<Protected roles={NON_CANDIDATE_ROLES}><GlobalSearch /></Protected>} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </AntApp>
      </LocaleProvider>
    </QueryClientProvider>
  )
}
