import { Form, Input, Button, Typography, Alert, Select } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, BankOutlined, GlobalOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography

// Common countries — extend as needed
const COUNTRIES = [
  { code: 'IN', name: 'India' },
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'AU', name: 'Australia' },
  { code: 'CA', name: 'Canada' },
  { code: 'SG', name: 'Singapore' },
  { code: 'AE', name: 'UAE' },
  { code: 'DE', name: 'Germany' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'FR', name: 'France' },
]

interface RegisterForm {
  name: string
  company_name: string
  email: string
  country_code: string
  password: string
  confirm_password: string
}

export default function RegisterCompany() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()

  const handleSubmit = async (values: RegisterForm) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: res } = await authApi.registerCompany({
        name: values.name,
        company_name: values.company_name,
        email: values.email,
        password: values.password,
        country_code: values.country_code,
      })
      setTokens(res.data.access_token, res.data.refresh_token)
      setUser(res.data.user)
      navigate('/dashboard')
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } })
        ?.response?.data
      // Show first field-level error if present
      const fieldErrors = errData?.errors
      const firstFieldError = fieldErrors
        ? Object.values(fieldErrors)[0]?.[0]
        : undefined
      setError(firstFieldError ?? errData?.message ?? 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Title level={3} style={{ marginBottom: 4, textAlign: 'center' }}>
        Create your company account
      </Title>
      <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 28 }}>
        Start hiring smarter today
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

      <Form layout="vertical" onFinish={handleSubmit} requiredMark={false} initialValues={{ country_code: 'IN' }}>
        <Form.Item
          name="name"
          label="Your full name"
          rules={[{ required: true, message: 'Your name is required' }]}
        >
          <Input
            prefix={<UserOutlined className="text-gray-400" />}
            placeholder="John Smith"
            size="large"
            autoComplete="name"
          />
        </Form.Item>

        <Form.Item
          name="company_name"
          label="Company name"
          rules={[{ required: true, message: 'Company name is required' }]}
        >
          <Input
            prefix={<BankOutlined className="text-gray-400" />}
            placeholder="Acme Corp"
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
            placeholder="john@company.com"
            size="large"
            autoComplete="email"
          />
        </Form.Item>

        <Form.Item
          name="country_code"
          label="Country"
          rules={[{ required: true, message: 'Country is required' }]}
        >
          <Select
            size="large"
            placeholder="Select country"
            suffixIcon={<GlobalOutlined className="text-gray-400" />}
            showSearch
            optionFilterProp="label"
            options={COUNTRIES.map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))}
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="Password"
          rules={[
            { required: true, message: 'Password is required' },
            { min: 8, message: 'At least 8 characters' },
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
          name="confirm_password"
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
