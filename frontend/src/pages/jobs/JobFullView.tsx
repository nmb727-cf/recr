import { useState, useEffect } from 'react'
import {
  Button, Card, Descriptions, Tag, Avatar, Space,
  Typography, Spin, Empty, Tabs, Table, Divider,
  message, Modal, Input, Timeline
} from 'antd'
import {
  Edit, Briefcase,
  Activity, Plus, CheckCircle, X
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)

import { useApiQuery } from '@/hooks/useApiQuery'
import { useQuery } from '@tanstack/react-query'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import { candidatesApi } from '@/api/candidates'
import type { JobRequisition, RequisitionStatus, Application } from '@/types'
import { cn } from '@/utils/cn'
import PipelineBoard from '../pipeline/PipelineBoard'
import JobMatchSuggestions from '@/components/JobMatchSuggestions'

const { Title, Text, Paragraph } = Typography

const STATUS_CONFIG: Record<RequisitionStatus, { label: string, color: string, dot: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
  pending_approval: { label: 'Pending', color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  approved: { label: 'Approved', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-400' },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  closed: { label: 'Closed', color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300' },
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const formatSalary = (amount: number | string, currency: string = 'INR') => 
  new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: currency,
    maximumFractionDigits: 0
  }).format(Number(amount))

// ─── Tabs ───────────────────────────────────────────────────────────────────

function OverviewTab({ requisition }: { requisition: JobRequisition }) {
  return (
    <div className="space-y-8">
      {/* FIX 6: Full view styling */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e2e8f0', 
        borderRadius: 8,
        padding: 16,
        marginBottom: 24,
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12
      }}>
        <div>
          <p style={{margin:0, color:'#888', fontSize:12}}>EXPERIENCE</p>
          <p style={{margin:0, fontWeight:600}}>{requisition.experience_min}-{requisition.experience_max} years</p>
        </div>
        <div>
          <p style={{margin:0, color:'#888', fontSize:12}}>SALARY</p>
          <p style={{margin:0, fontWeight:600}}>
            {requisition.salary_visible ? formatSalary(requisition.salary_min, requisition.salary_currency) : 'Competitive'}
          </p>
        </div>
        <div>
          <p style={{margin:0, color:'#888', fontSize:12}}>HEADCOUNT</p>
          <p style={{margin:0, fontWeight:600}}>{requisition.headcount}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title={<span className="text-sm font-bold text-slate-900">Basic Info</span>} bordered={false} className="shadow-soft-sm">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Type">{requisition.job_type.replace('_', ' ')}</Descriptions.Item>
            <Descriptions.Item label="Work Mode">{requisition.work_mode}</Descriptions.Item>
            <Descriptions.Item label="Location">{requisition.location_id || 'Remote'}</Descriptions.Item>
            <Descriptions.Item label="Department">{requisition.department_id || 'General'}</Descriptions.Item>
          </Descriptions>
        </Card>
        
        <Card title={<span className="text-sm font-bold text-slate-900">Required Skills</span>} bordered={false} className="shadow-soft-sm">
          <div className="flex flex-wrap gap-2">
            {(requisition.skills_required || []).map(s => (
              <Tag color="blue" key={s} className="m-0 border-none font-bold text-[10px] uppercase rounded-md px-2 py-0.5">
                {s}
              </Tag>
            ))}
            {(!requisition.skills_required || requisition.skills_required.length === 0) && <Text type="secondary" italic>No skills listed</Text>}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card title={<span className="text-base font-bold text-slate-900">Job Description</span>} bordered={false} className="shadow-soft-sm">
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
        </Card>
      </div>
    </div>
  )
}

