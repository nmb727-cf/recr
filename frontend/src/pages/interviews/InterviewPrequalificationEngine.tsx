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
  ClipboardList,
  Copy,
  Eye,
  GitBranch,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { prequalificationApi } from '@/api/prequalification'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type PrequalificationEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'form-builder' | 'knockout' | 'routing' | 'preview'

type PrequalSubtype =
  | 'screening_form'
  | 'knockout_form'
  | 'eligibility_form'
  | 'qualification_form'
  | 'job_fit_form'
  | 'skill_fit_form'

type QuestionType =
  | 'yes_no'
  | 'single_select'
  | 'multi_select'
  | 'short_text'
  | 'long_text'
  | 'number'
  | 'dropdown'
  | 'date'
  | 'file_upload'

type RuleActionType =
  | 'reject'
  | 'next_question'
  | 'skip_section'
  | 'manual_review'
  | 'show_question'
  | 'hide_question'
  | 'route_to_outcome'
  | 'end_form'

type DraftRule = {
  id: string
  condition_type: string
  compare_value: string
  action_type: RuleActionType
  outcome_code: string
  target_question_id: string
  target_section_id: string
}

type DraftQuestion = {
  id: string
  question_text: string
  question_type: QuestionType
  required: boolean
  help_text: string
  options_json: string[]
  score_weight: number
  is_knockout: boolean
  internal_note: string
  rules: DraftRule[]
}

type DraftSection = {
  id: string
  title: string
  description: string
  mandatory: boolean
  questions: DraftQuestion[]
}

