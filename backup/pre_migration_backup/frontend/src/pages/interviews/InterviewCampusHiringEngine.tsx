import { useMemo, useState } from 'react'
import {
  Button,
  Card,
  DatePicker,
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
  CalendarDays,
  Copy,
  Eye,
  GraduationCap,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
  Users,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'
import { getCategoryOptions, getInterviewTypeLabel, INTERVIEW_TYPE_CATEGORIES } from '@/utils/interviewTypeUx'

const { Text } = Typography
const { TextArea } = Input

type CampusHiringEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'flow' | 'candidates' | 'evaluation' | 'preview'
type CampusMode = 'onsite' | 'virtual' | 'hybrid'

type CampusStage = {
  id: string
  stage_name: string
  stage_order: number
  stage_type: string
  evaluator_assignment: string[]
}

type CampusHiringDraft = {
  id: string | null
  name: string
  university_campus: string
  role_domain: string
  hiring_batch_size: number
  program_date: string
  mode: CampusMode
  duration_minutes: number
  description: string
  is_active: boolean
  stages: CampusStage[]
  candidate_handling: {
    bulk_candidate_upload: boolean
    college_batch_grouping: string
    queue_management: string
    slot_allocation: string
  }
  evaluation: {
    scorecard_template_id: string
    stage_level_evaluation: boolean
    pass_logic: string
    reject_logic: string
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'flow', label: '2. Hiring Flow', icon: CalendarDays },
  { key: 'candidates', label: '3. Candidate Handling', icon: Users },
  { key: 'evaluation', label: '4. Evaluation', icon: ShieldCheck },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const MODE_OPTIONS = [
  { value: 'onsite', label: 'Onsite' },
  { value: 'virtual', label: 'Virtual' },
  { value: 'hybrid', label: 'Hybrid' },
]

const STAGE_TYPE_OPTIONS = INTERVIEW_TYPE_CATEGORIES.flatMap((category) =>
  getCategoryOptions(category).map((type) => ({
    value: type.value,
    label: `${getInterviewTypeLabel(type.value)} (${category})`,
  })),
)

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createStage(overrides: Partial<CampusStage> = {}): CampusStage {
  return {
    id: makeId('campus-stage'),
    stage_name: '',
    stage_order: 1,
    stage_type: 'aptitude_test',
    evaluator_assignment: [],
    ...overrides,
  }
}

function createDraft(): CampusHiringDraft {
  return {
    id: null,
    name: '',
    university_campus: '',
    role_domain: '',
    hiring_batch_size: 120,
    program_date: dayjs().add(14, 'day').startOf('day').toISOString(),
    mode: 'onsite',
    duration_minutes: 360,
    description: '',
    is_active: true,
    stages: [
      createStage({ stage_name: 'Aptitude Assessment', stage_order: 1, stage_type: 'aptitude_test', evaluator_assignment: ['assessment_team'] }),
      createStage({ stage_name: 'Group Discussion', stage_order: 2, stage_type: 'group_discussion', evaluator_assignment: ['campus_panel'] }),
      createStage({ stage_name: 'Technical Interview', stage_order: 3, stage_type: 'technical_interview', evaluator_assignment: ['engineering_panel'] }),
      createStage({ stage_name: 'HR Interview', stage_order: 4, stage_type: 'hr_interview', evaluator_assignment: ['hr_team'] }),
    ],
    candidate_handling: {
      bulk_candidate_upload: true,
      college_batch_grouping: 'cse_2026_batch',
      queue_management: 'batch_token_queue',
      slot_allocation: 'slot_by_department_and_batch',
    },
    evaluation: {
      scorecard_template_id: '',
      stage_level_evaluation: true,
      pass_logic: 'Candidate advances when mandatory campus stages are cleared with required score thresholds.',
      reject_logic: 'Candidate is rejected when a mandatory stage fails or evaluation rule returns reject.',
    },
  }
}

function parseTemplate(record: any): CampusHiringDraft {
  const meta = record?.metadata?.campus_hiring || {}
  const base = createDraft()
  const stages = Array.isArray(meta.stages) && meta.stages.length
    ? meta.stages.map((stage: any, index: number) => ({
        id: stage.id || makeId('campus-stage'),
        stage_name: stage.stage_name || `Stage ${index + 1}`,
        stage_order: Number(stage.stage_order ?? index + 1),
        stage_type: stage.stage_type || 'aptitude_test',
        evaluator_assignment: Array.isArray(stage.evaluator_assignment) ? stage.evaluator_assignment : [],
      }))
    : base.stages

  return {
    ...base,
    id: record.id,
    name: record.name || '',
    university_campus: meta.setup?.university_campus || '',
    role_domain: meta.setup?.role_domain || '',
    hiring_batch_size: Number(meta.setup?.hiring_batch_size ?? base.hiring_batch_size),
    program_date: meta.setup?.program_date || base.program_date,
    mode: meta.setup?.mode || base.mode,
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    stages,
    candidate_handling: {
      bulk_candidate_upload: meta.candidate_handling?.bulk_candidate_upload ?? true,
      college_batch_grouping: meta.candidate_handling?.college_batch_grouping || base.candidate_handling.college_batch_grouping,
      queue_management: meta.candidate_handling?.queue_management || base.candidate_handling.queue_management,
      slot_allocation: meta.candidate_handling?.slot_allocation || base.candidate_handling.slot_allocation,
    },
    evaluation: {
      scorecard_template_id: meta.evaluation?.scorecard_template_id || '',
      stage_level_evaluation: meta.evaluation?.stage_level_evaluation ?? true,
      pass_logic: meta.evaluation?.pass_logic || base.evaluation.pass_logic,
      reject_logic: meta.evaluation?.reject_logic || base.evaluation.reject_logic,
    },
  }
}

function serializeDraft(draft: CampusHiringDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'campus_hiring',
    duration_minutes: draft.duration_minutes,
    instructions: draft.stages.map((stage) => `${stage.stage_name}: ${stage.stage_type}`).join('\n'),
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      campus_hiring: {
        setup: {
          university_campus: draft.university_campus,
          role_domain: draft.role_domain,
          hiring_batch_size: draft.hiring_batch_size,
          program_date: draft.program_date,
          mode: draft.mode,
        },
        stages: draft.stages,
        candidate_handling: draft.candidate_handling,
        evaluation: draft.evaluation,
        usage: existing.metadata?.campus_hiring?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          scheduling_engine: true,
          scorecard_engine: true,
          flow_engine: true,
          decision_engine: true,
        },
      },
    },
  }
}

