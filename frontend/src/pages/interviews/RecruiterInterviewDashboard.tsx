import { useMemo, useState } from 'react'
import type { ElementType, ReactNode } from 'react'
import {
  Button,
  Card,
  DatePicker,
  Empty,
  Input,
  List,
  Select,
  Space,
  Tag,
  Typography,
} from 'antd'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Filter,
  ListChecks,
  RefreshCw,
  Send,
  UserCheck,
  Users,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useAuthStore } from '@/store/authStore'
import type { Interview } from '@/types'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Title, Text } = Typography

const AGENCY_ROLES = ['agency_owner', 'agency_admin', 'agency_recruiter']
const HIGH_PRIORITY_TYPES = ['final_round', 'panel_interview', 'leadership_interview', 'executive_interview']
const SCREENING_TYPES = ['recruiter_screening', 'phone_interview']

function interviewTypeLabel(type?: string) {
  if (!type) return 'Interview'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function normalizeLabel(value?: string | null) {
  return value && String(value).trim() ? String(value).trim() : 'Unassigned'
}

function getMetadataValue(interview: Interview, keys: string[]) {
  const metadata = interview.metadata || {}
  for (const key of keys) {
    const value = metadata[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function getDepartment(interview: Interview) {
  return getMetadataValue(interview, ['department', 'department_name', 'team'])
}

function getHiringManager(interview: Interview) {
  return getMetadataValue(interview, ['hiring_manager', 'hiring_manager_name', 'panel_owner'])
}

function getClientCompany(interview: Interview) {
  return getMetadataValue(interview, ['client_company', 'client_company_name', 'company_name', 'client_name'])
}

function getRecruiterName(interview: Interview) {
  return getMetadataValue(interview, ['recruiter_name', 'coordinator_name', 'agency_recruiter'])
}

function getCandidateOwner(interview: Interview) {
  return getMetadataValue(interview, ['candidate_owner', 'owner_name', 'account_manager'])
}

function getStageLabel(interview: Interview) {
  return getMetadataValue(interview, ['stage_name', 'flow_stage', 'round_name']) || `Round ${interview.interview_round || 1}`
}

function isPendingAction(interview: Interview) {
  return (
    !interview.scheduled_at ||
    ['draft', 'pending', 'awaiting_candidate', 'pending_feedback', 'awaiting_decision'].includes(interview.status)
  )
}

function isFeedbackOrDecisionPending(interview: Interview) {
  return ['pending_feedback', 'awaiting_decision'].includes(interview.status)
}

function isAwaitingConfirmation(interview: Interview) {
  return ['scheduled', 'rescheduled', 'awaiting_candidate', 'pending'].includes(interview.status)
}

function formatWhen(value?: string) {
  if (!value) return 'Schedule pending'
  return dayjs(value).format('DD MMM YYYY · hh:mm A')
}

function OptionSelect({
  value,
  onChange,
  placeholder,
  options,
}: {
  value: string
  onChange: (value: string) => void
  placeholder: string
  options: Array<{ value: string; label: string }>
}) {
  return <Select value={value} onChange={onChange} options={[{ value: '', label: placeholder }, ...options]} />
}

function SummaryMetric({ label, value }: { label: string; value: number }) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm">
      <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">{label}</div>
      <div className="mt-2 text-2xl font-black text-slate-900">{value}</div>
    </Card>
  )
}

function SectionCard({
  title,
  subtitle,
  icon: Icon,
  children,
}: {
  title: string
  subtitle: string
  icon: ElementType
  children: ReactNode
}) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-black uppercase tracking-wider text-slate-900">{title}</div>
          <div className="mt-1 text-sm text-slate-500">{subtitle}</div>
        </div>
      </div>
      {children}
    </Card>
  )
}

