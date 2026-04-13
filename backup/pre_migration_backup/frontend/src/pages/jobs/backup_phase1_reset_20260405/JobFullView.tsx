import { useState, useEffect } from 'react'
import {
  Button, Card, Descriptions, Tag, Avatar, Space,
  Typography, Spin, Empty, Tabs, Table, Divider,
  message, Modal, Input, Timeline, Tooltip, Progress, Badge
} from 'antd'
import {
  Edit, Briefcase,
  Activity, Plus, CheckCircle, X,
  LayoutGrid, Users, Target, Clock3, FileText, 
  Settings2, Send, Globe, Zap, MapPin, Building2, 
  ChevronLeft, ExternalLink, DollarSign, BrainCircuit,
  AlertCircle, Star, ChevronRight, RefreshCw, XCircle
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)

import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import { candidatesApi } from '@/api/candidates'
import { agenciesApi } from '@/api/agencies'
import type { JobRequisition, RequisitionStatus, Application, AgencyRelationship } from '@/types'
import { cn } from '@/utils/cn'
import PipelineBoard from '../pipeline/PipelineBoard'
import JobMatchSuggestions from '@/components/JobMatchSuggestions'
import { useAuthStore } from '@/store/authStore'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import JobCreateForm from '@/components/forms/JobCreateForm'

const { Title, Text, Paragraph } = Typography

