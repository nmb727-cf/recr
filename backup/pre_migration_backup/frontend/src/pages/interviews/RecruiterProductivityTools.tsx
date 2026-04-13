import { useMemo, useState } from 'react'
import type { ElementType, ReactNode } from 'react'
import {
  Button,
  Card,
  DatePicker,
  Empty,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  Briefcase,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Filter,
  ListChecks,
  MessageSquareText,
  RefreshCw,
  Send,
  Zap,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useAuthStore } from '@/store/authStore'
import type { Interview } from '@/types'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Title, Text } = Typography
const { TextArea } = Input

const AGENCY_ROLES = ['agency_owner', 'agency_admin', 'agency_recruiter']
const COMPANY_HIGH_PRIORITY_TYPES = ['final_round', 'panel_interview', 'leadership_interview', 'executive_interview']
const AGENCY_SCREENING_TYPES = ['recruiter_screening', 'phone_interview']

function interviewTypeLabel(type?: string) {
  if (!type) return 'Interview'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
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

export default function RecruiterProductivityTools() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
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
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([])
  const [bulkAssignee, setBulkAssignee] = useState('')
  const [bulkStatus, setBulkStatus] = useState('')
  const [bulkDateTime, setBulkDateTime] = useState<string>('')
  const [noteShell, setNoteShell] = useState('')
  const [callLogShell, setCallLogShell] = useState('')
  const [running, setRunning] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(['recruiter-productivity-tools'], () => interviewsApi.list())
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
  const interviewerOptions = useMemo(
    () =>
      Array.from(new Set(interviews.flatMap((item) => (item.interviewers || []).filter(Boolean))))
        .sort()
        .map((value) => ({ value: String(value), label: String(value) })),
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
      const haystack = [
        item.title,
        item.candidate_name,
        item.job_title,
        item.interview_type,
        getClientCompany(item),
        getRecruiterName(item),
        getCandidateOwner(item),
        getDepartment(item),
        getHiringManager(item),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      if (search && !haystack.includes(search.toLowerCase())) return false
      if (typeFilter && item.interview_type !== typeFilter) return false
      if (statusFilter && item.status !== statusFilter) return false
      if (dateFilter && (!item.scheduled_at || !dayjs(item.scheduled_at).isSame(dayjs(dateFilter), 'day'))) return false

      if (isAgencyWorkspace) {
        if (clientCompanyFilter && getClientCompany(item) !== clientCompanyFilter) return false
        if (clientJobFilter && item.job_title !== clientJobFilter) return false
        if (recruiterFilter && getRecruiterName(item) !== recruiterFilter) return false
        if (candidateOwnerFilter && getCandidateOwner(item) !== candidateOwnerFilter) return false
      } else {
        if (jobFilter && item.job_title !== jobFilter) return false
        if (departmentFilter && getDepartment(item) !== departmentFilter) return false
        if (hiringManagerFilter && getHiringManager(item) !== hiringManagerFilter) return false
        if (interviewerFilter && !(item.interviewers || []).includes(interviewerFilter)) return false
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

  const selectedInterviews = useMemo(
    () => filtered.filter((item) => selectedIds.includes(item.id)),
    [filtered, selectedIds],
  )

  const reminderItems = useMemo(
    () =>
      filtered.filter((item) => {
        const overdueFeedback = item.status === 'pending_feedback'
        const overdueDecision = item.status === 'awaiting_decision'
        const unscheduled = !item.scheduled_at && !['completed', 'cancelled'].includes(item.status)
        const noShowFollowup = ['no_show', 'missed'].includes(item.status)
        return overdueFeedback || overdueDecision || unscheduled || noShowFollowup
      }),
    [filtered],
  )

  const workBuckets = useMemo(() => {
    const now = dayjs()
    const urgent = filtered.filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isBefore(now) && !['completed', 'cancelled'].includes(item.status))
    const today = filtered.filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isSame(now, 'day'))
    const followUp = filtered.filter((item) => ['pending_feedback', 'awaiting_decision', 'rescheduled'].includes(item.status))
    const highPriority = filtered.filter((item) =>
      isAgencyWorkspace ? AGENCY_SCREENING_TYPES.includes(item.interview_type) : COMPANY_HIGH_PRIORITY_TYPES.includes(item.interview_type),
    )
    return [
      { label: 'Urgent Now', count: urgent.length, helper: 'Needs action immediately' },
      { label: 'Due Today', count: today.length, helper: 'Scheduled for today' },
      { label: 'Follow-up Required', count: followUp.length, helper: 'Reminder or review pending' },
      {
        label: isAgencyWorkspace ? 'Screening / Client Moves' : 'Final / Critical Rounds',
        count: highPriority.length,
        helper: isAgencyWorkspace ? 'Submission and client movement focus' : 'Final decision readiness focus',
      },
    ]
  }, [filtered, isAgencyWorkspace])

  const quickActionCards = isAgencyWorkspace
    ? [
        {
          title: 'Quick Recruiter Screening',
          description: 'Fast-track recruiter screen scheduling, reminders, and completion handling.',
          actions: [
            { label: 'Schedule Recruiter Screen', path: '/interviews/scheduling' },
            { label: 'Mark Screen Complete', mode: 'complete' as const },
            { label: 'Send Candidate Reminder', mode: 'reminder' as const },
          ],
        },
        {
          title: 'Client Interview Coordination',
          description: 'Coordinate with client interviewers and keep candidate confirmations moving.',
          actions: [
            { label: 'Schedule With Client', path: '/interviews/scheduling' },
            { label: 'Follow Up With Client', mode: 'note' as const },
            { label: 'Reschedule Quickly', mode: 'reschedule' as const },
          ],
        },
        {
          title: 'Submission Follow-Up Tools',
          description: 'Move submissions through client interview and feedback checkpoints faster.',
          actions: [
            { label: 'Awaiting Client Interview', status: 'scheduled' },
            { label: 'Awaiting Client Feedback', status: 'awaiting_decision' },
            { label: 'Update Candidate Status', path: '/interviews/queue' },
          ],
        },
      ]
    : [
        {
          title: 'Quick Schedule',
          description: 'Fast schedule next round, assign interviewer or panel, and secure a slot.',
          actions: [
            { label: 'Fast Schedule Next Round', path: '/interviews/scheduling' },
            { label: 'Assign Interviewer / Panel', mode: 'assign' as const },
            { label: 'Pick Slot Quickly', mode: 'reschedule' as const },
          ],
        },
        {
          title: 'Quick Feedback Chase',
          description: 'Accelerate overdue interviewer and hiring manager follow-up.',
          actions: [
            { label: 'Remind Interviewer', mode: 'reminder' as const },
            { label: 'Remind Hiring Manager', mode: 'note' as const },
            { label: 'Mark Overdue Follow-up', status: 'pending_feedback' },
          ],
        },
        {
          title: 'Quick Stage Actions',
          description: 'Move strong candidates forward without leaving the recruiter workflow.',
          actions: [
            { label: 'Move To Next Round', path: '/interviews/queue' },
            { label: 'Ready For Final Round', status: 'scheduled' },
            { label: 'Ready For Decision', status: 'awaiting_decision' },
          ],
        },
      ]

  const shortcutActions = isAgencyWorkspace
    ? [
        { label: 'Bulk Candidate Reminders', path: '/interviews/bulk-scheduling' },
        { label: 'Bulk Recruiter Screening', path: '/interviews/bulk-scheduling' },
        { label: 'Bulk Follow-up Actions', path: '/interviews/queue' },
        { label: 'Quick Call Log Shell', mode: 'call-log' as const },
        { label: 'Quick Note Shell', mode: 'note' as const },
        { label: 'Next Action Shortcuts', path: '/interviews/dashboard' },
      ]
    : [
        { label: 'Bulk Assign Interviewers', path: '/interviews/bulk-scheduling' },
        { label: 'Bulk Send Reminders', mode: 'reminder' as const },
        { label: 'Bulk Reschedule', mode: 'reschedule' as const },
        { label: 'Panel Coordination Shortcuts', path: '/interviews/live' },
        { label: 'Hiring Team Follow-up', mode: 'note' as const },
        { label: 'Final Round Prep Shortcuts', path: '/interviews/dashboard' },
      ]

  const bulkStatusOptions = isAgencyWorkspace
    ? [
        { value: 'scheduled', label: 'Awaiting Client Interview' },
        { value: 'awaiting_decision', label: 'Awaiting Client Feedback' },
        { value: 'completed', label: 'Screen Complete' },
        { value: 'rescheduled', label: 'Reschedule Required' },
      ]
    : [
        { value: 'scheduled', label: 'Ready For Next Round' },
        { value: 'awaiting_decision', label: 'Ready For Decision' },
        { value: 'pending_feedback', label: 'Feedback Follow-up' },
        { value: 'rescheduled', label: 'Reschedule Required' },
      ]

  const rows: ColumnsType<Interview> = [
    {
      title: 'Candidate',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      render: (value: string) => <Text className="font-semibold text-slate-900">{value || 'Unknown Candidate'}</Text>,
    },
    {
      title: isAgencyWorkspace ? 'Client / Job' : 'Job / Stage',
      key: 'context',
      render: (_, record) => (
        <div className="space-y-1">
          <div className="text-sm text-slate-800">{record.job_title || 'Unknown Job'}</div>
          <div className="text-xs text-slate-500">
            {isAgencyWorkspace ? getClientCompany(record) || 'Client pending' : getStageLabel(record)}
          </div>
        </div>
      ),
    },
    {
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value: string) => <Tag>{interviewTypeLabel(value)}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => (
        <Tag color={getStatusStyle(value, 'application').antColor}>{formatStatusLabel(value)}</Tag>
      ),
    },
    {
      title: 'Assigned',
      key: 'assigned',
      render: (_, record) => (
        <Text className="text-slate-600">
          {isAgencyWorkspace
            ? getRecruiterName(record) || getCandidateOwner(record) || 'Owner pending'
            : (record.interviewers || []).join(', ') || getHiringManager(record) || 'Assignee pending'}
        </Text>
      ),
    },
  ]

  const runSelected = async (mode: 'assign' | 'status' | 'reschedule' | 'complete') => {
    if (!selectedInterviews.length) {
      message.info('Select at least one interview')
      return
    }
    try {
      setRunning(true)
      if (mode === 'assign') {
        if (!bulkAssignee.trim()) {
          message.error('Select an assignee first')
          return
        }
        await Promise.all(selectedInterviews.map((item) => interviewsApi.update(item.id, { interviewers: [bulkAssignee] as any })))
      }
      if (mode === 'status') {
        if (!bulkStatus) {
          message.error('Select a status update first')
          return
        }
        await Promise.all(selectedInterviews.map((item) => interviewsApi.update(item.id, { status: bulkStatus as any })))
      }
      if (mode === 'reschedule') {
        if (!bulkDateTime) {
          message.error('Select a date and time first')
          return
        }
        await Promise.all(selectedInterviews.map((item) => interviewsApi.reschedule(item.id, { scheduled_at: bulkDateTime })))
      }
      if (mode === 'complete') {
        await Promise.all(selectedInterviews.map((item) => interviewsApi.complete(item.id)))
      }
      await queryClient.invalidateQueries({ queryKey: ['recruiter-productivity-tools'] })
      await queryClient.invalidateQueries({ queryKey: ['recruiter-interview-queue'] })
      await refetch()
      message.success(`Action applied to ${selectedInterviews.length} interview${selectedInterviews.length > 1 ? 's' : ''}`)
      setSelectedIds([])
    } catch {
      message.error('Unable to apply productivity action')
    } finally {
      setRunning(false)
    }
  }

  const runSoftAction = (mode: 'reminder' | 'note' | 'call-log' | 'assign' | 'reschedule', label: string) => {
    if (mode === 'assign') {
      void runSelected('assign')
      return
    }
    if (mode === 'reschedule') {
      void runSelected('reschedule')
      return
    }
    if (mode === 'reminder') {
      message.success(
        `${label} queued for ${selectedInterviews.length || reminderItems.length || filtered.length ? Math.max(selectedInterviews.length, 1) : 0} interview${Math.max(selectedInterviews.length, 1) > 1 ? 's' : ''}`,
      )
      return
    }
    if (mode === 'note') {
      if (!noteShell.trim()) {
        message.info('Add a note first')
        return
      }
      message.success('Coordination note shell saved')
      return
    }
    if (mode === 'call-log') {
      if (!callLogShell.trim()) {
        message.info('Add a call log first')
        return
      }
      message.success('Call log shell saved')
    }
  }

  const runStatusShortcut = async (status: string, label: string) => {
    if (!selectedInterviews.length) {
      message.info('Select at least one interview')
      return
    }
    try {
      setRunning(true)
      await Promise.all(selectedInterviews.map((item) => interviewsApi.update(item.id, { status: status as any })))
      await queryClient.invalidateQueries({ queryKey: ['recruiter-productivity-tools'] })
      await refetch()
      message.success(`${label} applied to ${selectedInterviews.length} interview${selectedInterviews.length > 1 ? 's' : ''}`)
      setSelectedIds([])
    } catch {
      message.error('Unable to update interview status')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">Recruiter Productivity Tools</Title>
          <Text className="text-sm text-slate-500">
            {isAgencyWorkspace
              ? 'Agency-side acceleration layer for screening, client coordination, reminders, follow-ups, and recruiter shortcuts.'
              : 'Company-side acceleration layer for scheduling, internal coordination, feedback chasing, and final decision readiness.'}
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()}>Refresh</Button>
          <Button onClick={() => navigate('/interviews/queue')}>Open Queue</Button>
          <Button type="primary" onClick={() => navigate('/interviews/bulk-scheduling')}>Open Bulk Scheduling</Button>
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
                ? 'Client company, client job, recruiter, candidate owner, status, type, and date filters.'
                : 'Job, department, interviewer, hiring manager, status, type, and date filters.'}
            </div>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <Input
            placeholder={isAgencyWorkspace ? 'Search candidate, client, job' : 'Search candidate, job, stage'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {isAgencyWorkspace ? (
            <>
              <OptionSelect value={clientCompanyFilter} onChange={setClientCompanyFilter} placeholder="All Client Companies" options={clientCompanyOptions} />
              <OptionSelect value={clientJobFilter} onChange={setClientJobFilter} placeholder="All Client Jobs" options={jobOptions} />
              <OptionSelect value={recruiterFilter} onChange={setRecruiterFilter} placeholder="All Recruiters" options={recruiterOptions} />
              <OptionSelect value={candidateOwnerFilter} onChange={setCandidateOwnerFilter} placeholder="All Candidate Owners" options={candidateOwnerOptions} />
            </>
          ) : (
            <>
              <OptionSelect value={jobFilter} onChange={setJobFilter} placeholder="All Jobs" options={jobOptions} />
              <OptionSelect value={departmentFilter} onChange={setDepartmentFilter} placeholder="All Departments" options={departmentOptions} />
              <OptionSelect value={interviewerFilter} onChange={setInterviewerFilter} placeholder="All Interviewers" options={interviewerOptions} />
              <OptionSelect value={hiringManagerFilter} onChange={setHiringManagerFilter} placeholder="All Hiring Managers" options={hiringManagerOptions} />
            </>
          )}
          <OptionSelect value={typeFilter} onChange={setTypeFilter} placeholder="All Interview Types" options={typeOptions} />
          <OptionSelect
            value={statusFilter}
            onChange={setStatusFilter}
            placeholder="All Statuses"
            options={[
              { value: 'scheduled', label: 'Scheduled' },
              { value: 'rescheduled', label: 'Rescheduled' },
              { value: 'pending_feedback', label: 'Pending Feedback' },
              { value: 'awaiting_decision', label: 'Awaiting Decision' },
              { value: 'completed', label: 'Completed' },
            ]}
          />
          <DatePicker className="w-full" value={dateFilter ? dayjs(dateFilter) : null} onChange={(value) => setDateFilter(value ? value.toISOString() : null)} />
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Quick Actions"
            subtitle={isAgencyWorkspace ? 'Agency-specific acceleration for screening and client coordination.' : 'Company-specific acceleration for scheduling, feedback, and stage movement.'}
            icon={Zap}
          >
            <div className="grid gap-4 xl:grid-cols-3">
              {quickActionCards.map((card) => (
                <div key={card.title} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="text-sm font-semibold text-slate-900">{card.title}</div>
                  <div className="mt-1 text-sm text-slate-500">{card.description}</div>
                  <div className="mt-4 grid gap-2">
                    {card.actions.map((action) => (
                      <Button
                        key={action.label}
                        onClick={() => {
                          if ('path' in action && action.path) navigate(action.path)
                          if ('mode' in action && action.mode) runSoftAction(action.mode, action.label)
                          if ('status' in action && action.status) void runStatusShortcut(action.status, action.label)
                        }}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Bulk Actions"
            subtitle={isAgencyWorkspace ? 'Bulk reminders, screening scheduling, follow-up actions, and status updates.' : 'Bulk interviewer assignment, reminders, rescheduling, and status updates.'}
            icon={ListChecks}
          >
            <div className="mb-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Select
                value={bulkAssignee}
                onChange={setBulkAssignee}
                placeholder={isAgencyWorkspace ? 'Select recruiter / owner' : 'Select interviewer / panel lead'}
                options={interviewerOptions}
              />
              <Select
                value={bulkStatus}
                onChange={setBulkStatus}
                placeholder="Select status update"
                options={bulkStatusOptions}
              />
              <DatePicker
                showTime
                className="w-full"
                value={bulkDateTime ? dayjs(bulkDateTime) : null}
                onChange={(value) => setBulkDateTime(value ? value.toISOString() : '')}
              />
              <div className="flex flex-wrap gap-2">
                <Button loading={running} onClick={() => void runSelected('assign')}>{isAgencyWorkspace ? 'Bulk Assign Owner' : 'Bulk Assign'}</Button>
                <Button loading={running} onClick={() => void runSelected('reschedule')}>Bulk Reschedule</Button>
                <Button loading={running} onClick={() => void runSelected('status')}>Bulk Status Update</Button>
                <Button onClick={() => runSoftAction('reminder', 'Bulk Reminder')}>Bulk Reminder</Button>
              </div>
            </div>

            <Table
              rowKey="id"
              loading={isLoading}
              columns={rows}
              dataSource={filtered}
              pagination={{ pageSize: 8 }}
              rowSelection={{ selectedRowKeys: selectedIds, onChange: setSelectedIds }}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interviews available for productivity actions" /> }}
            />
          </SectionCard>

          <SectionCard
            title="Reminder Center"
            subtitle={isAgencyWorkspace ? 'Pending reminders, reschedules, no-show follow-up, and client response chasing.' : 'Pending reminders, overdue feedback, hiring manager follow-up, and internal escalations.'}
            icon={Bell}
          >
            {!reminderItems.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No pending reminder work" />
            ) : (
              <div className="space-y-3">
                {reminderItems.slice(0, 8).map((item) => (
                  <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{item.candidate_name || 'Unknown Candidate'}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {item.job_title || 'Unknown Job'} · {interviewTypeLabel(item.interview_type)} · {formatStatusLabel(item.status)}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button onClick={() => runSoftAction('reminder', 'Reminder')}>Send Reminder</Button>
                        <Button onClick={() => navigate('/interviews/queue')}>Open Queue</Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Productivity Shortcuts"
            subtitle={isAgencyWorkspace ? 'High-frequency recruiter coordination shortcuts for agency operations.' : 'High-frequency internal hiring shortcuts for company operations.'}
            icon={CalendarDays}
          >
            <div className="grid gap-2">
              {shortcutActions.map((action) => (
                <Button
                  key={action.label}
                  onClick={() => {
                    if ('path' in action && action.path) navigate(action.path)
                    if ('mode' in action && action.mode) runSoftAction(action.mode, action.label)
                  }}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title={isAgencyWorkspace ? 'Quick Call Log / Note Shells' : 'Internal Coordination Tools'}
            subtitle={isAgencyWorkspace ? 'Capture call log shells and recruiter notes without leaving the workflow.' : 'Store panel coordination notes, hiring team follow-up context, and final round prep reminders.'}
            icon={MessageSquareText}
          >
            {isAgencyWorkspace ? (
              <div className="space-y-3">
                <TextArea
                  rows={4}
                  placeholder="Quick call log shell for client / candidate follow-up"
                  value={callLogShell}
                  onChange={(e) => setCallLogShell(e.target.value)}
                />
                <TextArea
                  rows={4}
                  placeholder="Quick recruiter note shell"
                  value={noteShell}
                  onChange={(e) => setNoteShell(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button onClick={() => runSoftAction('call-log', 'Quick Call Log')}>Save Call Log Shell</Button>
                  <Button onClick={() => runSoftAction('note', 'Quick Note')}>Save Note Shell</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <TextArea
                  rows={4}
                  placeholder="Panel coordination or hiring team follow-up shell"
                  value={noteShell}
                  onChange={(e) => setNoteShell(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button onClick={() => runSoftAction('note', 'Hiring Team Follow-up')}>Save Coordination Note</Button>
                  <Button onClick={() => navigate('/interviews/live')}>Open Final Round Prep</Button>
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Pending Work Buckets"
            subtitle="Interviews grouped by urgency so recruiters can act with minimal clicks."
            icon={Clock3}
          >
            <div className="space-y-3">
              {workBuckets.map((bucket) => (
                <div key={bucket.label} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-900">{bucket.label}</div>
                      <div className="mt-1 text-xs text-slate-500">{bucket.helper}</div>
                    </div>
                    <Tag color={bucket.count > 0 ? 'blue' : 'default'} className="m-0 rounded-full border-none px-3 py-1 font-bold uppercase">
                      {bucket.count}
                    </Tag>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Context Summary"
            subtitle="Current selection and workload visibility for recruiter actions."
            icon={CheckCircle2}
          >
            <Space direction="vertical" size={8} className="w-full">
              <Text className="text-sm text-slate-600">Filtered interviews: <span className="font-semibold text-slate-900">{filtered.length}</span></Text>
              <Text className="text-sm text-slate-600">Selected for action: <span className="font-semibold text-slate-900">{selectedInterviews.length}</span></Text>
              <Text className="text-sm text-slate-600">Reminder queue: <span className="font-semibold text-slate-900">{reminderItems.length}</span></Text>
              <Text className="text-sm text-slate-600">
                Workspace mode: <span className="font-semibold text-slate-900">{isAgencyWorkspace ? 'Agency Recruiter' : 'Company Recruiter'}</span>
              </Text>
            </Space>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
