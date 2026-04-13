import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Button, Empty, Input, InputNumber, Select, Switch, Table, Tag, Typography, message } from 'antd'
import { ArrowLeft, Bell, CheckCircle2, Clock3, Copy, Eye, Play, Plus, Settings2, SlidersHorizontal, Workflow, Zap } from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { automationApi } from '@/api/automation'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography

const AUTOMATION_STEPS = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'conditions', label: '2. Conditions', icon: SlidersHorizontal },
  { key: 'actions', label: '3. Actions', icon: Workflow },
  { key: 'preview', label: '4. Preview', icon: Eye },
] as const

const AUTOMATION_STEP_ORDER = AUTOMATION_STEPS.map((step) => step.key)

type AutomationStep = (typeof AUTOMATION_STEPS)[number]['key']

type ConditionRow = {
  id: string
  field: string
  operator: string
  value: string | number
}

type ActionRow = {
  id: string
  type: string
  target_stage: string
  template_id: string
  interviewer: string
  notification_template: string
}

type AutomationDraft = {
  id: string | null
  name: string
  description: string
  automation_type: string
  trigger_event: string
  is_active: boolean
  conditions: ConditionRow[]
  actions: ActionRow[]
}

type InterviewAutomationProps = {
  embedded?: boolean
}

const AUTOMATION_TYPE_OPTIONS = [
  { value: 'auto_scheduling', label: 'Auto Scheduling' },
  { value: 'auto_routing', label: 'Auto Routing' },
  { value: 'auto_decision', label: 'Auto Decision' },
  { value: 'auto_stage_movement', label: 'Auto Stage Movement' },
  { value: 'auto_interview_trigger', label: 'Auto Interview Trigger' },
  { value: 'auto_notification', label: 'Auto Notification' },
]

const TRIGGER_OPTIONS = [
  { value: 'prequalification.completed', label: 'Prequalification Completed' },
  { value: 'interview.completed', label: 'Interview Completed' },
  { value: 'score.submitted', label: 'Score Submitted' },
  { value: 'decision.made', label: 'Decision Made' },
  { value: 'candidate.status_changed', label: 'Candidate Status Change' },
]

const CONDITION_FIELD_OPTIONS = [
  { value: 'score', label: 'Score Threshold' },
  { value: 'interview_type', label: 'Interview Type' },
  { value: 'decision', label: 'Decision' },
  { value: 'stage', label: 'Stage' },
  { value: 'candidate_status', label: 'Candidate Status' },
]

const OPERATOR_OPTIONS = [
  { value: 'eq', label: '=' },
  { value: 'neq', label: '!=' },
  { value: 'gt', label: '>' },
  { value: 'gte', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'lte', label: '<=' },
  { value: 'contains', label: 'Contains' },
]

const ACTION_OPTIONS = [
  { value: 'move_to_next_stage', label: 'Move to Next Stage' },
  { value: 'schedule_next_interview', label: 'Schedule Next Interview' },
  { value: 'assign_interviewer', label: 'Assign Interviewer' },
  { value: 'send_notification', label: 'Send Notification' },
  { value: 'trigger_ai_interview', label: 'Trigger AI Interview' },
  { value: 'reject_candidate', label: 'Reject Candidate' },
  { value: 'mark_hire_ready', label: 'Mark Hire Ready' },
]

const TEST_ENTITY_OPTIONS = [
  { value: 'interview', label: 'Interview' },
  { value: 'application', label: 'Application' },
  { value: 'candidate', label: 'Candidate' },
]

function makeId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function createCondition(): ConditionRow {
  return { id: makeId(), field: 'score', operator: 'gte', value: 75 }
}

function createAction(type = 'move_to_next_stage'): ActionRow {
  return {
    id: makeId(),
    type,
    target_stage: '',
    template_id: '',
    interviewer: '',
    notification_template: '',
  }
}

function createDraft(): AutomationDraft {
  return {
    id: null,
    name: '',
    description: '',
    automation_type: 'auto_routing',
    trigger_event: 'interview.completed',
    is_active: true,
    conditions: [createCondition()],
    actions: [createAction()],
  }
}

