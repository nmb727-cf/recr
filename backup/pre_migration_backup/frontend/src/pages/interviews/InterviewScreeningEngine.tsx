import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Modal,
  Select,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Copy,
  Eye,
  Phone,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
  UserCheck,
  Workflow,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type ScreeningSubtype = 'recruiter_screening' | 'phone_interview'
type WizardStep = 'setup' | 'question-flow' | 'evaluation' | 'routing' | 'preview'

type ScreeningQuestion = {
  id: string
  source: 'question_bank' | 'custom'
  title: string
  prompt: string
  question_bank_id: string
  mandatory: boolean
  tags: string[]
}

type ScreeningDraft = {
  id: string | null
  name: string
  screening_type: ScreeningSubtype
  duration_minutes: number
  description: string
  is_active: boolean
  question_flow: {
    questions: ScreeningQuestion[]
  }
  evaluation: {
    scorecard_template_id: string
    pass_threshold: number
    reject_threshold: number
  }
  routing: {
    pass_action: 'move_to_next_interview' | 'manual_review'
    reject_action: 'reject'
    manual_review_enabled: boolean
    next_stage_name: string
  }
}

type ScreeningEngineProps = {
  embedded?: boolean
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'question-flow', label: '2. Question Flow', icon: UserCheck },
  { key: 'evaluation', label: '3. Evaluation', icon: ShieldCheck },
  { key: 'routing', label: '4. Routing', icon: Workflow },
  { key: 'preview', label: '5. Preview', icon: Eye },
]

const SCREENING_TYPES: Array<{
  value: ScreeningSubtype
  label: string
  icon: React.ElementType
  guidance: {
    description: string
    defaultDuration: number
    starterQuestions: string[]
  }
}> = [
  {
    value: 'recruiter_screening',
    label: 'Recruiter Screening',
    icon: UserCheck,
    guidance: {
      description: 'Use qualification, motivation, timeline, and baseline fit questions.',
      defaultDuration: 25,
      starterQuestions: ['Why are you considering this role?', 'What notice period are you on?', 'What relevant experience aligns to this role?'],
    },
  },
  {
    value: 'phone_interview',
    label: 'Phone Interview',
    icon: Phone,
    guidance: {
      description: 'Use structured screening calls with concise questions and clear pass/reject outcomes.',
      defaultDuration: 30,
      starterQuestions: ['Walk me through your recent role.', 'What compensation range are you targeting?', 'Are you available for the next stage this week?'],
    },
  },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createQuestion(prompt = ''): ScreeningQuestion {
  return {
    id: makeId('screening-question'),
    source: 'custom',
    title: '',
    prompt,
    question_bank_id: '',
    mandatory: true,
    tags: [],
  }
}

function createDraft(type: ScreeningSubtype = 'recruiter_screening'): ScreeningDraft {
  const config = SCREENING_TYPES.find((item) => item.value === type) || SCREENING_TYPES[0]
  return {
    id: null,
    name: '',
    screening_type: config.value,
    duration_minutes: config.guidance.defaultDuration,
    description: '',
    is_active: true,
    question_flow: {
      questions: config.guidance.starterQuestions.map((prompt) => createQuestion(prompt)),
    },
    evaluation: {
      scorecard_template_id: '',
      pass_threshold: 75,
      reject_threshold: 45,
    },
    routing: {
      pass_action: 'move_to_next_interview',
      reject_action: 'reject',
      manual_review_enabled: true,
      next_stage_name: 'next_interview_stage',
    },
  }
}

function parseTemplate(record: any): ScreeningDraft {
  const meta = record?.metadata?.screening_interview || {}
  const inferredType = (meta.setup?.screening_type || record?.interview_type || 'recruiter_screening') as ScreeningSubtype
  const base = createDraft(SCREENING_TYPES.some((item) => item.value === inferredType) ? inferredType : 'recruiter_screening')
  const flow = meta.question_flow || {}
  const evaluation = meta.evaluation || {}
  const routing = meta.routing || {}
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    question_flow: {
      questions: Array.isArray(flow.questions) && flow.questions.length
        ? flow.questions.map((question: any) => ({
            id: question.id || makeId('screening-question'),
            source: question.source || 'custom',
            title: question.title || '',
            prompt: question.prompt || question.text || '',
            question_bank_id: question.question_bank_id || '',
            mandatory: question.mandatory ?? true,
            tags: Array.isArray(question.tags) ? question.tags : [],
          }))
        : base.question_flow,
    },
    evaluation: {
      scorecard_template_id: evaluation.scorecard_template_id || '',
      pass_threshold: Number(evaluation.pass_threshold ?? 75),
      reject_threshold: Number(evaluation.reject_threshold ?? 45),
    },
    routing: {
      pass_action: routing.pass_action || 'move_to_next_interview',
      reject_action: 'reject',
      manual_review_enabled: routing.manual_review_enabled ?? true,
      next_stage_name: routing.next_stage_name || 'next_interview_stage',
    },
  }
}

