import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Divider,
  Empty,
  Input,
  InputNumber,
  List,
  Radio,
  Select,
  Space,
  Switch,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SaveOutlined,
  LinkOutlined,
  EyeOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { interviewsApi } from '@/api/interviews'

const { Title, Text } = Typography

type UiQuestionType =
  | 'yes_no'
  | 'single_select'
  | 'multi_select'
  | 'short_text'
  | 'long_text'
  | 'number'
  | 'rating'
  | 'file_upload'
  | 'coding_question'
  | 'video_question'

const UI_TYPE_OPTIONS: { value: UiQuestionType; label: string }[] = [
  { value: 'yes_no', label: 'Yes / No' },
  { value: 'single_select', label: 'Single Select' },
  { value: 'multi_select', label: 'Multi Select' },
  { value: 'short_text', label: 'Short Text' },
  { value: 'long_text', label: 'Long Text' },
  { value: 'number', label: 'Number' },
  { value: 'rating', label: 'Rating' },
  { value: 'file_upload', label: 'File Upload' },
  { value: 'coding_question', label: 'Coding Question (Shell)' },
  { value: 'video_question', label: 'Video Question (Shell)' },
]

type QuestionOption = {
  id: string
  label: string
  score: number
  preferred?: boolean
}

type NumberBand = {
  id: string
  from: number
  to: number
  score: number
}

type BuilderState = {
  id?: string
  title: string
  description: string
  uiType: UiQuestionType
  scope: 'global' | 'tenant' | 'template'
  difficulty: 'easy' | 'medium' | 'hard'
  skills: string[]
  tags: string[]
  scoringWeight: number
  expectedAnswer: string

  yesLabel: string
  noLabel: string
  yesNoExpected: 'yes' | 'no' | ''
  knockout: boolean
  yesScore: number
  noScore: number

  options: QuestionOption[]
  multiMin: number
  multiMax: number

  placeholder: string
  answerHint: string
  charLimit: number | null
  manualEvaluation: boolean

  numberMin: number | null
  numberMax: number | null
  numberUnits: string
  numberBands: NumberBand[]

  ratingScale: number
  ratingMinLabel: string
  ratingMaxLabel: string

  fileTypes: string[]
  fileCount: number
  fileSizeMb: number
  fileMandatory: boolean

  codingLanguages: string[]
  codingStarterCode: string
  codingEvaluationMode: string

  videoMaxDurationSec: number
  videoRetries: number
  videoPrepTimeSec: number
}

const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

const EMPTY_BUILDER: BuilderState = {
  title: '',
  description: '',
  uiType: 'short_text',
  scope: 'tenant',
  difficulty: 'medium',
  skills: [],
  tags: [],
  scoringWeight: 1,
  expectedAnswer: '',

  yesLabel: 'Yes',
  noLabel: 'No',
  yesNoExpected: '',
  knockout: false,
  yesScore: 1,
  noScore: 0,

  options: [
    { id: makeId(), label: 'Option 1', score: 0 },
    { id: makeId(), label: 'Option 2', score: 0 },
  ],
  multiMin: 1,
  multiMax: 2,

  placeholder: '',
  answerHint: '',
  charLimit: null,
  manualEvaluation: true,

  numberMin: null,
  numberMax: null,
  numberUnits: '',
  numberBands: [{ id: makeId(), from: 0, to: 100, score: 1 }],

  ratingScale: 5,
  ratingMinLabel: 'Poor',
  ratingMaxLabel: 'Excellent',

  fileTypes: ['pdf'],
  fileCount: 1,
  fileSizeMb: 5,
  fileMandatory: true,

  codingLanguages: ['javascript'],
  codingStarterCode: '',
  codingEvaluationMode: 'manual',

  videoMaxDurationSec: 120,
  videoRetries: 1,
  videoPrepTimeSec: 30,
}

const UI_TO_BACKEND: Record<UiQuestionType, string> = {
  yes_no: 'yes_no',
  single_select: 'multiple_choice',
  multi_select: 'multi_select',
  short_text: 'text',
  long_text: 'text',
  number: 'text',
  rating: 'rating',
  file_upload: 'file_upload',
  coding_question: 'coding',
  video_question: 'video',
}

function backendToUiType(question: any): UiQuestionType {
  const fromMeta = question?.metadata?.ui_type
  if (fromMeta && UI_TYPE_OPTIONS.some(o => o.value === fromMeta)) return fromMeta
  const t = question?.question_type
  if (t === 'multiple_choice') return 'single_select'
  if (t === 'multi_select') return 'multi_select'
  if (t === 'yes_no') return 'yes_no'
  if (t === 'rating') return 'rating'
  if (t === 'file_upload') return 'file_upload'
  if (t === 'coding') return 'coding_question'
  if (t === 'video') return 'video_question'
  return 'short_text'
}

function questionToBuilder(question: any): BuilderState {
  const uiType = backendToUiType(question)
  const md = question?.metadata || {}
  const opts = Array.isArray(question?.options_json)
    ? question.options_json.map((o: any, idx: number) => ({
        id: makeId(),
        label: typeof o === 'string' ? o : String(o?.label || `Option ${idx + 1}`),
        score: Number(o?.score || 0),
        preferred: Boolean(o?.preferred),
      }))
    : []

  return {
    ...EMPTY_BUILDER,
    id: question.id,
    title: question.question_title || '',
    description: question.description || '',
    uiType,
    scope: question.scope || 'tenant',
    difficulty: question.difficulty || 'medium',
    skills: Array.isArray(question.skills) ? question.skills : [],
    tags: Array.isArray(question.tags) ? question.tags : [],
    scoringWeight: Number(question.scoring_weight || 1),
    expectedAnswer: question.expected_answer || '',

    yesLabel: md.yes_label || 'Yes',
    noLabel: md.no_label || 'No',
    yesNoExpected: md.yes_no_expected || '',
    knockout: Boolean(md.knockout),
    yesScore: Number(md.yes_score ?? 1),
    noScore: Number(md.no_score ?? 0),

    options: opts.length ? opts : EMPTY_BUILDER.options,
    multiMin: Number(md.multi_min ?? 1),
    multiMax: Number(md.multi_max ?? Math.max(2, opts.length || 2)),

    placeholder: md.placeholder || '',
    answerHint: md.answer_hint || '',
    charLimit: md.char_limit ?? null,
    manualEvaluation: md.manual_evaluation ?? true,

    numberMin: md.number_min ?? null,
    numberMax: md.number_max ?? null,
    numberUnits: md.number_units || '',
    numberBands: Array.isArray(md.number_bands) && md.number_bands.length
      ? md.number_bands.map((b: any) => ({ id: makeId(), from: Number(b.from ?? 0), to: Number(b.to ?? 0), score: Number(b.score ?? 0) }))
      : EMPTY_BUILDER.numberBands,

    ratingScale: Number(md.rating_scale || 5),
    ratingMinLabel: md.rating_min_label || 'Poor',
    ratingMaxLabel: md.rating_max_label || 'Excellent',

    fileTypes: Array.isArray(md.file_types) && md.file_types.length ? md.file_types : ['pdf'],
    fileCount: Number(md.file_count || 1),
    fileSizeMb: Number(md.file_size_mb || 5),
    fileMandatory: md.file_mandatory ?? true,

    codingLanguages: Array.isArray(md.coding_languages) && md.coding_languages.length ? md.coding_languages : ['javascript'],
    codingStarterCode: md.coding_starter_code || '',
    codingEvaluationMode: md.coding_evaluation_mode || 'manual',

    videoMaxDurationSec: Number(md.video_max_duration_sec || 120),
    videoRetries: Number(md.video_retries || 1),
    videoPrepTimeSec: Number(md.video_prep_time_sec || 30),
  }
}

