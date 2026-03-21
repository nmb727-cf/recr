import { useState, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { passportApi } from '@/api/passport'
import { Spin } from 'antd'

interface OnboardingGuardProps {
  children: React.ReactNode
}

export default function OnboardingGuard({ children }: OnboardingGuardProps) {
  const { user, isAuthenticated } = useAuth()
  const location = useLocation()
  const [loading, setLoading] = useState(true)
  const [needsOnboarding, setNeedsOnboarding] = useState(false)

  useEffect(() => {
    const checkOnboarding = async () => {
      if (isAuthenticated && user?.role === 'candidate') {
        try {
          const res = await passportApi.get()
          const passport = res.data.data.passport
          if (passport.completeness_score < 30) {
            setNeedsOnboarding(true)
          }
        } catch (err: any) {
          if (err.response?.status === 404) {
            setNeedsOnboarding(true)
          }
        } finally {
          setLoading(false)
        }
      } else {
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

  if (needsOnboarding && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }

  return <>{children}</>
}
