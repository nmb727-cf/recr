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
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
  Wand2,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type RolePlayEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'scenario' | 'focus' | 'evaluation' | 'preview'

type RolePlayDraft = {
  id: string | null
  name: string
  role_domain: string
  scenario_type: string
  duration_minutes: number
  description: string
  is_active: boolean
  scenario: {
    scenario_description: string
    role_instructions: string
    candidate_role: string
    interviewer_role: string
    expected_objectives: string[]
  }
  evaluation_focus: {
    communication: boolean
    problem_solving: boolean
    negotiation: boolean
    empathy: boolean
    leadership: boolean
  }
  evaluation_model: {
    scorecard_template_id: string
    pass_threshold: number
    reject_threshold: number
    recommendation_logic: string
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'scenario', label: '2. Scenario Builder', icon: Layers3 },
  { key: 'focus', label: '3. Evaluation Focus', icon: ShieldCheck },
  { key: 'evaluation', label: '4. Evaluation Model', icon: Wand2 },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const SCENARIO_TYPES = [
  { value: 'customer_conflict', label: 'Customer Conflict' },
  { value: 'stakeholder_alignment', label: 'Stakeholder Alignment' },
  { value: 'sales_objection', label: 'Sales Objection Handling' },
  { value: 'people_management', label: 'People Management' },
  { value: 'incident_response', label: 'Incident Response' },
]

function createDraft(): RolePlayDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    scenario_type: 'customer_conflict',
    duration_minutes: 40,
    description: '',
    is_active: true,
    scenario: {
      scenario_description: '',
      role_instructions: '',
      candidate_role: '',
      interviewer_role: '',
      expected_objectives: ['Build rapport', 'Resolve tension', 'Drive toward practical next steps'],
    },
    evaluation_focus: {
      communication: true,
      problem_solving: true,
      negotiation: false,
      empathy: true,
      leadership: false,
    },
    evaluation_model: {
      scorecard_template_id: '',
      pass_threshold: 75,
      reject_threshold: 45,
      recommendation_logic: '',
    },
  }
}

function parseTemplate(record: any): RolePlayDraft {
  const meta = record?.metadata?.role_play || {}
  const base = createDraft()
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    scenario_type: meta.setup?.scenario_type || 'customer_conflict',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    scenario: {
      scenario_description: meta.scenario?.scenario_description || '',
      role_instructions: meta.scenario?.role_instructions || '',
      candidate_role: meta.scenario?.candidate_role || '',
      interviewer_role: meta.scenario?.interviewer_role || '',
      expected_objectives: Array.isArray(meta.scenario?.expected_objectives) ? meta.scenario.expected_objectives : base.scenario.expected_objectives,
    },
    evaluation_focus: {
      communication: meta.evaluation_focus?.communication ?? true,
      problem_solving: meta.evaluation_focus?.problem_solving ?? true,
      negotiation: meta.evaluation_focus?.negotiation ?? false,
      empathy: meta.evaluation_focus?.empathy ?? true,
      leadership: meta.evaluation_focus?.leadership ?? false,
    },
    evaluation_model: {
      scorecard_template_id: meta.evaluation_model?.scorecard_template_id || '',
      pass_threshold: Number(meta.evaluation_model?.pass_threshold ?? base.evaluation_model.pass_threshold),
      reject_threshold: Number(meta.evaluation_model?.reject_threshold ?? base.evaluation_model.reject_threshold),
      recommendation_logic: meta.evaluation_model?.recommendation_logic || '',
    },
  }
}

