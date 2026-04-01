import { useMemo, useState } from 'react'
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
  ArrowLeft,
  Copy,
  Eye,
  MessageSquareQuote,
  Plus,
  Settings2,
  Shield,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type MockEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'structure' | 'feedback' | 'preview'
type PracticeType = 'technical' | 'hr' | 'behavioral' | 'ai_practice'
type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced'

type MockInterviewDraft = {
  id: string | null
  name: string
  role_domain: string
  practice_type: PracticeType
  duration_minutes: number
  description: string
  is_active: boolean
  structure: {
    topics_to_cover: string[]
    question_selection: string
    difficulty_level: DifficultyLevel
    evaluation_focus: string[]
  }
  feedback_model: {
    feedback_template: string
    improvement_suggestions: string
    scoring_enabled: boolean
    recommendation: string
    scorecard_template_id: string
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'structure', label: '2. Interview Structure', icon: MessageSquareQuote },
  { key: 'feedback', label: '3. Feedback Model', icon: ShieldCheck },
  { key: 'preview', label: '4. Usage / Preview', icon: Eye },
]

const PRACTICE_TYPE_OPTIONS = [
  { value: 'technical', label: 'Technical' },
  { value: 'hr', label: 'HR' },
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'ai_practice', label: 'AI Practice' },
]

const DIFFICULTY_OPTIONS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

function createDraft(): MockInterviewDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    practice_type: 'technical',
    duration_minutes: 45,
    description: '',
    is_active: true,
    structure: {
      topics_to_cover: ['problem solving', 'communication'],
      question_selection: 'mixed_question_bank_and_custom',
      difficulty_level: 'intermediate',
      evaluation_focus: ['clarity', 'confidence', 'depth'],
    },
    feedback_model: {
      feedback_template: 'coach_style_actionable_feedback',
      improvement_suggestions: 'Highlight strengths first, then provide targeted practice recommendations.',
      scoring_enabled: true,
      recommendation: 'practice_more_then_retry',
      scorecard_template_id: '',
    },
  }
}

function parseTemplate(record: any): MockInterviewDraft {
  const meta = record?.metadata?.mock_interview || {}
  const base = createDraft()
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    practice_type: meta.setup?.practice_type || base.practice_type,
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    structure: {
      topics_to_cover: Array.isArray(meta.structure?.topics_to_cover) ? meta.structure.topics_to_cover : base.structure.topics_to_cover,
      question_selection: meta.structure?.question_selection || base.structure.question_selection,
      difficulty_level: meta.structure?.difficulty_level || base.structure.difficulty_level,
      evaluation_focus: Array.isArray(meta.structure?.evaluation_focus) ? meta.structure.evaluation_focus : base.structure.evaluation_focus,
    },
    feedback_model: {
      feedback_template: meta.feedback_model?.feedback_template || base.feedback_model.feedback_template,
      improvement_suggestions: meta.feedback_model?.improvement_suggestions || base.feedback_model.improvement_suggestions,
      scoring_enabled: meta.feedback_model?.scoring_enabled ?? base.feedback_model.scoring_enabled,
      recommendation: meta.feedback_model?.recommendation || base.feedback_model.recommendation,
      scorecard_template_id: meta.feedback_model?.scorecard_template_id || '',
    },
  }
}

function serializeDraft(draft: MockInterviewDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'mock_interview',
    duration_minutes: draft.duration_minutes,
    instructions: draft.structure.topics_to_cover.join(', '),
    scoring_type: draft.feedback_model.scoring_enabled ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      mock_interview: {
        setup: {
          role_domain: draft.role_domain,
          practice_type: draft.practice_type,
        },
        structure: draft.structure,
        feedback_model: draft.feedback_model,
        usage: existing.metadata?.mock_interview?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          scorecard_engine: true,
          question_engine: true,
          scheduling_engine: true,
          decision_engine: true,
        },
      },
    },
  }
}

