import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, Row, Select, Typography, message, Spin } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { organisationApi } from '@/api/organisation'
import { useAuth } from '@/hooks/useAuth'
import { clearCompanySignupPrefill, isOrganisationSetupIncomplete, readCompanySignupPrefill } from '@/utils/companyOnboarding'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'
import { BankOutlined, GlobalOutlined, InfoCircleOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function CompanyOnboarding() {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const navigate = useNavigate()
  const { user, fetchMe } = useAuth()

  const signupPrefill = useMemo(() => readCompanySignupPrefill(), [])

  const { data, isLoading, refetch } = useApiQuery(
    ['org_profile_onboarding'],
    () => organisationApi.getProfile()
  )
  const org = (data as any)?.organisation || (data as any)?.data?.organisation
  const isFirstSetup = isOrganisationSetupIncomplete(org)

  useEffect(() => {
    setEditMode(isFirstSetup)
    
    // Redirect if already onboarded and not in some explicit edit mode
    if (org && !isFirstSetup && !editMode && window.location.pathname.includes('onboarding')) {
      navigate('/dashboard', { replace: true })
    }
  }, [isFirstSetup, org, editMode, navigate])

  useEffect(() => {
    if (!org && !signupPrefill) return

    form.setFieldsValue({
      name: org?.name && !org.name.toLowerCase().includes('new company') && org.name !== 'My Organisation' 
        ? org.name 
        : signupPrefill?.company_name || '',
      industry: org?.industry || '',
      website: org?.website || '',
      size_range: org?.size_range || '11-50',
      country_code: org?.country_code || signupPrefill?.country_code || 'IN',
      timezone: org?.timezone || 'Asia/Kolkata',
    })
  }, [org, signupPrefill, form])

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      await organisationApi.updateProfile({
        name: values.name,
        industry: values.industry,
        website: values.website,
        size_range: values.size_range,
        country_code: values.country_code,
        timezone: values.timezone,
      } as any)

      clearCompanySignupPrefill()
      await fetchMe() // Refresh user context
      await refetch()
      if (isFirstSetup) {
        message.success('Organisation setup completed')
        navigate('/dashboard', { replace: true })
      } else {
        message.success('Organisation profile updated')
        setEditMode(false)
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.message || 'Failed to save organisation setup'
      const fieldErrors = err?.response?.data?.errors
      
      if (fieldErrors) {
        const errors = Object.entries(fieldErrors).map(([name, msgs]: any) => ({
          name,
          errors: msgs
        }))
        form.setFields(errors)
      }
      
      message.error(errorMsg)
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Spin size="large" tip="Loading your setup..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {isFirstSetup && (
        <Alert
          type="info"
          showIcon
          message="Setup required"
          description="Complete this once. After setup, you can edit everything from Settings."
        />
      )}

      {!isFirstSetup && !editMode && (
        <Card bordered={false} className="shadow-soft-sm border border-slate-100">
          <div className="space-y-4">
            <div>
              <Text type="secondary">Organisation Name</Text>
              <div className="font-semibold text-slate-900">{org?.name || 'N/A'}</div>
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <Text type="secondary">Country</Text>
                <div className="font-semibold text-slate-900">{org?.country_code || 'N/A'}</div>
              </Col>
              <Col span={12}>
                <Text type="secondary">Timezone</Text>
                <div className="font-semibold text-slate-900">{org?.timezone || 'N/A'}</div>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text type="secondary">Industry</Text>
                <div className="font-semibold text-slate-900">{org?.industry || 'N/A'}</div>
              </Col>
              <Col span={12}>
                <Text type="secondary">Company Size</Text>
                <div className="font-semibold text-slate-900">{org?.size_range || 'N/A'}</div>
              </Col>
            </Row>
            <div>
              <Text type="secondary">Website</Text>
              <div className="font-semibold text-slate-900">{org?.website || 'N/A'}</div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="primary" onClick={() => setEditMode(true)}>Edit</Button>
              <Button onClick={() => navigate('/dashboard', { replace: true })}>Go to Dashboard</Button>
            </div>
          </div>
        </Card>
      )}

      {(isFirstSetup || editMode) && (
        <Card bordered={false} className="shadow-soft-sm border border-slate-100">
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            className="p-2"
            requiredMark={false}
          >
            <Form.Item 
              name="name" 
              label={<Text className="font-bold text-slate-700">Organisation Name</Text>} 
              rules={[{ required: true, message: 'Please enter your company name' }]}
            >
              <Input size="large" placeholder="Acme Corp" className="rounded-xl h-11" prefix={<BankOutlined className="text-slate-400 mr-2" />} />
            </Form.Item>

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item 
                  name="country_code" 
                  label={<Text className="font-bold text-slate-700">Country</Text>} 
                  rules={[{ required: true, message: 'Select your country' }]}
                >
                  <Select
                    size="large"
                    showSearch
                    className="rounded-xl"
                    optionFilterProp="label"
                    prefix={<GlobalOutlined className="text-slate-400 mr-2" />}
                    options={COUNTRIES.map((c) => ({ value: c.code, label: c.name }))}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item 
                  name="timezone" 
                  label={<Text className="font-bold text-slate-700">Default Timezone</Text>} 
                  rules={[{ required: true }]}
                >
                  <Select
                    size="large"
                    showSearch
                    className="rounded-xl"
                    optionFilterProp="label"
                    options={TIMEZONES}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item 
                  name="industry" 
                  label={<Text className="font-bold text-slate-700">Industry</Text>} 
                  rules={[{ required: true, message: 'Industry is required' }]}
                >
                  <Input size="large" placeholder="e.g. Technology" className="rounded-xl h-11" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item 
                  name="size_range" 
                  label={<Text className="font-bold text-slate-700">Company Size</Text>}
                >
                  <Select size="large" className="rounded-xl">
                    <Select.Option value="1-10">1-10 employees</Select.Option>
                    <Select.Option value="11-50">11-50 employees</Select.Option>
                    <Select.Option value="51-200">51-200 employees</Select.Option>
                    <Select.Option value="201-500">201-500 employees</Select.Option>
                    <Select.Option value="500+">500+ employees</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="website" label={<Text className="font-bold text-slate-700">Website</Text>}>
              <Input size="large" placeholder="https://example.com" className="rounded-xl h-11" />
            </Form.Item>

            <div className="bg-slate-50 rounded-2xl p-5 border border-slate-100 mb-8">
              <div className="flex items-start gap-3">
                <InfoCircleOutlined className="text-blue-500 mt-1" />
                <div>
                  <Text className="block font-bold text-slate-700 text-sm">Administrator Account</Text>
                  <Text className="block text-xs text-slate-500 mt-1">
                    You are setting up this organisation as <strong>{user?.full_name}</strong> ({user?.email}). 
                    You will be the primary administrator.
                  </Text>
                </div>
              </div>
            </div>

            <Button 
              type="primary" 
              htmlType="submit" 
              loading={saving} 
              size="large"
              className="h-11 rounded-xl font-bold bg-blue-600 border-none shadow-soft-sm"
            >
              {isFirstSetup ? 'Save and Continue' : 'Save Changes'}
            </Button>
            {!isFirstSetup && (
              <Button
                style={{ marginLeft: 12 }}
                onClick={() => navigate('/settings?tab=organisation')}
              >
                Open Settings
              </Button>
            )}
          </Form>
        </Card>
      )}
    </div>
  )
}
