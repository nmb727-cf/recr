import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Button, Input, Select, Typography, Row, Col, Card,
  Drawer, Tag, Tabs, Spin, Badge, message, Space, Modal, InputNumber, DatePicker, Form
} from 'antd'
import {
  Plus,
  Search,
  Briefcase,
  Download,
  RefreshCw,
  ChevronRight,
  ArrowRight,
  Send,
  CheckCircle,
  Globe,
  LayoutGrid,
  ChevronLeft
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { requisitionsApi } from '@/api/jobs'
import { agenciesApi } from '@/api/agencies'
import { pipelineApi } from '@/api/pipeline'
import type { JobRequisition, AgencyRelationship } from '@/types'
import { cn } from '@/utils/cn'
import JobCreateForm from '@/components/forms/JobCreateForm'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Title, Text } = Typography

// ─── Status Config ──────────────────────────────────────────────────────────

const JOB_STATUS_OPTIONS = [
  { value: 'active', label: 'Active Jobs' },
  { value: 'paused', label: 'Paused Jobs' },
  { value: 'in_guarantee_period', label: 'In Guarantee Period' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'approved', label: 'Approved (Not Published)' },
  { value: 'draft', label: 'Drafts' },
  { value: 'closed', label: 'Closed Jobs' },
]

// ─── Sub-components ─────────────────────────────────────────────────────────

