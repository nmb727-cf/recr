import { useState } from 'react'
import {
  Button, Card, Descriptions, Tag, Avatar, Space,
  Typography, Spin, Empty, Tabs, Table, Divider,
  message, Modal, Input
} from 'antd'
import {
  Edit, Briefcase,
  Activity, MapPin, Plus, CheckCircle, X
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import type { JobRequisition, RequisitionStatus, Application } from '@/types'
import { cn } from '@/utils/cn'
import PipelineBoard from '../pipeline/PipelineBoard'

const { Title, Text, Paragraph } = Typography

const STATUS_CONFIG: Record<RequisitionStatus, { label: string, color: string, dot: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
  pending_approval: { label: 'Pending', color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  approved: { label: 'Approved', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-400' },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  closed: { label: 'Closed', color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300' },
}

// ─── Tabs ───────────────────────────────────────────────────────────────────

function OverviewTab({ requisition }: { requisition: JobRequisition }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title={<span className="text-sm font-bold text-slate-900">Job Details</span>} bordered={false} className="shadow-soft-sm">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Type">{requisition.job_type.replace('_', ' ')}</Descriptions.Item>
            <Descriptions.Item label="Mode">{requisition.work_mode}</Descriptions.Item>
            <Descriptions.Item label="Headcount">{requisition.headcount}</Descriptions.Item>
            <Descriptions.Item label="Experience">{requisition.experience_min}-{requisition.experience_max}y</Descriptions.Item>
          </Descriptions>
        </Card>
        <Card title={<span className="text-sm font-bold text-slate-900">Salary</span>} bordered={false} className="shadow-soft-sm">
          {requisition.salary_visible ? (
            <div>
              <Text className="text-2xl font-bold text-slate-900">
                {requisition.salary_currency} {Number(requisition.salary_min).toLocaleString()}
              </Text>
              <Text className="block text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-wider">Minimum per annum</Text>
            </div>
          ) : (
            <Text className="italic text-slate-400 text-sm">Salary hidden from candidates</Text>
          )}
        </Card>
        <Card title={<span className="text-sm font-bold text-slate-900">Location</span>} bordered={false} className="shadow-soft-sm">
          <div className="flex items-center gap-2 text-slate-600">
            <MapPin className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-semibold">{requisition.location_id || 'Remote / Head Office'}</span>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card title={<span className="text-base font-bold text-slate-900">Full Description</span>} bordered={false} className="shadow-soft-sm">
          <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">
            {requisition.description}
          </Paragraph>
          
          {requisition.requirements && (
            <>
              <Divider className="my-6" />
              <Title level={5} className="!text-sm !font-bold !text-slate-900 !mb-3 uppercase tracking-wider">Core Requirements</Title>
              <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">
                {requisition.requirements}
              </Paragraph>
            </>
          )}

          {requisition.responsibilities && (
            <>
              <Divider className="my-6" />
              <Title level={5} className="!text-sm !font-bold !text-slate-900 !mb-3 uppercase tracking-wider">Key Responsibilities</Title>
              <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">
                {requisition.responsibilities}
              </Paragraph>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}

function ApplicationsTab({ jobId, onRefresh }: { jobId: string, onRefresh: () => void }) {
  const { data, isLoading, refetch } = useApiQuery(['job-applications-full', jobId], () => 
    pipelineApi.listApplications({ requisition_id: jobId })
  )
  const applications = (data as any)?.applications ?? []

  const [rejectModal, setRejectModal] = useState<{ open: boolean, app: Application | null }>({ open: false, app: null })
  const [rejectReason, setRejectReason] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const handleShortlist = async (appId: string) => {
    try {
      await pipelineApi.shortlist(appId)
      message.success('Candidate shortlisted')
      refetch()
      onRefresh()
    } catch {
      message.error('Failed to shortlist')
    }
  }

  const handleReject = async () => {
    if (!rejectModal.app) return
    setActionLoading(true)
    try {
      await pipelineApi.reject(rejectModal.app.id, rejectReason)
      message.success('Candidate rejected')
      setRejectModal({ open: false, app: null })
      setRejectReason('')
      refetch()
      onRefresh()
    } catch {
      message.error('Failed to reject candidate')
    } finally {
      setActionLoading(false)
    }
  }

  const columns = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_: any, record: Application) => (
        <div className="flex items-center gap-3">
          <Avatar className="bg-blue-50 text-blue-600 font-bold border-none">
            {record.candidate_id.slice(0, 1).toUpperCase()}
          </Avatar>
          <Text className="font-bold text-slate-900">Candidate {record.candidate_id.slice(0, 4)}</Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <Tag className="rounded-full px-2.5 py-0.5 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase tracking-wider">{s.replace('_', ' ')}</Tag>
    },
    {
      title: 'Match Score',
      dataIndex: 'match_score',
      key: 'match',
      render: (score: number) => <span className="font-bold text-emerald-600">{score}%</span>
    },
    {
      title: 'Applied Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d: string) => <span className="text-slate-500 text-sm">{dayjs(d).format('MMM D, YYYY')}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Application) => (
        <Space>
          {record.status === 'applied' && (
            <Button size="small" type="text" icon={<CheckCircle className="h-4 w-4 text-emerald-600" />} onClick={() => handleShortlist(record.id)}>Shortlist</Button>
          )}
          <Button size="small" type="text" danger icon={<X className="h-4 w-4" />} onClick={() => setRejectModal({ open: true, app: record })}>Reject</Button>
        </Space>
      )
    }
  ]

  return (
    <>
      <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
        <Table 
          dataSource={applications} 
          columns={columns} 
          rowKey="id" 
          loading={isLoading} 
          pagination={{ pageSize: 10, className: "px-6" }}
          className="modern-table"
        />
      </Card>

      <Modal
        title="Reject Application"
        open={rejectModal.open}
        onCancel={() => setRejectModal({ open: false, app: null })}
        onOk={handleReject}
        confirmLoading={actionLoading}
        okText="Reject Candidate"
        okButtonProps={{ danger: true }}
      >
        <p className="text-slate-500 mb-4 text-sm font-medium">Please provide a reason for rejection (optional):</p>
        <Input.TextArea rows={3} value={rejectReason} onChange={e => setRejectReason(e.target.value)} placeholder="e.g. Insufficient technical experience..." />
      </Modal>
    </>
  )
}

function InterviewsTab({ jobId }: { jobId: string }) {
  const { data, isLoading } = useApiQuery(['job-interviews-full', jobId], () => 
    interviewsApi.list({ requisition_id: jobId })
  )
  const interviews = (data as any)?.interviews ?? []

  const columns = [
    {
      title: 'Candidate',
      dataIndex: 'candidate_name',
      key: 'candidate',
      render: (name: string) => <Text className="font-bold text-slate-900">{name || 'N/A'}</Text>
    },
    {
      title: 'Round',
      dataIndex: 'interview_round',
      key: 'round',
      align: 'center' as const
    },
    {
      title: 'Scheduled At',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      render: (d: string) => <span className="text-slate-500">{dayjs(d).format('MMM D, HH:mm')}</span>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <Tag color="blue" className="rounded-md font-bold text-[10px] uppercase border-none">{s}</Tag>
    }
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button type="primary" icon={<Plus className="h-4 w-4" />} className="rounded-xl font-bold">Schedule Interview</Button>
      </div>
      <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
        <Table 
          dataSource={interviews} 
          columns={columns} 
          rowKey="id" 
          loading={isLoading} 
          className="modern-table"
        />
      </Card>
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobFullView({ jobId, onRefresh, initialTab }: { jobId: string, onRefresh: () => void, initialTab?: string }) {
  const [activeTab, setActiveTab] = useState(initialTab || 'overview')

  const { data, isLoading } = useApiQuery(
    ['requisition', 'full', jobId],
    () => requisitionsApi.get(jobId)
  )

  const requisition = (data as any)?.requisition as JobRequisition

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!requisition) return <Empty description="Job not found" />

  const config = STATUS_CONFIG[requisition.status] || STATUS_CONFIG.draft

  return (
    <div className="space-y-8">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
        <div className="flex items-start gap-5">
          <div className="flex h-16 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-soft-lg">
            <Briefcase className="h-8 w-8" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider", config.color)}>
                <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
                {config.label}
              </div>
              <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-full px-2.5">
                {requisition.priority} Priority
              </Tag>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-tight">
              {requisition.title}
            </h1>
            <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm font-medium tracking-wide">
              {requisition.id} · CREATED {dayjs(requisition.created_at).format('MMM D, YYYY').toUpperCase()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl border-slate-200">
            <Activity className="h-4 w-4" /> Activity
          </Button>
          <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl bg-blue-600 border-none shadow-soft-md">
            Edit Requisition
          </Button>
        </div>
      </div>

      {/* Tabs Area */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="modern-tabs"
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: <OverviewTab requisition={requisition} />
          },
          {
            key: 'pipeline',
            label: 'Pipeline',
            children: (
              <div className="h-[calc(100vh-320px)] -mx-6 px-6 overflow-hidden">
                <PipelineBoard jobId={jobId} />
              </div>
            )
          },
          {
            key: 'applications',
            label: 'Applications',
            children: <ApplicationsTab jobId={jobId} onRefresh={onRefresh} />
          },
          {
            key: 'interviews',
            label: 'Interviews',
            children: <InterviewsTab jobId={jobId} />
          }
        ]}
      />
    </div>
  )
}