const STATUS_CONFIG: Record<RequisitionStatus, { label: string, color: string, dot: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
  pending_approval: { label: 'Pending', color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  approved: { label: 'Approved', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-400' },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  paused: { label: 'Paused', color: 'bg-amber-100 text-amber-600', dot: 'bg-amber-500' },
  in_guarantee_period: { label: 'Guarantee', color: 'bg-purple-50 text-purple-700', dot: 'bg-purple-500' },
  closed: { label: 'Closed', color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300' },
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

const formatSalary = (amount: number | string, currency: string = 'INR') => 
  new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: currency,
    maximumFractionDigits: 0
  }).format(Number(amount))

// ─── Tabs ───────────────────────────────────────────────────────────────────

function OverviewTab({ requisition, jobId }: { requisition: JobRequisition, jobId: string }) {
  const navigate = useNavigate()
  const metadata = requisition?.metadata || {}
  
  const stats = [
    { label: 'Total Applications', value: metadata.applications_count || 0, icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Active Interviews', value: metadata.interview || 0, icon: Activity, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Active Offers', value: metadata.offer || 0, icon: Target, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Requisition Age', value: dayjs(requisition.created_at).fromNow(true), icon: Clock3, color: 'text-slate-600', bg: 'bg-slate-50' },
  ] as Array<{ label: string, value: React.ReactNode, icon: any, color: string, bg: string }>

  const { data: agenciesData } = useApiQuery(
    ['job-agencies-full', jobId],
    () => agenciesApi.listAssignments({ requisition_id: jobId })
  )
  const assignments = Array.isArray((agenciesData as any)?.data?.assignments) ? (agenciesData as any).data.assignments : []

  return (
    <div className="space-y-6">
      {/* Operational Summary Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <div key={i} className="bg-white rounded-2xl p-4 border border-slate-100 shadow-soft-sm flex items-center gap-4">
            <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center shrink-0", s.bg, s.color)}>
              <s.icon size={20} />
            </div>
            <div>
              <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-wider mb-0.5">{s.label}</Text>
              <Text className="block font-black text-slate-900 text-xl leading-none">{s.value}</Text>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Pipeline Snapshot */}
          <Card 
            title={<span className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2"><LayoutGrid size={14} /> Pipeline Velocity</span>}
            bordered={false} 
            className="shadow-soft-sm rounded-2xl"
            extra={<Button type="link" size="small" onClick={() => navigate(`/pipeline?job=${jobId}`)} className="text-xs font-bold p-0 h-auto">Open Pipeline Board →</Button>}
          >
            <div className="grid grid-cols-5 gap-4 py-2">
              {['applied', 'screening', 'interview', 'offer', 'joined'].map((stage) => {
                const count = Number(metadata[stage]) || 0
                const total = Number(metadata.applications_count) || 1
                const percent = (count / total) * 100
                return (
                  <div key={stage} className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <Text className="text-[10px] font-black uppercase text-slate-500 tracking-tighter truncate">{stage}</Text>
                      <Text className="text-xs font-black text-slate-900">{count}</Text>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          stage === 'joined' ? "bg-emerald-500" : stage === 'offer' ? "bg-indigo-500" : "bg-blue-500"
                        )} 
                        style={{ width: `${percent}%` }} 
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>

          {/* Job Content */}
          <Card bordered={false} className="shadow-soft-sm rounded-2xl">
            <div className="space-y-8">
              <div>
                <Title level={5} className="!text-xs !font-black !uppercase !tracking-[0.2em] !text-indigo-600 !mb-4 flex items-center gap-2">
                  <FileText size={14} /> Job Description
                </Title>
                <div className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm border-l-2 border-slate-100 pl-6 py-1">
                  {requisition.description || 'No description provided.'}
                </div>
              </div>
              
              {requisition.requirements && (
                <div>
                  <Title level={5} className="!text-xs !font-black !uppercase !tracking-[0.2em] !text-indigo-600 !mb-4 flex items-center gap-2">
                    <BrainCircuit size={14} /> Requirements & Qualifications
                  </Title>
                  <div className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm border-l-2 border-slate-100 pl-6 py-1">
                    {requisition.requirements}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Intelligence Panel */}
          <Card 
            title={<span className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2"><Zap size={14} /> Hiring Intelligence</span>}
            bordered={false} 
            className="shadow-soft-sm rounded-2xl bg-slate-900 border-none"
          >
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <div className="flex items-center gap-2 mb-2 text-indigo-400">
                  <Target size={14} />
                  <Text className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Status Signal</Text>
                </div>
                <Text className="text-white text-xs font-bold block">
                  {requisition.status === 'active' ? 'Active sourcing mode. AI is matching candidates.' : 'Requisition is currently paused.'}
                </Text>
              </div>

              {Number(metadata.interview) > 5 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <div className="flex items-center gap-2 mb-2 text-amber-400">
                    <AlertCircle size={14} />
                    <Text className="text-[10px] font-black uppercase tracking-widest text-amber-400">Bottleneck Alert</Text>
                  </div>
                  <Text className="text-amber-100 text-xs font-bold block">
                    High volume in Interview stage. Consider expanding interview capacity.
                  </Text>
                </div>
              )}

              {assignments.length === 0 && requisition.status === 'active' && (
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                  <div className="flex items-center gap-2 mb-2 text-blue-400">
                    <Building2 size={14} />
                    <Text className="text-[10px] font-black uppercase tracking-widest text-blue-400">Sourcing Advice</Text>
                  </div>
                  <Text className="text-blue-100 text-xs font-bold block">
                    No agencies assigned. Assign partners to increase candidate flow.
                  </Text>
                </div>
              )}
            </div>
          </Card>

          {/* Quick Details Card */}
          <Card bordered={false} className="shadow-soft-sm rounded-2xl overflow-hidden">
            <div className="space-y-4">
              {[
                { label: 'Experience', value: `${requisition.experience_min}-${requisition.experience_max} Years`, icon: Target },
                { label: 'Salary', value: requisition.salary_visible ? formatSalary(requisition.salary_min, requisition.salary_currency) : 'Competitive', icon: DollarSign },
                { label: 'Headcount', value: `${requisition.headcount} Openings`, icon: Users },
                { label: 'Work Mode', value: requisition.work_mode.replace('_', ' '), icon: Globe },
                { label: 'Job Type', value: requisition.job_type.replace('_', ' '), icon: Briefcase },
                { label: 'Department', value: requisition.department_id || 'General', icon: Building2 },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between pb-3 border-b border-slate-50 last:border-0 last:pb-0">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 rounded-lg bg-slate-50 text-slate-400">
                      <item.icon size={12} />
                    </div>
                    <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{item.label}</Text>
                  </div>
                  <Text className="text-xs font-black text-slate-700">{item.value}</Text>
                </div>
              ))}
            </div>
          </Card>

          {/* Agency Partners */}
          <Card 
            title={<span className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2"><Building2 size={14} /> Agency Partners</span>}
            bordered={false} 
            className="shadow-soft-sm rounded-2xl"
          >
            {assignments.length > 0 ? (
              <div className="space-y-3">
                {assignments.map((a: any) => (
                  <div key={a.id} className="flex items-center justify-between p-2 rounded-xl border border-slate-50">
                    <div className="flex items-center gap-2">
                      <Avatar size={24} className="bg-indigo-50 text-indigo-600 font-bold text-[10px]">
                        {(a.agency_name || 'A').charAt(0)}
                      </Avatar>
                      <Text className="text-xs font-bold text-slate-700 truncate max-w-[120px]">{a.agency_name || 'Partner'}</Text>
                    </div>
                    <Tag className="m-0 border-none bg-emerald-50 text-emerald-600 font-black text-[8px] uppercase">{a.status}</Tag>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <Text className="text-[10px] font-bold text-slate-300 uppercase italic">No agencies assigned</Text>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

function ApplicationListTable({ 
  applications, 
  loading, 
  onRefresh,
  showAgency = false,
  isOwner
}: { 
  applications: Application[], 
  loading: boolean, 
  onRefresh: () => void,
  showAgency?: boolean,
  isOwner: boolean
}) {
  const [rejectModal, setRejectModal] = useState<{ open: boolean, app: Application | null }>({ open: false, app: null })
  const [rejectReason, setRejectReason] = useState('')
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({})
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (applications.length > 0) {
      const fetchNames = async () => {
        const ids = Array.from(new Set(applications.map((app: any) => app.candidate_id))).join(',')
        try {
          const res = await candidatesApi.list({ ids })
          const candidates = res.data.data.candidates
          const names: Record<string, string> = {}
          candidates.forEach((c: any) => {
            names[c.id] = c.full_name
          })
          setCandidateNames(prev => ({ ...prev, ...names }))
        } catch {
          // Fallback if batch fails
        }
      }
      fetchNames()
    }
  }, [applications])

  const promptStageNote = (title: string): Promise<string | null> =>
    new Promise((resolve) => {
      let note = ''
      Modal.confirm({
        title,
        icon: <AlertCircle className="text-indigo-600" />,
        content: (
          <div className="mt-2">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">Mandatory Activity Note</p>
            <Input.TextArea
              rows={3}
              placeholder="Enter reason for stage change"
              className="rounded-xl border-slate-200"
              onChange={(e) => { note = e.target.value }}
            />
          </div>
        ),
        okText: 'Update Stage',
        okButtonProps: { className: 'bg-indigo-600 border-none font-bold' },
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
    const note = await promptStageNote('Move to Shortlisted')
    if (!note) return
    try {
      await pipelineApi.shortlist(appId, note)
      message.success('Candidate shortlisted successfully')
      onRefresh()
    } catch {
      message.error('Failed to update stage')
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
      render: (_: any, record: Application) => {
        const name = candidateNames[record.candidate_id] || 'Loading...'
        return (
          <div className="flex items-center gap-3">
            <Avatar className="bg-indigo-50 text-indigo-600 font-black border-none" style={{ backgroundColor: avatarColor(name) }}>
              {name.charAt(0)}
            </Avatar>
            <div>
              <Text className="block font-black text-slate-900 text-sm leading-none mb-1">{name}</Text>
              <Text className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">ID: {record.id.slice(0, 8)}</Text>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => (
        <div className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-50 border border-slate-100 text-slate-600 font-black text-[9px] uppercase tracking-widest">
          {s.replace('_', ' ')}
        </div>
      )
    },
    {
      title: 'Match Score',
      dataIndex: 'match_score',
      key: 'match',
      render: (score: number) => (
        <div className="flex items-center gap-2">
          <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${score}%` }} />
          </div>
          <span className="font-black text-emerald-600 text-xs">{score}%</span>
        </div>
      )
    },
    ...(showAgency ? [{
      title: 'Agency',
      dataIndex: 'source_detail',
      key: 'agency',
      render: (detail: string) => <Text className="text-slate-500 text-xs font-bold truncate max-w-[120px] block">{detail || 'Partner Agency'}</Text>
    }] : []),
    {
      title: 'Applied Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d: string) => <span className="text-slate-400 text-[11px] font-bold uppercase tracking-tighter">{dayjs(d).format('MMM D, YYYY')}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, record: Application) => (
        <Space>
          {record.status === 'applied' && (
            <Tooltip title="Shortlist">
              <Button size="small" type="text" icon={<Star className="h-4 w-4 text-amber-500" />} onClick={() => handleShortlist(record.id)} disabled={!isOwner} />
            </Tooltip>
          )}
          <Tooltip title="Reject">
            <Button size="small" type="text" danger icon={<XCircle className="h-4 w-4" />} onClick={() => setRejectModal({ open: true, app: record })} disabled={!isOwner} />
          </Tooltip>
          <Button size="small" type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />
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
        pagination={{ pageSize: 10, className: "px-6 pb-4" }}
        className="enterprise-table"
      />

      <Modal
        title={<span className="font-black text-slate-900 tracking-tight">Reject Application</span>}
        open={rejectModal.open}
        onCancel={() => setRejectModal({ open: false, app: null })}
        onOk={handleReject}
        confirmLoading={actionLoading}
        okText="Confirm Rejection"
        okButtonProps={{ danger: true, disabled: !rejectReason.trim(), className: 'font-bold rounded-xl' }}
        cancelButtonProps={{ className: 'rounded-xl font-bold' }}
        className="rounded-2xl overflow-hidden"
      >
        <div className="mt-4">
          <p className="text-slate-500 mb-4 text-xs font-bold uppercase tracking-widest">Rejection Reason (Mandatory)</p>
          <Input.TextArea 
            rows={4} 
            value={rejectReason} 
            onChange={e => setRejectReason(e.target.value)} 
            placeholder="e.g. Insufficient technical experience in required stack..." 
            className="rounded-xl border-slate-200"
          />
        </div>
      </Modal>
    </>
  )
}

function ApplicationsTab({ jobId, onRefresh, isOwner }: { jobId: string, onRefresh: () => void, isOwner: boolean }) {
  const { data, isLoading, refetch } = useApiQuery(['job-applications-full', jobId], () => 
    pipelineApi.listApplications({ requisition_id: jobId })
  )
  const applications = (data as any)?.applications ?? []

  const directApps = applications.filter((app: any) => !app.is_agency_submission)
  const agencyApps = applications.filter((app: any) => app.is_agency_submission)

  return (
    <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden rounded-2xl border border-slate-100">
      <Tabs
        defaultActiveKey="direct"
        className="enterprise-inner-tabs"
        items={[
          { 
            key: 'direct', 
            label: <span className="flex items-center gap-2">Direct <Badge count={directApps.length} size="small" style={{ backgroundColor: '#4F46E5' }} /></span>, 
            children: <ApplicationListTable applications={directApps} loading={isLoading} onRefresh={() => { refetch(); onRefresh(); }} isOwner={isOwner} /> 
          },
          { 
            key: 'agency', 
            label: <span className="flex items-center gap-2">Agencies <Badge count={agencyApps.length} size="small" style={{ backgroundColor: '#4F46E5' }} /></span>, 
            children: <ApplicationListTable applications={agencyApps} loading={isLoading} onRefresh={() => { refetch(); onRefresh(); }} showAgency isOwner={isOwner} /> 
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
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'type',
      render: (t: string) => (
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center shrink-0">
            <Activity size={14} />
          </div>
          <Text className="font-black text-slate-700 capitalize text-sm">{t}</Text>
        </div>
      )
    },
    {
      title: 'Round',
      dataIndex: 'interview_round',
      key: 'round',
      align: 'center' as const,
      render: (r: number) => <span className="font-black text-slate-400 text-xs">#{r}</span>
    },
    {
      title: 'Scheduled Time',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      render: (d: string) => <span className="text-slate-500 font-bold text-xs">{d ? dayjs(d).format('MMM D · HH:mm') : 'TBD'}</span>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <div className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-600 font-black text-[9px] uppercase tracking-widest">{s}</div>
    },
    {
      title: 'Avg. Score',
      dataIndex: 'average_score',
      key: 'score',
      render: (s: number) => s ? (
        <div className="flex items-center gap-1.5 font-black text-indigo-600 text-xs bg-indigo-50 px-2 py-1 rounded-lg w-fit">
          <Star size={10} fill="currentColor" /> {s}/5
        </div>
      ) : <span className="text-slate-300 font-bold">—</span>
    }
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button type="primary" icon={<Plus size={16} />} className="rounded-xl font-black bg-slate-900 border-none h-10 px-6 text-xs uppercase tracking-widest">Schedule Interview</Button>
      </div>
      <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden rounded-2xl border border-slate-100">
        <Table 
          dataSource={interviews} 
          columns={columns} 
          rowKey="id" 
          loading={isLoading} 
          className="enterprise-table"
          pagination={{ pageSize: 10, className: "px-6 pb-4" }}
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
    <Card bordered={false} className="shadow-soft-sm p-10 rounded-2xl border border-slate-100 bg-white">
      {isLoading ? <div className="py-12 flex justify-center"><Spin /></div> : activities.length > 0 ? (
        <Timeline
          className="enterprise-timeline"
          items={activities.map((act, i) => ({
            key: i,
            children: (
              <div className="flex flex-col mb-6">
                <div className="flex items-center gap-2 mb-1">
                  <Text className="text-sm font-black text-indigo-600 truncate max-w-[200px]">{candidateNames[act.candidate_id] || 'Candidate'}</Text>
                  <Text className="text-slate-700 text-sm font-medium">{act.text}</Text>
                </div>
                <div className="flex items-center gap-2">
                  <Clock3 size={10} className="text-slate-300" />
                  <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                    {dayjs(act.date).format('MMM D, YYYY · HH:mm')} ({dayjs(act.date).fromNow()})
                  </Text>
                </div>
              </div>
            ),
            dot: <div className={cn("h-2.5 w-2.5 rounded-full border-2 border-white shadow-sm", act.type === 'submission' ? "bg-emerald-500" : "bg-indigo-500")} />,
          }))}
        />
      ) : (
        <Empty description="No activity recorded yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobFullView({ jobId, onRefresh, initialTab }: { jobId: string, onRefresh: () => void, initialTab?: string }) {
  const [activeTab, setActiveTab] = useState(initialTab || 'overview')
  const [editModalOpen, setEditModalOpen] = useState(false)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useApiQuery(
    ['requisition', 'full', jobId],
    () => requisitionsApi.get(jobId)
  )

  const requisition = (data as any)?.requisition as JobRequisition
  const isOwner = requisition?.created_by === user?.id

  // Mutations
  const submitMutation = useMutation({
    mutationFn: () => requisitionsApi.submitForApproval(jobId!),
    onSuccess: () => {
      message.success('Requisition submitted for approval')
      queryClient.invalidateQueries({ queryKey: ['requisition', 'full', jobId] })
    }
  })

  const approveMutation = useMutation({
    mutationFn: () => requisitionsApi.approve(jobId!),
    onSuccess: () => {
      message.success('Requisition approved')
      queryClient.invalidateQueries({ queryKey: ['requisition', 'full', jobId] })
    }
  })

  const publishMutation = useMutation({
    mutationFn: () => requisitionsApi.publish(jobId!),
    onSuccess: () => {
      message.success('Requisition published and is now ACTIVE')
      queryClient.invalidateQueries({ queryKey: ['requisition', 'full', jobId] })
    }
  })

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!requisition) return <div className="p-12"><Empty description="Requisition not found" /></div>

  const statusStyle = getStatusStyle(requisition.status, 'job')

  return (
    <div className="space-y-6">
      {/* Header Info - Revamped for Enterprise Command Center feel */}
      <div className="sticky top-0 z-20 -mx-4 rounded-2xl border border-slate-100 bg-white/90 px-6 py-6 backdrop-blur-md shadow-soft-sm">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div className="flex items-start gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-100">
              <Target size={28} />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-black uppercase tracking-[0.15em] border", statusStyle.softClass)}>
                  <span className={cn("h-1.5 w-1.5 rounded-full", statusStyle.dotClass)} />
                  {formatStatusLabel(requisition.status)}
                </span>
                <span className={cn(
                  "px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-[0.15em] border",
                  requisition.priority === 'urgent' ? "bg-rose-50 text-rose-600 border-rose-100" : "bg-slate-50 text-slate-500 border-slate-100"
                )}>
                  {requisition.priority} Priority
                </span>
              </div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight leading-tight mb-1">
                {requisition.title}
              </h1>
              <div className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.18em] mb-1.5">
                {requisition.job_ref_id || requisition.id}
              </div>
              <div className="flex flex-wrap items-center gap-4 text-slate-400 text-[11px] font-bold uppercase tracking-[0.1em]">
                <span className="flex items-center gap-1.5"><MapPin size={12} className="text-slate-300" /> {requisition.location_id || 'Remote'}</span>
                <span className="text-slate-200">•</span>
                <span className="flex items-center gap-1.5"><Building2 size={12} className="text-slate-300" /> {requisition.department_id || 'General'}</span>
                <span className="text-slate-200">•</span>
                <span className="flex items-center gap-1.5"><Users size={12} className="text-slate-300" /> {requisition.headcount} Openings</span>
                <span className="text-slate-200">•</span>
                <span className="text-slate-300 italic normal-case tracking-normal font-medium">Created {dayjs(requisition.created_at).format('MMM D, YYYY')}</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-3 self-end lg:self-start">
            <Button className="h-10 px-5 flex items-center gap-2 font-black text-xs uppercase tracking-widest rounded-xl border-slate-200 shadow-soft-sm bg-white" onClick={() => { refetch(); onRefresh(); }}>
              <RefreshCw size={14} className="text-slate-400" /> Sync
            </Button>
            <Button 
              type="primary" 
              icon={<Edit size={16} />} 
              className="h-10 px-6 flex items-center gap-2 font-black text-xs uppercase tracking-widest rounded-xl bg-indigo-600 border-none shadow-lg shadow-indigo-100"
              onClick={() => setEditModalOpen(true)}
            >
              Edit Job
            </Button>
            <Button className="h-10 w-10 flex items-center justify-center rounded-xl border-slate-200 shadow-soft-sm bg-white" icon={<Settings2 size={18} className="text-slate-400" />} />
          </div>
        </div>

        {/* Operational Ribbon */}
        <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-slate-50 pt-5">
          <Button 
            icon={<LayoutGrid size={14} />} 
            onClick={() => setActiveTab('pipeline')}
            className={cn(
              "h-8 rounded-lg text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 px-4",
              activeTab === 'pipeline' ? "bg-indigo-50 text-indigo-600 border-indigo-100 shadow-none" : "border-slate-200 text-slate-500"
            )}
          >
            Pipeline Board
          </Button>
          <Button 
            icon={<Plus size={14} />} 
            onClick={() => navigate('/candidates?mode=add')}
            className="h-8 rounded-lg text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border-slate-200 text-slate-500 px-4"
          >
            Add Candidate
          </Button>
          <Button 
            icon={<Building2 size={14} />} 
            disabled={requisition.status !== 'active'}
            className="h-8 rounded-lg text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border-slate-200 text-slate-500 px-4"
          >
            Assign Agency
          </Button>

          <div className="ml-auto flex items-center gap-2">
            {requisition.status === 'draft' && (
              <Button type="primary" icon={<Send size={14} />} onClick={() => submitMutation.mutate()} loading={submitMutation.isPending} className="bg-amber-500 border-none h-8 text-[10px] font-black uppercase rounded-lg px-4 shadow-amber-100 shadow-lg">Submit Request</Button>
            )}
            {requisition.status === 'pending_approval' && (
              <Button type="primary" icon={<CheckCircle size={14} />} onClick={() => approveMutation.mutate()} loading={approveMutation.isPending} className="bg-blue-600 border-none h-8 text-[10px] font-black uppercase rounded-lg px-4 shadow-blue-100 shadow-lg">Approve Req</Button>
            )}
            {requisition.status === 'approved' && (
              <Button type="primary" icon={<Globe size={14} />} onClick={() => publishMutation.mutate()} loading={publishMutation.isPending} className="bg-emerald-600 border-none h-8 text-[10px] font-black uppercase rounded-lg px-4 shadow-emerald-100 shadow-lg">Publish Live</Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs Area - Enterprise Style */}
      <div className="bg-white rounded-3xl border border-slate-100 shadow-soft-sm overflow-hidden min-h-[600px]">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          className="enterprise-tabs"
          items={[
            {
              key: 'overview',
              label: 'Overview',
              children: <div className="p-8"><OverviewTab requisition={requisition} jobId={jobId} /></div>
            },
            {
              key: 'pipeline',
              label: 'Pipeline Board',
              children: (
                <div className="h-[calc(100vh-280px)] -mx-px overflow-hidden bg-slate-50/50">
                  <PipelineBoard jobId={jobId} />
                </div>
              )
            },
            {
              key: 'applications',
              label: 'Associated Talent',
              children: <div className="p-8"><ApplicationsTab jobId={jobId} onRefresh={onRefresh} isOwner={isOwner} /></div>
            },
            {
              key: 'interviews',
              label: 'Scheduled Interviews',
              children: <div className="p-8"><InterviewsTab jobId={jobId} /></div>
            },
            {
              key: 'activity',
              label: 'Operational Logs',
              children: <div className="p-8"><ActivityTab jobId={jobId} /></div>
            },
            {
              key: 'suggestions',
              label: 'AI Matching',
              children: <div className="p-8"><JobMatchSuggestions jobId={jobId} /></div>
            }
          ]}
        />
      </div>

      <Modal
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        width={720}
        title={<span className="text-xl font-black tracking-tight text-slate-900 uppercase tracking-widest">Edit Requisition</span>}
        footer={null}
        destroyOnClose
        className="rounded-3xl overflow-hidden"
      >
        <div className="pt-4">
          <JobCreateForm 
            onSuccess={() => {
              setEditModalOpen(false)
              refetch()
              onRefresh()
              queryClient.invalidateQueries({ queryKey: ['requisition', 'full', jobId] })
            }} 
            initialValues={requisition} 
          />
        </div>
      </Modal>
    </div>
  )
}
