import { useMemo } from 'react'
import {
  Button,
  Card,
  Empty,
  List,
  Skeleton,
  Tag,
  Timeline,
  Typography,
} from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  CheckCircle2,
  ChevronRight,
  Clock3,
  ListChecks,
  MessageSquareQuote,
  Route,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'

const { Title, Text, Paragraph } = Typography

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  updated_at?: string
  created_at?: string
  duration_minutes?: number
  status?: string
  result?: string
  decision?: { decision?: string }
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function statusColor(status?: string) {
  switch (status) {
    case 'completed':
      return 'green'
    case 'shortlisted':
      return 'blue'
    case 'rejected':
      return 'red'
    case 'next_round':
      return 'purple'
    case 'pending':
      return 'gold'
    default:
      return 'default'
  }
}

function normalizeResult(status?: string, decision?: string) {
  const value = (decision || status || '').toLowerCase()
  if (value.includes('shortlist') || value.includes('recommend')) return 'shortlisted'
  if (value.includes('reject') || value.includes('no_hire')) return 'rejected'
  if (value.includes('next') || value.includes('advance') || value.includes('pass')) return 'next_round'
  if (value.includes('complete')) return 'completed'
  return 'pending'
}

function resultLabel(result: string) {
  switch (result) {
    case 'shortlisted':
      return 'Shortlisted'
    case 'rejected':
      return 'Rejected'
    case 'next_round':
      return 'Next Round'
    case 'completed':
      return 'Completed'
    default:
      return 'Pending'
  }
}

