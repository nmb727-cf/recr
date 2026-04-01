import { useMemo, useState } from 'react'
import {
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Modal,
  Select,
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
  Copy,
  Eye,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
  Workflow,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type SequentialRoundEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'round-structure' | 'round-config' | 'progression' | 'preview'
type RoundType = 'screening' | 'technical' | 'human' | 'hiring_manager' | 'final' | 'panel'
type RoundRule = 'pass' | 'reject' | 'manual_review'

type SequentialRoundItem = {
  id: string
  round_name: string
  round_order: number
  round_duration: number
  round_type: RoundType
  round_objective: string
  question_topic_flow: string[]
  interviewer_guidance: string
  scorecard_template_id: string
  mandatory: boolean
  round_rule: RoundRule
}

type SequentialDraft = {
  id: string | null
  name: string
  role_domain: string
  description: string
  total_rounds: number
  duration_summary: string
  is_active: boolean
  rounds: SequentialRoundItem[]
  progression: {
    move_to_next_round: boolean
    reject_after_round: boolean
    manual_review_between_rounds: boolean
    skip_round_shell_enabled: boolean
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'round-structure', label: '2. Round Structure', icon: Layers3 },
  { key: 'round-config', label: '3. Per Round Configuration', icon: ShieldCheck },
  { key: 'progression', label: '4. Progression Logic', icon: Workflow },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const ROUND_TYPE_OPTIONS = [
  { value: 'screening', label: 'Screening' },
  { value: 'technical', label: 'Technical' },
  { value: 'human', label: 'Human Interview' },
  { value: 'hiring_manager', label: 'Hiring Manager' },
  { value: 'final', label: 'Final Round' },
  { value: 'panel', label: 'Panel' },
]

const ROUND_RULE_OPTIONS = [
  { value: 'pass', label: 'Pass' },
  { value: 'manual_review', label: 'Manual Review' },
  { value: 'reject', label: 'Reject' },
]

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createRound(overrides: Partial<SequentialRoundItem> = {}): SequentialRoundItem {
  return {
    id: makeId('seq-round'),
    round_name: '',
    round_order: 1,
    round_duration: 30,
    round_type: 'screening',
    round_objective: '',
    question_topic_flow: [],
    interviewer_guidance: '',
    scorecard_template_id: '',
    mandatory: true,
    round_rule: 'pass',
    ...overrides,
  }
}

function createDraft(): SequentialDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    description: '',
    total_rounds: 4,
    duration_summary: '30m Screening + 60m Technical + 45m Hiring Manager + 30m Final',
    is_active: true,
    rounds: [
      createRound({ round_name: 'Round 1 Screening', round_order: 1, round_type: 'screening', round_objective: 'Verify baseline fit and availability' }),
      createRound({ round_name: 'Round 2 Technical', round_order: 2, round_type: 'technical', round_duration: 60, round_objective: 'Assess practical technical depth' }),
      createRound({ round_name: 'Round 3 Hiring Manager', round_order: 3, round_type: 'hiring_manager', round_duration: 45, round_objective: 'Evaluate role alignment and execution' }),
      createRound({ round_name: 'Round 4 Final', round_order: 4, round_type: 'final', round_objective: 'Final decision and risk review' }),
    ],
    progression: {
      move_to_next_round: true,
      reject_after_round: true,
      manual_review_between_rounds: true,
      skip_round_shell_enabled: false,
    },
  }
}

