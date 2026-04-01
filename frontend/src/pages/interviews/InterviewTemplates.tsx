import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Empty, Input, InputNumber, Select, Space, Switch, Table, Tag, Typography, message } from 'antd'
import { ArrowLeft, Clock, Copy, Eye, LayoutGrid, Plus, Settings2, ShieldCheck, Workflow } from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'
import { getCategoryOptions, getInterviewTypeCategory, INTERVIEW_TYPE_CATEGORIES, type InterviewTypeCategory } from '@/utils/interviewTypeUx'

const { Text } = Typography
const { TextArea } = Input

const TEMPLATE_STEPS = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'configuration', label: '2. Configuration', icon: LayoutGrid },
  { key: 'scorecard', label: '3. Scorecard', icon: ShieldCheck },
  { key: 'automation', label: '4. Automation', icon: Workflow },
  { key: 'preview', label: '5. Preview', icon: Eye },
] as const

const TEMPLATE_STEP_ORDER = TEMPLATE_STEPS.map((step) => step.key)

type TemplateStep = (typeof TEMPLATE_STEPS)[number]['key']

type TemplateDraft = {
  id: string | null
  name: string
  description: string
  interview_type: string
  category: InterviewTypeCategory
  duration_minutes: number
  is_active: boolean
  setup: {
    reusable_template: boolean
  }
  configuration: {
    ai_config: string
    interviewer_config: string
    assessment_config: string
    screening_config: string
    advanced_config: string
  }
  scorecard: {
    scorecard_template_id: string
  }
  automation: {
    trigger_mode: 'auto_trigger' | 'manual_trigger'
    routing: string
    scheduling_enabled: boolean
  }
}

function createDraft(): TemplateDraft {
  return {
    id: null,
    name: '',
    description: '',
    interview_type: 'ai_screening',
    category: 'AI',
    duration_minutes: 30,
    is_active: true,
    setup: {
      reusable_template: true,
    },
    configuration: {
      ai_config: '',
      interviewer_config: '',
      assessment_config: '',
      screening_config: '',
      advanced_config: '',
    },
    scorecard: {
      scorecard_template_id: '',
    },
    automation: {
      trigger_mode: 'manual_trigger',
      routing: 'manual_review',
      scheduling_enabled: true,
    },
  }
}

function parseTemplate(record: any): TemplateDraft {
  const meta = record?.metadata?.unified_template || {}
  return {
    id: record.id,
    name: record.name || '',
    description: record.description || '',
    interview_type: record.interview_type || 'ai_screening',
    category: meta.category || getInterviewTypeCategory(record.interview_type || 'ai_screening'),
    duration_minutes: record.duration_minutes || 30,
    is_active: record.is_active ?? true,
    setup: {
      reusable_template: meta.setup?.reusable_template ?? true,
    },
    configuration: {
      ai_config: meta.configuration?.ai_config || '',
      interviewer_config: meta.configuration?.interviewer_config || '',
      assessment_config: meta.configuration?.assessment_config || '',
      screening_config: meta.configuration?.screening_config || '',
      advanced_config: meta.configuration?.advanced_config || '',
    },
    scorecard: {
      scorecard_template_id: meta.scorecard?.scorecard_template_id || '',
    },
    automation: {
      trigger_mode: meta.automation?.trigger_mode || 'manual_trigger',
      routing: meta.automation?.routing || 'manual_review',
      scheduling_enabled: meta.automation?.scheduling_enabled ?? true,
    },
  }
}

function buildPayload(draft: TemplateDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: draft.interview_type,
    duration_minutes: draft.duration_minutes,
    instructions: draft.category === 'AI'
      ? draft.configuration.ai_config
      : draft.category === 'Technical'
        ? draft.configuration.interviewer_config
        : draft.category === 'Assessment'
          ? draft.configuration.assessment_config
          : draft.category === 'Screening'
            ? draft.configuration.screening_config
            : draft.configuration.advanced_config,
    scoring_type: draft.scorecard.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      unified_template: {
        category: draft.category,
        setup: draft.setup,
        configuration: draft.configuration,
        scorecard: draft.scorecard,
        automation: draft.automation,
        integrations: {
          flow_engine: true,
          scorecard_engine: true,
          ai_engine: true,
          scheduling_engine: draft.automation.scheduling_enabled,
        },
      },
    },
  }
}