function parseRule(rule: any): AutomationDraft {
  const conditions = Array.isArray(rule?.conditions?.all) ? rule.conditions.all : []
  const actions = Array.isArray(rule?.actions) ? rule.actions : []
  return {
    id: rule?.id || null,
    name: rule?.name || '',
    description: rule?.description || '',
    automation_type: rule?.metadata?.automation_type || 'auto_routing',
    trigger_event: rule?.trigger_event || 'interview.completed',
    is_active: rule?.is_active ?? true,
    conditions: conditions.length
      ? conditions.map((condition: any) => ({
          id: makeId(),
          field: condition?.field || 'score',
          operator: condition?.operator || 'gte',
          value: condition?.value ?? '',
        }))
      : [createCondition()],
    actions: actions.length
      ? actions.map((action: any) => ({
          id: makeId(),
          type: action?.type || 'move_to_next_stage',
          target_stage: action?.stage || action?.target_stage || '',
          template_id: action?.template || action?.template_id || '',
          interviewer: action?.interviewer || '',
          notification_template: action?.notification_template || action?.template || '',
        }))
      : [createAction()],
  }
}

function buildPayload(draft: AutomationDraft) {
  return {
    name: draft.name,
    description: draft.description,
    trigger_event: draft.trigger_event,
    is_active: draft.is_active,
    conditions: {
      all: draft.conditions.map((condition) => ({
        field: condition.field,
        operator: condition.operator,
        value: condition.value,
      })),
    },
    actions: draft.actions.map((action) => ({
      type: action.type,
      stage: action.target_stage || undefined,
      template: action.template_id || action.notification_template || undefined,
      interviewer: action.interviewer || undefined,
    })),
    metadata: {
      automation_type: draft.automation_type,
      module_id: 'ICC-AUTOMATION-ENGINE-01',
    },
  }
}

function StepShell({
  active,
  children,
}: {
  active: boolean
  children: ReactNode
}) {
  return <div className={cn(active ? 'block' : 'hidden')}>{children}</div>
}

