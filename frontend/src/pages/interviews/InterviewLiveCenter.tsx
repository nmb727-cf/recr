import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Empty, Input, InputNumber, Select, Spin, Table, Tag, Typography, message } from 'antd'
import { CheckCircle2, Clock3, MonitorPlay, Pause, Play, Square, UserCircle2 } from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import type { Interview } from '@/types'
import { cn } from '@/utils/cn'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { getInterviewTypeCategory, getInterviewTypeLabel } from '@/utils/interviewTypeUx'

const { Text } = Typography

const RECOMMENDATION_OPTIONS = [
  { value: 'hire', label: 'Hire' },
  { value: 'reject', label: 'Reject' },
  { value: 'hold', label: 'Hold' },
  { value: 'next_round', label: 'Next Round' },
  { value: 'manual_review', label: 'Manual Review' },
]

type InterviewLiveCenterProps = {
  embedded?: boolean
}

export default function InterviewLiveCenter({ embedded = false }: InterviewLiveCenterProps) {
  const queryClient = useQueryClient()
  const [selectedInterviewId, setSelectedInterviewId] = useState<string | null>(null)
  const [feedbackScore, setFeedbackScore] = useState<number | null>(null)
  const [feedbackRecommendation, setFeedbackRecommendation] = useState<string>('next_round')
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [decisionValue, setDecisionValue] = useState<string>('next_round')
  const [decisionNotes, setDecisionNotes] = useState('')
  const [decisionMode, setDecisionMode] = useState<'manual' | 'auto'>('manual')
  const [scorecardRatings, setScorecardRatings] = useState<Record<string, any>>({})
  const [actionLoading, setActionLoading] = useState<'start' | 'pause' | 'resume' | 'end' | 'feedback' | 'decision' | null>(null)

  const { data, isLoading } = useApiQuery(['live-interviews-list'], () =>
    interviewsApi.list({ ordering: 'scheduled_at' }),
  )
  const interviews: Interview[] = (data as any)?.interviews ?? []

  const liveInterviews = useMemo(() => {
    return interviews.filter((interview) =>
      ['scheduled', 'in_progress', 'paused', 'completed', 'awaiting_feedback', 'awaiting_decision'].includes(interview.status),
    )
  }, [interviews])

  useEffect(() => {
    if (!selectedInterviewId && liveInterviews.length > 0) setSelectedInterviewId(liveInterviews[0].id)
  }, [liveInterviews, selectedInterviewId])

  const selectedInterview = liveInterviews.find((interview) => interview.id === selectedInterviewId) || null

  const { data: kitResponse, isLoading: isKitLoading, isError: isKitError } = useApiQuery(
    ['live-interview-kit', selectedInterviewId],
    () => interviewsApi.getKit(selectedInterviewId || ''),
    { enabled: Boolean(selectedInterviewId) },
  )
  const { data: decisionResponse } = useApiQuery(
    ['live-interview-decision', selectedInterviewId],
    () => interviewsApi.getDecision(selectedInterviewId || ''),
    { enabled: Boolean(selectedInterviewId) },
  )

  const kit = (kitResponse as any)?.data || (kitResponse as any) || {}
  const currentDecision = (decisionResponse as any)?.data?.decision

  useEffect(() => {
    const attributes = kit?.scorecard?.attributes || []
    const nextRatings: Record<string, any> = {}
    attributes.forEach((attribute: any) => {
      nextRatings[attribute.id] = undefined
    })
    setScorecardRatings(nextRatings)
    setFeedbackScore(null)
    setFeedbackNotes('')
    setDecisionNotes('')
    setFeedbackRecommendation('next_round')
    setDecisionValue('next_round')
  }, [selectedInterviewId, kit?.scorecard?.id])

  const statusCounts = useMemo(() => ({
    ongoing: liveInterviews.filter((interview) => ['in_progress', 'paused'].includes(interview.status)).length,
    waiting: liveInterviews.filter((interview) => interview.status === 'scheduled').length,
    completed: liveInterviews.filter((interview) => ['completed', 'awaiting_feedback', 'awaiting_decision'].includes(interview.status)).length,
  }), [liveInterviews])

  const runInterviewAction = async (action: 'start' | 'pause' | 'resume' | 'end') => {
    if (!selectedInterview) return
    setActionLoading(action)
    try {
      if (action === 'start') await interviewsApi.start(selectedInterview.id)
      if (action === 'pause') await interviewsApi.update(selectedInterview.id, { status: 'paused' } as Partial<Interview>)
      if (action === 'resume') await interviewsApi.update(selectedInterview.id, { status: 'in_progress' } as Partial<Interview>)
      if (action === 'end') await interviewsApi.complete(selectedInterview.id)
      message.success(`Interview ${action === 'end' ? 'completed' : `${action}ed`}`)
      await queryClient.invalidateQueries({ queryKey: ['live-interviews-list'] })
      await queryClient.invalidateQueries({ queryKey: ['live-interview-kit', selectedInterview.id] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || `Failed to ${action} interview`)
    } finally {
      setActionLoading(null)
    }
  }

  const submitFeedback = async () => {
    if (!selectedInterview) return
    setActionLoading('feedback')
    try {
      const payloadRatings: Record<string, any> = {}
      ;(kit?.scorecard?.attributes || []).forEach((attribute: any) => {
        payloadRatings[attribute.attribute_name] = scorecardRatings[attribute.id]
      })
      await interviewsApi.submitStructuredFeedback(selectedInterview.id, {
        score: feedbackScore,
        notes: feedbackNotes,
        recommendation: feedbackRecommendation,
        scorecard_ratings: payloadRatings,
      })
      message.success('Evaluation submitted')
      await queryClient.invalidateQueries({ queryKey: ['live-interview-kit', selectedInterview.id] })
      await queryClient.invalidateQueries({ queryKey: ['live-interviews-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to submit evaluation')
    } finally {
      setActionLoading(null)
    }
  }

  const submitDecision = async () => {
    if (!selectedInterview) return
    setActionLoading('decision')
    try {
      if (decisionMode === 'auto') {
        await interviewsApi.evaluateDecision(selectedInterview.id, {
          persist: true,
          notes: decisionNotes,
          thresholds: { next_round_min: 80, reject_max: 50 },
          source_inputs: { score: feedbackScore ?? selectedInterview.feedback_average_score ?? 0 },
        })
      } else {
        await interviewsApi.recordDecision(selectedInterview.id, {
          decision: decisionValue,
          decision_source: 'manual',
          decision_mode: 'manual',
          notes: decisionNotes,
        })
      }
      message.success('Decision saved')
      await queryClient.invalidateQueries({ queryKey: ['live-interview-decision', selectedInterview.id] })
      await queryClient.invalidateQueries({ queryKey: ['live-interview-kit', selectedInterview.id] })
      await queryClient.invalidateQueries({ queryKey: ['live-interviews-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save decision')
    } finally {
      setActionLoading(null)
    }
  }

  const listColumns: ColumnsType<Interview> = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_, interview) => (
        <div>
          <p className="m-0 font-bold text-slate-900">{interview.candidate_name || interview.candidate_id || `Candidate ${interview.id.slice(0, 6)}`}</p>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{getInterviewTypeLabel(interview.interview_type)}</Text>
        </div>
      ),
    },
    {
      title: 'Stage',
      key: 'stage',
      render: (_, interview) => <Text className="text-slate-600">{(interview.metadata as any)?.stage_name || `Round ${interview.interview_round}`}</Text>,
    },
    {
      title: 'Interviewer',
      key: 'interviewer',
      render: (_, interview) => <Text className="text-slate-600">{interview.interviewers?.join(', ') || 'Unassigned'}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => {
        const style = getStatusStyle(value)
        return <Tag color={style.color}>{formatStatusLabel(value)}</Tag>
      },
    },
    {
      title: 'Time',
      key: 'time',
      render: (_, interview) => <Text className="text-slate-600">{interview.scheduled_at ? new Date(interview.scheduled_at).toLocaleString() : 'Not scheduled'}</Text>,
    },
  ]

  const containerClass = embedded ? 'h-full overflow-y-auto p-6 space-y-5' : 'min-h-screen bg-[#F8FAFC] p-6 space-y-5'

  return (
    <div className={containerClass}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <Text className="block text-[10px] font-black uppercase tracking-[0.24em] text-indigo-500">ICC-LIVE-INTERVIEW-CENTER-01</Text>
          <h2 className="m-0 mt-1 text-2xl font-black text-slate-900">Live Interviews</h2>
          <Text className="text-slate-500">Real-time interview execution across AI, human, technical, and assessment formats.</Text>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Ongoing Interviews', value: statusCounts.ongoing, icon: MonitorPlay, color: 'text-indigo-600', bg: 'bg-indigo-50' },
          { label: 'Waiting Candidates', value: statusCounts.waiting, icon: Clock3, color: 'text-amber-600', bg: 'bg-amber-50' },
          { label: 'Completed Interviews', value: statusCounts.completed, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
        ].map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-soft-sm">
            <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center', item.bg, item.color)}>
              <item.icon size={18} />
            </div>
            <Text className="mt-3 block text-[10px] font-black uppercase tracking-widest text-slate-400">{item.label}</Text>
            <Text className="block text-2xl font-black text-slate-900 leading-none">{item.value}</Text>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[420px_minmax(0,1fr)] gap-5 items-start">
        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
          <div className="mb-4">
            <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Live Interview List</Text>
            <Text className="text-slate-500">Open any interview to manage execution, evaluation, and decisioning in one place.</Text>
          </div>
          <Table
            rowKey="id"
            size="small"
            columns={listColumns}
            dataSource={liveInterviews}
            loading={isLoading}
            pagination={{ pageSize: 8, hideOnSinglePage: true }}
            onRow={(record) => ({
              onClick: () => setSelectedInterviewId(record.id),
              className: cn('cursor-pointer', selectedInterviewId === record.id && 'bg-indigo-50/60'),
            })}
          />
        </div>

        <div className="space-y-5">
          {!selectedInterview ? (
            <div className="rounded-2xl border border-slate-100 bg-white p-10 shadow-soft-sm">
              <Empty description="No live interview selected" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-5 items-start">
                <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Live Interview Room</Text>
                      <p className="m-0 mt-1 text-xl font-black text-slate-900">{selectedInterview.title || getInterviewTypeLabel(selectedInterview.interview_type)}</p>
                      <p className="m-0 mt-1 text-sm text-slate-500">
                        {getInterviewTypeCategory(selectedInterview.interview_type)} · {(selectedInterview.metadata as any)?.stage_name || `Round ${selectedInterview.interview_round}`}
                      </p>
                    </div>
                    <Tag color={getStatusStyle(selectedInterview.status).color}>{formatStatusLabel(selectedInterview.status)}</Tag>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-5">
                    <div className="rounded-xl bg-slate-50 p-4">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Execution Mode</Text>
                      <Text className="block mt-1 font-bold text-slate-800">{getInterviewTypeLabel(selectedInterview.interview_type)}</Text>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-4">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Interviewer</Text>
                      <Text className="block mt-1 font-bold text-slate-800">{selectedInterview.interviewers?.join(', ') || 'Unassigned'}</Text>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button icon={<Play size={14} />} type="primary" onClick={() => runInterviewAction('start')} loading={actionLoading === 'start'} disabled={selectedInterview.status === 'in_progress'}>
                      Start Interview
                    </Button>
                    <Button icon={<Pause size={14} />} onClick={() => runInterviewAction('pause')} loading={actionLoading === 'pause'} disabled={selectedInterview.status !== 'in_progress'}>
                      Pause
                    </Button>
                    <Button icon={<Play size={14} />} onClick={() => runInterviewAction('resume')} loading={actionLoading === 'resume'} disabled={selectedInterview.status !== 'paused'}>
                      Resume
                    </Button>
                    <Button icon={<Square size={14} />} danger onClick={() => runInterviewAction('end')} loading={actionLoading === 'end'} disabled={!['in_progress', 'paused'].includes(selectedInterview.status)}>
                      End Interview
                    </Button>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">Real-Time Status</Text>
                  <div className="space-y-3">
                    {[
                      { label: 'Ongoing Interviews', value: statusCounts.ongoing, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                      { label: 'Waiting Candidates', value: statusCounts.waiting, color: 'text-amber-600', bg: 'bg-amber-50' },
                      { label: 'Completed Interviews', value: statusCounts.completed, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                    ].map((item) => (
                      <div key={item.label} className={cn('rounded-xl p-4', item.bg)}>
                        <Text className={cn('block text-2xl font-black leading-none', item.color)}>{item.value}</Text>
                        <Text className="block mt-1 text-[9px] font-black uppercase tracking-widest text-slate-500">{item.label}</Text>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-5 items-start">
                <div className="space-y-5">
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                    <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title="Candidate Profile">
                      {isKitLoading ? <Spin /> : isKitError ? <Alert type="error" message="Failed to load interview panel" /> : (
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
                              <UserCircle2 size={20} />
                            </div>
                            <div>
                              <p className="m-0 font-black text-slate-900">{kit.candidate?.full_name || selectedInterview.candidate_name || selectedInterview.candidate_id || '-'}</p>
                              <Text className="text-slate-500 text-sm">{kit.candidate?.email || 'Email not available'}</Text>
                            </div>
                          </div>
                          <Text className="block text-slate-600">{kit.candidate?.current_title || 'Candidate title not available'}</Text>
                          <Text className="block text-slate-600">{kit.resume_url ? 'Resume available in interview kit' : 'Resume not attached'}</Text>
                        </div>
                      )}
                    </Card>

                    <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title="Job & Stage Details">
                      {isKitLoading ? <Spin /> : (
                        <div className="space-y-2">
                          <p className="m-0 font-black text-slate-900">{kit.job?.title || selectedInterview.job_title || 'Job not linked'}</p>
                          <Text className="block text-slate-600">{(selectedInterview.metadata as any)?.stage_name || `Round ${selectedInterview.interview_round}`}</Text>
                          <Text className="block text-slate-600">{selectedInterview.duration_minutes} minutes · {selectedInterview.scheduled_at ? new Date(selectedInterview.scheduled_at).toLocaleString() : 'Time pending'}</Text>
                          <Text className="block text-slate-600 whitespace-pre-wrap">{kit.instructions || selectedInterview.title || 'Interview instructions not available'}</Text>
                        </div>
                      )}
                    </Card>
                  </div>

                  <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title="Interview Panel">
                    {isKitLoading ? <Spin /> : (
                      <div className="space-y-4">
                        <div className="rounded-xl bg-slate-50 p-4">
                          <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Instructions</Text>
                          <Text className="block mt-2 text-slate-700 whitespace-pre-wrap">{kit.instructions || 'No interview instructions configured.'}</Text>
                        </div>
                        <div className="space-y-2">
                          <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Question / Task Flow</Text>
                          {(kit.questions || []).length === 0 ? (
                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No questions attached" />
                          ) : (
                            (kit.questions || []).map((question: any, index: number) => (
                              <div key={question.id || index} className="rounded-xl border border-slate-100 p-4">
                                <Text className="block font-bold text-slate-800">{index + 1}. {question.question_text}</Text>
                                <Text className="text-slate-500 text-sm">{question.question_type || 'Question'}</Text>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                </div>

                <div className="space-y-5">
                  <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title="Evaluation Panel">
                    {isKitLoading ? <Spin /> : (
                      <div className="space-y-4">
                        {(kit?.scorecard?.attributes || []).map((attribute: any) => (
                          <div key={attribute.id}>
                            <Text className="block mb-1 text-xs font-bold text-slate-600">{attribute.attribute_name}</Text>
                            {attribute.rating_type === 'yes_no' ? (
                              <Select
                                value={scorecardRatings[attribute.id]}
                                className="w-full"
                                options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]}
                                onChange={(value) => setScorecardRatings((current) => ({ ...current, [attribute.id]: value }))}
                              />
                            ) : attribute.rating_type === 'pass_fail' ? (
                              <Select
                                value={scorecardRatings[attribute.id]}
                                className="w-full"
                                options={[{ value: 'pass', label: 'Pass' }, { value: 'fail', label: 'Fail' }]}
                                onChange={(value) => setScorecardRatings((current) => ({ ...current, [attribute.id]: value }))}
                              />
                            ) : (
                              <InputNumber
                                min={1}
                                max={5}
                                className="w-full"
                                value={scorecardRatings[attribute.id]}
                                onChange={(value) => setScorecardRatings((current) => ({ ...current, [attribute.id]: value }))}
                              />
                            )}
                          </div>
                        ))}
                        <div>
                          <Text className="block mb-1 text-xs font-bold text-slate-600">Overall Score</Text>
                          <InputNumber min={0} max={100} className="w-full" value={feedbackScore ?? undefined} onChange={(value) => setFeedbackScore(Number(value || 0))} />
                        </div>
                        <div>
                          <Text className="block mb-1 text-xs font-bold text-slate-600">Recommendation</Text>
                          <Select value={feedbackRecommendation} className="w-full" options={RECOMMENDATION_OPTIONS} onChange={setFeedbackRecommendation} />
                        </div>
                        <div>
                          <Text className="block mb-1 text-xs font-bold text-slate-600">Notes</Text>
                          <Input.TextArea rows={4} value={feedbackNotes} onChange={(event) => setFeedbackNotes(event.target.value)} placeholder="Interview notes and evaluation summary" />
                        </div>
                        <Button type="primary" block onClick={submitFeedback} loading={actionLoading === 'feedback'}>
                          Submit Evaluation
                        </Button>
                      </div>
                    )}
                  </Card>

                  <Card className="rounded-2xl border-slate-100 shadow-soft-sm" title="Decision Panel">
                    <div className="space-y-4">
                      {currentDecision && (
                        <Alert
                          type="info"
                          showIcon
                          message={`Current decision: ${currentDecision.decision}`}
                          description={`Source: ${currentDecision.decision_source} · Mode: ${currentDecision.decision_mode}`}
                        />
                      )}
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Decision Mode</Text>
                        <Select
                          value={decisionMode}
                          className="w-full"
                          options={[{ value: 'manual', label: 'Manual decision' }, { value: 'auto', label: 'Auto evaluate' }]}
                          onChange={(value) => setDecisionMode(value)}
                        />
                      </div>
                      {decisionMode === 'manual' && (
                        <div>
                          <Text className="block mb-1 text-xs font-bold text-slate-600">Decision</Text>
                          <Select value={decisionValue} className="w-full" options={RECOMMENDATION_OPTIONS} onChange={setDecisionValue} />
                        </div>
                      )}
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Notes</Text>
                        <Input.TextArea rows={3} value={decisionNotes} onChange={(event) => setDecisionNotes(event.target.value)} placeholder="Decision notes or override reason" />
                      </div>
                      <Button block onClick={submitDecision} loading={actionLoading === 'decision'}>
                        Save Decision
                      </Button>
                    </div>
                  </Card>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