type PrequalificationDraft = {
  id: string | null
  name: string
  prequal_type: PrequalSubtype
  description: string
  associated_role: string
  is_active: boolean
  sections: DraftSection[]
  knockout_logic: {
    auto_reject_enabled: boolean
    scoring_enabled: boolean
    pass_threshold: number
    reject_threshold: number
    manual_review_enabled: boolean
  }
  routing: {
    pass_route: 'ai_interview' | 'technical_interview' | 'human_interview' | 'manual_review'
    reject_route: 'reject' | 'manual_review'
    manual_review_route: 'manual_review' | 'human_interview'
    next_stage_name: string
    recruiter_review_required: boolean
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'form-builder', label: '2. Form Builder', icon: ClipboardList },
  { key: 'knockout', label: '3. Knockout Logic', icon: ShieldCheck },
  { key: 'routing', label: '4. Routing', icon: GitBranch },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const QUESTION_TYPE_OPTIONS = [
  { value: 'yes_no', label: 'Yes / No' },
  { value: 'single_select', label: 'Single Select' },
  { value: 'multi_select', label: 'Multi Select' },
  { value: 'dropdown', label: 'Dropdown' },
  { value: 'short_text', label: 'Short Text' },
  { value: 'long_text', label: 'Long Text' },
  { value: 'number', label: 'Numeric' },
  { value: 'date', label: 'Date' },
  { value: 'file_upload', label: 'File Upload' },
] as const

const PREQUAL_TYPES: Array<{
  value: PrequalSubtype
  label: string
  aliases: string[]
  guidance: {
    description: string
    focus: string[]
    starterQuestions: string[]
  }
}> = [
  {
    value: 'screening_form',
    label: 'Screening Form',
    aliases: ['recruiter_screening'],
    guidance: {
      description: 'Use broad intake questions to filter readiness, experience, and baseline alignment.',
      focus: ['Baseline fit', 'Availability', 'Core eligibility'],
      starterQuestions: ['Are you available within 30 days?', 'Do you have relevant experience?', 'What location are you based in?'],
    },
  },
  {
    value: 'knockout_form',
    label: 'Knockout Form',
    aliases: ['phone_interview'],
    guidance: {
      description: 'Use hard filters with auto reject logic for mandatory requirements.',
      focus: ['Mandatory criteria', 'Hard disqualifiers', 'Fast routing'],
      starterQuestions: ['Do you require sponsorship?', 'Are you willing to work shifts?', 'Do you meet the minimum qualification?'],
    },
  },
  {
    value: 'eligibility_form',
    label: 'Eligibility Form',
    aliases: ['eligibility_screening'],
    guidance: {
      description: 'Validate legal, location, and employment eligibility before interview progression.',
      focus: ['Work authorization', 'Location match', 'Basic policy fit'],
      starterQuestions: ['Are you legally authorized to work?', 'Can you work in the required location?', 'Are you comfortable with the compensation range?'],
    },
  },
  {
    value: 'qualification_form',
    label: 'Qualification Form',
    aliases: ['qualification_form'],
    guidance: {
      description: 'Score experience, qualifications, and readiness to route candidates to the right interview stage.',
      focus: ['Qualification depth', 'Readiness', 'Experience fit'],
      starterQuestions: ['How many years of relevant experience do you have?', 'What certifications are relevant?', 'Describe your most recent similar role.'],
    },
  },
  {
    value: 'job_fit_form',
    label: 'Job Fit Form',
    aliases: ['job_fit_form'],
    guidance: {
      description: 'Use decision-tree logic to qualify candidates against job-specific fit criteria.',
      focus: ['Role alignment', 'Environment fit', 'Functional readiness'],
      starterQuestions: ['Why is this role a fit?', 'Which responsibilities match your experience?', 'What work environment suits you best?'],
    },
  },
  {
    value: 'skill_fit_form',
    label: 'Skill Fit Form',
    aliases: ['skill_fit_form'],
    guidance: {
      description: 'Use targeted skill checks and weighted scoring to decide which interview engine should run next.',
      focus: ['Skill coverage', 'Depth of expertise', 'Gap detection'],
      starterQuestions: ['Rate your skill level in the core area.', 'Which tools have you used recently?', 'What is your strongest domain skill?'],
    },
  },
]

function makeId(prefix: string) {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function createRule(overrides: Partial<DraftRule> = {}): DraftRule {
  return {
    id: makeId('prequal-rule'),
    condition_type: 'equals',
    compare_value: '',
    action_type: 'next_question',
    outcome_code: '',
    target_question_id: '',
    target_section_id: '',
    ...overrides,
  }
}

function createQuestion(overrides: Partial<DraftQuestion> = {}): DraftQuestion {
  return {
    id: makeId('prequal-question'),
    question_text: '',
    question_type: 'yes_no',
    required: true,
    help_text: '',
    options_json: [],
    score_weight: 10,
    is_knockout: false,
    internal_note: '',
    rules: [],
    ...overrides,
  }
}

function createSection(overrides: Partial<DraftSection> = {}): DraftSection {
  return {
    id: makeId('prequal-section'),
    title: '',
    description: '',
    mandatory: true,
    questions: [createQuestion()],
    ...overrides,
  }
}

function createDraft(type: PrequalSubtype = 'screening_form'): PrequalificationDraft {
  const config = PREQUAL_TYPES.find((item) => item.value === type) || PREQUAL_TYPES[0]
  return {
    id: null,
    name: '',
    prequal_type: config.value,
    description: '',
    associated_role: '',
    is_active: true,
    sections: [
      createSection({
        title: 'Candidate Basics',
        description: config.guidance.description,
        questions: config.guidance.starterQuestions.map((text, index) =>
          createQuestion({
            question_text: text,
            question_type: index === 0 ? 'yes_no' : 'short_text',
            score_weight: index === 0 ? 20 : 10,
          }),
        ),
      }),
    ],
    knockout_logic: {
      auto_reject_enabled: type === 'knockout_form' || type === 'eligibility_form',
      scoring_enabled: true,
      pass_threshold: 70,
      reject_threshold: 40,
      manual_review_enabled: true,
    },
    routing: {
      pass_route: 'ai_interview',
      reject_route: 'reject',
      manual_review_route: 'manual_review',
      next_stage_name: '',
      recruiter_review_required: false,
    },
  }
}

function parseForm(record: any): PrequalificationDraft {
  const meta = record?.metadata?.prequalification_engine || {}
  const setup = meta.setup || {}
  const knockout = meta.knockout_logic || {}
  const routing = meta.routing || {}
  const inferred = (setup.prequal_type || 'screening_form') as PrequalSubtype
  const sections = Array.isArray(record?.sections)
    ? record.sections.map((section: any) => ({
        id: section.id || makeId('prequal-section'),
        title: section.title || '',
        description: section.description || '',
        mandatory: section.metadata?.mandatory ?? true,
        questions: Array.isArray(section.questions) && section.questions.length
          ? section.questions.map((question: any) => ({
              id: question.id || makeId('prequal-question'),
              question_text: question.question_text || '',
              question_type: question.question_type || 'yes_no',
              required: question.required ?? true,
              help_text: question.help_text || '',
              options_json: Array.isArray(question.options_json)
                ? question.options_json.map((item: any) => String(item))
                : [],
              score_weight: Number(question.score_weight ?? 0),
              is_knockout: question.is_knockout ?? false,
              internal_note: question.metadata?.internal_note || '',
              rules: Array.isArray(question.rules)
                ? question.rules.map((rule: any) => ({
                    id: rule.id || makeId('prequal-rule'),
                    condition_type: rule.condition_type || 'equals',
                    compare_value: rule.compare_value || '',
                    action_type: rule.action_type || 'next_question',
                    outcome_code: rule.outcome_code || '',
                    target_question_id: rule.target_question_id || '',
                    target_section_id: rule.target_section_id || '',
                  }))
                : [],
            }))
          : [createQuestion()],
      }))
    : createDraft(inferred).sections

  return {
    id: record.id,
    name: record.name || '',
    prequal_type: inferred,
    description: record.description || '',
    associated_role: setup.associated_role || '',
    is_active: record.is_active ?? true,
    sections,
    knockout_logic: {
      auto_reject_enabled: knockout.auto_reject_enabled ?? false,
      scoring_enabled: knockout.scoring_enabled ?? true,
      pass_threshold: Number(knockout.pass_threshold ?? 70),
      reject_threshold: Number(knockout.reject_threshold ?? 40),
      manual_review_enabled: knockout.manual_review_enabled ?? true,
    },
    routing: {
      pass_route: routing.pass_route || 'ai_interview',
      reject_route: routing.reject_route || 'reject',
      manual_review_route: routing.manual_review_route || 'manual_review',
      next_stage_name: routing.next_stage_name || '',
      recruiter_review_required: routing.recruiter_review_required ?? false,
    },
  }
}

function getGuidance(type: PrequalSubtype) {
  return PREQUAL_TYPES.find((item) => item.value === type)?.guidance || PREQUAL_TYPES[0].guidance
}

function serializeFormMetadata(draft: PrequalificationDraft, existing: any = {}) {
  return {
    ...(existing.metadata || {}),
    prequalification_engine: {
      setup: {
        prequal_type: draft.prequal_type,
        associated_role: draft.associated_role,
      },
      knockout_logic: draft.knockout_logic,
      routing: draft.routing,
      usage: existing?.metadata?.prequalification_engine?.usage || {
        linked_jobs: [],
        linked_flows: [],
        linked_stages: [],
      },
      integrations: {
        flow_engine: true,
        interview_engine: true,
        scorecard_engine: true,
        decision_engine: true,
      },
    },
    unified_template: {
      ...(existing.metadata?.unified_template || {}),
      category: 'Screening',
      setup: { reusable_template: true },
      configuration: {
        screening_config: draft.sections.map((section) => section.description).filter(Boolean).join('\n\n'),
      },
    },
  }
}

export default function InterviewPrequalificationEngine({ embedded = false }: PrequalificationEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const requestedType = new URLSearchParams(location.search).get('type')
  const initialType = useMemo<PrequalSubtype>(() => {
    const match = PREQUAL_TYPES.find((item) => item.aliases.includes(requestedType || ''))?.value
    return match || 'screening_form'
  }, [requestedType])

  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedFormId, setSelectedFormId] = useState<string | null>(null)
  const [selectedFormRecord, setSelectedFormRecord] = useState<any>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [saving, setSaving] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [draft, setDraft] = useState<PrequalificationDraft>(createDraft(initialType))

  const { data, isLoading } = useApiQuery(['prequal-engine-forms-list'], () => prequalificationApi.listForms())
  const forms = (data as any)?.forms ?? []

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = PREQUAL_TYPES.find((item) => item.aliases.includes(requestedType))?.value
    if (!nextType) return
    setDraft(createDraft(nextType))
    setSelectedFormId(null)
    setSelectedFormRecord(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen])

  const prequalForms = forms.filter((form: any) => form?.metadata?.prequalification_engine || form?.metadata?.unified_template?.category === 'Screening')
  const guidance = getGuidance(draft.prequal_type)
  const usageMap = useMemo(() => new Map<string, number>(
    prequalForms.map((form: any) => {
      const usage = form?.metadata?.prequalification_engine?.usage || {}
      const usageCount =
        (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
        (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
        (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0)
      return [form.id, usageCount]
    }) as Array<[string, number]>,
  ), [prequalForms])

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.associated_role.trim()),
    'form-builder': Boolean(draft.sections.some((section) => section.questions.some((question) => question.question_text.trim()))),
    knockout: draft.knockout_logic.scoring_enabled || draft.knockout_logic.auto_reject_enabled,
    routing: Boolean(draft.routing.pass_route),
    preview: true,
  }

  const allSections = draft.sections
  const allQuestions = draft.sections.flatMap((section) => section.questions.map((question) => ({
    id: question.id,
    label: question.question_text || 'Untitled question',
    sectionTitle: section.title || 'Untitled section',
  })))

  const updateDraft = (updater: (current: PrequalificationDraft) => PrequalificationDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = (type: PrequalSubtype = initialType) => {
    setSelectedFormId(null)
    setSelectedFormRecord(null)
    setDraft(createDraft(type))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = async (record: any, step: WizardStep = 'setup') => {
    try {
      const response = await prequalificationApi.getForm(record.id)
      const detailedForm = (response as any)?.data?.form ?? (response as any)?.form
      setSelectedFormId(record.id)
      setSelectedFormRecord(detailedForm)
      setDraft(parseForm(detailedForm))
      setActiveStep(step)
      setIsBuilderOpen(true)
    } catch {
      message.error('Failed to load prequalification form')
    }
  }

  const persistDraft = async (nextDraft: PrequalificationDraft, existingRecord?: any, duplicate = false) => {
    const formPayload = {
      name: nextDraft.name,
      description: nextDraft.description,
      is_active: duplicate ? false : nextDraft.is_active,
      metadata: serializeFormMetadata(nextDraft, existingRecord),
    }

    let formId = selectedFormId
    if (formId && !duplicate) {
      await prequalificationApi.updateForm(formId, formPayload)
      const detailResponse = await prequalificationApi.getForm(formId)
      const detail = (detailResponse as any)?.data?.form ?? (detailResponse as any)?.form
      const existingSections = Array.isArray(detail?.sections) ? detail.sections : []
      await Promise.all(existingSections.map((section: any) => prequalificationApi.deleteSection(section.id)))
    } else {
      const createResponse = await prequalificationApi.createForm(formPayload)
      const created = (createResponse as any)?.data?.form ?? (createResponse as any)?.form
      formId = created?.id
    }

    if (!formId) throw new Error('Form id missing')

    const sectionMap = new Map<string, string>()
    const questionMap = new Map<string, string>()

    for (let sectionIndex = 0; sectionIndex < nextDraft.sections.length; sectionIndex += 1) {
      const section = nextDraft.sections[sectionIndex]
      const sectionResponse = await prequalificationApi.createSection({
        form: formId,
        title: section.title,
        description: section.description,
        order: sectionIndex,
      })
      const createdSection = (sectionResponse as any)?.data?.section ?? (sectionResponse as any)?.section
      sectionMap.set(section.id, createdSection.id)
      await prequalificationApi.updateSection(createdSection.id, {
        metadata: { mandatory: section.mandatory } as any,
      } as any)

      for (let questionIndex = 0; questionIndex < section.questions.length; questionIndex += 1) {
        const question = section.questions[questionIndex]
        const questionResponse = await prequalificationApi.createQuestion({
          section: createdSection.id,
          question_text: question.question_text,
          question_type: question.question_type,
          required: question.required,
          order: questionIndex,
          help_text: question.help_text,
          options_json: question.options_json,
          score_weight: question.score_weight,
          is_knockout: question.is_knockout,
        })
        const createdQuestion = (questionResponse as any)?.data?.question ?? (questionResponse as any)?.question
        questionMap.set(question.id, createdQuestion.id)
        await prequalificationApi.updateQuestion(createdQuestion.id, {
          metadata: { internal_note: question.internal_note },
        })
      }
    }

    for (const section of nextDraft.sections) {
      for (const question of section.questions) {
        const createdQuestionId = questionMap.get(question.id)
        if (!createdQuestionId) continue
        for (const rule of question.rules) {
          await prequalificationApi.createRule({
            question_id: createdQuestionId,
            condition_type: rule.condition_type,
            compare_value: rule.compare_value,
            action_type: rule.action_type,
            outcome_code: rule.outcome_code,
            target_question_id: questionMap.get(rule.target_question_id) || undefined,
            target_section_id: sectionMap.get(rule.target_section_id) || undefined,
          })
        }
      }
    }

    return formId
  }

  const saveDraft = async () => {
    if (!draft.name.trim()) {
      message.error('Prequalification name is required')
      return
    }
    if (!draft.sections.some((section) => section.questions.some((question) => question.question_text.trim()))) {
      message.error('Add at least one question')
      return
    }
    setSaving(true)
    try {
      const nextId = await persistDraft(draft, selectedFormRecord, false)
      setSelectedFormId(nextId)
      message.success(selectedFormId ? 'Prequalification updated' : 'Prequalification created')
      await queryClient.invalidateQueries({ queryKey: ['prequal-engine-forms-list'] })
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save prequalification')
    } finally {
      setSaving(false)
    }
  }

  const duplicateForm = async (record: any) => {
    try {
      const response = await prequalificationApi.getForm(record.id)
      const detailedForm = (response as any)?.data?.form ?? (response as any)?.form
      const duplicated = parseForm(detailedForm)
      await persistDraft({ ...duplicated, id: null, name: `${duplicated.name} Copy`, is_active: false }, detailedForm, true)
      message.success('Prequalification duplicated')
      await queryClient.invalidateQueries({ queryKey: ['prequal-engine-forms-list'] })
    } catch {
      message.error('Failed to duplicate prequalification')
    }
  }

  const archiveForm = async (record: any) => {
    try {
      await prequalificationApi.updateForm(record.id, {
        name: record.name,
        description: record.description,
        is_active: false,
        metadata: record.metadata || {},
      })
      message.success('Prequalification archived')
      await queryClient.invalidateQueries({ queryKey: ['prequal-engine-forms-list'] })
    } catch {
      message.error('Failed to archive prequalification')
    }
  }

  const updateSection = (sectionId: string, patch: Partial<DraftSection>) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) => (section.id === sectionId ? { ...section, ...patch } : section)),
    }))
  }

  const addSection = () => {
    updateDraft((current) => ({ ...current, sections: [...current.sections, createSection()] }))
  }

  const removeSection = (sectionId: string) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.length > 1 ? current.sections.filter((section) => section.id !== sectionId) : current.sections,
    }))
  }

  const updateQuestion = (sectionId: string, questionId: string, patch: Partial<DraftQuestion>) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id !== sectionId
          ? section
          : {
              ...section,
              questions: section.questions.map((question) =>
                question.id === questionId ? { ...question, ...patch } : question,
              ),
            },
      ),
    }))
  }

  const addQuestion = (sectionId: string) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id === sectionId ? { ...section, questions: [...section.questions, createQuestion()] } : section,
      ),
    }))
  }

  const removeQuestion = (sectionId: string, questionId: string) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id !== sectionId
          ? section
          : {
              ...section,
              questions: section.questions.length > 1 ? section.questions.filter((question) => question.id !== questionId) : section.questions,
            },
      ),
    }))
  }

  const moveQuestion = (sectionId: string, questionId: string, direction: number) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) => {
        if (section.id !== sectionId) return section
        const index = section.questions.findIndex((question) => question.id === questionId)
        const target = index + direction
        if (index === -1 || target < 0 || target >= section.questions.length) return section
        const nextQuestions = [...section.questions]
        const [item] = nextQuestions.splice(index, 1)
        nextQuestions.splice(target, 0, item)
        return { ...section, questions: nextQuestions }
      }),
    }))
  }

  const addRule = (sectionId: string, questionId: string) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id !== sectionId
          ? section
          : {
              ...section,
              questions: section.questions.map((question) =>
                question.id !== questionId
                  ? question
                  : {
                      ...question,
                      rules: [...question.rules, createRule()],
                    },
              ),
            },
      ),
    }))
  }

  const updateRule = (sectionId: string, questionId: string, ruleId: string, patch: Partial<DraftRule>) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id !== sectionId
          ? section
          : {
              ...section,
              questions: section.questions.map((question) =>
                question.id !== questionId
                  ? question
                  : {
                      ...question,
                      rules: question.rules.map((rule) => (rule.id === ruleId ? { ...rule, ...patch } : rule)),
                    },
              ),
            },
      ),
    }))
  }

  const removeRule = (sectionId: string, questionId: string, ruleId: string) => {
    updateDraft((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id !== sectionId
          ? section
          : {
              ...section,
              questions: section.questions.map((question) =>
                question.id !== questionId
                  ? question
                  : {
                      ...question,
                      rules: question.rules.filter((rule) => rule.id !== ruleId),
                    },
              ),
            },
      ),
    }))
  }

  const previewUsage = selectedFormRecord?.metadata?.prequalification_engine?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] }

  const columns: ColumnsType<any> = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (value: string) => <Text className="font-bold text-slate-900">{value}</Text>,
    },
    {
      title: 'Type',
      render: (_, record) => {
        const type = PREQUAL_TYPES.find((item) => item.value === record?.metadata?.prequalification_engine?.setup?.prequal_type)
        return <Tag color="blue">{type?.label || 'Prequalification'}</Tag>
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
          <Button size="small" icon={<Copy size={13} />} onClick={() => duplicateForm(record)}>Duplicate</Button>
          <Button size="small" icon={<Eye size={13} />} onClick={() => openEdit(record, 'preview')}>Preview</Button>
          <Button size="small" danger onClick={() => archiveForm(record)}>Archive</Button>
        </Space>
      ),
    },
  ]

  const builderView = (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-3">
        <div className="sticky top-0 rounded-3xl border border-slate-200 bg-white p-4 shadow-soft-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Prequalification Wizard</p>
          <div className="mt-4 space-y-2">
            {WIZARD_STEPS.map((step) => {
              const Icon = step.icon
              return (
                <button
                  key={step.key}
                  type="button"
                  onClick={() => setActiveStep(step.key)}
                  className={cn(
                    'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition-all',
                    activeStep === step.key ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white hover:border-slate-300',
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('flex h-9 w-9 items-center justify-center rounded-2xl', activeStep === step.key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500')}>
                      <Icon size={16} />
                    </div>
                    <p className="text-xs font-black uppercase tracking-widest text-slate-900">{step.label}</p>
                  </div>
                  <Tag color={stepCompletion[step.key] ? 'success' : 'default'}>{stepCompletion[step.key] ? 'Done' : 'Open'}</Tag>
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
              <p className="mt-2 text-sm text-slate-500">Define the prequalification form identity, purpose, and associated role context.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Prequalification Name</label>
                <Input value={draft.name} placeholder="e.g. Sales SDR Knockout Form" onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Type</label>
                <Select
                  value={draft.prequal_type}
                  options={PREQUAL_TYPES.map((item) => ({ value: item.value, label: item.label }))}
                  onChange={(value: PrequalSubtype) => updateDraft((current) => ({ ...current, prequal_type: value }))}
                />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Associated Role</label>
                <Input value={draft.associated_role} placeholder="e.g. Customer Support, Backend Engineering, Finance Operations" onChange={(event) => updateDraft((current) => ({ ...current, associated_role: event.target.value }))} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Description</label>
                <TextArea rows={4} value={draft.description} placeholder="Describe what this prequalification form is validating." onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
              </div>
            </div>
            <Card className="border-slate-200 bg-slate-50">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Type Guidance</p>
              <p className="mt-2 text-sm text-slate-600">{guidance.description}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {guidance.focus.map((item) => <Tag key={item}>{item}</Tag>)}
              </div>
            </Card>
          </div>

          <div className={cn(activeStep === 'form-builder' ? 'block space-y-6' : 'hidden')}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Form Builder</p>
                <p className="mt-2 text-sm text-slate-500">Build google-form style sections with nested question logic, branching rules, and knockout behavior.</p>
              </div>
              <Button icon={<Plus size={14} />} onClick={addSection}>Add Section</Button>
            </div>
            <div className="space-y-4">
              {draft.sections.map((section) => (
                <Card key={section.id} className="border-slate-200">
                  <div className="mb-4 flex items-center justify-between">
                    <p className="text-sm font-black text-slate-900">{section.title || 'Untitled section'}</p>
                    <Space>
                      <Switch checked={section.mandatory} onChange={(checked) => updateSection(section.id, { mandatory: checked })} />
                      <Button danger size="small" icon={<Trash2 size={13} />} onClick={() => removeSection(section.id)}>Remove</Button>
                    </Space>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Section Title</label>
                      <Input value={section.title} placeholder="e.g. Eligibility Check" onChange={(event) => updateSection(section.id, { title: event.target.value })} />
                    </div>
                    <div>
                      <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Mandatory</label>
                      <div className="flex h-8 items-center text-xs text-slate-500">{section.mandatory ? 'Required section' : 'Optional section'}</div>
                    </div>
                    <div className="md:col-span-2">
                      <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Section Description</label>
                      <TextArea rows={2} value={section.description} placeholder="Candidate-facing instructions for this section." onChange={(event) => updateSection(section.id, { description: event.target.value })} />
                    </div>
                  </div>
                  <div className="mt-5 space-y-4">
                    {section.questions.map((question, index) => (
                      <Card key={question.id} className="border-slate-200 bg-slate-50/50">
                        <div className="mb-4 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Tag color="blue">Question {index + 1}</Tag>
                            <Text className="font-bold text-slate-900">{QUESTION_TYPE_OPTIONS.find((item) => item.value === question.question_type)?.label}</Text>
                          </div>
                          <Space size={4}>
                            <Button size="small" icon={<ArrowUp size={13} />} disabled={index === 0} onClick={() => moveQuestion(section.id, question.id, -1)} />
                            <Button size="small" icon={<ArrowDown size={13} />} disabled={index === section.questions.length - 1} onClick={() => moveQuestion(section.id, question.id, 1)} />
                            <Button size="small" danger icon={<Trash2 size={13} />} onClick={() => removeQuestion(section.id, question.id)}>Remove</Button>
                          </Space>
                        </div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <div className="md:col-span-2">
                            <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Question</label>
                            <Input value={question.question_text} placeholder="Enter question text" onChange={(event) => updateQuestion(section.id, question.id, { question_text: event.target.value })} />
                          </div>
                          <div>
                            <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Response Type</label>
                            <Select
                              value={question.question_type}
                              options={QUESTION_TYPE_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
                              onChange={(value: QuestionType) => updateQuestion(section.id, question.id, { question_type: value, options_json: ['single_select', 'multi_select', 'dropdown'].includes(value) ? question.options_json : [] })}
                            />
                          </div>
                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Required</label>
                              <div className="flex h-8 items-center">
                                <Switch checked={question.required} onChange={(checked) => updateQuestion(section.id, question.id, { required: checked })} />
                              </div>
                            </div>
                            <div>
                              <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Knockout</label>
                              <div className="flex h-8 items-center">
                                <Switch checked={question.is_knockout} onChange={(checked) => updateQuestion(section.id, question.id, { is_knockout: checked })} />
                              </div>
                            </div>
                            <div>
                              <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Weight</label>
                              <InputNumber min={0} max={100} className="w-full" value={question.score_weight} onChange={(value) => updateQuestion(section.id, question.id, { score_weight: Number(value || 0) })} />
                            </div>
                          </div>
                          {['single_select', 'multi_select', 'dropdown'].includes(question.question_type) ? (
                            <div>
                              <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Options</label>
                              <Select mode="tags" value={question.options_json} open={false} placeholder="Add options" onChange={(value) => updateQuestion(section.id, question.id, { options_json: value })} />
                            </div>
                          ) : null}
                          <div className={cn(['single_select', 'multi_select', 'dropdown'].includes(question.question_type) ? '' : 'md:col-span-2')}>
                            <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Help Text</label>
                            <Input value={question.help_text} placeholder="Candidate help text" onChange={(event) => updateQuestion(section.id, question.id, { help_text: event.target.value })} />
                          </div>
                          <div className="md:col-span-2">
                            <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Internal Note</label>
                            <TextArea rows={2} value={question.internal_note} placeholder="Internal reviewer note or branching intent." onChange={(event) => updateQuestion(section.id, question.id, { internal_note: event.target.value })} />
                          </div>
                        </div>

                        <div className="mt-5 rounded-2xl border border-dashed border-slate-200 p-4">
                          <div className="mb-3 flex items-center justify-between">
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Conditional Logic</p>
                              <p className="mt-1 text-xs text-slate-500">Add yes/no branching, routing rules, or decision tree actions.</p>
                            </div>
                            <Button size="small" icon={<Plus size={13} />} onClick={() => addRule(section.id, question.id)}>Add Rule</Button>
                          </div>
                          <div className="space-y-3">
                            {question.rules.length === 0 ? (
                              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No branching rules yet" />
                            ) : question.rules.map((rule) => (
                              <div key={rule.id} className="rounded-2xl border border-slate-200 bg-white p-3">
                                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                                  <Select
                                    value={rule.condition_type}
                                    options={[
                                      { value: 'equals', label: 'Equals' },
                                      { value: 'not_equals', label: 'Not Equals' },
                                      { value: 'greater_than', label: 'Greater Than' },
                                      { value: 'less_than', label: 'Less Than' },
                                      { value: 'contains', label: 'Contains' },
                                      { value: 'is_empty', label: 'Is Empty' },
                                    ]}
                                    onChange={(value) => updateRule(section.id, question.id, rule.id, { condition_type: value })}
                                  />
                                  <Input value={rule.compare_value} placeholder="Compare value" onChange={(event) => updateRule(section.id, question.id, rule.id, { compare_value: event.target.value })} />
                                  <Select
                                    value={rule.action_type}
                                    options={[
                                      { value: 'reject', label: 'Reject' },
                                      { value: 'manual_review', label: 'Manual Review' },
                                      { value: 'next_question', label: 'Next Question' },
                                      { value: 'skip_section', label: 'Skip Section' },
                                      { value: 'show_question', label: 'Show Question' },
                                      { value: 'hide_question', label: 'Hide Question' },
                                      { value: 'route_to_outcome', label: 'Route To Outcome' },
                                      { value: 'end_form', label: 'End Form' },
                                    ]}
                                    onChange={(value: RuleActionType) => updateRule(section.id, question.id, rule.id, { action_type: value })}
                                  />
                                  <Button danger onClick={() => removeRule(section.id, question.id, rule.id)}>Remove</Button>
                                  {['skip_section'].includes(rule.action_type) ? (
                                    <Select
                                      className="xl:col-span-2"
                                      allowClear
                                      value={rule.target_section_id || undefined}
                                      placeholder="Target section"
                                      options={allSections.filter((item) => item.id !== section.id).map((item) => ({ value: item.id, label: item.title || 'Untitled section' }))}
                                      onChange={(value) => updateRule(section.id, question.id, rule.id, { target_section_id: value || '' })}
                                    />
                                  ) : null}
                                  {['show_question', 'hide_question'].includes(rule.action_type) ? (
                                    <Select
                                      className="xl:col-span-2"
                                      allowClear
                                      value={rule.target_question_id || undefined}
                                      placeholder="Target question"
                                      options={allQuestions.filter((item) => item.id !== question.id).map((item) => ({ value: item.id, label: `${item.sectionTitle} • ${item.label}` }))}
                                      onChange={(value) => updateRule(section.id, question.id, rule.id, { target_question_id: value || '' })}
                                    />
                                  ) : null}
                                  {['route_to_outcome', 'reject', 'manual_review'].includes(rule.action_type) ? (
                                    <Select
                                      className="xl:col-span-2"
                                      allowClear
                                      value={rule.outcome_code || undefined}
                                      placeholder="Outcome"
                                      options={[
                                        { value: 'reject', label: 'Reject' },
                                        { value: 'manual_review', label: 'Manual Review' },
                                        { value: 'ai_interview', label: 'Move to AI Interview' },
                                        { value: 'technical_interview', label: 'Move to Technical Interview' },
                                        { value: 'human_interview', label: 'Move to Human Interview' },
                                      ]}
                                      onChange={(value) => updateRule(section.id, question.id, rule.id, { outcome_code: value || '' })}
                                    />
                                  ) : null}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </Card>
                    ))}
                    <Button icon={<Plus size={14} />} onClick={() => addQuestion(section.id)}>Add Question</Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          <div className={cn(activeStep === 'knockout' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Knockout Logic</p>
              <p className="mt-2 text-sm text-slate-500">Configure auto reject, scoring, thresholds, and manual review behavior.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Auto Reject Rules</p>
                    <p className="mt-1 text-sm text-slate-500">Reject immediately when knockout rules or answers fail.</p>
                  </div>
                  <Switch checked={draft.knockout_logic.auto_reject_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, knockout_logic: { ...current.knockout_logic, auto_reject_enabled: checked } }))} />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scoring Enabled</p>
                    <p className="mt-1 text-sm text-slate-500">Use weighted answers to compute overall qualification score.</p>
                  </div>
                  <Switch checked={draft.knockout_logic.scoring_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, knockout_logic: { ...current.knockout_logic, scoring_enabled: checked } }))} />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Pass Threshold</label>
                <InputNumber min={0} max={100} addonAfter="%" className="w-full" value={draft.knockout_logic.pass_threshold} onChange={(value) => updateDraft((current) => ({ ...current, knockout_logic: { ...current.knockout_logic, pass_threshold: Number(value || 0) } }))} />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Reject Threshold</label>
                <InputNumber min={0} max={100} addonAfter="%" className="w-full" value={draft.knockout_logic.reject_threshold} onChange={(value) => updateDraft((current) => ({ ...current, knockout_logic: { ...current.knockout_logic, reject_threshold: Number(value || 0) } }))} />
              </div>
              <div className="md:col-span-2 rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Manual Review</p>
                    <p className="mt-1 text-sm text-slate-500">Candidates between thresholds can be routed to manual review.</p>
                  </div>
                  <Switch checked={draft.knockout_logic.manual_review_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, knockout_logic: { ...current.knockout_logic, manual_review_enabled: checked } }))} />
                </div>
              </div>
            </div>
          </div>

          <div className={cn(activeStep === 'routing' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Routing</p>
              <p className="mt-2 text-sm text-slate-500">Define which interview engine or decision state should run after prequalification.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Pass Route</label>
                <Select
                  value={draft.routing.pass_route}
                  options={[
                    { value: 'ai_interview', label: 'Move to AI Interview' },
                    { value: 'technical_interview', label: 'Move to Technical Interview' },
                    { value: 'human_interview', label: 'Move to Human Interview' },
                    { value: 'manual_review', label: 'Manual Review' },
                  ]}
                  onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, pass_route: value } }))}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Reject Route</label>
                <Select
                  value={draft.routing.reject_route}
                  options={[
                    { value: 'reject', label: 'Reject Candidate' },
                    { value: 'manual_review', label: 'Manual Review' },
                  ]}
                  onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, reject_route: value } }))}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Manual Review Route</label>
                <Select
                  value={draft.routing.manual_review_route}
                  options={[
                    { value: 'manual_review', label: 'Manual Review Queue' },
                    { value: 'human_interview', label: 'Move to Human Interview' },
                  ]}
                  onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, manual_review_route: value } }))}
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">Next Stage Mapping</label>
                <Input value={draft.routing.next_stage_name} placeholder="e.g. AI Sales Screen" onChange={(event) => updateDraft((current) => ({ ...current, routing: { ...current.routing, next_stage_name: event.target.value } }))} />
              </div>
              <div className="md:col-span-2 rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Recruiter Review Required</p>
                    <p className="mt-1 text-sm text-slate-500">Require recruiter review before automated routing continues.</p>
                  </div>
                  <Switch checked={draft.routing.recruiter_review_required} onChange={(checked) => updateDraft((current) => ({ ...current, routing: { ...current.routing, recruiter_review_required: checked } }))} />
                </div>
              </div>
            </div>
          </div>

          <div className={cn(activeStep === 'preview' ? 'block space-y-6' : 'hidden')}>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage / Preview</p>
              <p className="mt-2 text-sm text-slate-500">Review routing, knockout thresholds, and linked usage before saving.</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-slate-200"><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Sections</p><p className="mt-2 text-sm font-bold text-slate-900">{draft.sections.length}</p></Card>
              <Card className="border-slate-200"><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Questions</p><p className="mt-2 text-sm font-bold text-slate-900">{allQuestions.length}</p></Card>
              <Card className="border-slate-200"><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Pass Threshold</p><p className="mt-2 text-sm font-bold text-slate-900">{draft.knockout_logic.pass_threshold}%</p></Card>
              <Card className="border-slate-200"><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage Count</p><p className="mt-2 text-sm font-bold text-slate-900">{selectedFormId ? usageMap.get(selectedFormId) || 0 : 0}</p></Card>
            </div>
            <Card className="border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Routing Summary</p>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="rounded-2xl border border-slate-200 p-3">
                    <p className="text-xs font-black uppercase tracking-widest text-slate-400">Pass</p>
                    <p className="mt-2 text-sm font-bold text-slate-900">{draft.routing.pass_route.replace(/_/g, ' ')}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-3">
                    <p className="text-xs font-black uppercase tracking-widest text-slate-400">Reject</p>
                    <p className="mt-2 text-sm font-bold text-slate-900">{draft.routing.reject_route.replace(/_/g, ' ')}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-3">
                    <p className="text-xs font-black uppercase tracking-widest text-slate-400">Manual Review</p>
                    <p className="mt-2 text-sm font-bold text-slate-900">{draft.routing.manual_review_route.replace(/_/g, ' ')}</p>
                  </div>
                </div>
                <div className="space-y-3">
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
            </Card>
          </div>

          <div className="mt-8 flex items-center justify-between">
            <Button disabled={WIZARD_STEPS.findIndex((step) => step.key === activeStep) === 0} onClick={() => setActiveStep(WIZARD_STEPS[Math.max(WIZARD_STEPS.findIndex((step) => step.key === activeStep) - 1, 0)].key)}>
              Back
            </Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              {activeStep !== 'preview' ? (
                <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(WIZARD_STEPS.findIndex((step) => step.key === activeStep) + 1, WIZARD_STEPS.length - 1)].key)}>
                  Next
                </Button>
              ) : (
                <Button type="primary" loading={saving} onClick={saveDraft}>Save Prequalification</Button>
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
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Prequalification</p>
          <p className="mt-1 text-xs text-slate-500">Reusable screening and knockout forms with decision tree logic and routing.</p>
        </div>
        <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>Create Prequalification</Button>
      </div>
      <Table
        rowKey="id"
        loading={isLoading}
        columns={columns}
        dataSource={prequalForms}
        pagination={false}
        locale={{
          emptyText: (
            <Empty description="No prequalification forms yet">
              <Button type="primary" onClick={() => openCreate(initialType)}>Create Prequalification</Button>
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
            <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>Back to Prequalification</Button>
            <Space>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Prequalification</Button>
            </Space>
          </div>
        ) : null}
        {isBuilderOpen ? builderView : listView}
        <PreviewCardModal open={previewOpen} draft={draft} onClose={() => setPreviewOpen(false)} />
      </>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
            <ClipboardList size={18} />
          </div>
          <h1 className="text-base font-black uppercase tracking-tight text-slate-900">Prequalification</h1>
        </div>
        <Space>
          {isBuilderOpen ? (
            <>
              <Button onClick={() => setIsBuilderOpen(false)}>Back to Prequalification</Button>
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Prequalification</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/interviews/types')}>Registry</Button>
              <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate(initialType)}>Create Prequalification</Button>
            </>
          )}
        </Space>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {isBuilderOpen ? builderView : listView}
      </div>
      <PreviewCardModal open={previewOpen} draft={draft} onClose={() => setPreviewOpen(false)} />
    </div>
  )
}

