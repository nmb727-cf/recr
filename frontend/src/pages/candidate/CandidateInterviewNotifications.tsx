import { useMemo } from 'react'
import { Button, Card, Empty, List, Space, Tag, Typography, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  CalendarDays,
  CheckCircle2,
  Clock3,
  ExternalLink,
  History,
  PlayCircle,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { notificationsApi } from '@/api/notifications'
import type { Notification } from '@/types'

const { Title, Text } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
  status?: string
  candidate_runtime?: { token?: string; scheduling_token?: string }
  scheduling_link_token?: string
  scheduling_token?: string
  scheduling_link?: { token?: string; url?: string }
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
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

function classifyNotification(item: Notification) {
  const haystack = `${item.title} ${item.body} ${item.type}`.toLowerCase()
  if (haystack.includes('starting soon') || haystack.includes('reminder')) return 'reminder'
  if (haystack.includes('rescheduled') || haystack.includes('scheduled') || haystack.includes('invitation') || haystack.includes('cancel')) return 'update'
  if (haystack.includes('decision') || haystack.includes('next round') || haystack.includes('completed')) return 'result'
  return 'history'
}

function findInterviewForNotification(item: Notification, interviews: CandidateInterviewRow[]) {
  const haystack = `${item.title} ${item.body} ${item.link}`.toLowerCase()
  return interviews.find((row) => {
    const title = getInterviewTitle(row).toLowerCase()
    const type = interviewTypeLabel(row.interview_type).toLowerCase()
    return haystack.includes(row.id.toLowerCase()) || haystack.includes(title) || haystack.includes(type)
  })
}

function NotificationCard({
  item,
  interview,
  onOpen,
  onConfirm,
  onReschedule,
  onViewInterview,
}: {
  item: Notification
  interview?: CandidateInterviewRow
  onOpen: () => void
  onConfirm: () => void
  onReschedule: () => void
  onViewInterview: () => void
}) {
  const kind = classifyNotification(item)

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-slate-900">{item.title}</div>
            <Tag color={item.is_read ? 'default' : 'blue'}>{item.is_read ? 'Read' : 'New'}</Tag>
            <Tag>{kind}</Tag>
            <Tag color="purple">In-app</Tag>
            <Tag>email ready</Tag>
            <Tag>sms ready</Tag>
            <Tag>push ready</Tag>
          </div>
          <div className="mt-2 text-sm text-slate-500">{item.body}</div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span>{dayjs(item.created_at).format('DD MMM YYYY · hh:mm A')}</span>
            {interview ? (
              <>
                <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600">
                  {getInterviewTitle(interview)}
                </span>
                <span>{interview.scheduled_at ? dayjs(interview.scheduled_at).format('DD MMM · hh:mm A') : 'Schedule pending'}</span>
              </>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button onClick={onOpen}>Open</Button>
          {interview ? (
            <>
              <Button type="primary" icon={<PlayCircle className="h-4 w-4" />} onClick={onViewInterview}>
                Join Interview
              </Button>
              <Button onClick={onConfirm}>Confirm Schedule</Button>
              <Button icon={<ExternalLink className="h-4 w-4" />} disabled={!getReschedulePath(interview)} onClick={onReschedule}>
                Reschedule Request
              </Button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function SectionCard({
  title,
  icon: Icon,
  subtitle,
  children,
}: {
  title: string
  icon: React.ElementType
  subtitle: string
  children: React.ReactNode
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

export default function CandidateInterviewNotifications() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_notifications_dashboard'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const notificationsQuery = useQuery({
    queryKey: ['candidate_interview_notification_feed'],
    queryFn: async () => (await notificationsApi.list()).data?.data?.notifications || [],
  })

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => notificationsApi.markRead(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate_interview_notification_feed'] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: async () => notificationsApi.markAllRead(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate_interview_notification_feed'] })
      message.success('All interview notifications marked as read')
    },
  })

  const dashboard = interviewsQuery.data || {}
  const upcomingInterviews: CandidateInterviewRow[] = dashboard.upcoming_interviews || []
  const pendingInterviews: CandidateInterviewRow[] = dashboard.pending_interviews || []
  const completedInterviews: CandidateInterviewRow[] = dashboard.completed_interviews || []
  const allInterviews = [...upcomingInterviews, ...pendingInterviews, ...completedInterviews]

  const interviewNotifications = useMemo(() => {
    const items: Notification[] = notificationsQuery.data || []
    return items.filter((item) => {
      const haystack = `${item.title} ${item.body} ${item.type}`.toLowerCase()
      return haystack.includes('interview') || haystack.includes('schedule') || haystack.includes('decision') || haystack.includes('round')
    })
  }, [notificationsQuery.data])

  const reminders = useMemo(() => {
    const notifReminders = interviewNotifications.filter((item) => classifyNotification(item) === 'reminder')
    const upcomingReminders = upcomingInterviews
      .filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isAfter(dayjs()) && dayjs(item.scheduled_at).diff(dayjs(), 'hour') <= 24)
      .map((item) => ({
        id: `upcoming-${item.id}`,
        recipient_id: '',
        title: `${getInterviewTitle(item)} starting soon`,
        body: item.scheduled_at
          ? `Reminder for your ${interviewTypeLabel(item.interview_type)} on ${dayjs(item.scheduled_at).format('DD MMM YYYY · hh:mm A')}.`
          : 'Upcoming interview reminder.',
        type: 'interview_starting_soon',
        link: `/candidate/interviews/${item.id}/runtime?access_token=${getAccessToken(item)}`,
        is_read: false,
        created_at: item.scheduled_at || dayjs().toISOString(),
        interview: item,
      }))
    return [...notifReminders.map((item) => ({ ...item, interview: findInterviewForNotification(item, allInterviews) })), ...upcomingReminders].slice(0, 8)
  }, [interviewNotifications, upcomingInterviews, allInterviews])

  const updates = useMemo(
    () =>
      interviewNotifications
        .filter((item) => ['update', 'result'].includes(classifyNotification(item)))
        .map((item) => ({ ...item, interview: findInterviewForNotification(item, allInterviews) }))
        .slice(0, 8),
    [interviewNotifications, allInterviews],
  )

  const history = useMemo(
    () =>
      interviewNotifications
        .map((item) => ({ ...item, interview: findInterviewForNotification(item, allInterviews) }))
        .sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
    [interviewNotifications, allInterviews],
  )

  const unreadCount = interviewNotifications.filter((item) => !item.is_read).length

  const handleOpen = async (item: Notification) => {
    if (!item.is_read && !String(item.id).startsWith('upcoming-')) {
      await markReadMutation.mutateAsync(item.id)
    }
    if (item.link) navigate(item.link)
  }

  const handleConfirm = async (item: Notification) => {
    if (!String(item.id).startsWith('upcoming-') && !item.is_read) {
      await markReadMutation.mutateAsync(item.id)
    }
    message.success('Schedule confirmed')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Notifications
          </Title>
          <Text className="text-sm text-slate-500">
            Track interview reminders, schedule changes, invitations, and decision updates in one place.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Unread</div>
            <div className="mt-1 text-xl font-black text-slate-900">{unreadCount}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Upcoming Reminders</div>
            <div className="mt-1 text-xl font-black text-slate-900">{reminders.length}</div>
          </div>
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
          <Button type="primary" loading={markAllReadMutation.isPending} onClick={() => markAllReadMutation.mutate()}>
            Mark All Read
          </Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Upcoming Reminders"
            icon={Clock3}
            subtitle="Upcoming interviews, reminder timing, and quick join access."
          >
            {!reminders.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No upcoming reminders" />
            ) : (
              <div className="space-y-3">
                {reminders.map((item: any) => (
                  <NotificationCard
                    key={item.id}
                    item={item}
                    interview={item.interview}
                    onOpen={() => void handleOpen(item)}
                    onConfirm={() => void handleConfirm(item)}
                    onReschedule={() => {
                      const path = item.interview ? getReschedulePath(item.interview) : null
                      if (path) navigate(path)
                    }}
                    onViewInterview={() => {
                      if (!item.interview) return
                      navigate(`/candidate/interviews/${item.interview.id}/runtime?access_token=${getAccessToken(item.interview)}`)
                    }}
                  />
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Updates"
            icon={Bell}
            subtitle="Reschedule updates, new invitations, cancellations, and next round notifications."
          >
            {!updates.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview updates" />
            ) : (
              <div className="space-y-3">
                {updates.map((item: any) => (
                  <NotificationCard
                    key={item.id}
                    item={item}
                    interview={item.interview}
                    onOpen={() => void handleOpen(item)}
                    onConfirm={() => void handleConfirm(item)}
                    onReschedule={() => {
                      const path = item.interview ? getReschedulePath(item.interview) : null
                      if (path) navigate(path)
                    }}
                    onViewInterview={() => {
                      if (!item.interview) return
                      navigate(`/candidate/interviews/${item.interview.id}/instructions?access_token=${getAccessToken(item.interview)}`)
                    }}
                  />
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="History"
            icon={History}
            subtitle="Complete interview-related notification history and alert trail."
          >
            {!history.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview notification history" />
            ) : (
              <List
                dataSource={history}
                renderItem={(item: any) => (
                  <List.Item
                    className="!px-0"
                    actions={[
                      <Button key="open" type="link" onClick={() => void handleOpen(item)}>
                        Open
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-slate-900">{item.title}</span>
                          <Tag color={item.is_read ? 'default' : 'blue'}>{item.is_read ? 'Read' : 'New'}</Tag>
                        </div>
                      }
                      description={
                        <Space direction="vertical" size={2}>
                          <Text className="text-sm text-slate-600">{item.body}</Text>
                          <Text className="text-xs text-slate-400">{dayjs(item.created_at).format('DD MMM YYYY · hh:mm A')}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Candidate Actions"
            icon={PlayCircle}
            subtitle="Quick actions for interview joins, schedule confirmation, and reschedule requests."
          >
            <div className="grid gap-3">
              <Button type="primary" onClick={() => navigate('/candidate/interviews')}>
                Open Interview Dashboard
              </Button>
              <Button onClick={() => navigate('/candidate/interviews/results')}>
                Open Results
              </Button>
              <Button onClick={() => navigate('/candidate/interviews')}>
                View Interview
              </Button>
            </div>
          </SectionCard>

          <SectionCard
            title="Notification Channels"
            icon={CalendarDays}
            subtitle="Current and future-ready notification delivery channels."
          >
            <div className="space-y-3">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">In-app Notification</div>
                <div className="mt-1 text-sm text-slate-500">Live now for interview reminders, updates, and decisions.</div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">Email</div>
                <div className="mt-1 text-sm text-slate-500">Future-ready channel for mirrored interview alerts.</div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">SMS</div>
                <div className="mt-1 text-sm text-slate-500">Future-ready channel for urgent reminders and confirmations.</div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">Push Notification</div>
                <div className="mt-1 text-sm text-slate-500">Future-ready channel for real-time interview alerts.</div>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Status Summary"
            icon={CheckCircle2}
            subtitle="Interview notification and reminder visibility."
          >
            <Space direction="vertical" size={8} className="w-full">
              <Text className="text-sm text-slate-600">Total notifications: <span className="font-semibold text-slate-900">{history.length}</span></Text>
              <Text className="text-sm text-slate-600">Unread interview notifications: <span className="font-semibold text-slate-900">{unreadCount}</span></Text>
              <Text className="text-sm text-slate-600">Upcoming interview reminders: <span className="font-semibold text-slate-900">{reminders.length}</span></Text>
              <Text className="text-sm text-slate-600">Update alerts: <span className="font-semibold text-slate-900">{updates.length}</span></Text>
            </Space>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
