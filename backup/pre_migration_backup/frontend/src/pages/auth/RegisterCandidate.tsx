import { Form, Input, Button, Typography, Alert, Row, Col, Select } from 'antd'
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { TIMEZONES } from '@/utils/locale'

const { Title, Text } = Typography

interface RegisterForm {
  first_name: string
  last_name: string
  email: string
  phone?: string
  timezone: string
  password: string
  password_confirm: string
}

export default function RegisterCandidate() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const setTokens = useAuthStore(state => state.setTokens)
  const setUser = useAuthStore(state => state.setUser)

  const handleSubmit = async (values: RegisterForm) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: res } = await authApi.registerCandidate({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        password_confirm: values.password_confirm,
        phone: values.phone,
        timezone: values.timezone,
      })
      setTokens(res.data.access_token, res.data.refresh_token)
      setUser(res.data.user)
      navigate('/dashboard')
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
        Create your profile
      </Title>
      <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 28 }}>
        Find your next opportunity
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
        layout="vertical" 
        onFinish={handleSubmit} 
        requiredMark={false}
        initialValues={{ timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' }}
      >
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              name="first_name"
              label="First name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input
                prefix={<UserOutlined className="text-gray-400" />}
                placeholder="Jane"
                size="large"
                autoComplete="given-name"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="last_name"
              label="Last name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Doe" size="large" autoComplete="family-name" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Email is required' },
            { type: 'email', message: 'Enter a valid email address' },
          ]}
        >
          <Input
            prefix={<MailOutlined className="text-gray-400" />}
            placeholder="jane@example.com"
            size="large"
            autoComplete="email"
            type="email"
            name="email"
          />
        </Form.Item>

        <Form.Item
          name="timezone"
          label="Timezone"
          rules={[{ required: true, message: 'Required' }]}
        >
          <Select
            size="large"
            placeholder="Select timezone"
            suffixIcon={<ClockCircleOutlined className="text-gray-400" />}
            showSearch
            optionFilterProp="label"
            options={TIMEZONES}
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
            placeholder="••••••••"
            size="large"
            autoComplete="new-password"
            name="password"
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
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error('Passwords do not match'))
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined className="text-gray-400" />}
            placeholder="••••••••"
            size="large"
            autoComplete="new-password"
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