function serializeDraft(draft: RolePlayDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'role_play',
    duration_minutes: draft.duration_minutes,
    instructions: draft.scenario.role_instructions,
    scoring_type: draft.evaluation_model.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      role_play: {
        setup: {
          role_domain: draft.role_domain,
          scenario_type: draft.scenario_type,
        },
        scenario: draft.scenario,
        evaluation_focus: draft.evaluation_focus,
        evaluation_model: draft.evaluation_model,
        usage: existing.metadata?.role_play?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
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

export default function InterviewRolePlayEngine({ embedded = false }: RolePlayEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<RolePlayDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const rolePlayTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'role_play' || template.metadata?.role_play)
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

  const selectedTemplateRecord = rolePlayTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Role Play'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Role play interview duplicated')
    } catch {
      message.error('Failed to duplicate role play interview')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Role play interview archived')
    } catch {
      message.error('Failed to archive role play interview')
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
      message.success('Role play interview saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save role play interview')
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
          <Text className="font-semibold text-slate-900">{name || 'Untitled Role Play'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="orange">Role Play</Tag> },
    { title: 'Scenario Type', key: 'scenario', render: (_, record) => <Text>{record.parsed.scenario_type.replace(/_/g, ' ')}</Text> },
    { title: 'Duration', key: 'duration', render: (_, record) => <Text>{record.duration_minutes || 40} min</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Role Play</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable simulation-based interview templates for scenario-driven evaluation.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={rolePlayTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No role play interviews yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Role Play
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button key={step.key} type="button" onClick={() => setActiveStep(step.key)} className={cn('flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition', activeStep === step.key ? 'border-orange-200 bg-orange-50 text-orange-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300')}>
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Role Play Builder</h3>
            <p className="text-sm text-slate-500">Configure simulation scenarios, roles, evaluation focus, and recommendation logic.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Role Play</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Customer Escalation Role Play" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Customer Success" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scenario Type</Text>
                <Select value={draft.scenario_type} onChange={(value) => setDraft((current) => ({ ...current, scenario_type: value }))} options={SCENARIO_TYPES} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={15} max={180} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Scenario-based simulation to assess candidate response under realistic conditions." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'scenario' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scenario Description</Text>
                <TextArea rows={4} value={draft.scenario.scenario_description} onChange={(e) => setDraft((current) => ({ ...current, scenario: { ...current.scenario, scenario_description: e.target.value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role Instructions</Text>
                <TextArea rows={4} value={draft.scenario.role_instructions} onChange={(e) => setDraft((current) => ({ ...current, scenario: { ...current.scenario, role_instructions: e.target.value } }))} />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Candidate Role</Text>
                  <Input value={draft.scenario.candidate_role} onChange={(e) => setDraft((current) => ({ ...current, scenario: { ...current.scenario, candidate_role: e.target.value } }))} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interviewer Role</Text>
                  <Input value={draft.scenario.interviewer_role} onChange={(e) => setDraft((current) => ({ ...current, scenario: { ...current.scenario, interviewer_role: e.target.value } }))} />
                </div>
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Expected Objectives</Text>
                <Select mode="tags" value={draft.scenario.expected_objectives} onChange={(value) => setDraft((current) => ({ ...current, scenario: { ...current.scenario, expected_objectives: value } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'focus' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              {[
                ['communication', 'Communication'],
                ['problem_solving', 'Problem Solving'],
                ['negotiation', 'Negotiation'],
                ['empathy', 'Empathy'],
                ['leadership', 'Leadership'],
              ].map(([key, label]) => (
                <div key={key} className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                  <div>
                    <div className="text-xs font-black uppercase tracking-wider text-slate-400">{label}</div>
                  </div>
                  <Select
                    value={draft.evaluation_focus[key as keyof RolePlayDraft['evaluation_focus']] ? 'enabled' : 'disabled'}
                    onChange={(value) =>
                      setDraft((current) => ({
                        ...current,
                        evaluation_focus: {
                          ...current.evaluation_focus,
                          [key]: value === 'enabled',
                        },
                      }))
                    }
                    options={[
                      { value: 'enabled', label: 'Enabled' },
                      { value: 'disabled', label: 'Disabled' },
                    ]}
                    className="w-32"
                  />
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.evaluation_model.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Pass Threshold</Text>
                <InputNumber className="w-full" min={0} max={100} value={draft.evaluation_model.pass_threshold} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, pass_threshold: Number(value || 0) } }))} addonAfter="%" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Reject Threshold</Text>
                <InputNumber className="w-full" min={0} max={100} value={draft.evaluation_model.reject_threshold} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, reject_threshold: Number(value || 0) } }))} addonAfter="%" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Recommendation Logic</Text>
                <TextArea rows={4} value={draft.evaluation_model.recommendation_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, recommendation_logic: e.target.value } }))} />
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
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Role Play'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Scenario Type</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.scenario_type.replace(/_/g, ' ')}</div>
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
                  <div className="mb-3 text-xs font-black uppercase tracking-wider text-slate-400">Expected Objectives</div>
                  <div className="flex flex-wrap gap-2">
                    {draft.scenario.expected_objectives.map((objective) => <Tag key={objective}>{objective}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.role_play?.usage?.linked_jobs || []).length}</div>
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
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Role Play</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Role Play Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate View</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Role Play'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.scenario.scenario_description || 'Scenario description pending.'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-sm font-semibold text-slate-900">Candidate Role</div>
            <div className="mt-1 text-sm text-slate-500">{draft.scenario.candidate_role || 'Candidate role pending'}</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-sm font-semibold text-slate-900">Interviewer Role</div>
            <div className="mt-1 text-sm text-slate-500">{draft.scenario.interviewer_role || 'Interviewer role pending'}</div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