export default function InterviewAutomation({ embedded = false }: InterviewAutomationProps) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedRule, setSelectedRule] = useState<any | null>(null)
  const [draft, setDraft] = useState<AutomationDraft>(createDraft())
  const [activeStep, setActiveStep] = useState<AutomationStep>('setup')
  const [saving, setSaving] = useState(false)
  const [testTrigger, setTestTrigger] = useState('interview.completed')
  const [testEntityType, setTestEntityType] = useState('interview')
  const [testContext, setTestContext] = useState('{"score":82,"stage":"ai_screening","decision":"recommend"}')
  const [executing, setExecuting] = useState(false)

  const { data, isLoading } = useApiQuery(['automation-rules'], () => automationApi.listRules())
  const { data: logsData } = useApiQuery(['automation-logs'], () => automationApi.listLogs({ limit: 8 }))

  const rules = (data as any)?.data?.rules ?? (data as any)?.rules ?? []
  const logs = (logsData as any)?.data?.logs ?? (logsData as any)?.logs ?? []
  const activeStepIndex = AUTOMATION_STEP_ORDER.indexOf(activeStep)

  const filteredRules = useMemo(() => {
    return rules.filter((rule: any) => {
      const hay = `${rule?.name || ''} ${rule?.trigger_event || ''} ${rule?.metadata?.automation_type || ''}`.toLowerCase()
      return hay.includes(search.toLowerCase())
    })
  }, [rules, search])

  const usageSummary = useMemo(() => {
    return {
      active: rules.filter((rule: any) => rule?.is_active).length,
      disabled: rules.filter((rule: any) => !rule?.is_active).length,
      autoDecision: rules.filter((rule: any) => rule?.metadata?.automation_type === 'auto_decision').length,
      executed: rules.reduce((sum: number, rule: any) => sum + Number(rule?.execution_count || 0), 0),
    }
  }, [rules])

  const stepCompletion = {
    setup: Boolean(draft.name.trim() && draft.trigger_event && draft.automation_type),
    conditions: draft.conditions.length > 0 && draft.conditions.every((condition) => String(condition.field).trim() && String(condition.operator).trim() && String(condition.value).trim()),
    actions: draft.actions.length > 0 && draft.actions.every((action) => String(action.type).trim()),
    preview: true,
  }

  const updateDraft = (updater: (current: AutomationDraft) => AutomationDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = () => {
    setSelectedRule(null)
    setDraft(createDraft())
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const openEdit = (rule: any, step: AutomationStep = 'setup') => {
    setSelectedRule(rule)
    setDraft(parseRule(rule))
    setActiveStep(step)
    setIsBuilderOpen(true)
  }

  const duplicateRule = async (rule: any) => {
    try {
      const next = parseRule(rule)
      await automationApi.createRule(buildPayload({ ...next, id: null, name: `${next.name} Copy`, is_active: false }))
      message.success('Automation rule duplicated')
      await queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to duplicate rule')
    }
  }

  const toggleRule = async (rule: any, isActive: boolean) => {
    try {
      await automationApi.updateRule(rule.id, { ...rule, is_active: isActive })
      message.success(isActive ? 'Rule enabled' : 'Rule disabled')
      await queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to update rule state')
    }
  }

  const archiveRule = async (rule: any) => {
    try {
      await automationApi.updateRule(rule.id, { ...rule, is_active: false })
      message.success('Rule archived')
      await queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to archive rule')
    }
  }

  const saveDraft = async () => {
    setSaving(true)
    try {
      const payload = buildPayload(draft)
      if (selectedRule?.id) {
        await automationApi.updateRule(selectedRule.id, payload)
        message.success('Automation rule updated')
      } else {
        await automationApi.createRule(payload)
        message.success('Automation rule created')
      }
      await queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
      await queryClient.invalidateQueries({ queryKey: ['automation-logs'] })
      setIsBuilderOpen(false)
      setSelectedRule(null)
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to save automation rule')
    } finally {
      setSaving(false)
    }
  }

  const runTrigger = async () => {
    setExecuting(true)
    try {
      const context = testContext.trim() ? JSON.parse(testContext) : {}
      const response = await automationApi.trigger({
        trigger_event: testTrigger,
        entity_type: testEntityType,
        context,
      })
      const result = response.data?.data?.result
      message.success(`Triggered ${result?.executed_rules || 0} rule(s)`)
      await queryClient.invalidateQueries({ queryKey: ['automation-logs'] })
      await queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Failed to trigger automation')
    } finally {
      setExecuting(false)
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Rule Name',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, rule: any) => (
        <div>
          <p className="m-0 font-black text-slate-900">{value}</p>
          <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{rule?.metadata?.automation_type?.replace(/_/g, ' ') || 'automation'}</Text>
        </div>
      ),
    },
    {
      title: 'Trigger',
      dataIndex: 'trigger_event',
      key: 'trigger_event',
      render: (value: string) => <Tag color="blue">{value}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, rule: any) => <Text className="font-bold text-slate-700">{Array.isArray(rule?.actions) ? rule.actions.length : 0}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => <Tag color={value ? 'green' : 'default'}>{value ? 'Enabled' : 'Disabled'}</Tag>,
    },
    {
      title: 'Executed',
      dataIndex: 'execution_count',
      key: 'execution_count',
      render: (value: number) => value || 0,
    },
    {
      title: 'Actions',
      key: 'operations',
      render: (_, rule: any) => (
        <div className="flex items-center gap-2">
          <Button size="small" onClick={() => openEdit(rule)}>Edit</Button>
          <Button size="small" onClick={() => duplicateRule(rule)}>Duplicate</Button>
          <Button size="small" onClick={() => toggleRule(rule, !rule?.is_active)}>{rule?.is_active ? 'Disable' : 'Enable'}</Button>
          <Button size="small" danger onClick={() => archiveRule(rule)}>Archive</Button>
        </div>
      ),
    },
  ]

  const containerClass = embedded ? 'h-full overflow-y-auto p-6 space-y-5' : 'min-h-screen bg-[#F8FAFC] p-6 space-y-5'

  if (!isBuilderOpen) {
    return (
      <div className={containerClass}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <Text className="block text-[10px] font-black uppercase tracking-[0.24em] text-indigo-500">ICC-AUTOMATION-ENGINE-01</Text>
            <h2 className="m-0 mt-1 text-2xl font-black text-slate-900">Interview Automation</h2>
            <Text className="text-slate-500">Enterprise automation rules for scheduling, routing, decisions, stage movement, triggers, and notifications.</Text>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={openCreate}>Create Rule</Button>
        </div>

        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          {[
            { label: 'Active Rules', value: usageSummary.active, icon: Zap, color: 'text-indigo-600', bg: 'bg-indigo-50' },
            { label: 'Disabled Rules', value: usageSummary.disabled, icon: Clock3, color: 'text-slate-600', bg: 'bg-slate-100' },
            { label: 'Auto Decision', value: usageSummary.autoDecision, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Executions', value: usageSummary.executed, icon: Workflow, color: 'text-blue-600', bg: 'bg-blue-50' },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-soft-sm">
              <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center', item.bg, item.color)}>
                <item.icon size={18} />
              </div>
              <Text className="mt-3 block text-[10px] font-black uppercase tracking-widest text-slate-400">{item.label}</Text>
              <Text className="block text-2xl font-black text-slate-900 leading-none">{item.value}</Text>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.5fr)_420px] gap-5 items-start">
          <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Rule List</Text>
                <Text className="text-slate-500">Create, edit, duplicate, archive, and enable interview automation rules.</Text>
              </div>
              <Input
                placeholder="Search rules..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="w-64"
              />
            </div>

            <Table
              rowKey="id"
              loading={isLoading}
              columns={columns}
              dataSource={filteredRules}
              pagination={{ pageSize: 8, hideOnSinglePage: true }}
            />
          </div>

          <div className="space-y-5">
            <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div>
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Trigger Runner</Text>
                  <Text className="text-slate-500">Validate rule execution against live automation APIs.</Text>
                </div>
                <Button icon={<Play size={14} />} loading={executing} onClick={runTrigger}>Run</Button>
              </div>
              <div className="space-y-3">
                <Select value={testTrigger} onChange={setTestTrigger} options={TRIGGER_OPTIONS} className="w-full" />
                <Select value={testEntityType} onChange={setTestEntityType} options={TEST_ENTITY_OPTIONS} className="w-full" />
                <Input.TextArea rows={6} value={testContext} onChange={(event) => setTestContext(event.target.value)} placeholder='{"score":82,"stage":"ai_screening"}' />
              </div>
            </div>

            <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">Recent Automation Activity</Text>
              <div className="space-y-3">
                {logs.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No automation activity yet" />
                ) : logs.map((log: any, index: number) => (
                  <div key={log?.id || index} className="rounded-xl border border-slate-100 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <Text className="block font-bold text-slate-800">{log?.rule_name || log?.trigger_event || 'Automation Event'}</Text>
                        <Text className="text-[11px] text-slate-500">{log?.status || 'executed'} · {log?.trigger_event || 'rule_execution'}</Text>
                      </div>
                      <Tag color={(log?.status || '').toLowerCase().includes('fail') ? 'red' : 'green'}>{log?.status || 'executed'}</Tag>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={containerClass}>
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => {
            setIsBuilderOpen(false)
            setSelectedRule(null)
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
        >
          <ArrowLeft size={14} />
          Back to Automation
        </button>
        <div className="flex items-center gap-2">
          <Button onClick={runTrigger} icon={<Play size={14} />} loading={executing}>Test Trigger</Button>
          <Button type="primary" onClick={saveDraft} loading={saving}>Save Rule</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[240px_minmax(0,1fr)_340px] gap-5 items-start">
        <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-soft-sm sticky top-0">
          <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3">Automation Steps</Text>
          <div className="space-y-2">
            {AUTOMATION_STEPS.map((step, index) => {
              const completed = stepCompletion[step.key]
              const active = activeStep === step.key
              return (
                <button
                  key={step.key}
                  onClick={() => setActiveStep(step.key)}
                  className={cn(
                    'w-full rounded-xl border px-3 py-3 text-left transition',
                    active ? 'border-indigo-200 bg-indigo-50' : 'border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50',
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'h-9 w-9 rounded-xl flex items-center justify-center',
                      active ? 'bg-indigo-600 text-white' : completed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400',
                    )}>
                      <step.icon size={16} />
                    </div>
                    <div className="min-w-0">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step {index + 1}</Text>
                      <Text className="block font-bold text-slate-800">{step.label.replace(/^\d+\.\s*/, '')}</Text>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-soft-sm">
          <StepShell active={activeStep === 'setup'}>
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 1</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Rule Setup</h3>
                <Text className="text-slate-500">Define the automation type, trigger event, and baseline activation state.</Text>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Rule Name</Text>
                  <Input value={draft.name} onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} placeholder="Advance passed AI screening candidates" />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Automation Type</Text>
                  <Select value={draft.automation_type} onChange={(value) => updateDraft((current) => ({ ...current, automation_type: value }))} options={AUTOMATION_TYPE_OPTIONS} className="w-full" />
                </div>
                <div className="md:col-span-2">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Trigger Event</Text>
                  <Select value={draft.trigger_event} onChange={(value) => updateDraft((current) => ({ ...current, trigger_event: value }))} options={TRIGGER_OPTIONS} className="w-full" />
                </div>
                <div className="md:col-span-2">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Description</Text>
                  <Input.TextArea rows={4} value={draft.description} onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} placeholder="Describe when the rule should fire and what workflow outcome it automates." />
                </div>
                <div className="md:col-span-2 flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                  <div>
                    <Text className="block font-bold text-slate-800">Enable Rule</Text>
                    <Text className="text-slate-500">Disabled rules remain available for review but do not execute.</Text>
                  </div>
                  <Switch checked={draft.is_active} onChange={(checked) => updateDraft((current) => ({ ...current, is_active: checked }))} />
                </div>
              </div>
            </div>
          </StepShell>

          <StepShell active={activeStep === 'conditions'}>
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 2</Text>
                  <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Conditions</h3>
                  <Text className="text-slate-500">Define score, interview type, decision, stage, or candidate status conditions.</Text>
                </div>
                <Button icon={<Plus size={14} />} onClick={() => updateDraft((current) => ({ ...current, conditions: [...current.conditions, createCondition()] }))}>Add Condition</Button>
              </div>

              <div className="space-y-4">
                {draft.conditions.map((condition) => (
                  <div key={condition.id} className="rounded-2xl border border-slate-100 p-4">
                    <div className="grid grid-cols-1 md:grid-cols-[1.2fr_0.8fr_1fr_auto] gap-3 items-end">
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Condition Field</Text>
                        <Select
                          value={condition.field}
                          options={CONDITION_FIELD_OPTIONS}
                          onChange={(value) => updateDraft((current) => ({
                            ...current,
                            conditions: current.conditions.map((item) => item.id === condition.id ? { ...item, field: value } : item),
                          }))}
                          className="w-full"
                        />
                      </div>
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Operator</Text>
                        <Select
                          value={condition.operator}
                          options={OPERATOR_OPTIONS}
                          onChange={(value) => updateDraft((current) => ({
                            ...current,
                            conditions: current.conditions.map((item) => item.id === condition.id ? { ...item, operator: value } : item),
                          }))}
                          className="w-full"
                        />
                      </div>
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Value</Text>
                        {condition.field === 'score' ? (
                          <InputNumber
                            min={0}
                            max={100}
                            className="w-full"
                            value={Number(condition.value || 0)}
                            onChange={(value) => updateDraft((current) => ({
                              ...current,
                              conditions: current.conditions.map((item) => item.id === condition.id ? { ...item, value: Number(value || 0) } : item),
                            }))}
                          />
                        ) : (
                          <Input
                            value={String(condition.value ?? '')}
                            onChange={(event) => updateDraft((current) => ({
                              ...current,
                              conditions: current.conditions.map((item) => item.id === condition.id ? { ...item, value: event.target.value } : item),
                            }))}
                            placeholder="Enter rule value"
                          />
                        )}
                      </div>
                      <Button danger onClick={() => updateDraft((current) => ({ ...current, conditions: current.conditions.filter((item) => item.id !== condition.id) || [createCondition()] }))}>Remove</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </StepShell>

          <StepShell active={activeStep === 'actions'}>
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 3</Text>
                  <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Actions</h3>
                  <Text className="text-slate-500">Define what should happen when the automation rule matches.</Text>
                </div>
                <Button icon={<Plus size={14} />} onClick={() => updateDraft((current) => ({ ...current, actions: [...current.actions, createAction()] }))}>Add Action</Button>
              </div>

              <div className="space-y-4">
                {draft.actions.map((action) => (
                  <div key={action.id} className="rounded-2xl border border-slate-100 p-4 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-[1.3fr_auto] gap-3 items-end">
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Action Type</Text>
                        <Select
                          value={action.type}
                          options={ACTION_OPTIONS}
                          onChange={(value) => updateDraft((current) => ({
                            ...current,
                            actions: current.actions.map((item) => item.id === action.id ? { ...item, type: value } : item),
                          }))}
                          className="w-full"
                        />
                      </div>
                      <Button danger onClick={() => updateDraft((current) => ({ ...current, actions: current.actions.filter((item) => item.id !== action.id) || [createAction()] }))}>Remove</Button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Target Stage</Text>
                        <Input
                          value={action.target_stage}
                          onChange={(event) => updateDraft((current) => ({
                            ...current,
                            actions: current.actions.map((item) => item.id === action.id ? { ...item, target_stage: event.target.value } : item),
                          }))}
                          placeholder="technical_round / manual_review / shortlist"
                        />
                      </div>
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Template / Engine Reference</Text>
                        <Input
                          value={action.template_id}
                          onChange={(event) => updateDraft((current) => ({
                            ...current,
                            actions: current.actions.map((item) => item.id === action.id ? { ...item, template_id: event.target.value } : item),
                          }))}
                          placeholder="AI template or interview template id"
                        />
                      </div>
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Assign Interviewer</Text>
                        <Input
                          value={action.interviewer}
                          onChange={(event) => updateDraft((current) => ({
                            ...current,
                            actions: current.actions.map((item) => item.id === action.id ? { ...item, interviewer: event.target.value } : item),
                          }))}
                          placeholder="Recruiter or interviewer name"
                        />
                      </div>
                      <div>
                        <Text className="block mb-1 text-xs font-bold text-slate-600">Notification Template</Text>
                        <Input
                          value={action.notification_template}
                          onChange={(event) => updateDraft((current) => ({
                            ...current,
                            actions: current.actions.map((item) => item.id === action.id ? { ...item, notification_template: event.target.value } : item),
                          }))}
                          placeholder="candidate_invite / recruiter_alert"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </StepShell>

          <StepShell active={activeStep === 'preview'}>
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 4</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Preview</h3>
                <Text className="text-slate-500">Review trigger, conditions, actions, and execution behavior before saving.</Text>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-2xl border border-slate-100 p-5">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Rule Summary</Text>
                  <p className="mt-2 mb-0 text-lg font-black text-slate-900">{draft.name || 'Untitled automation rule'}</p>
                  <p className="mt-1 mb-0 text-sm text-slate-500">{draft.description || 'No description yet.'}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Tag color="blue">{draft.trigger_event}</Tag>
                    <Tag color="purple">{draft.automation_type.replace(/_/g, ' ')}</Tag>
                    <Tag color={draft.is_active ? 'green' : 'default'}>{draft.is_active ? 'Enabled' : 'Disabled'}</Tag>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-100 p-5">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Execution Outlook</Text>
                  <div className="mt-3 space-y-3">
                    <div className="rounded-xl bg-slate-50 p-3">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Conditions</Text>
                      <Text className="font-bold text-slate-800">{draft.conditions.length} condition{draft.conditions.length === 1 ? '' : 's'}</Text>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Actions</Text>
                      <Text className="font-bold text-slate-800">{draft.actions.length} action{draft.actions.length === 1 ? '' : 's'}</Text>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Integration Scope</Text>
                      <Text className="font-bold text-slate-800">Flows · Scheduling · Interviews · Decisions · Notifications</Text>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-100 p-5">
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">Rule Logic</Text>
                <div className="space-y-3">
                  {draft.conditions.map((condition, index) => (
                    <div key={condition.id} className="rounded-xl border border-slate-100 p-4">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Condition {index + 1}</Text>
                      <Text className="font-bold text-slate-800">{condition.field} {condition.operator} {String(condition.value)}</Text>
                    </div>
                  ))}
                  {draft.actions.map((action, index) => (
                    <div key={action.id} className="rounded-xl border border-slate-100 p-4">
                      <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Action {index + 1}</Text>
                      <Text className="font-bold text-slate-800">{action.type.replace(/_/g, ' ')}</Text>
                      <Text className="block text-sm text-slate-500">Stage: {action.target_stage || 'n/a'} · Template: {action.template_id || 'n/a'} · Notify: {action.notification_template || 'n/a'}</Text>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </StepShell>

          <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-5">
            <Button disabled={activeStepIndex === 0} onClick={() => setActiveStep(AUTOMATION_STEP_ORDER[Math.max(0, activeStepIndex - 1)])}>Back</Button>
            <div className="flex items-center gap-2">
              <Button onClick={saveDraft} loading={saving}>Save Draft</Button>
              <Button type="primary" disabled={activeStepIndex === AUTOMATION_STEP_ORDER.length - 1} onClick={() => setActiveStep(AUTOMATION_STEP_ORDER[Math.min(AUTOMATION_STEP_ORDER.length - 1, activeStepIndex + 1)])}>Next</Button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm sticky top-0 space-y-5">
          <div>
            <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Automation Summary</Text>
            <p className="mt-2 mb-0 text-lg font-black text-slate-900">{draft.name || 'Untitled Rule'}</p>
            <p className="mt-1 mb-0 text-sm text-slate-500">{draft.automation_type.replace(/_/g, ' ')} · {draft.trigger_event}</p>
          </div>

          <div className="rounded-xl bg-slate-950 p-4 text-white">
            <Text className="block text-[10px] font-black uppercase tracking-widest text-white/50">Decision Preview</Text>
            <p className="mt-3 mb-0 text-lg font-black">{draft.name || 'Automation Rule'}</p>
            <p className="mt-1 mb-0 text-sm text-white/70">{draft.conditions.length} conditions → {draft.actions.length} actions</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-white/5 p-3">
                <Text className="block text-[9px] font-black uppercase tracking-widest text-white/40">Trigger</Text>
                <Text className="font-bold text-white">{draft.trigger_event.replace(/\./g, ' ')}</Text>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <Text className="block text-[9px] font-black uppercase tracking-widest text-white/40">State</Text>
                <Text className="font-bold text-white">{draft.is_active ? 'enabled' : 'disabled'}</Text>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Supported Triggers</Text>
              <Text className="text-slate-700">Prequalification complete, interview complete, score submitted, decision made, candidate status change.</Text>
            </div>
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Action Coverage</Text>
              <Text className="text-slate-700">Routing, scheduling, interviewer assignment, notifications, AI trigger, rejection, hire-ready movement.</Text>
            </div>
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Execution Test</Text>
              <Button block icon={<Bell size={14} />} onClick={runTrigger} loading={executing}>Run Trigger Test</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
