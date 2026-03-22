import { useState, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { passportApi } from '@/api/passport'
import { organisationApi } from '@/api/organisation'
import { Spin } from 'antd'
import { isOrganisationSetupIncomplete } from '@/utils/companyOnboarding'

interface OnboardingGuardProps {
  children: React.ReactNode
}

export default function OnboardingGuard({ children }: OnboardingGuardProps) {
  const { user, isAuthenticated } = useAuth()
  const location = useLocation()
  const [loading, setLoading] = useState(true)
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [onboardingPath, setOnboardingPath] = useState('/onboarding')

  useEffect(() => {
    const checkOnboarding = async () => {
      if (!isAuthenticated || !user) {
        setLoading(false)
        return
      }

      try {
        if (user.role === 'candidate') {
          const res = await passportApi.get()
          const passport = res.data.data.passport
          if (passport.completeness_score < 40) {
            setNeedsOnboarding(true)
            setOnboardingPath('/onboarding')
          }
        } else if (['tenant_admin', 'recruiter', 'hiring_manager'].includes(user.role)) {
          // Check if organisation is set up
          const res = await organisationApi.getProfile()
          const org = res.data.data.organisation
          if (isOrganisationSetupIncomplete(org)) {
            setNeedsOnboarding(true)
            setOnboardingPath('/company-onboarding')
          }
        } else if (['agency_owner', 'agency_admin', 'agency_recruiter'].includes(user.role)) {
          const res = await organisationApi.getProfile()
          const org = res.data.data.organisation
          if (isOrganisationSetupIncomplete(org)) {
            setNeedsOnboarding(true)
            setOnboardingPath('/agency-onboarding')
          }
        }
      } catch (err: any) {
        if (err.response?.status === 404) {
          setNeedsOnboarding(true)
          if (user.role === 'candidate') setOnboardingPath('/onboarding')
          else if (['agency_owner', 'agency_admin', 'agency_recruiter'].includes(user.role)) setOnboardingPath('/agency-onboarding')
          else setOnboardingPath('/company-onboarding')
        }
      } finally {
        setLoading(false)
      }
    }

    checkOnboarding()
  }, [isAuthenticated, user])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Spin size="large" tip="Verifying profile..." />
      </div>
    )
  }

  if (needsOnboarding && location.pathname !== onboardingPath) {
    return <Navigate to={onboardingPath} replace />
  }

  return <>{children}</>
}
