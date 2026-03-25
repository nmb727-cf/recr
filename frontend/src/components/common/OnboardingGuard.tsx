import { useState, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { passportApi } from '@/api/passport'
import { organisationApi } from '@/api/organisation'
import { Spin } from 'antd'

interface OnboardingGuardProps {
  children: React.ReactNode
}

const COMPANY_ROLES = ['tenant_admin', 'recruiter', 'hiring_manager']
const AGENCY_ROLES = ['agency_owner', 'agency_admin', 'agency_recruiter']

export default function OnboardingGuard({ children }: OnboardingGuardProps) {
  const { user, isAuthenticated } = useAuth()
  const location = useLocation()
  const [loading, setLoading] = useState(true)
  const [redirectTo, setRedirectTo] = useState<string | null>(null)

  useEffect(() => {
    const check = async () => {
      if (!isAuthenticated || !user) {
        setLoading(false)
        return
      }

      // Step 1: Email must be verified
      if (!user.email_verified) {
        setRedirectTo('/verify-email')
        setLoading(false)
        return
      }

      try {
        if (user.role === 'candidate') {
          const res = await passportApi.get()
          const passport = res.data.data.passport
          if (passport.completeness_score < 40) {
            setRedirectTo('/onboarding')
          }
        } else if (COMPANY_ROLES.includes(user.role) || AGENCY_ROLES.includes(user.role)) {
          // Step 2: Onboarding wizard must be completed (checked via org metadata)
          const res = await organisationApi.getProfile()
          const org = res.data.data.organisation
          if (!org?.metadata?.onboarding_completed) {
            setRedirectTo('/onboarding/wizard')
          }
        }
      } catch (err: any) {
        if (err.response?.status === 404) {
          if (user.role === 'candidate') setRedirectTo('/onboarding')
          else setRedirectTo('/onboarding/wizard')
        }
      } finally {
        setLoading(false)
      }
    }

    check()
  }, [isAuthenticated, user])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Spin size="large" tip="Verifying profile..." />
      </div>
    )
  }

  if (redirectTo && location.pathname !== redirectTo) {
    return <Navigate to={redirectTo} replace />
  }

  return <>{children}</>
}
