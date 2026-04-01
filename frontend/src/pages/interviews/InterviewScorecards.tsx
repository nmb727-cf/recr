import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Empty, Input, InputNumber, Select, Space, Switch, Table, Tag, Typography, message } from 'antd'
import { ArrowLeft, ClipboardList, Copy, Eye, Plus, Settings2, ShieldCheck, Target, Trash2 } from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'
import { getCategoryOptions, getInterviewTypeCategory, INTERVIEW_TYPE_CATEGORIES, type InterviewTypeCategory } from '@/utils/interviewTypeUx'

const { Text } = Typography
const { TextArea } = Input

const RATING_OPTIONS = [
  { value: 'scale_1_5', label: '1-5 scale' },
  { value: 'yes_no', label: 'Yes / no' },
  { value: 'pass_fail', label: 'Pass / fail' },
  { value: 'custom_scale', label: 'Custom scale' },
]

const SCORECARD_STEPS = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'dimensions', label: '2. Dimensions', icon: ClipboardList },
  { key: 'scoring', label: '3. Scoring Logic', icon: ShieldCheck },
  { key: 'recommendation', label: '4. Recommendation Logic', icon: Target },
  { key: 'preview', label: '5. Preview', icon: Eye },
] as const

const SCORECARD_STEP_ORDER = SCORECARD_STEPS.map((step) => step.key)

type ScorecardBuilderStep = (typeof SCORECARD_STEPS)[number]['key']

type ScorecardDimension = {
  id: string
  attribute_name: string
  description: string
  weight: number
  rating_type: string
  required: boolean
  custom_scale: string
}

type ScorecardDraft = {
  id: string | null
  name: string
  description: string
  interview_type: string
  is_active: boolean
  reusable_template: boolean
  dimensions: ScorecardDimension[]
  scoring_logic: {
    ai_scoring_enabled: boolean
    manual_scoring_enabled: boolean
    blend_mode: 'ai_only' | 'manual_only' | 'blended'
    ai_weight: number
    manual_weight: number
  }
  recommendation_logic: {
    pass_threshold: number
    reject_threshold: number
  }
}

type InterviewScorecardsProps = {
  embedded?: boolean
}

function createDimension(overrides: Partial<ScorecardDimension> = {}): ScorecardDimension {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    attribute_name: '',
    description: '',
    weight: 20,
    rating_type: 'scale_1_5',
    required: true,
    custom_scale: '',
    ...overrides,
  }
}

function createDraft(): ScorecardDraft {
  return {
    id: null,
    name: '',
    description: '',
    interview_type: 'ai_screening',
    is_active: true,
    reusable_template: true,
    dimensions: [
      createDimension({ attribute_name: 'Communication' }),
      createDimension({ attribute_name: 'Problem Solving' }),
    ],
    scoring_logic: {
      ai_scoring_enabled: true,
      manual_scoring_enabled: true,
      blend_mode: 'blended',
      ai_weight: 60,
      manual_weight: 40,
    },
    recommendation_logic: {
      pass_threshold: 75,
      reject_threshold: 45,
    },
  }
}

function parseRecord(record: any): ScorecardDraft {
  return {
    id: record.id,
    name: record.name || '',
    description: record.description || '',
    interview_type: record.interview_type || 'ai_screening',
    is_active: record.is_active ?? true,
    reusable_template: record.metadata?.reusable_template ?? true,
    dimensions: Array.isArray(record.attributes) && record.attributes.length
      ? record.attributes.map((attribute: any) => ({
          id: attribute.id || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          attribute_name: attribute.attribute_name || '',
          description: attribute.description || '',
          weight: Number(attribute.weight || 0),
          rating_type: attribute.rating_type || 'scale_1_5',
          required: Boolean(attribute.required),
          custom_scale: Array.isArray(attribute.custom_scale) ? attribute.custom_scale.join(', ') : '',
        }))
      : [createDimension()],
    scoring_logic: {
      ai_scoring_enabled: record.metadata?.scoring_logic?.ai_scoring_enabled ?? true,
      manual_scoring_enabled: record.metadata?.scoring_logic?.manual_scoring_enabled ?? true,
      blend_mode: record.metadata?.scoring_logic?.blend_mode ?? 'blended',
      ai_weight: Number(record.metadata?.scoring_logic?.ai_weight ?? 60),
      manual_weight: Number(record.metadata?.scoring_logic?.manual_weight ?? 40),
    },
    recommendation_logic: {
      pass_threshold: Number(record.metadata?.recommendation_logic?.pass_threshold ?? record.metadata?.recommendation_mapping?.recommend ?? 75),
      reject_threshold: Number(record.metadata?.recommendation_logic?.reject_threshold ?? record.metadata?.recommendation_mapping?.concern ?? 45),
    },
  }
}

