import { useMemo, useState } from 'react'
import { Alert, Button, Card, Empty, List, Progress, Tag, Typography, message } from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  Link2,
  Mic,
  MonitorSmartphone,
  PlayCircle,
  Video,
  Wifi,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'

const { Title, Text, Paragraph } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
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

function getPreparationTips(type?: string) {
  const label = interviewTypeLabel(type).toLowerCase()
  if (label.includes('technical')) {
    return ['Review core concepts and recent project work', 'Prepare concise problem-solving explanations', 'Keep a stable device and quiet environment ready']
  }
  if (label.includes('ai') || label.includes('async')) {
    return ['Practice concise responses aloud', 'Check camera, mic, and response timing', 'Prepare examples with clear structure']
  }
  if (label.includes('hr') || label.includes('behavioral') || label.includes('leadership')) {
    return ['Prepare situation-based examples', 'Review role motivation and achievements', 'Keep answers structured and specific']
  }
  return ['Review the role and job expectations', 'Prepare key examples and talking points', 'Check device, network, and surroundings in advance']
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

export default function CandidateInterviewPreparation() {
  const navigate = useNavigate()
  const [selectedInterviewId, setSelectedInterviewId] = useState('')
  const [checks, setChecks] = useState({
    mic: false,
    camera: false,
    internet: false,
    device: false,
  })

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_preparation_dashboard'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const dashboard = interviewsQuery.data || {}
  const upcomingInterviews: CandidateInterviewRow[] = [
    ...(dashboard.upcoming_interviews || []),
    ...(dashboard.pending_interviews || []),
  ]
    .filter((item: CandidateInterviewRow) => !['completed', 'cancelled', 'missed', 'expired', 'blocked'].includes(item.status || ''))
    .sort((a: CandidateInterviewRow, b: CandidateInterviewRow) => dayjs(a.scheduled_at || 0).valueOf() - dayjs(b.scheduled_at || 0).valueOf())

  const activeInterview = useMemo(() => {
    if (!upcomingInterviews.length) return null
    if (!selectedInterviewId) return upcomingInterviews[0]
    return upcomingInterviews.find((item) => item.id === selectedInterviewId) || upcomingInterviews[0]
  }, [upcomingInterviews, selectedInterviewId])

  const instructionsQuery = useQuery({
    queryKey: ['candidate_interview_preparation_instructions', activeInterview?.id],
    enabled: Boolean(activeInterview?.id),
    queryFn: async () => (await interviewsApi.candidateInstructions(activeInterview?.id || '')).data?.data || {},
  })

  const instructionsPayload = instructionsQuery.data || {}
  const runtime = instructionsPayload.runtime || {}
  const instructionText =
    instructionsPayload.instructions ||
    activeInterview?.metadata?.candidate_instructions ||
    'Please review interview expectations, complete your device checks, and be ready before the access window opens.'

  const sampleQuestions = Array.isArray(activeInterview?.metadata?.sample_questions)
    ? (activeInterview?.metadata?.sample_questions as string[])
    : []
  const materials = Array.isArray(activeInterview?.metadata?.preparation_materials)
    ? (activeInterview?.metadata?.preparation_materials as Array<{ title?: string; type?: string; url?: string }>)
    : []

  const checklistItems = [
    { key: 'job_review', label: 'Reviewed role, company, and interview format', done: Boolean(activeInterview) },
    { key: 'schedule_confirm', label: 'Confirmed interview time and timezone', done: Boolean(activeInterview?.scheduled_at) },
    { key: 'guidelines', label: 'Read interview instructions and requirements', done: Boolean(instructionText) },
    { key: 'system', label: 'Completed system checks', done: Object.values(checks).every(Boolean) },
  ]

  const readinessPercent = Math.round((checklistItems.filter((item) => item.done).length / checklistItems.length) * 100)

  const toggleCheck = (key: keyof typeof checks, label: string) => {
    setChecks((prev) => {
      const next = { ...prev, [key]: !prev[key] }
      message.success(`${label} ${next[key] ? 'marked ready' : 'marked pending'}`)
      return next
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Preparation
          </Title>
          <Text className="text-sm text-slate-500">
            Prepare for upcoming interviews with guidelines, materials, readiness checks, and a candidate checklist.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Upcoming</div>
            <div className="mt-1 text-xl font-black text-slate-900">{upcomingInterviews.length}</div>
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
            title="Upcoming Interview Preparation"
            icon={CalendarDays}
            subtitle="Upcoming interview details and practical preparation tips."
          >
            {!upcomingInterviews.length ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No upcoming interviews to prepare for" />
            ) : (
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {upcomingInterviews.map((item) => (
                    <Button
                      key={item.id}
                      type={activeInterview?.id === item.id ? 'primary' : 'default'}
                      onClick={() => setSelectedInterviewId(item.id)}
                    >
                      {getInterviewTitle(item)}
                    </Button>
                  ))}
                </div>

                {activeInterview ? (
                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <div className="text-sm font-semibold text-slate-900">{getInterviewTitle(activeInterview)}</div>
                          <Tag>{interviewTypeLabel(activeInterview.interview_type)}</Tag>
                        </div>
                        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <CalendarDays className="h-3.5 w-3.5" />
                            {activeInterview.scheduled_at ? dayjs(activeInterview.scheduled_at).format('DD MMM YYYY') : 'Date pending'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock3 className="h-3.5 w-3.5" />
                            {activeInterview.scheduled_at ? dayjs(activeInterview.scheduled_at).format('hh:mm A') : 'Time pending'}
                            {activeInterview.duration_minutes ? ` · ${activeInterview.duration_minutes} min` : ''}
                          </span>
                        </div>
                        <div className="mt-4 space-y-2">
                          {getPreparationTips(activeInterview.interview_type).map((tip) => (
                            <div key={tip} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                              {tip}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="primary"
                          icon={<PlayCircle className="h-4 w-4" />}
                          onClick={() => navigate(`/candidate/interviews/${activeInterview.id}/runtime?access_token=${getAccessToken(activeInterview)}`)}
                        >
                          Join Interview
                        </Button>
                        <Button onClick={() => navigate(`/candidate/interviews/${activeInterview.id}/instructions?access_token=${getAccessToken(activeInterview)}`)}>
                          View Details
                        </Button>
                        <Button
                          disabled={!getReschedulePath(activeInterview)}
                          onClick={() => {
                            const path = getReschedulePath(activeInterview)
                            if (path) navigate(path)
                          }}
                        >
                          Schedule
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Interview Guidelines"
            icon={FileText}
            subtitle="Instructions, requirements, interview format, and expected duration."
          >
            {!activeInterview ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview selected" />
            ) : (
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-white p-5">
                  <Paragraph className="!mb-0 text-sm text-slate-600">{instructionText}</Paragraph>
                </div>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interview Format</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{interviewTypeLabel(activeInterview.interview_type)}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Expected Duration</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{activeInterview.duration_minutes || 60} minutes</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Single Attempt</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{runtime.single_attempt ? 'Enabled' : 'Flexible'}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Access Window</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">
                      {runtime.not_before && runtime.expires_at
                        ? `${dayjs(runtime.not_before).format('DD MMM hh:mm A')} - ${dayjs(runtime.expires_at).format('DD MMM hh:mm A')}`
                        : 'Visible on interview day'}
                    </div>
                  </div>
                </div>
                <Alert
                  type="info"
                  showIcon
                  message="Preparation Guidance"
                  description="Review the format, confirm your access window, and complete system checks before the interview starts."
                />
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Preparation Materials"
            icon={Link2}
            subtitle="Documents, links, future-ready videos, and sample questions."
          >
            {!activeInterview ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No preparation materials available yet" />
            ) : (
              <div className="space-y-4">
                {materials.length ? (
                  <List
                    dataSource={materials}
                    renderItem={(item) => (
                      <List.Item
                        actions={
                          item.url
                            ? [
                                <Button key="open" type="link" href={item.url} target="_blank" rel="noreferrer">
                                  Open
                                </Button>,
                              ]
                            : undefined
                        }
                      >
                        <List.Item.Meta
                          title={<span className="text-sm font-semibold text-slate-900">{item.title || 'Preparation Material'}</span>}
                          description={<span className="text-sm text-slate-500">{item.type || 'Document / link'}</span>}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                    No attached documents or links yet for this interview.
                  </div>
                )}

                {sampleQuestions.length ? (
                  <div className="space-y-3">
                    <div className="text-sm font-semibold text-slate-900">Sample Questions</div>
                    {sampleQuestions.map((question) => (
                      <div key={question} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                        {question}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
                    Sample questions will appear here when attached to the interview template.
                  </div>
                )}

                <div className="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
                  Video preparation material support is future ready and can be surfaced here when enabled.
                </div>
              </div>
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="System Check"
            icon={MonitorSmartphone}
            subtitle="Candidate-side device readiness checks before the interview starts."
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center gap-3">
                  <Mic className="h-4 w-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Mic Check</div>
                    <div className="text-xs text-slate-500">Confirm microphone access and voice clarity.</div>
                  </div>
                </div>
                <Button type={checks.mic ? 'primary' : 'default'} onClick={() => toggleCheck('mic', 'Mic check')}>
                  {checks.mic ? 'Ready' : 'Run Check'}
                </Button>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center gap-3">
                  <Video className="h-4 w-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Camera Check</div>
                    <div className="text-xs text-slate-500">Confirm camera access, framing, and lighting.</div>
                  </div>
                </div>
                <Button type={checks.camera ? 'primary' : 'default'} onClick={() => toggleCheck('camera', 'Camera check')}>
                  {checks.camera ? 'Ready' : 'Run Check'}
                </Button>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center gap-3">
                  <Wifi className="h-4 w-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Internet Check</div>
                    <div className="text-xs text-slate-500">Confirm stable network connectivity for the interview.</div>
                  </div>
                </div>
                <Button type={checks.internet ? 'primary' : 'default'} onClick={() => toggleCheck('internet', 'Internet check')}>
                  {checks.internet ? 'Ready' : 'Run Check'}
                </Button>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center gap-3">
                  <MonitorSmartphone className="h-4 w-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Device Check</div>
                    <div className="text-xs text-slate-500">Confirm browser, battery, and device readiness.</div>
                  </div>
                </div>
                <Button type={checks.device ? 'primary' : 'default'} onClick={() => toggleCheck('device', 'Device check')}>
                  {checks.device ? 'Ready' : 'Run Check'}
                </Button>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Candidate Checklist"
            icon={CheckCircle2}
            subtitle="Preparation checklist and readiness indicator for the selected interview."
          >
            <div className="space-y-4">
              <Progress percent={readinessPercent} strokeColor="#2563eb" />
              <div className="space-y-3">
                {checklistItems.map((item) => (
                  <div key={item.key} className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                    <div className="text-sm text-slate-700">{item.label}</div>
                    <Tag color={item.done ? 'green' : 'default'} className="m-0">
                      {item.done ? 'Ready' : 'Pending'}
                    </Tag>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
