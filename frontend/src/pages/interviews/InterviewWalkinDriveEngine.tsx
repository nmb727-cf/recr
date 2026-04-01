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
  DoorOpen,
  Eye,
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

type WalkinDriveEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'flow' | 'candidates' | 'evaluation' | 'preview'
type WalkinMode = 'onsite' | 'virtual' | 'hybrid'

type WalkinStage = {
  id: string
  stage_name: string
  stage_order: number
  stage_type: string
  evaluator_assignment: string[]
}

type WalkinDriveDraft = {
  id: string | null
  name: string
  role_domain: string
  drive_date: string
  mode: WalkinMode
  location: string
  duration_minutes: number
  description: string
  is_active: boolean
  stages: WalkinStage[]
  candidate_handling: {
    bulk_candidate_entry: boolean
    queue_management: string
    batch_handling: string
    capacity_per_slot: number
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
  { key: 'flow', label: '2. Interview Flow', icon: CalendarDays },
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

function createStage(overrides: Partial<WalkinStage> = {}): WalkinStage {
  return {
    id: makeId('walkin-stage'),
    stage_name: '',
    stage_order: 1,
    stage_type: 'recruiter_screening',
    evaluator_assignment: [],
    ...overrides,
  }
}

function createDraft(): WalkinDriveDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    drive_date: dayjs().add(7, 'day').startOf('day').toISOString(),
    mode: 'onsite',
    location: '',
    duration_minutes: 240,
    description: '',
    is_active: true,
    stages: [
      createStage({ stage_name: 'Registration Desk', stage_order: 1, stage_type: 'recruiter_screening', evaluator_assignment: ['talent_ops'] }),
      createStage({ stage_name: 'Technical Panel', stage_order: 2, stage_type: 'technical_interview', evaluator_assignment: ['engineering_panel'] }),
      createStage({ stage_name: 'HR Closure', stage_order: 3, stage_type: 'hr_interview', evaluator_assignment: ['hr_team'] }),
    ],
    candidate_handling: {
      bulk_candidate_entry: true,
      queue_management: 'token_queue_with_priority_lane',
      batch_handling: 'batch_of_20_per_hour',
      capacity_per_slot: 20,
    },
    evaluation: {
      scorecard_template_id: '',
      stage_level_evaluation: true,
      pass_logic: 'Candidate clears drive when all mandatory stages are passed.',
      reject_logic: 'Candidate is rejected when a mandatory stage returns reject or knockout.',
    },
  }
}

function parseTemplate(record: any): WalkinDriveDraft {
  const meta = record?.metadata?.walkin_drive || {}
  const base = createDraft()
  const stages = Array.isArray(meta.stages) && meta.stages.length
    ? meta.stages.map((stage: any, index: number) => ({
        id: stage.id || makeId('walkin-stage'),
        stage_name: stage.stage_name || `Stage ${index + 1}`,
        stage_order: Number(stage.stage_order ?? index + 1),
        stage_type: stage.stage_type || 'recruiter_screening',
        evaluator_assignment: Array.isArray(stage.evaluator_assignment) ? stage.evaluator_assignment : [],
      }))
    : base.stages

  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    drive_date: meta.setup?.drive_date || base.drive_date,
    mode: meta.setup?.mode || base.mode,
    location: meta.setup?.location || '',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    stages,
    candidate_handling: {
      bulk_candidate_entry: meta.candidate_handling?.bulk_candidate_entry ?? true,
      queue_management: meta.candidate_handling?.queue_management || base.candidate_handling.queue_management,
      batch_handling: meta.candidate_handling?.batch_handling || base.candidate_handling.batch_handling,
      capacity_per_slot: Number(meta.candidate_handling?.capacity_per_slot ?? base.candidate_handling.capacity_per_slot),
    },
    evaluation: {
      scorecard_template_id: meta.evaluation?.scorecard_template_id || '',
      stage_level_evaluation: meta.evaluation?.stage_level_evaluation ?? true,
      pass_logic: meta.evaluation?.pass_logic || base.evaluation.pass_logic,
      reject_logic: meta.evaluation?.reject_logic || base.evaluation.reject_logic,
    },
  }
}

