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
  BarChart2,
  Copy,
  Eye,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type BarRaiserEngineProps = {
  embedded?: boolean
}

type WizardStep = 'setup' | 'focus' | 'structure' | 'evaluation' | 'preview'
type SeniorityLevel = 'mid' | 'senior' | 'staff' | 'principal' | 'executive'
type Recommendation = 'strong_hire' | 'hire' | 'no_hire'

type BarRaiserDraft = {
  id: string | null
  name: string
  role_domain: string
  seniority_level: SeniorityLevel
  duration_minutes: number
  description: string
  is_active: boolean
  evaluation_focus: {
    leadership_evaluation: boolean
    decision_making: boolean
    ownership: boolean
    technical_depth_optional: boolean
    culture_impact: boolean
  }
  structure: {
    discussion_topics: string[]
    evaluation_prompts: string[]
    interviewer_guidance: string
    expected_outcomes: string[]
  }
  evaluation_model: {
    scorecard_template_id: string
    hire_no_hire_logic: string
    recommendation_scale: Recommendation[]
    final_recommendation: Recommendation
  }
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'focus', label: '2. Evaluation Focus', icon: ShieldCheck },
  { key: 'structure', label: '3. Interview Structure', icon: Layers3 },
  { key: 'evaluation', label: '4. Evaluation Model', icon: BarChart2 },
  { key: 'preview', label: '5. Usage / Preview', icon: Eye },
]

const SENIORITY_OPTIONS = [
  { value: 'mid', label: 'Mid' },
  { value: 'senior', label: 'Senior' },
  { value: 'staff', label: 'Staff' },
  { value: 'principal', label: 'Principal' },
  { value: 'executive', label: 'Executive' },
]

const RECOMMENDATION_OPTIONS = [
  { value: 'strong_hire', label: 'Strong Hire' },
  { value: 'hire', label: 'Hire' },
  { value: 'no_hire', label: 'No Hire' },
]

function createDraft(): BarRaiserDraft {
  return {
    id: null,
    name: '',
    role_domain: '',
    seniority_level: 'senior',
    duration_minutes: 60,
    description: '',
    is_active: true,
    evaluation_focus: {
      leadership_evaluation: true,
      decision_making: true,
      ownership: true,
      technical_depth_optional: false,
      culture_impact: true,
    },
    structure: {
      discussion_topics: ['Ambiguous decision scenario', 'Cross-functional conflict', 'Long-term ownership'],
      evaluation_prompts: ['Tell me about a decision you made with incomplete information.'],
      interviewer_guidance: '',
      expected_outcomes: ['Clear ownership signal', 'Principled judgment', 'High standards impact'],
    },
    evaluation_model: {
      scorecard_template_id: '',
      hire_no_hire_logic: '',
      recommendation_scale: ['strong_hire', 'hire', 'no_hire'],
      final_recommendation: 'hire',
    },
  }
}

function parseTemplate(record: any): BarRaiserDraft {
  const meta = record?.metadata?.bar_raiser || {}
  const base = createDraft()
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    role_domain: meta.setup?.role_domain || '',
    seniority_level: meta.setup?.seniority_level || 'senior',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    evaluation_focus: {
      leadership_evaluation: meta.evaluation_focus?.leadership_evaluation ?? true,
      decision_making: meta.evaluation_focus?.decision_making ?? true,
      ownership: meta.evaluation_focus?.ownership ?? true,
      technical_depth_optional: meta.evaluation_focus?.technical_depth_optional ?? false,
      culture_impact: meta.evaluation_focus?.culture_impact ?? true,
    },
    structure: {
      discussion_topics: Array.isArray(meta.structure?.discussion_topics) ? meta.structure.discussion_topics : base.structure.discussion_topics,
      evaluation_prompts: Array.isArray(meta.structure?.evaluation_prompts) ? meta.structure.evaluation_prompts : base.structure.evaluation_prompts,
      interviewer_guidance: meta.structure?.interviewer_guidance || '',
      expected_outcomes: Array.isArray(meta.structure?.expected_outcomes) ? meta.structure.expected_outcomes : base.structure.expected_outcomes,
    },
    evaluation_model: {
      scorecard_template_id: meta.evaluation_model?.scorecard_template_id || '',
      hire_no_hire_logic: meta.evaluation_model?.hire_no_hire_logic || '',
      recommendation_scale: Array.isArray(meta.evaluation_model?.recommendation_scale) ? meta.evaluation_model.recommendation_scale : base.evaluation_model.recommendation_scale,
      final_recommendation: meta.evaluation_model?.final_recommendation || 'hire',
    },
  }
}

