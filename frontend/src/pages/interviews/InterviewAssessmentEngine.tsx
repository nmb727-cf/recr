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
  Brain,
  Copy,
  Eye,
  FileText,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type AssessmentEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'structure' | 'question-flow' | 'evaluation' | 'preview'

type AssessmentSubtype =
  | 'mcq_assessment'
  | 'aptitude_test'
  | 'case_study'
  | 'take_home_assignment'
  | 'work_sample_test'
  | 'language_assessment'
  | 'cognitive_assessment'
  | 'psychometric_assessment'
  | 'file_submission_assignment'

type AssessmentSection = {
  id: string
  title: string
  instructions: string
  question_blocks: string[]
  time_per_section_minutes: number
  file_submission_allowed: boolean
  mandatory: boolean
}

type AssessmentQuestion = {
  id: string
  source: 'question_bank' | 'custom'
  title: string
  prompt: string
  question_bank_id: string
  mandatory: boolean
  task_tags: string[]
  evaluator_note: string
}

type AssessmentDraft = {
  id: string | null
  name: string
  assessment_type: AssessmentSubtype
  backend_interview_type: string
  duration_minutes: number
  description: string
  difficulty_level: 'easy' | 'medium' | 'hard'
  role_domain_tags: string[]
  is_active: boolean
  structure: {
    sections: AssessmentSection[]
  }
  question_flow: {
    questions: AssessmentQuestion[]
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
  { key: 'structure', label: '2. Structure', icon: Layers3 },
  { key: 'question-flow', label: '3. Question / Task Flow', icon: FileText },
  { key: 'evaluation', label: '4. Evaluation', icon: ShieldCheck },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const ASSESSMENT_TYPES: Array<{
  value: AssessmentSubtype
  label: string
  backendType: string
  aliases: string[]
  guidance: {
    title: string
    description: string
    blocks: string[]
    focus: string[]
    fileSubmission: boolean
  }
}> = [
  {
    value: 'mcq_assessment',
    label: 'MCQ Assessment',
    backendType: 'mcq_assessment',
    aliases: [],
    guidance: {
      title: 'MCQ Assessment',
      description: 'Use objective question blocks with clear answer validation and time-boxed sections.',
      blocks: ['Objective questions', 'Knowledge coverage', 'Auto-evaluation'],
      focus: ['Accuracy', 'Breadth', 'Time discipline'],
      fileSubmission: false,
    },
  },
  {
    value: 'aptitude_test',
    label: 'Aptitude Test',
    backendType: 'aptitude',
    aliases: ['aptitude_test'],
    guidance: {
      title: 'Aptitude Test',
      description: 'Use timed sections focused on reasoning, logic, and quantitative accuracy.',
      blocks: ['Numerical reasoning', 'Logical reasoning', 'Verbal reasoning'],
      focus: ['Speed', 'Reasoning accuracy', 'Baseline capability'],
      fileSubmission: false,
    },
  },
  {
    value: 'case_study',
    label: 'Case Study',
    backendType: 'case_study',
    aliases: [],
    guidance: {
      title: 'Case Study',
      description: 'Use long-form sections with instructions, task context, and rubric-driven review.',
      blocks: ['Scenario brief', 'Analysis task', 'Recommendation summary'],
      focus: ['Structure', 'Decision quality', 'Communication'],
      fileSubmission: false,
    },
  },
  {
    value: 'take_home_assignment',
    label: 'Take Home Assignment',
    backendType: 'take_home_assignment',
    aliases: [],
    guidance: {
      title: 'Take Home Assignment',
      description: 'Support task instructions, file or link submission, and rubric-based manual review.',
      blocks: ['Assignment brief', 'Deliverables', 'Submission instructions'],
      focus: ['Execution quality', 'Completeness', 'Documentation'],
      fileSubmission: true,
    },
  },
  {
    value: 'work_sample_test',
    label: 'Work Sample Test',
    backendType: 'work_sample',
    aliases: ['work_sample_test'],
    guidance: {
      title: 'Work Sample Test',
      description: 'Use realistic job-like tasks with clear evaluation dimensions and submission requirements.',
      blocks: ['Task brief', 'Expected output', 'Review criteria'],
      focus: ['Role realism', 'Task execution', 'Output quality'],
      fileSubmission: true,
    },
  },
  {
    value: 'language_assessment',
    label: 'Language Assessment',
    backendType: 'language',
    aliases: ['language_assessment'],
    guidance: {
      title: 'Language Assessment',
      description: 'Use comprehension, grammar, and communication prompts with structured scoring.',
      blocks: ['Reading / writing', 'Comprehension', 'Communication'],
      focus: ['Clarity', 'Grammar', 'Language fluency'],
      fileSubmission: false,
    },
  },
  {
    value: 'cognitive_assessment',
    label: 'Cognitive Assessment',
    backendType: 'cognitive',
    aliases: ['cognitive_assessment'],
    guidance: {
      title: 'Cognitive Assessment',
      description: 'Use reasoning and pattern-based tasks with objective scoring shells.',
      blocks: ['Pattern recognition', 'Reasoning', 'Decision logic'],
      focus: ['Reasoning', 'Cognitive speed', 'Abstract problem solving'],
      fileSubmission: false,
    },
  },
  {
    value: 'psychometric_assessment',
    label: 'Psychometric Assessment',
    backendType: 'psychometric',
    aliases: ['psychometric_assessment'],
    guidance: {
      title: 'Psychometric Assessment',
      description: 'Use behavioral scoring sections and interpretation guidelines rather than strict pass/fail logic.',
      blocks: ['Behavioral profile', 'Trait interpretation', 'Fit indicators'],
      focus: ['Behavioral signal', 'Trait consistency', 'Fit interpretation'],
      fileSubmission: false,
    },
  },
  {
    value: 'file_submission_assignment',
    label: 'File Submission Assignment',
    backendType: 'take_home_assignment',
    aliases: ['file_submission_assignment'],
    guidance: {
      title: 'File Submission Assignment',
      description: 'Use upload-friendly sections with explicit file submission and manual review expectations.',
      blocks: ['Submission brief', 'File requirements', 'Reviewer instructions'],
      focus: ['Submission quality', 'Completion', 'Reviewer consistency'],
      fileSubmission: true,
    },
  },
]

const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createSection(overrides: Partial<AssessmentSection> = {}): AssessmentSection {
  return {
    id: makeId('assessment-section'),
    title: '',
    instructions: '',
    question_blocks: [],
    time_per_section_minutes: 15,
    file_submission_allowed: false,
    mandatory: true,
    ...overrides,
  }
}

function createQuestion(overrides: Partial<AssessmentQuestion> = {}): AssessmentQuestion {
  return {
    id: makeId('assessment-question'),
    source: 'custom',
    title: '',
    prompt: '',
    question_bank_id: '',
    mandatory: true,
    task_tags: [],
    evaluator_note: '',
    ...overrides,
  }
}

function createDraft(type: AssessmentSubtype = 'mcq_assessment'): AssessmentDraft {
  const config = ASSESSMENT_TYPES.find((item) => item.value === type) || ASSESSMENT_TYPES[0]
  return {
    id: null,
    name: '',
    assessment_type: config.value,
    backend_interview_type: config.backendType,
    duration_minutes: 45,
    description: '',
    difficulty_level: 'medium',
    role_domain_tags: [],
    is_active: true,
    structure: {
      sections: [
        createSection({
          title: config.guidance.blocks[0] || '',
          question_blocks: config.guidance.blocks,
          file_submission_allowed: config.guidance.fileSubmission,
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

function parseTemplate(record: any): AssessmentDraft {
  const meta = record?.metadata?.assessment_engine || {}
  const setup = meta.setup || {}
  const structure = meta.structure || {}
  const flow = meta.question_flow || {}
  const evaluation = meta.evaluation || {}
  const inferredType = (setup.assessment_type || meta.assessment_type || 'mcq_assessment') as AssessmentSubtype
  const mapped = ASSESSMENT_TYPES.find((item) => item.value === inferredType) || ASSESSMENT_TYPES[0]

  return {
    id: record.id,
    name: record.name || '',
    assessment_type: mapped.value,
    backend_interview_type: record.interview_type || mapped.backendType,
    duration_minutes: record.duration_minutes || 45,
    description: record.description || '',
    difficulty_level: setup.difficulty_level || 'medium',
    role_domain_tags: Array.isArray(setup.role_domain_tags) ? setup.role_domain_tags : [],
    is_active: record.is_active ?? true,
    structure: {
      sections: Array.isArray(structure.sections) && structure.sections.length
        ? structure.sections.map((section: any) => ({
            id: section.id || makeId('assessment-section'),
            title: section.title || '',
            instructions: section.instructions || '',
            question_blocks: Array.isArray(section.question_blocks) ? section.question_blocks : [],
            time_per_section_minutes: Number(section.time_per_section_minutes ?? 15),
            file_submission_allowed: section.file_submission_allowed ?? false,
            mandatory: section.mandatory ?? true,
          }))
        : createDraft(mapped.value).structure.sections,
    },
    question_flow: {
      questions: Array.isArray(flow.questions)
        ? flow.questions.map((question: any) => ({
            id: question.id || makeId('assessment-question'),
            source: question.source || 'custom',
            title: question.title || '',
            prompt: question.prompt || question.text || '',
            question_bank_id: question.question_bank_id || '',
            mandatory: question.mandatory ?? true,
            task_tags: Array.isArray(question.task_tags) ? question.task_tags : [],
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

function serializeDraft(draft: AssessmentDraft, existing: any = {}) {
  const typeConfig = ASSESSMENT_TYPES.find((item) => item.value === draft.assessment_type) || ASSESSMENT_TYPES[0]
  const questionsPayload = draft.question_flow.questions.map((question, index) => ({
    id: question.id,
    title: question.title || `Task ${index + 1}`,
    text: question.prompt,
    source: question.source,
    question_bank_id: question.question_bank_id,
    mandatory: question.mandatory,
    task_tags: question.task_tags,
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
    instructions: draft.structure.sections.map((section) => section.instructions).filter(Boolean).join('\n\n'),
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    questions: questionsPayload,
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      assessment_engine: {
        setup: {
          assessment_type: draft.assessment_type,
          difficulty_level: draft.difficulty_level,
          role_domain_tags: draft.role_domain_tags,
        },
        structure: draft.structure,
        question_flow: draft.question_flow,
        evaluation: draft.evaluation,
        usage: existing?.metadata?.assessment_engine?.usage || {
          linked_jobs: [],
          linked_flows: [],
          linked_stages: [],
        },
        integrations: {
          template_engine: true,
          question_engine: true,
          scorecard_engine: true,
          flow_engine: true,
          outcome_engine: true,
        },
      },
      unified_template: {
        ...(existing.metadata?.unified_template || {}),
        category: 'Assessment',
        setup: { reusable_template: true },
        configuration: {
          ai_config: '',
          interviewer_config: '',
          assessment_config: draft.structure.sections.map((section) => section.instructions).filter(Boolean).join('\n\n'),
          screening_config: '',
          advanced_config: '',
        },
        scorecard: {
          scorecard_template_id: draft.evaluation.scorecard_template_id,
        },
        automation: {
          trigger_mode: 'manual_trigger',
          routing: draft.evaluation.manual_review_enabled ? 'manual_review' : 'pass_fail',
          scheduling_enabled: false,
        },
        integrations: {
          flow_engine: true,
          scorecard_engine: true,
          ai_engine: false,
          scheduling_engine: false,
        },
      },
    },
  }
}

function getAssessmentGuidance(type: AssessmentSubtype) {
  return ASSESSMENT_TYPES.find((item) => item.value === type)?.guidance || ASSESSMENT_TYPES[0].guidance
}

export default function InterviewAssessmentEngine({ embedded = false }: AssessmentEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const searchParams = new URLSearchParams(location.search)
  const requestedType = searchParams.get('type')
  const initialType = useMemo<AssessmentSubtype>(() => {
    const mapped = ASSESSMENT_TYPES.find((item) => item.backendType === requestedType || item.aliases.includes(requestedType || ''))?.value
    return mapped || 'mcq_assessment'
  }, [requestedType])

  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [saving, setSaving] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [draft, setDraft] = useState<AssessmentDraft>(createDraft(initialType))

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: questionBankData } = useApiQuery(['assessment-question-bank'], () => interviewsApi.listQuestionBank())

  const allTemplates = (templatesData as any)?.templates ?? []
  const flows = (flowsData as any)?.flows ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const questionBank = ((questionBankData as any)?.questions ?? []).filter((item: any) => Array.isArray(item.skills))
  const assessmentTemplates = allTemplates.filter((template: any) => {
    const meta = template?.metadata || {}
    return meta?.assessment_engine || meta?.unified_template?.category === 'Assessment'
  })

  const selectedTemplate = useMemo(
    () => assessmentTemplates.find((template: any) => template.id === selectedTemplateId) ?? null,
    [selectedTemplateId, assessmentTemplates],
  )

  useEffect(() => {
    if (!selectedTemplate) return
    setDraft(parseTemplate(selectedTemplate))
  }, [selectedTemplate])

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = ASSESSMENT_TYPES.find((item) => item.backendType === requestedType || item.aliases.includes(requestedType))?.value
    if (!nextType) return
    setDraft(createDraft(nextType))
    setSelectedTemplateId(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen])

  const guidance = getAssessmentGuidance(draft.assessment_type)
  const usageMap = useMemo(() => {
    return new Map<string, number>(
      assessmentTemplates.map((template: any) => {
        const meta = template?.metadata?.assessment_engine || {}
        const usage = meta.usage || {}
        const usageCount =
          (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
          (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
          (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0) +
          flows.filter((flow: any) => (flow?.stages || []).some((stage: any) => stage?.template_id === template.id)).length
        return [template.id, usageCount]
      }) as Array<[string, number]>,
    )
  }, [flows, assessmentTemplates])

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.assessment_type),
    structure: Boolean(draft.structure.sections.some((section) => section.title.trim())),
    'question-flow': Boolean(draft.question_flow.questions.length > 0),
    evaluation: Boolean(draft.evaluation.scorecard_template_id || draft.evaluation.dimension_mapping.length > 0),
    preview: true,
  }

  const updateDraft = (updater: (current: AssessmentDraft) => AssessmentDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = (type: AssessmentSubtype = initialType) => {
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
      message.success('Assessment duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to duplicate assessment')
    }
  }

  const archiveTemplate = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      message.success('Assessment archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to archive assessment')
    }
  }

  const saveDraft = async () => {
    if (!draft.name.trim()) {
      message.error('Assessment name is required')
      return
    }
    if (!draft.question_flow.questions.length) {
      message.error('Add at least one question or task')
      return
    }
    setSaving(true)
    try {
      const payload = serializeDraft(draft, selectedTemplate)
      if (selectedTemplateId) {
        await interviewsApi.updateTemplate(selectedTemplateId, payload)
        message.success('Assessment updated')
      } else {
        const response = await interviewsApi.createTemplate(payload)
        setSelectedTemplateId((response.data as any)?.data?.template?.id || null)
        message.success('Assessment created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setIsBuilderOpen(false)
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save assessment')
    } finally {
      setSaving(false)
    }
  }

  const updateSection = (sectionId: string, patch: Partial<AssessmentSection>) => {
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
        sections: [...current.structure.sections, createSection({ file_submission_allowed: guidance.fileSubmission })],
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
            task_tags: Array.isArray(source.skills) ? source.skills : [],
          }),
        ],
      },
    }))
  }

  const updateQuestion = (questionId: string, patch: Partial<AssessmentQuestion>) => {
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
  const previewUsage = selectedTemplate?.metadata?.assessment_engine?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] }

  const columns: ColumnsType<any> = [
    {
      title: 'Assessment Name',
      dataIndex: 'name',
      render: (value: string) => <Text className="font-bold text-slate-900">{value}</Text>,
    },
    {
      title: 'Assessment Type',
      render: (_, record) => {
        const meta = record?.metadata?.assessment_engine || {}
        const type = ASSESSMENT_TYPES.find((item) => item.value === meta.setup?.assessment_type)
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
        const scorecardId = record?.metadata?.assessment_engine?.evaluation?.scorecard_template_id
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
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessment Wizard</p>
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
              <p className="mt-2 text-sm text-slate-500">Define reusable assessment identity, duration, difficulty, and role/domain tags.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Assessment Name</label>
                <Input value={draft.name} placeholder="e.g. Finance Analyst Case Study" onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Assessment Type</label>
                <Select
                  value={draft.assessment_type}
                  options={ASSESSMENT_TYPES.map((item) => ({ value: item.value, label: item.label }))}
                  onChange={(value: AssessmentSubtype) => {
                    const config = ASSESSMENT_TYPES.find((item) => item.value === value) || ASSESSMENT_TYPES[0]
                    updateDraft((current) => ({
                      ...current,
                      assessment_type: value,
                      backend_interview_type: config.backendType,
                      structure: current.id ? current.structure : createDraft(value).structure,
                    }))
                  }}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Duration</label>
                <InputNumber min={15} max={240} className="w-full" addonAfter="min" value={draft.duration_minutes} onChange={(value) => updateDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Difficulty Level</label>
                <Select value={draft.difficulty_level} options={DIFFICULTY_OPTIONS} onChange={(value) => updateDraft((current) => ({ ...current, difficulty_level: value }))} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Role / Domain Tags</label>
                <Select mode="tags" value={draft.role_domain_tags} open={false} placeholder="Add role or domain tags" onChange={(value) => updateDraft((current) => ({ ...current, role_domain_tags: value }))} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Description</label>
                <TextArea rows={4} value={draft.description} placeholder="Describe the purpose and expected outcome of this assessment." onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
              </div>
            </div>
            <Card className="border-slate-200 bg-slate-50">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{guidance.title}</p>
              <p className="mt-2 text-sm text-slate-600">{guidance.description}</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question Blocks</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {guidance.blocks.map((item) => <Tag key={item}>{item}</Tag>)}
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
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Structure</p>
                <p className="mt-2 text-sm text-slate-500">Define sections, instructions, question blocks, section timing, file submission, and mandatory sections.</p>
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
                    <Input value={section.title} placeholder="e.g. Scenario brief" onChange={(event) => updateSection(section.id, { title: event.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Time Per Section</label>
                    <InputNumber min={5} max={180} className="w-full" addonAfter="min" value={section.time_per_section_minutes} onChange={(value) => updateSection(section.id, { time_per_section_minutes: Number(value || 0) })} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Instructions</label>
                    <TextArea rows={3} value={section.instructions} placeholder="Instructions for the candidate in this section." onChange={(event) => updateSection(section.id, { instructions: event.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Question Blocks</label>
                    <Select mode="tags" value={section.question_blocks} open={false} placeholder="Add question blocks" onChange={(value) => updateSection(section.id, { question_blocks: value })} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">File Submission</label>
                      <div className="flex h-8 items-center">
                        <Switch checked={section.file_submission_allowed} onChange={(checked) => updateSection(section.id, { file_submission_allowed: checked })} />
                      </div>
                    </div>
                    <div>
                      <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Mandatory</label>
                      <div className="flex h-8 items-center">
                        <Switch checked={section.mandatory} onChange={(checked) => updateSection(section.id, { mandatory: checked })} />
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className={cn(activeStep === 'question-flow' ? 'block space-y-6' : 'hidden')}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Question / Task Flow</p>
                <p className="mt-2 text-sm text-slate-500">Attach reusable questions from Question Bank or add custom questions and tasks.</p>
              </div>
              <Space>
                <Select
                  showSearch
                  placeholder="Attach from Question Bank"
                  className="min-w-[260px]"
                  options={questionBank.map((question: any) => ({ value: question.id, label: question.question_title }))}
                  onChange={(value) => addQuestionFromBank(value)}
                />
                <Button icon={<Plus size={14} />} onClick={addCustomQuestion}>Add Custom Task</Button>
              </Space>
            </div>
            {draft.question_flow.questions.length === 0 ? (
              <Empty description="No questions or tasks attached yet" />
            ) : (
              <div className="space-y-4">
                {draft.question_flow.questions.map((question, index) => (
                  <Card key={question.id} className="border-slate-200">
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Tag color={question.source === 'question_bank' ? 'blue' : 'default'}>
                          {question.source === 'question_bank' ? 'Question Bank' : 'Custom'}
                        </Tag>
                        <Text className="font-bold text-slate-900">Task {index + 1}</Text>
                      </div>
                      <Space size={4}>
                        <Button size="small" icon={<ArrowUp size={13} />} disabled={index === 0} onClick={() => moveQuestion(question.id, -1)} />
                        <Button size="small" icon={<ArrowDown size={13} />} disabled={index === draft.question_flow.questions.length - 1} onClick={() => moveQuestion(question.id, 1)} />
                        <Button danger size="small" icon={<Trash2 size={13} />} onClick={() => removeQuestion(question.id)}>Remove</Button>
                      </Space>
                    </div>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Task Title</label>
                        <Input value={question.title} placeholder="e.g. Analyze the candidate case brief" onChange={(event) => updateQuestion(question.id, { title: event.target.value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Mandatory</label>
                        <div className="flex h-8 items-center">
                          <Switch checked={question.mandatory} onChange={(checked) => updateQuestion(question.id, { mandatory: checked })} />
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Prompt</label>
                        <TextArea rows={4} value={question.prompt} placeholder="Assessment task or question prompt" onChange={(event) => updateQuestion(question.id, { prompt: event.target.value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Task Tags</label>
                        <Select mode="tags" value={question.task_tags} open={false} placeholder="Add tags" onChange={(value) => updateQuestion(question.id, { task_tags: value })} />
                      </div>
                      <div>
                        <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Evaluator Note</label>
                        <Input value={question.evaluator_note} placeholder="What should reviewers look for?" onChange={(event) => updateQuestion(question.id, { evaluator_note: event.target.value })} />
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
              <p className="mt-2 text-sm text-slate-500">Attach scorecard template and define pass, reject, and manual review rules.</p>
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
                <Select mode="tags" value={draft.evaluation.dimension_mapping} open={false} placeholder="Map assessment dimensions" onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, dimension_mapping: value } }))} />
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
                    <p className="mt-1 text-sm text-slate-500">Enable manual review for borderline assessment results.</p>
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
              <p className="mt-2 text-sm text-slate-500">Review the assessment summary, linked usage, and reusable configuration before saving.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessment Type</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{ASSESSMENT_TYPES.find((item) => item.value === draft.assessment_type)?.label}</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.duration_minutes} minutes</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Questions / Tasks</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.question_flow.questions.length}</p>
              </Card>
              <Card className="border-slate-200">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage Count</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{selectedTemplateId ? usageMap.get(selectedTemplateId) || 0 : 0}</p>
              </Card>
            </div>

            <Card className="border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Preview Summary</p>
              <p className="mt-3 text-lg font-black text-slate-900">{draft.name || 'Untitled assessment'}</p>
              <p className="mt-2 text-sm text-slate-600">{draft.description || guidance.description}</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Sections</p>
                  <div className="mt-2 space-y-2">
                    {draft.structure.sections.map((section) => (
                      <div key={section.id} className="rounded-2xl border border-slate-200 p-3">
                        <p className="text-sm font-bold text-slate-900">{section.title || 'Untitled section'}</p>
                        <p className="mt-1 text-xs text-slate-500">{section.question_blocks.join(', ') || 'No question blocks added'}</p>
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
                  Save Assessment
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
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessments</p>
          <p className="mt-1 text-xs text-slate-500">Reusable assessment templates connected to question, scorecard, flow, and outcome systems.</p>
        </div>
        <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>
          Create Assessment
        </Button>
      </div>
      <Table
        rowKey="id"
        loading={isLoading}
        columns={columns}
        dataSource={assessmentTemplates}
        pagination={false}
        locale={{
          emptyText: (
            <Empty description="No assessments yet">
              <Button type="primary" onClick={() => openCreate(initialType)}>Create Assessment</Button>
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
            <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>Back to Assessments</Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Assessment</Button>
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
            <Brain size={18} />
          </div>
          <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">Assessments</h1>
        </div>
        <Space>
          {isBuilderOpen ? (
            <>
              <Button onClick={() => setIsBuilderOpen(false)}>Back to Assessments</Button>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Assessment</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/interviews/types')}>Registry</Button>
              <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>Create Assessment</Button>
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
  draft: AssessmentDraft
  scorecardName: string
  onClose: () => void
}) {
  const assessmentType = ASSESSMENT_TYPES.find((item) => item.value === draft.assessment_type)
  return (
    <Card
      className={cn(
        'fixed inset-x-0 top-20 z-[100] mx-auto hidden w-[min(900px,calc(100vw-48px))] rounded-3xl border border-slate-200 shadow-2xl',
        open ? 'block' : 'hidden',
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessment Preview</p>
          <p className="mt-2 text-lg font-black text-slate-900">{draft.name || 'Untitled assessment'}</p>
        </div>
        <Button onClick={onClose}>Close</Button>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-3xl bg-slate-950 p-6 text-white">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessment Summary</p>
          <p className="mt-3 text-2xl font-black">{assessmentType?.label}</p>
          <p className="mt-2 text-sm text-slate-300">{draft.role_domain_tags.join(', ') || 'No role / domain tags set'}</p>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Duration</p>
              <p className="mt-1 text-sm font-bold">{draft.duration_minutes}m</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Difficulty</p>
              <p className="mt-1 text-sm font-bold">{draft.difficulty_level}</p>
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
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Task Sequence</p>
            <div className="mt-3 space-y-2">
              {draft.question_flow.questions.length ? draft.question_flow.questions.map((question, index) => (
                <div key={question.id} className="rounded-2xl border border-slate-200 p-3">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Task {index + 1}</p>
                  <p className="mt-1 text-sm font-bold text-slate-900">{question.title || 'Untitled task'}</p>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{question.prompt || 'Prompt pending'}</p>
                </div>
              )) : <Empty description="No tasks added" />}
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
