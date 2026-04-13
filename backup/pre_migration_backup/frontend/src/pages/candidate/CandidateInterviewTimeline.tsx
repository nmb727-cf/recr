import { useMemo } from 'react'
import { Button, Card, Empty, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock3,
  PlayCircle,
  Route,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'

const { Title, Text } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
  interview_round?: number
  status?: string
  result?: string
  decision?: { decision?: string }
  metadata?: Record<string, unknown>
  candidate_runtime?: { token?: string; scheduling_token?: string }
  scheduling_link_token?: string
  scheduling_token?: string
  scheduling_link?: { token?: string; url?: string }
}

type TimelineStage = CandidateInterviewRow & {
  stageName: string
  stageStatus: 'completed' | 'scheduled' | 'upcoming' | 'in_progress' | 'skipped' | 'cancelled'
  isCurrent: boolean
  isNext: boolean
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function getInterviewTitle(row: CandidateInterviewRow) {
  return row.title || interviewTypeLabel(row.interview_type)
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

function normalizeTimelineStatus(row: CandidateInterviewRow): TimelineStage['stageStatus'] {
  if (row.status === 'completed') return 'completed'
  if (row.status === 'in_progress') return 'in_progress'
  if (['cancelled', 'missed', 'expired', 'blocked', 'rejected'].includes(row.status || '')) return 'cancelled'
  if (row.status === 'skipped') return 'skipped'
  if (['scheduled', 'confirmed', 'rescheduled'].includes(row.status || '')) {
    if (row.scheduled_at && dayjs(row.scheduled_at).isAfter(dayjs())) return 'scheduled'
    return 'upcoming'
  }
  if (row.scheduled_at && dayjs(row.scheduled_at).isAfter(dayjs())) return 'upcoming'
  return 'upcoming'
}

function statusTagColor(status: TimelineStage['stageStatus']) {
  switch (status) {
    case 'completed':
      return 'green'
    case 'in_progress':
      return 'gold'
    case 'scheduled':
      return 'blue'
    case 'upcoming':
      return 'purple'
    case 'skipped':
      return 'default'
    case 'cancelled':
      return 'red'
    default:
      return 'default'
  }
}

function prettyStatus(status: TimelineStage['stageStatus']) {
  return status.replace(/_/g, ' ')
}

export default function CandidateInterviewTimeline() {
  const navigate = useNavigate()

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_timeline'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const dashboard = interviewsQuery.data || {}
  const allRows: CandidateInterviewRow[] = [
    ...(dashboard.pending_interviews || []),
    ...(dashboard.upcoming_interviews || []),
    ...(dashboard.completed_interviews || []),
    ...(dashboard.missed_interviews || []),
  ]

  const timeline = useMemo(() => {
    const deduped = Array.from(new Map(allRows.map((row) => [row.id, row])).values())
    const sorted = deduped.sort((a, b) => {
      const roundDiff = (a.interview_round || 0) - (b.interview_round || 0)
      if (roundDiff !== 0) return roundDiff
      return dayjs(a.scheduled_at || a.id).valueOf() - dayjs(b.scheduled_at || b.id).valueOf()
    })

    const currentIndex = sorted.findIndex((row) => ['in_progress', 'scheduled', 'confirmed', 'rescheduled', 'awaiting_candidate'].includes(row.status || ''))
    const nextIndex =
      currentIndex >= 0
        ? sorted.findIndex((row, index) => index > currentIndex && !['completed', 'cancelled', 'missed', 'expired', 'blocked'].includes(row.status || ''))
        : sorted.findIndex((row) => !['completed', 'cancelled', 'missed', 'expired', 'blocked'].includes(row.status || ''))

    return sorted.map((row, index) => ({
      ...row,
      stageName: getStageName(row),
      stageStatus: normalizeTimelineStatus(row),
      isCurrent: index === currentIndex,
      isNext: index === nextIndex && index !== currentIndex,
    }))
  }, [allRows])

  const currentStage = timeline.find((item) => item.isCurrent) || null
  const nextStage = timeline.find((item) => item.isNext) || null

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Timeline
          </Title>
          <Text className="text-sm text-slate-500">
            View your full interview journey, current stage, upcoming rounds, stage details, and next actions.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Stages</div>
            <div className="mt-1 text-xl font-black text-slate-900">{timeline.length}</div>
          </div>
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <div className="mb-4 flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                <Route className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">Journey Timeline</div>
                <div className="mt-1 text-sm text-slate-500">Application submitted through final interview stages.</div>
              </div>
            </div>

            {!timeline.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview timeline available yet" />
            ) : (
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span>Application Submitted</span>
                    <Tag color="green" className="m-0">completed</Tag>
                  </div>
                </div>

                {timeline.map((stage, index) => (
                  <div key={stage.id} className="flex gap-4">
                    <div className="flex w-10 flex-col items-center">
                      <div
                        className={[
                          'flex h-10 w-10 items-center justify-center rounded-full border-2 text-xs font-black uppercase',
                          stage.isCurrent
                            ? 'border-blue-600 bg-blue-600 text-white'
                            : stage.isNext
                              ? 'border-purple-500 bg-purple-50 text-purple-600'
                              : stage.stageStatus === 'completed'
                                ? 'border-green-600 bg-green-50 text-green-700'
                                : 'border-slate-300 bg-white text-slate-500',
                        ].join(' ')}
                      >
                        {index + 1}
                      </div>
                      {index < timeline.length - 1 ? <div className="mt-2 h-full w-px bg-slate-200" /> : null}
                    </div>

                    <div className="flex-1 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <div className="text-sm font-semibold text-slate-900">{stage.stageName}</div>
                            <Tag color={statusTagColor(stage.stageStatus)} className="m-0">
                              {prettyStatus(stage.stageStatus)}
                            </Tag>
                            {stage.isCurrent ? <Tag color="blue" className="m-0">Current Stage</Tag> : null}
                            {stage.isNext ? <Tag color="purple" className="m-0">Next Stage</Tag> : null}
                          </div>
                          <div className="mt-2 text-sm text-slate-600">{getInterviewTitle(stage)}</div>
                          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <CalendarDays className="h-3.5 w-3.5" />
                              {stage.scheduled_at ? dayjs(stage.scheduled_at).format('DD MMM YYYY') : 'Date pending'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock3 className="h-3.5 w-3.5" />
                              {stage.scheduled_at ? dayjs(stage.scheduled_at).format('hh:mm A') : 'Time pending'}
                              {stage.duration_minutes ? ` · ${stage.duration_minutes} min` : ''}
                            </span>
                            <span>{interviewTypeLabel(stage.interview_type)}</span>
                          </div>
                          <div className="mt-3 text-sm text-slate-500">
                            Result: {stage.result || stage.decision?.decision || 'Pending release'}
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Button onClick={() => navigate(`/candidate/interviews/${stage.id}/instructions?access_token=${getAccessToken(stage)}`)}>
                            View Stage Details
                          </Button>
                          <Button
                            type="primary"
                            icon={<PlayCircle className="h-4 w-4" />}
                            disabled={!['in_progress', 'scheduled', 'confirmed', 'rescheduled', 'awaiting_candidate'].includes(stage.status || '')}
                            onClick={() => navigate(`/candidate/interviews/${stage.id}/runtime?access_token=${getAccessToken(stage)}`)}
                          >
                            Join Interview
                          </Button>
                          <Button
                            disabled={!getReschedulePath(stage)}
                            onClick={() => {
                              const path = getReschedulePath(stage)
                              if (path) navigate(path)
                            }}
                          >
                            Schedule Interview
                          </Button>
                          <Button onClick={() => navigate(`/candidate/interviews/results?interview=${stage.id}`)}>
                            View Results
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <div className="mb-4 flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                <ChevronRight className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">Current Progress</div>
                <div className="mt-1 text-sm text-slate-500">Current stage and next stage summary.</div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Current Stage</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {currentStage ? currentStage.stageName : 'No current stage'}
                </div>
                <div className="mt-1 text-sm text-slate-500">
                  {currentStage ? getInterviewTitle(currentStage) : 'Waiting for next interview stage'}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Next Stage</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {nextStage ? nextStage.stageName : 'No next stage yet'}
                </div>
                <div className="mt-1 text-sm text-slate-500">
                  {nextStage ? getInterviewTitle(nextStage) : 'This is currently the last visible stage'}
                </div>
              </div>
            </div>
          </Card>

          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <div className="mb-4 flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                <CalendarDays className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">Stage Status Guide</div>
                <div className="mt-1 text-sm text-slate-500">Supported timeline states for your interview journey.</div>
              </div>
            </div>

            <div className="space-y-3">
              {['completed', 'scheduled', 'upcoming', 'in progress', 'skipped', 'cancelled'].map((label) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                  <div className="text-sm font-semibold capitalize text-slate-900">{label}</div>
                  <Tag className="m-0">{label}</Tag>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
