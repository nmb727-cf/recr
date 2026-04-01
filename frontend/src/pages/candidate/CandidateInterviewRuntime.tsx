import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Progress,
  Radio,
  Space,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Bot,
  CheckCircle2,
  Clock3,
  FileText,
  ListChecks,
  Mic,
  PauseCircle,
  PlayCircle,
  Users,
  Video,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

function formatInterviewType(value?: string) {
  if (!value) return 'Interview'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatTimer(totalSeconds: number) {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function statusColor(status?: string) {
  switch (status) {
    case 'completed':
    case 'submitted':
      return 'green'
    case 'in_progress':
      return 'blue'
    case 'scheduled':
    case 'not_started':
      return 'default'
    case 'expired':
    case 'missed':
    case 'blocked':
      return 'red'
    default:
      return 'gold'
  }
}

function getExecutionMode(interviewType?: string) {
  const type = interviewType || ''
  if (type.includes('ai') || type === 'one_way_video' || type === 'async_text_interview') return 'ai'
  if (type.includes('assessment') || type === 'aptitude_test' || type === 'case_study' || type === 'work_sample_test') return 'assessment'
  if (type.includes('video') || type === 'one_way_video' || type === 'prerecorded_video' || type === 'live_video') return 'video'
  if (type === 'group_discussion') return 'group'
  if (type === 'presentation_interview') return 'presentation'
  if (type === 'role_play') return 'role_play'
  if (type === 'portfolio_review') return 'portfolio'
  if (type === 'mock_interview') return 'mock'
  if (type.includes('human') || type.includes('panel') || type.includes('hr') || type.includes('leadership') || type.includes('executive')) return 'human'
  if (type.includes('technical') || type === 'coding_interview' || type === 'system_design' || type === 'debugging_interview' || type === 'whiteboard_interview') return 'technical'
  return 'generic'
}

export default function CandidateInterviewRuntime() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('access_token') || ''
  const [sessionId] = useState<string>(() => `sess_${crypto.randomUUID()}`)
  const qc = useQueryClient()

  const [currentQuestionId, setCurrentQuestionId] = useState<string>('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [optionAnswers, setOptionAnswers] = useState<Record<string, string>>({})
  const [assignmentUrl, setAssignmentUrl] = useState('')
  const [started, setStarted] = useState(false)
  const [paused, setPaused] = useState(false)
  const [timerSec, setTimerSec] = useState(0)

  const runtimeQ = useQuery({
    queryKey: ['candidate_interview_runtime', id],
    enabled: !!id,
    queryFn: async () => (await interviewsApi.candidateRuntime(id, { access_token: token, session_id: sessionId })).data?.data || {},
    retry: false,
  })

  const runtime = runtimeQ.data || {}
  const interview = runtime.interview || {}
  const questions = Array.isArray(runtime.questions) ? runtime.questions : []
  const session = runtime.session || {}
  const securityShell = runtime.security_shell || {}
  const instructions = runtime.instructions || interview.instructions || 'Follow the interview instructions and submit all required responses before finishing.'
  const notes = runtime.notes || interview.notes || interview.metadata?.candidate_notes || ''
  const stages = runtime.stages || interview.stages || []
  const executionMode = getExecutionMode(interview.interview_type)

  useEffect(() => {
    const err: any = runtimeQ.error
    const code = err?.response?.data?.errors?.code
    if (code === 'token_expired') navigate('/candidate/interviews/expired', { replace: true })
    if (code === 'session_locked' || code === 'token_invalid' || code === 'attempt_blocked' || code === 'time_window_early') {
      navigate('/candidate/interviews/blocked', { replace: true })
    }
  }, [runtimeQ.error, navigate])

  useEffect(() => {
    if (!currentQuestionId && questions.length > 0) setCurrentQuestionId(questions[0].id)
  }, [questions, currentQuestionId])

  useEffect(() => {
    if (!started || paused) return
    const timer = setInterval(() => setTimerSec((value) => value + 1), 1000)
    return () => clearInterval(timer)
  }, [started, paused])

  useEffect(() => {
    if (!id || !started) return
    const onVisibility = () => {
      if (document.hidden) interviewsApi.candidateSecurityEvent(id, { event_type: 'tab_switch' })
    }
    const onCopy = () => interviewsApi.candidateSecurityEvent(id, { event_type: 'copy_paste' })
    const onStorage = () => interviewsApi.candidateSecurityEvent(id, { event_type: 'multiple_window' })
    document.addEventListener('visibilitychange', onVisibility)
    document.addEventListener('copy', onCopy)
    window.addEventListener('storage', onStorage)
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      document.removeEventListener('copy', onCopy)
      window.removeEventListener('storage', onStorage)
    }
  }, [id, started])

  const current = useMemo(
    () => questions.find((question: any) => question.id === currentQuestionId) || null,
    [questions, currentQuestionId],
  )

  const currentQuestionIndex = questions.findIndex((question: any) => question.id === currentQuestionId)
  const progressPercent = questions.length ? Math.round(((currentQuestionIndex + 1) / questions.length) * 100) : interview.status === 'completed' ? 100 : 0

  const startM = useMutation({
    mutationFn: async () => interviewsApi.candidateStart(id, { access_token: token, session_id: sessionId }),
    onSuccess: () => {
      setStarted(true)
      setPaused(false)
      message.success('Interview started')
      qc.invalidateQueries({ queryKey: ['candidate_interview_runtime', id] })
    },
    onError: () => message.error('Unable to start interview'),
  })

  const submitM = useMutation({
    mutationFn: async (payload: any) => interviewsApi.candidateSubmitAnswer(id, payload),
    onSuccess: () => {
      message.success('Answer submitted')
      qc.invalidateQueries({ queryKey: ['candidate_interview_runtime', id] })
    },
    onError: () => message.error('Failed to submit answer'),
  })

  const completeM = useMutation({
    mutationFn: async () => interviewsApi.candidateComplete(id),
    onSuccess: () => {
      message.success('Interview completed')
      qc.invalidateQueries({ queryKey: ['candidate_interview_runtime', id] })
      navigate(`/candidate/interviews/${id}/status`)
    },
    onError: () => message.error('Failed to complete interview'),
  })

  const goToNextQuestion = () => {
    if (!questions.length || currentQuestionIndex === -1) return
    const next = questions[currentQuestionIndex + 1]
    if (next) setCurrentQuestionId(next.id)
  }

  const onSubmitCurrent = () => {
    if (!current) return
    const answerText = optionAnswers[current.id] || answers[current.id] || ''
    submitM.mutate({
      question_id: current.id,
      answer_text: answerText,
      assignment_url: assignmentUrl || undefined,
    })
  }

  const renderQuestionBody = () => {
    if (!current) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a question or wait for the interview stage to load" />
    }

    const choiceOptions = current.options || current.answer_options || []
    const hasChoices = Array.isArray(choiceOptions) && choiceOptions.length > 0
    const isVideoMode = executionMode === 'video'
    const isHumanMode = executionMode === 'human'
    const isGroupMode = executionMode === 'group'
    const isPresentationMode = executionMode === 'presentation'
    const isRolePlayMode = executionMode === 'role_play'
    const isPortfolioMode = executionMode === 'portfolio'

    return (
      <div className="space-y-5">
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Tag color="blue">Question {Math.max(currentQuestionIndex + 1, 1)}</Tag>
            {current.type || current.response_mode ? <Tag>{current.type || current.response_mode}</Tag> : null}
          </div>
          <Title level={5} className="!mb-2 !mt-0">
            {current.question_text || current.prompt || 'Interview prompt pending'}
          </Title>
          {current.instructions ? <Paragraph className="!mb-0 text-slate-500">{current.instructions}</Paragraph> : null}
        </div>

        {executionMode === 'ai' || executionMode === 'technical' || executionMode === 'mock' || executionMode === 'generic' ? (
          <Card className="rounded-3xl border-slate-200" title="Response">
            <Input.TextArea
              rows={8}
              disabled={paused}
              value={answers[current.id] || ''}
              onChange={(event) => setAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
              placeholder="Write your answer here"
            />
          </Card>
        ) : null}

        {executionMode === 'assessment' ? (
          <Card className="rounded-3xl border-slate-200" title="Assessment Response">
            {hasChoices ? (
              <Radio.Group
                className="w-full"
                value={optionAnswers[current.id]}
                onChange={(event) => setOptionAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
              >
                <Space direction="vertical" className="w-full">
                  {choiceOptions.map((option: any, index: number) => (
                    <Radio key={`${current.id}-${index}`} value={String(option.value || option.label || option)}>
                      {String(option.label || option.value || option)}
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            ) : (
              <Input.TextArea
                rows={8}
                disabled={paused}
                value={answers[current.id] || ''}
                onChange={(event) => setAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
                placeholder="Write your answer here"
              />
            )}
          </Card>
        ) : null}

        {isVideoMode ? (
          <Card className="rounded-3xl border-slate-200" title="Video Response Shell">
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <Video className="mx-auto h-10 w-10 text-slate-400" />
              <div className="mt-3 text-sm font-semibold text-slate-700">Recording UI shell</div>
              <div className="mt-1 text-sm text-slate-500">Video capture remains a unified candidate execution shell here. Meeting links and external providers still work from the runtime controls.</div>
            </div>
            <div className="mt-4">
              <Input.TextArea
                rows={4}
                disabled={paused}
                value={answers[current.id] || ''}
                onChange={(event) => setAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
                placeholder="Optional supporting notes for your video response"
              />
            </div>
          </Card>
        ) : null}

        {isHumanMode ? (
          <Card className="rounded-3xl border-slate-200" title="Live Interview Waiting Screen">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
              <div className="text-sm font-semibold text-slate-900">This interview is coordinated live with interviewer participation.</div>
              <div className="mt-2 text-sm text-slate-500">Use the meeting or external interview links from the top controls when the interviewer is ready.</div>
            </div>
          </Card>
        ) : null}

        {isGroupMode ? (
          <Card className="rounded-3xl border-slate-200" title="Group Discussion Waiting Room">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-slate-500" />
                <div className="text-sm text-slate-600">Waiting room shell active. Join from the available meeting link once moderators open the discussion.</div>
              </div>
            </div>
          </Card>
        ) : null}

        {isPresentationMode ? (
          <Card className="rounded-3xl border-slate-200" title="Presentation Area">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
              <div className="text-sm font-semibold text-slate-900">Presentation delivery shell</div>
              <div className="mt-2 text-sm text-slate-500">Use this area for speaking notes, structure, and presentation flow before live delivery or recorded upload.</div>
            </div>
            <div className="mt-4">
              <Input.TextArea
                rows={6}
                disabled={paused}
                value={answers[current.id] || ''}
                onChange={(event) => setAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
                placeholder="Presentation notes or response summary"
              />
            </div>
          </Card>
        ) : null}

        {isRolePlayMode || isPortfolioMode ? (
          <Card className="rounded-3xl border-slate-200" title={isRolePlayMode ? 'Role Play Response' : 'Portfolio Review Response'}>
            <Input.TextArea
              rows={7}
              disabled={paused}
              value={answers[current.id] || ''}
              onChange={(event) => setAnswers((prev) => ({ ...prev, [current.id]: event.target.value }))}
              placeholder={isRolePlayMode ? 'Respond to the scenario or document your approach' : 'Describe your portfolio, project decisions, and outcomes'}
            />
          </Card>
        ) : null}

        <Card className="rounded-3xl border-slate-200" title="Attachments / Submission">
          <Space direction="vertical" className="w-full">
            <Upload
              beforeUpload={() => false}
              maxCount={1}
              onChange={(info) => {
                const file = info.fileList?.[0]
                if (file) setAssignmentUrl(file.name)
              }}
            >
              <Button icon={<UploadOutlined />}>Attach Supporting File</Button>
            </Upload>
            {assignmentUrl ? <Text className="text-sm text-slate-500">Attached: {assignmentUrl}</Text> : null}
          </Space>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Title level={4} className="!mb-0 !mt-0">
                {interview.title || formatInterviewType(interview.interview_type)}
              </Title>
              <Tag>{formatInterviewType(interview.interview_type)}</Tag>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
              <span className="flex items-center gap-1"><Clock3 className="h-4 w-4" /> Timer: {formatTimer(timerSec)}</span>
              <span>Session: {session.session_id || session.active_session_id || sessionId}</span>
              {interview.duration_minutes ? <span>Duration: {interview.duration_minutes} min</span> : null}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[420px]">
            <div className="rounded-2xl border border-slate-200 px-4 py-3">
              <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Status</div>
              <div className="mt-2">
                <Tag color={statusColor(interview.status)}>{interview.status || 'not_started'}</Tag>
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 px-4 py-3">
              <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Progress</div>
              <div className="mt-2 text-lg font-black text-slate-900">{progressPercent}%</div>
            </div>
            <div className="rounded-2xl border border-slate-200 px-4 py-3">
              <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Questions</div>
              <div className="mt-2 text-lg font-black text-slate-900">{questions.length}</div>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <Progress percent={progressPercent} showInfo={false} strokeColor="#2563eb" />
        </div>
      </div>

      <Alert
        type="info"
        showIcon
        message="Unified Interview Execution"
        description="This runtime adapts to AI, technical, human, assessment, video, group discussion, presentation, role play, portfolio review, mock interview, and related registry interview types through one candidate execution layer."
      />

      <div className="flex flex-wrap gap-3">
        <Button type="primary" icon={<PlayCircle className="h-4 w-4" />} loading={startM.isPending} onClick={() => startM.mutate()}>
          {started || interview.status === 'in_progress' ? 'Resume / Restart' : 'Start Interview'}
        </Button>
        <Button
          icon={<PauseCircle className="h-4 w-4" />}
          disabled={!started || interview.status === 'completed'}
          onClick={() => setPaused((value) => !value)}
        >
          {paused ? 'Resume' : 'Pause'}
        </Button>
        {interview.meeting_link ? (
          <Button href={interview.meeting_link} target="_blank" rel="noreferrer">
            Join Meeting
          </Button>
        ) : null}
        {interview.external_interview_link ? (
          <Button href={interview.external_interview_link} target="_blank" rel="noreferrer">
            Open External Interview
          </Button>
        ) : null}
        <Button onClick={() => navigate(`/candidate/interviews/${id}/instructions?access_token=${token}`)}>View Instructions</Button>
        <Button onClick={() => navigate(`/candidate/interviews/${id}/status`)}>View Status</Button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200" title="Main Interview Area">
            {runtimeQ.isLoading ? (
              <div className="py-12 text-center text-sm text-slate-500">Loading interview runtime...</div>
            ) : (
              renderQuestionBody()
            )}
          </Card>

          <Card className="rounded-3xl border-slate-200" title="Execution Controls">
            <div className="flex flex-wrap gap-3">
              <Button type="primary" loading={submitM.isPending} onClick={onSubmitCurrent} disabled={!current || paused || interview.status === 'completed'}>
                Submit
              </Button>
              <Button onClick={goToNextQuestion} disabled={!questions.length || currentQuestionIndex >= questions.length - 1}>
                Next Question
              </Button>
              <Button danger loading={completeM.isPending} onClick={() => completeM.mutate()} disabled={interview.status === 'completed'}>
                Finish Interview
              </Button>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200" title="Instructions">
            <Paragraph className="!mb-0 text-sm text-slate-600">{instructions}</Paragraph>
          </Card>

          <Card className="rounded-3xl border-slate-200" title="Progress">
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Current Step</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {current ? `Question ${Math.max(currentQuestionIndex + 1, 1)} of ${questions.length}` : 'Waiting for interview items'}
                </div>
              </div>
              <div className="space-y-2">
                {questions.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No staged questions yet" />
                ) : (
                  questions.map((question: any, index: number) => (
                    <button
                      key={question.id}
                      type="button"
                      onClick={() => setCurrentQuestionId(question.id)}
                      className={cn(
                        'flex w-full items-center justify-between rounded-2xl border px-3 py-3 text-left',
                        question.id === currentQuestionId ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600',
                      )}
                    >
                      <span className="flex min-w-0 items-center gap-3">
                        <ListChecks className="h-4 w-4 shrink-0" />
                        <span className="truncate text-sm font-medium">{question.question_text || question.prompt || `Question ${index + 1}`}</span>
                      </span>
                      <Tag className="m-0">Q{index + 1}</Tag>
                    </button>
                  ))
                )}
              </div>
            </div>
          </Card>

          <Card className="rounded-3xl border-slate-200" title="Stages">
            {Array.isArray(stages) && stages.length ? (
              <div className="space-y-2">
                {stages.map((stage: any, index: number) => (
                  <div key={stage.id || `${stage.name}-${index}`} className="rounded-2xl border border-slate-200 p-3">
                    <div className="text-sm font-semibold text-slate-900">{stage.name || `Stage ${index + 1}`}</div>
                    <div className="mt-1 text-xs text-slate-500">{formatInterviewType(stage.stage_type || stage.type)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                Unified single-stage runtime in progress for this interview.
              </div>
            )}
          </Card>

          <Card className="rounded-3xl border-slate-200" title="Notes">
            <div className="space-y-3 text-sm text-slate-600">
              <div className="flex items-center gap-2 text-slate-700">
                {executionMode === 'ai' ? <Bot className="h-4 w-4" /> : executionMode === 'video' ? <Video className="h-4 w-4" /> : executionMode === 'group' ? <Users className="h-4 w-4" /> : executionMode === 'assessment' ? <FileText className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                <span>Execution mode: {executionMode}</span>
              </div>
              <div>{notes || 'No additional notes provided for this interview.'}</div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Security Shell</div>
                <div className="mt-2 space-y-1 text-xs text-slate-500">
                  <div>Single attempt: {securityShell.single_attempt_shell ? 'Enabled' : 'Not enforced'}</div>
                  <div>Session lock: {session.active_session_id || session.session_id || 'Pending'}</div>
                  <div>Paused: {paused ? 'Yes' : 'No'}</div>
                </div>
              </div>
            </div>
          </Card>

          {paused ? (
            <Alert
              type="warning"
              showIcon
              message="Interview paused"
              description="Pause is currently handled as a candidate-side execution shell. Resume when you are ready to continue."
            />
          ) : null}
          {interview.status === 'completed' || interview.status === 'submitted' ? (
            <Alert type="success" showIcon message="Interview completed" description="Your interview has been submitted. You can review status from the status page." />
          ) : null}
          {interview.status === 'expired' ? (
            <Alert type="error" showIcon message="Interview expired" description="This interview is no longer available in the allowed time window." />
          ) : null}
        </div>
      </div>
    </div>
  )
}
