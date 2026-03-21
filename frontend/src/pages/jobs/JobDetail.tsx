import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Descriptions, Tag,
  Typography, Spin, Empty, Tabs, Table, Avatar
} from 'antd'
import {
  ArrowLeft, Edit, Briefcase,
  Activity, MapPin,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import type { JobRequisition, RequisitionStatus, Application } from '@/types'
import { cn } from '@/utils/cn'
import PipelineBoard from '../pipeline/PipelineBoard'

const { Text, Paragraph } = Typography

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
        <Card title="Details" bordered={false} className="shadow-soft-sm">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Type">{requisition.job_type.replace('_', ' ')}</Descriptions.Item>
            <Descriptions.Item label="Mode">{requisition.work_mode}</Descriptions.Item>
            <Descriptions.Item label="Headcount">{requisition.headcount}</Descriptions.Item>
            <Descriptions.Item label="Experience">{requisition.experience_min}-{requisition.experience_max}y</Descriptions.Item>
          </Descriptions>
        </Card>
        <Card title="Salary" bordered={false} className="shadow-soft-sm">
          {requisition.salary_visible ? (
            <div>
              <Text className="text-2xl font-bold text-slate-900">
                {requisition.salary_currency} {Number(requisition.salary_min).toLocaleString()}
              </Text>
              <Text className="block text-xs text-slate-400 font-bold uppercase mt-1">Minimum per annum</Text>
            </div>
          ) : (
            <Text className="italic text-slate-400">Salary hidden from candidates</Text>
          )}
        </Card>
        <Card title="Location" bordered={false} className="shadow-soft-sm">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-slate-400" />
            <Text className="font-semibold text-slate-700">{requisition.location_id || 'Remote / Head Office'}</Text>
          </div>
        </Card>
      </div>

      <Card title="Job Description" bordered={false} className="shadow-soft-sm">
        <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap">
          {requisition.description}
        </Paragraph>
      </Card>

      <Card title="Requirements" bordered={false} className="shadow-soft-sm">
        <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap">
          {requisition.requirements}
        </Paragraph>
      </Card>

      <Card title="Key Responsibilities" bordered={false} className="shadow-soft-sm">
        <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap">
          {requisition.responsibilities}
        </Paragraph>
      </Card>
    </div>
  )
}

function ApplicationsTab({ jobId }: { jobId: string }) {
  const { data, isLoading } = useApiQuery(['job-applications', jobId], () => 
    pipelineApi.listApplications({ requisition_id: jobId })
  )
  const applications = (data as any)?.applications ?? []

  const columns = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_: any, record: Application) => (
        <div className="flex items-center gap-3">
          <Avatar className="bg-blue-100 text-blue-600 font-bold">
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
      render: (s: string) => <Tag className="rounded-full px-2.5 py-0.5 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase">{s}</Tag>
    },
    {
      title: 'Applied Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d: string) => dayjs(d).format('MMM D, YYYY')
    }
  ]

  return (
    <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
      <Table 
        dataSource={applications} 
        columns={columns} 
        rowKey="id" 
        loading={isLoading} 
        pagination={{ pageSize: 10 }}
      />
    </Card>
  )
}

function InterviewsTab({ jobId }: { jobId: string }) {
  const { data, isLoading } = useApiQuery(['job-interviews', jobId], () => 
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
      key: 'round'
    },
    {
      title: 'Scheduled At',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      render: (d: string) => dayjs(d).format('MMM D, YYYY HH:mm')
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <Tag color="blue">{s}</Tag>
    }
  ]

  return (
    <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
      <Table 
        dataSource={interviews} 
        columns={columns} 
        rowKey="id" 
        loading={isLoading} 
      />
    </Card>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')

  const { data, isLoading } = useApiQuery(
    ['requisition', id],
    () => requisitionsApi.get(id!)
  )

  const requisition = (data as any)?.requisition as JobRequisition

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!requisition) return <Empty description="Job not found" />

  const config = STATUS_CONFIG[requisition.status] || STATUS_CONFIG.draft

  return (
    <div className="space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col gap-6">
        <Button 
          type="text" 
          icon={<ArrowLeft className="h-4 w-4" />} 
          className="flex items-center gap-2 text-slate-500 font-medium hover:text-slate-900 w-fit p-0"
          onClick={() => navigate('/jobs')}
        >
          Back to Jobs
        </Button>

        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 shadow-soft-sm">
              <Briefcase className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1.5">
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
              <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm font-medium">
                {requisition.id} · Created {dayjs(requisition.created_at).format('MMM D, YYYY')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button className="h-10 flex items-center gap-2 font-semibold">
              <Activity className="h-4 w-4" /> Activity
            </Button>
            <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-10 flex items-center gap-2 font-semibold">
              Edit Job
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
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
              <div className="h-[calc(100vh-350px)] overflow-hidden -mx-8 px-8">
                <PipelineBoard jobId={id} />
              </div>
            )
          },
          {
            key: 'applications',
            label: 'Applications',
            children: <ApplicationsTab jobId={id!} />
          },
          {
            key: 'interviews',
            label: 'Interviews',
            children: <InterviewsTab jobId={id!} />
          }
        ]}
      />
    </div>
  )
}
