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
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Building2,
  Copy,
  Eye,
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

type AssessmentCenterEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'exercises' | 'evaluation' | 'scheduling' | 'preview'
type ExerciseType = 'group_discussion' | 'role_play' | 'case_study' | 'presentation' | 'technical_task'

type AssessmentExercise = {
  id: string
  exercise_name: string
  exercise_type: ExerciseType
  exercise_duration: number
  exercise_order: number
}

type AssessmentCenterDraft = {
  id: string | null
  name: string
  role_domain: string
  duration_minutes: number
  description: string
  is_active: boolean
  exercises: AssessmentExercise[]
  evaluation_model: {
    per_exercise_scoring: boolean
    overall_scoring: boolean
    scorecard_template_id: string
    pass_threshold: number
  }
  scheduling_model: {
    multi_session_scheduling: boolean
    evaluator_assignment: string[]
    candidate_grouping: string
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'exercises', label: '2. Exercise Builder', icon: Layers3 },
  { key: 'evaluation', label: '3. Evaluation Model', icon: ShieldCheck },
  { key: 'scheduling', label: '4. Scheduling Model', icon: Building2 },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const EXERCISE_OPTIONS = [
  { value: 'group_discussion', label: 'Group Discussion' },
  { value: 'role_play', label: 'Role Play' },
  { value: 'case_study', label: 'Case Study' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'technical_task', label: 'Technical Task' },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createExercise(overrides: Partial<AssessmentExercise> = {}): AssessmentExercise {
  return {
    id: makeId('assessment-exercise'),
    exercise_name: '',
    exercise_type: 'group_discussion',
    exercise_duration: 30,
    exercise_order: 1,
    ...overrides,
  }
}

function createDraft(): AssessmentCenterDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    duration_minutes: 180,
    description: '',
    is_active: true,
    exercises: [
      createExercise({ exercise_name: 'Opening Group Discussion', exercise_type: 'group_discussion', exercise_duration: 45, exercise_order: 1 }),
      createExercise({ exercise_name: 'Role Play Scenario', exercise_type: 'role_play', exercise_duration: 30, exercise_order: 2 }),
      createExercise({ exercise_name: 'Case Presentation', exercise_type: 'presentation', exercise_duration: 45, exercise_order: 3 }),
    ],
    evaluation_model: {
      per_exercise_scoring: true,
      overall_scoring: true,
      scorecard_template_id: '',
      pass_threshold: 75,
    },
    scheduling_model: {
      multi_session_scheduling: false,
      evaluator_assignment: [],
      candidate_grouping: 'cohort_batch_a',
    },
  }
}

function parseTemplate(record: any): AssessmentCenterDraft {
  const meta = record?.metadata?.assessment_center || {}
  const base = createDraft()
  const exercises = Array.isArray(meta.exercises) && meta.exercises.length
    ? meta.exercises.map((exercise: any, index: number) => ({
        id: exercise.id || makeId('assessment-exercise'),
        exercise_name: exercise.exercise_name || `Exercise ${index + 1}`,
        exercise_type: exercise.exercise_type || 'group_discussion',
        exercise_duration: Number(exercise.exercise_duration ?? 30),
        exercise_order: Number(exercise.exercise_order ?? index + 1),
      }))
    : base.exercises

  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    exercises,
    evaluation_model: {
      per_exercise_scoring: meta.evaluation_model?.per_exercise_scoring ?? true,
      overall_scoring: meta.evaluation_model?.overall_scoring ?? true,
      scorecard_template_id: meta.evaluation_model?.scorecard_template_id || '',
      pass_threshold: Number(meta.evaluation_model?.pass_threshold ?? base.evaluation_model.pass_threshold),
    },
    scheduling_model: {
      multi_session_scheduling: meta.scheduling_model?.multi_session_scheduling ?? false,
      evaluator_assignment: Array.isArray(meta.scheduling_model?.evaluator_assignment) ? meta.scheduling_model.evaluator_assignment : [],
      candidate_grouping: meta.scheduling_model?.candidate_grouping || 'cohort_batch_a',
    },
  }
}

