import { useMemo, useState } from 'react'
import {
  Button,
  Card,
  Empty,
  Input,
  Rate,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  CheckCircle2,
  ClipboardCheck,
  MessageSquareQuote,
  Star,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

type CandidateInterviewRow = {
  id: string
  title?: string
  interview_type?: string
  scheduled_at?: string
  duration_minutes?: number
  status?: string
  result?: string
  decision?: { decision?: string }
}

function interviewTypeLabel(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function getInterviewTitle(row?: CandidateInterviewRow | null) {
  if (!row) return 'Interview'
  return row.title || interviewTypeLabel(row.interview_type)
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

export default function CandidateInterviewFeedback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [selectedInterviewId, setSelectedInterviewId] = useState('')
  const [overallRating, setOverallRating] = useState(0)
  const [difficultyRating, setDifficultyRating] = useState(0)
  const [clarityRating, setClarityRating] = useState(0)
  const [professionalismRating, setProfessionalismRating] = useState(0)
  const [communicationRating, setCommunicationRating] = useState(0)
  const [interviewerClarityRating, setInterviewerClarityRating] = useState(0)
  const [schedulingExperience, setSchedulingExperience] = useState('')
  const [platformUsability, setPlatformUsability] = useState('')
  const [instructionsClarity, setInstructionsClarity] = useState('')
  const [comments, setComments] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [skipped, setSkipped] = useState(false)

  const interviewsQuery = useQuery({
    queryKey: ['candidate_interview_feedback_list'],
    queryFn: async () => (await interviewsApi.candidateList()).data?.data || {},
  })

  const dashboard = interviewsQuery.data || {}
  const completedInterviews: CandidateInterviewRow[] = dashboard.completed_interviews || []
  const allInterviews: CandidateInterviewRow[] = dashboard.interviews || []

  const activeInterview = useMemo(() => {
    const routeInterviewId = searchParams.get('interview') || selectedInterviewId
    return (
      completedInterviews.find((item) => item.id === routeInterviewId) ||
      allInterviews.find((item) => item.id === routeInterviewId) ||
      completedInterviews[0] ||
      null
    )
  }, [searchParams, selectedInterviewId, completedInterviews, allInterviews])

  const feedbackVisible = Boolean(activeInterview)

  const handleSubmit = () => {
    if (!activeInterview) {
      message.info('Select a completed interview first')
      return
    }
    setSubmitted(true)
    setSkipped(false)
    message.success('Candidate feedback shell submitted')
  }

  const handleSkip = () => {
    setSkipped(true)
    setSubmitted(false)
    message.success('Feedback skipped')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">
            Interview Feedback
          </Title>
          <Text className="text-sm text-slate-500">
            Share optional feedback about your interview experience after completion.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/candidate/interviews/results')}>Open Results</Button>
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Interviews</Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="rounded-3xl border-slate-200 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <ClipboardCheck className="h-5 w-5 text-blue-600" />
            <div>
              <div className="text-sm font-black uppercase tracking-wider text-slate-900">Completed Interviews</div>
              <div className="text-sm text-slate-500">Select the completed interview you want to review.</div>
            </div>
          </div>

          {completedInterviews.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No completed interviews available for feedback" />
          ) : (
            <div className="space-y-3">
              {completedInterviews.map((row) => {
                const isActive = row.id === activeInterview?.id
                return (
                  <button
                    key={row.id}
                    type="button"
                    onClick={() => setSelectedInterviewId(row.id)}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      isActive ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{getInterviewTitle(row)}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {interviewTypeLabel(row.interview_type)} · {row.scheduled_at ? dayjs(row.scheduled_at).format('DD MMM YYYY') : 'Date pending'}
                        </div>
                      </div>
                      <Tag color="green" className="m-0">Completed</Tag>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </Card>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            {!feedbackVisible ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Feedback appears after interview completion" />
            ) : (
              <div className="space-y-5">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <Title level={4} className="!mb-1 !mt-0">
                      {getInterviewTitle(activeInterview)}
                    </Title>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
                      <span>{interviewTypeLabel(activeInterview?.interview_type)}</span>
                      {activeInterview?.scheduled_at ? <span>· {dayjs(activeInterview.scheduled_at).format('DD MMM YYYY')}</span> : null}
                      {activeInterview?.duration_minutes ? <span>· {activeInterview.duration_minutes} min</span> : null}
                    </div>
                  </div>
                  <Tag color="blue">Optional Feedback</Tag>
                </div>

                {submitted ? (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                    Feedback shell submitted successfully. This is ready to connect to analytics/reporting when a backend endpoint is added.
                  </div>
                ) : null}
                {skipped ? (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    Feedback skipped. You can still return later from the candidate portal if feedback collection remains open.
                  </div>
                ) : null}
              </div>
            )}
          </Card>

          {feedbackVisible ? (
            <>
              <div className="grid gap-6 xl:grid-cols-2">
                <SectionCard
                  title="Interview Experience Rating"
                  icon={Star}
                  subtitle="Overall experience, difficulty, and clarity."
                >
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Overall Rating</div>
                      <Rate value={overallRating} onChange={setOverallRating} />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Difficulty Rating</div>
                      <Rate value={difficultyRating} onChange={setDifficultyRating} />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Clarity Rating</div>
                      <Rate value={clarityRating} onChange={setClarityRating} />
                    </div>
                  </div>
                </SectionCard>

                <SectionCard
                  title="Interviewer Feedback"
                  icon={CheckCircle2}
                  subtitle="Optional feedback on professionalism, communication, and clarity."
                >
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Professionalism</div>
                      <Rate value={professionalismRating} onChange={setProfessionalismRating} />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Communication</div>
                      <Rate value={communicationRating} onChange={setCommunicationRating} />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Clarity</div>
                      <Rate value={interviewerClarityRating} onChange={setInterviewerClarityRating} />
                    </div>
                  </div>
                </SectionCard>
              </div>

              <div className="grid gap-6 xl:grid-cols-2">
                <SectionCard
                  title="Process Feedback"
                  icon={ClipboardCheck}
                  subtitle="Scheduling, platform usability, and instruction clarity."
                >
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Scheduling Experience</div>
                      <Select
                        className="w-full"
                        value={schedulingExperience}
                        onChange={setSchedulingExperience}
                        options={[
                          { value: 'excellent', label: 'Excellent' },
                          { value: 'good', label: 'Good' },
                          { value: 'average', label: 'Average' },
                          { value: 'poor', label: 'Poor' },
                        ]}
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Platform Usability</div>
                      <Select
                        className="w-full"
                        value={platformUsability}
                        onChange={setPlatformUsability}
                        options={[
                          { value: 'excellent', label: 'Excellent' },
                          { value: 'good', label: 'Good' },
                          { value: 'average', label: 'Average' },
                          { value: 'poor', label: 'Poor' },
                        ]}
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-semibold text-slate-900">Instructions Clarity</div>
                      <Select
                        className="w-full"
                        value={instructionsClarity}
                        onChange={setInstructionsClarity}
                        options={[
                          { value: 'very_clear', label: 'Very Clear' },
                          { value: 'clear', label: 'Clear' },
                          { value: 'mixed', label: 'Mixed' },
                          { value: 'unclear', label: 'Unclear' },
                        ]}
                      />
                    </div>
                  </div>
                </SectionCard>

                <SectionCard
                  title="Candidate Comments"
                  icon={MessageSquareQuote}
                  subtitle="Open text feedback and suggestions."
                >
                  <TextArea
                    rows={10}
                    placeholder="Share any feedback, suggestions, or comments about the interview experience."
                    value={comments}
                    onChange={(event) => setComments(event.target.value)}
                  />
                </SectionCard>
              </div>

              <SectionCard
                title="Submission"
                icon={CheckCircle2}
                subtitle="Submit feedback or skip participation."
              >
                <Space wrap>
                  <Button type="primary" onClick={handleSubmit}>
                    Submit Feedback
                  </Button>
                  <Button onClick={handleSkip}>Skip Feedback</Button>
                  <Button onClick={() => navigate('/candidate/interviews/results')}>
                    View Results
                  </Button>
                </Space>
                <Paragraph className="!mb-0 !mt-4 text-sm text-slate-500">
                  Candidate feedback is optional. This page is wired for analytics/reporting integration when a dedicated feedback submission API is added.
                </Paragraph>
              </SectionCard>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