export default function InterviewMockEngine({ embedded = false }: MockEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<MockInterviewDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const mockTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'mock_interview' || template.metadata?.mock_interview)
        .map((template: any) => ({ ...template, parsed: parseTemplate(template) })),
    [allTemplates],
  )

  const usageByTemplateId = useMemo(() => {
    const usageMap = new Map<string, { flows: string[]; stages: string[] }>()
    flows.forEach((flow: any) => {
      const flowName = flow.name || 'Untitled flow'
      ;(flow.stages || []).forEach((stage: any) => {
        const templateId = stage.template_id || stage.ai_template_id || stage.metadata?.template_id
        if (!templateId) return
        const current = usageMap.get(templateId) || { flows: [], stages: [] }
        if (!current.flows.includes(flowName)) current.flows.push(flowName)
        if (stage.name && !current.stages.includes(stage.name)) current.stages.push(stage.name)
        usageMap.set(templateId, current)
      })
    })
    return usageMap
  }, [flows])

  const selectedTemplateRecord = mockTemplates.find((template: any) => template.id === selectedTemplateId) || null
  const currentUsage = selectedTemplateId ? usageByTemplateId.get(selectedTemplateId) : null
  const stepIndex = WIZARD_STEPS.findIndex((step) => step.key === activeStep)

  const openCreate = () => {
    setSelectedTemplateId(null)
    setDraft(createDraft())
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = (record: any) => {
    setSelectedTemplateId(record.id)
    setDraft(parseTemplate(record))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const handleDuplicate = async (record: any) => {
    try {
      await interviewsApi.createTemplate(
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Mock Interview'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Mock interview duplicated')
    } catch {
      message.error('Failed to duplicate mock interview')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Mock interview archived')
    } catch {
      message.error('Failed to archive mock interview')
    }
  }

  const handleSave = async () => {
    if (!draft.name.trim()) {
      message.error('Interview name is required')
      setActiveStep('setup')
      return
    }
    setSaving(true)
    try {
      const existing = selectedTemplateRecord || {}
      const payload = serializeDraft(draft, existing)
      if (selectedTemplateId) {
        await interviewsApi.updateTemplate(selectedTemplateId, { ...existing, ...payload })
      } else {
        await interviewsApi.createTemplate(payload)
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Mock interview saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save mock interview')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Mock Interview'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="default">Mock Interview</Tag> },
    { title: 'Role / Domain', key: 'role', render: (_, record) => <Text>{record.parsed.role_domain || 'Not set'}</Text> },
    { title: 'Duration', key: 'duration', render: (_, record) => <Text>{record.duration_minutes || 45} min</Text> },
    { title: 'Status', key: 'status', render: (_, record) => <Tag color={record.is_active ? 'success' : 'default'}>{record.is_active ? 'Active' : 'Archived'}</Tag> },
    {
      title: 'Usage Count',
      key: 'usage',
      render: (_, record) => {
        const usage = usageByTemplateId.get(record.id)
        return <Text>{(usage?.flows.length || 0) + (usage?.stages.length || 0)}</Text>
      },
    },
    {
      title: 'Last Updated',
      key: 'updated',
      render: (_, record) => <Text className="text-xs text-slate-500">{new Date(record.updated_at || record.created_at).toLocaleDateString()}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div className="flex flex-wrap gap-2">
          <Button size="small" onClick={() => openEdit(record)}>Edit</Button>
          <Button size="small" icon={<Copy size={14} />} onClick={() => handleDuplicate(record)}>Duplicate</Button>
          <Button size="small" onClick={() => { openEdit(record); setPreviewOpen(true); setActiveStep('preview') }}>Preview</Button>
          <Button size="small" danger onClick={() => handleArchive(record)}>Archive</Button>
        </div>
      ),
    },
  ]

  if (!isBuilderOpen) {
    return (
      <div className={cn('space-y-6', embedded ? '' : 'p-6')}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Mock Interview</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable practice interviews for preparation, coaching, and pre-panel readiness.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={mockTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No mock interviews yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Mock Interviews
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button
                key={step.key}
                type="button"
                onClick={() => setActiveStep(step.key)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition',
                  activeStep === step.key ? 'border-slate-300 bg-slate-100 text-slate-900' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                )}
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white">
                  <Icon size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-black uppercase tracking-wider">{step.label}</div>
                </div>
              </button>
            )
          })}
        </div>
      </Card>

      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Mock Interview Builder</h3>
            <p className="text-sm text-slate-500">Configure practice structure, coaching feedback, and optional scoring guidance.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Mock Interview</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Frontend Mock Round" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Frontend Engineering" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Type</Text>
                <Select value={draft.practice_type} onChange={(value) => setDraft((current) => ({ ...current, practice_type: value }))} options={PRACTICE_TYPE_OPTIONS} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={15} max={180} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Practice interview focused on confidence, structure, and targeted preparation." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'structure' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Topics To Cover</Text>
                <Select mode="tags" value={draft.structure.topics_to_cover} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, topics_to_cover: value } }))} placeholder="problem solving, self introduction, system design" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Question Selection</Text>
                <Input value={draft.structure.question_selection} onChange={(e) => setDraft((current) => ({ ...current, structure: { ...current.structure, question_selection: e.target.value } }))} placeholder="mixed_question_bank_and_custom" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Difficulty Level</Text>
                <Select value={draft.structure.difficulty_level} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, difficulty_level: value } }))} options={DIFFICULTY_OPTIONS} />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluation Focus</Text>
                <Select mode="tags" value={draft.structure.evaluation_focus} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, evaluation_focus: value } }))} placeholder="clarity, technical depth, composure" />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'feedback' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Feedback Template</Text>
                <Input value={draft.feedback_model.feedback_template} onChange={(e) => setDraft((current) => ({ ...current, feedback_model: { ...current.feedback_model, feedback_template: e.target.value } }))} placeholder="coach_style_actionable_feedback" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Improvement Suggestions</Text>
                <TextArea rows={4} value={draft.feedback_model.improvement_suggestions} onChange={(e) => setDraft((current) => ({ ...current, feedback_model: { ...current.feedback_model, improvement_suggestions: e.target.value } }))} placeholder="Recommend rehearsal areas, pacing, structure, and follow-up preparation." />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Scoring</div>
                  <div className="text-sm text-slate-500">Enable optional practice scoring aligned with scorecards.</div>
                </div>
                <Select value={draft.feedback_model.scoring_enabled ? 'enabled' : 'disabled'} onChange={(value) => setDraft((current) => ({ ...current, feedback_model: { ...current.feedback_model, scoring_enabled: value === 'enabled' } }))} options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]} className="w-32" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Recommendation</Text>
                <Input value={draft.feedback_model.recommendation} onChange={(e) => setDraft((current) => ({ ...current, feedback_model: { ...current.feedback_model, recommendation: e.target.value } }))} placeholder="practice_more_then_retry" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.feedback_model.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, feedback_model: { ...current.feedback_model, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'preview' ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Preview Summary</div>
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Mock Interview'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-xs font-black uppercase tracking-wider text-slate-400">Practice Type</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{PRACTICE_TYPE_OPTIONS.find((option) => option.value === draft.practice_type)?.label}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-xs font-black uppercase tracking-wider text-slate-400">Difficulty</div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">{DIFFICULTY_OPTIONS.find((option) => option.value === draft.structure.difficulty_level)?.label}</div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 p-3">
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Topics</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {draft.structure.topics_to_cover.map((topic) => <Tag key={topic}>{topic}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Flows</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(currentUsage?.flows || []).length ? currentUsage?.flows.map((flow) => <Tag key={flow}>{flow}</Tag>) : <Text className="text-sm text-slate-500">No linked flows yet</Text>}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Coaching Outcome</div>
                  <div className="mt-2 text-sm text-slate-600">{draft.feedback_model.recommendation || 'Recommendation pending'}</div>
                </div>
              </div>
            </Card>
          </div>
        ) : null}

        <div className="flex items-center justify-between">
          <Button onClick={() => setActiveStep(WIZARD_STEPS[Math.max(stepIndex - 1, 0)].key)} disabled={stepIndex === 0}>Back</Button>
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Mock Interview</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Mock Interview Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Practice Session</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Mock Interview'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.description || 'Mock interview description pending.'}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs font-black uppercase tracking-wider text-slate-400">Topics</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {draft.structure.topics_to_cover.map((topic) => <Tag key={topic}>{topic}</Tag>)}
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs font-black uppercase tracking-wider text-slate-400">Improvement Suggestions</div>
              <div className="mt-2 text-sm text-slate-600">{draft.feedback_model.improvement_suggestions}</div>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