function builderToPayload(b: BuilderState) {
  const metadata: Record<string, any> = {
    ui_type: b.uiType,
    placeholder: b.placeholder,
    answer_hint: b.answerHint,
    char_limit: b.charLimit,
    manual_evaluation: b.manualEvaluation,
    knockout: b.knockout,
    multi_min: b.multiMin,
    multi_max: b.multiMax,
    number_min: b.numberMin,
    number_max: b.numberMax,
    number_units: b.numberUnits,
    number_bands: b.numberBands.map(({ from, to, score }) => ({ from, to, score })),
    rating_scale: b.ratingScale,
    rating_min_label: b.ratingMinLabel,
    rating_max_label: b.ratingMaxLabel,
    file_types: b.fileTypes,
    file_count: b.fileCount,
    file_size_mb: b.fileSizeMb,
    file_mandatory: b.fileMandatory,
    coding_languages: b.codingLanguages,
    coding_starter_code: b.codingStarterCode,
    coding_evaluation_mode: b.codingEvaluationMode,
    video_max_duration_sec: b.videoMaxDurationSec,
    video_retries: b.videoRetries,
    video_prep_time_sec: b.videoPrepTimeSec,
  }

  let optionsJson: any[] = []
  let expectedAnswer = b.expectedAnswer

  if (b.uiType === 'yes_no') {
    metadata.yes_label = b.yesLabel
    metadata.no_label = b.noLabel
    metadata.yes_no_expected = b.yesNoExpected
    metadata.yes_score = b.yesScore
    metadata.no_score = b.noScore
    optionsJson = [
      { label: b.yesLabel, value: 'yes', score: b.yesScore },
      { label: b.noLabel, value: 'no', score: b.noScore },
    ]
    if (!expectedAnswer && b.yesNoExpected) expectedAnswer = b.yesNoExpected
  }

  if (b.uiType === 'single_select' || b.uiType === 'multi_select') {
    optionsJson = b.options.map(o => ({
      label: o.label,
      score: o.score,
      preferred: !!o.preferred,
    }))
    const preferred = b.options.filter(o => o.preferred).map(o => o.label)
    if (!expectedAnswer && preferred.length) expectedAnswer = preferred.join(', ')
  }

  if (b.uiType === 'rating') {
    optionsJson = Array.from({ length: b.ratingScale }).map((_, i) => ({
      value: i + 1,
      label: String(i + 1),
      score: i + 1,
    }))
  }

  return {
    scope: b.scope,
    question_title: b.title,
    description: b.description,
    question_type: UI_TO_BACKEND[b.uiType],
    difficulty: b.difficulty,
    tags: b.tags,
    skills: b.skills,
    expected_answer: expectedAnswer,
    scoring_weight: b.scoringWeight,
    options_json: optionsJson,
    metadata,
  }
}

function TypeBadge({ type }: { type: UiQuestionType }) {
  const label = UI_TYPE_OPTIONS.find(t => t.value === type)?.label || type
  return <Tag className="m-0 uppercase text-[10px] font-semibold">{label}</Tag>
}

function validateQuestionBuilder(b: BuilderState): string[] {
  const errors: string[] = []
  if (!b.title.trim()) errors.push('Question title is required.')
  if (b.scoringWeight < 0) errors.push('Scoring weight cannot be negative.')

  if (b.uiType === 'yes_no') {
    if (!b.yesLabel.trim() || !b.noLabel.trim()) errors.push('Yes/No labels are required.')
    if (b.yesLabel.trim().toLowerCase() === b.noLabel.trim().toLowerCase()) {
      errors.push('Yes and No labels must be different.')
    }
  }

  if (b.uiType === 'single_select' || b.uiType === 'multi_select') {
    const validOptions = b.options.filter(o => o.label.trim())
    if (validOptions.length < 2) errors.push('At least 2 options are required.')
    const normalized = validOptions.map(o => o.label.trim().toLowerCase())
    if (new Set(normalized).size !== normalized.length) errors.push('Option labels must be unique.')
    if (b.uiType === 'single_select' && validOptions.filter(o => o.preferred).length > 1) {
      errors.push('Single select can only have one preferred option.')
    }
    if (b.uiType === 'multi_select') {
      if (b.multiMin < 1) errors.push('Minimum selection must be at least 1.')
      if (b.multiMax < b.multiMin) errors.push('Maximum selection must be greater than or equal to minimum selection.')
      if (b.multiMax > validOptions.length) errors.push('Maximum selection cannot exceed available options.')
    }
  }

  if (b.uiType === 'short_text' || b.uiType === 'long_text') {
    if (b.charLimit !== null && b.charLimit < 1) errors.push('Character limit must be at least 1.')
  }

  if (b.uiType === 'number') {
    if (b.numberMin !== null && b.numberMax !== null && b.numberMin > b.numberMax) {
      errors.push('Number min cannot be greater than max.')
    }
    for (const band of b.numberBands) {
      if (band.from > band.to) errors.push('Each scoring band must have from <= to.')
    }
  }

  if (b.uiType === 'rating') {
    if (b.ratingScale < 2 || b.ratingScale > 10) errors.push('Rating scale must be between 2 and 10.')
  }

  if (b.uiType === 'file_upload') {
    if (!b.fileTypes.length) errors.push('At least one file type is required.')
    if (b.fileCount < 1) errors.push('File count must be at least 1.')
    if (b.fileSizeMb < 1) errors.push('File size limit must be at least 1 MB.')
  }

  if (b.uiType === 'coding_question') {
    if (!b.codingLanguages.length) errors.push('Select at least one coding language.')
  }

  if (b.uiType === 'video_question') {
    if (b.videoMaxDurationSec < 30) errors.push('Video max duration must be at least 30 seconds.')
    if (b.videoRetries < 0) errors.push('Video retries cannot be negative.')
    if (b.videoPrepTimeSec < 0) errors.push('Preparation time cannot be negative.')
  }

  return errors
}

