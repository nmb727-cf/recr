import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
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
  Layers3,
  Pencil,
  Plus,
  Settings2,
  ShieldCheck,
  StickyNote,
  Trash2,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type WhiteboardEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'structure' | 'guidance' | 'evaluation' | 'preview'

type WhiteboardStructureItem = {
  id: string
  title: string
  item_type: 'topic' | 'problem_statement' | 'architecture_prompt' | 'system_design_prompt'
  prompt: string
  mandatory: boolean
}

type WhiteboardDraft = {
  id: string | null
  name: string
  role_domain: string
  difficulty_level: 'junior' | 'mid' | 'senior' | 'lead'
  duration_minutes: number
  description: string
  is_active: boolean
  structure: {
    items: WhiteboardStructureItem[]
  }
  guidance: {
    interviewer_notes: string
    evaluation_focus: string[]
    expected_discussion_areas: string[]
  }
  evaluation: {
    scorecard_template_id: string
    scoring_dimensions: string[]
    pass_threshold: number
    reject_threshold: number
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'structure', label: '2. Interview Structure', icon: Layers3 },
  { key: 'guidance', label: '3. Interview Guidance', icon: StickyNote },
  { key: 'evaluation', label: '4. Evaluation', icon: ShieldCheck },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const DIFFICULTY_OPTIONS = [
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
]

const STRUCTURE_ITEM_OPTIONS = [
  { value: 'topic', label: 'Topic to Assess' },
  { value: 'problem_statement', label: 'Problem Statement' },
  { value: 'architecture_prompt', label: 'Architecture Prompt' },
  { value: 'system_design_prompt', label: 'System Design Prompt' },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createStructureItem(
  itemType: WhiteboardStructureItem['item_type'] = 'topic',
  overrides: Partial<WhiteboardStructureItem> = {},
): WhiteboardStructureItem {
  return {
    id: makeId('whiteboard-item'),
    title: '',
    item_type: itemType,
    prompt: '',
    mandatory: true,
    ...overrides,
  }
}

function createDraft(): WhiteboardDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    difficulty_level: 'mid',
    duration_minutes: 60,
    description: '',
    is_active: true,
    structure: {
      items: [
        createStructureItem('topic', { title: 'Core topic', prompt: 'Distributed systems and tradeoffs' }),
        createStructureItem('problem_statement', { title: 'Problem statement', prompt: 'Design a collaborative whiteboard service for remote interviews.' }),
      ],
    },
    guidance: {
      interviewer_notes: '',
      evaluation_focus: ['Problem solving', 'Communication', 'Architecture decisions'],
      expected_discussion_areas: ['Scalability', 'Tradeoffs', 'Data model'],
    },
    evaluation: {
      scorecard_template_id: '',
      scoring_dimensions: ['problem_solving', 'technical_depth', 'communication', 'architecture_reasoning'],
      pass_threshold: 78,
      reject_threshold: 48,
    },
  }
}

function parseTemplate(record: any): WhiteboardDraft {
  const meta = record?.metadata?.whiteboard_interview || {}
  const base = createDraft()
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    difficulty_level: meta.setup?.difficulty_level || 'mid',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    structure: {
      items: Array.isArray(meta.structure?.items) && meta.structure.items.length
        ? meta.structure.items.map((item: any) => ({
            id: item.id || makeId('whiteboard-item'),
            title: item.title || '',
            item_type: item.item_type || 'topic',
            prompt: item.prompt || '',
            mandatory: item.mandatory ?? true,
          }))
        : base.structure.items,
    },
    guidance: {
      interviewer_notes: meta.guidance?.interviewer_notes || '',
      evaluation_focus: Array.isArray(meta.guidance?.evaluation_focus) ? meta.guidance.evaluation_focus : base.guidance.evaluation_focus,
      expected_discussion_areas: Array.isArray(meta.guidance?.expected_discussion_areas)
        ? meta.guidance.expected_discussion_areas
        : base.guidance.expected_discussion_areas,
    },
    evaluation: {
      scorecard_template_id: meta.evaluation?.scorecard_template_id || '',
      scoring_dimensions: Array.isArray(meta.evaluation?.scoring_dimensions)
        ? meta.evaluation.scoring_dimensions
        : base.evaluation.scoring_dimensions,
      pass_threshold: Number(meta.evaluation?.pass_threshold ?? base.evaluation.pass_threshold),
      reject_threshold: Number(meta.evaluation?.reject_threshold ?? base.evaluation.reject_threshold),
    },
  }
}