function ApplicationListTable({ 
  applications, 
  loading, 
  onRefresh,
  showAgency = false 
}: { 
  applications: Application[], 
  loading: boolean, 
  onRefresh: () => void,
  showAgency?: boolean 
}) {
  const [rejectModal, setRejectModal] = useState<{ open: boolean, app: Application | null }>({ open: false, app: null })
  const [rejectReason, setRejectReason] = useState('')
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({})
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (applications.length > 0) {
      const fetchNames = async () => {
        const names: Record<string, string> = {}
        await Promise.all(applications.map(async (app) => {
          try {
            const res = await candidatesApi.get(app.candidate_id)
            names[app.candidate_id] = res.data.data.candidate.full_name || 'Unknown Candidate'
          } catch {
            names[app.candidate_id] = 'Unknown Candidate'
          }
        }))
        setCandidateNames(prev => ({ ...prev, ...names }))
      }
      fetchNames()
    }
  }, [applications])

  const promptStageNote = (title: string): Promise<string | null> =>
    new Promise((resolve) => {
      let note = ''
      Modal.confirm({
        title,
        content: (
          <div className="mt-2">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">Mandatory Note</p>
            <Input.TextArea
              rows={3}
              placeholder="Enter reason for stage change"
              onChange={(e) => { note = e.target.value }}
            />
          </div>
        ),
        okText: 'Confirm',
        onOk: async () => {
          if (!note.trim()) {
            message.error('A note is required')
            throw new Error('missing_note')
          }
          resolve(note.trim())
        },
        onCancel: () => resolve(null),
      })
    })

  const handleShortlist = async (appId: string) => {
    const note = await promptStageNote('Confirm Stage Change')
    if (!note) return
    try {
      await pipelineApi.shortlist(appId, note)
      message.success('Candidate shortlisted')
      onRefresh()
    } catch {
      message.error('Failed to shortlist')
    }
  }

  const handleReject = async () => {
    if (!rejectModal.app) return
    if (!rejectReason.trim()) {
      message.error('A note is required')
      return
    }
    setActionLoading(true)
    try {
      await pipelineApi.reject(rejectModal.app.id, rejectReason.trim())
      message.success('Candidate rejected')
      setRejectModal({ open: false, app: null })
      setRejectReason('')
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
            {candidateNames[record.candidate_id]?.charAt(0) || 'C'}
          </Avatar>
          <Text className="font-bold text-slate-900">{candidateNames[record.candidate_id] || 'Loading...'}</Text>
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
    ...(showAgency ? [{
      title: 'Agency',
      dataIndex: 'source_detail',
      key: 'agency',
      render: (detail: string) => <Text className="text-slate-500 text-sm">{detail || 'Partner Agency'}</Text>
    }] : []),
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
      <Table 
        dataSource={applications} 
        columns={columns} 
        rowKey="id" 
        loading={loading} 
        pagination={{ pageSize: 10, className: "px-6" }}
        className="modern-table"
      />

      <Modal
        title="Reject Application"
        open={rejectModal.open}
        onCancel={() => setRejectModal({ open: false, app: null })}
        onOk={handleReject}
        confirmLoading={actionLoading}
        okText="Reject Candidate"
        okButtonProps={{ danger: true, disabled: !rejectReason.trim() }}
      >
        <p className="text-slate-500 mb-4 text-sm font-medium">Please provide a reason for rejection (optional):</p>
        <Input.TextArea rows={3} value={rejectReason} onChange={e => setRejectReason(e.target.value)} placeholder="e.g. Insufficient technical experience..." />
      </Modal>
    </>
  )
}

function ApplicationsTab({ jobId, onRefresh }: { jobId: string, onRefresh: () => void }) {
  const { data, isLoading, refetch } = useApiQuery(['job-applications-full', jobId], () => 
    pipelineApi.listApplications({ requisition_id: jobId })
  )
  const applications = (data as any)?.applications ?? []

  const directApps = applications.filter((app: any) => !app.is_agency_submission)
  const agencyApps = applications.filter((app: any) => app.is_agency_submission)

  return (
    <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
      <Tabs
        defaultActiveKey="direct"
        className="inner-tabs px-6 pt-2"
        items={[
          { 
            key: 'direct', 
            label: `Direct Applications (${directApps.length})`, 
            children: <ApplicationListTable applications={directApps} loading={isLoading} onRefresh={() => { refetch(); onRefresh(); }} /> 
          },
          { 
            key: 'agency', 
            label: `Agency Submissions (${agencyApps.length})`, 
            children: <ApplicationListTable applications={agencyApps} loading={isLoading} onRefresh={() => { refetch(); onRefresh(); }} showAgency /> 
          },
        ]}
      />
    </Card>
  )
}

