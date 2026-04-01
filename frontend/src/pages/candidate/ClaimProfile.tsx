/**
 * CandidateClaimProfile — /candidate/claim/:token
 * =================================================
 * Handles Source 1 (company/agency added a candidate and sent them a claim link)
 * and can also be the final step of Source 2 (apply-link submission with
 * account creation).
 *
 * Flow:
 *  1. Fetch claim info (GET /api/v1/candidates/claim/<token>/)
 *     • Validates token server-side; returns prefilled name/email/phone.
 *     • If already claimed → show success message.
 *
 *  2. If the visitor is already authenticated with a matching identity:
 *     • Auto-submit the link POST immediately.
 *
 *  3. If a user account already exists (identity check):
 *     • Show Login panel (email prefilled, forgot-password link visible).
 *
 *  4. If no user account exists:
 *     • Show Signup panel (name/email/phone prefilled from claim data).
 *
 *  5. After successful auth → POST /api/v1/candidates/claim/<token>/
 *     • Backend links the user account to the candidate record.
 *     • Redirect to /onboarding so the candidate can enrich their profile.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Card, Form, Input, Button, Typography, Alert, Divider, Spin, Space,
} from 'antd'
import {
  UserOutlined, LockOutlined, PhoneOutlined, CheckCircleFilled,
  WarningOutlined,
} from '@ant-design/icons'
import { candidatesApi } from '@/api/candidates'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useAuth } from '@/hooks/useAuth'
import type { RegisterCandidatePayload } from '@/types'

const { Title, Text, Paragraph } = Typography

interface ClaimInfo {
  first_name: string
  last_name: string
  email: string
  phone: string
  current_title: string
  current_company: string
  account_status: string
  already_claimed: boolean
}

type PanelMode = 'loading' | 'already_claimed' | 'login' | 'signup' | 'linking' | 'done' | 'error'

export default function ClaimProfile() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const storeLogin = useAuthStore((s) => s.login)

  const [claimInfo, setClaimInfo] = useState<ClaimInfo | null>(null)
  const [mode, setMode] = useState<PanelMode>('loading')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [loginForm] = Form.useForm()
  const [signupForm] = Form.useForm()

  // ── Step 1: Fetch claim info ──────────────────────────────────────────────
  useEffect(() => {
    if (!token) return
    ;(async () => {
      try {
        const res = await candidatesApi.getClaimInfo(token)
        const info: ClaimInfo = res.data.data.candidate
        setClaimInfo(info)

        if (info.already_claimed) {
          setMode('already_claimed')
          return
        }

        // ── Step 2: Auto-link if already authenticated with matching identity ─
        if (user) {
          const emailMatch =
            user.email && info.email && user.email.toLowerCase() === info.email.toLowerCase()
          const phoneMatch =
            (user as any).phone && info.phone && (user as any).phone === info.phone
          if (emailMatch || phoneMatch) {
            await doLink(token)
            return
          }
        }

        // ── Step 3 vs 4: Check if a user account already exists ──────────────
        const identityRes = await candidatesApi.checkIdentity({
          email: info.email,
          phone: info.phone,
        })
        const { user_exists } = identityRes.data.data

        setMode(user_exists ? 'login' : 'signup')
      } catch (err: any) {
        const msg =
          err.response?.data?.message || 'This claim link is invalid or has expired.'
        setErrorMsg(msg)
        setMode('error')
      }
    })()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, user])

  // ── Step 5: POST claim link ───────────────────────────────────────────────
  async function doLink(claimToken: string) {
    setMode('linking')
    try {
      await candidatesApi.claimProfile(claimToken)
      setMode('done')
      // Give the user a moment to read the success message then redirect
      setTimeout(() => navigate('/onboarding', { replace: true }), 1800)
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to link profile. Please try again.'
      setErrorMsg(msg)
      setMode('error')
    }
  }

  // ── Login handler ─────────────────────────────────────────────────────────
  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      // Use the store login so tokens are persisted and the http client is
      // immediately authorised for the subsequent claim POST.
      await storeLogin(values.email, values.password)
      await doLink(token!)
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Login failed. Check your credentials.'
      setErrorMsg(msg)
    } finally {
      setLoading(false)
    }
  }

  // ── Signup handler ────────────────────────────────────────────────────────
  const handleSignup = async (values: {
    first_name: string
    last_name: string
    email: string
    phone: string
    password: string
    confirm_password: string
  }) => {
    if (values.password !== values.confirm_password) {
      signupForm.setFields([{ name: 'confirm_password', errors: ['Passwords do not match'] }])
      return
    }
    setLoading(true)
    try {
      const payload: RegisterCandidatePayload = {
        email: values.email,
        password: values.password,
        password_confirm: values.confirm_password,
        first_name: values.first_name,
        last_name: values.last_name,
      }
      // Source 3 identity guard: backend returns needs_login if email already exists
      const signupRes = await authApi.registerCandidate(payload)
      const signupData = signupRes.data?.data as any
      if (signupData?.needs_login) {
        setErrorMsg(
          'An account with this email already exists. Please use the login form below.'
        )
        setMode('login')
        return
      }
      // Persist tokens from registration response so the claim POST is authorised
      if (signupData?.access_token) {
        const setTokens = useAuthStore.getState().setTokens
        setTokens(signupData.access_token, signupData.refresh_token)
      }
      // Account created — now link to the candidate record
      await doLink(token!)
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Signup failed. Please try again.'
      setErrorMsg(msg)
    } finally {
      setLoading(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  if (mode === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <Spin size="large" />
      </div>
    )
  }

  if (mode === 'error') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <Card className="w-full max-w-md rounded-3xl shadow-soft-lg">
          <div className="text-center p-4">
            <WarningOutlined className="text-amber-500 text-5xl mb-4" />
            <Title level={4} className="!mb-2">Link Unavailable</Title>
            <Paragraph className="text-slate-500">{errorMsg}</Paragraph>
            <Button type="primary" onClick={() => navigate('/login')}>
              Go to Login
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  if (mode === 'already_claimed' || mode === 'done') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <Card className="w-full max-w-md rounded-3xl shadow-soft-lg">
          <div className="text-center p-4">
            <CheckCircleFilled className="text-emerald-500 text-5xl mb-4" />
            <Title level={4} className="!mb-2">Profile Claimed!</Title>
            <Paragraph className="text-slate-500">
              {mode === 'done'
                ? 'Your profile has been linked. Redirecting you to complete your onboarding…'
                : 'This profile has already been claimed. Log in to access your dashboard.'}
            </Paragraph>
            {mode === 'already_claimed' && (
              <Button type="primary" onClick={() => navigate('/login')}>
                Go to Login
              </Button>
            )}
          </div>
        </Card>
      </div>
    )
  }

  if (mode === 'linking') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Linking your profile…</Text>
        </Space>
      </div>
    )
  }

  const subtitle =
    claimInfo?.current_title && claimInfo?.current_company
      ? `${claimInfo.current_title} at ${claimInfo.current_company}`
      : claimInfo?.current_title || ''

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
      <Card className="w-full max-w-md rounded-3xl shadow-soft-lg border border-slate-100">
        <div className="text-center mb-6">
          <div className="h-16 w-16 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <UserOutlined style={{ fontSize: 28 }} />
          </div>
          <Title level={3} className="!mb-1 tracking-tight">
            {mode === 'login' ? 'Log in to claim your profile' : 'Create your account'}
          </Title>
          {claimInfo && (
            <Text className="text-slate-500 block">
              {claimInfo.first_name} {claimInfo.last_name}
              {subtitle ? ` · ${subtitle}` : ''}
            </Text>
          )}
        </div>

        {errorMsg && (
          <Alert
            type="warning"
            message={errorMsg}
            className="mb-4 rounded-xl"
            closable
            onClose={() => setErrorMsg('')}
          />
        )}

        {/* ── Login panel ─────────────────────────────────────────────── */}
        {mode === 'login' && (
          <Form
            form={loginForm}
            layout="vertical"
            initialValues={{ email: claimInfo?.email }}
            onFinish={handleLogin}
            requiredMark={false}
          >
            <Form.Item name="email" label="Email" rules={[{ required: true }]}>
              <Input
                prefix={<UserOutlined className="text-slate-300" />}
                placeholder="your@email.com"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true }]}>
              <Input.Password
                prefix={<LockOutlined className="text-slate-300" />}
                placeholder="Your password"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              loading={loading}
              className="h-12 rounded-xl font-bold bg-blue-600 border-none"
            >
              Log In & Claim Profile
            </Button>
            <div className="text-center mt-4 space-y-2">
              <div>
                <Link to="/forgot-password" className="text-blue-500 text-sm">
                  Forgot password?
                </Link>
              </div>
              <div>
                <Button
                  type="link"
                  className="text-slate-400 text-sm p-0"
                  onClick={() => setMode('signup')}
                >
                  Don't have an account? Sign up
                </Button>
              </div>
            </div>
          </Form>
        )}

        {/* ── Signup panel ────────────────────────────────────────────── */}
        {mode === 'signup' && (
          <Form
            form={signupForm}
            layout="vertical"
            initialValues={{
              first_name: claimInfo?.first_name,
              last_name: claimInfo?.last_name,
              email: claimInfo?.email,
              phone: claimInfo?.phone,
            }}
            onFinish={handleSignup}
            requiredMark={false}
          >
            <div className="grid grid-cols-2 gap-3">
              <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
                <Input placeholder="First" className="h-11 rounded-xl" />
              </Form.Item>
              <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
                <Input placeholder="Last" className="h-11 rounded-xl" />
              </Form.Item>
            </div>
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true }, { type: 'email' }]}
            >
              <Input
                prefix={<UserOutlined className="text-slate-300" />}
                placeholder="your@email.com"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Form.Item name="phone" label="Phone">
              <Input
                prefix={<PhoneOutlined className="text-slate-300" />}
                placeholder="+91 9876543210"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
              <Input.Password
                prefix={<LockOutlined className="text-slate-300" />}
                placeholder="Min. 8 characters"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Form.Item
              name="confirm_password"
              label="Confirm Password"
              rules={[{ required: true }]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-slate-300" />}
                placeholder="Repeat your password"
                className="h-11 rounded-xl"
              />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              loading={loading}
              className="h-12 rounded-xl font-bold bg-blue-600 border-none"
            >
              Create Account & Claim Profile
            </Button>
            <Divider className="my-4" />
            <div className="text-center">
              <Button
                type="link"
                className="text-slate-400 text-sm p-0"
                onClick={() => setMode('login')}
              >
                Already have an account? Log in
              </Button>
            </div>
          </Form>
        )}
      </Card>
    </div>
  )
}
