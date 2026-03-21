import { Form, Input, Button, Typography, Alert, Row, Col } from 'antd'
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  PhoneOutlined,
} from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography

interface RegisterForm {
  first_name: string
  last_name: string
  email: string
  phone?: string
  password: string
  confirm_password: string
}

export default function RegisterCandidate() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()

  const handleSubmit = async (values: RegisterForm) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: res } = await authApi.registerCandidate({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        phone: values.phone,
      })
      setTokens(res.data.access_token, res.data.refresh_token)
      setUser(res.data.user)
      navigate('/dashboard')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Registration failed. Please try again.'
      setError(msg)
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

      <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
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
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="last_name"
              label="Last name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Doe" size="large" />
            </Form.Item>
          </Col>
        </Row>

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
            placeholder="jane@example.com"
            size="large"
          />
        </Form.Item>

        <Form.Item name="phone" label="Phone (optional)">
          <Input
            prefix={<PhoneOutlined className="text-gray-400" />}
            placeholder="+91 98765 43210"
            size="large"
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
            placeholder="••••••••"
            size="large"
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