function buildPayload(draft: ScorecardDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: draft.interview_type,
    is_active: draft.is_active,
    attributes: draft.dimensions.map((dimension, index) => ({
      attribute_name: dimension.attribute_name,
      weight: Number(dimension.weight || 0),
      rating_type: dimension.rating_type,
      required: Boolean(dimension.required),
      custom_scale: dimension.rating_type === 'custom_scale'
        ? String(dimension.custom_scale || '')
            .split(',')
            .map((entry: string) => entry.trim())
            .filter(Boolean)
        : [],
      order_index: index,
    })),
    metadata: {
      ...(existing.metadata || {}),
      reusable_template: draft.reusable_template,
      scoring_logic: draft.scoring_logic,
      recommendation_logic: draft.recommendation_logic,
      recommendation_mapping: {
        strong_recommend: 90,
        recommend: draft.recommendation_logic.pass_threshold,
        neutral: Math.round((draft.recommendation_logic.pass_threshold + draft.recommendation_logic.reject_threshold) / 2),
        concern: draft.recommendation_logic.reject_threshold,
        reject: 0,
      },
    },
  }
}

export default function InterviewScorecards({ embedded = false }: InterviewScorecardsProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null)
  const [activeStep, setActiveStep] = useState<ScorecardBuilderStep>('setup')
  const [selectedTypeCategory, setSelectedTypeCategory] = useState<InterviewTypeCategory>('AI')
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<ScorecardDraft>(createDraft())

  const { data, isLoading } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: templatesData } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const scorecards = (data as any)?.scorecards ?? []
  const templates = (templatesData as any)?.templates ?? []
  const flows = (flowsData as any)?.flows ?? []

  const usageMap = useMemo(() => {
    return new Map<string, number>(
      scorecards.map((scorecard: any) => {
        const templateUsage = templates.filter((template: any) =>
          template?.metadata?.ai_interview?.evaluation?.scorecard_template_id === scorecard.id
          || template?.scorecard_template_id === scorecard.id,
        ).length
        const flowUsage = flows.filter((flow: any) =>
          (flow?.stages || []).some((stage: any) => stage?.scorecard_template_id === scorecard.id),
        ).length
        return [scorecard.id, templateUsage + flowUsage]
      }) as Array<[string, number]>,
    )
  }, [flows, scorecards, templates])

  const activeStepIndex = SCORECARD_STEP_ORDER.indexOf(activeStep)
  const totalWeight = draft.dimensions.reduce((sum, dimension) => sum + Number(dimension.weight || 0), 0)
  const manualReviewStart = draft.recommendation_logic.reject_threshold + 1
  const manualReviewEnd = draft.recommendation_logic.pass_threshold - 1
  const usageSummary = selectedRecord?.id ? usageMap.get(selectedRecord.id) || 0 : 0
  const filteredTypeOptions = getCategoryOptions(selectedTypeCategory)

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.interview_type),
    dimensions: Boolean(draft.dimensions.some((dimension) => dimension.attribute_name.trim())),
    scoring: Boolean(draft.scoring_logic.ai_scoring_enabled || draft.scoring_logic.manual_scoring_enabled),
    recommendation: draft.recommendation_logic.pass_threshold > draft.recommendation_logic.reject_threshold,
    preview: Boolean(draft.dimensions.length),
  }

  const updateDraft = (updater: (current: ScorecardDraft) => ScorecardDraft) => {
    setDraft((current) => updater(current))
  }

  const updateDimension = (dimensionId: string, updates: Partial<ScorecardDimension>) => {
    updateDraft((current) => ({
      ...current,
      dimensions: current.dimensions.map((dimension) =>
        dimension.id === dimensionId ? { ...dimension, ...updates } : dimension,
      ),
    }))
  }

  const addDimension = () => {
    updateDraft((current) => ({
      ...current,
      dimensions: [...current.dimensions, createDimension()],
    }))
  }

  const removeDimension = (dimensionId: string) => {
    updateDraft((current) => {
      const nextDimensions = current.dimensions.filter((dimension) => dimension.id !== dimensionId)
      return {
        ...current,
        dimensions: nextDimensions.length ? nextDimensions : [createDimension()],
      }
    })
  }

  const openCreate = () => {
    setSelectedRecord(null)
    setDraft(createDraft())
    setSelectedTypeCategory(getInterviewTypeCategory('ai_screening'))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = (record: any, step: ScorecardBuilderStep = 'setup') => {
    setSelectedRecord(record)
    setDraft(parseRecord(record))
    setSelectedTypeCategory(getInterviewTypeCategory(record.interview_type || 'ai_screening'))
    setActiveStep(step)
    setIsBuilderOpen(true)
  }

  const duplicateScorecard = async (record: any) => {
    try {
      const sourceDraft = parseRecord(record)
      const payload = buildPayload({
        ...sourceDraft,
        id: null,
        name: `${sourceDraft.name} Copy`,
        is_active: false,
      }, record)
      await interviewsApi.createScorecard(payload)
      message.success('Scorecard duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-scorecards'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to duplicate scorecard')
    }
  }

  const archiveScorecard = async (record: any) => {
    try {
      await interviewsApi.updateScorecard(record.id, { ...record, is_active: false })
      message.success('Scorecard archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-scorecards'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to archive scorecard')
    }
  }

  const saveDraft = async () => {
    setSaving(true)
    try {
      const payload = buildPayload(draft, selectedRecord)
      if (selectedRecord?.id) {
        await interviewsApi.updateScorecard(selectedRecord.id, payload)
        message.success('Scorecard updated')
      } else {
        await interviewsApi.createScorecard(payload)
        message.success('Scorecard created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-scorecards'] })
      setIsBuilderOpen(false)
      setSelectedRecord(null)
      setDraft(createDraft())
      setActiveStep('setup')
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save scorecard')
    } finally {
      setSaving(false)
    }
  }

  const goToPrevStep = () => {
    if (activeStepIndex > 0) setActiveStep(SCORECARD_STEP_ORDER[activeStepIndex - 1])
  }

  const goToNextStep = () => {
    if (activeStepIndex < SCORECARD_STEP_ORDER.length - 1) setActiveStep(SCORECARD_STEP_ORDER[activeStepIndex + 1])
  }

  const BuilderField = ({ label, helper, children }: { label: string; helper?: string; children: ReactNode }) => (
    <div className="space-y-2">
      <div>
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{label}</p>
        {helper ? <p className="mt-1 text-xs text-slate-500">{helper}</p> : null}
      </div>
      {children}
    </div>
  )

  const columns: ColumnsType<any> = [
    {
      title: 'Scorecard Name',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, record: any) => (
        <div>
          <Text className="font-bold text-slate-900">{value}</Text>
          <div className="text-xs text-slate-400">{record.description || 'No description'}</div>
        </div>
      ),
    },
    {
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value: string) => <Tag className="uppercase">{value?.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Dimension Count',
      key: 'dimensions',
      render: (_, record: any) => record.attributes?.length || 0,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => <Tag color={value ? 'success' : 'default'}>{value ? 'Active' : 'Archived'}</Tag>,
    },
    {
      title: 'Usage Count',
      key: 'usage_count',
      render: (_, record: any) => usageMap.get(record.id) || 0,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (value: string) => new Date(value).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: any) => (
        <Space wrap>
          <Button size="small" onClick={() => openEdit(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateScorecard(record)} icon={<Copy size={14} />}>Duplicate</Button>
          <Button size="small" onClick={() => openEdit(record, 'preview')} icon={<Eye size={14} />}>Preview</Button>
          <Button size="small" danger onClick={() => archiveScorecard(record)}>Archive</Button>
        </Space>
      ),
    },
  ]

  const listView = (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <ClipboardList size={18} />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">Scorecards</h2>
            <p className="mt-1 text-xs text-slate-500">Reusable scorecard templates connected to AI interviews, technical rounds, panels, HR rounds, and flow stages.</p>
          </div>
        </div>
        <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create Scorecard</Button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-md overflow-hidden">
        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={scorecards}
          columns={columns}
          pagination={{ pageSize: 12, hideOnSinglePage: true }}
          className="enterprise-table"
          locale={{
            emptyText: (
              <Empty description="No scorecards yet" image={Empty.PRESENTED_IMAGE_SIMPLE}>
                <Button type="primary" onClick={openCreate}>Create Scorecard</Button>
              </Empty>
            ),
          }}
        />
      </div>
    </div>
  )

  const builderView = (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-3">
        <div className="sticky top-6 space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Builder Steps</h3>
            <div className="mt-4 space-y-2">
              {SCORECARD_STEPS.map((step) => {
                const Icon = step.icon
                const done = stepCompletion[step.key]
                return (
                  <button
                    key={step.key}
                    type="button"
                    onClick={() => setActiveStep(step.key)}
                    className={cn(
                      'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition',
                      activeStep === step.key ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white hover:border-slate-300',
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn('flex h-8 w-8 items-center justify-center rounded-xl', done ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500')}>
                        <Icon size={14} />
                      </div>
                      <div>
                        <p className="text-xs font-black uppercase tracking-widest text-slate-900">{step.label}</p>
                        <p className="text-[11px] text-slate-500">{done ? 'Complete' : 'Needs input'}</p>
                      </div>
                    </div>
                    <Tag color={done ? 'success' : 'default'}>{done ? 'Done' : 'Open'}</Tag>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Scorecard Status</h3>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">State</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{selectedRecord ? 'Editing' : 'Draft'}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Completed</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{Object.values(stepCompletion).filter(Boolean).length}/5</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-6 space-y-6">
        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Current Step</p>
            <p className="mt-1 text-sm font-bold text-slate-900">{SCORECARD_STEPS[activeStepIndex]?.label}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
            <Button onClick={goToNextStep} disabled={activeStepIndex === SCORECARD_STEP_ORDER.length - 1}>Next</Button>
          </div>
        </div>

        <div className={cn(activeStep === 'setup' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <Settings2 size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">1. Setup</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <BuilderField label="Scorecard Name">
                <Input value={draft.name} onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
              </BuilderField>
              <BuilderField label="Interview Type">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <Select
                    value={selectedTypeCategory}
                    options={INTERVIEW_TYPE_CATEGORIES.map((category) => ({ value: category, label: category }))}
                    onChange={(value) => setSelectedTypeCategory(value)}
                  />
                  <Select
                    value={draft.interview_type}
                    options={filteredTypeOptions.map((option) => ({ value: option.value, label: option.label }))}
                    onChange={(value) => updateDraft((current) => ({ ...current, interview_type: value }))}
                  />
                </div>
              </BuilderField>
              <div className="md:col-span-2">
                <BuilderField label="Description">
                  <TextArea rows={3} value={draft.description} onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
                </BuilderField>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4 md:col-span-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Reusable template</span>
                  <Switch checked={draft.reusable_template} onChange={(checked) => updateDraft((current) => ({ ...current, reusable_template: checked }))} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className={cn(activeStep === 'dimensions' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <ClipboardList size={16} className="text-indigo-600" />
                <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">2. Dimensions</h2>
              </div>
              <Button type="dashed" onClick={addDimension} icon={<Plus size={14} />}>Add Dimension</Button>
            </div>
            <div className="space-y-4">
              {draft.dimensions.map((dimension, index) => (
                <div key={dimension.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <p className="text-sm font-bold text-slate-900">{dimension.attribute_name || `Dimension ${index + 1}`}</p>
                    <Button danger type="text" icon={<Trash2 size={14} />} onClick={() => removeDimension(dimension.id)}>Remove</Button>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <BuilderField label="Dimension Name">
                      <Input value={dimension.attribute_name} onChange={(event) => updateDimension(dimension.id, { attribute_name: event.target.value })} />
                    </BuilderField>
                    <BuilderField label="Weight">
                      <InputNumber min={0} max={100} className="w-full" addonAfter="%" value={dimension.weight} onChange={(value) => updateDimension(dimension.id, { weight: Number(value || 0) })} />
                    </BuilderField>
                    <BuilderField label="Rating Scale">
                      <Select value={dimension.rating_type} options={RATING_OPTIONS} onChange={(value) => updateDimension(dimension.id, { rating_type: value })} />
                    </BuilderField>
                    <div className="rounded-2xl border border-slate-200 p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-slate-900">Required</span>
                        <Switch checked={dimension.required} onChange={(checked) => updateDimension(dimension.id, { required: checked })} />
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <BuilderField label="Description">
                        <TextArea rows={2} value={dimension.description} onChange={(event) => updateDimension(dimension.id, { description: event.target.value })} />
                      </BuilderField>
                    </div>
                    {dimension.rating_type === 'custom_scale' ? (
                      <div className="md:col-span-2">
                        <BuilderField label="Custom Scale Values" helper="Comma separated values for custom ratings.">
                          <Input value={dimension.custom_scale} onChange={(event) => updateDimension(dimension.id, { custom_scale: event.target.value })} />
                        </BuilderField>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className={cn(activeStep === 'scoring' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">3. Scoring Logic</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">AI scoring</span>
                  <Switch checked={draft.scoring_logic.ai_scoring_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, scoring_logic: { ...current.scoring_logic, ai_scoring_enabled: checked } }))} />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Manual scoring</span>
                  <Switch checked={draft.scoring_logic.manual_scoring_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, scoring_logic: { ...current.scoring_logic, manual_scoring_enabled: checked } }))} />
                </div>
              </div>
              <BuilderField label="Scoring Mode">
                <Select
                  value={draft.scoring_logic.blend_mode}
                  options={[
                    { value: 'ai_only', label: 'AI only' },
                    { value: 'manual_only', label: 'Manual only' },
                    { value: 'blended', label: 'Blended' },
                  ]}
                  onChange={(value) => updateDraft((current) => ({ ...current, scoring_logic: { ...current.scoring_logic, blend_mode: value } }))}
                />
              </BuilderField>
            </div>
            {draft.scoring_logic.blend_mode === 'blended' ? (
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <BuilderField label="AI Weight">
                  <InputNumber min={0} max={100} className="w-full" addonAfter="% AI" value={draft.scoring_logic.ai_weight} onChange={(value) => updateDraft((current) => ({ ...current, scoring_logic: { ...current.scoring_logic, ai_weight: Number(value || 0) } }))} />
                </BuilderField>
                <BuilderField label="Manual Weight">
                  <InputNumber min={0} max={100} className="w-full" addonAfter="% Manual" value={draft.scoring_logic.manual_weight} onChange={(value) => updateDraft((current) => ({ ...current, scoring_logic: { ...current.scoring_logic, manual_weight: Number(value || 0) } }))} />
                </BuilderField>
              </div>
            ) : null}
          </div>
        </div>

        <div className={cn(activeStep === 'recommendation' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <Target size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">4. Recommendation Logic</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <BuilderField label="Pass Threshold">
                <InputNumber min={0} max={100} className="w-full" value={draft.recommendation_logic.pass_threshold} onChange={(value) => updateDraft((current) => ({ ...current, recommendation_logic: { ...current.recommendation_logic, pass_threshold: Number(value || 0) } }))} />
              </BuilderField>
              <BuilderField label="Reject Threshold">
                <InputNumber min={0} max={100} className="w-full" value={draft.recommendation_logic.reject_threshold} onChange={(value) => updateDraft((current) => ({ ...current, recommendation_logic: { ...current.recommendation_logic, reject_threshold: Number(value || 0) } }))} />
              </BuilderField>
            </div>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-bold text-slate-900">Manual Review Range</p>
              <p className="mt-2 text-xs text-slate-500">
                {manualReviewEnd >= manualReviewStart
                  ? `${manualReviewStart} - ${manualReviewEnd}`
                  : 'Thresholds overlap. Increase pass threshold or reduce reject threshold.'}
              </p>
            </div>
          </div>
        </div>

        <div className={cn(activeStep === 'preview' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
            <div className="mb-2 flex items-center gap-2">
              <Eye size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">5. Preview</h2>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-950 p-5 text-white">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard Preview</p>
              <h3 className="mt-3 text-xl font-black">{draft.name || 'Untitled Scorecard'}</h3>
              <p className="mt-2 text-sm text-slate-300">{draft.description || 'Scorecard description appears here.'}</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Dimensions Summary</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.dimensions.length} dimensions</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Weight Summary</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{totalWeight}% total weight</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scoring Logic</p>
                <p className="mt-2 text-sm font-bold text-slate-900">
                  {draft.scoring_logic.blend_mode === 'blended'
                    ? `${draft.scoring_logic.ai_weight}% AI / ${draft.scoring_logic.manual_weight}% Manual`
                    : draft.scoring_logic.blend_mode.replace(/_/g, ' ')}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage Summary</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{usageSummary} linked uses</p>
              </div>
            </div>
            <div className="space-y-3">
              {draft.dimensions.map((dimension) => (
                <div key={dimension.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{dimension.attribute_name || 'Unnamed dimension'}</p>
                      <p className="mt-1 text-xs text-slate-500">{dimension.description || 'No dimension description'}</p>
                    </div>
                    <Tag>{dimension.weight}%</Tag>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
          <div className="flex items-center gap-2">
            {activeStepIndex < SCORECARD_STEP_ORDER.length - 1 ? (
              <Button type="primary" onClick={goToNextStep}>Next Step</Button>
            ) : (
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Scorecard</Button>
            )}
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-3 space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Preview Summary</h3>
          <div className="mt-4 space-y-3">
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Interview Type</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{draft.interview_type.replace(/_/g, ' ')}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Dimensions</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{draft.dimensions.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Weight Total</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{totalWeight}%</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{usageSummary}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  if (embedded) {
    return (
      <>
        {isBuilderOpen ? (
          <div className="mb-4 flex items-center justify-between">
            <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>Back to Scorecards</Button>
            <Space>
              <Button onClick={() => setActiveStep('preview')}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Scorecard</Button>
            </Space>
          </div>
        ) : null}
        {isBuilderOpen ? builderView : listView}
      </>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
              <ClipboardList size={18} />
            </div>
            <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">Scorecards</h1>
          </div>
        </div>
        <Space>
          {isBuilderOpen ? (
            <>
              <Button onClick={() => setIsBuilderOpen(false)}>Back to Scorecards</Button>
              <Button onClick={() => setActiveStep('preview')}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Scorecard</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/interviews?s=scorecards')}>Command Center</Button>
              <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create Scorecard</Button>
            </>
          )}
        </Space>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {isBuilderOpen ? builderView : listView}
      </div>
    </div>
  )
}
