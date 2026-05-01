import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Layout, Steps, Button, Card, Typography, Form, Input, Row, Col, Select, 
  InputNumber, DatePicker, Checkbox, Tag, message, Spin, Divider, Badge, Alert, List, Radio, Progress
} from 'antd'
import {
  ChevronRight, ChevronLeft, Save, Rocket, Briefcase, Users, Workflow, 
  BrainCircuit, ShieldCheck, Zap, AlertTriangle, CheckCircle2, LayoutGrid, Plus, Trash2, Sliders, Target, Box, Globe, ExternalLink, Activity, DollarSign, FileText
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { organisationApi } from '@/api/organisation'
import { agenciesApi } from '@/api/agencies'
import { interviewsApi } from '@/api/interviews'
import { cn } from '@/utils/cn'
import dayjs from 'dayjs'
import type { JobRequisition, InterviewPackage, JobStage } from '@/types'
import { useTranslation } from 'react-i18next'
import { CURRENCIES } from '@/utils/locale'

const { Content, Sider } = Layout
const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// ─── Steps Configuration ───────────────────────────────────────────────────

const STEPS = [
  { title: 'Job Info', icon: <Briefcase size={18} /> },
  { title: 'Hiring Team', icon: <Users size={18} /> },
  { title: 'Sourcing', icon: <Target size={18} /> },
  { title: 'Workflow', icon: <Workflow size={18} /> },
  { title: 'Interviews', icon: <Box size={18} /> },
  { title: 'Automation', icon: <BrainCircuit size={18} /> },
  { title: 'Offers', icon: <ShieldCheck size={18} /> },
  { title: 'Review', icon: <CheckCircle2 size={18} /> },
]

// ─── Main Component ─────────────────────────────────────────────────────────

export default function JobSetupStudio() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { t } = useTranslation(['jobs', 'common'])
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [jobData, setJobData] = useState<Partial<JobRequisition> | null>(null)

  const isEditMode = !!id

  // Data fetching
  const { data: requisitionData, isLoading: jobLoading } = useApiQuery(
    ['requisition', 'setup', id],
    () => requisitionsApi.get(id!),
    { enabled: isEditMode }
  )

  const { data: usersData } = useApiQuery(['org-users'], () => organisationApi.listUsers())
  const { data: departmentsData } = useApiQuery(['org-departments'], () => organisationApi.listDepartments())
  const { data: locsData } = useApiQuery(['org-locations'], () => organisationApi.listLocations())
  const { data: packagesData } = useApiQuery(['interview-packages'], () => interviewsApi.listPackages({ is_active: true }))
  const { data: bindingData } = useApiQuery(['job-interview-binding', id], () => interviewsApi.getJobBinding(id!), { enabled: !!id })
  const { data: agenciesData } = useApiQuery(['agencies-available'], () => agenciesApi.listAvailableAgencies())

  const users = ((usersData as any)?.users ?? [])
  const departments = ((departmentsData as any)?.departments ?? [])
  const locations = ((locsData as any)?.locations ?? [])
  const interviewPackages = ((packagesData as any)?.data?.packages ?? []) as InterviewPackage[]
  const currentBinding = (bindingData as any)?.data?.binding
  const availableAgencies = ((agenciesData as any)?.agencies ?? [])

  const { data: stagesData } = useApiQuery(['job-stages', id], () => requisitionsApi.listStages(id!), { enabled: !!id })
  const stages = ((stagesData as any)?.stages ?? []) as JobStage[]

  useEffect(() => {
    if (requisitionData) {
      const job = (requisitionData as any).requisition
      setJobData(job)
      form.setFieldsValue({
        ...job,
        job_owner_id: job.metadata?.job_owner_id,
        internal_recruiter_ids: job.metadata?.internal_recruiter_ids || [],
        target_date: job.target_date ? dayjs(job.target_date) : null,
        interview_package_id: currentBinding?.package_id,
        sourcing_mode: job.metadata?.sourcing_mode || 'hybrid',
        automation_enabled: job.metadata?.automation_enabled ?? true,
        agency_tenant_ids: job.metadata?.agency_tenant_ids || [],
        auto_distribute_to_agencies: Boolean((job as any).auto_distribute_to_agencies),
        agency_distribution_policy: (job as any).agency_distribution_policy || 'manual',
      })
    }
  }, [requisitionData, form, currentBinding])

  const handleNext = async () => {
    try {
      await form.validateFields()
      setCurrentStep(prev => prev + 1)
    } catch (err) {
      message.error('Please fix errors before proceeding.')
    }
  }

  const handleBack = () => setCurrentStep(prev => prev - 1)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      // 1. Prepare Metadata for orchestration flags
      const metadata = {
        ...(jobData?.metadata || {}),
        job_owner_id: values.job_owner_id,
        internal_recruiter_ids: values.internal_recruiter_ids,
        sourcing_mode: values.sourcing_mode,
        automation_enabled: values.automation_enabled,
        agency_tenant_ids: values.agency_tenant_ids
      }

      // 2. Prepare Payload - keeping supported schema fields at root
      const payload = {
        ...values,
        metadata,
        target_date: values.target_date ? dayjs(values.target_date).format('YYYY-MM-DD') : null
      }
      
      // Clean up fields that should stay in metadata only
      delete (payload as any).job_owner_id
      delete (payload as any).internal_recruiter_ids
      delete (payload as any).sourcing_mode
      delete (payload as any).automation_enabled
      delete (payload as any).interview_package_id
      delete (payload as any).agency_tenant_ids

      const res = isEditMode 
        ? await requisitionsApi.update(id!, payload)
        : await requisitionsApi.create(payload)
      
      const newJobId = (res as any)?.data?.data?.requisition?.id || id

      if (values.interview_package_id && values.interview_package_id !== currentBinding?.package_id) {
        await interviewsApi.bindJobPackage(newJobId, values.interview_package_id)
      }

      message.success(isEditMode ? 'Job configuration updated' : 'Job created successfully')
      navigate(`/jobs?id=${newJobId}`)
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to save job')
    } finally {
      setLoading(false)
    }
  }

  if (jobLoading) return <div className="h-screen flex items-center justify-center bg-white"><Spin size="large" tip="Initializing Studio..." /></div>

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-50 shadow-soft-sm">
        <div className="flex items-center gap-4">
          <Button icon={<ChevronLeft size={18} />} onClick={() => navigate('/jobs')} className="border-slate-200" />
          <Divider type="vertical" className="h-8 border-slate-200" />
          <div>
            <Title level={4} className="!m-0 text-slate-900 font-black tracking-tight uppercase tracking-widest leading-none">
              {isEditMode ? 'Job Setup Studio' : 'Job Creation Engine'}
            </Title>
            <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] block mt-1">
              {isEditMode ? `Configuring: ${jobData?.job_ref_id || 'REQUISITION'}` : 'New Enterprise Requisition'}
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button icon={<Save size={16} />} className="font-bold text-[11px] uppercase tracking-widest border-slate-200 h-10 px-6 rounded-xl">Save Draft</Button>
          <Button 
            type="primary" 
            onClick={() => currentStep === STEPS.length - 1 ? form.submit() : handleNext()} 
            loading={loading}
            className="bg-indigo-600 border-none font-black text-[11px] uppercase tracking-widest h-10 px-8 rounded-xl shadow-indigo-100 shadow-lg"
          >
            {currentStep === STEPS.length - 1 ? 'Publish & Launch' : 'Save & Continue'}
          </Button>
        </div>
      </header>

      <Layout className="flex-1 bg-transparent">
        <Sider width={300} className="bg-white border-r border-slate-200 hidden lg:block" theme="light">
          <div className="p-8">
            <Steps
              direction="vertical"
              current={currentStep}
              onChange={setCurrentStep}
              className="job-setup-steps"
              items={STEPS.map((step, idx) => ({
                title: <span className="text-[11px] font-black uppercase tracking-widest">{step.title}</span>,
                icon: (
                  <div className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-xl transition-all border",
                    currentStep === idx ? "bg-indigo-600 text-white border-indigo-600 shadow-soft-lg" : 
                    currentStep > idx ? "bg-emerald-50 text-emerald-600 border-emerald-100" : "bg-slate-50 text-slate-400 border-slate-100"
                  )}>
                    {currentStep > idx ? <CheckCircle2 size={16} /> : step.icon}
                  </div>
                )
              }))}
            />
          </div>
        </Sider>

        <Content className="overflow-y-auto custom-scrollbar bg-white">
          <div className="max-w-4xl mx-auto p-12">
            <Form form={form} layout="vertical" onFinish={onFinish} requiredMark="optional">
              
              {/* STEP 1: Basic Info */}
              {currentStep === 0 && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1 text-2xl uppercase">Job Identity & Parameters</Title>
                    <Paragraph className="text-slate-500 font-medium">Define the core identity, requirements, and compensation for this role.</Paragraph>
                  </div>
                  
                  {/* Group 1: Core Identity */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Target size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Core Identity</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Form.Item name="title" label="Job Title" rules={[{ required: true }]}>
                        <Input size="large" className="rounded-xl border-slate-200 h-12 text-lg font-bold" placeholder="e.g. Senior Backend Engineer" />
                      </Form.Item>

                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item name="department_id" label="Department" rules={[{ required: true }]}>
                            <Select size="large" className="rounded-xl" placeholder="Select department" options={departments.map((d: any) => ({ label: d.name, value: d.id }))} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="location" label="Location" rules={[{ required: true }]}>
                            <Input size="large" className="rounded-xl" placeholder="e.g. Bengaluru, India" />
                          </Form.Item>
                        </Col>
                      </Row>
                    </div>
                  </Card>

                  {/* Group 2: Hiring Parameters */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Sliders size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Hiring Parameters</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Row gutter={24}>
                        <Col span={8}>
                          <Form.Item name="job_type" label="Employment Type" rules={[{ required: true }]}>
                            <Select size="large" options={[
                              { value: 'full_time', label: 'Full Time' },
                              { value: 'part_time', label: 'Part Time' },
                              { value: 'contract', label: 'Contract' },
                              { value: 'internship', label: 'Internship' },
                              { value: 'freelance', label: 'Freelance' }
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="work_mode" label="Work Mode" rules={[{ required: true }]}>
                            <Select size="large" options={[
                              { value: 'remote', label: 'Remote' },
                              { value: 'onsite', label: 'On-site' },
                              { value: 'hybrid', label: 'Hybrid' }
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="priority" label="Priority">
                            <Select size="large" options={[
                              { value: 'low', label: 'Low' },
                              { value: 'medium', label: 'Medium' },
                              { value: 'high', label: 'High' },
                              { value: 'urgent', label: 'Urgent' }
                            ]} />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={24}>
                        <Col span={8}>
                          <Form.Item name="headcount" label="Headcount" rules={[{ required: true }]}>
                            <InputNumber size="large" min={1} className="w-full rounded-xl" />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="target_date" label="Target Date">
                            <DatePicker size="large" className="w-full rounded-xl" />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="budget_code" label="Budget Code">
                            <Input size="large" className="rounded-xl" placeholder="e.g. ENG-2026-04" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <div className="flex items-center gap-6 p-4 bg-slate-50 rounded-2xl border border-slate-100 mt-2">
                        <Form.Item name="is_confidential" valuePropName="checked" noStyle>
                          <Checkbox><span className="text-xs font-bold text-slate-600 uppercase tracking-tight">Confidential Job</span></Checkbox>
                        </Form.Item>
                        <Text className="text-[10px] text-slate-400 font-medium">Restricts visibility to assigned team only.</Text>
                      </div>
                    </div>
                  </Card>

                  {/* Group 3: Experience & Compensation */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <DollarSign size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Experience & Compensation</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item label="Experience Range (Years)">
                            <div className="flex items-center gap-3">
                              <Form.Item name="experience_min" noStyle><InputNumber placeholder="Min" min={0} className="w-full rounded-xl" /></Form.Item>
                              <span className="text-slate-300">—</span>
                              <Form.Item name="experience_max" noStyle><InputNumber placeholder="Max" min={0} className="w-full rounded-xl" /></Form.Item>
                            </div>
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="Annual Salary Bracket">
                            <div className="flex items-center gap-3">
                              <Form.Item name="salary_currency" noStyle rules={[{ required: true }]}>
                                <Select className="w-32 rounded-xl" options={CURRENCIES.map(c => ({ label: c.code, value: c.code }))} />
                              </Form.Item>
                              <Form.Item name="salary_min" noStyle><InputNumber placeholder="Min" min={0} className="w-full rounded-xl" /></Form.Item>
                              <span className="text-slate-300">—</span>
                              <Form.Item name="salary_max" noStyle><InputNumber placeholder="Max" min={0} className="w-full rounded-xl" /></Form.Item>
                            </div>
                          </Form.Item>
                        </Col>
                      </Row>
                      <div className="flex items-center gap-4">
                        <Form.Item name="salary_visible" valuePropName="checked" noStyle>
                          <Checkbox><span className="text-xs font-bold text-slate-600 uppercase tracking-tight">Show salary on job boards</span></Checkbox>
                        </Form.Item>
                      </div>
                    </div>
                  </Card>

                  {/* Group 4: Role Definition */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <FileText size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Role Definition</span>
                    </div>
                    <div className="p-6 space-y-6">
                      <Form.Item name="skills_required" label="Target Skills">
                        <Select mode="tags" size="large" placeholder="e.g. React, Node.js, System Design" className="rounded-xl" />
                      </Form.Item>
                      
                      <Form.Item name="description" label="The Mission (Description)">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What is the primary goal of this role?" />
                      </Form.Item>

                      <Form.Item name="responsibilities" label="Key Responsibilities">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What will this person do day-to-day?" />
                      </Form.Item>

                      <Form.Item name="requirements" label="Ideal Candidate (Requirements)">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What background and experience are you looking for?" />
                      </Form.Item>
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 2: Hiring Team */}
              {currentStep === 1 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Hiring Team & Ownership</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-2">
                    <Row gutter={24}>
                      <Col span={12}><Form.Item name="job_owner_id" label="Job Owner" rules={[{ required: true }]}><Select size="large" options={users.map((u: any) => ({ label: u.full_name, value: u.id }))} /></Form.Item></Col>
                      <Col span={12}><Form.Item name="hiring_manager_id" label="Hiring Manager"><Select size="large" options={users.map((u: any) => ({ label: u.full_name, value: u.id }))} /></Form.Item></Col>
                    </Row>
                    <Form.Item name="internal_recruiter_ids" label="Assigned Recruiters"><Select size="large" mode="multiple" options={users.map((u: any) => ({ label: u.full_name, value: u.id }))} /></Form.Item>
                  </Card>
                </div>
              )}

              {/* STEP 3: Sourcing Setup */}
              {currentStep === 2 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Sourcing Configuration</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-2">
                    <Form.Item name="sourcing_mode" label="Sourcing Mode">
                      <Radio.Group className="w-full">
                        <Row gutter={16}>
                          <Col span={8}><Radio.Button value="internal" className="w-full h-20 flex flex-col items-center justify-center rounded-xl font-bold">Internal Only</Radio.Button></Col>
                          <Col span={8}><Radio.Button value="hybrid" className="w-full h-20 flex flex-col items-center justify-center rounded-xl font-bold">Hybrid</Radio.Button></Col>
                          <Col span={8}><Radio.Button value="external" className="w-full h-20 flex flex-col items-center justify-center rounded-xl font-bold">Agency Driven</Radio.Button></Col>
                        </Row>
                      </Radio.Group>
                    </Form.Item>
                    <Form.Item name="agency_tenant_ids" label="Assign Agencies"><Select size="large" mode="multiple" options={availableAgencies.map((a: any) => ({ label: a.name, value: a.agency_tenant_id }))} /></Form.Item>
                    <Row gutter={24}>
                      <Col span={12}>
                        <Form.Item name="auto_distribute_to_agencies" valuePropName="checked">
                          <Checkbox>Auto distribute to agencies</Checkbox>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="agency_distribution_policy" label="Distribution Policy">
                          <Select size="large" options={[
                            { value: 'manual', label: 'Manual' },
                            { value: 'performance_ranked', label: 'Performance Ranked' },
                            { value: 'all', label: 'All Preferred Agencies' },
                          ]} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                </div>
              )}

              {/* STEP 4: Workflow Setup */}
              {currentStep === 3 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Pipeline & Workflow</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-6 bg-slate-50/50">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="h-10 w-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center"><LayoutGrid size={20} /></div>
                      <div>
                        <Text className="block text-sm font-black uppercase tracking-widest text-slate-800">Standard Hiring Flow</Text>
                        <Text className="text-[10px] font-bold text-slate-400 uppercase">System default pipeline stages active</Text>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'].map((s, i) => (
                        <div key={i} className="flex items-center gap-4 p-3 bg-white rounded-xl border border-slate-100">
                          <Badge count={i+1} style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
                          <Text className="font-bold text-slate-700 uppercase text-[11px] tracking-tight">{s}</Text>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 5: Interview Setup */}
              {currentStep === 4 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Interview Engine</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-2">
                    <Form.Item name="interview_package_id" label="Interview Package Template">
                      <Select size="large" options={interviewPackages.map(p => ({ label: p.title, value: p.id }))} />
                    </Form.Item>
                    {form.getFieldValue('interview_package_id') && (
                      <div className="bg-slate-50 p-6 rounded-2xl">
                        <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">Package Rounds Preview</Text>
                        <List dataSource={interviewPackages.find(p => p.id === form.getFieldValue('interview_package_id'))?.rounds} renderItem={(r: any, i) => (
                          <List.Item className="bg-white p-3 rounded-xl border border-slate-100 mb-2 border-none">
                            <Badge count={i+1} className="mr-3" style={{ backgroundColor: '#4f46e5' }} /> <Text className="font-bold uppercase text-[11px] text-slate-700">{r.name}</Text>
                          </List.Item>
                        )} />
                      </div>
                    )}
                  </Card>
                </div>
              )}

              {/* STEP 6: Automation Setup */}
              {currentStep === 5 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Automation Engine</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-6">
                    <div className="flex items-center justify-between p-4 bg-indigo-50 rounded-2xl border border-indigo-100 mb-6">
                      <div className="flex items-center gap-3">
                        <BrainCircuit size={24} className="text-indigo-600" />
                        <div>
                          <Text className="block text-xs font-black text-indigo-700 uppercase tracking-widest">Hiring AI Brain</Text>
                          <Text className="text-[10px] font-bold text-indigo-500 uppercase">Autonomous orchestration enabled</Text>
                        </div>
                      </div>
                      <Form.Item name="automation_enabled" valuePropName="checked" noStyle><Checkbox /></Form.Item>
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between text-slate-600"><Text className="text-[11px] font-bold uppercase">Auto-assign best recruiter</Text><Tag color="blue">Active</Tag></div>
                      <div className="flex items-center justify-between text-slate-600"><Text className="text-[11px] font-bold uppercase">SLA Breach detection</Text><Tag color="blue">Active</Tag></div>
                      <div className="flex items-center justify-between text-slate-600"><Text className="text-[11px] font-bold uppercase">AI screening threshold</Text><Tag color="blue">Active</Tag></div>
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 7: Offer Setup */}
              {currentStep === 6 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Offer Foundations</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-2">
                    <Row gutter={24}>
                      <Col span={8}><Form.Item name="salary_currency" label="Currency"><Select size="large" options={CURRENCIES.map(c => ({ label: c.code, value: c.code }))} /></Form.Item></Col>
                      <Col span={8}><Form.Item name="salary_min" label="Min Salary"><InputNumber size="large" className="w-full" /></Form.Item></Col>
                      <Col span={8}><Form.Item name="salary_max" label="Max Salary"><InputNumber size="large" className="w-full" /></Form.Item></Col>
                    </Row>
                  </Card>
                </div>
              )}

              {/* STEP 8: Final Review */}
              {currentStep === STEPS.length - 1 && (
                <div className="animate-in fade-in duration-700 space-y-8 text-center py-12">
                  <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-soft-lg"><CheckCircle2 size={40} /></div>
                  <Title level={2} className="font-black tracking-tight text-slate-900">Configuration Complete</Title>
                  <Paragraph className="text-slate-500 font-medium">Your job requisition is ready for launch. Review final metrics below.</Paragraph>
                  <Card className="text-left rounded-3xl border-slate-100 bg-slate-50/50 p-8 shadow-soft-sm">
                    <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-6">Launch Summary</Text>
                    <div className="grid grid-cols-2 gap-x-12 gap-y-6">
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Title</Text><Text className="font-bold text-slate-800 uppercase text-sm">{form.getFieldValue('title')}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Department</Text><Text className="font-bold text-slate-800 uppercase text-sm">{departments.find((d: any) => d.id === form.getFieldValue('department_id'))?.name || 'N/A'}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Headcount</Text><Text className="font-bold text-indigo-600 uppercase text-lg">{form.getFieldValue('headcount')}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Priority</Text><Tag className="w-fit font-black text-[9px] uppercase border-none bg-rose-50 text-rose-600">{form.getFieldValue('priority')}</Tag></div>
                    </div>
                  </Card>
                </div>
              )}

              <div className={cn("mt-12 pt-8 border-t border-slate-200 flex items-center justify-between", currentStep === STEPS.length - 1 ? "hidden" : "")}>
                <Button disabled={currentStep === 0} onClick={handleBack} className="h-12 px-8 rounded-2xl font-black text-[11px] uppercase tracking-widest border-slate-200 text-slate-500 hover:bg-slate-50"><ChevronLeft size={18} className="mr-2" /> Previous</Button>
                <Button type="primary" onClick={handleNext} className="bg-indigo-600 border-none h-12 px-10 rounded-2xl font-black text-[11px] uppercase tracking-widest shadow-indigo-100 shadow-lg">Save & Continue <ChevronRight size={18} className="ml-2" /></Button>
              </div>
            </Form>
          </div>
        </Content>

        <Sider width={320} className="bg-[#F8FAFC] border-l border-slate-200 hidden xl:block p-8" theme="light">
          <div className="sticky top-24 space-y-6">
            <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-soft-sm">
              <div className="flex justify-between items-center mb-2">
                <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Setup Progress</Text>
                <Text className="text-[10px] font-black text-indigo-600">{Math.round((currentStep / (STEPS.length - 1)) * 100)}%</Text>
              </div>
              <Progress percent={Math.round((currentStep / (STEPS.length - 1)) * 100)} strokeColor="#4f46e5" showInfo={false} size="small" />
            </div>
            
            <Alert 
              message={<span className="text-[10px] font-black uppercase text-indigo-700">Studio Intelligence</span>} 
              description={<p className="text-[11px] text-indigo-600/80 font-medium m-0 leading-relaxed">System recommends attaching an 'Engineering Standard' interview package for this role type.</p>} 
              type="info" 
              showIcon 
              icon={<BrainCircuit size={16} />} 
              className="rounded-2xl border-indigo-100 bg-indigo-50/50" 
            />
          </div>
        </Sider>
      </Layout>
    </div>
  )
}