function serializeDraft(draft: WalkinDriveDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'walkin_drive',
    duration_minutes: draft.duration_minutes,
    instructions: draft.stages.map((stage) => `${stage.stage_name}: ${stage.stage_type}`).join('\n'),
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      walkin_drive: {
        setup: {
          role_domain: draft.role_domain,
          drive_date: draft.drive_date,
          mode: draft.mode,
          location: draft.location,
        },
        stages: draft.stages,
        candidate_handling: draft.candidate_handling,
        evaluation: draft.evaluation,
        usage: existing.metadata?.walkin_drive?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
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

export default function InterviewWalkinDriveEngine({ embedded = false }: WalkinDriveEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<WalkinDriveDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const walkinTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'walkin_drive' || template.metadata?.walkin_drive)
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

  const selectedTemplateRecord = walkinTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Walk-in Drive'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Walk-in drive duplicated')
    } catch {
      message.error('Failed to duplicate walk-in drive')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Walk-in drive archived')
    } catch {
      message.error('Failed to archive walk-in drive')
    }
  }

  const handleSave = async () => {
    if (!draft.name.trim()) {
      message.error('Drive name is required')
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
      message.success('Walk-in drive saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save walk-in drive')
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

  const updateStage = (id: string, patch: Partial<WalkinStage>) => {
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
      title: 'Drive Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Walk-in Drive'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Role / Domain', key: 'role', render: (_, record) => <Text>{record.parsed.role_domain || 'Not set'}</Text> },
    {
      title: 'Date',
      key: 'date',
      render: (_, record) => <Text>{dayjs(record.parsed.drive_date).format('DD MMM YYYY')}</Text>,
    },
    {
      title: 'Location / Mode',
      key: 'location_mode',
      render: (_, record) => (
        <div className="flex min-w-0 flex-col">
          <Text>{MODE_OPTIONS.find((option) => option.value === record.parsed.mode)?.label || 'Mode pending'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.location || 'Location pending'}</Text>
        </div>
      ),
    },
    { title: 'Status', key: 'status', render: (_, record) => <Tag color={record.is_active ? 'success' : 'default'}>{record.is_active ? 'Active' : 'Archived'}</Tag> },
    {
      title: 'Candidate Count',
      key: 'candidate_count',
      render: (_, record) => <Text>{record.metadata?.walkin_drive?.candidate_handling?.capacity_per_slot || record.parsed.candidate_handling.capacity_per_slot}</Text>,
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Walk-in Drive</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable high-volume walk-in drive events with staged evaluation, queueing, and routing.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={walkinTemplates}
            loading={isLoading}
            pagination={false}
            locale={{ emptyText: <Empty description="No walk-in drives yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Walk-in Drives
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Walk-in Drive Builder</h3>
            <p className="text-sm text-slate-500">Configure high-volume event setup, stage flow, candidate queueing, and evaluation rules.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Walk-in Drive</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Drive Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="April Engineering Walk-in Drive" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Software Engineering" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Date</Text>
                <DatePicker className="w-full" value={draft.drive_date ? dayjs(draft.drive_date) : null} onChange={(value) => setDraft((current) => ({ ...current, drive_date: value ? value.toISOString() : '' }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Mode</Text>
                <Select value={draft.mode} onChange={(value) => setDraft((current) => ({ ...current, mode: value }))} options={MODE_OPTIONS} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Location</Text>
                <Input value={draft.location} onChange={(e) => setDraft((current) => ({ ...current, location: e.target.value }))} placeholder={draft.mode === 'onsite' ? 'Bengaluru Hiring Hub' : 'Meeting link / venue note'} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration Summary</Text>
                <InputNumber className="w-full" min={60} max={960} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="High-volume hiring event with screening, technical, and HR closure stages." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'flow' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-900">Interview Flow</h4>
                <p className="text-sm text-slate-500">Define stage order, stage type, and evaluator ownership for the event.</p>
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
                      <Select mode="tags" value={stage.evaluator_assignment} onChange={(value) => updateStage(stage.id, { evaluator_assignment: value })} placeholder="talent_ops, panel_a, hr_team" />
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
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Bulk Candidate Entry</div>
                  <div className="text-sm text-slate-500">Allow importing and registering large candidate batches.</div>
                </div>
                <Select
                  value={draft.candidate_handling.bulk_candidate_entry ? 'enabled' : 'disabled'}
                  onChange={(value) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, bulk_candidate_entry: value === 'enabled' } }))}
                  options={[{ value: 'enabled', label: 'Enabled' }, { value: 'disabled', label: 'Disabled' }]}
                  className="w-32"
                />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Queue Management</Text>
                <Input value={draft.candidate_handling.queue_management} onChange={(e) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, queue_management: e.target.value } }))} placeholder="token_queue_with_priority_lane" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Batch Handling</Text>
                <Input value={draft.candidate_handling.batch_handling} onChange={(e) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, batch_handling: e.target.value } }))} placeholder="batch_of_20_per_hour" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Capacity Per Slot</Text>
                <InputNumber className="w-full" min={1} max={500} value={draft.candidate_handling.capacity_per_slot} onChange={(value) => setDraft((current) => ({ ...current, candidate_handling: { ...current.candidate_handling, capacity_per_slot: Number(value || 0) } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select
                  value={draft.evaluation.scorecard_template_id || undefined}
                  onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value } }))}
                  options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))}
                  allowClear
                />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Stage Level Evaluation</div>
                  <div className="text-sm text-slate-500">Require scoring at each stage before candidate moves ahead.</div>
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
                <TextArea rows={3} value={draft.evaluation.pass_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_logic: e.target.value } }))} placeholder="Candidate clears drive when all mandatory stages are passed." />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Reject Logic</Text>
                <TextArea rows={3} value={draft.evaluation.reject_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_logic: e.target.value } }))} placeholder="Reject when a knockout or mandatory stage fails." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'preview' ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Stage Flow Summary</div>
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Walk-in Drive'}</h4>
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
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Drive Overview</div>
                  <div className="mt-2 text-sm text-slate-600">{dayjs(draft.drive_date).format('DD MMM YYYY')} • {MODE_OPTIONS.find((option) => option.value === draft.mode)?.label}</div>
                  <div className="mt-1 text-sm text-slate-500">{draft.location || 'Location pending'}</div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.walkin_drive?.usage?.linked_jobs || []).length}</div>
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
          {stepIndex === WIZARD_STEPS.length - 1 ? (
            <Button type="primary" loading={saving} onClick={handleSave}>Save Walk-in Drive</Button>
          ) : (
            <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>
          )}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Walk-in Drive Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Drive Overview</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Walk-in Drive'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.description || 'Drive description pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.stages.map((stage, index) => (
              <div key={stage.id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">{index + 1}. {stage.stage_name || `Stage ${index + 1}`}</div>
                  <Tag>{getInterviewTypeLabel(stage.stage_type)}</Tag>
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  {stage.evaluator_assignment.length ? stage.evaluator_assignment.join(', ') : 'Evaluator assignment pending'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
