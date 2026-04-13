import { useMemo, useState } from 'react'
import {
  Button,
  Card,
  DatePicker,
  Empty,
  Input,
  Modal,
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
  CalendarDays,
  CheckCircle2,
  Clock3,
  Filter,
  ListChecks,
  RefreshCw,
  UserCheck,
  Users,
  XCircle,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import type { Interview } from '@/types'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Title, Text } = Typography

type QueueAction = 'schedule' | 'reschedule' | 'assign' | 'cancel' | 'complete'

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'rescheduled', label: 'Rescheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'pending_feedback', label: 'Pending Feedback' },
  { value: 'cancelled', label: 'Cancelled' },
]

function interviewTypeLabel(type?: string) {
  if (!type) return 'Interview'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function QueueSection({
  title,
  icon: Icon,
  subtitle,
  dataSource,
  columns,
  loading,
  rowSelection,
}: {
  title: string
  icon: React.ElementType
  subtitle: string
  dataSource: Interview[]
  columns: ColumnsType<Interview>
  loading: boolean
  rowSelection?: any
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
      <Table
        rowKey="id"
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        rowSelection={rowSelection}
        pagination={false}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={`No ${title.toLowerCase()}`} /> }}
      />
    </Card>
  )
}

export default function RecruiterInterviewQueue() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [jobFilter, setJobFilter] = useState('')
  const [recruiterFilter, setRecruiterFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFilter, setDateFilter] = useState<string | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [actionModal, setActionModal] = useState<{ open: boolean; type: QueueAction | null; interview: Interview | null }>({
    open: false,
    type: null,
    interview: null,
  })
  const [actionDateTime, setActionDateTime] = useState<string>('')
  const [actionAssignee, setActionAssignee] = useState<string>('')
  const [actionReason, setActionReason] = useState<string>('')

  const { data, isLoading, refetch } = useApiQuery(['recruiter-interview-queue'], () => interviewsApi.list())
  const interviews: Interview[] = (data as any)?.interviews || []

  const typeOptions = useMemo(
    () => Array.from(new Set(interviews.map((item) => item.interview_type).filter(Boolean))).map((value) => ({ value, label: interviewTypeLabel(value) })),
    [interviews],
  )

  const jobOptions = useMemo(
    () => Array.from(new Set(interviews.map((item) => item.job_title).filter(Boolean))).map((value) => ({ value, label: value })),
    [interviews],
  )

  const recruiterOptions = useMemo(
    () =>
      Array.from(
        new Set(
          interviews.flatMap((item) => (Array.isArray(item.interviewers) ? item.interviewers : []).filter(Boolean)),
        ),
      ).map((value) => ({ value, label: String(value) })),
    [interviews],
  )

  const filteredInterviews = useMemo(() => {
    return interviews.filter((item) => {
      const haystack = `${item.title} ${item.candidate_name} ${item.job_title} ${item.interview_type}`.toLowerCase()
      if (search && !haystack.includes(search.toLowerCase())) return false
      if (typeFilter && item.interview_type !== typeFilter) return false
      if (jobFilter && item.job_title !== jobFilter) return false
      if (recruiterFilter && !(item.interviewers || []).includes(recruiterFilter)) return false
      if (statusFilter && item.status !== statusFilter) return false
      if (dateFilter && (!item.scheduled_at || !dayjs(item.scheduled_at).isSame(dayjs(dateFilter), 'day'))) return false
      return true
    })
  }, [interviews, search, typeFilter, jobFilter, recruiterFilter, statusFilter, dateFilter])

  const today = dayjs()
  const upcoming = filteredInterviews
    .filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isAfter(today))
    .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf())

  const todayInterviews = filteredInterviews
    .filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isSame(today, 'day'))
    .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf())

  const pendingAction = filteredInterviews.filter((item) => {
    const missingSchedule = !item.scheduled_at || ['draft', 'pending', 'awaiting_candidate'].includes(item.status)
    const needsFeedback = item.status === 'pending_feedback'
    const needsDecision = item.status === 'awaiting_decision'
    return missingSchedule || needsFeedback || needsDecision
  })

  const overdue = filteredInterviews.filter((item) => {
    const isMissed = ['no_show', 'missed'].includes(item.status)
    const delayedFeedback = item.status === 'pending_feedback'
    const delayedScheduling = !item.scheduled_at && !['completed', 'cancelled'].includes(item.status)
    const pastDueSchedule = item.scheduled_at && dayjs(item.scheduled_at).isBefore(today) && ['scheduled', 'rescheduled'].includes(item.status)
    return isMissed || delayedFeedback || delayedScheduling || pastDueSchedule
  })

  const selectedInterviews = filteredInterviews.filter((item) => selectedRowKeys.includes(item.id))

  const openActionModal = (type: QueueAction, interview: Interview | null = null) => {
    setActionModal({ open: true, type, interview })
    setActionDateTime(interview?.scheduled_at || '')
    setActionAssignee((interview?.interviewers || [])[0] || '')
    setActionReason('')
  }

  const closeActionModal = () => {
    setActionModal({ open: false, type: null, interview: null })
    setActionDateTime('')
    setActionAssignee('')
    setActionReason('')
  }

  const runAction = async (items: Interview[]) => {
    if (!actionModal.type || !items.length) return
    try {
      if (actionModal.type === 'schedule' || actionModal.type === 'reschedule') {
        if (!actionDateTime) {
          message.error('Schedule date and time is required')
          return
        }
        await Promise.all(items.map((item) => interviewsApi.reschedule(item.id, { scheduled_at: actionDateTime })))
      }
      if (actionModal.type === 'assign') {
        if (!actionAssignee.trim()) {
          message.error('Assignee is required')
          return
        }
        await Promise.all(items.map((item) => interviewsApi.update(item.id, { interviewers: [actionAssignee] as any })))
      }
      if (actionModal.type === 'cancel') {
        await Promise.all(items.map((item) => interviewsApi.cancel(item.id, actionReason || 'Cancelled from recruiter queue')))
      }
      if (actionModal.type === 'complete') {
        await Promise.all(items.map((item) => interviewsApi.complete(item.id)))
      }

      await queryClient.invalidateQueries({ queryKey: ['recruiter-interview-queue'] })
      await refetch()
      message.success(`Queue action applied to ${items.length} interview${items.length > 1 ? 's' : ''}`)
      closeActionModal()
      setSelectedRowKeys([])
    } catch {
      message.error('Unable to complete queue action')
    }
  }

  const sendReminder = (items: Interview[]) => {
    if (!items.length) {
      message.info('Select at least one interview')
      return
    }
    message.success(`Reminder queued for ${items.length} interview${items.length > 1 ? 's' : ''}`)
  }

  const baseColumns: ColumnsType<Interview> = [
    {
      title: 'Candidate Name',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      render: (value: string) => <Text className="font-semibold text-slate-900">{value || 'Unknown Candidate'}</Text>,
    },
    {
      title: 'Job',
      dataIndex: 'job_title',
      key: 'job_title',
      render: (value: string) => <Text className="text-slate-600">{value || 'Unknown Job'}</Text>,
    },
    {
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value: string) => <Tag>{interviewTypeLabel(value)}</Tag>,
    },
    {
      title: 'Date',
      dataIndex: 'scheduled_at',
      key: 'date',
      render: (value: string) => <Text>{value ? dayjs(value).format('DD MMM YYYY') : 'Needs scheduling'}</Text>,
    },
    {
      title: 'Time',
      dataIndex: 'scheduled_at',
      key: 'time',
      render: (value: string) => <Text>{value ? dayjs(value).format('hh:mm A') : '-'}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => (
        <Tag color={getStatusStyle(value, 'application').antColor}>
          {formatStatusLabel(value)}
        </Tag>
      ),
    },
    {
      title: 'Assigned Interviewer',
      dataIndex: 'interviewers',
      key: 'interviewers',
      render: (value: string[]) => <Text>{Array.isArray(value) && value.length ? value.join(', ') : 'Unassigned'}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space wrap>
          <Button size="small" onClick={() => openActionModal(record.scheduled_at ? 'reschedule' : 'schedule', record)}>
            {record.scheduled_at ? 'Reschedule' : 'Schedule'}
          </Button>
          <Button size="small" onClick={() => openActionModal('assign', record)}>Assign</Button>
          <Button size="small" onClick={() => sendReminder([record])}>Reminder</Button>
          <Button size="small" onClick={() => openActionModal('complete', record)}>Mark Complete</Button>
          <Button size="small" danger onClick={() => openActionModal('cancel', record)}>Cancel</Button>
          {record.meeting_link ? (
            <Button size="small" type="primary" href={record.meeting_link} target="_blank" rel="noreferrer">
              Join
            </Button>
          ) : null}
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">Recruiter Interview Queue</Title>
          <Text className="text-sm text-slate-500">
            Fast operational queue for scheduling, assignment, reminders, feedback follow-up, and interview completion across company and agency workflows.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Upcoming</div>
            <div className="mt-1 text-xl font-black text-slate-900">{upcoming.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Pending Action</div>
            <div className="mt-1 text-xl font-black text-slate-900">{pendingAction.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Today</div>
            <div className="mt-1 text-xl font-black text-slate-900">{todayInterviews.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Overdue</div>
            <div className="mt-1 text-xl font-black text-slate-900">{overdue.length}</div>
          </div>
        </div>
      </div>

      <Card className="rounded-3xl border-slate-200 shadow-sm">
        <div className="mb-4 flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <Filter className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-black uppercase tracking-wider text-slate-900">Filters</div>
            <div className="text-sm text-slate-500">Interview type, job, recruiter, status, and date filters for fast queue triage.</div>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <Input placeholder="Search candidate, job, type" value={search} onChange={(e) => setSearch(e.target.value)} />
          <Select value={typeFilter} onChange={setTypeFilter} options={[{ value: '', label: 'All Types' }, ...typeOptions]} />
          <Select value={jobFilter} onChange={setJobFilter} options={[{ value: '', label: 'All Jobs' }, ...jobOptions]} />
          <Select value={recruiterFilter} onChange={setRecruiterFilter} options={[{ value: '', label: 'All Recruiters' }, ...recruiterOptions]} />
          <Select value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />
          <DatePicker className="w-full" value={dateFilter ? dayjs(dateFilter) : null} onChange={(value) => setDateFilter(value ? value.toISOString() : null)} />
        </div>
      </Card>

      <Card className="rounded-3xl border-slate-200 shadow-sm">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-black uppercase tracking-wider text-slate-900">Bulk Actions</div>
              <div className="text-sm text-slate-500">Bulk schedule, bulk assign, and bulk reminders for selected interviews.</div>
            </div>
          </div>
          <Tag>{selectedInterviews.length} selected</Tag>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button icon={<CalendarDays className="h-4 w-4" />} disabled={!selectedInterviews.length} onClick={() => openActionModal('schedule')}>Bulk Schedule</Button>
          <Button icon={<UserCheck className="h-4 w-4" />} disabled={!selectedInterviews.length} onClick={() => openActionModal('assign')}>Bulk Assign</Button>
          <Button icon={<Bell className="h-4 w-4" />} disabled={!selectedInterviews.length} onClick={() => sendReminder(selectedInterviews)}>Bulk Reminder</Button>
          <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()}>Refresh Queue</Button>
          <Button type="primary" onClick={() => navigate('/interviews/bulk-scheduling')}>Open Bulk Scheduling</Button>
          <Button type="link" onClick={() => navigate('/interviews/scheduling')}>Open Scheduling</Button>
        </div>
      </Card>

      <div className="space-y-6">
        <QueueSection
          title="Upcoming Interviews"
          icon={CalendarDays}
          subtitle="Scheduled interviews with recruiter visibility into candidate, job, type, time, and assigned interviewer."
          dataSource={upcoming}
          columns={baseColumns}
          loading={isLoading}
          rowSelection={rowSelection}
        />
        <QueueSection
          title="Pending Action"
          icon={ListChecks}
          subtitle="Interviews needing scheduling, feedback, or decision follow-up."
          dataSource={pendingAction}
          columns={baseColumns}
          loading={isLoading}
          rowSelection={rowSelection}
        />
        <QueueSection
          title="Today's Interviews"
          icon={Clock3}
          subtitle="Today’s interview schedule with quick join and fast recruiter actions."
          dataSource={todayInterviews}
          columns={baseColumns}
          loading={isLoading}
          rowSelection={rowSelection}
        />
        <QueueSection
          title="Overdue Interviews"
          icon={XCircle}
          subtitle="Missed interviews, delayed scheduling, and pending feedback that need immediate attention."
          dataSource={overdue}
          columns={baseColumns}
          loading={isLoading}
          rowSelection={rowSelection}
        />
      </div>

      <Modal
        open={actionModal.open}
        onCancel={closeActionModal}
        onOk={() => runAction(actionModal.interview ? [actionModal.interview] : selectedInterviews)}
        okText="Apply Action"
        destroyOnClose
        title="Queue Action"
      >
        <div className="space-y-4">
          {(actionModal.type === 'schedule' || actionModal.type === 'reschedule') ? (
            <div>
              <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Schedule Date & Time</Text>
              <DatePicker
                showTime
                className="w-full"
                value={actionDateTime ? dayjs(actionDateTime) : null}
                onChange={(value) => setActionDateTime(value ? value.toISOString() : '')}
              />
            </div>
          ) : null}
          {actionModal.type === 'assign' ? (
            <div>
              <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Assign Interviewer</Text>
              <Input value={actionAssignee} onChange={(e) => setActionAssignee(e.target.value)} placeholder="Interviewer user ID or name shell" />
            </div>
          ) : null}
          {actionModal.type === 'cancel' ? (
            <div>
              <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Cancel Reason</Text>
              <Input.TextArea rows={4} value={actionReason} onChange={(e) => setActionReason(e.target.value)} placeholder="Reason for cancellation" />
            </div>
          ) : null}
          {actionModal.type === 'complete' ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Mark the selected interview{actionModal.interview ? '' : 's'} as complete.
            </div>
          ) : null}
          {!actionModal.interview ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Applying action to {selectedInterviews.length} selected interview{selectedInterviews.length === 1 ? '' : 's'}.
            </div>
          ) : null}
        </div>
      </Modal>
    </div>
  )
}