function serializeDraft(draft: ScreeningDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: draft.screening_type,
    duration_minutes: draft.duration_minutes,
    instructions: draft.question_flow.questions.map((question) => question.prompt).filter(Boolean).join('\n\n'),
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      screening_interview: {
        setup: {
          screening_type: draft.screening_type,
        },
        question_flow: {
          questions: draft.question_flow.questions,
        },
        evaluation: draft.evaluation,
        routing: draft.routing,
        usage: existing.metadata?.screening_interview?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          flow_engine: true,
          scorecard_engine: true,
          scheduling_engine: true,
        },
      },
    },
  }
}

function getGuidance(type: ScreeningSubtype) {
  return SCREENING_TYPES.find((item) => item.value === type) || SCREENING_TYPES[0]
}

export default function InterviewScreeningEngine({ embedded = false }: ScreeningEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const requestedType = new URLSearchParams(location.search).get('type')
  const initialType = useMemo<ScreeningSubtype>(() => {
    return requestedType === 'phone_interview' ? 'phone_interview' : 'recruiter_screening'
  }, [requestedType])

  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<ScreeningDraft>(createDraft(initialType))

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())
  const { data: questionBankData } = useApiQuery(['screening-question-bank'], () => interviewsApi.listQuestionBank())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []
  const questionBank = (questionBankData as any)?.questions ?? []

  const screeningTemplates = allTemplates.filter((template: any) => {
    const meta = template?.metadata || {}
    return meta?.screening_interview || ['recruiter_screening', 'phone_interview'].includes(template?.interview_type)
  })

  const selectedTemplate = screeningTemplates.find((template: any) => template.id === selectedTemplateId) ?? null
  const selectedScorecard = scorecards.find((scorecard: any) => scorecard.id === draft.evaluation.scorecard_template_id) ?? null
  const guidance = getGuidance(draft.screening_type)
  const stepIndex = WIZARD_STEPS.findIndex((step) => step.key === activeStep)

  const usageMap = useMemo(() => {
    return new Map(
      screeningTemplates.map((template: any) => {
        const meta = template?.metadata?.screening_interview || {}
        const usage = meta.usage || {}
        const usageCount =
          (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
          (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
          (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0) +
          flows.filter((flow: any) => (flow?.stages || []).some((stage: any) => stage?.template_id === template.id)).length
        return [template.id, usageCount]
      }),
    )
  }, [flows, screeningTemplates])

  useEffect(() => {
    if (!selectedTemplate) return
    setDraft(parseTemplate(selectedTemplate))
  }, [selectedTemplate])

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = requestedType === 'phone_interview' ? 'phone_interview' : requestedType === 'recruiter_screening' ? 'recruiter_screening' : null
    if (!nextType) return
    setDraft(createDraft(nextType))
    setSelectedTemplateId(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen])

  const updateDraft = (updater: (current: ScreeningDraft) => ScreeningDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = (type: ScreeningSubtype = initialType) => {
    setSelectedTemplateId(null)
    setDraft(createDraft(type))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const editTemplate = (template: any) => {
    setSelectedTemplateId(template.id)
    setDraft(parseTemplate(template))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const duplicateTemplate = async (template: any) => {
    try {
      const next = parseTemplate(template)
      await interviewsApi.createTemplate(serializeDraft({ ...next, id: null, name: `${next.name || template.name} Copy`, is_active: false }, template))
      message.success('Screening interview duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch {
      message.error('Failed to duplicate screening interview')
    }
  }

  const archiveTemplate = async (template: any) => {
    try {
      await interviewsApi.updateTemplate(template.id, { ...template, is_active: false })
      message.success('Screening interview archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch {
      message.error('Failed to archive screening interview')
    }
  }

  const saveDraft = async () => {
    setSaving(true)
    try {
      const payload = serializeDraft(draft, selectedTemplate)
      if (selectedTemplate?.id) {
        await interviewsApi.updateTemplate(selectedTemplate.id, payload)
        message.success('Screening interview updated')
      } else {
        await interviewsApi.createTemplate(payload)
        message.success('Screening interview created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setIsBuilderOpen(false)
      setSelectedTemplateId(null)
    } catch {
      message.error('Failed to save screening interview')
    } finally {
      setSaving(false)
    }
  }

  const questionBankOptions = questionBank.map((question: any) => ({
    value: question.id,
    label: question.question_title || question.title || 'Question',
    payload: question,
  }))

  const addQuestion = () => {
    updateDraft((current) => ({ ...current, question_flow: { questions: [...current.question_flow.questions, createQuestion()] } }))
  }

  const addQuestionFromBank = (questionId: string) => {
    const selected = questionBankOptions.find((option) => option.value === questionId)?.payload
    if (!selected) return
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: [
          ...current.question_flow.questions,
          {
            id: makeId('screening-question'),
            source: 'question_bank',
            title: selected.question_title || '',
            prompt: selected.question_title || '',
            question_bank_id: selected.id,
            mandatory: true,
            tags: Array.isArray(selected.tags) ? selected.tags : [],
          },
        ],
      },
    }))
  }

  const updateQuestion = (id: string, patch: Partial<ScreeningQuestion>) => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: current.question_flow.questions.map((question) => question.id === id ? { ...question, ...patch } : question),
      },
    }))
  }

  const moveQuestion = (id: string, direction: 'up' | 'down') => {
    updateDraft((current) => {
      const questions = [...current.question_flow.questions]
      const index = questions.findIndex((question) => question.id === id)
      const target = direction === 'up' ? index - 1 : index + 1
      if (index < 0 || target < 0 || target >= questions.length) return current
      ;[questions[index], questions[target]] = [questions[target], questions[index]]
      return { ...current, question_flow: { questions } }
    })
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, record: any) => (
        <div>
          <p className="m-0 font-black text-slate-900">{value}</p>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{record.interview_type?.replace(/_/g, ' ')}</Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value: string) => <Tag color="blue">{value?.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Duration',
      dataIndex: 'duration_minutes',
      key: 'duration_minutes',
      render: (value: number) => `${value || 0}m`,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => <Tag color={value ? 'green' : 'default'}>{value ? 'Active' : 'Archived'}</Tag>,
    },
    {
      title: 'Usage Count',
      key: 'usage',
      render: (_, record: any) => usageMap.get(record.id) || 0,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (value: string) => value ? new Date(value).toLocaleDateString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: any) => (
        <div className="flex items-center gap-2">
          <Button size="small" onClick={() => editTemplate(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateTemplate(record)}>Duplicate</Button>
          <Button size="small" onClick={() => archiveTemplate(record)}>Archive</Button>
          <Button size="small" onClick={() => { setSelectedTemplateId(record.id); setPreviewOpen(true) }}>Preview</Button>
        </div>
      ),
    },
  ]

  const containerClass = embedded ? 'h-full overflow-y-auto p-6 space-y-5' : 'min-h-screen bg-[#F8FAFC] p-6 space-y-5'

  if (!isBuilderOpen) {
    return (
      <div className={containerClass}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <Text className="block text-[10px] font-black uppercase tracking-[0.24em] text-indigo-500">ICC-SCREENING-ENGINE-01</Text>
            <h2 className="m-0 mt-1 text-2xl font-black text-slate-900">Screening Interviews</h2>
            <Text className="text-slate-500">Dedicated screening engine for recruiter screening and phone interviews.</Text>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate()}>Create Screening Interview</Button>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
          <Table rowKey="id" columns={columns} dataSource={screeningTemplates} loading={isLoading} pagination={{ pageSize: 8, hideOnSinglePage: true }} />
        </div>

        <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={720} title="Screening Preview">
          {selectedTemplate ? (
            <div className="space-y-4">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Template</Text>
                <p className="mt-1 mb-0 text-lg font-black text-slate-900">{selectedTemplate.name}</p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Type</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.interview_type?.replace(/_/g, ' ')}</Text>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.duration_minutes || 0}m</Text>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.metadata?.screening_interview?.evaluation?.scorecard_template_id ? 'Linked' : 'Not linked'}</Text>
                </div>
              </div>
            </div>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a screening interview first" />
          )}
        </Modal>
      </div>
    )
  }

  return (
    <div className={containerClass}>
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => {
            setIsBuilderOpen(false)
            setSelectedTemplateId(null)
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
        >
          <ArrowLeft size={14} />
          Back to Screening Interviews
        </button>
        <Button type="primary" onClick={saveDraft} loading={saving}>Save Screening Interview</Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[240px_minmax(0,1fr)_320px] gap-5 items-start">
        <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-soft-sm sticky top-0">
          <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3">Wizard Steps</Text>
          <div className="space-y-2">
            {WIZARD_STEPS.map((step) => (
              <button
                key={step.key}
                onClick={() => setActiveStep(step.key)}
                className={cn(
                  'w-full rounded-xl border px-3 py-3 text-left transition',
                  activeStep === step.key ? 'border-indigo-200 bg-indigo-50' : 'border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50',
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center', activeStep === step.key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-400')}>
                    <step.icon size={16} />
                  </div>
                  <Text className="font-bold text-slate-800">{step.label.replace(/^\d+\.\s*/, '')}</Text>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-soft-sm">
          {activeStep === 'setup' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 1</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Setup</h3>
                <Text className="text-slate-500">{guidance.guidance.description}</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Interview Name</Text>
                  <Input value={draft.name} onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Screening Type</Text>
                  <Select
                    value={draft.screening_type}
                    options={SCREENING_TYPES.map((item) => ({ value: item.value, label: item.label }))}
                    onChange={(value) => updateDraft((current) => ({ ...createDraft(value), id: current.id, name: current.name, description: current.description, evaluation: current.evaluation, routing: current.routing }))}
                  />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Duration</Text>
                  <InputNumber min={10} max={90} className="w-full" value={draft.duration_minutes} onChange={(value) => updateDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Status</Text>
                  <Select value={draft.is_active ? 'active' : 'archived'} options={[{ value: 'active', label: 'Active' }, { value: 'archived', label: 'Archived' }]} onChange={(value) => updateDraft((current) => ({ ...current, is_active: value === 'active' }))} />
                </div>
                <div className="md:col-span-2">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Description</Text>
                  <TextArea rows={4} value={draft.description} onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
                </div>
              </div>
            </div>
          )}

          {activeStep === 'question-flow' && (
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 2</Text>
                  <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Question Flow</h3>
                  <Text className="text-slate-500">Attach question bank items, add custom screening questions, and control order.</Text>
                </div>
                <div className="flex items-center gap-2">
                  <Select
                    className="w-64"
                    placeholder="Attach from Question Bank"
                    options={questionBankOptions.map((item) => ({ value: item.value, label: item.label }))}
                    onChange={addQuestionFromBank}
                    showSearch
                    optionFilterProp="label"
                  />
                  <Button icon={<Plus size={14} />} onClick={addQuestion}>Add Custom</Button>
                </div>
              </div>

              <div className="space-y-4">
                {draft.question_flow.questions.map((question, index) => (
                  <div key={question.id} className="rounded-2xl border border-slate-100 p-4">
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <Text className="font-bold text-slate-800">Question {index + 1}</Text>
                      <div className="flex items-center gap-2">
                        <Button size="small" icon={<ArrowUp size={12} />} onClick={() => moveQuestion(question.id, 'up')} disabled={index === 0} />
                        <Button size="small" icon={<ArrowDown size={12} />} onClick={() => moveQuestion(question.id, 'down')} disabled={index === draft.question_flow.questions.length - 1} />
                        <Button size="small" danger icon={<Trash2 size={12} />} onClick={() => updateDraft((current) => ({ ...current, question_flow: { questions: current.question_flow.questions.filter((item) => item.id !== question.id) } }))} />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 gap-4">
                      <Input value={question.title} onChange={(event) => updateQuestion(question.id, { title: event.target.value })} placeholder="Question title" />
                      <TextArea rows={3} value={question.prompt} onChange={(event) => updateQuestion(question.id, { prompt: event.target.value })} placeholder="Question prompt" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeStep === 'evaluation' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 3</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Evaluation</h3>
                <Text className="text-slate-500">Attach a scorecard and define pass or reject thresholds.</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-3">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Scorecard Template</Text>
                  <Select allowClear value={draft.evaluation.scorecard_template_id || undefined} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value || '' } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Pass Threshold</Text>
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.pass_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_threshold: Number(value || 0) } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Reject Threshold</Text>
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.reject_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_threshold: Number(value || 0) } }))} />
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Linked Scorecard</Text>
                <Text className="font-bold text-slate-800">{selectedScorecard?.name || 'No scorecard attached'}</Text>
              </div>
            </div>
          )}

          {activeStep === 'routing' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 4</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Routing</h3>
                <Text className="text-slate-500">Define how passed, rejected, and borderline candidates move through the flow.</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Pass Action</Text>
                  <Select value={draft.routing.pass_action} options={[{ value: 'move_to_next_interview', label: 'Move to Next Interview' }, { value: 'manual_review', label: 'Manual Review' }]} onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, pass_action: value } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Next Stage</Text>
                  <Input value={draft.routing.next_stage_name} onChange={(event) => updateDraft((current) => ({ ...current, routing: { ...current.routing, next_stage_name: event.target.value } }))} />
                </div>
                <div className="md:col-span-2">
                  <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                    <div>
                      <Text className="block font-bold text-slate-800">Manual Review Enabled</Text>
                      <Text className="text-slate-500">Borderline candidates can be paused for recruiter review.</Text>
                    </div>
                    <Select value={draft.routing.manual_review_enabled ? 'yes' : 'no'} options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, manual_review_enabled: value === 'yes' } }))} className="w-24" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeStep === 'preview' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 5</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Usage / Preview</h3>
                <Text className="text-slate-500">Review screening flow, scorecard linkage, and routing before saving.</Text>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl border border-slate-100 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Summary</Text>
                  <Text className="block mt-2 font-bold text-slate-800">{draft.name || 'Untitled Screening Interview'}</Text>
                  <Text className="text-slate-500">{draft.screening_type.replace(/_/g, ' ')} · {draft.duration_minutes}m</Text>
                </div>
                <div className="rounded-xl border border-slate-100 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Routing</Text>
                  <Text className="block mt-2 font-bold text-slate-800">{draft.routing.pass_action.replace(/_/g, ' ')}</Text>
                  <Text className="text-slate-500">Next stage: {draft.routing.next_stage_name}</Text>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-5">
            <Button disabled={stepIndex === 0} onClick={() => setActiveStep(WIZARD_STEPS[Math.max(0, stepIndex - 1)].key)}>Back</Button>
            <div className="flex items-center gap-2">
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" disabled={stepIndex === WIZARD_STEPS.length - 1} onClick={() => setActiveStep(WIZARD_STEPS[Math.min(WIZARD_STEPS.length - 1, stepIndex + 1)].key)}>Next</Button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm sticky top-0 space-y-5">
          <div>
            <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Screening Summary</Text>
            <p className="mt-2 mb-0 text-lg font-black text-slate-900">{draft.name || 'Untitled Screening Interview'}</p>
            <p className="mt-1 mb-0 text-sm text-slate-500">{draft.screening_type.replace(/_/g, ' ')} · {draft.question_flow.questions.length} questions</p>
          </div>
          <div className="rounded-xl bg-slate-950 p-4 text-white">
            <Text className="block text-[10px] font-black uppercase tracking-widest text-white/50">Candidate View</Text>
            <p className="mt-3 mb-0 text-lg font-black">{draft.name || 'Screening Interview'}</p>
            <p className="mt-1 mb-0 text-sm text-white/70">{draft.duration_minutes} minutes · {draft.question_flow.questions.length} questions</p>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</Text>
              <Text className="font-bold text-slate-800">{selectedScorecard?.name || 'No scorecard linked'}</Text>
            </div>
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Thresholds</Text>
              <Text className="font-bold text-slate-800">Pass {draft.evaluation.pass_threshold} · Reject {draft.evaluation.reject_threshold}</Text>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
