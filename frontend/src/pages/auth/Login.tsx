import { Form, Input, Button, Typography, Divider, Alert } from 'antd'
import { MailOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { useAuth } from '@/hooks/useAuth'

const { Title, Text } = Typography

interface LoginForm {
  email: string
  password: string
}

export default function Login() {
  const [error, setError] = useState<string | null>(null)
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string })?.from ?? '/dashboard'

  const handleSubmit = async (values: LoginForm) => {
    setError(null)
    try {
      await login(values.email, values.password)
      navigate(from, { replace: true })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Login failed. Please check your credentials.'
      setError(msg)
    }
  }

  return (
    <AuthLayout>
      <Title level={3} style={{ marginBottom: 4, textAlign: 'center' }}>
        Welcome back
      </Title>
      <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 28 }}>
        Sign in to your account
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
          label="Email"
          rules={[
            { required: true, message: 'Email is required' },
            { type: 'email', message: 'Enter a valid email' },
          ]}
        >
          <Input
            prefix={<MailOutlined className="text-gray-400" />}
            placeholder="you@company.com"
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
              <span>Password</span>
              <Link
                to="/forgot-password"
                style={{ fontSize: 13, fontWeight: 400 }}
              >
                Forgot password?
              </Link>
            </div>
          }
          rules={[{ required: true, message: 'Password is required' }]}
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
            Sign in
          </Button>
        </Form.Item>
      </Form>

      <Divider style={{ margin: '16px 0' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Don't have an account?
        </Text>
      </Divider>

      <div className="flex flex-col gap-2">
        <Link to="/register/company">
          <Button block size="large" style={{ height: 40 }}>
            Register your company
          </Button>
        </Link>
        <Link to="/register/agency">
          <Button block size="large" style={{ height: 40 }}>
            Register as an agency
          </Button>
        </Link>
        <Link to="/register/candidate">
          <Button block size="large" style={{ height: 40 }}>
            Register as a candidate
          </Button>
        </Link>
      </div>
    </AuthLayout>
  )
}