export default function CandidateInterviewResults() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_results_list'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const dashboard = interviewsQuery.data || {}
  const allInterviews: CandidateInterviewRow[] = dashboard.interviews || []
  const completedInterviews: CandidateInterviewRow[] = dashboard.completed_interviews || []
  const upcomingInterviews: CandidateInterviewRow[] = dashboard.upcoming_interviews || []

  const selectedInterviewId =
    searchParams.get('interview') ||
    completedInterviews[0]?.id ||
    allInterviews[0]?.id ||
    ''

  const statusQuery = useQuery({
    queryKey: ['candidate_interview_result_detail', selectedInterviewId],
    enabled: Boolean(selectedInterviewId),
    queryFn: async () => (await interviewsApi.candidateResults({ interview_id: selectedInterviewId })).data?.data || {},
  })

  const selectedRow =
    allInterviews.find((item) => item.id === selectedInterviewId) ||
    completedInterviews.find((item) => item.id === selectedInterviewId) ||
    null

  const detail = statusQuery.data || {}
  const normalizedResult = normalizeResult(detail.status, detail.interview?.decision?.decision || selectedRow?.decision?.decision)
  const nextInterview = useMemo(
    () =>
      upcomingInterviews
        .filter((row) => !selectedRow || row.id !== selectedRow.id)
        .sort((a, b) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf())[0] || null,
    [upcomingInterviews, selectedRow],
  )

  const historyItems = useMemo(
    () =>
      [...allInterviews]
        .sort((a, b) => dayjs(b.scheduled_at || b.updated_at || b.created_at).valueOf() - dayjs(a.scheduled_at || a.updated_at || a.created_at).valueOf())
        .slice(0, 8),
    [allInterviews],
  )

  const feedbackSummary =
    detail.feedback_summary ||
    (detail.scores?.overall_score != null ? `Overall score recorded: ${detail.scores.overall_score}` : '')

  const improvementSuggestions =
    detail.decision?.metadata?.candidate_feedback ||
    detail.decision?.metadata?.improvement_suggestions ||
    ''

  return (
    <div className="space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Title level={3} className="!mb-1 !mt-0">
              Interview Results
            </Title>
          <Text className="text-sm text-slate-500">
            Review completed interviews, visible results, next steps, and available feedback.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/candidate/interviews/feedback' + (selectedInterviewId ? `?interview=${selectedInterviewId}` : ''))}>
            Open Feedback
          </Button>
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="rounded-3xl border-slate-200">
          <div className="mb-4 flex items-center gap-3">
            <ListChecks className="h-5 w-5 text-blue-600" />
            <div>
              <div className="text-sm font-black uppercase tracking-wider text-slate-900">Completed Interviews</div>
              <div className="text-sm text-slate-500">Select an interview to view result details and history.</div>
            </div>
          </div>

          {interviewsQuery.isLoading ? (
            <Skeleton active paragraph={{ rows: 6 }} />
          ) : completedInterviews.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No completed interviews yet" />
          ) : (
            <div className="space-y-3">
              {completedInterviews.map((row) => {
                const result = normalizeResult(row.status, row.decision?.decision)
                const isActive = row.id === selectedInterviewId
                return (
                  <button
                    key={row.id}
                    type="button"
                    onClick={() => setSearchParams({ interview: row.id })}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      isActive ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-900">{row.title || interviewTypeLabel(row.interview_type)}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {interviewTypeLabel(row.interview_type)} · {row.scheduled_at ? dayjs(row.scheduled_at).format('DD MMM YYYY') : 'Date pending'}
                        </div>
                      </div>
                      <Tag color={statusColor(result)} className="m-0">
                        {resultLabel(result)}
                      </Tag>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </Card>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200">
            {statusQuery.isLoading ? (
              <Skeleton active paragraph={{ rows: 8 }} />
            ) : !selectedInterviewId ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a completed interview" />
            ) : (
              <div className="space-y-5">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <Title level={4} className="!mb-1 !mt-0">
                      {selectedRow?.title || interviewTypeLabel(selectedRow?.interview_type)}
                    </Title>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
                      <span>{interviewTypeLabel(selectedRow?.interview_type)}</span>
                      {selectedRow?.scheduled_at ? <span>· {dayjs(selectedRow.scheduled_at).format('DD MMM YYYY')}</span> : null}
                      {selectedRow?.duration_minutes ? <span>· {selectedRow.duration_minutes} min</span> : null}
                    </div>
                  </div>
                  <Tag color={statusColor(normalizedResult)}>{resultLabel(normalizedResult)}</Tag>
                </div>

                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interview Result</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{resultLabel(normalizedResult)}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Overall Score</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{detail.scores?.overall_score ?? 'Not shared'}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Human Score</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{detail.scores?.human_score ?? 'Not shared'}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">AI Score</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{detail.scores?.ai_score ?? 'Not shared'}</div>
                  </div>
                </div>
              </div>
            )}
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card className="rounded-3xl border-slate-200">
              <div className="mb-4 flex items-center gap-3">
                <MessageSquareQuote className="h-5 w-5 text-emerald-600" />
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Feedback</div>
                  <div className="text-sm text-slate-500">Recruiter feedback and improvement suggestions appear when visible.</div>
                </div>
              </div>

              {statusQuery.isLoading ? (
                <Skeleton active paragraph={{ rows: 4 }} />
              ) : feedbackSummary || improvementSuggestions ? (
                <div className="space-y-4">
                  {feedbackSummary ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Visible Feedback</div>
                      <div className="mt-2 text-sm text-slate-700">{feedbackSummary}</div>
                    </div>
                  ) : null}
                  {improvementSuggestions ? (
                    <div className="rounded-2xl border border-slate-200 p-4">
                      <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Improvement Suggestions</div>
                      <div className="mt-2 text-sm text-slate-700">{improvementSuggestions}</div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No visible feedback shared for this interview" />
              )}
            </Card>

            <Card className="rounded-3xl border-slate-200">
              <div className="mb-4 flex items-center gap-3">
                <Route className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Next Steps</div>
                  <div className="text-sm text-slate-500">Follow-up action based on the current interview result.</div>
                </div>
              </div>

              {normalizedResult === 'next_round' && nextInterview ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-sm font-semibold text-slate-900">Next interview scheduled</div>
                  <div className="mt-2 text-sm text-slate-600">{nextInterview.title || interviewTypeLabel(nextInterview.interview_type)}</div>
                  <div className="mt-1 text-sm text-slate-500">{nextInterview.scheduled_at ? dayjs(nextInterview.scheduled_at).format('DD MMM YYYY · hh:mm A') : 'Schedule pending'}</div>
                  <Button className="mt-4" type="primary" onClick={() => navigate('/candidate/interviews')}>
                    View Interviews
                  </Button>
                </div>
              ) : normalizedResult === 'shortlisted' ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  You are shortlisted. The team may schedule your next round or share a decision update soon.
                </div>
              ) : normalizedResult === 'rejected' ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  This interview process has concluded for this role.
                </div>
              ) : normalizedResult === 'completed' ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  Interview completed. Waiting for decision.
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  Result is pending. Check back later for updates.
                </div>
              )}
            </Card>
          </div>

          <Card className="rounded-3xl border-slate-200">
            <div className="mb-4 flex items-center gap-3">
              <Clock3 className="h-5 w-5 text-slate-600" />
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">History</div>
                <div className="text-sm text-slate-500">Past interviews, status changes, and outcome timeline.</div>
              </div>
            </div>

            {interviewsQuery.isLoading ? (
              <Skeleton active paragraph={{ rows: 5 }} />
            ) : historyItems.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No interview history yet" />
            ) : (
              <Timeline
                items={historyItems.map((item) => {
                  const itemResult = normalizeResult(item.status, item.decision?.decision)
                  return {
                    color: itemResult === 'rejected' ? 'red' : itemResult === 'shortlisted' || itemResult === 'next_round' ? 'blue' : 'green',
                    dot: <CheckCircle2 className="h-4 w-4" />,
                    children: (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-900">{item.title || interviewTypeLabel(item.interview_type)}</span>
                          <Tag color={statusColor(itemResult)} className="m-0">{resultLabel(itemResult)}</Tag>
                        </div>
                        <div className="text-sm text-slate-500">
                          {item.scheduled_at ? dayjs(item.scheduled_at).format('DD MMM YYYY · hh:mm A') : 'Date pending'}
                        </div>
                      </div>
                    ),
                  }
                })}
              />
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