export default function InterviewTemplates() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null)
  const [draft, setDraft] = useState<TemplateDraft>(createDraft())
  const [activeStep, setActiveStep] = useState<TemplateStep>('setup')
  const [selectedCategory, setSelectedCategory] = useState<InterviewTypeCategory>('AI')
  const [saving, setSaving] = useState(false)

  const { data, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const templates = (data as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const filteredTemplates = templates.filter((template: any) =>
    template.name.toLowerCase().includes(search.toLowerCase()),
  )
  const filteredTypeOptions = getCategoryOptions(selectedCategory)
  const activeStepIndex = TEMPLATE_STEP_ORDER.indexOf(activeStep)
  const selectedScorecard = scorecards.find((scorecard: any) => scorecard.id === draft.scorecard.scorecard_template_id) ?? null
  const usageCount = useMemo(() => {
    if (!selectedRecord?.id) return 0
    return flows.filter((flow: any) =>
      (flow?.stages || []).some((stage: any) => stage?.template_id === selectedRecord.id),
    ).length
  }, [flows, selectedRecord])

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.interview_type),
    configuration: Boolean(
      draft.category === 'AI'
        ? draft.configuration.ai_config.trim()
        : draft.category === 'Technical'
          ? draft.configuration.interviewer_config.trim()
          : draft.category === 'Assessment'
            ? draft.configuration.assessment_config.trim()
            : draft.category === 'Screening'
              ? draft.configuration.screening_config.trim()
              : draft.configuration.advanced_config.trim(),
    ),
    scorecard: true,
    automation: Boolean(draft.automation.routing.trim()),
    preview: true,
  }

  const updateDraft = (updater: (current: TemplateDraft) => TemplateDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = () => {
    const next = createDraft()
    setSelectedRecord(null)
    setDraft(next)
    setSelectedCategory(next.category)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = (record: any, step: TemplateStep = 'setup') => {
    const next = parseTemplate(record)
    setSelectedRecord(record)
    setDraft(next)
    setSelectedCategory(next.category)
    setActiveStep(step)
    setIsBuilderOpen(true)
  }

  const duplicateTemplate = async (record: any) => {
    try {
      const next = parseTemplate(record)
      await interviewsApi.createTemplate(buildPayload({ ...next, id: null, name: `${next.name} Copy`, is_active: false }, record))
      message.success('Template duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to duplicate template')
    }
  }

  const archiveTemplate = async (record: any) => {
    try {
      await interviewsApi.updateTemplate(record.id, { ...record, is_active: false })
      message.success('Template archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to archive template')
    }
  }

  const saveDraft = async () => {
    setSaving(true)
    try {
      const payload = buildPayload(draft, selectedRecord)
      if (selectedRecord?.id) {
        await interviewsApi.updateTemplate(selectedRecord.id, payload)
        message.success('Template updated')
      } else {
        await interviewsApi.createTemplate(payload)
        message.success('Template created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setIsBuilderOpen(false)
      setSelectedRecord(null)
      setDraft(createDraft())
      setActiveStep('setup')
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save template')
    } finally {
      setSaving(false)
    }
  }

  const goToPrevStep = () => {
    if (activeStepIndex > 0) setActiveStep(TEMPLATE_STEP_ORDER[activeStepIndex - 1])
  }

  const goToNextStep = () => {
    if (activeStepIndex < TEMPLATE_STEP_ORDER.length - 1) setActiveStep(TEMPLATE_STEP_ORDER[activeStepIndex + 1])
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
      title: 'Template Name',
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
      title: 'Category',
      key: 'category',
      render: (_, record: any) => <Tag>{record?.metadata?.unified_template?.category || getInterviewTypeCategory(record.interview_type)}</Tag>,
    },
    {
      title: 'Scorecard',
      key: 'scorecard',
      render: (_, record: any) => {
        const linked = record?.metadata?.unified_template?.scorecard?.scorecard_template_id
        return <Text className="text-xs text-slate-500">{linked ? 'Linked' : 'Not linked'}</Text>
      },
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => <Tag color={value ? 'success' : 'default'}>{value ? 'Active' : 'Archived'}</Tag>,
    },
    {
      title: 'Usage',
      key: 'usage',
      render: (_, record: any) =>
        flows.filter((flow: any) => (flow?.stages || []).some((stage: any) => stage?.template_id === record.id)).length,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: any) => (
        <Space wrap>
          <Button size="small" onClick={() => openEdit(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateTemplate(record)} icon={<Copy size={14} />}>Duplicate</Button>
          <Button size="small" onClick={() => openEdit(record, 'preview')} icon={<Eye size={14} />}>Preview</Button>
          <Button size="small" danger onClick={() => archiveTemplate(record)}>Archive</Button>
        </Space>
      ),
    },
  ]

  const listView = (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <LayoutGrid size={18} />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">Interview Templates</h2>
            <p className="mt-1 text-xs text-slate-500">Reusable templates across AI, human, technical, assessment, screening, and advanced interview types.</p>
          </div>
        </div>
        <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create Template</Button>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white shadow-soft-md overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/30 flex items-center justify-between">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 transition-all max-w-sm flex-1">
            <Input
              placeholder="Search templates..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="border-none shadow-none px-0"
            />
          </div>
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{filteredTemplates.length} Templates</Text>
        </div>
        <div className="p-4">
          <Table
            columns={columns}
            dataSource={filteredTemplates}
            rowKey="id"
            loading={isLoading}
            pagination={{ pageSize: 12, hideOnSinglePage: true }}
            className="enterprise-table"
            locale={{
              emptyText: (
                <Empty description="No templates yet" image={Empty.PRESENTED_IMAGE_SIMPLE}>
                  <Button type="primary" onClick={openCreate}>Create Template</Button>
                </Empty>
              ),
            }}
          />
        </div>
      </div>
    </div>
  )

  const configurationField =
    draft.category === 'AI'
      ? (
        <BuilderField label="AI Config" helper="Reusable AI interview configuration shell.">
          <TextArea rows={6} value={draft.configuration.ai_config} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, ai_config: event.target.value } }))} />
        </BuilderField>
      )
      : draft.category === 'Technical'
        ? (
          <BuilderField label="Interviewer Config" helper="Interviewer guidance, panel setup, and technical execution notes.">
            <TextArea rows={6} value={draft.configuration.interviewer_config} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, interviewer_config: event.target.value } }))} />
          </BuilderField>
        )
        : draft.category === 'Assessment'
          ? (
            <BuilderField label="Assessment Config" helper="Assessment shell, attempt logic, and candidate instructions.">
              <TextArea rows={6} value={draft.configuration.assessment_config} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, assessment_config: event.target.value } }))} />
            </BuilderField>
          )
          : draft.category === 'Screening'
            ? (
              <BuilderField label="Screening Config" helper="Qualification gates and screening execution notes.">
                <TextArea rows={6} value={draft.configuration.screening_config} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, screening_config: event.target.value } }))} />
              </BuilderField>
            )
            : (
              <BuilderField label="Advanced Config" helper="Specialized workflow or simulation setup.">
                <TextArea rows={6} value={draft.configuration.advanced_config} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, advanced_config: event.target.value } }))} />
              </BuilderField>
            )

  const builderView = (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-3">
        <div className="sticky top-6 space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Builder Steps</h3>
            <div className="mt-4 space-y-2">
              {TEMPLATE_STEPS.map((step) => {
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
        </div>
      </div>

      <div className="col-span-12 lg:col-span-6 space-y-6">
        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Current Step</p>
            <p className="mt-1 text-sm font-bold text-slate-900">{TEMPLATE_STEPS[activeStepIndex]?.label}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
            <Button onClick={goToNextStep} disabled={activeStepIndex === TEMPLATE_STEP_ORDER.length - 1}>Next</Button>
          </div>
        </div>

        <div className={cn(activeStep === 'setup' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <Settings2 size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">1. Setup</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <BuilderField label="Template Name">
                <Input value={draft.name} onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
              </BuilderField>
              <BuilderField label="Duration">
                <InputNumber min={5} max={180} className="w-full" addonAfter="min" value={draft.duration_minutes} onChange={(value) => updateDraft((current) => ({ ...current, duration_minutes: Number(value || 30) }))} />
              </BuilderField>
              <div className="md:col-span-2">
                <BuilderField label="Description">
                  <TextArea rows={3} value={draft.description} onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
                </BuilderField>
              </div>
              <BuilderField label="Category">
                <Select value={selectedCategory} options={INTERVIEW_TYPE_CATEGORIES.map((category) => ({ value: category, label: category }))} onChange={(value) => setSelectedCategory(value)} />
              </BuilderField>
              <BuilderField label="Interview Type">
                <Select
                  value={draft.interview_type}
                  options={filteredTypeOptions.map((option) => ({ value: option.value, label: option.label }))}
                  onChange={(value) => updateDraft((current) => ({ ...current, interview_type: value, category: getInterviewTypeCategory(value) }))}
                />
              </BuilderField>
              <div className="rounded-2xl border border-slate-200 p-4 md:col-span-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Reusable template</span>
                  <Switch checked={draft.setup.reusable_template} onChange={(checked) => updateDraft((current) => ({ ...current, setup: { ...current.setup, reusable_template: checked } }))} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className={cn(activeStep === 'configuration' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <LayoutGrid size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">2. Configuration</h2>
            </div>
            {configurationField}
          </div>
        </div>

        <div className={cn(activeStep === 'scorecard' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">3. Scorecard</h2>
            </div>
            <BuilderField label="Scorecard Template" helper="Attach a reusable scorecard template.">
              <Select allowClear value={draft.scorecard.scorecard_template_id || undefined} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} onChange={(value) => updateDraft((current) => ({ ...current, scorecard: { scorecard_template_id: value || '' } }))} />
            </BuilderField>
          </div>
        </div>

        <div className={cn(activeStep === 'automation' ? 'block' : 'hidden')}>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <Workflow size={16} className="text-indigo-600" />
              <h2 className="text-sm font-black uppercase tracking-widest text-slate-900">4. Automation</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <BuilderField label="Trigger Mode">
                <Select value={draft.automation.trigger_mode} options={[{ value: 'auto_trigger', label: 'Auto trigger' }, { value: 'manual_trigger', label: 'Manual trigger' }]} onChange={(value) => updateDraft((current) => ({ ...current, automation: { ...current.automation, trigger_mode: value } }))} />
              </BuilderField>
              <BuilderField label="Routing">
                <Input value={draft.automation.routing} onChange={(event) => updateDraft((current) => ({ ...current, automation: { ...current.automation, routing: event.target.value } }))} />
              </BuilderField>
              <div className="rounded-2xl border border-slate-200 p-4 md:col-span-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">Scheduling enabled</span>
                  <Switch checked={draft.automation.scheduling_enabled} onChange={(checked) => updateDraft((current) => ({ ...current, automation: { ...current.automation, scheduling_enabled: checked } }))} />
                </div>
              </div>
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
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Template Summary</p>
              <h3 className="mt-3 text-xl font-black">{draft.name || 'Untitled Template'}</h3>
              <p className="mt-2 text-sm text-slate-300">{draft.description || 'Template description appears here.'}</p>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Interview Type</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.interview_type.replace(/_/g, ' ')}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{selectedScorecard?.name || 'No scorecard linked'}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Automation</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{draft.automation.trigger_mode.replace(/_/g, ' ')} · {draft.automation.routing}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{usageCount} flow links</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <Button onClick={goToPrevStep} disabled={activeStepIndex === 0}>Back</Button>
          <div className="flex items-center gap-2">
            {activeStepIndex < TEMPLATE_STEP_ORDER.length - 1 ? (
              <Button type="primary" onClick={goToNextStep}>Next Step</Button>
            ) : (
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Template</Button>
            )}
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-3 space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Template Summary</h3>
          <div className="mt-4 space-y-3">
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Category</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{draft.category}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{draft.duration_minutes} min</p>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</p>
              <p className="mt-2 text-sm font-bold text-slate-900">{selectedScorecard ? 'Mapped' : 'Unmapped'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
              <LayoutGrid size={18} />
            </div>
            <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">Interview Templates</h1>
          </div>
        </div>
        <Space>
          {isBuilderOpen ? (
            <>
              <Button icon={<ArrowLeft size={14} />} onClick={() => setIsBuilderOpen(false)}>Back to Templates</Button>
              <Button onClick={() => setActiveStep('preview')}>Preview</Button>
              <Button type="primary" loading={saving} onClick={saveDraft}>Save Template</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/interviews')}>Command Center</Button>
              <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create Template</Button>
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