function parseTemplate(record: any): SequentialDraft {
  const meta = record?.metadata?.sequential_round || {}
  const base = createDraft()
  const rounds = Array.isArray(meta.rounds) && meta.rounds.length
    ? meta.rounds.map((round: any, index: number) => ({
        id: round.id || makeId('seq-round'),
        round_name: round.round_name || `Round ${index + 1}`,
        round_order: Number(round.round_order ?? index + 1),
        round_duration: Number(round.round_duration ?? 30),
        round_type: round.round_type || 'screening',
        round_objective: round.round_objective || '',
        question_topic_flow: Array.isArray(round.question_topic_flow) ? round.question_topic_flow : [],
        interviewer_guidance: round.interviewer_guidance || '',
        scorecard_template_id: round.scorecard_template_id || '',
        mandatory: round.mandatory ?? true,
        round_rule: round.round_rule || 'pass',
      }))
    : base.rounds

  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    description: record.description || '',
    total_rounds: Number(meta.setup?.total_rounds ?? rounds.length),
    duration_summary: meta.setup?.duration_summary || base.duration_summary,
    is_active: record.is_active ?? true,
    rounds,
    progression: {
      move_to_next_round: meta.progression?.move_to_next_round ?? true,
      reject_after_round: meta.progression?.reject_after_round ?? true,
      manual_review_between_rounds: meta.progression?.manual_review_between_rounds ?? true,
      skip_round_shell_enabled: meta.progression?.skip_round_shell_enabled ?? false,
    },
  }
}

function serializeDraft(draft: SequentialDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'sequential_round',
    duration_minutes: draft.rounds.reduce((sum, round) => sum + Number(round.round_duration || 0), 0),
    instructions: draft.rounds.map((round) => `${round.round_name}: ${round.round_objective}`).join('\n'),
    scoring_type: draft.rounds.some((round) => round.scorecard_template_id) ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      sequential_round: {
        setup: {
          role_domain: draft.role_domain,
          total_rounds: draft.total_rounds,
          duration_summary: draft.duration_summary,
        },
        rounds: draft.rounds,
        progression: draft.progression,
        usage: existing.metadata?.sequential_round?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          human_engine: true,
          technical_engine: true,
          scorecard_engine: true,
          flow_engine: true,
          scheduling_engine: true,
          decision_engine: true,
        },
      },
    },
  }
}