function serializeDraft(draft: WhiteboardDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'whiteboard_interview',
    duration_minutes: draft.duration_minutes,
    instructions: draft.guidance.interviewer_notes,
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      whiteboard_interview: {
        setup: {
          role_domain: draft.role_domain,
          difficulty_level: draft.difficulty_level,
        },
        structure: draft.structure,
        guidance: draft.guidance,
        evaluation: draft.evaluation,
        usage: existing.metadata?.whiteboard_interview?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          technical_engine: true,
          scorecard_engine: true,
          flow_engine: true,
          scheduling_engine: true,
        },
      },
    },
  }
}

function getCompletionState(draft: WhiteboardDraft) {
  return {
    setup: Boolean(draft.name.trim() && draft.role_domain.trim()),
    structure: draft.structure.items.some((item) => item.title.trim() && item.prompt.trim()),
    guidance: Boolean(draft.guidance.interviewer_notes.trim() || draft.guidance.evaluation_focus.length),
    evaluation: draft.evaluation.pass_threshold > draft.evaluation.reject_threshold,
    preview: true,
  } satisfies Record<WizardStep, boolean>
}

export default function InterviewWhiteboardEngine({ embedded = false }: WhiteboardEngineProps) {
  const location = useLocation()
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<WhiteboardDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const whiteboardTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'whiteboard_interview' || template.metadata?.whiteboard_interview)
        .map((template: any) => ({
          ...template,
          parsed: parseTemplate(template),
        })),
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

  const selectedTemplateRecord = whiteboardTemplates.find((template: any) => template.id === selectedTemplateId) || null
  const completion = getCompletionState(draft)
  const currentUsage = selectedTemplateId ? usageByTemplateId.get(selectedTemplateId) : null
  const stepIndex = WIZARD_STEPS.findIndex((step) => step.key === activeStep)

  useEffect(() => {
    const requestedType = new URLSearchParams(location.search).get('type')
    if (requestedType === 'whiteboard_interview') {
      setDraft((current) => current)
    }
  }, [location.search])

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
        serializeDraft(
          { ...parseTemplate(record), id: null, name: `${record.name || 'Whiteboard Interview'} Copy` },
          {},
        ),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Whiteboard interview duplicated')
    } catch {
      message.error('Failed to duplicate whiteboard interview')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Whiteboard interview archived')
    } catch {
      message.error('Failed to archive whiteboard interview')
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
      message.success('Whiteboard interview saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save whiteboard interview')
    } finally {
      setSaving(false)
    }
  }

  const addStructureItem = (itemType: WhiteboardStructureItem['item_type']) => {
    setDraft((current) => ({
      ...current,
      structure: {
        items: [...current.structure.items, createStructureItem(itemType)],
      },
    }))
  }

  const updateStructureItem = (id: string, patch: Partial<WhiteboardStructureItem>) => {
    setDraft((current) => ({
      ...current,
      structure: {
        items: current.structure.items.map((item) => (item.id === id ? { ...item, ...patch } : item)),
      },
    }))
  }

  const moveStructureItem = (id: string, direction: -1 | 1) => {
    setDraft((current) => {
      const index = current.structure.items.findIndex((item) => item.id === id)
      const nextIndex = index + direction
      if (index < 0 || nextIndex < 0 || nextIndex >= current.structure.items.length) return current
      const items = [...current.structure.items]
      ;[items[index], items[nextIndex]] = [items[nextIndex], items[index]]
      return { ...current, structure: { items } }
    })
  }

  const removeStructureItem = (id: string) => {
    setDraft((current) => ({
      ...current,
      structure: {
        items: current.structure.items.filter((item) => item.id !== id),
      },
    }))
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Whiteboard Interview'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    {
      title: 'Type',
      key: 'type',
      render: () => <Tag color="orange">Whiteboard</Tag>,
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record) => <Text>{record.duration_minutes || 60} min</Text>,
    },
    {
      title: 'Scorecard',
      key: 'scorecard',
      render: (_, record) => {
        const scorecard = scorecards.find((item: any) => item.id === record.parsed.evaluation.scorecard_template_id)
        return <Text className="text-xs text-slate-600">{scorecard?.name || 'Not attached'}</Text>
      },
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => <Tag color={record.is_active ? 'success' : 'default'}>{record.is_active ? 'Active' : 'Archived'}</Tag>,
    },
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
          <Button size="small" onClick={() => {
            openEdit(record)
            setPreviewOpen(true)
            setActiveStep('preview')
          }}>
            Preview
          </Button>
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Whiteboard Interview</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable whiteboard interview templates for technical and system design rounds.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>
            Create
          </Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={whiteboardTemplates}
            loading={isLoading}
            pagination={false}
            locale={{ emptyText: <Empty description="No whiteboard interviews yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button
          type="button"
          onClick={() => setIsBuilderOpen(false)}
          className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600"
        >
          <ArrowLeft size={16} />
          Back to Whiteboard Interviews
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
                  activeStep === step.key
                    ? 'border-orange-200 bg-orange-50 text-orange-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                )}
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white">
                  <Icon size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-black uppercase tracking-wider">{step.label}</div>
                  <div className="text-[11px] text-slate-400">{completion[step.key] ? 'Configured' : 'Pending'}</div>
                </div>
              </button>
            )
          })}
        </div>
      </Card>

      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Whiteboard Interview Builder</h3>
            <p className="text-sm text-slate-500">Configure reusable whiteboard interviews for architecture and system design rounds.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Whiteboard Interview</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Name</Text>
                <Input value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} placeholder="Senior Platform Whiteboard" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(event) => setDraft((current) => ({ ...current, role_domain: event.target.value }))} placeholder="Platform Engineering" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Difficulty Level</Text>
                <Select value={draft.difficulty_level} onChange={(value) => setDraft((current) => ({ ...current, difficulty_level: value }))} options={DIFFICULTY_OPTIONS} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={15} max={180} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} placeholder="Use this for high-signal collaborative problem solving and system design discussions." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'structure' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-900">Interview Structure</h4>
                <p className="text-sm text-slate-500">Add the topics, prompts, and whiteboard problem statements in execution order.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {STRUCTURE_ITEM_OPTIONS.map((option) => (
                  <Button key={option.value} onClick={() => addStructureItem(option.value as WhiteboardStructureItem['item_type'])}>
                    <Plus size={14} />
                    {option.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {draft.structure.items.map((item, index) => (
                <div key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-black uppercase tracking-wider text-slate-400">Item {index + 1}</div>
                      <div className="text-sm font-semibold text-slate-900">{item.title || 'Untitled whiteboard item'}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="small" icon={<ArrowUp size={14} />} onClick={() => moveStructureItem(item.id, -1)} disabled={index === 0} />
                      <Button size="small" icon={<ArrowDown size={14} />} onClick={() => moveStructureItem(item.id, 1)} disabled={index === draft.structure.items.length - 1} />
                      <Button size="small" danger icon={<Trash2 size={14} />} onClick={() => removeStructureItem(item.id)} />
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Title</Text>
                      <Input value={item.title} onChange={(event) => updateStructureItem(item.id, { title: event.target.value })} placeholder="Architecture prompt" />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Item Type</Text>
                      <Select value={item.item_type} onChange={(value) => updateStructureItem(item.id, { item_type: value })} options={STRUCTURE_ITEM_OPTIONS} />
                    </div>
                    <div className="md:col-span-2">
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Prompt</Text>
                      <TextArea rows={4} value={item.prompt} onChange={(event) => updateStructureItem(item.id, { prompt: event.target.value })} placeholder="Ask the candidate to design a collaborative whiteboard platform with realtime synchronization and conflict handling." />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'guidance' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interviewer Notes</Text>
                <TextArea rows={5} value={draft.guidance.interviewer_notes} onChange={(event) => setDraft((current) => ({ ...current, guidance: { ...current.guidance, interviewer_notes: event.target.value } }))} placeholder="Probe tradeoffs, ask for assumptions, and push on failure handling and scaling decisions." />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluation Focus</Text>
                <Select mode="tags" value={draft.guidance.evaluation_focus} onChange={(value) => setDraft((current) => ({ ...current, guidance: { ...current.guidance, evaluation_focus: value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Expected Discussion Areas</Text>
                <Select mode="tags" value={draft.guidance.expected_discussion_areas} onChange={(value) => setDraft((current) => ({ ...current, guidance: { ...current.guidance, expected_discussion_areas: value } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Template</Text>
                <Select
                  value={draft.evaluation.scorecard_template_id || undefined}
                  onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value } }))}
                  options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))}
                  allowClear
                  placeholder="Attach scorecard template"
                />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scoring Dimensions</Text>
                <Select mode="tags" value={draft.evaluation.scoring_dimensions} onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scoring_dimensions: value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Pass Threshold</Text>
                <InputNumber className="w-full" min={0} max={100} value={draft.evaluation.pass_threshold} onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_threshold: Number(value || 0) } }))} addonAfter="%" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Reject Threshold</Text>
                <InputNumber className="w-full" min={0} max={100} value={draft.evaluation.reject_threshold} onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_threshold: Number(value || 0) } }))} addonAfter="%" />
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
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Whiteboard Interview'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Role / Domain</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.role_domain || 'Pending'}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Difficulty</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.difficulty_level}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Duration</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.duration_minutes} min</div>
                  </div>
                </div>
                <div>
                  <div className="mb-3 text-xs font-black uppercase tracking-wider text-slate-400">Interview Structure</div>
                  <div className="space-y-3">
                    {draft.structure.items.map((item, index) => (
                      <div key={item.id} className="rounded-xl border border-slate-200 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-slate-900">{index + 1}. {item.title || 'Untitled item'}</div>
                          <Tag>{STRUCTURE_ITEM_OPTIONS.find((option) => option.value === item.item_type)?.label || item.item_type}</Tag>
                        </div>
                        <p className="mt-2 text-sm text-slate-500">{item.prompt || 'Prompt pending'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.whiteboard_interview?.usage?.linked_jobs || []).length}</div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Flows</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(currentUsage?.flows || []).length ? currentUsage?.flows.map((flow) => <Tag key={flow}>{flow}</Tag>) : <Text className="text-sm text-slate-500">No linked flows yet</Text>}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Evaluation</div>
                  <div className="mt-2 text-sm text-slate-600">Pass: {draft.evaluation.pass_threshold}%</div>
                  <div className="text-sm text-slate-600">Reject: {draft.evaluation.reject_threshold}%</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {draft.evaluation.scoring_dimensions.map((dimension) => <Tag key={dimension}>{dimension}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : null}

        <div className="flex items-center justify-between">
          <Button onClick={() => setActiveStep(WIZARD_STEPS[Math.max(stepIndex - 1, 0)].key)} disabled={stepIndex === 0}>Back</Button>
          {stepIndex === WIZARD_STEPS.length - 1 ? (
            <Button type="primary" loading={saving} onClick={handleSave}>Save Whiteboard Interview</Button>
          ) : (
            <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>
          )}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Whiteboard Interview Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate View</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Whiteboard Interview'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.description || 'Interview description pending.'}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="rounded-2xl border-slate-200">
              <div className="text-xs font-black uppercase tracking-wider text-slate-400">Question Sequence</div>
              <div className="mt-3 space-y-3">
                {draft.structure.items.map((item, index) => (
                  <div key={item.id} className="rounded-xl border border-slate-200 p-3">
                    <div className="text-sm font-semibold text-slate-900">{index + 1}. {item.title || 'Untitled item'}</div>
                    <div className="mt-1 text-xs text-slate-500">{item.prompt || 'Prompt pending'}</div>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="text-xs font-black uppercase tracking-wider text-slate-400">Interview Guidance</div>
              <div className="mt-3 space-y-3 text-sm text-slate-600">
                <div>Focus: {draft.guidance.evaluation_focus.join(', ') || 'Pending'}</div>
                <div>Expected discussion: {draft.guidance.expected_discussion_areas.join(', ') || 'Pending'}</div>
                <div>Duration: {draft.duration_minutes} minutes</div>
              </div>
            </Card>
          </div>
        </div>
      </Modal>
    </div>
  )
}