function serializeDraft(draft: BarRaiserDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: 'bar_raiser',
    duration_minutes: draft.duration_minutes,
    instructions: draft.structure.interviewer_guidance,
    scoring_type: draft.evaluation_model.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      bar_raiser: {
        setup: {
          role_domain: draft.role_domain,
          seniority_level: draft.seniority_level,
        },
        evaluation_focus: draft.evaluation_focus,
        structure: draft.structure,
        evaluation_model: draft.evaluation_model,
        usage: existing.metadata?.bar_raiser?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          scorecard_engine: true,
          flow_engine: true,
          decision_engine: true,
          scheduling_engine: true,
        },
      },
    },
  }
}

export default function InterviewBarRaiserEngine({ embedded = false }: BarRaiserEngineProps) {
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<BarRaiserDraft>(createDraft())

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const barRaiserTemplates = useMemo(
    () =>
      allTemplates
        .filter((template: any) => template.interview_type === 'bar_raiser' || template.metadata?.bar_raiser)
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

  const selectedTemplateRecord = barRaiserTemplates.find((template: any) => template.id === selectedTemplateId) || null
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
        serializeDraft({ ...parseTemplate(record), id: null, name: `${record.name || 'Bar Raiser'} Copy` }, {}),
      )
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Bar raiser interview duplicated')
    } catch {
      message.error('Failed to duplicate bar raiser interview')
    }
  }

  const handleArchive = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      message.success('Bar raiser interview archived')
    } catch {
      message.error('Failed to archive bar raiser interview')
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
      message.success('Bar raiser interview saved')
      setIsBuilderOpen(false)
    } catch {
      message.error('Failed to save bar raiser interview')
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
          <Text className="font-semibold text-slate-900">{name || 'Untitled Bar Raiser'}</Text>
          <Text className="text-xs text-slate-500">{record.parsed.role_domain || 'Role domain pending'}</Text>
        </div>
      ),
    },
    { title: 'Type', key: 'type', render: () => <Tag color="green">Bar Raiser</Tag> },
    { title: 'Level', key: 'level', render: (_, record) => <Text>{record.parsed.seniority_level}</Text> },
    { title: 'Duration', key: 'duration', render: (_, record) => <Text>{record.duration_minutes || 60} min</Text> },
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
            <h2 className="text-xl font-black uppercase tracking-tight text-slate-900">Bar Raiser</h2>
            <p className="mt-1 text-sm text-slate-500">Reusable final quality gate interviews for principled hiring decisions.</p>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create</Button>
        </div>

        <Card className="rounded-2xl border-slate-200">
          <Table rowKey="id" columns={columns} dataSource={barRaiserTemplates} loading={isLoading} pagination={false} locale={{ emptyText: <Empty description="No bar raiser interviews yet" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }} />
        </Card>
      </div>
    )
  }

  return (
    <div className={cn('grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]', embedded ? '' : 'p-6')}>
      <Card className="h-fit rounded-2xl border-slate-200">
        <button type="button" onClick={() => setIsBuilderOpen(false)} className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-600">
          <ArrowLeft size={16} />
          Back to Bar Raiser
        </button>
        <div className="space-y-2">
          {WIZARD_STEPS.map((step) => {
            const Icon = step.icon
            return (
              <button key={step.key} type="button" onClick={() => setActiveStep(step.key)} className={cn('flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition', activeStep === step.key ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300')}>
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
            <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">Bar Raiser Builder</h3>
            <p className="text-sm text-slate-500">Configure leadership-focused final gate interviews and recommendation logic.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>Save Bar Raiser</Button>
          </div>
        </div>

        {activeStep === 'setup' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Name</Text>
                <Input value={draft.name} onChange={(e) => setDraft((current) => ({ ...current, name: e.target.value }))} placeholder="Senior Product Bar Raiser" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Role / Domain</Text>
                <Input value={draft.role_domain} onChange={(e) => setDraft((current) => ({ ...current, role_domain: e.target.value }))} placeholder="Product Management" />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Seniority Level</Text>
                <Select value={draft.seniority_level} onChange={(value) => setDraft((current) => ({ ...current, seniority_level: value }))} options={SENIORITY_OPTIONS} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                <InputNumber className="w-full" min={15} max={180} value={draft.duration_minutes} onChange={(value) => setDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} addonAfter="min" />
              </div>
              <div className="md:col-span-2">
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Description</Text>
                <TextArea rows={4} value={draft.description} onChange={(e) => setDraft((current) => ({ ...current, description: e.target.value }))} placeholder="Final quality gate to validate judgment, ownership, and long-term bar raising potential." />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'focus' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              {[
                ['leadership_evaluation', 'Leadership Evaluation'],
                ['decision_making', 'Decision Making'],
                ['ownership', 'Ownership'],
                ['technical_depth_optional', 'Technical Depth (Optional)'],
                ['culture_impact', 'Culture Impact'],
              ].map(([key, label]) => (
                <div key={key} className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
                  <div>
                    <div className="text-xs font-black uppercase tracking-wider text-slate-400">{label}</div>
                  </div>
                  <Select
                    value={draft.evaluation_focus[key as keyof BarRaiserDraft['evaluation_focus']] ? 'enabled' : 'disabled'}
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

        {activeStep === 'structure' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Discussion Topics</Text>
                <Select mode="tags" value={draft.structure.discussion_topics} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, discussion_topics: value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Evaluation Prompts</Text>
                <Select mode="tags" value={draft.structure.evaluation_prompts} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, evaluation_prompts: value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interviewer Guidance</Text>
                <TextArea rows={4} value={draft.structure.interviewer_guidance} onChange={(e) => setDraft((current) => ({ ...current, structure: { ...current.structure, interviewer_guidance: e.target.value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Expected Outcomes</Text>
                <Select mode="tags" value={draft.structure.expected_outcomes} onChange={(value) => setDraft((current) => ({ ...current, structure: { ...current.structure, expected_outcomes: value } }))} />
              </div>
            </div>
          </Card>
        ) : null}

        {activeStep === 'evaluation' ? (
          <Card className="rounded-2xl border-slate-200">
            <div className="grid gap-4">
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Scorecard Mapping</Text>
                <Select value={draft.evaluation_model.scorecard_template_id || undefined} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, scorecard_template_id: value } }))} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} allowClear />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Hire / No Hire Logic</Text>
                <TextArea rows={4} value={draft.evaluation_model.hire_no_hire_logic} onChange={(e) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, hire_no_hire_logic: e.target.value } }))} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Recommendation Scale</Text>
                <Select mode="multiple" value={draft.evaluation_model.recommendation_scale} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, recommendation_scale: value } }))} options={RECOMMENDATION_OPTIONS} />
              </div>
              <div>
                <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Final Recommendation</Text>
                <Select value={draft.evaluation_model.final_recommendation} onChange={(value) => setDraft((current) => ({ ...current, evaluation_model: { ...current.evaluation_model, final_recommendation: value } }))} options={RECOMMENDATION_OPTIONS} />
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
                  <h4 className="mt-1 text-lg font-bold text-slate-900">{draft.name || 'Untitled Bar Raiser'}</h4>
                  <p className="mt-2 text-sm text-slate-500">{draft.description || 'Description pending'}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Level</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.seniority_level}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Duration</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.duration_minutes} min</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Recommendation</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900">{draft.evaluation_model.final_recommendation.replace('_', ' ')}</div>
                  </div>
                </div>
                <div>
                  <div className="mb-3 text-xs font-black uppercase tracking-wider text-slate-400">Discussion Topics</div>
                  <div className="flex flex-wrap gap-2">
                    {draft.structure.discussion_topics.map((topic) => <Tag key={topic}>{topic}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <div className="space-y-4">
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-slate-400">Linked Jobs</div>
                  <div className="mt-2 text-sm text-slate-600">{(selectedTemplateRecord?.metadata?.bar_raiser?.usage?.linked_jobs || []).length}</div>
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
          {stepIndex === WIZARD_STEPS.length - 1 ? <Button type="primary" loading={saving} onClick={handleSave}>Save Bar Raiser</Button> : <Button type="primary" onClick={() => setActiveStep(WIZARD_STEPS[Math.min(stepIndex + 1, WIZARD_STEPS.length - 1)].key)}>Next</Button>}
        </div>
      </div>

      <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={920} title="Bar Raiser Preview">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-950 p-5 text-white">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">Candidate View</div>
            <h4 className="mt-2 text-xl font-semibold">{draft.name || 'Untitled Bar Raiser'}</h4>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">{draft.structure.interviewer_guidance || 'Interviewer guidance pending.'}</p>
          </div>
          <div className="space-y-3">
            {draft.structure.evaluation_prompts.map((prompt) => (
              <div key={prompt} className="rounded-xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">{prompt}</div>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  )
}