function AssignAgencyModal({
  open,
  jobId,
  onClose,
  onSuccess,
}: {
  open: boolean
  jobId: string
  onClose: () => void
  onSuccess: () => void
}) {
  const { t } = useTranslation(['jobs', 'common'])
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data: agenciesData, isLoading: agenciesLoading } = useApiQuery(
    ['agencies-active'],
    () => agenciesApi.listRelationships(),
    { enabled: open }
  )

  const agencies = (
    (agenciesData as any)?.relationships ??
    (agenciesData as any)?.data?.relationships ??
    []
  ) as AgencyRelationship[]

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      await agenciesApi.createAssignment({
        agency_tenant_id: values.agency_tenant_id,
        requisition_id: jobId,
        max_submissions: values.max_submissions,
        deadline: values.deadline.format('YYYY-MM-DD'),
        notes: values.notes,
      })
      message.success(t('jobs:messages.assigned_success', 'Job assigned to agency successfully'))
      form.resetFields()
      onSuccess()
    } catch (err: any) {
      if (err?.errorFields) return
      message.error(err?.response?.data?.message || t('jobs:messages.assigned_error', 'Failed to assign agency'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold text-slate-900">{t('jobs:actions.assign_agency', 'Assign Agency to this Job')}</span>}
      open={open}
      onCancel={onClose}
      onOk={handleSubmit}
      okText={t('jobs:actions.assign_agency_cta', 'Assign Agency')}
      confirmLoading={submitting}
      okButtonProps={{ className: 'bg-blue-600 border-none font-bold' }}
      width={520}
      destroyOnClose
    >
      <Form form={form} layout="vertical" className="mt-4">
        <Form.Item name="agency_tenant_id" label={t('jobs:fields.agency_partner', 'Agency Partner')} rules={[{ required: true, message: t('jobs:validation.select_agency', 'Select an agency') }]}>
          <Select
            placeholder={t('jobs:placeholders.select_agency', 'Select partner agency...')}
            loading={agenciesLoading}
            showSearch
            options={agencies
              .map((a: any) => {
                const agencyId = a?.agency_tenant_id || a?.agency_id
                if (!agencyId) return null
                const label = a?.agency?.name || a?.agency_name || `Agency ${String(agencyId).slice(0, 8)}`
                return { value: agencyId, label }
              })
              .filter(Boolean) as Array<{ value: string; label: string }>}
            className="h-10"
          />
        </Form.Item>
        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="max_submissions" label={t('jobs:fields.submission_limit', 'Submission Limit')} rules={[{ required: true }]} initialValue={5}>
            <InputNumber min={1} max={100} className="w-full h-10" />
          </Form.Item>
          <Form.Item name="deadline" label={t('jobs:fields.deadline', 'Deadline')} rules={[{ required: true }]}>
            <DatePicker className="w-full h-10" disabledDate={d => d.isBefore(dayjs())} />
          </Form.Item>
        </div>
        <Form.Item name="notes" label={t('jobs:fields.special_instructions', 'Special Instructions')}>
          <Input.TextArea rows={3} placeholder={t('jobs:placeholders.special_instructions', 'Any specific requirements for this agency...')} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

const FullJobList = ({ jobs, onSelect, selectedJobId, isLoading }: any) => {
  const jobList = Array.isArray(jobs) ? jobs : []

  const columns: ColumnsType<JobRequisition> = [
    {
      title: 'Job Role',
      dataIndex: 'title',
      key: 'title',
      render: (title, record) => (
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Briefcase className="h-4.5 w-4.5" />
          </div>
          <div>
            <Text className="block font-bold text-slate-900 leading-tight">{title || 'Untitled'}</Text>
            <Text className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
              {record?.location_id || 'Remote'} • {record?.job_type?.replace('_', ' ') || 'Full Time'}
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: string) => {
        const config = getStatusStyle(status, 'job')
        return (
          <div className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider", config.softClass)}>
            <span className={cn("h-1 w-1 rounded-full", config.dotClass)} />
            {formatStatusLabel(status)}
          </div>
        )
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => (
        <Tag color={priority === 'high' || priority === 'urgent' ? 'red' : priority === 'medium' ? 'orange' : 'blue'} 
             className="m-0 border-none font-bold text-[10px] uppercase rounded px-2">
          {priority || 'Medium'}
        </Tag>
      )
    },
    {
      title: 'Applications',
      key: 'applications',
      width: 150,
      render: (_, record) => {
        const metadata = record?.metadata || {}
        return (
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <Badge count={Number(metadata?.applications_count) || 0} showZero overflowCount={999} 
                     style={{ backgroundColor: '#3b82f6', fontSize: '10px' }} />
              <Text className="text-[11px] font-bold text-slate-400 uppercase">Total</Text>
            </div>
            <div className="flex gap-1 mt-1">
               <div className="bg-slate-100 rounded px-1.5 py-0.5 text-[9px] font-bold text-slate-500">APP {Number(metadata?.applied) || 0}</div>
               <div className="bg-blue-50 rounded px-1.5 py-0.5 text-[9px] font-bold text-blue-600">INT {Number(metadata?.interview) || 0}</div>
               <div className="bg-emerald-50 rounded px-1.5 py-0.5 text-[9px] font-bold text-emerald-600">OFF {Number(metadata?.offer) || 0}</div>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created',
      width: 120,
      render: (date) => <Text className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">{date ? dayjs(date).format('MMM D, YYYY') : 'N/A'}</Text>
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />
    }
  ]

  return (
    <Table<JobRequisition>
      columns={columns}
      dataSource={jobList}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          "cursor-pointer transition-all duration-200",
          record.id === selectedJobId ? "bg-blue-50 hover:bg-blue-50" : "hover:bg-slate-50"
        ),
      })}
      pagination={{ pageSize: 10, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedJobList = ({ jobs, onSelect, selectedJobId }: any) => {
  const { t } = useTranslation('jobs')
  const jobList = Array.isArray(jobs) ? jobs : []
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
        <Text className="font-bold text-slate-900">{t('list.all_jobs', 'All Jobs')}</Text>
        <Badge count={jobList.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
      </div>
      {jobList.map((item: any) => (
        <div 
          key={item.id}
          onClick={() => onSelect(item)}
          className={cn(
            "p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
            item.id === selectedJobId 
              ? "bg-blue-50/50 border-l-blue-600" 
              : "bg-white border-l-transparent hover:bg-slate-50"
          )}
        >
          <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
            {item.title || 'Untitled'}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <div className={cn(
              "text-[9px] font-bold uppercase px-1.5 py-0.5 rounded",
              getStatusStyle(item.status, 'job').softClass
            )}>
              {formatStatusLabel(item.status || 'draft')}
            </div>
            <Text className="text-[10px] text-slate-400 font-medium truncate uppercase">
              {item.location_id || 'Remote'}
            </Text>
          </div>
        </div>
      ))}
    </div>
  )
}

const JobDetailPanel = ({
  job,
  onClose,
  onEdit,
}: {
  job: JobRequisition
  onClose: () => void
  onEdit: (job: JobRequisition) => void
}) => {
  const { t } = useTranslation(['jobs', 'common'])
  const jobId = job?.id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [assignModalOpen, setAssignModalOpen] = useState(false)

  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['job-pipeline', jobId],
    () => pipelineApi.getPipeline(jobId),
    { enabled: !!jobId }
  )

  const { data: agenciesData, refetch: refetchAgencies } = useApiQuery(
    ['job-agencies', jobId],
    () => agenciesApi.listAssignments({ requisition_id: jobId }),
    { enabled: !!jobId }
  )
  const { data: requisitionDetail } = useApiQuery(
    ['job-detail', jobId],
    () => requisitionsApi.get(jobId!),
    { enabled: !!jobId }
  )

  // Actions
  const submitMutation = useMutation({
    mutationFn: () => requisitionsApi.submitForApproval(jobId!),
    onSuccess: () => {
      message.success(t('jobs:messages.submitted_for_approval', 'Requisition submitted for approval'))
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const approveMutation = useMutation({
    mutationFn: () => requisitionsApi.approve(jobId!),
    onSuccess: () => {
      message.success(t('jobs:messages.approved', 'Requisition approved'))
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const publishMutation = useMutation({
    mutationFn: () => requisitionsApi.publish(jobId!),
    onSuccess: () => {
      message.success(t('jobs:messages.published_active', 'Requisition published and is now ACTIVE'))
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const pipeline = (pipelineData as any)?.data?.pipeline || {}
  const assignments = Array.isArray((agenciesData as any)?.data?.assignments) ? (agenciesData as any).data.assignments : []
  const placementGuarantees = (
    (requisitionDetail as any)?.placement_guarantees ??
    (requisitionDetail as any)?.data?.placement_guarantees ??
    []
  ) as Array<any>

  const formatSalary = (amount: any) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: job?.salary_currency || 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const tabItems = [
    {
      key: 'overview',
      label: t('jobs:tabs.overview', 'Overview'),
      children: (
        <div className="p-6">
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Experience', value: `${job?.experience_min || 0}-${job?.experience_max || 0} years` },
              { label: 'Salary Range', value: `${formatSalary(job?.salary_min)} - ${formatSalary(job?.salary_max)}` },
              { label: 'Headcount', value: job?.headcount || 0 },
              { label: 'Job Type', value: job?.job_type?.replace('_', ' ') || 'N/A' },
              { label: 'Work Mode', value: job?.work_mode || 'N/A' },
              { label: 'Priority', value: job?.priority || 'Medium', type: 'tag' },
              { label: 'Agencies', value: assignments.length },
              { label: 'Hiring Status', value: formatStatusLabel(job?.hiring_status || 'active_hiring') },
              {
                label: 'Guarantee Watch Until',
                value: job?.guarantee_watch_until ? dayjs(job.guarantee_watch_until).format('MMM D, YYYY') : 'N/A'
              }
            ].map((stat, i) => (
              <div key={i} className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</Text>
                {stat.type === 'tag' ? (
                  <Tag color={stat.value === 'high' ? 'red' : 'blue'} className="m-0 font-bold uppercase text-[11px]">{stat.value as string}</Tag>
                ) : (
                  <Text className="block font-bold text-slate-700">{stat.value}</Text>
                )}
              </div>
            ))}
          </div>

          <div className="space-y-6">
            {placementGuarantees.length > 0 && (
              <div>
                <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">
                  Post Placement Monitoring
                </Title>
                <div className="space-y-2">
                  {placementGuarantees.slice(0, 5).map((g: any) => (
                    <div key={g.id} className="rounded-xl border border-amber-100 bg-amber-50 p-3">
                      <div className="flex items-center justify-between">
                        <Text className="font-bold text-amber-900 text-xs uppercase tracking-wide">{(g.status || 'active').replace(/_/g, ' ')}</Text>
                        <Text className="text-[11px] text-amber-700">Ends: {g.guarantee_end_date ? dayjs(g.guarantee_end_date).format('MMM D, YYYY') : 'N/A'}</Text>
                      </div>
                      <Text className="text-[11px] text-amber-700">Resolution: {(g.guarantee_resolution_type || 'replacement_only').replace(/_/g, ' ')}</Text>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Description</Title>
              <Text className="text-slate-600 leading-relaxed block whitespace-pre-wrap">{job?.description || 'No description provided.'}</Text>
            </div>
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Requirements</Title>
              <Text className="text-slate-600 leading-relaxed block whitespace-pre-wrap">{job?.requirements || 'No requirements specified.'}</Text>
            </div>
          </div>
        </div>
      )
    },
    {
      key: 'pipeline',
      label: t('jobs:tabs.pipeline', 'Pipeline'),
      children: (
        <div className="p-6 overflow-x-auto">
          {pipelineLoading ? <Spin /> : (
            <div className="flex gap-4 min-w-max pb-4">
              {Object.entries(pipeline).map(([stageId, stageData]: [string, any]) => (
                <div key={stageId} className="w-64 shrink-0 bg-slate-50/50 rounded-2xl p-4 border border-slate-200 shadow-soft-sm">
                  <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                    <Text className="font-bold text-slate-900 text-xs uppercase tracking-widest">{stageData?.stage?.name || 'Stage'}</Text>
                    <Badge count={stageData?.count || 0} showZero size="small" style={{ backgroundColor: '#fff', color: '#64748b', border: '1px solid #e2e8f0', boxShadow: 'none' }} />
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(stageData?.applications) && stageData.applications.map((app: any) => (
                      <div key={app.id} className="bg-white rounded-xl p-3 border border-slate-100 shadow-soft-sm">
                        <Text className="block font-bold text-slate-700 text-xs mb-1">
                          {app.candidate_name || `Candidate #${app.id?.substring(0, 5)}`}
                        </Text>
                        <div className="flex items-center justify-between">
                          <Tag className="m-0 text-[9px] uppercase font-bold border-none bg-slate-100 text-slate-500">{app.status || 'applied'}</Tag>
                          <ArrowRight className="h-3 w-3 text-slate-300" />
                        </div>
                      </div>
                    ))}
                    {(stageData?.count === 0 || !stageData?.applications?.length) && <div className="py-8 text-center text-slate-300 text-[10px] font-bold uppercase tracking-widest">No candidates</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Detail Header - Consistent UX */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Button icon={<ChevronLeft className="h-4 w-4" />} onClick={onClose} className="h-8 w-8 flex items-center justify-center rounded-lg border-slate-200" />
          <div>
            <div className="flex items-center gap-3 mb-0.5">
               <Title level={4} className="!m-0 text-slate-900">{job?.title || 'Untitled'}</Title>
               <Tag className={cn("m-0 border-none font-bold text-[9px] uppercase rounded-full px-2", getStatusStyle(job?.status || 'draft', 'job').softClass)}>
                  {formatStatusLabel(job?.status || 'draft')}
               </Tag>
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              {job?.location_id || 'Remote'} · {job?.priority || 'Medium'} Priority
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            className="h-9 font-bold px-4 rounded-lg"
            onClick={() => onEdit(job)}
          >
            Edit
          </Button>
          <Button 
            type="primary" 
            className="h-9 font-bold px-4 rounded-lg bg-blue-600 border-none shadow-soft-sm"
            onClick={() => navigate(`/pipeline?job=${jobId}`)}
            icon={<LayoutGrid className="h-4 w-4" />}
          >
            Pipeline
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Quick Actions Bar */}
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
           <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Workflow Actions</Text>
           <Space>
              {job?.status === 'draft' && (
                <Button 
                  size="small" 
                  icon={<Send className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg"
                  loading={submitMutation.isPending}
                  onClick={() => submitMutation.mutate()}
                >
                  Submit
                </Button>
              )}
              {job?.status === 'pending_approval' && (
                <Button 
                  size="small" 
                  type="primary" 
                  icon={<CheckCircle className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg bg-blue-600 border-none"
                  loading={approveMutation.isPending}
                  onClick={() => approveMutation.mutate()}
                >
                  Approve
                </Button>
              )}
              {job?.status === 'approved' && (
                <Button 
                  size="small" 
                  type="primary" 
                  icon={<Globe className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg bg-emerald-600 border-none"
                  loading={publishMutation.isPending}
                  onClick={() => publishMutation.mutate()}
                >
                  Publish
                </Button>
              )}
              {job?.status === 'active' && (
                <Button 
                  size="small" 
                  icon={<Plus className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg"
                  onClick={() => setAssignModalOpen(true)}
                >
                  {t('jobs:actions.assign_agency_short', 'Assign Agency')}
                </Button>
              )}
           </Space>
        </div>

        <Tabs 
          defaultActiveKey="overview" 
          items={tabItems} 
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>

      <AssignAgencyModal
        open={assignModalOpen}
        jobId={jobId!}
        onClose={() => setAssignModalOpen(false)}
        onSuccess={() => {
          setAssignModalOpen(false)
          refetchAgencies()
        }}
      />
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobsList() {
  const { t } = useTranslation(['jobs', 'common'])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedJob, setSelectedJob] = useState<JobRequisition | null>(null)
  const [createDrawerOpen, setCreateDrawerOpen] = useState(false)
  const [editingJob, setEditingJob] = useState<JobRequisition | null>(null)

  const { data, isLoading, refetch } = useApiQuery(
    ['jobs', statusFilter, search],
    () => requisitionsApi.list({
      status: statusFilter || undefined,
      search: search || undefined,
    })
  )

  // useApiQuery already unwraps ApiResponse -> data, so requisitions are usually at data.requisitions.
  // Keep a fallback for older nested usage to avoid regressions during API contract transitions.
  const requisitions =
    ((data as any)?.requisitions as JobRequisition[] | undefined) ??
    ((data as any)?.data?.requisitions as JobRequisition[] | undefined) ??
    []

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6">
      {/* Top Header / Actions */}
      {!selectedJob && (
        <div className="p-6 pb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{t('jobs:page.title', 'Jobs')}</h1>
            <p className="text-slate-500 mt-1">{t('jobs:page.subtitle', 'Create, publish, and manage requisitions')}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button icon={<Download className="h-4 w-4" />} className="flex items-center gap-2 font-bold h-10 rounded-xl">{t('common:actions.export', 'Export')}</Button>
            <Button 
              type="primary" 
              icon={<Plus className="h-4 w-4" />} 
              className="flex items-center gap-2 font-bold h-10 rounded-xl bg-blue-600 border-none shadow-soft-md"
              onClick={() => setCreateDrawerOpen(true)}
            >
              {t('jobs:actions.create_job', 'Create Job')}
            </Button>
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      {!selectedJob && (
        <div className="px-6 pb-6">
          <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '12px' } }}>
            <Row gutter={[12, 12]} align="middle">
              <Col xs={24} md={12}>
                <Input
                  prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                  placeholder={t('jobs:search.placeholder', 'Search by role, location, or department...')}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-10 text-sm border-slate-200 rounded-xl"
                  allowClear
                />
              </Col>
              <Col xs={12} md={8}>
                <Select
                  className="w-full h-10"
                  placeholder={t('jobs:filters.status', 'Status')}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  allowClear
                  options={JOB_STATUS_OPTIONS}
                />
              </Col>
              <Col xs={12} md={4}>
                <Button
                  icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />}
                  onClick={() => refetch()}
                  className="w-full h-10 flex items-center justify-center rounded-xl border-slate-200 font-bold"
                >
                  {t('common:actions.refresh', 'Refresh')}
                </Button>
              </Col>
            </Row>
          </Card>
        </div>
      )}

      <StandardSplitView
        isDetailOpen={!!selectedJob}
        compactListContent={
          <CompressedJobList
            jobs={requisitions}
            selectedJobId={selectedJob?.id}
            onSelect={setSelectedJob}
          />
        }
        fullListContent={
          <div className="p-6 pt-0 h-full overflow-y-auto">
            <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
              <FullJobList
                jobs={requisitions}
                onSelect={setSelectedJob}
                isLoading={isLoading}
              />
            </Card>
          </div>
        }
        detailContent={
          selectedJob ? (
            <JobDetailPanel
              job={selectedJob}
              onClose={() => setSelectedJob(null)}
              onEdit={(job) => {
                setEditingJob(job)
                setCreateDrawerOpen(true)
              }}
            />
          ) : null
        }
      />

      {/* Create Job Drawer */}
      <Drawer
        open={createDrawerOpen}
        onClose={() => {
          setCreateDrawerOpen(false)
          setEditingJob(null)
        }}
        width={640}
        title={<span className="text-lg font-bold">{editingJob ? t('jobs:actions.edit_job', 'Edit Job Requisition') : t('jobs:actions.create_job_drawer', 'Create New Job Requisition')}</span>}
        destroyOnClose
      >
        <JobCreateForm onSuccess={() => {
          setCreateDrawerOpen(false)
          setEditingJob(null)
          refetch()
        }} initialValues={editingJob} />
      </Drawer>
    </div>
  )
}
