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
  UploadOutlined
} from '@ant-design/icons'
import { useAuth } from '@/hooks/useAuth'
import { authApi } from '@/api/auth'
import { passportApi } from '@/api/passport'
import type { Passport } from '@/types'

const { Title, Text } = Typography

export default function Onboarding() {
  const navigate = useNavigate()
  const { user, fetchMe } = useAuth()
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [passport, setPassport] = useState<Passport | null>(null)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await passportApi.get()
        setPassport(res.data.data.passport)
      } catch (err: any) {
        if (err.response?.status !== 404) {
          message.error('Failed to load profile status')
        }
      }
    }
    checkStatus()
  }, [])

  const handleStep1 = async (values: any) => {
    setLoading(true)
    try {
      await authApi.updateMe(values)
      await fetchMe()
      setCurrentStep(1)
      message.success('Basic info saved')
    } catch (err: any) {
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
      message.error(err.response?.data?.message || 'Failed to save preferences')
    } finally {
      setLoading(false)
    }
  }

  const handleStep3 = async (values: any) => {
    setLoading(true)
    try {
      const res = await passportApi.update(values)
      setPassport(res.data.data.passport)
      message.success('Onboarding complete!')
      navigate('/dashboard')
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to save resume')
    } finally {
      setLoading(false)
    }
  }

  const skipStep3 = () => {
    message.success('Welcome to RecruitOS!')
    navigate('/dashboard')
  }

  const steps = [
    {
      title: 'Basic Info',
      icon: <UserOutlined />,
    },
    {
      title: 'Skills & Preferences',
      icon: <SolutionOutlined />,
    },
    {
      title: 'Resume',
      icon: <FileTextOutlined />,
    },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-10">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-2xl mb-4">R</div>
          <Title level={2} className="!mb-1">Complete your profile</Title>
          <Text type="secondary">Help us find the best opportunities for you</Text>
        </div>

        <Steps 
          current={currentStep} 
          items={steps} 
          className="mb-8"
        />

        <Card bordered={false} className="shadow-soft-lg rounded-2xl p-4">
          {currentStep === 0 && (
            <Form
              layout="vertical"
              initialValues={user || {}}
              onFinish={handleStep1}
              requiredMark={false}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
                    <Input placeholder="John" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
                    <Input placeholder="Doe" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="phone" label="Phone Number" rules={[{ required: true }]}>
                <Input placeholder="+1 (555) 000-0000" />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="current_title" label="Current Job Title">
                    <Input placeholder="Senior Engineer" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="current_company" label="Current Company">
                    <Input placeholder="Acme Corp" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="current_location_city" label="City">
                    <Input placeholder="San Francisco" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="current_location_country" label="Country">
                    <Input placeholder="USA" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="experience_years" label="Total Years of Experience">
                <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
              <Button type="primary" htmlType="submit" block size="large" loading={loading} className="mt-4 rounded-xl font-bold h-12">
                Continue <ArrowRightOutlined />
              </Button>
            </Form>
          )}

          {currentStep === 1 && (
            <Form
              layout="vertical"
              initialValues={passport || {
                is_actively_looking: true,
                preferred_work_mode: 'remote',
                notice_period_days: 30,
                salary_currency: 'USD'
              }}
              onFinish={handleStep2}
              requiredMark={false}
            >
              <Form.Item name="skills" label="Skills" rules={[{ required: true, message: 'Please add at least one skill' }]}>
                <Select mode="tags" placeholder="Type a skill and press enter (e.g. React, Python)" />
              </Form.Item>
              
              <Row gutter={24} className="mb-4">
                <Col span={12}>
                  <Form.Item name="is_actively_looking" label="Actively looking for jobs" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="preferred_work_mode" label="Work Mode">
                    <Select options={[
                      { value: 'remote', label: 'Remote' },
                      { value: 'onsite', label: 'On-site' },
                      { value: 'hybrid', label: 'Hybrid' },
                      { value: 'any', label: 'Any' },
                    ]} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="notice_period_days" label="Notice Period (Days)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="salary_currency" label="Currency">
                    <Input placeholder="USD" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="expected_salary_min" label="Min Salary">
                    <InputNumber min={0} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="expected_salary_max" label="Max Salary">
                    <InputNumber min={0} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <div className="flex gap-3">
                <Button block size="large" onClick={() => setCurrentStep(0)} className="h-12 rounded-xl font-bold">
                  <ArrowLeftOutlined /> Back
                </Button>
                <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-12 rounded-xl font-bold">
                  Continue <ArrowRightOutlined />
                </Button>
              </div>
            </Form>
          )}

          {currentStep === 2 && (
            <div className="text-center py-6">
              <div className="mb-8">
                <div className="h-20 w-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <UploadOutlined style={{ fontSize: 32 }} />
                </div>
                <Title level={4}>Upload your Resume</Title>
                <Text type="secondary">Adding a resume increases your profile strength significantly</Text>
              </div>

              <Form layout="vertical" onFinish={handleStep3}>
                <Form.Item name="resume_url" label="Resume URL (PDF/DOCX)">
                  <Input placeholder="Link to your resume (e.g. Google Drive, Dropbox)" />
                </Form.Item>
                
                <div className="flex flex-col gap-3">
                  <Button type="primary" htmlType="submit" block size="large" loading={loading} className="h-12 rounded-xl font-bold">
                    Finish Onboarding
                  </Button>
                  <Button type="text" block onClick={skipStep3} className="text-slate-400">
                    Skip for now
                  </Button>
                </div>
              </Form>

              {passport && (
                <div className="mt-10 pt-6 border-t border-slate-100">
                  <Text type="secondary" className="block mb-2">Profile Strength</Text>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-600 transition-all duration-500" 
                      style={{ width: `${passport.completeness_score}%` }} 
                    />
                  </div>
                  <Text className="text-xs font-bold text-blue-600 mt-2 block">{passport.completeness_score}% COMPLETE</Text>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
