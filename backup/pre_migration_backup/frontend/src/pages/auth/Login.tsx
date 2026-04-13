import { Form, Input, Button, Typography, Divider, Alert } from 'antd'
import { MailOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import AuthLayout from '@/layouts/AuthLayout'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/authStore'
import { canAccessMasterAdmin, resolvePostLoginRoute } from '@/utils/authAccess'

const { Title, Text } = Typography

interface LoginForm {
  email: string
  password: string
}

export default function Login() {
  const { t } = useTranslation(['auth', 'common'])
  const [error, setError] = useState<string | null>(null)
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const setPendingVerificationEmail = useAuthStore(state => state.setPendingVerificationEmail)

  const from = (location.state as { from?: string })?.from

  const handleSubmit = async (values: LoginForm) => {
    setError(null)
    try {
      await login(values.email, values.password)
      const loggedInUser = useAuthStore.getState().user
      const normalizedFrom =
        from && from !== '/login' && from !== '/unauthorized' ? from : null
      const target = normalizedFrom
        ? normalizedFrom.startsWith('/admin')
          ? canAccessMasterAdmin(loggedInUser)
            ? normalizedFrom
            : '/unauthorized'
          : normalizedFrom
        : resolvePostLoginRoute(loggedInUser)
      console.log('[Login] Success — navigating to', target)
      navigate(target, { replace: true })
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: { message?: string; errors?: Record<string, any> } } })?.response?.data
      console.log('[Login] Error response:', errData)
      const errorCode = errData?.errors?.error_code
      console.log('[Login] error_code:', errorCode)

      if (errorCode === 'email_not_verified') {
        const verifyEmail = errData?.errors?.email || values.email
        console.log('[Login] email_not_verified — navigating to /verify-email for', verifyEmail)
        setPendingVerificationEmail(verifyEmail)
        navigate('/verify-email', { replace: true })
        return
      }

      setError(errData?.message ?? t('auth:login_failed', 'Login failed. Please check your credentials.'))
    }
  }

  return (
    <AuthLayout>
      <Title level={3} style={{ marginBottom: 4, textAlign: 'center' }}>
        {t('auth:welcome_back', 'Welcome back')}
      </Title>
      <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 28 }}>
        {t('auth:sign_in_subtitle', 'Sign in to your account')}
      </Text>

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

      <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
        <Form.Item
          name="email"
          label={t('auth:email', 'Email')}
          rules={[
            { required: true, message: t('auth:email_required', 'Email is required') },
            { type: 'email', message: t('auth:email_invalid', 'Enter a valid email') },
          ]}
        >
          <Input
            prefix={<MailOutlined className="text-gray-400" />}
            placeholder={t('auth:email_placeholder', 'you@company.com')}
            size="large"
            autoComplete="email"
            type="email"
            name="email"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label={
            <div className="flex w-full justify-between">
              <span>{t('auth:password', 'Password')}</span>
              <Link
                to="/forgot-password"
                style={{ fontSize: 13, fontWeight: 400 }}
              >
                {t('auth:forgot_password', 'Forgot password?')}
              </Link>
            </div>
          }
          rules={[{ required: true, message: t('auth:password_required', 'Password is required') }]}
        >
          <Input.Password
            prefix={<LockOutlined className="text-gray-400" />}
            placeholder="••••••••"
            size="large"
            autoComplete="current-password"
            name="password"
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 12 }}>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={isLoading}
            style={{ height: 44 }}
          >
            {t('auth:login', 'Sign in')}
          </Button>
        </Form.Item>
      </Form>

      <Divider style={{ margin: '16px 0' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {t('auth:no_account', "Don't have an account?")}
        </Text>
      </Divider>

      <div className="flex flex-col gap-2">
        <Link to="/register/company">
          <Button block size="large" style={{ height: 40 }}>
            {t('auth:register_company', 'Register your company')}
          </Button>
        </Link>
        <Link to="/register/agency">
          <Button block size="large" style={{ height: 40 }}>
            {t('auth:register_agency', 'Register as an agency')}
          </Button>
        </Link>
        <Link to="/register/candidate">
          <Button block size="large" style={{ height: 40 }}>
            {t('auth:register_candidate', 'Register as a candidate')}
          </Button>
        </Link>
      </div>
    </AuthLayout>
  )
}
