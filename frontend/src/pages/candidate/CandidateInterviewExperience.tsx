import { useMemo } from 'react'
import { Alert, Button, Card, Empty, Progress, Space, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Headphones,
  MonitorSmartphone,
  PlayCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { notificationsApi } from '@/api/notifications'
import { useAuthStore } from '@/store/authStore'
import type { Notification } from '@/types'

const { Title, Text } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
  interview_round?: number
  status?: string
  metadata?: Record<string, unknown>
  candidate_runtime?: { token?: string; scheduling_token?: string }
  scheduling_link_token?: string
  scheduling_token?: string
  scheduling_link?: { token?: string; url?: string }
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function getInterviewTitle(row?: CandidateInterviewRow | null) {
  if (!row) return 'Interview'
  return row.title || interviewTypeLabel(row.interview_type)
}

function getAccessToken(row?: CandidateInterviewRow | null) {
  return row?.candidate_runtime?.token || ''
}

function getReschedulePath(row?: CandidateInterviewRow | null) {
  if (!row) return null
  const token =
    row.scheduling_link_token ||
    row.scheduling_token ||
    row.scheduling_link?.token ||
    row.candidate_runtime?.scheduling_token ||
    ''
  return token ? `/interviews/scheduling/self/${token}` : null
}

function normalizeProgressStatus(status?: string) {
  if (status === 'completed') return 'completed'
  if (status === 'in_progress') return 'in_progress'
  if (['scheduled', 'confirmed', 'rescheduled', 'awaiting_candidate'].includes(status || '')) return 'scheduled'
  if (['cancelled', 'missed', 'expired', 'blocked'].includes(status || '')) return 'cancelled'
  return 'upcoming'
}

function getStageName(row: CandidateInterviewRow) {
  const metadata = row.metadata || {}
  const direct =
    metadata.stage_name ||
    metadata.flow_stage ||
    metadata.round_name ||
    metadata.stage ||
    metadata.interview_stage
  if (typeof direct === 'string' && direct.trim()) return direct.trim()
  if (row.interview_round) return `Round ${row.interview_round}`
  return getInterviewTitle(row)
}

function statusTagColor(status: string) {
  switch (status) {
    case 'completed':
      return 'green'
    case 'in_progress':
      return 'gold'
    case 'scheduled':
      return 'blue'
    case 'cancelled':
      return 'red'
    default:
      return 'purple'
  }
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

export default function CandidateInterviewExperience() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const timezone = user?.timezone || browserTimezone
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const deviceLabel = /mobile|android|iphone|ipad/i.test(userAgent) ? 'Mobile / Tablet' : 'Desktop'
  const accessibilityReady = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_experience'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const notificationsQuery = useQuery({
    queryKey: ['candidate_interview_experience_notifications'],
    queryFn: async () => (await notificationsApi.list()).data?.data?.notifications || [],
  })

  const dashboard = interviewsQuery.data || {}
  const pending: CandidateInterviewRow[] = dashboard.pending_interviews || []
  const upcoming: CandidateInterviewRow[] = dashboard.upcoming_interviews || []
  const completed: CandidateInterviewRow[] = dashboard.completed_interviews || []
  const missed: CandidateInterviewRow[] = dashboard.missed_interviews || []

  const allRows = useMemo(
    () => [...pending, ...upcoming, ...completed, ...missed],
    [pending, upcoming, completed, missed],
  )

  const timeline = useMemo(() => {
    const deduped = Array.from(new Map(allRows.map((row) => [row.id, row])).values())
    return deduped
      .sort((a, b) => {
        const roundDiff = (a.interview_round || 0) - (b.interview_round || 0)
        if (roundDiff !== 0) return roundDiff
        return dayjs(a.scheduled_at || 0).valueOf() - dayjs(b.scheduled_at || 0).valueOf()
      })
      .map((row) => ({
        ...row,
        stageName: getStageName(row),
        progressStatus: normalizeProgressStatus(row.status),
      }))
  }, [allRows])

  const currentStage =
    timeline.find((row) => ['in_progress', 'scheduled'].includes(row.progressStatus)) || timeline[0] || null
  const nextStage =
    timeline.find((row, index) => index > timeline.findIndex((item) => item.id === currentStage?.id) && !['completed', 'cancelled'].includes(row.progressStatus)) || null

  const completedCount = timeline.filter((row) => row.progressStatus === 'completed').length
  const progressPercent = timeline.length ? Math.round((completedCount / timeline.length) * 100) : 0

  const interviewNotifications: Notification[] = notificationsQuery.data || []
  const smartReminders = useMemo(() => {
    const reminderFeed = interviewNotifications.filter((item) => {
      const haystack = `${item.title} ${item.body} ${item.type}`.toLowerCase()
      return haystack.includes('interview') || haystack.includes('schedule') || haystack.includes('reminder')
    })
    const upcomingAlerts = upcoming
      .filter((item) => item.scheduled_at && dayjs(item.scheduled_at).isAfter(dayjs()) && dayjs(item.scheduled_at).diff(dayjs(), 'day') <= 3)
      .map((item) => ({
        id: `upcoming-${item.id}`,
        title: `${getInterviewTitle(item)} is coming up`,
        body: item.scheduled_at
          ? `Scheduled for ${dayjs(item.scheduled_at).format('DD MMM YYYY · hh:mm A')}${timezone ? ` (${timezone})` : ''}`
          : 'Upcoming interview reminder',
      }))
    return [...upcomingAlerts, ...reminderFeed.slice(0, 4)]
  }, [interviewNotifications, upcoming, timezone])

  const readinessItems = [
    { label: 'Upcoming interview selected', done: Boolean(currentStage) },
    { label: 'Interview schedule confirmed', done: Boolean(currentStage?.scheduled_at) },
    { label: 'Preparation center available', done: upcoming.length > 0 || pending.length > 0 },
    { label: 'Help and support access ready', done: true },
  ]
  const readinessPercent = Math.round((readinessItems.filter((item) => item.done).length / readinessItems.length) * 100)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Experience
          </Title>
          <Text className="text-sm text-slate-500">
            One place for progress, reminders, readiness, quick actions, and interview journey context.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Progress</div>
            <div className="mt-1 text-xl font-black text-slate-900">{progressPercent}%</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Readiness</div>
            <div className="mt-1 text-xl font-black text-slate-900">{readinessPercent}%</div>
          </div>
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Interview Progress Indicator"
            icon={CheckCircle2}
            subtitle="Progress bar, stage completion, and next-step visibility."
          >
            {!timeline.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview experience data available yet" />
            ) : (
              <div className="space-y-4">
                <Progress percent={progressPercent} strokeColor="#2563eb" />
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Completed Stages</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{completedCount} / {timeline.length}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Current Stage</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{currentStage?.stageName || 'Waiting'}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Next Step</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{nextStage?.stageName || 'Stay ready'}</div>
                  </div>
                </div>
                <div className="space-y-3">
                  {timeline.slice(0, 5).map((stage) => (
                    <div key={stage.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{stage.stageName}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {getInterviewTitle(stage)} · {stage.scheduled_at ? dayjs(stage.scheduled_at).format('DD MMM YYYY · hh:mm A') : 'Date pending'}
                        </div>
                      </div>
                      <Tag color={statusTagColor(stage.progressStatus)} className="m-0">
                        {stage.progressStatus.replace(/_/g, ' ')}
                      </Tag>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Smart Reminders"
            icon={Bell}
            subtitle="Upcoming interview alerts, preparation reminders, and scheduling reminders."
          >
            {!smartReminders.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No reminders right now" />
            ) : (
              <div className="space-y-3">
                {smartReminders.map((item: any) => (
                  <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="text-sm font-semibold text-slate-900">{item.title}</div>
                    <div className="mt-1 text-sm text-slate-500">{item.body}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Experience Summary"
            icon={Sparkles}
            subtitle="Interview history, progress summary, and current stage in one view."
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">History</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{allRows.length} interview records</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Current Stage</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{currentStage?.stageName || 'Waiting'}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Upcoming</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{upcoming.length}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Completed</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{completed.length}</div>
              </div>
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Candidate Confidence Indicators"
            icon={ShieldCheck}
            subtitle="Readiness status, preparation completion, and checklist progress."
          >
            <div className="space-y-4">
              <Progress percent={readinessPercent} strokeColor="#16a34a" />
              {readinessItems.map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                  <div className="text-sm text-slate-700">{item.label}</div>
                  <Tag color={item.done ? 'green' : 'default'} className="m-0">
                    {item.done ? 'Ready' : 'Pending'}
                  </Tag>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Quick Actions"
            icon={PlayCircle}
            subtitle="Join, reschedule, view instructions, or contact support with minimal friction."
          >
            <Space direction="vertical" size={12} className="w-full">
              <Button
                block
                type="primary"
                disabled={!currentStage}
                onClick={() => {
                  if (!currentStage) return
                  navigate(`/candidate/interviews/${currentStage.id}/runtime?access_token=${getAccessToken(currentStage)}`)
                }}
              >
                Join Interview
              </Button>
              <Button
                block
                disabled={!getReschedulePath(currentStage)}
                onClick={() => {
                  const path = getReschedulePath(currentStage)
                  if (path) navigate(path)
                }}
              >
                Reschedule
              </Button>
              <Button
                block
                disabled={!currentStage}
                onClick={() => {
                  if (!currentStage) return
                  navigate(`/candidate/interviews/${currentStage.id}/instructions?access_token=${getAccessToken(currentStage)}`)
                }}
              >
                View Instructions
              </Button>
              <Button block onClick={() => navigate('/candidate/interviews/help')}>
                Contact Support
              </Button>
            </Space>
          </SectionCard>

          <SectionCard
            title="Personalization"
            icon={MonitorSmartphone}
            subtitle="Timezone awareness, device detection, and accessibility improvements."
          >
            <div className="space-y-3">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Timezone Awareness</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{timezone}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Device Detection</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{deviceLabel}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Accessibility</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {accessibilityReady ? 'Reduced motion preference detected' : 'Standard motion preference'}
                </div>
              </div>
              <Alert
                type="info"
                showIcon
                message="Unified Experience Layer"
                description="This page connects your interview timeline, preparation, reminders, and support tools into one candidate-friendly surface."
              />
            </div>
          </SectionCard>

          <SectionCard
            title="Linked Centers"
            icon={Headphones}
            subtitle="Jump directly into related candidate interview tools."
          >
            <Space direction="vertical" size={12} className="w-full">
              <Button block onClick={() => navigate('/candidate/interviews/preparation')}>Open Preparation Center</Button>
              <Button block onClick={() => navigate('/candidate/interviews/timeline')}>Open Timeline</Button>
              <Button block onClick={() => navigate('/candidate/interviews/notifications')}>Open Notifications</Button>
              <Button block onClick={() => navigate('/candidate/interviews/help')}>Open Help Center</Button>
            </Space>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