export default function InterviewQuestionBank() {
  const qc = useQueryClient()

  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null)
  const [isCreatingNewQuestion, setIsCreatingNewQuestion] = useState(false)
  const [builder, setBuilder] = useState<BuilderState>(EMPTY_BUILDER)

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [difficultyFilter, setDifficultyFilter] = useState<string>('')
  const [scopeFilter, setScopeFilter] = useState<string>('')
  const [skillFilter, setSkillFilter] = useState<string>('')
  const [tagFilter, setTagFilter] = useState<string>('')

  const [attachType, setAttachType] = useState<'template' | 'interview_type' | 'assessment'>('template')
  const [attachTemplateId, setAttachTemplateId] = useState<string | undefined>()
  const [attachInterviewType, setAttachInterviewType] = useState<string | undefined>()
  const [attachAssessmentRef, setAttachAssessmentRef] = useState<string>('')
  const [attachOrder, setAttachOrder] = useState<number>(0)

  const [sectionName, setSectionName] = useState('')
  const [sectionDescription, setSectionDescription] = useState('')
  const [sectionInstructions, setSectionInstructions] = useState('')
  const [sectionScope, setSectionScope] = useState<'global' | 'tenant' | 'template'>('tenant')
  const [sectionTargetType, setSectionTargetType] = useState<'template' | 'interview_type' | 'assessment'>('template')
  const [sectionTargetRef, setSectionTargetRef] = useState<string>('')
  const [sectionOrder, setSectionOrder] = useState<number>(0)
  const [sectionItems, setSectionItems] = useState<Array<{ question_id: string; order_index: number; required: boolean }>>([])
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null)

  const questionsQ = useQuery({
    queryKey: ['interview_question_bank'],
    queryFn: async () => (await interviewsApi.listQuestionBank()).data?.data?.questions || [],
  })

  const attachmentsQ = useQuery({
    queryKey: ['interview_question_attachments'],
    queryFn: async () => (await interviewsApi.listQuestionAttachments()).data?.data?.attachments || [],
  })

  const groupsQ = useQuery({
    queryKey: ['interview_question_groups'],
    queryFn: async () => (await interviewsApi.listQuestionGroups()).data?.data?.groups || [],
  })

  const templatesQ = useQuery({
    queryKey: ['interview_templates_for_questions'],
    queryFn: async () => (await interviewsApi.listTemplates()).data?.data?.templates || [],
  })

  const typesQ = useQuery({
    queryKey: ['interview_types_for_questions'],
    queryFn: async () => (await interviewsApi.listTypes()).data?.data?.types || [],
  })

  const saveQuestionM = useMutation({
    mutationFn: async (payload: any) => {
      if (builder.id) return interviewsApi.updateQuestionBank(builder.id, payload)
      return interviewsApi.createQuestionBank(payload)
    },
    onSuccess: (res) => {
      const q = res.data?.data?.question
      message.success(builder.id ? 'Question updated' : 'Question created')
      qc.invalidateQueries({ queryKey: ['interview_question_bank'] })
      setIsCreatingNewQuestion(false)
      if (q?.id) setSelectedQuestionId(q.id)
    },
    onError: () => message.error('Failed to save question'),
  })

  const attachQuestionM = useMutation({
    mutationFn: async (payload: any) => interviewsApi.attachQuestion(payload),
    onSuccess: () => {
      message.success('Question attached successfully')
      qc.invalidateQueries({ queryKey: ['interview_question_attachments'] })
    },
    onError: () => message.error('Failed to attach question'),
  })

  const createGroupM = useMutation({
    mutationFn: async (payload: any) => {
      if (editingSectionId) return interviewsApi.updateQuestionGroup(editingSectionId, payload)
      return interviewsApi.createQuestionGroup(payload)
    },
    onSuccess: () => {
      message.success(editingSectionId ? 'Section updated' : 'Section saved')
      qc.invalidateQueries({ queryKey: ['interview_question_groups'] })
      setSectionName('')
      setSectionDescription('')
      setSectionInstructions('')
      setSectionItems([])
      setSectionTargetRef('')
      setSectionOrder(0)
      setEditingSectionId(null)
    },
    onError: () => message.error('Failed to save section'),
  })

  const questions = questionsQ.data || []
  const attachments = attachmentsQ.data || []
  const groups = groupsQ.data || []
  const templates = templatesQ.data || []
  const interviewTypes = typesQ.data || []

  const usageByQuestion = useMemo(() => {
    const usage: Record<string, number> = {}
    for (const a of attachments) {
      const qid = a?.question?.id
      if (!qid) continue
      usage[qid] = (usage[qid] || 0) + 1
    }
    return usage
  }, [attachments])

  const skillOptions = useMemo(() => {
    const values = new Set<string>()
    questions.forEach((q: any) => (q.skills || []).forEach((s: string) => values.add(s)))
    return Array.from(values)
  }, [questions])

  const tagOptions = useMemo(() => {
    const values = new Set<string>()
    questions.forEach((q: any) => (q.tags || []).forEach((t: string) => values.add(t)))
    return Array.from(values)
  }, [questions])

  const filteredQuestions = useMemo(() => {
    return questions.filter((q: any) => {
      const uiType = backendToUiType(q)
      const matchesSearch = !search ||
        q.question_title?.toLowerCase().includes(search.toLowerCase()) ||
        q.description?.toLowerCase().includes(search.toLowerCase())
      const matchesType = !typeFilter || uiType === typeFilter
      const matchesDifficulty = !difficultyFilter || q.difficulty === difficultyFilter
      const matchesScope = !scopeFilter || q.scope === scopeFilter
      const matchesSkill = !skillFilter || (q.skills || []).includes(skillFilter)
      const matchesTag = !tagFilter || (q.tags || []).includes(tagFilter)
      return matchesSearch && matchesType && matchesDifficulty && matchesScope && matchesSkill && matchesTag
    })
  }, [questions, search, typeFilter, difficultyFilter, scopeFilter, skillFilter, tagFilter])

  useEffect(() => {
    if (isCreatingNewQuestion) return
    if (!selectedQuestionId && filteredQuestions.length) {
      setSelectedQuestionId(filteredQuestions[0].id)
      return
    }
    if (selectedQuestionId && !questions.find((q: any) => q.id === selectedQuestionId)) {
      setSelectedQuestionId(filteredQuestions[0]?.id || null)
    }
  }, [selectedQuestionId, filteredQuestions, questions, isCreatingNewQuestion])

  useEffect(() => {
    if (!selectedQuestionId) {
      setBuilder(EMPTY_BUILDER)
      return
    }
    const q = questions.find((x: any) => x.id === selectedQuestionId)
    if (q) setBuilder(questionToBuilder(q))
  }, [selectedQuestionId, questions])

  const selectedQuestion = useMemo(
    () => questions.find((q: any) => q.id === selectedQuestionId),
    [questions, selectedQuestionId],
  )
  const questionValidationErrors = useMemo(() => validateQuestionBuilder(builder), [builder])

  const moveOption = (index: number, direction: -1 | 1) => {
    const target = index + direction
    if (target < 0 || target >= builder.options.length) return
    const next = [...builder.options]
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    setBuilder({ ...builder, options: next })
  }

  const saveQuestion = () => {
    if (questionValidationErrors.length) {
      message.error(questionValidationErrors[0])
      return
    }
    saveQuestionM.mutate(builderToPayload(builder))
  }

  const createNewQuestion = () => {
    setIsCreatingNewQuestion(true)
    setSelectedQuestionId(null)
    setBuilder({ ...EMPTY_BUILDER, options: [...EMPTY_BUILDER.options.map(o => ({ ...o, id: makeId() }))] })
  }

  const addOption = () => {
    setBuilder({
      ...builder,
      options: [...builder.options, { id: makeId(), label: `Option ${builder.options.length + 1}`, score: 0 }],
    })
  }

  const removeOption = (id: string) => {
    setBuilder({ ...builder, options: builder.options.filter(o => o.id !== id) })
  }

  const attachQuestion = () => {
    const questionId = selectedQuestion?.id || builder.id
    if (!questionId) {
      message.error('Save or select a question first')
      return
    }

    const payload: any = {
      question_id: questionId,
      attach_type: attachType,
      order_index: attachOrder,
      is_active: true,
    }

    if (attachType === 'template') {
      if (!attachTemplateId) {
        message.error('Select a template destination.')
        return
      }
      payload.template_id = attachTemplateId
    }
    if (attachType === 'interview_type') {
      if (!attachInterviewType) {
        message.error('Select an interview type destination.')
        return
      }
      payload.interview_type = attachInterviewType
    }
    if (attachType === 'assessment') {
      if (!attachAssessmentRef.trim()) {
        message.error('Assessment reference is required.')
        return
      }
      payload.assessment_ref = attachAssessmentRef.trim()
    }

    attachQuestionM.mutate(payload)
  }

  const addSectionQuestion = (questionId: string) => {
    if (sectionItems.some(i => i.question_id === questionId)) return
    setSectionItems(prev => [...prev, { question_id: questionId, order_index: prev.length, required: true }])
  }

  const moveSectionQuestion = (index: number, direction: -1 | 1) => {
    const target = index + direction
    if (target < 0 || target >= sectionItems.length) return
    const next = [...sectionItems]
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    setSectionItems(next.map((x, idx) => ({ ...x, order_index: idx })))
  }

  const saveSection = () => {
    if (!sectionName.trim()) {
      message.error('Section name is required')
      return
    }
    if (!sectionItems.length) {
      message.error('Add at least one question to section')
      return
    }
    if (!sectionTargetRef.trim()) {
      message.error('Section destination is required')
      return
    }
    createGroupM.mutate({
      scope: sectionScope,
      name: sectionName,
      description: sectionDescription,
      section_name: sectionName,
      target_type: sectionTargetType,
      target_ref: sectionTargetRef,
      order_index: sectionOrder,
      metadata: { instructions: sectionInstructions },
      items: sectionItems,
    })
  }

  const loadSectionForEdit = (group: any) => {
    setEditingSectionId(group.id)
    setSectionName(group.name || '')
    setSectionDescription(group.description || '')
    setSectionInstructions(group.metadata?.instructions || '')
    setSectionScope(group.scope || 'tenant')
    setSectionTargetType(group.target_type || 'template')
    setSectionTargetRef(group.target_ref || '')
    setSectionOrder(Number(group.order_index || 0))
    setSectionItems(
      (group.items || []).map((item: any, idx: number) => ({
        question_id: item.question?.id || item.question_id,
        order_index: Number(item.order_index ?? idx),
        required: Boolean(item.required ?? true),
      })),
    )
  }

  const resetSectionBuilder = () => {
    setEditingSectionId(null)
    setSectionName('')
    setSectionDescription('')
    setSectionInstructions('')
    setSectionScope('tenant')
    setSectionTargetType('template')
    setSectionTargetRef('')
    setSectionOrder(0)
    setSectionItems([])
  }

  const renderDynamicBuilder = () => {
    if (builder.uiType === 'yes_no') {
      return (
        <Card size="small" title="Yes / No Logic">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Text className="text-xs font-semibold">Positive Label</Text>
              <Input value={builder.yesLabel} onChange={(e) => setBuilder({ ...builder, yesLabel: e.target.value })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Negative Label</Text>
              <Input value={builder.noLabel} onChange={(e) => setBuilder({ ...builder, noLabel: e.target.value })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Expected Answer</Text>
              <Select
                className="w-full"
                value={builder.yesNoExpected}
                onChange={(v) => setBuilder({ ...builder, yesNoExpected: v })}
                options={[
                  { value: '', label: 'Not set' },
                  { value: 'yes', label: builder.yesLabel || 'Yes' },
                  { value: 'no', label: builder.noLabel || 'No' },
                ]}
              />
            </div>
            <div className="flex items-center gap-3 pt-6">
              <Switch checked={builder.knockout} onChange={(v) => setBuilder({ ...builder, knockout: v })} />
              <Text className="text-xs font-semibold">Knockout Question</Text>
            </div>
            <div>
              <Text className="text-xs font-semibold">Score for Positive</Text>
              <InputNumber className="w-full" value={builder.yesScore} onChange={(v) => setBuilder({ ...builder, yesScore: Number(v || 0) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Score for Negative</Text>
              <InputNumber className="w-full" value={builder.noScore} onChange={(v) => setBuilder({ ...builder, noScore: Number(v || 0) })} />
            </div>
          </div>
        </Card>
      )
    }

    if (builder.uiType === 'single_select' || builder.uiType === 'multi_select') {
      return (
        <Space direction="vertical" size={12} className="w-full">
          <Card size="small" title="Option Builder">
            <Space direction="vertical" size={8} className="w-full">
              {builder.options.map((opt, index) => (
                <div key={opt.id} className="border border-slate-200 rounded-lg p-3 bg-white flex items-center gap-2">
                  <Input
                    value={opt.label}
                    onChange={(e) => {
                      const next = [...builder.options]
                      next[index] = { ...opt, label: e.target.value }
                      setBuilder({ ...builder, options: next })
                    }}
                    placeholder={`Option ${index + 1}`}
                  />
                  <InputNumber
                    value={opt.score}
                    onChange={(v) => {
                      const next = [...builder.options]
                      next[index] = { ...opt, score: Number(v || 0) }
                      setBuilder({ ...builder, options: next })
                    }}
                    placeholder="Score"
                  />
                  <Checkbox
                    checked={opt.preferred}
                    onChange={(e) => {
                      const next = [...builder.options]
                      if (builder.uiType === 'single_select' && e.target.checked) {
                        for (let i = 0; i < next.length; i += 1) next[i] = { ...next[i], preferred: false }
                      }
                      next[index] = { ...opt, preferred: e.target.checked }
                      setBuilder({ ...builder, options: next })
                    }}
                  >Preferred</Checkbox>
                  <Button icon={<ArrowUpOutlined />} onClick={() => moveOption(index, -1)} />
                  <Button icon={<ArrowDownOutlined />} onClick={() => moveOption(index, 1)} />
                  <Button danger icon={<DeleteOutlined />} onClick={() => removeOption(opt.id)} />
                </div>
              ))}
              <Button icon={<PlusOutlined />} onClick={addOption}>Add Option</Button>
            </Space>
          </Card>
          {builder.uiType === 'multi_select' && (
            <Card size="small" title="Multi Select Rules">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <Text className="text-xs font-semibold">Minimum Selection</Text>
                  <InputNumber className="w-full" min={1} value={builder.multiMin} onChange={(v) => setBuilder({ ...builder, multiMin: Number(v || 1) })} />
                </div>
                <div>
                  <Text className="text-xs font-semibold">Maximum Selection</Text>
                  <InputNumber className="w-full" min={1} value={builder.multiMax} onChange={(v) => setBuilder({ ...builder, multiMax: Number(v || 1) })} />
                </div>
              </div>
            </Card>
          )}
        </Space>
      )
    }

    if (builder.uiType === 'short_text' || builder.uiType === 'long_text') {
      return (
        <Card size="small" title="Text Answer Rules">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Text className="text-xs font-semibold">Placeholder</Text>
              <Input value={builder.placeholder} onChange={(e) => setBuilder({ ...builder, placeholder: e.target.value })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Answer Hint</Text>
              <Input value={builder.answerHint} onChange={(e) => setBuilder({ ...builder, answerHint: e.target.value })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Character Limit</Text>
              <InputNumber className="w-full" min={1} value={builder.charLimit ?? undefined} onChange={(v) => setBuilder({ ...builder, charLimit: v == null ? null : Number(v) })} />
            </div>
            <div className="flex items-center gap-3 pt-6">
              <Switch checked={builder.manualEvaluation} onChange={(v) => setBuilder({ ...builder, manualEvaluation: v })} />
              <Text className="text-xs font-semibold">Manual Evaluation Required</Text>
            </div>
          </div>
        </Card>
      )
    }

    if (builder.uiType === 'number') {
      return (
        <Card size="small" title="Number Rules">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div>
              <Text className="text-xs font-semibold">Min Value</Text>
              <InputNumber className="w-full" value={builder.numberMin ?? undefined} onChange={(v) => setBuilder({ ...builder, numberMin: v == null ? null : Number(v) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Max Value</Text>
              <InputNumber className="w-full" value={builder.numberMax ?? undefined} onChange={(v) => setBuilder({ ...builder, numberMax: v == null ? null : Number(v) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Units</Text>
              <Input value={builder.numberUnits} onChange={(e) => setBuilder({ ...builder, numberUnits: e.target.value })} placeholder="years, %, INR" />
            </div>
          </div>
          <Divider className="my-3" />
          <Space direction="vertical" size={8} className="w-full">
            <Text className="text-xs font-semibold">Scoring Bands</Text>
            {builder.numberBands.map((band, index) => (
              <div key={band.id} className="grid grid-cols-4 gap-2 items-center">
                <InputNumber className="w-full" value={band.from} onChange={(v) => {
                  const next = [...builder.numberBands]
                  next[index] = { ...band, from: Number(v || 0) }
                  setBuilder({ ...builder, numberBands: next })
                }} />
                <InputNumber className="w-full" value={band.to} onChange={(v) => {
                  const next = [...builder.numberBands]
                  next[index] = { ...band, to: Number(v || 0) }
                  setBuilder({ ...builder, numberBands: next })
                }} />
                <InputNumber className="w-full" value={band.score} onChange={(v) => {
                  const next = [...builder.numberBands]
                  next[index] = { ...band, score: Number(v || 0) }
                  setBuilder({ ...builder, numberBands: next })
                }} />
                <Button danger icon={<DeleteOutlined />} onClick={() => {
                  setBuilder({ ...builder, numberBands: builder.numberBands.filter(b => b.id !== band.id) })
                }} />
              </div>
            ))}
            <Button icon={<PlusOutlined />} onClick={() => setBuilder({ ...builder, numberBands: [...builder.numberBands, { id: makeId(), from: 0, to: 0, score: 0 }] })}>Add Band</Button>
          </Space>
        </Card>
      )
    }

    if (builder.uiType === 'rating') {
      return (
        <Card size="small" title="Rating Rules">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Text className="text-xs font-semibold">Scale Size</Text>
              <InputNumber className="w-full" min={2} max={10} value={builder.ratingScale} onChange={(v) => setBuilder({ ...builder, ratingScale: Number(v || 5) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Min Label</Text>
              <Input value={builder.ratingMinLabel} onChange={(e) => setBuilder({ ...builder, ratingMinLabel: e.target.value })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Max Label</Text>
              <Input value={builder.ratingMaxLabel} onChange={(e) => setBuilder({ ...builder, ratingMaxLabel: e.target.value })} />
            </div>
          </div>
        </Card>
      )
    }

    if (builder.uiType === 'file_upload') {
      return (
        <Card size="small" title="File Upload Rules">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <Text className="text-xs font-semibold">Allowed File Types</Text>
              <Select mode="tags" className="w-full" value={builder.fileTypes} onChange={(v) => setBuilder({ ...builder, fileTypes: v })} options={['pdf', 'doc', 'docx', 'xls', 'csv', 'zip'].map(v => ({ value: v, label: v.toUpperCase() }))} />
            </div>
            <div>
              <Text className="text-xs font-semibold">File Count</Text>
              <InputNumber className="w-full" min={1} value={builder.fileCount} onChange={(v) => setBuilder({ ...builder, fileCount: Number(v || 1) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Size Limit (MB)</Text>
              <InputNumber className="w-full" min={1} value={builder.fileSizeMb} onChange={(v) => setBuilder({ ...builder, fileSizeMb: Number(v || 1) })} />
            </div>
            <div className="flex items-center gap-3 pt-6">
              <Switch checked={builder.fileMandatory} onChange={(v) => setBuilder({ ...builder, fileMandatory: v })} />
              <Text className="text-xs font-semibold">Mandatory</Text>
            </div>
          </div>
        </Card>
      )
    }

    if (builder.uiType === 'coding_question') {
      return (
        <Card size="small" title="Coding Shell Settings">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Text className="text-xs font-semibold">Language Selector</Text>
              <Select mode="multiple" className="w-full" value={builder.codingLanguages} onChange={(v) => setBuilder({ ...builder, codingLanguages: v })} options={['javascript', 'python', 'java', 'go', 'csharp', 'typescript'].map(v => ({ value: v, label: v }))} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Evaluation Mode</Text>
              <Select className="w-full" value={builder.codingEvaluationMode} onChange={(v) => setBuilder({ ...builder, codingEvaluationMode: v })} options={[{ value: 'manual', label: 'Manual Review' }, { value: 'hybrid', label: 'Hybrid (Shell)' }, { value: 'auto_shell', label: 'Auto Shell' }]} />
            </div>
            <div className="md:col-span-2">
              <Text className="text-xs font-semibold">Starter Code Shell</Text>
              <Input.TextArea rows={8} value={builder.codingStarterCode} onChange={(e) => setBuilder({ ...builder, codingStarterCode: e.target.value })} placeholder="// starter code" />
            </div>
          </div>
        </Card>
      )
    }

    if (builder.uiType === 'video_question') {
      return (
        <Card size="small" title="Video Shell Settings">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Text className="text-xs font-semibold">Max Duration (sec)</Text>
              <InputNumber className="w-full" min={30} value={builder.videoMaxDurationSec} onChange={(v) => setBuilder({ ...builder, videoMaxDurationSec: Number(v || 30) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Retries</Text>
              <InputNumber className="w-full" min={0} value={builder.videoRetries} onChange={(v) => setBuilder({ ...builder, videoRetries: Number(v || 0) })} />
            </div>
            <div>
              <Text className="text-xs font-semibold">Preparation Time (sec)</Text>
              <InputNumber className="w-full" min={0} value={builder.videoPrepTimeSec} onChange={(v) => setBuilder({ ...builder, videoPrepTimeSec: Number(v || 0) })} />
            </div>
          </div>
        </Card>
      )
    }

    return null
  }

  const renderPreview = () => {
    const title = builder.title || 'Untitled Question'
    if (builder.uiType === 'yes_no') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <Space>
            <Button>{builder.yesLabel}</Button>
            <Button>{builder.noLabel}</Button>
          </Space>
        </div>
      )
    }
    if (builder.uiType === 'single_select') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          {builder.options.map(o => (
            <div key={o.id} className="flex items-center justify-between">
              <Radio>{o.label || 'Option'}</Radio>
              {o.preferred && <Tag color="green">Preferred</Tag>}
            </div>
          ))}
        </div>
      )
    }
    if (builder.uiType === 'multi_select') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          {builder.options.map(o => <div key={o.id}><Checkbox>{o.label || 'Option'}</Checkbox></div>)}
          <Text type="secondary">Select {builder.multiMin} to {builder.multiMax} options</Text>
        </div>
      )
    }
    if (builder.uiType === 'short_text' || builder.uiType === 'long_text') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <Input.TextArea rows={builder.uiType === 'long_text' ? 5 : 2} placeholder={builder.placeholder || 'Write your answer...'} />
        </div>
      )
    }
    if (builder.uiType === 'number') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <InputNumber className="w-full" placeholder={builder.numberUnits ? `Enter value in ${builder.numberUnits}` : 'Enter value'} />
        </div>
      )
    }
    if (builder.uiType === 'rating') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <Space>
            {Array.from({ length: builder.ratingScale }).map((_, i) => (
              <Button key={i} shape="circle">{i + 1}</Button>
            ))}
          </Space>
          <div className="flex justify-between"><Text type="secondary">{builder.ratingMinLabel}</Text><Text type="secondary">{builder.ratingMaxLabel}</Text></div>
        </div>
      )
    }
    if (builder.uiType === 'file_upload') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <div className="border border-dashed rounded-lg p-6 text-center">
            <Text type="secondary">Upload files ({builder.fileTypes.join(', ').toUpperCase()})</Text>
          </div>
        </div>
      )
    }
    if (builder.uiType === 'coding_question') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <Tag>Language: {builder.codingLanguages.join(', ') || 'N/A'}</Tag>
          <Input.TextArea rows={6} placeholder="Code editor shell" value={builder.codingStarterCode} readOnly />
        </div>
      )
    }
    if (builder.uiType === 'video_question') {
      return (
        <div className="space-y-3">
          <Text className="font-semibold text-base">{title}</Text>
          <div className="border rounded-lg p-4 text-center">
            <Text>Video recorder shell ({builder.videoMaxDurationSec}s max)</Text>
          </div>
        </div>
      )
    }
    return <Empty description="No preview" />
  }

  const selectedQuestionUsage = selectedQuestion?.id ? usageByQuestion[selectedQuestion.id] || 0 : 0
  const selectedQuestionAttachments = useMemo(
    () => attachments.filter((a: any) => a?.question?.id === selectedQuestion?.id),
    [attachments, selectedQuestion?.id],
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} className="!mb-0">Interview Types / Question Bank</Title>
          <Text type="secondary">Enterprise question library for templates, interview types, and assessments</Text>
        </div>
        <Tag color="blue">ICC-INTERVIEW-QUESTION-ENGINE-01</Tag>
      </div>

      <Tabs
        defaultActiveKey="builder"
        items={[
          {
            key: 'builder',
            label: 'Question Builder',
            children: (
              <div className="grid grid-cols-1 xl:grid-cols-[330px_minmax(0,1fr)_320px] gap-4">
                <Card
                  title={<span className="font-semibold">Question Explorer</span>}
                  extra={<Button size="small" icon={<PlusOutlined />} onClick={createNewQuestion}>New</Button>}
                  className="h-[calc(100vh-260px)] overflow-hidden"
                  bodyStyle={{ height: 'calc(100% - 56px)', overflow: 'auto', paddingTop: 12 }}
                >
                  <Space direction="vertical" size={10} className="w-full">
                    <Input placeholder="Search questions" value={search} onChange={(e) => setSearch(e.target.value)} />
                    <div className="grid grid-cols-2 gap-2">
                      <Select placeholder="Type" value={typeFilter || undefined} allowClear onChange={(v) => setTypeFilter(v || '')} options={UI_TYPE_OPTIONS} />
                      <Select placeholder="Difficulty" value={difficultyFilter || undefined} allowClear onChange={(v) => setDifficultyFilter(v || '')} options={[{ value: 'easy' }, { value: 'medium' }, { value: 'hard' }]} />
                      <Select placeholder="Scope" value={scopeFilter || undefined} allowClear onChange={(v) => setScopeFilter(v || '')} options={[{ value: 'global' }, { value: 'tenant' }, { value: 'template' }]} />
                      <Select placeholder="Skill" value={skillFilter || undefined} allowClear onChange={(v) => setSkillFilter(v || '')} options={skillOptions.map(v => ({ value: v, label: v }))} />
                      <Select className="col-span-2" placeholder="Tag" value={tagFilter || undefined} allowClear onChange={(v) => setTagFilter(v || '')} options={tagOptions.map(v => ({ value: v, label: v }))} />
                    </div>
                    <Divider className="my-2" />

                    {filteredQuestions.length === 0 ? (
                      <Empty description="No questions found" />
                    ) : (
                      <List
                        dataSource={filteredQuestions}
                        renderItem={(q: any) => {
                          const isActive = q.id === selectedQuestionId
                          const uiType = backendToUiType(q)
                          const usage = usageByQuestion[q.id] || 0
                          return (
                            <List.Item
                              onClick={() => {
                                setIsCreatingNewQuestion(false)
                                setSelectedQuestionId(q.id)
                              }}
                              className={`cursor-pointer rounded-lg px-3 py-2 border ${isActive ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white'}`}
                            >
                              <div className="w-full space-y-1">
                                <div className="flex items-start justify-between gap-2">
                                  <Text className="font-semibold text-sm">{q.question_title}</Text>
                                  <TypeBadge type={uiType} />
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  <Tag>{q.difficulty}</Tag>
                                  <Tag>{q.scope}</Tag>
                                  <Tag>Usage {usage}</Tag>
                                </div>
                                <Text type="secondary" className="text-xs block">Updated {dayjs(q.updated_at).format('DD MMM YYYY')}</Text>
                              </div>
                            </List.Item>
                          )
                        }}
                      />
                    )}
                  </Space>
                </Card>

                <Space direction="vertical" size={12} className="w-full">
                  <Card
                    title="Main Builder"
                    extra={
                      <Space>
                        {builder.id && <Tag color="processing">Editing</Tag>}
                        <Button
                          type="primary"
                          icon={<SaveOutlined />}
                          loading={saveQuestionM.isPending}
                          onClick={saveQuestion}
                          disabled={questionValidationErrors.length > 0}
                        >
                          Save Question
                        </Button>
                      </Space>
                    }
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                      <div className="md:col-span-2">
                        <Text className="text-xs font-semibold">Question Title</Text>
                        <Input value={builder.title} onChange={(e) => setBuilder({ ...builder, title: e.target.value })} placeholder="Enter question title" />
                      </div>
                      <div className="md:col-span-2">
                        <Text className="text-xs font-semibold">Description</Text>
                        <Input.TextArea rows={3} value={builder.description} onChange={(e) => setBuilder({ ...builder, description: e.target.value })} placeholder="Instructions/context" />
                      </div>
                      <div>
                        <Text className="text-xs font-semibold">Question Type</Text>
                        <Select
                          className="w-full"
                          value={builder.uiType}
                          onChange={(v) => setBuilder({ ...builder, uiType: v })}
                          options={UI_TYPE_OPTIONS}
                        />
                      </div>
                      <div>
                        <Text className="text-xs font-semibold">Expected Answer (Optional)</Text>
                        <Input value={builder.expectedAnswer} onChange={(e) => setBuilder({ ...builder, expectedAnswer: e.target.value })} />
                      </div>
                    </div>

                    {questionValidationErrors.length > 0 && (
                      <Alert
                        className="mb-3"
                        type="warning"
                        showIcon
                        message="Validation Required"
                        description={questionValidationErrors[0]}
                      />
                    )}

                    {renderDynamicBuilder()}
                  </Card>
                </Space>

                <Card title="Configuration Panel" className="h-[calc(100vh-260px)] overflow-hidden" bodyStyle={{ height: 'calc(100% - 56px)', overflow: 'auto' }}>
                  <Space direction="vertical" size={10} className="w-full">
                    <div>
                      <Text className="text-xs font-semibold">Scope</Text>
                      <Select className="w-full" value={builder.scope} onChange={(v) => setBuilder({ ...builder, scope: v })} options={[{ value: 'global' }, { value: 'tenant' }, { value: 'template' }]} />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Difficulty</Text>
                      <Select className="w-full" value={builder.difficulty} onChange={(v) => setBuilder({ ...builder, difficulty: v })} options={[{ value: 'easy' }, { value: 'medium' }, { value: 'hard' }]} />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Scoring Weight</Text>
                      <InputNumber className="w-full" min={0} step={0.5} value={builder.scoringWeight} onChange={(v) => setBuilder({ ...builder, scoringWeight: Number(v || 0) })} />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Skills</Text>
                      <Select mode="tags" className="w-full" value={builder.skills} onChange={(v) => setBuilder({ ...builder, skills: v })} options={skillOptions.map(v => ({ value: v, label: v }))} />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Tags</Text>
                      <Select mode="tags" className="w-full" value={builder.tags} onChange={(v) => setBuilder({ ...builder, tags: v })} options={tagOptions.map(v => ({ value: v, label: v }))} />
                    </div>
                    <Divider className="my-2" />
                    <div className="space-y-1">
                      <Text className="text-xs font-semibold">Usage Snapshot</Text>
                      <div className="flex flex-wrap gap-2">
                        <Tag>Used {selectedQuestionUsage} times</Tag>
                        <Tag>{builder.scope} scope</Tag>
                        <Tag>{builder.difficulty}</Tag>
                      </div>
                    </div>
                  </Space>
                </Card>
              </div>
            ),
          },
          {
            key: 'attach',
            label: 'Attach & Usage',
            children: (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card title="Attach Question to Destination">
                  <Space direction="vertical" size={12} className="w-full">
                    <div>
                      <Text className="text-xs font-semibold">Question</Text>
                      <Select
                        className="w-full"
                        value={selectedQuestionId || undefined}
                        onChange={(v) => {
                          setIsCreatingNewQuestion(false)
                          setSelectedQuestionId(v)
                        }}
                        options={questions.map((q: any) => ({ value: q.id, label: q.question_title }))}
                        placeholder="Select question"
                      />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Attach To</Text>
                      <Select className="w-full" value={attachType} onChange={(v) => setAttachType(v)} options={[{ value: 'template', label: 'Interview Template' }, { value: 'interview_type', label: 'Interview Type Default Bank' }, { value: 'assessment', label: 'Assessment' }]} />
                    </div>

                    {attachType === 'template' && (
                      <div>
                        <Text className="text-xs font-semibold">Template</Text>
                        <Select
                          className="w-full"
                          value={attachTemplateId}
                          onChange={setAttachTemplateId}
                          placeholder="Select template"
                          options={templates.map((t: any) => ({ value: t.id, label: t.name || t.title || t.id }))}
                        />
                      </div>
                    )}

                    {attachType === 'interview_type' && (
                      <div>
                        <Text className="text-xs font-semibold">Interview Type</Text>
                        <Select
                          className="w-full"
                          value={attachInterviewType}
                          onChange={setAttachInterviewType}
                          placeholder="Select interview type"
                          options={interviewTypes.map((t: any) => ({ value: t.code, label: t.name || t.code }))}
                        />
                      </div>
                    )}

                    {attachType === 'assessment' && (
                      <div>
                        <Text className="text-xs font-semibold">Assessment Reference</Text>
                        <Input
                          value={attachAssessmentRef}
                          onChange={(e) => setAttachAssessmentRef(e.target.value)}
                          placeholder="e.g. technical_assessment_v1"
                        />
                      </div>
                    )}

                    <div>
                      <Text className="text-xs font-semibold">Order</Text>
                      <InputNumber className="w-full" min={0} value={attachOrder} onChange={(v) => setAttachOrder(Number(v || 0))} />
                    </div>

                    <Button type="primary" icon={<LinkOutlined />} loading={attachQuestionM.isPending} onClick={attachQuestion}>Attach Question</Button>
                  </Space>
                </Card>

                <Card title="Existing Attachments">
                  {selectedQuestion?.id && (
                    <>
                      <div className="mb-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                        <Text className="text-xs font-semibold block">Selected Question Usage</Text>
                        <Text type="secondary" className="text-xs">
                          {selectedQuestion.question_title} is attached {selectedQuestionUsage} time(s)
                        </Text>
                      </div>
                    </>
                  )}
                  {attachments.length === 0 ? (
                    <Empty description="No attachments yet" />
                  ) : (
                    <List
                      dataSource={selectedQuestion?.id ? selectedQuestionAttachments : attachments}
                      renderItem={(a: any) => (
                        <List.Item>
                          <div className="w-full">
                            <div className="flex items-center justify-between">
                              <Text className="font-semibold">{a.question?.question_title || 'Question'}</Text>
                              <Tag>{a.attach_type}</Tag>
                            </div>
                            <Text type="secondary" className="text-xs">
                              {a.attach_type === 'template' && `Template: ${a.template_id || '-'}`}
                              {a.attach_type === 'interview_type' && `Interview Type: ${a.interview_type || '-'}`}
                              {a.attach_type === 'assessment' && `Assessment: ${a.assessment_ref || '-'}`}
                            </Text>
                          </div>
                        </List.Item>
                      )}
                    />
                  )}
                </Card>
              </div>
            ),
          },
          {
            key: 'grouping',
            label: 'Sections / Grouping',
            children: (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card
                  title={editingSectionId ? 'Section Builder (Editing)' : 'Section Builder'}
                  extra={
                    editingSectionId ? (
                      <Button size="small" onClick={resetSectionBuilder}>Create New Section</Button>
                    ) : undefined
                  }
                >
                  <Space direction="vertical" size={12} className="w-full">
                    <div>
                      <Text className="text-xs font-semibold">Section Name</Text>
                      <Input value={sectionName} onChange={(e) => setSectionName(e.target.value)} placeholder="Behavioral Fundamentals" />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Section Description</Text>
                      <Input.TextArea rows={2} value={sectionDescription} onChange={(e) => setSectionDescription(e.target.value)} />
                    </div>
                    <div>
                      <Text className="text-xs font-semibold">Section Instructions</Text>
                      <Input.TextArea rows={2} value={sectionInstructions} onChange={(e) => setSectionInstructions(e.target.value)} placeholder="Ask all questions in STAR format" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <Text className="text-xs font-semibold">Scope</Text>
                        <Select className="w-full" value={sectionScope} onChange={(v) => setSectionScope(v)} options={[{ value: 'global' }, { value: 'tenant' }, { value: 'template' }]} />
                      </div>
                      <div>
                        <Text className="text-xs font-semibold">Order</Text>
                        <InputNumber className="w-full" min={0} value={sectionOrder} onChange={(v) => setSectionOrder(Number(v || 0))} />
                      </div>
                      <div>
                        <Text className="text-xs font-semibold">Attach Section To</Text>
                        <Select className="w-full" value={sectionTargetType} onChange={(v) => setSectionTargetType(v)} options={[{ value: 'template', label: 'Template' }, { value: 'interview_type', label: 'Interview Type' }, { value: 'assessment', label: 'Assessment' }]} />
                      </div>
                      <div>
                        <Text className="text-xs font-semibold">Destination</Text>
                        {sectionTargetType === 'template' ? (
                          <Select className="w-full" value={sectionTargetRef || undefined} onChange={(v) => setSectionTargetRef(v || '')} options={templates.map((t: any) => ({ value: t.id, label: t.name || t.title || t.id }))} />
                        ) : sectionTargetType === 'interview_type' ? (
                          <Select className="w-full" value={sectionTargetRef || undefined} onChange={(v) => setSectionTargetRef(v || '')} options={interviewTypes.map((t: any) => ({ value: t.code, label: t.name || t.code }))} />
                        ) : (
                          <Input value={sectionTargetRef} onChange={(e) => setSectionTargetRef(e.target.value)} placeholder="assessment_ref" />
                        )}
                      </div>
                    </div>

                    <Divider className="my-2" />

                    <div>
                      <Text className="text-xs font-semibold">Add Questions</Text>
                      <Select
                        className="w-full"
                        showSearch
                        placeholder="Select a question"
                        options={questions.map((q: any) => ({ value: q.id, label: q.question_title }))}
                        onSelect={(v) => addSectionQuestion(String(v))}
                      />
                    </div>

                    <Space direction="vertical" size={8} className="w-full">
                      {sectionItems.map((item, index) => {
                        const q = questions.find((x: any) => x.id === item.question_id)
                        return (
                          <div key={item.question_id} className="border rounded-lg p-3 flex items-center gap-2">
                            <div className="flex-1">
                              <Text className="font-medium text-sm">{q?.question_title || item.question_id}</Text>
                            </div>
                            <Checkbox
                              checked={item.required}
                              onChange={(e) => {
                                const next = [...sectionItems]
                                next[index] = { ...item, required: e.target.checked }
                                setSectionItems(next)
                              }}
                            >Required</Checkbox>
                            <Button icon={<ArrowUpOutlined />} onClick={() => moveSectionQuestion(index, -1)} />
                            <Button icon={<ArrowDownOutlined />} onClick={() => moveSectionQuestion(index, 1)} />
                            <Button danger icon={<DeleteOutlined />} onClick={() => setSectionItems(sectionItems.filter(i => i.question_id !== item.question_id))} />
                          </div>
                        )
                      })}
                    </Space>

                    <Button type="primary" icon={<FolderOpenOutlined />} loading={createGroupM.isPending} onClick={saveSection}>
                      {editingSectionId ? 'Update Section' : 'Save Section'}
                    </Button>
                  </Space>
                </Card>

                <Card title="Existing Sections">
                  {groups.length === 0 ? (
                    <Empty description="No sections yet" />
                  ) : (
                    <List
                      dataSource={groups}
                      renderItem={(g: any) => (
                        <List.Item>
                          <div className="w-full">
                            <div className="flex items-center justify-between">
                              <Text className="font-semibold">{g.name}</Text>
                              <Space>
                                <Tag>{g.target_type}</Tag>
                                <Button size="small" onClick={() => loadSectionForEdit(g)}>Edit</Button>
                              </Space>
                            </div>
                            <Text type="secondary" className="text-xs block">{g.description || '-'}</Text>
                            <Text type="secondary" className="text-xs block">Target: {g.target_ref || '-'}</Text>
                            <Text type="secondary" className="text-xs block">Questions: {(g.items || []).length}</Text>
                          </div>
                        </List.Item>
                      )}
                    />
                  )}
                </Card>
              </div>
            ),
          },
          {
            key: 'preview',
            label: 'Preview',
            children: (
              <Card title="Candidate / Interviewer Preview" extra={<Button icon={<EyeOutlined />} onClick={() => message.info('Preview is live and reflects current builder state')}>Refresh Preview</Button>}>
                {renderPreview()}
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}
