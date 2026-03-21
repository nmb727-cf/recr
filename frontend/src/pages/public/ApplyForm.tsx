import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Card, Steps, Form, Input, Button, Row, Col, Select, 
  Switch, InputNumber, Upload, message, Typography, 
  Result, Spin
} from 'antd'
import { 
  UserOutlined, 
  SolutionOutlined, 
  InboxOutlined,
  CheckCircleOutlined,
  LockOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons'
import http from '@/utils/http'

const { Title, Text } = Typography
const { Dragger } = Upload

export default function ApplyForm() {
  const { token } = useParams<{ token: string }>()
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [config, setConfig] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [error, setError] = useState<string | null>(null)
  const [, setIsSubmitted] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await http.get(`/apply/${token}/`, {
          headers: { 'X-Skip-Auth': 'true' }
        })
        setConfig(res.data.data)
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError("This invite link has expired or is invalid")
        } else if (err.response?.status === 400) {
          setError("You have already submitted your application")
        } else {
          setError("Something went wrong. Please try again later.")
        }
      } finally {
        setLoading(false)
      }
    }
    fetchConfig()
  }, [token])

  const next = async () => {
    try {
      const values = await form.validateFields()
      setFormData({ ...formData, ...values })
      setCurrentStep(currentStep + 1)
    } catch (err) {
      // validation failed
    }
  }

  const prev = () => {
    setCurrentStep(currentStep - 1)
  }

  const onFinish = async (values: any) => {
    const finalData = { ...formData, ...values }
    setSubmitting(true)
    try {
      await http.post(`/apply/${token}/submit/`, finalData, {
        headers: { 'X-Skip-Auth': 'true' }
      })
      setIsSubmitted(true)
      setCurrentStep(3)
    } catch (err: any) {
      message.error(err.response?.data?.message || "Failed to submit application")
    } finally {
      setSubmitting(true)
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><Spin size="large" tip="Loading application form..." /></div>
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <Card bordered={false} className="w-full max-w-md shadow-soft-lg rounded-3xl text-center">
          <Result
            status="warning"
            title="Unable to proceed"
            subTitle={error}
            extra={<Button type="primary" size="large" className="rounded-xl font-bold bg-slate-900 border-none px-8" onClick={() => window.location.href = '/'}>Go Home</Button>}
          />
        </Card>
      </div>
    )
  }

  const steps = [
    { title: 'Personal Info', icon: <UserOutlined /> },
    { title: 'Skills & Exp', icon: <SolutionOutlined /> },
    { title: 'CV Upload', icon: <InboxOutlined /> },
    { title: 'Done', icon: <CheckCircleOutlined /> },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 py-12">
      <div className="w-full max-w-[680px]">
        {/* Company Header */}
        <div className="text-center mb-10">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-soft-md text-blue-600 font-black text-3xl mb-4 border border-slate-100 overflow-hidden">
            {config?.company_logo ? <img src={config.company_logo} alt="logo" /> : config?.company_name?.charAt(0)}
          </div>
          <Title level={3} className="!mb-1">{config?.company_name}</Title>
          <Text type="secondary" className="text-base">has invited you to apply</Text>
          {config?.job_title && (
            <div className="mt-4 inline-block bg-blue-50 text-blue-700 px-4 py-1.5 rounded-full font-bold text-sm border border-blue-100">
              Applying for: {config.job_title}
            </div>
          )}
        </div>

        <Steps 
          current={currentStep} 
          items={steps} 
          className="mb-10 px-4"
        />

        <Card bordered={false} className="shadow-soft-xl rounded-3xl p-4 sm:p-8">
          <Form
            form={form}
            layout="vertical"
            requiredMark={false}
            onFinish={onFinish}
          >
            {currentStep === 0 && (
              <div className="space-y-4">
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
                      <Input placeholder="John" className="h-11 rounded-xl" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
                      <Input placeholder="Doe" className="h-11 rounded-xl" />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item name="email" label="Email Address" rules={[{ required: true, type: 'email' }]}>
                  <Input placeholder="john@example.com" className="h-11 rounded-xl" />
                </Form.Item>
                <Form.Item name="phone" label="Phone Number">
                  <Input placeholder="+1 (555) 000-0000" className="h-11 rounded-xl" />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="current_title" label="Current Title">
                      <Input placeholder="Product Designer" className="h-11 rounded-xl" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="current_company" label="Current Company">
                      <Input placeholder="Acme Corp" className="h-11 rounded-xl" />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item name="current_location_city" label="City">
                  <Input placeholder="London" className="h-11 rounded-xl" />
                </Form.Item>
                <Button type="primary" block size="large" onClick={next} className="h-12 rounded-xl font-bold bg-blue-600 border-none mt-4">
                  Next Step <ArrowRightOutlined />
                </Button>
              </div>
            )}

            {currentStep === 1 && (
              <div className="space-y-4">
                <Form.Item name="skills" label="Key Skills" rules={[{ required: true }]}>
                  <Select mode="tags" placeholder="Type a skill and press enter" className="min-h-11" />
                </Form.Item>
                <Form.Item name="experience_years" label="Years of Experience">
                  <InputNumber min={0} step={0.5} style={{ width: '100%' }} className="h-11 rounded-xl pt-1" />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="expected_salary_min" label="Expected Min Salary">
                      <InputNumber min={0} style={{ width: '100%' }} className="h-11 rounded-xl pt-1" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="expected_salary_max" label="Expected Max Salary">
                      <InputNumber min={0} style={{ width: '100%' }} className="h-11 rounded-xl pt-1" />
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={16} align="middle">
                  <Col span={12}>
                    <Form.Item name="notice_period_days" label="Notice Period (Days)">
                      <InputNumber min={0} style={{ width: '100%' }} className="h-11 rounded-xl pt-1" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="is_actively_looking" label="Actively Looking?" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
                <div className="flex gap-3 pt-4">
                  <Button block size="large" onClick={prev} className="h-12 rounded-xl font-bold border-slate-200">
                    <ArrowLeftOutlined /> Back
                  </Button>
                  <Button type="primary" block size="large" onClick={next} className="h-12 rounded-xl font-bold bg-blue-600 border-none">
                    Next Step <ArrowRightOutlined />
                  </Button>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <Form.Item name="cv_filename">
                  <Dragger 
                    multiple={false} 
                    accept=".pdf,.doc,.docx"
                    beforeUpload={(file) => {
                      setFormData({ ...formData, cv_filename: file.name });
                      return false;
                    }}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined className="text-blue-600" />
                    </p>
                    <p className="ant-upload-text font-bold">Click or drag resume to this area to upload</p>
                    <p className="ant-upload-hint text-xs text-slate-400">Support for PDF, DOC or DOCX only.</p>
                  </Dragger>
                </Form.Item>
                <div className="flex flex-col gap-3 pt-4">
                  <div className="flex gap-3 w-full">
                    <Button block size="large" onClick={prev} className="h-12 rounded-xl font-bold border-slate-200">
                      <ArrowLeftOutlined /> Back
                    </Button>
                    <Button type="primary" block size="large" onClick={next} className="h-12 rounded-xl font-bold bg-blue-600 border-none">
                      Continue to Final Step
                    </Button>
                  </div>
                  <Button type="text" block className="text-slate-400" onClick={next}>Skip for now</Button>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="text-center py-4">
                <div className="mb-8">
                  <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircleOutlined style={{ fontSize: 40 }} />
                  </div>
                  <Title level={3}>Almost done!</Title>
                  <Text type="secondary" className="text-base">Your profile has been submitted to {config?.company_name}</Text>
                </div>

                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 mb-8 text-left">
                  <Form.Item name="wants_account" valuePropName="checked" className="!mb-0">
                    <Switch defaultChecked /> <span className="ml-3 font-bold text-slate-700">Create an account to track your application updates</span>
                  </Form.Item>
                  
                  <Form.Item 
                    noStyle
                    shouldUpdate={(prevValues, currentValues) => prevValues.wants_account !== currentValues.wants_account}
                  >
                    {({ getFieldValue }) => 
                      getFieldValue('wants_account') ? (
                        <div className="mt-6">
                          <Form.Item name="password" label="Create Password" rules={[{ required: true, min: 8 }]}>
                            <Input.Password prefix={<LockOutlined className="text-slate-400 mr-2" />} placeholder="Minimum 8 characters" className="h-11 rounded-xl" />
                          </Form.Item>
                        </div>
                      ) : null
                    }
                  </Form.Item>
                </div>

                <Button type="primary" htmlType="submit" block size="large" loading={submitting} className="h-14 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md">
                  {form.getFieldValue('wants_account') ? 'Create Account & Complete' : 'Complete Application'}
                </Button>
              </div>
            )}
          </Form>
        </Card>
      </div>
    </div>
  )
}
