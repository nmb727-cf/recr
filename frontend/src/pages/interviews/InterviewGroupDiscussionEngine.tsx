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
  ArrowLeft,
  Copy,
  Eye,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
  Users,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type GroupDiscussionEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'structure' | 'evaluation' | 'participants' | 'preview'

type GroupDiscussionDraft = {
  id: string | null
  name: string
  role_domain: string
  description: string
  duration_minutes: number
  max_participants: number
  is_active: boolean
  structure: {
    topic_selection: string[]
    discussion_instructions: string
    evaluation_focus_areas: string[]
    discussion_guidelines: string
  }
  evaluation: {
    individual_scoring: boolean
    group_scoring: boolean
    evaluator_notes: string
    scorecard_template_id: string
  }
  participants: {
    multiple_candidates: boolean
    multiple_evaluators: boolean
    participant_limit: number
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'structure', label: '2. Discussion Structure', icon: Layers3 },
  { key: 'evaluation', label: '3. Evaluation Model', icon: ShieldCheck },
  { key: 'participants', label: '4. Participant Handling', icon: Users },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

function createDraft(): GroupDiscussionDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    description: '',
    duration_minutes: 45,
    max_participants: 6,
    is_active: true,
    structure: {
      topic_selection: ['Market entry strategy', 'Prioritization tradeoffs'],
      discussion_instructions: '',
      evaluation_focus_areas: ['Communication', 'Collaboration', 'Reasoning'],
      discussion_guidelines: '',
    },
    evaluation: {
      individual_scoring: true,
      group_scoring: false,
      evaluator_notes: '',
      scorecard_template_id: '',
    },
    participants: {
      multiple_candidates: true,
      multiple_evaluators: true,
      participant_limit: 6,
    },
  }
}

function parseTemplate(record: any): GroupDiscussionDraft {
  const meta = record?.metadata?.group_discussion || {}
  const base = createDraft()
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    description: record.description || '',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    max_participants: Number(meta.setup?.max_participants ?? base.max_participants),
    is_active: record.is_active ?? true,
    structure: {
      topic_selection: Array.isArray(meta.structure?.topic_selection) ? meta.structure.topic_selection : base.structure.topic_selection,
      discussion_instructions: meta.structure?.discussion_instructions || '',
      evaluation_focus_areas: Array.isArray(meta.structure?.evaluation_focus_areas) ? meta.structure.evaluation_focus_areas : base.structure.evaluation_focus_areas,
      discussion_guidelines: meta.structure?.discussion_guidelines || '',
    },
    evaluation: {
      individual_scoring: meta.evaluation?.individual_scoring ?? true,
      group_scoring: meta.evaluation?.group_scoring ?? false,
      evaluator_notes: meta.evaluation?.evaluator_notes || '',
      scorecard_template_id: meta.evaluation?.scorecard_template_id || '',
    },
    participants: {
      multiple_candidates: meta.participants?.multiple_candidates ?? true,
      multiple_evaluators: meta.participants?.multiple_evaluators ?? true,
      participant_limit: Number(meta.participants?.participant_limit ?? base.participants.participant_limit),
    },
  }
}

