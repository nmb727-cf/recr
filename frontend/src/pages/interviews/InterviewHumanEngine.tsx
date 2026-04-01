import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Briefcase,
  Copy,
  Eye,
  Heart,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
  UserCheck,
  Users,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type HumanEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'structure' | 'question-flow' | 'evaluation' | 'preview'

type HumanSubtype =
  | 'hr_interview'
  | 'hiring_manager_interview'
  | 'behavioral_interview'
  | 'panel_interview'
  | 'stakeholder_interview'
  | 'final_round'
  | 'leadership_interview'
  | 'executive_interview'
  | 'culture_fit'

type HumanSection = {
  id: string
  title: string
  topics: string[]
  focus_areas: string[]
  mandatory: boolean
  interviewer_notes: string
  optional_guidelines: string
}

type HumanQuestion = {
  id: string
  source: 'question_bank' | 'custom'
  title: string
  prompt: string
  question_bank_id: string
  mandatory: boolean
  topic_tags: string[]
  evaluator_note: string
}

type HumanDraft = {
  id: string | null
  name: string
  human_type: HumanSubtype
  backend_interview_type: string
  duration_minutes: number
  description: string
  level_seniority: 'junior' | 'mid' | 'senior' | 'lead' | 'executive'
  role_department: string
  is_active: boolean
  structure: {
    sections: HumanSection[]
  }
  question_flow: {
    questions: HumanQuestion[]
  }
  evaluation: {
    scorecard_template_id: string
    dimension_mapping: string[]
    pass_threshold: number
    reject_threshold: number
    manual_review_enabled: boolean
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'structure', label: '2. Interview Structure', icon: Layers3 },
  { key: 'question-flow', label: '3. Question / Topic Flow', icon: Briefcase },
  { key: 'evaluation', label: '4. Evaluation', icon: ShieldCheck },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const HUMAN_TYPES: Array<{
  value: HumanSubtype
  label: string
  backendType: string
  aliases: string[]
  icon: React.ElementType
  guidance: {
    title: string
    topics: string[]
    focus: string[]
    description: string
  }
}> = [
  {
    value: 'hr_interview',
    label: 'HR Interview',
    backendType: 'hr_interview',
    aliases: [],
    icon: UserCheck,
    guidance: {
      title: 'HR Interview',
      topics: ['Motivation', 'Culture fit', 'Compensation alignment'],
      focus: ['Candidate expectations', 'Policy fit', 'Joining readiness'],
      description: 'Use HR-led topics to validate motivation, fit, and process readiness.',
    },
  },
  {
    value: 'hiring_manager_interview',
    label: 'Hiring Manager Interview',
    backendType: 'hiring_manager',
    aliases: ['hiring_manager_interview'],
    icon: Briefcase,
    guidance: {
      title: 'Hiring Manager Focus',
      topics: ['Role fit', 'Delivery expectations', 'Team collaboration'],
      focus: ['Role ownership', 'Execution confidence', 'Fit with team context'],
      description: 'Structure this around manager expectations, role delivery, and team context.',
    },
  },
  {
    value: 'behavioral_interview',
    label: 'Behavioral Interview',
    backendType: 'behavioral',
    aliases: ['behavioral_interview'],
    icon: Heart,
    guidance: {
      title: 'Behavioral Interview',
      topics: ['Past behavior', 'Collaboration', 'Conflict handling'],
      focus: ['STAR quality', 'Ownership', 'Reflection and learning'],
      description: 'Bias toward competency-based prompts with strong STAR evidence.',
    },
  },
  {
    value: 'panel_interview',
    label: 'Panel Interview',
    backendType: 'panel',
    aliases: ['panel_interview'],
    icon: Users,
    guidance: {
      title: 'Panel Interview',
      topics: ['Multi-evaluator coverage', 'Cross-functional fit', 'Decision confidence'],
      focus: ['Dimension ownership', 'Panel coordination', 'Balanced recommendation'],
      description: 'Use section structure to assign focus areas across multiple interviewers.',
    },
  },
  {
    value: 'stakeholder_interview',
    label: 'Stakeholder Interview',
    backendType: 'stakeholder',
    aliases: ['stakeholder_interview'],
    icon: Users,
    guidance: {
      title: 'Stakeholder Interview',
      topics: ['Cross-functional collaboration', 'Influence', 'Expectation management'],
      focus: ['Stakeholder confidence', 'Communication quality', 'Operating style'],
      description: 'Use this for cross-functional rounds where stakeholder trust matters.',
    },
  },
  {
    value: 'final_round',
    label: 'Final Round',
    backendType: 'final_round',
    aliases: [],
    icon: ShieldCheck,
    guidance: {
      title: 'Final Round',
      topics: ['Decision readiness', 'Risk check', 'Offer confidence'],
      focus: ['Final signal quality', 'Hiring risk', 'Executive summary'],
      description: 'Center this round on final decision quality and remaining concerns.',
    },
  },
  {
    value: 'leadership_interview',
    label: 'Leadership Interview',
    backendType: 'leadership',
    aliases: ['leadership_interview'],
    icon: Briefcase,
    guidance: {
      title: 'Leadership Interview',
      topics: ['Leadership style', 'Team scaling', 'Decision making'],
      focus: ['Ownership', 'Influence', 'Change leadership'],
      description: 'Use leadership-oriented sections to assess team, strategy, and decision quality.',
    },
  },
  {
    value: 'executive_interview',
    label: 'Executive Interview',
    backendType: 'executive',
    aliases: ['executive_interview'],
    icon: Briefcase,
    guidance: {
      title: 'Executive Interview',
      topics: ['Strategic thinking', 'Executive presence', 'Business alignment'],
      focus: ['Strategic judgment', 'Communication to leadership', 'Risk framing'],
      description: 'This round should validate executive communication, business context, and leadership maturity.',
    },
  },
  {
    value: 'culture_fit',
    label: 'Culture Fit',
    backendType: 'culture_fit',
    aliases: ['cultural_fit'],
    icon: Heart,
    guidance: {
      title: 'Culture Fit',
      topics: ['Values alignment', 'Working style', 'Team compatibility'],
      focus: ['Behavioral alignment', 'Team norms', 'Interpersonal fit'],
      description: 'Use values and work-style prompts to understand long-term fit.',
    },
  },
]

const LEVEL_OPTIONS = [
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
  { value: 'executive', label: 'Executive' },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createSection(overrides: Partial<HumanSection> = {}): HumanSection {
  return {
    id: makeId('human-section'),
    title: '',
    topics: [],
    focus_areas: [],
    mandatory: true,
    interviewer_notes: '',
    optional_guidelines: '',
    ...overrides,
  }
}

function createQuestion(overrides: Partial<HumanQuestion> = {}): HumanQuestion {
  return {
    id: makeId('human-question'),
    source: 'custom',
    title: '',
    prompt: '',
    question_bank_id: '',
    mandatory: true,
    topic_tags: [],
    evaluator_note: '',
    ...overrides,
  }
}

function createDraft(type: HumanSubtype = 'hr_interview'): HumanDraft {
  const config = HUMAN_TYPES.find((item) => item.value === type) || HUMAN_TYPES[0]
  return {
    id: null,
    name: '',
    human_type: config.value,
    backend_interview_type: config.backendType,
    duration_minutes: 45,
    description: '',
    level_seniority: 'mid',
    role_department: '',
    is_active: true,
    structure: {
      sections: [
        createSection({
          title: config.guidance.topics[0] || '',
          topics: config.guidance.topics,
          focus_areas: config.guidance.focus,
        }),
      ],
    },
    question_flow: {
      questions: [],
    },
    evaluation: {
      scorecard_template_id: '',
      dimension_mapping: [],
      pass_threshold: 75,
      reject_threshold: 45,
      manual_review_enabled: true,
    },
  }
}

function parseTemplate(record: any): HumanDraft {
  const meta = record?.metadata?.human_interview || {}
  const setup = meta.setup || {}
  const structure = meta.structure || {}
  const flow = meta.question_flow || {}
  const evaluation = meta.evaluation || {}
  const inferredType = (setup.human_type || meta.human_type || 'hr_interview') as HumanSubtype
  const mapped = HUMAN_TYPES.find((item) => item.value === inferredType) || HUMAN_TYPES[0]

  return {
    id: record.id,
    name: record.name || '',
    human_type: mapped.value,
    backend_interview_type: record.interview_type || mapped.backendType,
    duration_minutes: record.duration_minutes || 45,
    description: record.description || '',
    level_seniority: setup.level_seniority || 'mid',
    role_department: setup.role_department || '',
    is_active: record.is_active ?? true,
    structure: {
      sections: Array.isArray(structure.sections) && structure.sections.length
        ? structure.sections.map((section: any) => ({
            id: section.id || makeId('human-section'),
            title: section.title || '',
            topics: Array.isArray(section.topics) ? section.topics : [],
            focus_areas: Array.isArray(section.focus_areas) ? section.focus_areas : [],
            mandatory: section.mandatory ?? true,
            interviewer_notes: section.interviewer_notes || '',
            optional_guidelines: section.optional_guidelines || '',
          }))
        : createDraft(mapped.value).structure.sections,
    },
    question_flow: {
      questions: Array.isArray(flow.questions)
        ? flow.questions.map((question: any) => ({
            id: question.id || makeId('human-question'),
            source: question.source || 'custom',
            title: question.title || '',
            prompt: question.prompt || question.text || '',
            question_bank_id: question.question_bank_id || '',
            mandatory: question.mandatory ?? true,
            topic_tags: Array.isArray(question.topic_tags) ? question.topic_tags : [],
            evaluator_note: question.evaluator_note || '',
          }))
        : [],
    },
    evaluation: {
      scorecard_template_id: evaluation.scorecard_template_id || meta.scorecard_template_id || '',
      dimension_mapping: Array.isArray(evaluation.dimension_mapping) ? evaluation.dimension_mapping : [],
      pass_threshold: Number(evaluation.pass_threshold ?? 75),
      reject_threshold: Number(evaluation.reject_threshold ?? 45),
      manual_review_enabled: evaluation.manual_review_enabled ?? true,
    },
  }
}

function serializeDraft(draft: HumanDraft, existing: any = {}) {
  const typeConfig = HUMAN_TYPES.find((item) => item.value === draft.human_type) || HUMAN_TYPES[0]
  const questionsPayload = draft.question_flow.questions.map((question, index) => ({
    id: question.id,
    title: question.title || `Question ${index + 1}`,
    text: question.prompt,
    source: question.source,
    question_bank_id: question.question_bank_id,
    mandatory: question.mandatory,
    topic_tags: question.topic_tags,
    evaluator_note: question.evaluator_note,
    type: 'text',
    order_index: index,
    duration: 0,
    options: [],
  }))

  return {
    name: draft.name,
    description: draft.description,
    interview_type: typeConfig.backendType,
    duration_minutes: draft.duration_minutes,
    instructions: draft.structure.sections.map((section) => section.interviewer_notes).filter(Boolean).join('\n\n'),
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    questions: questionsPayload,
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      human_interview: {
        setup: {
          human_type: draft.human_type,
          level_seniority: draft.level_seniority,
          role_department: draft.role_department,
        },
        structure: draft.structure,
        question_flow: draft.question_flow,
        evaluation: draft.evaluation,
        usage: existing?.metadata?.human_interview?.usage || {
          linked_jobs: [],
          linked_flows: [],
          linked_stages: [],
        },
        integrations: {
          template_engine: true,
          scorecard_engine: true,
          question_engine: true,
          flow_engine: true,
          scheduling_engine: true,
          outcome_engine: true,
        },
      },
      unified_template: {
        ...(existing.metadata?.unified_template || {}),
        category: 'Human',
        setup: { reusable_template: true },
        configuration: {
          ai_config: '',
          interviewer_config: draft.structure.sections.map((section) => section.interviewer_notes).filter(Boolean).join('\n\n'),
          assessment_config: '',
          screening_config: '',
          advanced_config: '',
        },
        scorecard: {
          scorecard_template_id: draft.evaluation.scorecard_template_id,
        },
        automation: {
          trigger_mode: 'manual_trigger',
          routing: draft.evaluation.manual_review_enabled ? 'manual_review' : 'pass_fail',
          scheduling_enabled: true,
        },
        integrations: {
          flow_engine: true,
          scorecard_engine: true,
          ai_engine: false,
          scheduling_engine: true,
        },
      },
    },
  }
}

function getHumanGuidance(type: HumanSubtype) {
  return HUMAN_TYPES.find((item) => item.value === type)?.guidance || HUMAN_TYPES[0].guidance
}

export default function InterviewHumanEngine({ embedded = false }: HumanEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const searchParams = new URLSearchParams(location.search)
  const requestedType = searchParams.get('type')
  const initialType = useMemo<HumanSubtype>(() => {
    const mapped = HUMAN_TYPES.find((item) => item.backendType === requestedType || item.aliases.includes(requestedType || ''))?.value
    return mapped || 'hr_interview'
  }, [requestedType])

  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [saving, setSaving] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [draft, setDraft] = useState<HumanDraft>(createDraft(initialType))

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: questionBankData } = useApiQuery(['human-question-bank'], () => interviewsApi.listQuestionBank())

  const allTemplates = (templatesData as any)?.templates ?? []
  const flows = (flowsData as any)?.flows ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const questionBank = ((questionBankData as any)?.questions ?? []).filter((item: any) => Array.isArray(item.skills))
  const humanTemplates = allTemplates.filter((template: any) => {
    const meta = template?.metadata || {}
    return meta?.human_interview || meta?.unified_template?.category === 'Human'
  })

  const selectedTemplate = useMemo(
    () => humanTemplates.find((template: any) => template.id === selectedTemplateId) ?? null,
    [selectedTemplateId, humanTemplates],
  )

  useEffect(() => {
    if (!selectedTemplate) return
    setDraft(parseTemplate(selectedTemplate))
  }, [selectedTemplate])

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = HUMAN_TYPES.find((item) => item.backendType === requestedType || item.aliases.includes(requestedType))?.value
    if (!nextType) return
    setDraft(createDraft(nextType))
    setSelectedTemplateId(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen])

  const guidance = getHumanGuidance(draft.human_type)
  const usageMap = useMemo(() => {
    return new Map<string, number>(
      humanTemplates.map((template: any) => {
        const meta = template?.metadata?.human_interview || {}
        const usage = meta.usage || {}
        const usageCount =
          (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
          (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
          (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0) +
          flows.filter((flow: any) => (flow?.stages || []).some((stage: any) => stage?.template_id === template.id)).length
        return [template.id, usageCount]
      }) as Array<[string, number]>,
    )
  }, [flows, humanTemplates])

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.human_type && draft.role_department.trim()),
    structure: Boolean(draft.structure.sections.some((section) => section.title.trim())),
    'question-flow': Boolean(draft.question_flow.questions.length > 0),
    evaluation: Boolean(draft.evaluation.scorecard_template_id || draft.evaluation.dimension_mapping.length > 0),
    preview: true,
  }

  const updateDraft = (updater: (current: HumanDraft) => HumanDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = (type: HumanSubtype = initialType) => {
    const next = createDraft(type)
    setSelectedTemplateId(null)
    setDraft(next)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = (record: any, step: WizardStep = 'setup') => {
    setSelectedTemplateId(record.id)
    setDraft(parseTemplate(record))
    setActiveStep(step)
    setIsBuilderOpen(true)
  }

  const duplicateTemplate = async (record: any) => {
    try {
      const duplicated = parseTemplate(record)
      const payload = serializeDraft({ ...duplicated, id: null, name: `${duplicated.name} Copy`, is_active: false }, record)
      await interviewsApi.createTemplate(payload)
      message.success('Human interview duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to duplicate human interview')
    }
  }

  const archiveTemplate = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      message.success('Human interview archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to archive human interview')
    }
  }

  const saveDraft = async () => {
    if (!draft.name.trim()) {
      message.error('Interview name is required')
      return
    }
    if (!draft.question_flow.questions.length) {
      message.error('Add at least one question or topic')
      return
    }
    setSaving(true)
    try {
      const payload = serializeDraft(draft, selectedTemplate)
      if (selectedTemplateId) {
        await interviewsApi.updateTemplate(selectedTemplateId, payload)
        message.success('Human interview updated')
      } else {
        const response = await interviewsApi.createTemplate(payload)
        setSelectedTemplateId((response.data as any)?.data?.template?.id || null)
        message.success('Human interview created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setIsBuilderOpen(false)
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save human interview')
    } finally {
      setSaving(false)
    }
  }

  const updateSection = (sectionId: string, patch: Partial<HumanSection>) => {
    updateDraft((current) => ({
      ...current,
      structure: {
        sections: current.structure.sections.map((section) =>
          section.id === sectionId ? { ...section, ...patch } : section,
        ),
      },
    }))
  }

  const addSection = () => {
    updateDraft((current) => ({
      ...current,
      structure: {
        sections: [...current.structure.sections, createSection()],
      },
    }))
  }

  const removeSection = (sectionId: string) => {
    updateDraft((current) => ({
      ...current,
      structure: {
        sections: current.structure.sections.length > 1
          ? current.structure.sections.filter((section) => section.id !== sectionId)
          : current.structure.sections,
      },
    }))
  }

  const addQuestionFromBank = (questionId: string) => {
    const source = questionBank.find((item: any) => item.id === questionId)
    if (!source) return
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: [
          ...current.question_flow.questions,
          createQuestion({
            source: 'question_bank',
            title: source.question_title,
            prompt: source.description || source.question_title,
            question_bank_id: source.id,
            topic_tags: Array.isArray(source.skills) ? source.skills : [],
          }),
        ],
      },
    }))
  }

  const updateQuestion = (questionId: string, patch: Partial<HumanQuestion>) => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: current.question_flow.questions.map((question) =>
          question.id === questionId ? { ...question, ...patch } : question,
        ),
      },
    }))
  }

  const addCustomQuestion = () => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: [...current.question_flow.questions, createQuestion({ source: 'custom' })],
      },
    }))
  }

  const removeQuestion = (questionId: string) => {
    updateDraft((current) => ({
      ...current,
      question_flow: {
        questions: current.question_flow.questions.filter((question) => question.id !== questionId),
      },
    }))
  }

  const moveQuestion = (questionId: string, direction: number) => {
    updateDraft((current) => {
      const index = current.question_flow.questions.findIndex((question) => question.id === questionId)
      const target = index + direction
      if (index === -1 || target < 0 || target >= current.question_flow.questions.length) return current
      const next = [...current.question_flow.questions]
      const [item] = next.splice(index, 1)
      next.splice(target, 0, item)
      return {
        ...current,
        question_flow: {
          questions: next,
        },
      }
    })
  }

  const selectedScorecard = scorecards.find((scorecard: any) => scorecard.id === draft.evaluation.scorecard_template_id) ?? null
  const previewUsage = selectedTemplate?.metadata?.human_interview?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      render: (value: string) => <Text className="font-bold text-slate-900">{value}</Text>,
    },
    {
      title: 'Interview Type',
      render: (_, record) => {
        const meta = record?.metadata?.human_interview || {}
        const type = HUMAN_TYPES.find((item) => item.value === meta.setup?.human_type)
        return <Tag color="blue">{type?.label || record.interview_type?.replace(/_/g, ' ')}</Tag>
      },
    },
    {
      title: 'Duration',
      dataIndex: 'duration_minutes',
      render: (value: number) => `${value || 0}m`,
    },
    {
      title: 'Scorecard',
      render: (_, record) => {
        const scorecardId = record?.metadata?.human_interview?.evaluation?.scorecard_template_id
        const scorecard = scorecards.find((entry: any) => entry.id === scorecardId)
        return <Text className="text-slate-600">{scorecard?.name || 'Not linked'}</Text>
      },
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'success' : 'default'}>{active ? 'Active' : 'Archived'}</Tag>,
    },
    {
      title: 'Usage Count',
      render: (_, record) => usageMap.get(record.id) || 0,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      render: (value: string) => new Date(value).toLocaleDateString(),
    },
    {
      title: 'Actions',
      render: (_, record) => (
        <Space size={4}>
          <Button size="small" onClick={() => openEdit(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateTemplate(record)} icon={<Copy size={13} />}>Duplicate</Button>
          <Button size="small" onClick={() => { setSelectedTemplateId(record.id); setDraft(parseTemplate(record)); setPreviewOpen(true) }} icon={<Eye size={13} />}>Preview</Button>
          <Button size="small" danger onClick={() => archiveTemplate(record)}>Archive</Button>
        </Space>
      ),
    },
  ]

  const builderView = (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-3">
        <div className="sticky top-0 rounded-3xl border border-slate-200 bg-white p-4 shadow-soft-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Human Interview Wizard</p>
          <div className="mt-4 space-y-2">
            {WIZARD_STEPS.map((step) => {
              const Icon = step.icon
              const isActive = step.key === activeStep
              const complete = stepCompletion[step.key]
              return (
                <button
                  key={step.key}
                  type="button"
                  onClick={() => setActiveStep(step.key)}
                  className={cn(
                    'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition-all',
                    isActive ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white hover:border-slate-300',
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('flex h-9 w-9 items-center justify-center rounded-2xl', isActive ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500')}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <p className="text-xs font-black uppercase tracking-widest text-slate-900">{step.label}</p>
                    </div>
                  </div>
                  <Tag color={complete ? 'success' : 'default'}>{complete ? 'Done' : 'Open'}</Tag>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-9">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft-sm">
          <div className={cn(activeStep === 'setup' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Setup</p>
              <p className="mt-2 text-sm text-slate-500">Define the human interview type, duration, seniority context, and role ownership.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Interview Name</label>
                <Input value={draft.name} placeholder="e.g. Leadership Final Conversation" onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Human Interview Type</label>
                <Select
                  value={draft.human_type}
                  options={HUMAN_TYPES.map((item) => ({ value: item.value, label: item.label }))}
                  onChange={(value: HumanSubtype) => {
                    const config = HUMAN_TYPES.find((item) => item.value === value) || HUMAN_TYPES[0]
                    updateDraft((current) => ({
                      ...current,
                      human_type: value,
                      backend_interview_type: config.backendType,
                      structure: current.id ? current.structure : createDraft(value).structure,
                    }))
                  }}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Duration</label>
                <InputNumber min={15} max={180} className="w-full" addonAfter="min" value={draft.duration_minutes} onChange={(value) => updateDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Level / Seniority</label>
                <Select value={draft.level_seniority} options={LEVEL_OPTIONS} onChange={(value) => updateDraft((current) => ({ ...current, level_seniority: value }))} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Role / Department</label>
                <Input value={draft.role_department} placeholder="e.g. Sales Leadership, People Operations, Customer Success" onChange={(event) => updateDraft((current) => ({ ...current, role_department: event.target.value }))} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Description</label>
                <TextArea rows={4} value={draft.description} placeholder="Describe the purpose of this human interview and what the interviewer should validate." onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
              </div>
            </div>
            <Card className="border-slate-200 bg-slate-50">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{guidance.title}</p>
              <p className="mt-2 text-sm text-slate-600">{guidance.description}</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Suggested Topics</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {guidance.topics.map((item) => <Tag key={item}>{item}</Tag>)}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Focus Areas</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {guidance.focus.map((item) => <Tag key={item} color="blue">{item}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          <div className={cn(activeStep === 'structure' ? 'block space-y-6' : 'hidden')}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Interview Structure</p>
                <p className="mt-2 text-sm text-slate-500">Define topics, focus areas, interviewer notes, optional guidelines, and section structure.</p>
              </div>
              <Button icon={<Plus size={14} />} onClick={addSection}>Add Section</Button>
            </div>
            {draft.structure.sections.map((section, index) => (
              <Card key={section.id} className="border-slate-200">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm font-black text-slate-900">Section {index + 1}</p>
                  <Button danger size="small" icon={<Trash2 size={13} />} onClick={() => removeSection(section.id)}>Remove</Button>
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Section Title</label>
                    <Input value={section.title} placeholder="e.g. Motivation and Role Alignment" onChange={(event) => updateSection(section.id, { title: event.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Mandatory</label>
                    <div className="flex h-8 items-center">
                      <Switch checked={section.mandatory} onChange={(checked) => updateSection(section.id, { mandatory: checked })} />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Topics To Assess</label>
                    <Select mode="tags" value={section.topics} open={false} placeholder="Add topics" onChange={(value) => updateSection(section.id, { topics: value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Interview Focus Areas</label>
                    <Select mode="tags" value={section.focus_areas} open={false} placeholder="Add focus areas" onChange={(value) => updateSection(section.id, { focus_areas: value })} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Interviewer Notes</label>
                    <TextArea rows={3} value={section.interviewer_notes} placeholder="Interviewer notes and expected probing direction." onChange={(event) => updateSection(section.id, { interviewer_notes: event.target.value })} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Optional Guidelines</label>
                    <TextArea rows={2} value={section.optional_guidelines} placeholder="Optional guidance for interview execution." onChange={(event) => updateSection(section.id, { optional_guidelines: event.target.value })} />
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className={cn(activeStep === 'question-flow' ? 'block space-y-6' : 'hidden')}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question / Topic Flow</p>
                <p className="mt-2 text-sm text-slate-500">Attach from Question Bank or create custom human interview questions and topics.</p>
              </div>
              <Space>
                <Select
                  showSearch
                  placeholder="Attach from Question Bank"
                  className="min-w-[260px]"
                  options={questionBank.map((question: any) => ({ value: question.id, label: question.question_title }))}
                  onChange={(value) => addQuestionFromBank(value)}
                />
                <Button icon={<Plus size={14} />} onClick={addCustomQuestion}>Add Custom Question</Button>
              </Space>
            </div>
            {draft.question_flow.questions.length === 0 ? (
              <Empty description="No questions or topics attached yet" />
            ) : (
              <div className="space-y-4">
                {draft.question_flow.questions.map((question, index) => (
                  <Card key={question.id} className="border-slate-200">
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Tag color={question.source === 'question_bank' ? 'blue' : 'default'}>
                          {question.source === 'question_bank' ? 'Question Bank' : 'Custom'}
                        </Tag>
                        <Text className="font-bold text-slate-900">Question {index + 1}</Text>
                      </div>
                      <Space size={4}>
                        <Button size="small" icon={<ArrowUp size={13} />} disabled={index === 0} onClick={() => moveQuestion(question.id, -1)} />
                        <Button size="small" icon={<ArrowDown size={13} />} disabled={index === draft.question_flow.questions.length - 1} onClick={() => moveQuestion(question.id, 1)} />
                        <Button danger size="small" icon={<Trash2 size={13} />} onClick={() => removeQuestion(question.id)}>Remove</Button>
                      </Space>
                    </div>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Question Title</label>
                        <Input value={question.title} placeholder="e.g. Stakeholder conflict example" onChange={(event) => updateQuestion(question.id, { title: event.target.value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Mandatory</label>
                        <div className="flex h-8 items-center">
                          <Switch checked={question.mandatory} onChange={(checked) => updateQuestion(question.id, { mandatory: checked })} />
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Prompt</label>
                        <TextArea rows={4} value={question.prompt} placeholder="Interview question prompt" onChange={(event) => updateQuestion(question.id, { prompt: event.target.value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Topic Tags</label>
                        <Select mode="tags" value={question.topic_tags} open={false} placeholder="Add tags" onChange={(value) => updateQuestion(question.id, { topic_tags: value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Evaluator Note</label>
                        <Input value={question.evaluator_note} placeholder="What should interviewer listen for?" onChange={(event) => updateQuestion(question.id, { evaluator_note: event.target.value })} />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <div className={cn(activeStep === 'evaluation' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Evaluation</p>
              <p className="mt-2 text-sm text-slate-500">Attach scorecard template and define pass, reject, and manual review logic.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Scorecard Template</label>
                <Select
                  allowClear
                  value={draft.evaluation.scorecard_template_id || undefined}
                  options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))}
                  onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value || '' } }))}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Dimension Mapping</label>
                <Select mode="tags" value={draft.evaluation.dimension_mapping} open={false} placeholder="Map interview dimensions" onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, dimension_mapping: value } }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Pass Threshold</label>
                <InputNumber min={0} max={100} className="w-full" addonAfter="%" value={draft.evaluation.pass_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_threshold: Number(value || 0) } }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Reject Threshold</label>
                <InputNumber min={0} max={100} className="w-full" addonAfter="%" value={draft.evaluation.reject_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_threshold: Number(value || 0) } }))} />
              </div>
              <div className="md:col-span-2">
                <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Manual Review</p>
                    <p className="mt-1 text-sm text-slate-500">Enable manual review for middle-band outcomes.</p>
                  </div>
                  <Switch checked={draft.evaluation.manual_review_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, manual_review_enabled: checked } }))} />
                </div>
              </div>
            </div>
            <Card className="border-slate-200 bg-slate-50">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{selectedScorecard?.name || 'No scorecard attached'}</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Pass</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{draft.evaluation.pass_threshold}%</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Manual Review Range</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">
                    {draft.evaluation.manual_review_enabled ? `${draft.evaluation.reject_threshold + 1}% - ${draft.evaluation.pass_threshold - 1}%` : 'Disabled'}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          <div className={cn(activeStep === 'preview' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage / Preview</p>
              <p className="mt-2 text-sm text-slate-500">Review the human interview summary, linked usage, and reusable configuration before saving.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Interview Type</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{HUMAN_TYPES.find((item) => item.value === draft.human_type)?.label}</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.duration_minutes} minutes</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Questions / Topics</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.question_flow.questions.length}</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage Count</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{selectedTemplateId ? usageMap.get(selectedTemplateId) || 0 : 0}</p>
              </Card>
            </div>

            <Card className="border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Preview Summary</p>
              <p className="mt-3 text-lg font-black text-slate-900">{draft.name || 'Untitled human interview'}</p>
              <p className="mt-2 text-sm text-slate-600">{draft.description || guidance.description}</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Sections</p>
                  <div className="mt-2 space-y-2">
                    {draft.structure.sections.map((section) => (
                      <div key={section.id} className="rounded-2xl border border-slate-200 p-3">
                        <p className="text-sm font-bold text-slate-900">{section.title || 'Untitled section'}</p>
                        <p className="mt-1 text-xs text-slate-500">{section.topics.join(', ') || 'No topics added'}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Linked Usage</p>
                  <div className="mt-2 space-y-3">
                    <div className="rounded-2xl border border-slate-200 p-3">
                      <p className="text-xs font-black uppercase tracking-widest text-slate-400">Linked Flows</p>
                      <p className="mt-2 text-sm font-bold text-slate-900">{Array.isArray(previewUsage.linked_flows) ? previewUsage.linked_flows.length : 0}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-3">
                      <p className="text-xs font-black uppercase tracking-widest text-slate-400">Linked Jobs</p>
                      <p className="mt-2 text-sm font-bold text-slate-900">{Array.isArray(previewUsage.linked_jobs) ? previewUsage.linked_jobs.length : 0}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-3">
                      <p className="text-xs font-black uppercase tracking-widest text-slate-400">Linked Stages</p>
                      <p className="mt-2 text-sm font-bold text-slate-900">{Array.isArray(previewUsage.linked_stages) ? previewUsage.linked_stages.length : 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          <div className="mt-8 flex items-center justify-between">
            <Button
              disabled={WIZARD_STEPS.findIndex((step) => step.key === activeStep) === 0}
              onClick={() => setActiveStep(WIZARD_STEPS[Math.max(WIZARD_STEPS.findIndex((step) => step.key === activeStep) - 1, 0)].key)}
            >
              Back
            </Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              {activeStep !== 'preview' ? (
                <Button
                  type="primary"
                  onClick={() => setActiveStep(WIZARD_STEPS[Math.min(WIZARD_STEPS.findIndex((step) => step.key === activeStep) + 1, WIZARD_STEPS.length - 1)].key)}
                >
                  Next
                </Button>
              ) : (
                <Button type="primary" loading={saving} onClick={saveDraft}>
                  Save Human Interview
                </Button>
              )}
            </Space>
          </div>
        </div>
      </div>
    </div>
  )

  const listView = (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Human Interviews</p>
          <p className="mt-1 text-xs text-slate-500">Reusable human interview templates connected to scorecards, questions, flows, and scheduling.</p>
        </div>
        <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>
          Create Human Interview
        </Button>
      </div>
      <Table
        rowKey="id"
        loading={isLoading}
        columns={columns}
        dataSource={humanTemplates}
        pagination={false}
        locale={{
          emptyText: (
            <Empty description="No human interviews yet">
              <Button type="primary" onClick={() => openCreate(initialType)}>Create Human Interview</Button>
            </Empty>
          ),
        }}
      />
    </div>
  )

  if (embedded) {
    return (
      <>
        {isBuilderOpen ? (
          <div className="mb-4 flex items-center justify-between">
            <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>Back to Human Interviews</Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Human Interview</Button>
            </Space>
          </div>
        ) : null}
        {isBuilderOpen ? builderView : listView}
        <PreviewCardModal
          open={previewOpen}
          draft={draft}
          scorecardName={selectedScorecard?.name || 'No scorecard linked'}
          onClose={() => setPreviewOpen(false)}
        />
      </>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
            <Users size={18} />
          </div>
          <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">Human Interviews</h1>
        </div>
        <Space>
          {isBuilderOpen ? (
            <>
              <Button onClick={() => setIsBuilderOpen(false)}>Back to Human Interviews</Button>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Human Interview</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/interviews/types')}>Registry</Button>
              <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>Create Human Interview</Button>
            </>
          )}
        </Space>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {isBuilderOpen ? builderView : listView}
      </div>
      <PreviewCardModal
        open={previewOpen}
        draft={draft}
        scorecardName={selectedScorecard?.name || 'No scorecard linked'}
        onClose={() => setPreviewOpen(false)}
      />
    </div>
  )
}

function PreviewCardModal({
  open,
  draft,
  scorecardName,
  onClose,
}: {
  open: boolean
  draft: HumanDraft
  scorecardName: string
  onClose: () => void
}) {
  const humanType = HUMAN_TYPES.find((item) => item.value === draft.human_type)
  return (
    <Card
      className={cn(
        'fixed inset-x-0 top-20 z-[100] mx-auto hidden w-[min(900px,calc(100vw-48px))] rounded-3xl border border-slate-200 shadow-2xl',
        open ? 'block' : 'hidden',
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Human Interview Preview</p>
          <p className="mt-2 text-lg font-black text-slate-900">{draft.name || 'Untitled human interview'}</p>
        </div>
        <Button onClick={onClose}>Close</Button>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-3xl bg-slate-950 p-6 text-white">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Interview Summary</p>
          <p className="mt-3 text-2xl font-black">{humanType?.label}</p>
          <p className="mt-2 text-sm text-slate-300">{draft.role_department || 'Role / department not set'}</p>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Duration</p>
              <p className="mt-1 text-sm font-bold">{draft.duration_minutes}m</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Seniority</p>
              <p className="mt-1 text-sm font-bold">{draft.level_seniority}</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Sections</p>
              <p className="mt-1 text-sm font-bold">{draft.structure.sections.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Scorecard</p>
              <p className="mt-1 text-sm font-bold">{scorecardName}</p>
            </div>
          </div>
        </div>
        <div className="space-y-3">
          <Card className="border-slate-200">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question Sequence</p>
            <div className="mt-3 space-y-2">
              {draft.question_flow.questions.length ? draft.question_flow.questions.map((question, index) => (
                <div key={question.id} className="rounded-2xl border border-slate-200 p-3">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question {index + 1}</p>
                  <p className="mt-1 text-sm font-bold text-slate-900">{question.title || 'Untitled question'}</p>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{question.prompt || 'Prompt pending'}</p>
                </div>
              )) : <Empty description="No questions added" />}
            </div>
          </Card>
          <Card className="border-slate-200">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Thresholds</p>
            <p className="mt-2 text-sm font-bold text-slate-900">Pass {draft.evaluation.pass_threshold}% · Reject {draft.evaluation.reject_threshold}%</p>
            <p className="mt-1 text-xs text-slate-500">{draft.evaluation.manual_review_enabled ? 'Manual review enabled for middle band.' : 'Manual review disabled.'}</p>
          </Card>
        </div>
      </div>
    </Card>
  )
}
