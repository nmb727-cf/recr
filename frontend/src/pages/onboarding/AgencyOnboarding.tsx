import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, Row, Select, Typography, message, Spin } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { organisationApi } from '@/api/organisation'
import { useAuth } from '@/hooks/useAuth'
import {
  clearAgencySignupPrefill,
  isOrganisationSetupIncomplete,
  readAgencySignupPrefill,
} from '@/utils/companyOnboarding'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'

const { Title, Text } = Typography

const AGENCY_SIZE_OPTIONS = [
  { value: '1-10', label: '1-10 employees' },
  { value: '11-50', label: '11-50 employees' },
  { value: '51-200', label: '51-200 employees' },
  { value: '201-500', label: '201-500 employees' },
  { value: '500+', label: '500+ employees' },
]

export default function AgencyOnboarding() {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const navigate = useNavigate()
  const { user } = useAuth()
  const signupPrefill = useMemo(() => readAgencySignupPrefill(), [])

  const { data, isLoading, refetch } = useApiQuery(['org_profile_agency_onboarding'], () =>
    organisationApi.getProfile()
  )
  const org = (data as any)?.organisation || (data as any)?.data?.organisation
  const isFirstSetup = isOrganisationSetupIncomplete(org)

  useEffect(() => {
    setEditMode(isFirstSetup)
    
    // Redirect if already onboarded and not in some explicit edit mode
    if (org && !isFirstSetup && !editMode && window.location.pathname.includes('onboarding')) {
      navigate('/agencies/my-jobs', { replace: true })
    }
  }, [isFirstSetup, org, editMode, navigate])

  useEffect(() => {
    if (!org && !signupPrefill) return

    form.setFieldsValue({
      name:
        org?.name && !org.name.toLowerCase().includes('new company') && org.name !== 'My Organisation'
          ? org.name
          : (signupPrefill?.agency_name || org?.name || ''),
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

      clearAgencySignupPrefill()
      const refreshed = await refetch()
      const refreshedOrg =
        (refreshed?.data as any)?.organisation ||
        (refreshed?.data as any)?.data?.organisation
      const isStillIncomplete = isOrganisationSetupIncomplete(refreshedOrg)
      if (isFirstSetup) {
        message.success('Agency setup completed')
        // Always advance first-time onboarding users out of setup on successful save.
        navigate('/agencies/my-jobs', { replace: true })
      } else {
        message.success('Agency profile updated')
        // For revisits, return to read mode after successful save.
        setEditMode(false)
      }

      // Safety net: if backend response lags briefly but save succeeded, do not trap user in onboarding.
      if (isFirstSetup && isStillIncomplete) {
        navigate('/agencies/my-jobs', { replace: true })
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.message || 'Failed to save agency setup'
      const fieldErrors = err?.response?.data?.errors

      if (fieldErrors) {
        const errors = Object.entries(fieldErrors).map(([name, msgs]: any) => ({
          name,
          errors: Array.isArray(msgs) ? msgs : [String(msgs)],
        }))
        form.setFields(errors)
        const first = Object.values(fieldErrors)[0]
        const firstMsg = Array.isArray(first) ? first[0] : String(first)
        message.error(firstMsg || errorMsg)
        return
      }

      message.error(errorMsg)
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Spin size="large" tip="Loading your agency setup..." />
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
          description="Complete this once. After setup, you can edit from Settings whenever needed."
        />
      )}

      {!isFirstSetup && !editMode && (
        <Card bordered={false} className="shadow-soft-sm border border-slate-100">
          <div className="space-y-4">
            <div>
              <Text type="secondary">Agency Name</Text>
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
                <Text type="secondary">Agency Size</Text>
                <div className="font-semibold text-slate-900">{org?.size_range || 'N/A'}</div>
              </Col>
            </Row>
            <div>
              <Text type="secondary">Website</Text>
              <div className="font-semibold text-slate-900">{org?.website || 'N/A'}</div>
            </div>
            <div>
              <Text type="secondary">Owner</Text>
              <div className="font-semibold text-slate-900">{user?.full_name || signupPrefill?.name || 'N/A'}</div>
            </div>
            <div>
              <Text type="secondary">Email</Text>
              <div className="font-semibold text-slate-900">{user?.email || signupPrefill?.email || 'N/A'}</div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="primary" onClick={() => setEditMode(true)}>
                Edit
              </Button>
              <Button onClick={() => navigate('/agencies/my-jobs', { replace: true })}>Go to Agency Jobs</Button>
            </div>
          </div>
        </Card>
      )}

      {(isFirstSetup || editMode) && (
        <Card bordered={false} className="shadow-soft-sm border border-slate-100">
          <Form form={form} layout="vertical" onFinish={onFinish} requiredMark={false}>
            <Form.Item name="name" label="Agency Name" rules={[{ required: true, message: 'Agency name is required' }]}>
              <Input />
            </Form.Item>

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item name="country_code" label="Country" rules={[{ required: true, message: 'Country is required' }]}>
                  <Select
                    showSearch
                    optionFilterProp="label"
                    options={COUNTRIES.map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="timezone" label="Timezone" rules={[{ required: true, message: 'Timezone is required' }]}>
                  <Select showSearch optionFilterProp="label" options={TIMEZONES} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item name="industry" label="Industry" rules={[{ required: true, message: 'Industry is required' }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="size_range" label="Agency Size">
                  <Select
                    options={AGENCY_SIZE_OPTIONS}
                    optionFilterProp="label"
                    showSearch
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="website" label="Website">
              <Input placeholder="https://example.com" />
            </Form.Item>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 mb-4">
              <Text className="block text-xs uppercase tracking-wider font-semibold text-slate-500">
                Account context
              </Text>
              <Text className="block text-sm text-slate-700 mt-1">
                Owner: {user?.full_name || signupPrefill?.name || 'N/A'}
              </Text>
              <Text className="block text-sm text-slate-700">
                Email: {user?.email || signupPrefill?.email || 'N/A'}
              </Text>
            </div>

            <div className="flex items-center gap-3">
              <Button type="primary" htmlType="submit" loading={saving}>
                {isFirstSetup ? 'Save and Continue' : 'Save Changes'}
              </Button>
              {!isFirstSetup && (
                <Button onClick={() => setEditMode(false)}>
                  Cancel
                </Button>
              )}
              {!isFirstSetup && (
                <Button onClick={() => navigate('/settings?tab=organisation')}>
                  Open Settings
                </Button>
              )}
            </div>
          </Form>
        </Card>
      )}
    </div>
  )
}
