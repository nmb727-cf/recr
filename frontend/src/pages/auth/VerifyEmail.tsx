import { useState, useEffect, useRef } from 'react'
import { Button, Typography, Alert } from 'antd'
import { MailOutlined, ReloadOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography
const OTP_LENGTH = 6
const RESEND_COOLDOWN = 60

export default function VerifyEmail() {
  const navigate = useNavigate()
  const user = useAuthStore(state => state.user)
  const setUser = useAuthStore(state => state.setUser)
  const setTokens = useAuthStore(state => state.setTokens)
  const pendingEmail = useAuthStore(state => state.pendingVerificationEmail)
  const setPendingEmail = useAuthStore(state => state.setPendingVerificationEmail)

  const email = pendingEmail || user?.email || ''

  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(''))
  const [error, setError] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [verified, setVerified] = useState(false)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Focus first box on mount
  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  // Cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return
    const id = setInterval(() => setResendCooldown(c => c - 1), 1000)
    return () => clearInterval(id)
  }, [resendCooldown])

  // Auto-submit when all digits are filled
  useEffect(() => {
    const code = digits.join('')
    if (code.length === OTP_LENGTH && !isVerifying) {
      handleVerify(code)
    }
  }, [digits])

  const handleVerify = async (code: string) => {
    console.log('[OTP] Verification started for:', email)
    if (!email) {
      console.warn('[OTP] No email in session — redirecting to login')
      setError('Session expired. Please sign up again.')
      return
    }
    setError(null)
    setIsVerifying(true)
    try {
      console.log('[OTP] Sending verify request...')
      const { data: res } = await authApi.verifyOTP(email, code)
      console.log('[OTP] Verify response received:', { email_verified: res.data.user.email_verified, role: res.data.user.role })

      // Store fresh tokens issued by the backend on successful verification
      setTokens(res.data.access_token, res.data.refresh_token)
      console.log('[OTP] Tokens stored')

      setUser(res.data.user)
      console.log('[OTP] Auth store updated, email_verified:', res.data.user.email_verified)

      setPendingEmail(null)
      setVerified(true)

      // Brief success state, then route based on role
      setTimeout(() => {
        const role = res.data.user.role
        const dest = role === 'candidate' ? '/onboarding' : '/onboarding/wizard'
        console.log('[OTP] Redirecting to', dest, '(role:', role + ')')
        navigate(dest, { replace: true })
      }, 1200)
    } catch (err: any) {
      console.error('[OTP] Verification failed:', err?.response?.data ?? err)
      setError(
        err?.response?.data?.message || 'Invalid or expired code. Try again.'
      )
      // Clear inputs on error so the user can re-enter
      setDigits(Array(OTP_LENGTH).fill(''))
      inputRefs.current[0]?.focus()
    } finally {
      setIsVerifying(false)
    }
  }

  const handleResend = async () => {
    if (!email || resendCooldown > 0) return
    setIsResending(true)
    setError(null)
    try {
      await authApi.sendOTP(email)
      setResendCooldown(RESEND_COOLDOWN)
      setDigits(Array(OTP_LENGTH).fill(''))
      inputRefs.current[0]?.focus()
    } catch {
      setError('Failed to resend. Please try again.')
    } finally {
      setIsResending(false)
    }
  }

  const handleDigitInput = (index: number, value: string) => {
    // Handle paste of full OTP
    if (value.length > 1) {
      const pasted = value.replace(/\D/g, '').slice(0, OTP_LENGTH)
      const next = Array(OTP_LENGTH).fill('')
      pasted.split('').forEach((c, i) => { next[i] = c })
      setDigits(next)
      const focusIndex = Math.min(pasted.length, OTP_LENGTH - 1)
      inputRefs.current[focusIndex]?.focus()
      return
    }

    const digit = value.replace(/\D/g, '')
    const next = [...digits]
    next[index] = digit
    setDigits(next)

    if (digit && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  if (verified) {
    return (
      <AuthLayout>
        <div style={{ textAlign: 'center', padding: '32px 0' }}>
          <CheckCircleOutlined style={{ fontSize: 56, color: '#52c41a', marginBottom: 16 }} />
          <Title level={3} style={{ marginBottom: 8 }}>Email verified!</Title>
          <Text type="secondary">Setting up your workspace...</Text>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: '#eff6ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
        }}>
          <MailOutlined style={{ fontSize: 24, color: '#1e40af' }} />
        </div>
        <Title level={3} style={{ marginBottom: 4 }}>Check your email</Title>
        <Text type="secondary">
          We sent a 6-digit code to
        </Text>
        <br />
        <Text strong style={{ color: '#0f172a' }}>{email}</Text>
      </div>

      {error && (
        <Alert
          type="error"
          message={error}
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 20 }}
        />
      )}

      {/* OTP digit boxes */}
      <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 24 }}>
        {digits.map((d, i) => (
          <input
            key={i}
            ref={el => { inputRefs.current[i] = el }}
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={d}
            onChange={e => handleDigitInput(i, e.target.value)}
            onKeyDown={e => handleKeyDown(i, e)}
            disabled={isVerifying}
            style={{
              width: 48,
              height: 56,
              textAlign: 'center',
              fontSize: 22,
              fontWeight: 600,
              border: `2px solid ${error ? '#ff4d4f' : d ? '#1e40af' : '#e2e8f0'}`,
              borderRadius: 10,
              outline: 'none',
              background: isVerifying ? '#f8fafc' : '#ffffff',
              color: '#0f172a',
              transition: 'border-color 0.2s',
              cursor: isVerifying ? 'not-allowed' : 'text',
            }}
            onFocus={e => { e.target.style.borderColor = '#1e40af' }}
            onBlur={e => { if (!d) e.target.style.borderColor = '#e2e8f0' }}
          />
        ))}
      </div>

      {isVerifying && (
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 16 }}>
          Verifying...
        </Text>
      )}

      <div style={{ textAlign: 'center' }}>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Didn't receive it?{' '}
        </Text>
        <Button
          type="link"
          size="small"
          icon={<ReloadOutlined />}
          loading={isResending}
          disabled={resendCooldown > 0 || isResending}
          onClick={handleResend}
          style={{ padding: '0 4px', fontSize: 13 }}
        >
          {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
        </Button>
      </div>
    </AuthLayout>
  )
}