export default function InterviewSequentialRoundEngine({ embedded = false }: SequentialRoundEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<SequentialDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const sequentialTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'sequential_round' || template.metadata?.sequential_round)
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

  const selectedTemplateRecord = sequentialTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Sequential Round'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Sequential round interview duplicated')
    } catch {
      message.error('Failed to duplicate sequential round interview')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Sequential round interview archived')
    } catch {
      message.error('Failed to archive sequential round interview')
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
      message.success('Sequential round interview saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save sequential round interview')
    } finally {
      setSaving(false)
    }
  }

  const addRound = () => {
    setDraft((current) => {
      const nextOrder = current.rounds.length + 1
      const rounds = [...current.rounds, createRound({ round_name: `Round ${nextOrder}`, round_order: nextOrder })]
      return { ...current, total_rounds: rounds.length, rounds }
    })
  }

  const updateRound = (id: string, patch: Partial<SequentialRoundItem>) => {
    setDraft((current) => ({
      ...current,
      rounds: current.rounds.map((round) => (round.id === id ? { ...round, ...patch } : round)),
    }))
  }

  const reorderRounds = (id: string, direction: -1 | 1) => {
    setDraft((current) => {
      const index = current.rounds.findIndex((round) => round.id === id)
      const nextIndex = index + direction
      if (index < 0 || nextIndex < 0 || nextIndex >= current.rounds.length) return current
      const rounds = [...current.rounds]
      ;[rounds[index], rounds[nextIndex]] = [rounds[nextIndex], rounds[index]]
      return { ...current, rounds: rounds.map((round, idx) => ({ ...round, round_order: idx + 1 })) }
    })
  }

  const removeRound = (id: string) => {
    setDraft((current) => {
      const rounds = current.rounds.filter((round) => round.id !== id).map((round, idx) => ({ ...round, round_order: idx + 1 }))
      return { ...current, total_rounds: rounds.length, rounds }
    })
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Sequential Round'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="blue">Sequential Round</Tag> },
    { title: 'Total Rounds', key: 'rounds', render: (_, record) => <Text>{record.parsed.rounds.length}</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Sequential Round</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable multi-round interview processes with per-round configuration and progression logic.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={sequentialTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No sequential round interviews yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Sequential Rounds
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button key={step.key} type="button" onClick={() => setActiveStep(step.key)} className={cn('flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition', activeStep === step.key ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300')}>
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Sequential Round Builder</h3>
            <p className="text-sm text-slate-500">Configure round order, objectives, scorecards, and progression rules.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Sequential Round</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Engineering Sequential Process" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Platform Engineering" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Structured multi-round interview process." />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Total Rounds</Text>
                <InputNumber className="w-full" min={1} max={10} value={draft.total_rounds} onChange={(value) => setDraft((current) => ({ ...current, total_rounds: Number(value || 0) }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration Summary</Text>
                <Input value={draft.duration_summary} onChange={(e) => setDraft((current) => ({ ...current, duration_summary: e.target.value }))} placeholder="30m + 60m + 45m + 30m" />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'round-structure' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-900">Round Structure</h4>
                <p className="text-sm text-slate-500">Define round order, type, duration, and objective.</p>
              </div>
              <Button onClick={addRound}><Plus size={14} />Add Round</Button>
            </div>
            <div className="space-y-4">
              {draft.rounds.map((round, index) => (
                <div key={round.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-black uppercase tracking-wider text-slate-400">Round {index + 1}</div>
                      <div className="text-sm font-semibold text-slate-900">{round.round_name || `Round ${index + 1}`}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="small" icon={<ArrowUp size={14} />} onClick={() => reorderRounds(round.id, -1)} disabled={index === 0} />
                      <Button size="small" icon={<ArrowDown size={14} />} onClick={() => reorderRounds(round.id, 1)} disabled={index === draft.rounds.length - 1} />
                      <Button size="small" danger icon={<Trash2 size={14} />} onClick={() => removeRound(round.id)} />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Round Name</Text>
                      <Input value={round.round_name} onChange={(e) => updateRound(round.id, { round_name: e.target.value })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Round Type</Text>
                      <Select value={round.round_type} onChange={(value) => updateRound(round.id, { round_type: value })} options={ROUND_TYPE_OPTIONS} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Round Order</Text>
                      <InputNumber className="w-full" min={1} value={round.round_order} onChange={(value) => updateRound(round.id, { round_order: Number(value || 1) })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Round Duration</Text>
                      <InputNumber className="w-full" min={10} value={round.round_duration} onChange={(value) => updateRound(round.id, { round_duration: Number(value || 0) })} addonAfter="min" />
                    </div>
                    <div className="md:col-span-2">
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Round Objective</Text>
                      <TextArea rows={3} value={round.round_objective} onChange={(e) => updateRound(round.id, { round_objective: e.target.value })} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'round-config' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="space-y-4">
              {draft.rounds.map((round, index) => (
                <div key={round.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="mb-4">
                    <div className="text-xs font-black uppercase tracking-wider text-slate-400">Round {index + 1}</div>
                    <div className="text-sm font-semibold text-slate-900">{round.round_name || `Round ${index + 1}`}</div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="md:col-span-2">
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Question / Topic Flow</Text>
                      <Select mode="tags" value={round.question_topic_flow} onChange={(value) => updateRound(round.id, { question_topic_flow: value })} placeholder="Algorithms, architecture review, leadership scenario" />
                    </div>
                    <div className="md:col-span-2">
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interviewer Guidance</Text>
                      <TextArea rows={4} value={round.interviewer_guidance} onChange={(e) => updateRound(round.id, { interviewer_guidance: e.target.value })} />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                      <Select value={round.scorecard_template_id || undefined} onChange={(value) => updateRound(round.id, { scorecard_template_id: value })} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
                    </div>
                    <div>
                      <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Pass / Reject / Review Rule</Text>
                      <Select value={round.round_rule} onChange={(value) => updateRound(round.id, { round_rule: value })} options={ROUND_RULE_OPTIONS} />
                    </div>
                    <div className="md:col-span-2 flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                      <div>
                        <div className="text-xs font-black uppercase tracking-wider text-slate-400">Mandatory Round</div>
                        <div className="text-sm text-slate-500">Mark whether this round is required before candidate progression.</div>
                      </div>
                      <Switch checked={round.mandatory} onChange={(checked) => updateRound(round.id, { mandatory: checked })} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'progression' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Move To Next Round</div>
                  <div className="text-sm text-slate-500">Advance candidates when a round outcome is pass.</div>
                </div>
                <Switch checked={draft.progression.move_to_next_round} onChange={(checked) => setDraft((current) => ({ ...current, progression: { ...current.progression, move_to_next_round: checked } }))} />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Reject After Round</div>
                  <div className="text-sm text-slate-500">Allow immediate rejection after a failed round.</div>
                </div>
                <Switch checked={draft.progression.reject_after_round} onChange={(checked) => setDraft((current) => ({ ...current, progression: { ...current.progression, reject_after_round: checked } }))} />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Manual Review Between Rounds</div>
                  <div className="text-sm text-slate-500">Send borderline outcomes to manual review before progressing.</div>
                </div>
                <Switch checked={draft.progression.manual_review_between_rounds} onChange={(checked) => setDraft((current) => ({ ...current, progression: { ...current.progression, manual_review_between_rounds: checked } }))} />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Skip Round Shell</div>
                  <div className="text-sm text-slate-500">Future-ready shell for conditional round skipping logic.</div>
                </div>
                <Switch checked={draft.progression.skip_round_shell_enabled} onChange={(checked) => setDraft((current) => ({ ...current, progression: { ...current.progression, skip_round_shell_enabled: checked } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'preview' ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Round Flow Summary</div>
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Sequential Round'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="space-y-3">
                  {draft.rounds.map((round, index) => (
                    <div key={round.id} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-slate-900">{index + 1}. {round.round_name || `Round ${index + 1}`}</div>
                        <Tag>{ROUND_TYPE_OPTIONS.find((option) => option.value === round.round_type)?.label || round.round_type}</Tag>
                      </div>
                      <div className="mt-2 text-sm text-slate-500">{round.round_objective || 'Objective pending'}</div>
                      <div className="mt-2 text-xs text-slate-400">{round.round_duration} min</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.sequential_round?.usage?.linked_jobs || []).length}</div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Flows</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(currentUsage?.flows || []).length ? currentUsage?.flows.map((flow) => <Tag key={flow}>{flow}</Tag>) : <Text className="text-sm text-slate-500">No linked flows yet</Text>}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Stages</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(currentUsage?.stages || []).length ? currentUsage?.stages.map((stage) => <Tag key={stage}>{stage}</Tag>) : <Text className="text-sm text-slate-500">No linked stages yet</Text>}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : null}

        <div className="flex items-center justify-between">
          <Button onClick={() => setActiveStep(WIZARD_STEPS[Math.max(stepIndex - 1, 0)].key)} disabled={stepIndex === 0}>Back</Button>
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Sequential Round</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Sequential Round Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate Flow</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Sequential Round'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.duration_summary || 'Duration summary pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.rounds.map((round, index) => (
              <div key={round.id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">{index + 1}. {round.round_name || `Round ${index + 1}`}</div>
                  <Tag>{ROUND_TYPE_OPTIONS.find((option) => option.value === round.round_type)?.label || round.round_type}</Tag>
                </div>
                <div className="mt-2 text-sm text-slate-500">{round.round_objective || 'Objective pending'}</div>
                <div className="mt-2 text-xs text-slate-400">{round.round_duration} min • Rule: {round.round_rule.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
