import { Form, Input, Button, Typography, Alert, Select, Row, Col } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, BankOutlined, GlobalOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthLayout from '@/layouts/AuthLayout'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { cacheCompanySignupPrefill } from '@/utils/companyOnboarding'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'

const { Title, Text } = Typography

interface RegisterForm {
  name: string // Company Name
  first_name: string
  last_name: string
  email: string
  country_code: string
  timezone: string
  password: string
  password_confirm: string
}

export default function RegisterCompany() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const setTokens = useAuthStore(state => state.setTokens)
  const setUser = useAuthStore(state => state.setUser)

  const handleSubmit = async (values: RegisterForm) => {
    setError(null)
    setIsLoading(true)
    try {
      const { data: res } = await authApi.registerCompany({
        name: values.name,
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        password_confirm: values.password_confirm,
        country_code: values.country_code,
        timezone: values.timezone,
      })
      cacheCompanySignupPrefill({
        name: `${values.first_name} ${values.last_name}`,
        company_name: values.name,
        email: values.email,
        country_code: values.country_code,
      })
      setTokens(res.data.access_token, res.data.refresh_token)
      setUser(res.data.user)
      navigate('/dashboard')
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: { message?: string; errors?: Record<string, string | string[]> } } })
        ?.response?.data
      
      const fieldErrors = errData?.errors
      if (fieldErrors) {
        // Collect all field errors into a single string
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

  const handleCountryChange = (val: string) => {
    if (val === 'IN') form.setFieldsValue({ timezone: 'Asia/Kolkata' })
    if (val === 'US') form.setFieldsValue({ timezone: 'America/New_York' })
    if (val === 'GB') form.setFieldsValue({ timezone: 'Europe/London' })
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

      <Form 
        form={form}
        layout="vertical" 
        onFinish={handleSubmit} 
        requiredMark={false} 
        initialValues={{ country_code: 'IN', timezone: 'Asia/Kolkata' }}
      >
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              name="first_name"
              label="First name"
              rules={[{ required: true, message: 'First name is required' }]}
            >
              <Input
                prefix={<UserOutlined className="text-gray-400" />}
                placeholder="John"
                size="large"
                autoComplete="given-name"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="last_name"
              label="Last name"
              rules={[{ required: true, message: 'Last name is required' }]}
            >
              <Input
                prefix={<UserOutlined className="text-gray-400" />}
                placeholder="Smith"
                size="large"
                autoComplete="family-name"
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="name"
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
            type="email"
            name="email"
          />
        </Form.Item>

        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              name="country_code"
              label="Country"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Select
                size="large"
                placeholder="Select country"
                suffixIcon={<GlobalOutlined className="text-gray-400" />}
                showSearch
                optionFilterProp="label"
                onChange={handleCountryChange}
                options={COUNTRIES.map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
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
          </Col>
        </Row>

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
