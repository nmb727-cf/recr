import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Form, Input, Button, Typography, Spin, 
  message, Result, Checkbox, Select, Divider, InputNumber, Row, Col
} from 'antd'
import { candidatesApi } from '@/api/candidates'
import { Globe, Briefcase, Zap, FileText } from 'lucide-react'

const { Title, Text } = Typography

export default function ApplyForm() {
  const { token } = useParams<{ token: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formConfig, setFormConfig] = useState<{
    company_name: string
    job_title: string | null
  } | null>(null)
  const [wantsAccount, setWantsAccount] = useState(false)

  // Skill search state (local for public form)
  const [skillOptions, setSkillOptions] = useState<{value: string, label: string}[]>([])
  const [skillSearching, setSkillSearching] = useState(false)

  useEffect(() => {
    if (!token) return
    candidatesApi.getPublicForm(token)
      .then(res => {
        setFormConfig((res as any).data.data)
      })
      .catch(err => {
        setError(
          err?.response?.data?.message || 
          'This link is invalid or expired.'
        )
      })
      .finally(() => setLoading(false))
  }, [token])

  const handleSkillSearch = async (q: string) => {
    if (!q || q.length < 1) return
    setSkillSearching(true)
    try {
      const res = await candidatesApi.searchSkills(q)
      const skills = (res as any)?.data?.data?.skills || []
      setSkillOptions(skills.map((s: any) => ({ value: s.name, label: s.name })))
    } catch {
      setSkillOptions([])
    } finally {
      setSkillSearching(false)
    }
  }

  const onFinish = async (values: any) => {
    if (!token) return
    setSubmitting(true)
    try {
      await candidatesApi.submitPublicForm(token, {
        ...values,
        highest_education: values.highest_education || '',
        graduation_year: values.graduation_year || null,
        nationality: values.nationality || '',
        work_authorization: values.work_authorization || 'not_specified',
        wants_account: wantsAccount,
      })
      setSubmitted(true)
    } catch (err: any) {
      message.error(
        err?.response?.data?.message || 'Submission failed'
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <Spin size="large" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <Result status="error" title="Invalid Link" subTitle={error} />
    </div>
  )

  if (submitted) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center border border-slate-100">
        <div className="h-16 w-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl text-emerald-500">✓</span>
        </div>
        <Title level={3} className="font-bold text-slate-900">Application Received!</Title>
        <Text className="text-slate-500 text-base block mb-6">
          Your details have been sent to {formConfig?.company_name}. 
          The team will review your profile and get in touch if there's a fit.
        </Text>
        {wantsAccount ? (
          <div className="mt-4 p-4 bg-indigo-50 rounded-2xl border border-indigo-100 text-left">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={16} className="text-indigo-600" />
              <Text className="font-bold text-indigo-900">TalentOS Account Created</Text>
            </div>
            <Text className="text-xs text-indigo-700 leading-relaxed">
              We've created your secure profile. Check your email to set a password. 
              You can now reuse this data for any future applications.
            </Text>
          </div>
        ) : (
          <Button block size="large" className="rounded-xl border-slate-200" onClick={() => window.location.reload()}>
            Finish
          </Button>
        )}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-12 px-4">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="h-16 w-16 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-indigo-200 shadow-xl">
            <span className="text-white font-black text-2xl uppercase">
              {formConfig?.company_name?.charAt(0)}
            </span>
          </div>
          <Title level={2} className="!mb-2 font-black tracking-tight text-slate-900">
            {formConfig?.company_name}
          </Title>
          {formConfig?.job_title ? (
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-50 text-indigo-700 rounded-full font-bold text-sm border border-indigo-100">
              <Briefcase size={14} />
              Applying for {formConfig.job_title}
            </div>
          ) : (
            <Text className="text-slate-500 text-base font-medium">
              Join our talent network and share your profile
            </Text>
          )}
        </div>

        {/* Form */}
        <div className="bg-white rounded-[24px] shadow-sm p-8 md:p-10 border border-slate-100">
          <Form form={form} layout="vertical" onFinish={onFinish} className="space-y-8">
            
            {/* ── Basic Info ── */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">1</div>
                <Text className="text-base font-bold text-slate-800">Basic Information</Text>
              </div>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
                    <Input placeholder="Jane" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
                    <Input placeholder="Doe" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="email" label="Email Address" rules={[{ required: true, type: 'email' }]}>
                <Input type="email" placeholder="jane@example.com" className="h-11 rounded-xl" />
              </Form.Item>
              <Form.Item name="phone" label="Phone Number" rules={[{ required: true }]}>
                <Input placeholder="+91 98765 43210" className="h-11 rounded-xl" />
              </Form.Item>
              <Form.Item name="linkedin_url" label="LinkedIn Profile URL">
                <Input placeholder="https://linkedin.com/in/yourname" className="h-11 rounded-xl" />
              </Form.Item>
            </section>

            <Divider className="!m-0" />

            {/* ── Professional Info ── */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">2</div>
                <Text className="text-base font-bold text-slate-800">Professional Experience</Text>
              </div>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="current_title" label="Current Job Title">
                    <Input placeholder="e.g. Senior Software Engineer" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="current_company" label="Current Company">
                    <Input placeholder="e.g. Acme Corp" className="h-11 rounded-xl" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="experience_years" label="Total Years of Exp">
                    <InputNumber min={0} step={0.5} placeholder="5" className="w-full h-11 rounded-xl flex items-center" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="relevant_experience_years" label="Relevant Exp (Optional)">
                    <InputNumber min={0} step={0.5} placeholder="3" className="w-full h-11 rounded-xl flex items-center" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="highest_education" label="Highest Education">
                    <Select placeholder="Select education level" 
                            className="h-11" options={[
                      { value: 'high_school', label: 'High School' },
                      { value: 'diploma', label: 'Diploma' },
                      { value: 'bachelor', label: "Bachelor's Degree" },
                      { value: 'master', label: "Master's Degree" },
                      { value: 'phd', label: 'PhD / Doctorate' },
                      { value: 'other', label: 'Other' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="graduation_year" label="Graduation Year">
                    <InputNumber 
                      min={1970} 
                      max={2030} 
                      placeholder="2020" 
                      className="w-full h-11 rounded-xl flex items-center" 
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="skills" label="Key Skills (Type and press Enter)">
                <Select
                  mode="tags"
                  placeholder="Search or add skills (e.g. Python, React, Sales)"
                  onSearch={handleSkillSearch}
                  options={skillOptions}
                  loading={skillSearching}
                  className="rounded-xl overflow-hidden"
                  size="large"
                />
              </Form.Item>
            </section>

            <Divider className="!m-0" />

            {/* ── Location & Preferences ── */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">3</div>
                <Text className="text-base font-bold text-slate-800">Preferences & Availability</Text>
              </div>
              <Form.Item name="current_location_city" label="Current City">
                <Input placeholder="e.g. Bengaluru, India" className="h-11 rounded-xl" />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="nationality" label="Nationality">
                    <Input 
                      placeholder="e.g. Indian, American" 
                      className="h-11 rounded-xl" 
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="work_authorization" 
                             label="Work Authorization">
                    <Select placeholder="Select status" 
                            className="h-11" options={[
                      { value: 'citizen', label: 'Citizen' },
                      { value: 'permanent_resident', 
                        label: 'Permanent Resident' },
                      { value: 'work_visa', label: 'Work Visa' },
                      { value: 'need_sponsorship', 
                        label: 'Needs Sponsorship' },
                      { value: 'not_specified', 
                        label: 'Prefer not to say' },
                    ]} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="availability_status" label="Availability">
                    <Select placeholder="Select status" className="h-11" options={[
                      { value: 'available_now', label: 'Available Now' },
                      { value: 'notice_period', label: 'Serving Notice' },
                      { value: 'open_to_offers', label: 'Open to Offers' },
                      { value: 'not_looking', label: 'Not Looking' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="notice_period_days" label="Notice Period (Days)">
                    <Select placeholder="Select days" className="h-11" options={[
                      { value: 0, label: 'Immediate' },
                      { value: 15, label: '15 Days' },
                      { value: 30, label: '30 Days' },
                      { value: 60, label: '60 Days' },
                      { value: 90, label: '90 Days' },
                    ]} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="work_mode_preference" label="Work Mode Preference">
                <Select placeholder="Select preference" className="h-11" options={[
                  { value: 'any', label: 'Any (Remote/On-site/Hybrid)' },
                  { value: 'remote', label: 'Remote Only' },
                  { value: 'hybrid', label: 'Hybrid' },
                  { value: 'onsite', label: 'On-site' },
                ]} />
              </Form.Item>
            </section>

            <Divider className="!m-0" />

            {/* ── Documents ── */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-8 w-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold">4</div>
                <Text className="text-base font-bold text-slate-800">Resume & Documents</Text>
              </div>
              <Form.Item name="resume_url" label="Public Resume Link (e.g. Google Drive, Dropbox)" rules={[{ required: true }]}>
                <Input placeholder="https://drive.google.com/..." className="h-11 rounded-xl" prefix={<FileText size={14} className="text-slate-400 mr-1" />} />
              </Form.Item>
              <Text className="text-[11px] text-slate-400 block -mt-4">
                Please ensure the link is shared with "Anyone with the link" permissions.
              </Text>
            </section>

            <Divider className="!m-0" />

            {/* ── Account ── */}
            <section>
              <div className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${
                wantsAccount ? 'border-indigo-200 bg-indigo-50/30' : 'border-slate-100 hover:border-slate-200 bg-slate-50/50'
              }`}
                onClick={() => setWantsAccount(!wantsAccount)}
              >
                <div className="flex items-start gap-4">
                  <Checkbox checked={wantsAccount} 
                    onChange={e => setWantsAccount(e.target.checked)}
                    onClick={e => e.stopPropagation()}
                    className="mt-1"
                  />
                  <div>
                    <p className="font-bold text-slate-900 text-sm m-0">Create a Secure TalentOS Profile</p>
                    <p className="text-slate-500 text-xs m-0 mt-1 leading-relaxed">
                      Join our talent network to save your details securely. Your profile can be reused for any company using TalentOS, and you'll get a personal dashboard to track your applications.
                    </p>
                  </div>
                </div>
              </div>

              {wantsAccount && (
                <div className="mt-6 pt-2">
                  <Form.Item name="password" label="Create a Secure Password"
                    rules={[{ required: true }, { min: 8, message: 'Minimum 8 characters required' }]}>
                    <Input.Password placeholder="At least 8 characters" className="h-11 rounded-xl" />
                  </Form.Item>
                </div>
              )}
            </section>

            <Button
              type="primary"
              htmlType="submit"
              block
              loading={submitting}
              className="h-14 rounded-2xl font-bold text-base bg-[#4F46E5] hover:bg-[#4338CA] border-none shadow-indigo-100 shadow-lg mt-4"
            >
              Submit Application
            </Button>

          </Form>
        </div>

        <div className="text-center mt-10">
          <p className="text-xs text-slate-400 font-medium flex items-center justify-center gap-1.5 uppercase tracking-widest">
            <Globe size={12} /> Securely Powered by TalentOS
          </p>
        </div>
      </div>
    </div>
  )
}