function PreviewCardModal({
  open,
  draft,
  onClose,
}: {
  open: boolean
  draft: PrequalificationDraft
  onClose: () => void
}) {
  const type = PREQUAL_TYPES.find((item) => item.value === draft.prequal_type)
  return (
    <Card
      className={cn(
        'fixed inset-x-0 top-20 z-[100] mx-auto hidden w-[min(900px,calc(100vw-48px))] rounded-3xl border border-slate-200 shadow-2xl',
        open ? 'block' : 'hidden',
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Prequalification Preview</p>
          <p className="mt-2 text-lg font-black text-slate-900">{draft.name || 'Untitled prequalification'}</p>
        </div>
        <Button onClick={onClose}>Close</Button>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-3xl bg-slate-950 p-6 text-white">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Summary</p>
          <p className="mt-3 text-2xl font-black">{type?.label}</p>
          <p className="mt-2 text-sm text-slate-300">{draft.associated_role || 'Associated role not set'}</p>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Sections</p>
              <p className="mt-1 text-sm font-bold">{draft.sections.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Questions</p>
              <p className="mt-1 text-sm font-bold">{draft.sections.reduce((sum, section) => sum + section.questions.length, 0)}</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Pass</p>
              <p className="mt-1 text-sm font-bold">{draft.knockout_logic.pass_threshold}%</p>
            </div>
            <div className="rounded-2xl bg-slate-900 p-3">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Pass Route</p>
              <p className="mt-1 text-sm font-bold">{draft.routing.pass_route.replace(/_/g, ' ')}</p>
            </div>
          </div>
        </div>
        <div className="space-y-3">
          <Card className="border-slate-200">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Decision Tree</p>
            <div className="mt-3 space-y-2">
              {draft.sections.flatMap((section) => section.questions).slice(0, 5).map((question, index) => (
                <div key={question.id} className="rounded-2xl border border-slate-200 p-3">
                  <p className="text-xs font-black uppercase tracking-widest text-slate-400">Question {index + 1}</p>
                  <p className="mt-2 text-sm font-bold text-slate-900">{question.question_text || 'Untitled question'}</p>
                  <p className="mt-1 text-xs text-slate-500">{question.rules.length ? `${question.rules.length} logic rule(s)` : 'No logic rules'}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </Card>
  )
}