function serializeDraft(draft: AssessmentCenterDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'assessment_center',
    duration_minutes: draft.duration_minutes,
    instructions: draft.exercises.map((exercise) => `${exercise.exercise_name}: ${exercise.exercise_type}`).join('\n'),
    scoring_type: draft.evaluation_model.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      assessment_center: {
        setup: {
          role_domain: draft.role_domain,
        },
        exercises: draft.exercises,
        evaluation_model: draft.evaluation_model,
        scheduling_model: draft.scheduling_model,
        usage: existing.metadata?.assessment_center?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          scorecard_engine: true,
          flow_engine: true,
          scheduling_engine: true,
          decision_engine: true,
        },
      },
    },
  }
}

export default function InterviewAssessmentCenterEngine({ embedded = false }: AssessmentCenterEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<AssessmentCenterDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const assessmentCenterTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'assessment_center' || template.metadata?.assessment_center)
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

  const selectedTemplateRecord = assessmentCenterTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Assessment Center'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Assessment center duplicated')
    } catch {
      message.error('Failed to duplicate assessment center')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Assessment center archived')
    } catch {
      message.error('Failed to archive assessment center')
    }
  }

  const handleSave = async () => {
    if (!draft.name.trim()) {
      message.error('Assessment name is required')
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
      message.success('Assessment center saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save assessment center')
    } finally {
      setSaving(false)
    }
  }

  const addExercise = () => {
    setDraft((current) => {
      const nextOrder = current.exercises.length + 1
      return {
        ...current,
        exercises: [...current.exercises, createExercise({ exercise_name: `Exercise ${nextOrder}`, exercise_order: nextOrder })],
      }
    })
  }

  const updateExercise = (id: string, patch: Partial<AssessmentExercise>) => {
    setDraft((current) => ({
      ...current,
      exercises: current.exercises.map((exercise) => (exercise.id === id ? { ...exercise, ...patch } : exercise)),
    }))
  }

  const reorderExercise = (id: string, direction: -1 | 1) => {
    setDraft((current) => {
      const index = current.exercises.findIndex((exercise) => exercise.id === id)
      const nextIndex = index + direction
      if (index < 0 || nextIndex < 0 || nextIndex >= current.exercises.length) return current
      const exercises = [...current.exercises]
      ;[exercises[index], exercises[nextIndex]] = [exercises[nextIndex], exercises[index]]
      return { ...current, exercises: exercises.map((exercise, idx) => ({ ...exercise, exercise_order: idx + 1 })) }
    })
  }

  const removeExercise = (id: string) => {
    setDraft((current) => ({
      ...current,
      exercises: current.exercises.filter((exercise) => exercise.id !== id).map((exercise, idx) => ({ ...exercise, exercise_order: idx + 1 })),
    }))
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Assessment Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Assessment Center'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="default">Assessment Center</Tag> },
    { title: 'Exercises Count', key: 'exercises', render: (_, record) => <Text>{record.parsed.exercises.length}</Text> },
    { title: 'Duration', key: 'duration', render: (_, record) => <Text>{record.duration_minutes || 180} min</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Assessment Center</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable multi-exercise assessment centers for structured high-volume evaluation.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={assessmentCenterTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No assessment centers yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Assessment Centers
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button key={step.key} type="button" onClick={() => setActiveStep(step.key)} className={cn('flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition', activeStep === step.key ? 'border-slate-300 bg-slate-100 text-slate-900' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300')}>
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Assessment Center Builder</h3>
            <p className="text-sm text-slate-500">Configure multi-exercise assessment flow, scoring, and scheduling model.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Assessment Center</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Assessment Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Graduate Assessment Center" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Business Analyst" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={30} max={480} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div />
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Multi-exercise assessment center with structured scoring across several exercises." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'exercises' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-900">Exercise Builder</h4>
                <p className="text-sm text-slate-500">Add exercises, define exercise type, order, and duration.</p>
              </div>
              <Button onClick={addExercise}><Plus size={14} />Add Exercise</Button>
            </div>
            <div className="space-y-4">
              {draft.exercises.map((exercise, index) => (
                <div key={exercise.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-black uppercase tracking-wider text-slate-400">Exercise {index + 1}</div>
                      <div className="text-sm font-semibold text-slate-900">{exercise.exercise_name || `Exercise ${index + 1}`}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="small" icon={<ArrowUp size={14} />} onClick={() => reorderExercise(exercise.id, -1)} disabled={index === 0} />
                      <Button size="small" icon={<ArrowDown size={14} />} onClick={() => reorderExercise(exercise.id, 1)} disabled={index === draft.exercises.length - 1} />
                      <Button size="small" danger icon={<Trash2 size={14} />} onClick={() => removeExercise(exercise.id)} />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Exercise Name</Text>
                      <Input value={exercise.exercise_name} onChange={(e) => updateExercise(exercise.id, { exercise_name: e.target.value })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Exercise Type</Text>
                      <Select value={exercise.exercise_type} onChange={(value) => updateExercise(exercise.id, { exercise_type: value })} options={EXERCISE_OPTIONS} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Exercise Duration</Text>
                      <InputNumber className="w-full" min={10} value={exercise.exercise_duration} onChange={(value) => updateExercise(exercise.id, { exercise_duration: Number(value || 0) })} addonAfter="min" />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Exercise Order</Text>
                      <InputNumber className="w-full" min={1} value={exercise.exercise_order} onChange={(value) => updateExercise(exercise.id, { exercise_order: Number(value || 1) })} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div><div className="text-xs font-black uppercase tracking-wider text-slate-400">Per Exercise Scoring</div></div>
                <Select value={draft.evaluation_model.per_exercise_scoring ? 'enabled' : 'disabled'} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, per_exercise_scoring: value === 'enabled' } }))} options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]} className="w-32" />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div><div className="text-xs font-black uppercase tracking-wider text-slate-400">Overall Scoring</div></div>
                <Select value={draft.evaluation_model.overall_scoring ? 'enabled' : 'disabled'} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, overall_scoring: value === 'enabled' } }))} options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]} className="w-32" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.evaluation_model.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Pass Threshold</Text>
                <InputNumber className="w-full" min={0} max={100} value={draft.evaluation_model.pass_threshold} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, pass_threshold: Number(value || 0) } }))} addonAfter="%" />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'scheduling' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div><div className="text-xs font-black uppercase tracking-wider text-slate-400">Multi-Session Scheduling</div></div>
                <Select value={draft.scheduling_model.multi_session_scheduling ? 'enabled' : 'disabled'} onChange={(value) => setDraft((current) => ({ ...current, scheduling_model: { ...current.scheduling_model, multi_session_scheduling: value === 'enabled' } }))} options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]} className="w-32" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluator Assignment</Text>
                <Select mode="tags" value={draft.scheduling_model.evaluator_assignment} onChange={(value) => setDraft((current) => ({ ...current, scheduling_model: { ...current.scheduling_model, evaluator_assignment: value } }))} placeholder="panel_a, technical_assessors, hr_reviewers" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Candidate Grouping</Text>
                <Input value={draft.scheduling_model.candidate_grouping} onChange={(e) => setDraft((current) => ({ ...current, scheduling_model: { ...current.scheduling_model, candidate_grouping: e.target.value } }))} placeholder="cohort_batch_a" />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'preview' ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Exercise Flow Summary</div>
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Assessment Center'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="space-y-3">
                  {draft.exercises.map((exercise, index) => (
                    <div key={exercise.id} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-slate-900">{index + 1}. {exercise.exercise_name || `Exercise ${index + 1}`}</div>
                        <Tag>{EXERCISE_OPTIONS.find((option) => option.value === exercise.exercise_type)?.label || exercise.exercise_type}</Tag>
                      </div>
                      <div className="mt-2 text-xs text-slate-400">{exercise.exercise_duration} min</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.assessment_center?.usage?.linked_jobs || []).length}</div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Flows</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(currentUsage?.flows || []).length ? currentUsage?.flows.map((flow) => <Tag key={flow}>{flow}</Tag>) : <Text className="text-sm text-slate-500">No linked flows yet</Text>}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : null}

        <div className="flex items-center justify-between">
          <Button onClick={() => setActiveStep(WIZARD_STEPS[Math.max(stepIndex - 1, 0)].key)} disabled={stepIndex === 0}>Back</Button>
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Assessment Center</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Assessment Center Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate Flow</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Assessment Center'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.description || 'Assessment center description pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.exercises.map((exercise, index) => (
              <div key={exercise.id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">{index + 1}. {exercise.exercise_name || `Exercise ${index + 1}`}</div>
                  <Tag>{EXERCISE_OPTIONS.find((option) => option.value === exercise.exercise_type)?.label || exercise.exercise_type}</Tag>
                </div>
                <div className="mt-2 text-xs text-slate-400">{exercise.exercise_duration} min</div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
