import { useState, useMemo } from 'react'
import {
  Table, Tag, Button, Typography, Card, Input, Select, Badge, Avatar,
} from 'antd'
import {
  Search, RefreshCw, User, Briefcase, Calendar, Clock, ChevronRight
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import type { Application, ApplicationStatus, Candidate, JobRequisition } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)
const { Title, Text } = Typography

function prettyLabel(value?: string | null) {
  if (!value) return '—'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatShortDate(value?: string | null) {
  if (!value) return '—'
  return dayjs(value).isValid() ? dayjs(value).format('MMM D, YYYY') : value
}

const STATUS_MAP: Record<ApplicationStatus, { label: string; color: string }> = {
  applied: { label: 'Applied', color: 'blue' },
  screening: { label: 'Screening', color: 'cyan' },
  shortlisted: { label: 'Shortlisted', color: 'green' },
  in_review: { label: 'In Review', color: 'orange' },
  interview: { label: 'Interview', color: 'purple' },
  interview_scheduled: { label: 'Interview', color: 'purple' },
  on_hold: { label: 'On Hold', color: 'default' },
  offer_extended: { label: 'Offer', color: 'gold' },
  offer_accepted: { label: 'Accepted', color: 'green' },
  joined: { label: 'Joined', color: 'success' },
  placement_confirmed: { label: 'Confirmed', color: 'success' },
  placement_cancelled: { label: 'Cancelled', color: 'red' },
  rejected: { label: 'Rejected', color: 'red' },
  withdrawn: { label: 'Withdrawn', color: 'default' },
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function MySubmissions() {
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const openQuickView = useDrawerStore(s => s.openQuickView)

  // Fetch submissions
  const { data: subData, isLoading: subLoading, refetch } = useApiQuery(
    ['agency', 'my-submissions', searchText, statusFilter], 
    () => agenciesApi.mySubmissions({
      search: searchText || undefined,
      status: statusFilter || undefined,
      limit: 200,
      offset: 0,
    })
  )
  const submissions = (subData as { submissions: Application[] } | undefined)?.submissions ?? []

  // Fetch all candidates to resolve names (or at least those relevant)
  const { data: candData, isLoading: candLoading } = useApiQuery(
    ['all-candidates'],
    () => candidatesApi.list({ source: 'agency' })
  )
  const candidates = (candData as { candidates: Candidate[] } | undefined)?.candidates ?? []
  const candidateMap = useMemo(() => new Map<string, Candidate>(candidates.map((c: Candidate) => [c.id, c])), [candidates])

  // Fetch all requisitions to resolve titles
  const { data: reqData, isLoading: reqLoading } = useApiQuery(
    ['all-requisitions'],
    () => requisitionsApi.list()
  )
  const requisitions = (reqData as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []
  const jobMap = useMemo(() => new Map<string, JobRequisition>(requisitions.map((r: JobRequisition) => [r.id, r])), [requisitions])

  // Filtered submissions
  const filteredSubmissions = useMemo(() => {
    return submissions.filter((s: Application) => {
      const candidate = candidateMap.get(s.candidate_id)
      const job = jobMap.get(s.requisition_id)
      
      const matchesSearch = !searchText || 
        candidate?.full_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        job?.title?.toLowerCase().includes(searchText.toLowerCase()) ||
        s.candidate_id.toLowerCase().includes(searchText.toLowerCase())

      const matchesStatus = !statusFilter || s.status === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [submissions, candidateMap, jobMap, searchText, statusFilter])

  const expandedRowRender = (submission: Application) => (
    <div className="grid grid-cols-1 gap-4 py-2 lg:grid-cols-2">
      <div className="rounded-2xl border border-violet-100 bg-violet-50/60 p-4">
        <div className="mb-3 flex items-center justify-between">
          <Text className="text-[10px] font-bold uppercase tracking-[0.16em] text-violet-700">Candidate Protection</Text>
          <Tag color={submission.is_agency_protected ? 'purple' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">
            {submission.is_agency_protected ? 'Protected' : 'Not Protected'}
          </Tag>
        </div>
        {submission.is_agency_protected ? (
          <div className="space-y-2 text-sm text-slate-700">
            <div><span className="font-semibold">Protected Until:</span> {formatShortDate(submission.protected_until)}</div>
            <div><span className="font-semibold">Scope:</span> {prettyLabel(submission.protection_scope)}</div>
          </div>
        ) : (
          <Text className="text-sm text-slate-500">No active protection is visible for this submitted candidate.</Text>
        )}
      </div>

      <div className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4">
        <div className="mb-3 flex items-center justify-between">
          <Text className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-700">Guarantee Watch</Text>
          <Tag color={submission.is_under_guarantee ? 'gold' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">
            {submission.is_under_guarantee ? 'Under Guarantee' : 'Not Active'}
          </Tag>
        </div>
        {submission.guarantee_status ? (
          <div className="space-y-2 text-sm text-slate-700">
            <div><span className="font-semibold">Status:</span> {prettyLabel(submission.guarantee_status)}</div>
            <div><span className="font-semibold">Guarantee Start:</span> {formatShortDate(submission.guarantee_start_date)}</div>
            <div><span className="font-semibold">Guarantee End:</span> {formatShortDate(submission.guarantee_end_date)}</div>
            <div><span className="font-semibold">Resolution Type:</span> {prettyLabel(submission.guarantee_resolution_type)}</div>
            <div><span className="font-semibold">Refund Rule:</span> {submission.refund_mode ? `${prettyLabel(submission.refund_mode)}${submission.refund_percentage != null ? ` (${submission.refund_percentage}%)` : ''}` : '—'}</div>
            <div><span className="font-semibold">Replacement Limit:</span> {prettyLabel(submission.replacement_attempt_limit)}</div>
          </div>
        ) : (
          <Text className="text-sm text-slate-500">No active guarantee data is available for this submission yet.</Text>
        )}
      </div>
    </div>
  )

  const columns: ColumnsType<Application> = [
    {
      title: 'Candidate Name',
      key: 'candidate',
      render: (_, r) => {
        const c = candidateMap.get(r.candidate_id)
        return (
          <div className="flex items-center gap-3">
            <Avatar size={32} className="bg-blue-50 text-blue-600 font-bold border-none shrink-0">
              {c?.full_name?.charAt(0).toUpperCase() || 'C'}
            </Avatar>
            <div className="min-w-0">
              <Text className="block font-bold text-slate-900 leading-tight truncate">
                {c?.full_name || `ID: ${r.candidate_id.slice(0, 8)}`}
              </Text>
              <Text className="text-[10px] text-slate-400 font-medium truncate uppercase tracking-tight">
                {c?.current_title || 'No Title'}
              </Text>
              <div className="mt-1 flex flex-wrap gap-1">
                {r.is_agency_protected && (
                  <Tag color="purple" className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                    Protected Until {formatShortDate(r.protected_until)}
                  </Tag>
                )}
                {r.is_under_guarantee && (
                  <Tag color="gold" className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                    Under Guarantee
                  </Tag>
                )}
              </div>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Job Position',
      key: 'job',
      render: (_, r) => {
        const j = jobMap.get(r.requisition_id)
        return (
          <div className="flex flex-col min-w-0">
            <Text className="font-bold text-slate-700 text-sm truncate">{j?.title || 'Unknown Job'}</Text>
            <Text className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              {j?.job_type?.replace('_', ' ') || 'N/A'}
            </Text>
          </div>
        )
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (s: ApplicationStatus, r: Application) => {
        const info = STATUS_MAP[s] || { label: s, color: 'default' }
        return (
          <div className="flex flex-wrap gap-1">
            <Tag color={info.color} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
              {info.label}
            </Tag>
            {s === 'joined' && r?.is_under_guarantee && (
              <Tag color="gold" className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
                {prettyLabel(r.guarantee_status || 'active')}
              </Tag>
            )}
          </div>
        )
      }
    },
    {
      title: 'Submission Date',
      dataIndex: 'created_at',
      key: 'date',
      width: 160,
      render: (d) => (
        <div className="flex items-center gap-2 text-slate-500">
          <Calendar className="h-3.5 w-3.5 text-slate-400" />
          <span className="text-sm font-medium">{dayjs(d).format('MMM D, YYYY')}</span>
        </div>
      )
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated',
      width: 140,
      render: (d) => (
        <div className="flex items-center gap-2 text-slate-400">
          <Clock className="h-3.5 w-3.5" />
          <span className="text-xs font-medium">{dayjs(d).fromNow()}</span>
        </div>
      )
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <ChevronRight className="h-4 w-4 text-slate-300" />
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <Title level={2} className="!mb-1 !text-3xl !font-bold tracking-tight">My Submissions</Title>
          <Text className="text-slate-500 font-medium">Track all candidates you've submitted to client positions.</Text>
        </div>
        <div className="flex items-center gap-3">
          <Badge count={filteredSubmissions.length} overflowCount={999} showZero color="#1e40af" />
          <Button 
            icon={<RefreshCw className={cn("h-4 w-4", subLoading && "animate-spin")} />} 
            onClick={() => refetch()} 
            className="h-10 rounded-xl font-bold border-slate-200"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters Card */}
      <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '16px' } }}>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 z-10" />
            <Input 
              placeholder="Search by candidate name, job title, or ID..." 
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              className="pl-10 h-10 rounded-xl border-slate-200"
              allowClear
            />
          </div>
          <div className="w-full md:w-64">
            <Select
              placeholder="Filter by Status"
              className="w-full h-10"
              allowClear
              value={statusFilter}
              onChange={setStatusFilter}
              options={Object.entries(STATUS_MAP).map(([val, info]) => ({
                value: val,
                label: info.label
              }))}
            />
          </div>
        </div>
      </Card>

      {/* Table Card */}
      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
        <Table<Application>
          columns={columns}
          dataSource={filteredSubmissions}
          rowKey="id"
          loading={subLoading || candLoading || reqLoading}
          expandable={{ expandedRowRender }}
          onRow={(r) => ({
            onClick: () => {
              const job = jobMap.get(r.requisition_id)
              openQuickView('agency_submission', { 
                submission: r, 
                jobTitle: job?.title 
              })
            },
            className: "cursor-pointer transition-all duration-200 hover:bg-slate-50/80"
          })}
          pagination={{ 
            pageSize: 10,
            showSizeChanger: true,
            className: "px-6 py-4 border-t border-slate-50"
          }}
          className="modern-table"
        />
      </Card>

      {/* Stats Summary (Optional) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2 bg-blue-50/50 border border-blue-100/50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Submissions</Text>
              <Title level={4} className="!m-0">{submissions.length}</Title>
            </div>
          </div>
        </Card>
        <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2 bg-emerald-50/50 border border-emerald-100/50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-100 flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Shortlisted</Text>
              <Title level={4} className="!m-0">{submissions.filter((s: Application) => s.status === 'shortlisted' || s.status === 'interview_scheduled').length}</Title>
            </div>
          </div>
        </Card>
        <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2 bg-slate-50/50 border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-slate-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Process</Text>
              <Title level={4} className="!m-0">{submissions.filter((s: Application) => !['rejected', 'withdrawn', 'offer_accepted'].includes(s.status)).length}</Title>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
