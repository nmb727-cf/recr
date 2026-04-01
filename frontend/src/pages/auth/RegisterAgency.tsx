import { Form, Input, Button, Typography, Alert } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, BankOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { cacheKnownAgency } from '@/utils/companyOnboarding'

const { Title, Text } = Typography

interface RegisterForm {
  name: string
  first_name: string
  last_name: string
  email: string
  password: string
  password_confirm: string
}

export default function RegisterAgency() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const setTokens = useAuthStore(state => state.setTokens)
  const setUser = useAuthStore(state => state.setUser)
  const setPendingVerificationEmail = useAuthStore(state => state.setPendingVerificationEmail)

  const handleSubmit = async (values: RegisterForm) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: res } = await authApi.registerAgency({
        name: values.name,
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        password_confirm: values.password_confirm,
      })
      cacheKnownAgency({
        agency_tenant_id: res.data.user.tenant_id,
        name: values.name,
        email: values.email,
      })
      setTokens(res.data.access_token, res.data.refresh_token)
      setUser(res.data.user)
      setPendingVerificationEmail(values.email)
      navigate('/verify-email')
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: { message?: string; errors?: Record<string, string | string[]> } } })
        ?.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors) {
        const errorMessages = Object.entries(fieldErrors).map(([field, error]) => {
          const message = Array.isArray(error) ? error[0] : error
          return `${field}: ${message}`
        })
        setError(errorMessages.join(' | '))
      } else {
        setError(errData?.message ?? 'Registration failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Title level={3} style={{ marginBottom: 4, textAlign: 'center' }}>
        Create your agency account
      </Title>
      <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 28 }}>
        Start managing clients and submissions
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

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        requiredMark={false}
      >
        <Form.Item
          name="first_name"
          label="First name"
          rules={[{ required: true, message: 'First name is required' }]}
          style={{ display: 'inline-block', width: 'calc(50% - 6px)', marginRight: 12 }}
        >
          <Input
            prefix={<UserOutlined className="text-gray-400" />}
            placeholder="Jane"
            size="large"
            autoComplete="given-name"
          />
        </Form.Item>
        <Form.Item
          name="last_name"
          label="Last name"
          rules={[{ required: true, message: 'Last name is required' }]}
          style={{ display: 'inline-block', width: 'calc(50% - 6px)' }}
        >
          <Input
            prefix={<UserOutlined className="text-gray-400" />}
            placeholder="Smith"
            size="large"
            autoComplete="family-name"
          />
        </Form.Item>

        <Form.Item
          name="name"
          label="Agency name"
          rules={[{ required: true, message: 'Agency name is required' }]}
        >
          <Input
            prefix={<BankOutlined className="text-gray-400" />}
            placeholder="TalentBridge Partners"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="email"
          label="Work email"
          rules={[
            { required: true, message: 'Email is required' },
            { type: 'email', message: 'Enter a valid email' },
          ]}
        >
          <Input
            prefix={<MailOutlined className="text-gray-400" />}
            placeholder="jane@agency.com"
            size="large"
            autoComplete="email"
            type="email"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="Password"
          rules={[
            { required: true, message: 'Password is required' },
            { min: 8, message: 'At least 8 characters' },
            {
              pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
              message: 'Must include uppercase, lowercase and a number',
            },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined className="text-gray-400" />}
            placeholder="Min. 8 characters"
            size="large"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="password_confirm"
          label="Confirm password"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) return Promise.resolve()
                return Promise.reject(new Error('Passwords do not match'))
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined className="text-gray-400" />}
            placeholder="Re-enter password"
            size="large"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 12, marginTop: 4 }}>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={isLoading}
            style={{ height: 44 }}
          >
            Create account
          </Button>
        </Form.Item>
      </Form>

      <Text type="secondary" style={{ display: 'block', textAlign: 'center', fontSize: 13 }}>
        Already have an account?{' '}
        <Link to="/login" style={{ color: '#1890ff' }}>
          Sign in
        </Link>
      </Text>
    </AuthLayout>
  )
}