function InterviewsTab({ jobId }: { jobId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['job-interviews-full', jobId],
    queryFn: async () => {
      const res = await pipelineApi.listApplications({ requisition_id: jobId })
      const apps = res.data.data.applications
      const interviewPromises = apps.map(app => 
        interviewsApi.list({ application_id: app.id })
      )
      const results = await Promise.all(interviewPromises)
      return results.flatMap(r => r.data.data.interviews)
    },
    enabled: !!jobId
  })
  
  const interviews = data ?? []

  const columns = [
    {
      title: 'Type',
      dataIndex: 'interview_type',
      key: 'type',
      render: (t: string) => <Text className="font-bold text-slate-700 capitalize">{t}</Text>
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
      render: (d: string) => <span className="text-slate-500 font-medium">{d ? dayjs(d).format('MMM D, HH:mm') : 'TBD'}</span>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <Tag color="blue" className="rounded-md font-bold text-[10px] uppercase border-none">{s}</Tag>
    },
    {
      title: 'Score',
      dataIndex: 'average_score',
      key: 'score',
      render: (s: number) => s ? <span className="font-bold text-blue-600">{s}/5</span> : '—'
    }
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button type="primary" icon={<Plus className="h-4 w-4" />} className="rounded-xl font-bold bg-slate-900 border-none">Schedule Interview</Button>
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

function ActivityTab({ jobId }: { jobId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['job-activity-timeline', jobId],
    queryFn: async () => {
      const appRes = await pipelineApi.listApplications({ requisition_id: jobId })
      const apps = appRes.data.data.applications
      
      const historyPromises = apps.map(app => pipelineApi.getApplication(app.id))
      const historyResults = await Promise.all(historyPromises)
      
      const allEvents: any[] = []
      historyResults.forEach(res => {
        const app = res.data.data.application
        const history = (res.data.data as any).history || []
        
        // Add initial submission
        allEvents.push({
          candidate_id: app.candidate_id,
          text: `submitted application`,
          date: app.created_at,
          type: 'submission'
        })
        
        // Add stage movements
        history.forEach((h: any) => {
          allEvents.push({
            candidate_id: app.candidate_id,
            text: `moved to ${h.to_stage_name || 'next stage'}`,
            date: h.moved_at,
            type: 'move'
          })
        })
      })
      
      return allEvents.sort((a, b) => dayjs(b.date).unix() - dayjs(a.date).unix())
    }
  })

  const activities = data ?? []
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({})

  useEffect(() => {
    if (activities.length > 0) {
      const fetchNames = async () => {
        const uniqueIds = Array.from(new Set(activities.map(a => a.candidate_id)))
        const names: Record<string, string> = {}
        await Promise.all(uniqueIds.map(async (id) => {
          try {
            const res = await candidatesApi.get(id)
            names[id] = res.data.data.candidate.full_name
          } catch {}
        }))
        setCandidateNames(prev => ({ ...prev, ...names }))
      }
      fetchNames()
    }
  }, [activities])

  return (
    <Card bordered={false} className="shadow-soft-sm p-8">
      {isLoading ? <Spin /> : (
        <Timeline
          items={activities.map((act, i) => ({
            key: i,
            children: (
              <div className="flex flex-col">
                <Text className="text-sm font-medium text-slate-900">
                  <span className="font-bold text-blue-600">{candidateNames[act.candidate_id] || 'Candidate'}</span> {act.text}
                </Text>
                <Text type="secondary" className="text-[11px] font-bold uppercase mt-1 text-slate-400">
                  {dayjs(act.date).fromNow()}
                </Text>
              </div>
            ),
            dot: <div className={cn("h-2 w-2 rounded-full", act.type === 'submission' ? "bg-emerald-500" : "bg-blue-500")} />,
          }))}
        />
      )}
    </Card>
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
      <div className="sticky top-0 z-20 -mx-2 rounded-xl border border-slate-100 bg-white/95 px-2 py-3 backdrop-blur">
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
              ID: {requisition.id.slice(0, 8)} · CREATED {dayjs(requisition.created_at).format('MMM D, YYYY').toUpperCase()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl border-slate-200" onClick={() => setActiveTab('activity')}>
            <Activity className="h-4 w-4" /> Activity
          </Button>
          <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl bg-blue-600 border-none shadow-soft-md">
            Edit Requisition
          </Button>
        </div>
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
          },
          {
            key: 'activity',
            label: 'Activity',
            children: <ActivityTab jobId={jobId} />
          },
          {
            key: 'suggestions',
            label: 'Suggested Candidates',
            children: <JobMatchSuggestions jobId={jobId} />
          }
        ]}
      />
    </div>
  )
}
