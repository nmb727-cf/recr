import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Steps, Card, Form, Input, Button, Row, Col, Select,
  Switch, InputNumber, message, Typography
} from 'antd'
import { 
  UserOutlined, 
  SolutionOutlined, 
  FileTextOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
  LinkOutlined,
  CheckCircleFilled,
  InfoCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { useAuth } from '@/hooks/useAuth'
import { authApi } from '@/api/auth'
import { passportApi } from '@/api/passport'
import type { Passport } from '@/types'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'

const { Title, Text } = Typography

const ONBOARDING_THRESHOLD = 40

export default function Onboarding() {
  const navigate = useNavigate()
  const { user, fetchMe } = useAuth()
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [passport, setPassport] = useState<Passport | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await passportApi.get()
        const p = res.data.data.passport
        setPassport(p)
        if (p.completeness_score >= ONBOARDING_THRESHOLD) {
          navigate('/dashboard')
        }
      } catch (err: any) {
        if (err.response?.status !== 404) {
          message.error('Failed to load profile status')
        }
      }
    }
    checkStatus()
  }, [navigate])

  const handleStep1 = async (values: any) => {
    setLoading(true)
    try {
      // 1. Update basic user info
      await authApi.updateMe({
        first_name: values.first_name,
        last_name: values.last_name,
        phone: values.phone,
        timezone: values.timezone
      })
      
      // 2. Update passport profile info
      await passportApi.update({
        current_title: values.current_title,
        current_company: values.current_company,
        current_location_city: values.current_location_city,
        current_location_country: values.current_location_country,
        experience_years: values.experience_years
      })

      await fetchMe()
      const res = await passportApi.get()
      setPassport(res.data.data.passport)
      
      setCurrentStep(1)
      message.success('Basic info saved')
    } catch (err: any) {
      console.error('Step 1 Error:', err.response?.data)
      message.error(err.response?.data?.message || 'Failed to save basic info')
    } finally {
      setLoading(false)
    }
  }

  const handleStep2 = async (values: any) => {
    setLoading(true)
    try {
      const res = await passportApi.update(values)
      setPassport(res.data.data.passport)
      setCurrentStep(2)
      message.success('Preferences saved')
    } catch (err: any) {
      console.error('Step 2 Error:', err.response?.data)
      message.error(err.response?.data?.message || 'Failed to save preferences')
    } finally {
      setLoading(false)
    }
  }

  const handleStep3 = async (values: any) => {
    setLoading(true)
    try {
      const res = await passportApi.update({
        current_cv_url: values.current_cv_url
      })
      setPassport(res.data.data.passport)
      message.success('Profile updated!')
      navigate('/dashboard')
    } catch (err: any) {
      console.error('Step 3 Error:', err.response?.data)
      message.error(err.response?.data?.message || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const skipStep3 = () => {
    message.success('Welcome to RecruitOS!')
    navigate('/dashboard')
  }

  const steps = [
    { title: 'Basic Info', icon: <UserOutlined /> },
    { title: 'Skills & Preferences', icon: <SolutionOutlined /> },
    { title: 'Resume', icon: <FileTextOutlined /> },
  ]

  const onCountryChange = (val: string) => {
    const country = COUNTRIES.find(c => c.code === val || c.name === val)
    if (country) {
      form.setFieldsValue({ salary_currency: country.currency })
    }
  }

  const step0InitialValues = {
    ...user,
    timezone: user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    current_title: passport?.current_title,
    current_company: passport?.current_company,
    current_location_city: passport?.current_location_city,
    current_location_country: passport?.current_location_country,
    experience_years: passport?.experience_years
  }

  return (
    <div className="w-full">
      <Steps 
        current={currentStep} 
        items={steps} 
        className="mb-8"
      />

        <Card bordered={false} className="shadow-soft-lg rounded-3xl p-2 border border-slate-100">
          {currentStep === 0 && (
            <Form
              form={form}
              layout="vertical"
              initialValues={step0InitialValues}
              onFinish={handleStep1}
              requiredMark={false}
              className="p-4"
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="first_name" label="First Name" rules={[{ required: true, message: 'First name is required' }]}>
                    <Input placeholder="John" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="last_name" label="Last Name" rules={[{ required: true, message: 'Last name is required' }]}>
                    <Input placeholder="Doe" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item 
                    name="phone" 
                    label="Phone Number" 
                    rules={[
                      { required: true, message: 'Phone number is required' },
                      { pattern: /^\+?[\d\s-]{10,15}$/, message: 'Numbers only (10-15 digits)' }
                    ]}
                  >
                    <Input placeholder="+1 555 000 0000" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="timezone" label="Preferred Timezone" rules={[{ required: true }]}>
                    <Select 
                      showSearch
                      optionFilterProp="label"
                      suffixIcon={<ClockCircleOutlined />}
                      options={TIMEZONES} 
                      className="h-11"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="current_title" label="Current Job Title">
                    <Input placeholder="Senior Engineer" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="current_company" label="Current Company">
                    <Input placeholder="Acme Corp" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="current_location_city" label="City">
                    <Input placeholder="Mumbai" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="current_location_country" label="Country">
                    <Select 
                      showSearch
                      placeholder="Select country" 
                      className="h-11"
                      onChange={onCountryChange}
                      options={COUNTRIES.map(c => ({ value: c.code, label: c.name }))}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="experience_years" label="Total Years of Experience">
                <InputNumber min={0} max={50} step={0.5} className="w-full h-11 rounded-xl flex items-center" />
              </Form.Item>

              <Button type="primary" htmlType="submit" block size="large" loading={loading} className="mt-4 rounded-xl font-bold h-12 bg-blue-600 border-none shadow-soft-sm">
                Save & Continue <ArrowRightOutlined />
              </Button>
            </Form>
          )}

          {currentStep === 1 && (
            <Form
              form={form}
              layout="vertical"
              initialValues={passport || {
                is_actively_looking: true,
                preferred_work_mode: 'remote',
                notice_period_days: 30,
                salary_currency: 'USD'
              }}
              onFinish={handleStep2}
              requiredMark={false}
              className="p-4"
            >
              <Form.Item name="skills" label="Key Skills" rules={[{ required: true, message: 'Please add at least one skill' }]}>
                <Select 
                  mode="tags" 
                  placeholder="Type a skill and press enter (e.g. React, Python)" 
                  className="min-h-[44px] rounded-xl"
                />
              </Form.Item>
              
              <div className="bg-slate-50 p-5 rounded-2xl mb-6 border border-slate-100">
                <Row gutter={24} align="middle">
                  <Col span={14}>
                    <Text className="font-bold text-slate-700 block">Actively looking for jobs</Text>
                    <Text className="text-xs text-slate-400">Your profile will be visible to recruiters</Text>
                  </Col>
                  <Col span={10} className="text-right">
                    <Form.Item name="is_actively_looking" valuePropName="checked" className="m-0">
                      <Switch className="bg-slate-300" />
                    </Form.Item>
                  </Col>
                </Row>
              </div>

              <Form.Item name="preferred_work_mode" label="Preferred Work Mode">
                <Select className="h-11" options={[
                  { value: 'remote', label: 'Remote Only' },
                  { value: 'onsite', label: 'On-site Office' },
                  { value: 'hybrid', label: 'Hybrid' },
                  { value: 'any', label: 'Open to Any' },
                ]} />
              </Form.Item>

              <Form.Item name="notice_period_days" label="Notice Period (Days)">
                <InputNumber min={0} max={180} className="w-full h-11 rounded-xl flex items-center" />
              </Form.Item>

              <Row gutter={12}>
                <Col span={6}>
                  <Form.Item name="salary_currency" label="Currency">
                    <Input placeholder="USD" className="h-11 rounded-xl uppercase" />
                  </Form.Item>
                </Col>
                <Col span={9}>
                  <Form.Item name="expected_salary_min" label="Min. Annual Salary">
                    <InputNumber min={0} className="w-full h-11 rounded-xl flex items-center" placeholder="Min" />
                  </Form.Item>
                </Col>
                <Col span={9}>
                  <Form.Item name="expected_salary_max" label="Max. Annual Salary">
                    <InputNumber min={0} className="w-full h-11 rounded-xl flex items-center" placeholder="Max" />
                  </Form.Item>
                </Col>
              </Row>

              <div className="flex gap-3 mt-6">
                <Button block size="large" onClick={() => setCurrentStep(0)} className="h-12 rounded-xl font-bold border-slate-200 text-slate-600">
                  <ArrowLeftOutlined /> Back
                </Button>
                <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-12 rounded-xl font-bold bg-blue-600 border-none shadow-soft-sm">
                  Save & Continue <ArrowRightOutlined />
                </Button>
              </div>
            </Form>
          )}

          {currentStep === 2 && (
            <div className="text-center p-6">
              <div className="mb-10">
                <div className="h-20 w-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-soft-sm">
                  <FileTextOutlined style={{ fontSize: 32 }} />
                </div>
                <Title level={3} className="!mb-2 tracking-tight">Your Resume</Title>
                <Text className="text-slate-500 font-medium block mb-2">Help us understand your background better</Text>
                
                <div className="max-w-md mx-auto bg-amber-50 p-4 rounded-2xl border border-amber-100 flex items-start gap-3 text-left mt-6">
                  <InfoCircleOutlined className="text-amber-500 mt-0.5" />
                  <div className="text-xs text-amber-700 leading-relaxed">
                    <strong>Phase 1 Note:</strong> Direct file upload is coming soon. For now, please provide a public link to your resume (e.g. from Google Drive, Dropbox, or a portfolio site).
                  </div>
                </div>
              </div>

              <Form layout="vertical" onFinish={handleStep3} className="max-w-md mx-auto">
                <Form.Item 
                  name="current_cv_url" 
                  label={<span className="text-slate-400 font-bold text-[10px] uppercase tracking-widest">Public Resume URL (Optional)</span>}
                  rules={[{ type: 'url', message: 'Please enter a valid URL' }]}
                >
                  <Input prefix={<LinkOutlined className="text-slate-300" />} placeholder="https://..." className="h-12 rounded-xl" />
                </Form.Item>
                
                <div className="flex flex-col gap-3 mt-8">
                  <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md">
                    Finish & View Dashboard
                  </Button>
                  <Button type="text" block onClick={skipStep3} className="text-slate-400 font-bold">
                    Skip this for now
                  </Button>
                </div>
              </Form>

              {passport && (
                <div className="mt-12 p-6 bg-slate-50 rounded-3xl border border-slate-100 text-left">
                  <div className="flex justify-between items-center mb-3">
                    <Text className="font-bold text-slate-500 text-xs uppercase tracking-widest">Profile Completion Status</Text>
                    <Text className="text-xs font-bold text-blue-600">{passport.completeness_score}%</Text>
                  </div>
                  <div className="h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-600 transition-all duration-700 ease-out" 
                      style={{ width: `${passport.completeness_score}%` }} 
                    />
                  </div>
                  {passport.completeness_score >= ONBOARDING_THRESHOLD && (
                    <div className="mt-4 flex items-center gap-2 text-emerald-600">
                      <CheckCircleFilled />
                      <span className="text-xs font-bold uppercase tracking-tight font-sans">Minimum requirements met</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
    </div>
  )
}