function AggregateList({
  items,
  primaryLabel,
  secondaryLabel,
}: {
  items: Array<{ label: string; count: number; secondary: string }>
  primaryLabel: string
  secondaryLabel: string
}) {
  if (!items.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No records available" />
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-slate-900">{item.label}</div>
              <div className="mt-1 text-xs text-slate-500">
                {primaryLabel}: {item.count} · {secondaryLabel}: {item.secondary}
              </div>
            </div>
            <Tag color="blue" className="m-0 rounded-full border-none px-3 py-1 font-bold uppercase">
              {item.count}
            </Tag>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function RecruiterInterviewDashboard() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const isAgencyWorkspace = AGENCY_ROLES.includes(user?.role || '')

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFilter, setDateFilter] = useState<string | null>(null)
  const [jobFilter, setJobFilter] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [hiringManagerFilter, setHiringManagerFilter] = useState('')
  const [interviewerFilter, setInterviewerFilter] = useState('')
  const [clientCompanyFilter, setClientCompanyFilter] = useState('')
  const [clientJobFilter, setClientJobFilter] = useState('')
  const [recruiterFilter, setRecruiterFilter] = useState('')
  const [candidateOwnerFilter, setCandidateOwnerFilter] = useState('')

  const { data, isLoading, refetch } = useApiQuery(['recruiter-interview-dashboard'], () => interviewsApi.list())
  const interviews: Interview[] = (data as any)?.interviews || []

  const typeOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map((item) => item.interview_type).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: interviewTypeLabel(value) })),
    [interviews],
  )

  const jobOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map((item) => item.job_title).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value as string })),
    [interviews],
  )

  const departmentOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map(getDepartment).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [interviews],
  )

  const hiringManagerOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map(getHiringManager).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [interviews],
  )

  const interviewerOptions = useMemo(
    () =>
      Array.from(new Set(interviews.flatMap((item) => (item.interviewers || []).filter(Boolean))))
        .sort()
        .map((value) => ({ value: String(value), label: String(value) })),
    [interviews],
  )

  const clientCompanyOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map(getClientCompany).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [interviews],
  )

  const recruiterOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map(getRecruiterName).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [interviews],
  )

  const candidateOwnerOptions = useMemo(
    () =>
      Array.from(new Set(interviews.map(getCandidateOwner).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [interviews],
  )

  const filtered = useMemo(() => {
    return interviews.filter((item) => {
      const companyName = getClientCompany(item)
      const recruiterName = getRecruiterName(item)
      const candidateOwner = getCandidateOwner(item)
      const department = getDepartment(item)
      const hiringManager = getHiringManager(item)
      const interviewers = item.interviewers || []
      const haystack = [
        item.title,
        item.candidate_name,
        item.job_title,
        item.interview_type,
        companyName,
        recruiterName,
        candidateOwner,
        department,
        hiringManager,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      if (search && !haystack.includes(search.toLowerCase())) return false
      if (typeFilter && item.interview_type !== typeFilter) return false
      if (statusFilter && item.status !== statusFilter) return false
      if (dateFilter && (!item.scheduled_at || !dayjs(item.scheduled_at).isSame(dayjs(dateFilter), 'day'))) return false

      if (isAgencyWorkspace) {
        if (clientCompanyFilter && companyName !== clientCompanyFilter) return false
        if (clientJobFilter && item.job_title !== clientJobFilter) return false
        if (recruiterFilter && recruiterName !== recruiterFilter) return false
        if (candidateOwnerFilter && candidateOwner !== candidateOwnerFilter) return false
      } else {
        if (jobFilter && item.job_title !== jobFilter) return false
        if (departmentFilter && department !== departmentFilter) return false
        if (hiringManagerFilter && hiringManager !== hiringManagerFilter) return false
        if (interviewerFilter && !interviewers.includes(interviewerFilter)) return false
      }

      return true
    })
  }, [
    interviews,
    search,
    typeFilter,
    statusFilter,
    dateFilter,
    isAgencyWorkspace,
    clientCompanyFilter,
    clientJobFilter,
    recruiterFilter,
    candidateOwnerFilter,
    jobFilter,
    departmentFilter,
    hiringManagerFilter,
    interviewerFilter,
  ])

  const today = dayjs()

  const todaysInterviews = useMemo(
    () =>
      filtered
        .filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isSame(today, 'day'))
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf()),
    [filtered, today],
  )

  const upcoming = useMemo(
    () =>
      filtered
        .filter(
          (item) =>
            item.scheduled_at &&
            dayjs(item.scheduled_at).isAfter(today) &&
            dayjs(item.scheduled_at).isBefore(today.add(7, 'day')),
        )
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf()),
    [filtered, today],
  )

  const sharedPendingActions = useMemo(() => filtered.filter(isPendingAction), [filtered])

  const companyPendingActions = useMemo(
    () => filtered.filter((item) => isFeedbackOrDecisionPending(item) || HIGH_PRIORITY_TYPES.includes(item.interview_type)),
    [filtered],
  )

  const highPriorityRounds = useMemo(
    () =>
      filtered
        .filter((item) => HIGH_PRIORITY_TYPES.includes(item.interview_type))
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf()),
    [filtered],
  )

  const agencyScreeningQueue = useMemo(
    () =>
      filtered
        .filter((item) => SCREENING_TYPES.includes(item.interview_type) && isPendingAction(item))
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf()),
    [filtered],
  )

  const clientCoordination = useMemo(
    () =>
      filtered
        .filter((item) => !SCREENING_TYPES.includes(item.interview_type) && isAwaitingConfirmation(item))
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf()),
    [filtered],
  )

  const agencyFollowUps = useMemo(
    () =>
      filtered.filter((item) =>
        ['rescheduled', 'cancelled', 'pending_feedback', 'awaiting_decision'].includes(item.status),
      ),
    [filtered],
  )

  const recentActivity = useMemo(
    () =>
      filtered
        .slice()
        .sort((a, b) => dayjs(b.updated_at || b.created_at).valueOf() - dayjs(a.updated_at || a.created_at).valueOf())
        .slice(0, 8),
    [filtered],
  )

  const summary = useMemo(
    () => ({
      scheduled: filtered.filter((item) => ['scheduled', 'rescheduled'].includes(item.status)).length,
      completed: filtered.filter((item) => item.status === 'completed').length,
      pending: filtered.filter((item) => isPendingAction(item)).length,
      cancelled: filtered.filter((item) => item.status === 'cancelled').length,
    }),
    [filtered],
  )

  const companyLoad = useMemo(() => {
    const grouped = new Map<string, { count: number; stages: Set<string> }>()
    filtered.forEach((item) => {
      const key = normalizeLabel(item.job_title)
      const stage = getStageLabel(item)
      const existing = grouped.get(key) || { count: 0, stages: new Set<string>() }
      existing.count += 1
      existing.stages.add(stage)
      grouped.set(key, existing)
    })

    return Array.from(grouped.entries())
      .map(([label, value]) => ({
        label,
        count: value.count,
        secondary: Array.from(value.stages).slice(0, 3).join(', ') || 'No stage data',
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6)
  }, [filtered])

  const agencyLoad = useMemo(() => {
    const grouped = new Map<string, { count: number; jobs: Set<string> }>()
    filtered.forEach((item) => {
      const client = normalizeLabel(getClientCompany(item))
      const job = normalizeLabel(item.job_title)
      const existing = grouped.get(client) || { count: 0, jobs: new Set<string>() }
      existing.count += 1
      existing.jobs.add(job)
      grouped.set(client, existing)
    })

    return Array.from(grouped.entries())
      .map(([label, value]) => ({
        label,
        count: value.count,
        secondary: Array.from(value.jobs).slice(0, 3).join(', ') || 'No client jobs mapped',
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6)
  }, [filtered])

  const quickActions = isAgencyWorkspace
    ? [
        { label: 'Schedule Recruiter Screen', path: '/interviews/scheduling', primary: true },
        { label: 'Coordinate Client Interview', path: '/interviews/queue' },
        { label: 'Send Candidate Reminder', path: '/interviews/queue' },
        { label: 'Follow Up With Client', path: '/interviews/queue' },
        { label: 'Update Candidate Status', path: '/interviews/queue' },
        { label: 'Reschedule Interview', path: '/interviews/scheduling' },
      ]
    : [
        { label: 'Schedule Interview', path: '/interviews/scheduling', primary: true },
        { label: 'Assign Interviewer / Panel', path: '/interviews/queue' },
        { label: 'Send Reminder', path: '/interviews/queue' },
        { label: 'Request Feedback', path: '/interviews/queue' },
        { label: 'Move To Next Round', path: '/interviews/queue' },
        { label: 'Finalize Decision', path: '/interviews/live' },
      ]

  const renderInterviewList = (items: Interview[], emptyText: string, context: 'company' | 'agency' | 'shared') => {
    if (!items.length) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
    }

    return (
      <div className="space-y-3">
        {items.map((item) => {
          const clientCompany = getClientCompany(item)
          const recruiterName = getRecruiterName(item)
          const candidateOwner = getCandidateOwner(item)
          const department = getDepartment(item)
          const hiringManager = getHiringManager(item)
          const stage = getStageLabel(item)

          return (
            <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="text-sm font-semibold text-slate-900">{item.candidate_name || 'Unknown Candidate'}</div>
                    <Tag color={getStatusStyle(item.status, 'application').antColor}>{formatStatusLabel(item.status)}</Tag>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600">{item.job_title || 'Unknown Job'}</span>
                    <span>{interviewTypeLabel(item.interview_type)}</span>
                    <span>{formatWhen(item.scheduled_at)}</span>
                    <span>{stage}</span>
                    {context === 'company' ? (
                      <>
                        <span>Dept: {normalizeLabel(department)}</span>
                        <span>Hiring manager: {normalizeLabel(hiringManager)}</span>
                        <span>
                          Assigned: {(item.interviewers || []).length ? item.interviewers.join(', ') : 'Panel pending'}
                        </span>
                      </>
                    ) : context === 'agency' ? (
                      <>
                        <span>Client: {normalizeLabel(clientCompany)}</span>
                        <span>Recruiter: {normalizeLabel(recruiterName)}</span>
                        <span>Owner: {normalizeLabel(candidateOwner)}</span>
                      </>
                    ) : (
                      <span>
                        Assigned: {(item.interviewers || []).length ? item.interviewers.join(', ') : 'Interviewer unassigned'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {item.meeting_link ? (
                    <Button type="primary" href={item.meeting_link} target="_blank" rel="noreferrer">
                      Join
                    </Button>
                  ) : null}
                  <Button onClick={() => navigate('/interviews/queue')}>Open Queue</Button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Recruiter Interview Dashboard
          </Title>
          <Text className="text-sm text-slate-500">
            {isAgencyWorkspace
              ? 'Agency-side interview operations for recruiter screening, client coordination, follow-ups, and interview load.'
              : 'Company-side interview operations for daily scheduling, internal reviews, panel coordination, and final decision readiness.'}
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()}>
            Refresh
          </Button>
          <Button type="primary" onClick={() => navigate('/interviews/queue')}>
            Open Queue
          </Button>
        </div>
      </div>

      <Card className="rounded-3xl border-slate-200 shadow-sm">
        <div className="mb-4 flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <Filter className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-black uppercase tracking-wider text-slate-900">Filters</div>
            <div className="text-sm text-slate-500">
              {isAgencyWorkspace
                ? 'Client company, client job, recruiter, candidate owner, interview type, status, and date filters.'
                : 'Job, department, hiring manager, interviewer, interview type, status, and date filters.'}
            </div>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <Input
            placeholder={isAgencyWorkspace ? 'Search candidate, client, job' : 'Search candidate, job, interview'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {isAgencyWorkspace ? (
            <>
              <OptionSelect
                value={clientCompanyFilter}
                onChange={setClientCompanyFilter}
                placeholder="All Client Companies"
                options={clientCompanyOptions}
              />
              <OptionSelect value={clientJobFilter} onChange={setClientJobFilter} placeholder="All Client Jobs" options={jobOptions} />
              <OptionSelect value={recruiterFilter} onChange={setRecruiterFilter} placeholder="All Recruiters" options={recruiterOptions} />
              <OptionSelect
                value={candidateOwnerFilter}
                onChange={setCandidateOwnerFilter}
                placeholder="All Candidate Owners"
                options={candidateOwnerOptions}
              />
            </>
          ) : (
            <>
              <OptionSelect value={jobFilter} onChange={setJobFilter} placeholder="All Jobs" options={jobOptions} />
              <OptionSelect
                value={departmentFilter}
                onChange={setDepartmentFilter}
                placeholder="All Departments"
                options={departmentOptions}
              />
              <OptionSelect
                value={hiringManagerFilter}
                onChange={setHiringManagerFilter}
                placeholder="All Hiring Managers"
                options={hiringManagerOptions}
              />
              <OptionSelect
                value={interviewerFilter}
                onChange={setInterviewerFilter}
                placeholder="All Interviewers"
                options={interviewerOptions}
              />
            </>
          )}
          <OptionSelect value={typeFilter} onChange={setTypeFilter} placeholder="All Interview Types" options={typeOptions} />
          <OptionSelect
            value={statusFilter}
            onChange={setStatusFilter}
            placeholder="All Statuses"
            options={[
              { value: 'scheduled', label: 'Scheduled' },
              { value: 'completed', label: 'Completed' },
              { value: 'pending_feedback', label: 'Pending Feedback' },
              { value: 'awaiting_decision', label: 'Decision Pending' },
              { value: 'cancelled', label: 'Cancelled' },
              { value: 'rescheduled', label: 'Rescheduled' },
            ]}
          />
          <DatePicker
            className="w-full"
            value={dateFilter ? dayjs(dateFilter) : null}
            onChange={(value) => setDateFilter(value ? value.toISOString() : null)}
          />
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryMetric label="Scheduled" value={summary.scheduled} />
        <SummaryMetric label="Completed" value={summary.completed} />
        <SummaryMetric label="Pending" value={summary.pending} />
        <SummaryMetric label="Cancelled" value={summary.cancelled} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Today's Interviews"
            subtitle={
              isAgencyWorkspace
                ? 'Today’s recruiter screening and client interview schedule.'
                : 'Today’s company interviews with assigned interviewer and panel access.'
            }
            icon={Clock3}
          >
            {renderInterviewList(
              todaysInterviews,
              isAgencyWorkspace ? 'No interviews scheduled today for agency coordination' : 'No interviews scheduled today',
              isAgencyWorkspace ? 'agency' : 'company',
            )}
          </SectionCard>

          <SectionCard
            title="Upcoming Interviews"
            subtitle="Scheduled interviews across the next seven days."
            icon={CalendarDays}
          >
            {renderInterviewList(upcoming, 'No upcoming interviews in the next 7 days', isAgencyWorkspace ? 'agency' : 'company')}
          </SectionCard>

          <SectionCard
            title={isAgencyWorkspace ? 'Recruiter Screening Queue' : 'Pending Internal Actions'}
            subtitle={
              isAgencyWorkspace
                ? 'Recruiter screening and phone interview work waiting for first contact or coordination.'
                : 'Feedback, hiring manager review, panel review, and decision work needing internal action.'
            }
            icon={isAgencyWorkspace ? UserCheck : ListChecks}
          >
            {renderInterviewList(
              isAgencyWorkspace ? agencyScreeningQueue : companyPendingActions,
              isAgencyWorkspace ? 'No recruiter screening items pending' : 'No pending internal actions',
              isAgencyWorkspace ? 'agency' : 'company',
            )}
          </SectionCard>

          <SectionCard
            title={isAgencyWorkspace ? 'Client Interview Coordination' : 'Upcoming Final / High Priority Rounds'}
            subtitle={
              isAgencyWorkspace
                ? 'Submitted candidates, upcoming client interviews, and confirmations awaiting response.'
                : 'Final round, panel, leadership, and executive interviews that need close coordination.'
            }
            icon={isAgencyWorkspace ? Building2 : CheckCircle2}
          >
            {renderInterviewList(
              isAgencyWorkspace ? clientCoordination : highPriorityRounds,
              isAgencyWorkspace ? 'No client interviews awaiting coordination' : 'No high priority rounds scheduled',
              isAgencyWorkspace ? 'agency' : 'company',
            )}
          </SectionCard>

          <SectionCard
            title={isAgencyWorkspace ? 'Candidate Follow-up Actions' : 'Job-wise Interview Load'}
            subtitle={
              isAgencyWorkspace
                ? 'Reminder pending, reschedule needed, no-show follow-up, and client feedback follow-up.'
                : 'Interview volume by open job with visible stage distribution.'
            }
            icon={isAgencyWorkspace ? Send : Briefcase}
          >
            {isAgencyWorkspace ? (
              renderInterviewList(agencyFollowUps, 'No follow-up actions pending', 'agency')
            ) : (
              <AggregateList items={companyLoad} primaryLabel="Interviews" secondaryLabel="Stages" />
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Recruiter Quick Actions"
            subtitle={
              isAgencyWorkspace
                ? 'Agency-facing actions for scheduling, coordination, reminders, and client follow-ups.'
                : 'Company-facing actions for scheduling, assignments, reminders, and decision readiness.'
            }
            icon={UserCheck}
          >
            <div className="grid gap-3">
              {quickActions.map((action) => (
                <Button
                  key={action.label}
                  type={action.primary ? 'primary' : 'default'}
                  onClick={() => navigate(action.path)}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title={isAgencyWorkspace ? 'Client-wise Interview Load' : 'Shared Pending Actions'}
            subtitle={
              isAgencyWorkspace
                ? 'Interview volume by client company and client job.'
                : 'Cross-dashboard pending scheduling, feedback, and decision work.'
            }
            icon={isAgencyWorkspace ? Users : Bell}
          >
            {isAgencyWorkspace ? (
              <AggregateList items={agencyLoad} primaryLabel="Interviews" secondaryLabel="Client Jobs" />
            ) : (
              renderInterviewList(sharedPendingActions, 'No shared pending actions', 'shared')
            )}
          </SectionCard>

          <SectionCard
            title="Recent Activity"
            subtitle="Latest interview changes and recent operational updates."
            icon={Bell}
          >
            {isLoading ? (
              <div className="py-4 text-sm text-slate-500">Loading activity...</div>
            ) : recentActivity.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No recent interview activity" />
            ) : (
              <List
                dataSource={recentActivity}
                renderItem={(item) => (
                  <List.Item className="!px-0">
                    <List.Item.Meta
                      title={<span className="text-sm font-semibold text-slate-900">{item.candidate_name || 'Unknown Candidate'}</span>}
                      description={
                        <Space direction="vertical" size={2}>
                          <Text className="text-sm text-slate-600">
                            {item.job_title || 'Unknown Job'} · {interviewTypeLabel(item.interview_type)}
                          </Text>
                          <Text className="text-xs text-slate-400">
                            {formatStatusLabel(item.status)} · {dayjs(item.updated_at || item.created_at).format('DD MMM YYYY · hh:mm A')}
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
