import { useMemo } from 'react'
import { Button, Card, Empty, List, Space, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock3,
  ExternalLink,
  PlayCircle,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { notificationsApi } from '@/api/notifications'
import type { Notification } from '@/types'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
  status?: string
  result?: string
  decision?: { decision?: string }
  candidate_runtime?: { token?: string; scheduling_token?: string }
  scheduling_link_token?: string
  scheduling_token?: string
  scheduling_link?: { token?: string; url?: string }
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function statusColor(status?: string) {
  switch (status) {
    case 'completed':
      return 'green'
    case 'in_progress':
      return 'gold'
    case 'scheduled':
      return 'blue'
    case 'awaiting_candidate':
      return 'purple'
    case 'expired':
    case 'missed':
    case 'blocked':
    case 'cancelled':
      return 'red'
    default:
      return 'default'
  }
}

function getInterviewTitle(row: CandidateInterviewRow) {
  return row.title || interviewTypeLabel(row.interview_type)
}

function getAccessToken(row: CandidateInterviewRow) {
  return row.candidate_runtime?.token || ''
}

function getReschedulePath(row: CandidateInterviewRow) {
  const token =
    row.scheduling_link_token ||
    row.scheduling_token ||
    row.scheduling_link?.token ||
    row.candidate_runtime?.scheduling_token ||
    ''
  return token ? `/interviews/scheduling/self/${token}` : null
}

function InterviewRow({
  row,
  primaryLabel = 'Join Interview',
  showResult = false,
  primaryAction = 'runtime',
  onAddToCalendar,
}: {
  row: CandidateInterviewRow
  primaryLabel?: string
  showResult?: boolean
  primaryAction?: 'runtime' | 'results'
  onAddToCalendar?: (row: CandidateInterviewRow) => void
}) {
  const navigate = useNavigate()
  const reschedulePath = getReschedulePath(row)
  const accessToken = getAccessToken(row)

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-slate-900">{getInterviewTitle(row)}</div>
            <Tag color={statusColor(row.status)} className="m-0">
              {row.status || 'pending'}
            </Tag>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600">
              {interviewTypeLabel(row.interview_type)}
            </span>
            <span className="flex items-center gap-1">
              <CalendarDays className="h-3.5 w-3.5" />
              {row.scheduled_at ? dayjs(row.scheduled_at).format('DD MMM YYYY') : 'Date pending'}
            </span>
            <span className="flex items-center gap-1">
              <Clock3 className="h-3.5 w-3.5" />
              {row.scheduled_at ? dayjs(row.scheduled_at).format('hh:mm A') : 'Time pending'}
              {row.duration_minutes ? ` · ${row.duration_minutes} min` : ''}
            </span>
          </div>
          {showResult ? (
            <div className="mt-3 text-sm text-slate-600">
              Result: {row.result || row.decision?.decision || 'Awaiting release'}
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            type="primary"
            icon={<PlayCircle className="h-4 w-4" />}
            onClick={() =>
              primaryAction === 'results'
                ? navigate(`/candidate/interviews/results?interview=${row.id}`)
                : navigate(`/candidate/interviews/${row.id}/runtime?access_token=${accessToken}`)
            }
          >
            {primaryLabel}
          </Button>
          <Button onClick={() => navigate(`/candidate/interviews/${row.id}/instructions?access_token=${accessToken}`)}>
            View Details
          </Button>
          {row.status === 'scheduled' && onAddToCalendar && (
            <Button icon={<CalendarDays className="h-4 w-4" />} onClick={() => onAddToCalendar(row)}>
              Calendar
            </Button>
          )}
          <Button
            icon={<ExternalLink className="h-4 w-4" />}
            disabled={!reschedulePath}
            onClick={() => {
              if (reschedulePath) navigate(reschedulePath)
            }}
          >
            Reschedule
          </Button>
        </div>
      </div>
    </div>
  )
}

function SectionCard({
  title,
  icon,
  subtitle,
  children,
}: {
  title: string
  icon: React.ElementType
  subtitle?: string
  children: React.ReactNode
}) {
  const Icon = icon
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-black uppercase tracking-wider text-slate-900">{title}</div>
          {subtitle ? <div className="mt-1 text-sm text-slate-500">{subtitle}</div> : null}
        </div>
      </div>
      {children}
    </Card>
  )
}

export default function CandidateInterviewDashboard() {
  const navigate = useNavigate()

  const handleAddToCalendar = (interview: CandidateInterviewRow) => {
    if (!interview.scheduled_at) return
    const start = dayjs(interview.scheduled_at).format('YYYYMMDDTHHmmssZ')
    const end = dayjs(interview.scheduled_at).add(interview.duration_minutes || 60, 'minute').format('YYYYMMDDTHHmmssZ')
    const title = encodeURIComponent(interview.title || 'Interview')
    const details = encodeURIComponent(`Interview Type: ${interview.interview_type}\nJoin Link: ${interview.meeting_link || 'TBD'}`)
    
    // Simple Google Calendar link
    const url = `https://www.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${start}/${end}&details=${details}&sf=true&output=xml`
    window.open(url, '_blank')
  }

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interviews_dashboard'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const notificationsQuery = useQuery({
    queryKey: ['candidate_interview_notifications'],
    queryFn: async () => (await notificationsApi.list()).data?.data?.notifications || [],
  })

  const dashboard = interviewsQuery.data || {}
  const upcomingInterviews: CandidateInterviewRow[] = dashboard.upcoming_interviews || []
  const pendingInterviews: CandidateInterviewRow[] = dashboard.pending_interviews || []
  const completedInterviews: CandidateInterviewRow[] = dashboard.completed_interviews || []
  const missedInterviews: CandidateInterviewRow[] = dashboard.missed_interviews || []
  const cancelledInterviews: CandidateInterviewRow[] = dashboard.cancelled_interviews || []

  const interviewNotifications = useMemo(() => {
    const items: Notification[] = notificationsQuery.data || []
    return items
      .filter((item) => {
        const haystack = `${item.title} ${item.body} ${item.type}`.toLowerCase()
        return haystack.includes('interview') || haystack.includes('schedule') || haystack.includes('decision')
      })
      .slice(0, 6)
  }, [notificationsQuery.data])

  const quickActionTarget = pendingInterviews[0] || upcomingInterviews[0] || null
  const totalInterviews = upcomingInterviews.length + pendingInterviews.length + completedInterviews.length + missedInterviews.length + cancelledInterviews.length

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interviews
          </Title>
          <Text className="text-sm text-slate-500">
            Manage upcoming rounds, pending actions, completed interviews, and interview updates in one place.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Upcoming</div>
            <div className="mt-1 text-xl font-black text-slate-900">{upcomingInterviews.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Pending</div>
            <div className="mt-1 text-xl font-black text-slate-900">{pendingInterviews.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Completed</div>
            <div className="mt-1 text-xl font-black text-slate-900">{completedInterviews.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Total</div>
            <div className="mt-1 text-xl font-black text-slate-900">{totalInterviews}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Upcoming Interviews"
            icon={CalendarDays}
            subtitle="Scheduled interviews with join access and timing details."
          >
            {upcomingInterviews.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No upcoming interviews" />
            ) : (
              <div className="space-y-3">
                {upcomingInterviews.slice(0, 5).map((row) => (
                  <InterviewRow key={row.id} row={row} onAddToCalendar={handleAddToCalendar} />
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Pending Interviews"
            icon={Clock3}
            subtitle="Interviews waiting for candidate action or currently in progress."
          >
            {pendingInterviews.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No pending interviews" />
            ) : (
              <div className="space-y-3">
                {pendingInterviews.map((row) => (
                  <InterviewRow 
                    key={row.id} 
                    row={row} 
                    primaryLabel={row.status === 'in_progress' ? 'Resume Interview' : 'Join Interview'} 
                    onAddToCalendar={handleAddToCalendar}
                  />
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Completed Interviews"
            icon={CheckCircle2}
            subtitle="Completed interviews and visible outcome information where release is allowed."
          >
            {completedInterviews.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No completed interviews" />
            ) : (
              <div className="space-y-3">
                {completedInterviews.map((row) => (
                  <div key={row.id} className="space-y-2">
                    <InterviewRow row={row} primaryLabel="View Results" showResult primaryAction="results" />
                    <div className="flex justify-end">
                      <Button onClick={() => navigate(`/candidate/interviews/feedback?interview=${row.id}`)}>
                        Give Feedback
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Quick Actions"
            icon={PlayCircle}
            subtitle="Jump straight into your next actionable interview."
          >
            {quickActionTarget ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-sm font-semibold text-slate-900">{getInterviewTitle(quickActionTarget)}</div>
                <div className="mt-2 text-sm text-slate-500">
                  {quickActionTarget.scheduled_at
                    ? dayjs(quickActionTarget.scheduled_at).format('DD MMM YYYY · hh:mm A')
                    : 'Schedule pending'}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    type="primary"
                    onClick={() => navigate(`/candidate/interviews/${quickActionTarget.id}/runtime?access_token=${getAccessToken(quickActionTarget)}`)}
                  >
                    Join Interview
                  </Button>
                  <Button onClick={() => navigate('/candidate/interviews/preparation')}>
                    Open Preparation
                  </Button>
                  <Button onClick={() => navigate('/candidate/interviews/experience')}>
                    Open Experience
                  </Button>
                  <Button onClick={() => navigate('/candidate/interviews/help')}>
                    Open Help
                  </Button>
                  <Button onClick={() => navigate('/candidate/interviews/timeline')}>
                    Open Timeline
                  </Button>
                  <Button onClick={() => navigate('/candidate/interviews/notifications')}>
                    Open Notifications
                  </Button>
                  <Button onClick={() => navigate(`/candidate/interviews/${quickActionTarget.id}/instructions?access_token=${getAccessToken(quickActionTarget)}`)}>
                    View Details
                  </Button>
                </div>
              </div>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No quick actions right now" />
            )}
          </SectionCard>

          <SectionCard
            title="Interview Notifications"
            icon={Bell}
            subtitle="Schedule updates, reminders, and decision notifications."
          >
            {interviewNotifications.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview notifications" />
            ) : (
              <List
                itemLayout="horizontal"
                dataSource={interviewNotifications}
                renderItem={(item) => (
                  <List.Item
                    className="!px-0"
                    actions={[
                      <button
                        key="open"
                        type="button"
                        className="text-xs font-black uppercase tracking-wider text-blue-600"
                        onClick={() => {
                          if (item.link) navigate(item.link)
                        }}
                      >
                        Open
                      </button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={<span className="text-sm font-semibold text-slate-900">{item.title}</span>}
                      description={
                        <div className="space-y-1">
                          <div className="text-sm text-slate-500">{item.body}</div>
                          <div className="text-xs text-slate-400">{dayjs(item.created_at).format('DD MMM YYYY · hh:mm A')}</div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </SectionCard>

          <SectionCard
            title="Interview Status"
            icon={ChevronRight}
            subtitle="Additional visibility for interrupted or missed interviews."
          >
            <div className="space-y-3">
              <Button block onClick={() => navigate('/candidate/interviews/results')}>
                Open Results
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/feedback')}>
                Open Feedback
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/experience')}>
                Open Experience
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/preparation')}>
                Open Preparation
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/help')}>
                Open Help
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/timeline')}>
                Open Timeline
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/notifications')}>
                Open Notifications
              </Button>
              <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-widest text-slate-400">Cancelled / Missed / Expired</div>
                  <div className="mt-1 text-lg font-bold text-slate-900">{missedInterviews.length + cancelledInterviews.length}</div>
                </div>
                <Tag color={(missedInterviews.length + cancelledInterviews.length) ? 'red' : 'default'}>
                  {(missedInterviews.length + cancelledInterviews.length) ? 'Needs attention' : 'Clear'}
                </Tag>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4 text-sm text-slate-500">
                If rescheduling is enabled for an interview, use the `Reschedule` action from the interview row.
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