export default function InterviewCampusHiringEngine({ embedded = false }: CampusHiringEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<CampusHiringDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const campusTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'campus_hiring' || template.metadata?.campus_hiring)
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

  const selectedTemplateRecord = campusTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Campus Hiring'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Campus hiring program duplicated')
    } catch {
      message.error('Failed to duplicate campus hiring program')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Campus hiring program archived')
    } catch {
      message.error('Failed to archive campus hiring program')
    }
  }

  const handleSave = async () => {
    if (!draft.name.trim()) {
      message.error('Program name is required')
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
      message.success('Campus hiring program saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save campus hiring program')
    } finally {
      setSaving(false)
    }
  }

  const addStage = () => {
    setDraft((current) => ({
      ...current,
      stages: [...current.stages, createStage({ stage_name: `Stage ${current.stages.length + 1}`, stage_order: current.stages.length + 1 })],
    }))
  }

  const updateStage = (id: string, patch: Partial<CampusStage>) => {
    setDraft((current) => ({
      ...current,
      stages: current.stages.map((stage) => (stage.id === id ? { ...stage, ...patch } : stage)),
    }))
  }

  const reorderStage = (id: string, direction: -1 | 1) => {
    setDraft((current) => {
      const index = current.stages.findIndex((stage) => stage.id === id)
      const nextIndex = index + direction
      if (index < 0 || nextIndex < 0 || nextIndex >= current.stages.length) return current
      const stages = [...current.stages]
      ;[stages[index], stages[nextIndex]] = [stages[nextIndex], stages[index]]
      return { ...current, stages: stages.map((stage, idx) => ({ ...stage, stage_order: idx + 1 })) }
    })
  }

  const removeStage = (id: string) => {
    setDraft((current) => ({
      ...current,
      stages: current.stages.filter((stage) => stage.id !== id).map((stage, idx) => ({ ...stage, stage_order: idx + 1 })),
    }))
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Program Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Campus Program'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.university_campus || 'Campus pending'}</Text>
        </div>
      ),
    },
    { title: 'University / Campus', key: 'campus', render: (_, record) => <Text>{record.parsed.university_campus || 'Not set'}</Text> },
    { title: 'Role / Domain', key: 'role', render: (_, record) => <Text>{record.parsed.role_domain || 'Not set'}</Text> },
    { title: 'Date', key: 'date', render: (_, record) => <Text>{dayjs(record.parsed.program_date).format('DD MMM YYYY')}</Text> },
    { title: 'Status', key: 'status', render: (_, record) => <Tag color={record.is_active ? 'success' : 'default'}>{record.is_active ? 'Active' : 'Archived'}</Tag> },
    { title: 'Candidate Count', key: 'candidate_count', render: (_, record) => <Text>{record.parsed.hiring_batch_size}</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Campus Hiring</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable campus hiring programs for university batch intake and graduate recruiting events.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={campusTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No campus hiring programs yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Campus Hiring
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Campus Hiring Builder</h3>
            <p className="text-sm text-slate-500">Configure university program setup, stage flow, batch handling, and evaluation logic.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Campus Program</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Program Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="2026 Graduate Engineering Program" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">University / Campus</Text>
                <Input value={draft.university_campus} onChange={(e) => setDraft((current) => ({ ...current, university_campus: e.target.value }))} placeholder="IIT Bombay" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Graduate Software Engineer" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Hiring Batch Size</Text>
                <InputNumber className="w-full" min={1} max={5000} value={draft.hiring_batch_size} onChange={(value) => setDraft((current) => ({ ...current, hiring_batch_size: Number(value || 0) }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Date</Text>
                <DatePicker className="w-full" value={draft.program_date ? dayjs(draft.program_date) : null} onChange={(value) => setDraft((current) => ({ ...current, program_date: value ? value.toISOString() : '' }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Mode</Text>
                <Select value={draft.mode} onChange={(value) => setDraft((current) => ({ ...current, mode: value }))} options={MODE_OPTIONS} />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Graduate hiring program with aptitude, discussion, technical, and HR evaluation stages." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'flow' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-900">Hiring Flow</h4>
                <p className="text-sm text-slate-500">Define stage order, stage type, and evaluator ownership for the campus program.</p>
              </div>
              <Button onClick={addStage}><Plus size={14} />Add Stage</Button>
            </div>
            <div className="space-y-4">
              {draft.stages.map((stage, index) => (
                <div key={stage.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-black uppercase tracking-wider text-slate-400">Stage {index + 1}</div>
                      <div className="text-sm font-semibold text-slate-900">{stage.stage_name || `Stage ${index + 1}`}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="small" icon={<ArrowUp size={14} />} onClick={() => reorderStage(stage.id, -1)} disabled={index === 0} />
                      <Button size="small" icon={<ArrowDown size={14} />} onClick={() => reorderStage(stage.id, 1)} disabled={index === draft.stages.length - 1} />
                      <Button size="small" danger icon={<Trash2 size={14} />} onClick={() => removeStage(stage.id)} />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Stage Name</Text>
                      <Input value={stage.stage_name} onChange={(e) => updateStage(stage.id, { stage_name: e.target.value })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Stage Type</Text>
                      <Select value={stage.stage_type} onChange={(value) => updateStage(stage.id, { stage_type: value })} options={STAGE_TYPE_OPTIONS} showSearch optionFilterProp="label" />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Stage Order</Text>
                      <InputNumber className="w-full" min={1} value={stage.stage_order} onChange={(value) => updateStage(stage.id, { stage_order: Number(value || 1) })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluator Assignment</Text>
                      <Select mode="tags" value={stage.evaluator_assignment} onChange={(value) => updateStage(stage.id, { evaluator_assignment: value })} placeholder="assessment_team, campus_panel, hr_team" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'candidates' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 md:col-span-2">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Bulk Candidate Upload</div>
                  <div className="text-sm text-slate-500">Allow large campus candidate uploads for batch intake.</div>
                </div>
                <Select
                  value={draft.candidate_handling.bulk_candidate_upload ? 'enabled' : 'disabled'}
                  onChange={(value) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, bulk_candidate_upload: value === 'enabled' } }))}
                  options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]}
                  className="w-32"
                />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">College Batch Grouping</Text>
                <Input value={draft.candidate_handling.college_batch_grouping} onChange={(e) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, college_batch_grouping: e.target.value } }))} placeholder="cse_2026_batch" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Queue Management</Text>
                <Input value={draft.candidate_handling.queue_management} onChange={(e) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, queue_management: e.target.value } }))} placeholder="batch_token_queue" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Slot Allocation</Text>
                <Input value={draft.candidate_handling.slot_allocation} onChange={(e) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, slot_allocation: e.target.value } }))} placeholder="slot_by_department_and_batch" />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.evaluation.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Stage-Level Evaluation</div>
                  <div className="text-sm text-slate-500">Require evaluation completion at each campus stage before progression.</div>
                </div>
                <Select
                  value={draft.evaluation.stage_level_evaluation ? 'enabled' : 'disabled'}
                  onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, stage_level_evaluation: value === 'enabled' } }))}
                  options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]}
                  className="w-32"
                />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Pass Logic</Text>
                <TextArea rows={3} value={draft.evaluation.pass_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_logic: e.target.value } }))} placeholder="Advance candidate when required campus stages clear thresholds." />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Reject Logic</Text>
                <TextArea rows={3} value={draft.evaluation.reject_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_logic: e.target.value } }))} placeholder="Reject candidate on mandatory stage failure or rule-based elimination." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'preview' ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Program Flow Summary</div>
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Campus Program'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="space-y-3">
                  {draft.stages.map((stage, index) => (
                    <div key={stage.id} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-slate-900">{index + 1}. {stage.stage_name || `Stage ${index + 1}`}</div>
                        <Tag>{getInterviewTypeLabel(stage.stage_type)}</Tag>
                      </div>
                      <div className="mt-2 text-xs text-slate-400">{stage.evaluator_assignment.length ? stage.evaluator_assignment.join(', ') : 'Evaluator assignment pending'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Program Overview</div>
                  <div className="mt-2 text-sm text-slate-600">{draft.university_campus || 'Campus pending'}</div>
                  <div className="mt-1 text-sm text-slate-500">{dayjs(draft.program_date).format('DD MMM YYYY')} • {MODE_OPTIONS.find((option) => option.value === draft.mode)?.label}</div>
                  <div className="mt-1 text-sm text-slate-500">Batch Size: {draft.hiring_batch_size}</div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.campus_hiring?.usage?.linked_jobs || []).length}</div>
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
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Campus Program</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Campus Hiring Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Campus Program</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Campus Program'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.description || 'Campus hiring description pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.stages.map((stage, index) => (
              <div key={stage.id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">{index + 1}. {stage.stage_name || `Stage ${index + 1}`}</div>
                  <Tag>{getInterviewTypeLabel(stage.stage_type)}</Tag>
                </div>
                <div className="mt-2 text-xs text-slate-400">{stage.evaluator_assignment.length ? stage.evaluator_assignment.join(', ') : 'Evaluator assignment pending'}</div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