function serializeDraft(draft: GroupDiscussionDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'group_discussion',
    duration_minutes: draft.duration_minutes,
    instructions: draft.structure.discussion_instructions,
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      group_discussion: {
        setup: {
          role_domain: draft.role_domain,
          max_participants: draft.max_participants,
        },
        structure: draft.structure,
        evaluation: draft.evaluation,
        participants: draft.participants,
        usage: existing.metadata?.group_discussion?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
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

export default function InterviewGroupDiscussionEngine({ embedded = false }: GroupDiscussionEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<GroupDiscussionDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const groupTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'group_discussion' || template.metadata?.group_discussion)
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

  const selectedTemplateRecord = groupTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Group Discussion'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Group discussion duplicated')
    } catch {
      message.error('Failed to duplicate group discussion')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Group discussion archived')
    } catch {
      message.error('Failed to archive group discussion')
    }
  }

  const handleSave = async () => {
    if (!draft.name.trim()) {
      message.error('Discussion name is required')
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
      message.success('Group discussion saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save group discussion')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Discussion Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div className="flex min-w-0 flex-col">
          <Text className="font-semibold text-slate-900">{name || 'Untitled Group Discussion'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="teal">Group Discussion</Tag> },
    { title: 'Participants Count', key: 'participants', render: (_, record) => <Text>{record.parsed.participants.participant_limit}</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Group Discussion</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable multi-candidate group discussion templates with shared evaluation setup.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={groupTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No group discussions yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Group Discussions
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button key={step.key} type="button" onClick={() => setActiveStep(step.key)} className={cn('flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition', activeStep === step.key ? 'border-teal-200 bg-teal-50 text-teal-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300')}>
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Group Discussion Builder</h3>
            <p className="text-sm text-slate-500">Configure topic, evaluation, and participant handling for multi-candidate discussions.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Group Discussion</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Discussion Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Leadership Group Discussion" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Graduate Sales Program" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Assess group collaboration, communication, and decision-making." />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={15} max={180} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Max Participants</Text>
                <InputNumber className="w-full" min={2} max={20} value={draft.max_participants} onChange={(value) => setDraft((current) => ({ ...current, max_participants: Number(value || 0), participants: { ...current.participants, participant_limit: Number(value || 0) } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'structure' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Topic Selection</Text>
                <Select mode="tags" value={draft.structure.topic_selection} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, topic_selection: value } }))} placeholder="Market expansion, team conflict, prioritization" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Discussion Instructions</Text>
                <TextArea rows={4} value={draft.structure.discussion_instructions} onChange={(e) => setDraft((current) => ({ ...current, structure: { ...current.structure, discussion_instructions: e.target.value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluation Focus Areas</Text>
                <Select mode="tags" value={draft.structure.evaluation_focus_areas} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, evaluation_focus_areas: value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Discussion Guidelines</Text>
                <TextArea rows={4} value={draft.structure.discussion_guidelines} onChange={(e) => setDraft((current) => ({ ...current, structure: { ...current.structure, discussion_guidelines: e.target.value } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Individual Scoring</div>
                  <div className="text-sm text-slate-500">Evaluate each candidate independently within the discussion.</div>
                </div>
                <Switch checked={draft.evaluation.individual_scoring} onChange={(checked) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, individual_scoring: checked } }))} />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Group Scoring</div>
                  <div className="text-sm text-slate-500">Allow evaluator scoring for overall group interaction outcome.</div>
                </div>
                <Switch checked={draft.evaluation.group_scoring} onChange={(checked) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, group_scoring: checked } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluator Notes</Text>
                <TextArea rows={4} value={draft.evaluation.evaluator_notes} onChange={(e) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, evaluator_notes: e.target.value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.evaluation.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'participants' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Multiple Candidates</div>
                  <div className="text-sm text-slate-500">Support multiple candidate participation in the same session.</div>
                </div>
                <Switch checked={draft.participants.multiple_candidates} onChange={(checked) => setDraft((current) => ({ ...current, participants: { ...current.participants, multiple_candidates: checked } }))} />
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Multiple Evaluators</div>
                  <div className="text-sm text-slate-500">Allow multiple evaluators to observe and score the discussion.</div>
                </div>
                <Switch checked={draft.participants.multiple_evaluators} onChange={(checked) => setDraft((current) => ({ ...current, participants: { ...current.participants, multiple_evaluators: checked } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Participant Limit</Text>
                <InputNumber className="w-full" min={2} max={20} value={draft.participants.participant_limit} onChange={(value) => setDraft((current) => ({ ...current, participants: { ...current.participants, participant_limit: Number(value || 0) } }))} />
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
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Group Discussion'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Participants</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.participants.participant_limit}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Duration</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.duration_minutes} min</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Role / Domain</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.role_domain || 'Pending'}</div>
                  </div>
                </div>
                <div>
                  <div className="mb-3 text-xs font-black uppercase tracking-wider text-slate-400">Topics</div>
                  <div className="flex flex-wrap gap-2">
                    {draft.structure.topic_selection.map((topic) => <Tag key={topic}>{topic}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.group_discussion?.usage?.linked_jobs || []).length}</div>
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
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Group Discussion</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Group Discussion Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate View</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Group Discussion'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.structure.discussion_instructions || 'Discussion instructions pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.structure.topic_selection.map((topic) => (
              <div key={topic} className="rounded-xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">{topic}</div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
