import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout, Steps, Button, Card, Typography, Form, Input, Row, Col, Select,
  InputNumber, DatePicker, Checkbox, Tag, message, Spin, Divider, Badge, Alert, List, Radio, Progress, Modal, Switch, Tooltip,
} from 'antd'
import {
  ChevronRight, ChevronLeft, Save, Briefcase, Users, Workflow,
  BrainCircuit, ShieldCheck, CheckCircle2, LayoutGrid, Plus, Trash2, Sliders, Target, Box,
  DollarSign, FileText, Layers, MapPin, GripVertical, UserCheck, AlertTriangle, Clock,
  Lock, ArrowUpDown, Zap,
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi, jdTemplatesApi, jobLocationsApi, jobPrequalApi, stagesApi } from '@/api/jobs'
import { prequalificationApi } from '@/api/prequalification'
import { organisationApi } from '@/api/organisation'
import { agenciesApi } from '@/api/agencies'
import { interviewsApi } from '@/api/interviews'
import { cn } from '@/utils/cn'
import dayjs from 'dayjs'
import type { JobRequisition, InterviewPackage, JobStage } from '@/types'
import { useTranslation } from 'react-i18next'
import { CURRENCIES } from '@/utils/locale'

// ─── Approval Chain Builder ───────────────────────────────────────────────────

interface ApproverEntry {
  user_id: string
  name: string
  order: number
  is_fallback: boolean
}

function ApprovalChainBuilder({
  value = [],
  onChange,
  users,
}: {
  value?: ApproverEntry[]
  onChange?: (v: ApproverEntry[]) => void
  users: any[]
}) {
  const addApprover = () => {
    const next: ApproverEntry = { user_id: '', name: '', order: value.length + 1, is_fallback: false }
    onChange?.([...value, next])
  }

  const remove = (idx: number) => {
    const updated = value.filter((_, i) => i !== idx).map((a, i) => ({ ...a, order: i + 1 }))
    onChange?.(updated)
  }

  const setUser = (idx: number, userId: string) => {
    const user = users.find(u => u.id === userId)
    const updated = value.map((a, i) =>
      i === idx ? { ...a, user_id: userId, name: user?.full_name || user?.email || '' } : a
    )
    onChange?.(updated)
  }

  const toggleFallback = (idx: number, checked: boolean) => {
    const updated = value.map((a, i) => i === idx ? { ...a, is_fallback: checked } : a)
    onChange?.(updated)
  }

  const moveUp = (idx: number) => {
    if (idx === 0) return
    const arr = [...value]
    ;[arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]]
    onChange?.(arr.map((a, i) => ({ ...a, order: i + 1 })))
  }

  const moveDown = (idx: number) => {
    if (idx === value.length - 1) return
    const arr = [...value]
    ;[arr[idx], arr[idx + 1]] = [arr[idx + 1], arr[idx]]
    onChange?.(arr.map((a, i) => ({ ...a, order: i + 1 })))
  }

  return (
    <div className="space-y-2">
      {value.map((entry, idx) => (
        <div key={idx} className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200">
          <div className="flex flex-col gap-0.5">
            <button
              type="button"
              onClick={() => moveUp(idx)}
              className="text-slate-300 hover:text-slate-600 disabled:opacity-30"
              disabled={idx === 0}
            >
              <ArrowUpDown size={12} />
            </button>
          </div>

          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 text-xs font-black flex-shrink-0">
            {entry.is_fallback ? <UserCheck size={13} /> : idx + 1}
          </div>

          <Select
            className="flex-1"
            placeholder="Select approver"
            value={entry.user_id || undefined}
            onChange={(v) => setUser(idx, v)}
            options={users.map(u => ({ label: u.full_name || u.email, value: u.id }))}
            showSearch
            filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
          />

          <Tooltip title="Fallback approver (used if primary is unavailable)">
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <Switch
                size="small"
                checked={entry.is_fallback}
                onChange={(c) => toggleFallback(idx, c)}
              />
              <span className="text-[10px] font-bold uppercase tracking-wide whitespace-nowrap">Fallback</span>
            </div>
          </Tooltip>

          <button
            type="button"
            onClick={() => remove(idx)}
            className="text-slate-300 hover:text-rose-500 transition-colors flex-shrink-0"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={addApprover}
        className="w-full flex items-center justify-center gap-2 p-3 rounded-xl border border-dashed border-slate-300 text-slate-400 hover:border-indigo-400 hover:text-indigo-600 transition-all text-xs font-bold uppercase tracking-wide"
      >
        <Plus size={14} /> Add Approver
      </button>

      {value.length > 0 && (
        <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-xl border border-blue-100 mt-2">
          <AlertTriangle size={13} className="text-blue-500 flex-shrink-0 mt-0.5" />
          <p className="text-[11px] text-blue-600 font-medium m-0">
            Approvers will be notified in order. Job proceeds only after all required approvals are granted.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Location Multi-select ────────────────────────────────────────────────────

interface LocationEntry {
  id?: string          // JobLocation record id (for existing)
  location_id: string
  location_name: string
  is_primary: boolean
}

function LocationMultiSelect({
  value = [],
  onChange,
  locationOptions,
}: {
  value?: LocationEntry[]
  onChange?: (v: LocationEntry[]) => void
  locationOptions: any[]
}) {
  const addLocation = (locId: string) => {
    if (value.find(l => l.location_id === locId)) return
    const loc = locationOptions.find(l => l.id === locId)
    const isPrimary = value.length === 0
    onChange?.([...value, { location_id: locId, location_name: loc?.name || '', is_primary: isPrimary }])
  }

  const remove = (locId: string) => {
    const filtered = value.filter(l => l.location_id !== locId)
    // Ensure at least one is primary
    if (filtered.length > 0 && !filtered.some(l => l.is_primary)) {
      filtered[0].is_primary = true
    }
    onChange?.(filtered)
  }

  const setPrimary = (locId: string) => {
    onChange?.(value.map(l => ({ ...l, is_primary: l.location_id === locId })))
  }

  const usedIds = value.map(l => l.location_id)
  const availableOptions = locationOptions.filter(l => !usedIds.includes(l.id))

  return (
    <div className="space-y-2">
      {value.map((entry) => (
        <div key={entry.location_id} className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200">
          <MapPin size={14} className={entry.is_primary ? 'text-indigo-600' : 'text-slate-300'} />
          <span className="flex-1 text-sm font-medium text-slate-700">{entry.location_name}</span>
          {entry.is_primary ? (
            <Tag className="rounded-full border-0 bg-indigo-50 text-indigo-600 text-[10px] font-bold">Primary</Tag>
          ) : (
            <button
              type="button"
              onClick={() => setPrimary(entry.location_id)}
              className="text-[10px] text-slate-400 hover:text-indigo-600 font-bold uppercase"
            >
              Set Primary
            </button>
          )}
          <button
            type="button"
            onClick={() => remove(entry.location_id)}
            className="text-slate-300 hover:text-rose-500 transition-colors"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}
      {availableOptions.length > 0 && (
        <Select
          className="w-full"
          placeholder="+ Add location"
          value={undefined}
          onChange={(v) => addLocation(v)}
          options={availableOptions.map(l => ({ label: l.name, value: l.id }))}
          showSearch
          filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
        />
      )}
      {value.length === 0 && (
        <p className="text-xs text-slate-400 mt-1">Select at least one location. The first becomes primary.</p>
      )}
    </div>
  )
}

const { Content, Sider } = Layout
const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// ─── Steps Configuration ───────────────────────────────────────────────────
const STEPS = [
  { title: 'Job Info', icon: <Briefcase size={18} /> },
  { title: 'Hiring Team', icon: <Users size={18} /> },
  { title: 'Sourcing', icon: <Target size={18} /> },
  { title: 'Workflow', icon: <Workflow size={18} /> },
  { title: 'Orchestration', icon: <Layers size={18} /> },
  { title: 'Prequal', icon: <ShieldCheck size={18} /> },
  { title: 'Interviews', icon: <Box size={18} /> },
  { title: 'Automation', icon: <BrainCircuit size={18} /> },
  { title: 'Offers', icon: <DollarSign size={18} /> },
  { title: 'Review', icon: <CheckCircle2 size={18} /> },
]

import { orchestrationApi } from '@/api/orchestration'

// ─── Workflow Master Selector ──────────────────────────────────────────────────

function WorkflowMasterSelector({
  value,
  onChange,
  onTemplateSelect,
}: {
  value?: { workflow_id?: string; workflow_template_id?: string; workflow_enabled: boolean; is_workflow_controlled: boolean }
  onChange: (v: any) => void
  onTemplateSelect: (templateId: string) => void
}) {
  const { data: templatesData, isLoading } = useApiQuery(['workflow-templates'], orchestrationApi.listTemplates)
  const templates = (templatesData as any)?.templates || []

  const enabled = value?.workflow_enabled || false
  const controlled = value?.is_workflow_controlled || false

  return (
    <div className="space-y-6">
      <Card className={cn(
        "rounded-3xl border-slate-100 transition-all",
        enabled ? "shadow-soft-md border-indigo-100" : "shadow-none bg-slate-50/50"
      )}>
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-2xl flex items-center justify-center transition-colors",
              enabled ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-400"
            )}>
              <Layers size={20} />
            </div>
            <div>
              <Title level={4} className="!m-0 font-black tracking-tight">Workflow Master Orchestration</Title>
              <Text className="text-slate-400 text-xs font-medium">Toggle end-to-end automation engine for this job</Text>
            </div>
          </div>
          <Switch 
            checked={enabled} 
            onChange={(c) => onChange({ ...value, workflow_enabled: c })}
            checkedChildren="ENABLED"
            unCheckedChildren="DISABLED"
          />
        </div>

        {enabled && (
          <div className="p-6 animate-in fade-in slide-in-from-top-2 duration-300 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">Orchestration Template</span>
                <Select
                  className="w-full"
                  size="large"
                  placeholder="Select workflow template"
                  loading={isLoading}
                  value={value?.workflow_template_id}
                  onChange={(v) => {
                    onChange({ ...value, workflow_template_id: v })
                    onTemplateSelect(v)
                  }}
                  options={templates.map((t: any) => ({
                    label: (
                      <div className="py-1">
                        <div className="font-bold text-slate-700">{t.name}</div>
                        <div className="text-[10px] text-slate-400 font-medium">{t.description}</div>
                      </div>
                    ),
                    value: t.id
                  }))}
                />
              </div>

              <div className="flex flex-col gap-4">
                <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <ShieldCheck size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">Enforce Workflow Pipeline</span>
                    </div>
                    <Switch 
                      size="small"
                      checked={controlled}
                      onChange={(c) => onChange({ ...value, is_workflow_controlled: c })}
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed font-medium m-0">
                    When enabled, the hiring pipeline stages are derived directly from the workflow template. Manual editing will be disabled.
                  </p>
                </div>
              </div>
            </div>

            {value?.workflow_template_id && (
              <div className="mt-8 p-6 bg-slate-50 rounded-3xl border border-slate-100 border-dashed">
                <div className="flex items-center gap-2 mb-4">
                  <Workflow size={14} className="text-slate-400" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Workflow Preview</span>
                </div>
                {/* Visual preview placeholder */}
                <div className="flex items-center gap-3 overflow-x-auto pb-2">
                  {['Job Created', 'Approvals', 'Sourcing', 'Screening', 'Offers'].map((s, i) => (
                    <React.Fragment key={s}>
                      <div className="px-3 py-2 bg-white rounded-xl border border-slate-200 shadow-sm text-[10px] font-bold text-slate-600 whitespace-nowrap">
                        {s}
                      </div>
                      {i < 4 && <ChevronRight size={12} className="text-slate-300" />}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}

// ─── Default Stages ───────────────────────────────────────────────────────────

const DEFAULT_STAGES = [
  { name: 'Sourced', stage_type: 'sourcing', stage_order: 1, is_mandatory: true, is_critical_path: true, stage_zone: 'pre_submission' },
  { name: 'Screening', stage_type: 'screening', stage_order: 2, is_mandatory: true, is_critical_path: true, stage_zone: 'hiring_flow' },
  { name: 'Interview', stage_type: 'interview', stage_order: 3, is_mandatory: true, is_critical_path: true, stage_zone: 'hiring_flow' },
  { name: 'Offer', stage_type: 'offer', stage_order: 4, is_mandatory: true, is_critical_path: true, stage_zone: 'hiring_flow' },
  { name: 'Hired', stage_type: 'joined', stage_order: 5, is_mandatory: true, is_critical_path: true, stage_zone: 'closed' },
]

// ─── Job Stage Builder ────────────────────────────────────────────────────────

function JobStageBuilder({
  value = [],
  onChange,
  users,
  readOnly = false,
}: {
  value?: Partial<JobStage>[]
  onChange?: (v: Partial<JobStage>[]) => void
  users: any[]
  readOnly?: boolean
}) {
  const addStage = () => {
    if (readOnly) return
    const next: Partial<JobStage> = {
      name: 'New Stage',
      stage_type: 'screening',
      stage_order: value.length + 1,
      is_mandatory: false,
      is_critical_path: true,
      stage_zone: 'hiring_flow',
      trigger_type: 'none',
    }
    onChange?.([...value, next])
  }

  const remove = (idx: number) => {
    if (readOnly) return
    onChange?.(value.filter((_, i) => i !== idx).map((s, i) => ({ ...s, stage_order: i + 1 })))
  }

  const update = (idx: number, patch: Partial<JobStage>) => {
    if (readOnly) return
    onChange?.(value.map((s, i) => i === idx ? { ...s, ...patch } : s))
  }

  const moveUp = (idx: number) => {
    if (readOnly || idx === 0) return
    const arr = [...value]
    ;[arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]]
    onChange?.(arr.map((s, i) => ({ ...s, stage_order: i + 1 })))
  }

  const moveDown = (idx: number) => {
    if (readOnly || idx === value.length - 1) return
    const arr = [...value]
    ;[arr[idx], arr[idx + 1]] = [arr[idx + 1], arr[idx]]
    onChange?.(arr.map((s, i) => ({ ...s, stage_order: i + 1 })))
  }

  return (
    <div className="space-y-3">
      {value.map((stage, idx) => (
        <Card
          key={idx}
          size="small"
          className={cn(
            "rounded-2xl border-slate-200 transition-colors",
            readOnly ? "bg-slate-50/50 shadow-none" : "shadow-soft-sm hover:border-indigo-200"
          )}
          styles={{ body: { padding: '12px 16px' } }}
        >
          <div className="flex items-start gap-4">
            <div className="flex flex-col gap-1 mt-1">
              <button type="button" onClick={() => moveUp(idx)} disabled={readOnly || idx === 0} className="text-slate-300 hover:text-indigo-600 disabled:opacity-20"><ArrowUpDown size={12} /></button>
              <div className={cn(
                "w-6 h-6 rounded flex items-center justify-center text-[10px] font-black",
                stage.metadata?.workflow_controlled ? "bg-purple-100 text-purple-600" : "bg-slate-100 text-slate-500"
              )}>
                {idx + 1}
              </div>
            </div>

            <div className="flex-1 space-y-4">
              <Row gutter={12}>
                <Col span={8}>
                  <Input
                    placeholder="Stage Name"
                    value={stage.name}
                    onChange={(e) => update(idx, { name: e.target.value })}
                    className="font-bold text-slate-700"
                    disabled={readOnly}
                  />
                </Col>
                <Col span={8}>
                  <Select
                    className="w-full"
                    placeholder="Responsible Role"
                    value={stage.responsible_role}
                    onChange={(v) => update(idx, { responsible_role: v as any })}
                    disabled={readOnly}
                    options={[
                      { value: 'recruiter', label: 'Recruiter' },
                      { value: 'hiring_manager', label: 'Hiring Manager' },
                      { value: 'coordinator', label: 'Coordinator' },
                      { value: 'interviewer', label: 'Interviewer/Panel' },
                      { value: 'agency', label: 'Agency' },
                    ]}
                  />
                </Col>
                <Col span={8}>
                  <Select
                    className="w-full"
                    placeholder="Responsible User"
                    value={stage.responsible_user_id}
                    onChange={(v) => update(idx, { responsible_user_id: v })}
                    disabled={readOnly}
                    options={users.map(u => ({ label: u.full_name || u.email, value: u.id }))}
                    allowClear
                    showSearch
                    filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                  />
                </Col>
              </Row>

              <div className="flex items-center gap-6 pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Type</span>
                  <Select
                    size="small"
                    className="w-28"
                    value={stage.stage_type}
                    onChange={(v) => update(idx, { stage_type: v as any })}
                    disabled={readOnly}
                    options={[
                      { value: 'sourcing', label: 'Sourcing' },
                      { value: 'screening', label: 'Screening' },
                      { value: 'interview', label: 'Interview' },
                      { value: 'assessment', label: 'Assessment' },
                      { value: 'offer', label: 'Offer' },
                      { value: 'joined', label: 'Joined' },
                    ]}
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Trigger</span>
                  <Select
                    size="small"
                    className="w-32"
                    value={stage.trigger_type}
                    onChange={(v) => update(idx, { trigger_type: v as any })}
                    disabled={readOnly}
                    options={[
                      { value: 'none', label: 'None' },
                      { value: 'interview', label: 'Interview Round' },
                      { value: 'prequal', label: 'Prequalification' },
                      { value: 'approval', label: 'Approval' },
                    ]}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Authority</span>
                  <Select
                    size="small"
                    className="w-32"
                    value={stage.decision_authority}
                    onChange={(v) => update(idx, { decision_authority: v as any })}
                    disabled={readOnly}
                    options={[
                      { value: 'any', label: 'Anyone' },
                      { value: 'recruiter', label: 'Recruiter' },
                      { value: 'hiring_manager', label: 'Manager' },
                      { value: 'coordinator', label: 'Coordinator' },
                      { value: 'admin', label: 'Admin/Owner' },
                    ]}
                  />
                </div>

                {stage.metadata?.workflow_controlled && (
                  <Tag color="purple" className="rounded-full border-none px-2 font-black text-[8px] uppercase tracking-tighter ml-auto">
                    Workflow Controlled
                  </Tag>
                )}

                <div className={cn("flex items-center gap-4", !stage.metadata?.workflow_controlled && "ml-auto")}>
                  <Checkbox
                    checked={stage.is_mandatory}
                    onChange={(e) => update(idx, { is_mandatory: e.target.checked })}
                    disabled={readOnly}
                  >
                    <span className="text-[9px] font-black text-slate-500 uppercase">Mandatory</span>
                  </Checkbox>
                  {!readOnly && (
                    <button
                      type="button"
                      onClick={() => remove(idx)}
                      className="text-slate-300 hover:text-rose-500 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      ))}

      {!readOnly && (
        <button
          type="button"
          onClick={addStage}
          className="w-full flex items-center justify-center gap-2 p-4 rounded-2xl border border-dashed border-slate-300 text-slate-400 hover:border-indigo-400 hover:text-indigo-600 transition-all text-xs font-bold uppercase tracking-wide bg-slate-50/30"
        >
          <Plus size={16} /> Add Pipeline Stage
        </button>
      )}
    </div>
  )
}

// ─── Main Component ─────────────────────────────────────────────────────────

export default function JobSetupStudio() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation(['jobs', 'common'])
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [jobData, setJobData] = useState<Partial<JobRequisition> | null>(null)
  const [templatePickerOpen, setTemplatePickerOpen] = useState(false)
  const [templateSearch, setTemplateSearch] = useState('')
  // Multiple locations controlled state (synced with form field)
  const [selectedLocations, setSelectedLocations] = useState<LocationEntry[]>([])
  // Approval chain controlled state
  const [approvalRequired, setApprovalRequired] = useState(false)
  const [approvalChain, setApprovalChain] = useState<ApproverEntry[]>([])
  // Prequalification binding state
  const [prequalEnabled, setPrequalEnabled] = useState(false)
  const [prequalFormId, setPrequalFormId] = useState<string | null>(null)
  const [prequalThreshold, setPrequalThreshold] = useState<number | null>(null)
  const [prequalPassAction, setPrequalPassAction] = useState<string>('advance')
  const [prequalFailAction, setPrequalFailAction] = useState<string>('reject')

  // Pipeline binding state
  const [jobStages, setJobStages] = useState<Partial<JobStage>[]>(DEFAULT_STAGES)

  // Interview binding state
  const [roundsOverride, setRoundsOverride] = useState<any[]>([])
  const [editingRoundIndex, setEditingRoundIndex] = useState<number | null>(null)

  const isEditMode = !!id

  const { data: requisitionData, isLoading: jobLoading } = useApiQuery(
    ['requisition', 'setup', id],
    () => requisitionsApi.get(id!),
    { enabled: isEditMode }
  )

  const { data: usersData } = useApiQuery(['org-users'], () => organisationApi.listUsers())
  const { data: departmentsData } = useApiQuery(['org-departments'], () => organisationApi.listDepartments())
  const { data: locsData } = useApiQuery(['org-locations'], () => organisationApi.listLocations())
  const { data: packagesData } = useApiQuery(['interview-packages'], () => interviewsApi.listPackages({ is_active: true }))
  const { data: typesData } = useApiQuery(['interview-types'], () => interviewsApi.listTypes())
  const { data: interviewTemplatesData } = useApiQuery(['interview-templates'], () => interviewsApi.listTemplates({ is_active: true }))
  const { data: bindingData } = useApiQuery(['job-interview-binding', id], () => interviewsApi.getJobBinding(id!), { enabled: !!id })
  const { data: agenciesData } = useApiQuery(['agencies-available'], () => agenciesApi.listAvailableAgencies())
  const { data: existingLocsData } = useApiQuery(
    ['job-locations', id],
    () => jobLocationsApi.list(id!),
    { enabled: isEditMode }
  )
  const { data: templatesData } = useApiQuery(
    ['jd-templates-picker', templateSearch],
    () => jdTemplatesApi.list({ active_only: 'true', ...(templateSearch ? { search: templateSearch } : {}) }),
    { enabled: templatePickerOpen }
  )

  // Prequalification forms list (for template selector)
  const { data: prequalFormsData } = useApiQuery(
    ['prequal-forms-list'],
    () => prequalificationApi.listForms(),
  )

  const jdTemplates = (templatesData as any)?.data?.templates
    ?? (templatesData as any)?.templates ?? []
  const prequalForms: any[] = (prequalFormsData as any)?.data?.forms
    ?? (prequalFormsData as any)?.forms ?? []

  const applyTemplate = (tpl: any) => {
    form.setFieldsValue({
      description: tpl.description || form.getFieldValue('description'),
      requirements: tpl.requirements || form.getFieldValue('requirements'),
      responsibilities: tpl.responsibilities || form.getFieldValue('responsibilities'),
      skills_required: tpl.skills_suggested?.length > 0 ? tpl.skills_suggested : form.getFieldValue('skills_required'),
    })
    setTemplatePickerOpen(false)
    message.success(`Template "${tpl.name}" applied`)
  }

  const users = ((usersData as any)?.users ?? [])
  const departments = ((departmentsData as any)?.departments ?? [])
  const locationOptions = ((locsData as any)?.locations ?? [])
  const interviewPackages = ((packagesData as any)?.data?.packages ?? []) as InterviewPackage[]
  const interviewTypes = ((typesData as any)?.data?.types ?? (typesData as any)?.types ?? []) as any[]
  const interviewTemplates = ((interviewTemplatesData as any)?.data?.templates ?? (interviewTemplatesData as any)?.templates ?? []) as any[]
  const currentBinding = (bindingData as any)?.data?.binding
  const availableAgencies = ((agenciesData as any)?.agencies ?? [])

  useEffect(() => {
    if (requisitionData) {
      const job = (requisitionData as any).requisition
      const stages = (requisitionData as any).stages || []
      setJobData(job)
      if (stages.length > 0) {
        setJobStages(stages)
      }
      const chain: ApproverEntry[] = Array.isArray(job.approval_chain) ? job.approval_chain : []
      setApprovalChain(chain)
      setApprovalRequired(chain.length > 0)
      
      const binding = currentBinding
      if (binding) {
        setRoundsOverride(binding.rounds_override || binding.effective_rounds || [])
      }

      form.setFieldsValue({
        ...job,
        job_owner_id: job.metadata?.job_owner_id || job.job_owner_id,
        internal_recruiter_ids: job.metadata?.internal_recruiter_ids || [],
        target_date: job.target_date ? dayjs(job.target_date) : null,
        expiry_date: job.metadata?.expiry_date ? dayjs(job.metadata.expiry_date) : null,
        interview_package_id: currentBinding?.package_id,
        interview_automation_enabled: currentBinding?.automation_enabled ?? true,
        interview_auto_pass_enabled: currentBinding?.auto_pass_enabled ?? true,
        interview_auto_reject_enabled: currentBinding?.auto_reject_enabled ?? true,
        interview_manual_review_required: currentBinding?.manual_review_required ?? false,
        sourcing_mode: job.sourcing_mode || 'internal_only',
        automation_enabled: job.metadata?.automation_enabled ?? true,
        agency_tenant_ids: job.metadata?.agency_tenant_ids || [],
        auto_distribute_to_agencies: Boolean(job.auto_distribute_to_agencies),
        agency_distribution_policy: job.agency_distribution_policy || 'manual',
        backup_recruiter_id: job.backup_recruiter_id,
        coordinator_id: job.coordinator_id,
      })
      // Load prequal binding state
      setPrequalEnabled(Boolean(job.prequal_enabled))
      setPrequalFormId(job.prequal_form_id || null)
      setPrequalThreshold(job.prequal_threshold_override ?? null)
      setPrequalPassAction(job.prequal_pass_action || 'advance')
      setPrequalFailAction(job.prequal_fail_action || 'reject')
    }
  }, [requisitionData, form, currentBinding])

  // Load existing locations when in edit mode
  useEffect(() => {
    if (existingLocsData) {
      const locs = (existingLocsData as any)?.data?.locations ?? (existingLocsData as any)?.locations ?? []
      if (locs.length > 0) {
        setSelectedLocations(locs.map((l: any) => ({
          id: l.id,
          location_id: l.location_id,
          location_name: l.location_name,
          is_primary: l.is_primary,
        })))
      }
    }
  }, [existingLocsData])

  const handleNext = async () => {
    try {
      await form.validateFields()
      setCurrentStep(prev => prev + 1)
    } catch (err) {
      message.error('Please fix errors before proceeding.')
    }
  }

  const handleBack = () => setCurrentStep(prev => prev - 1)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const metadata = {
        ...(jobData?.metadata || {}),
        internal_recruiter_ids: values.internal_recruiter_ids || [],
        automation_enabled: values.automation_enabled,
        agency_tenant_ids: values.agency_tenant_ids || [],
        expiry_date: values.expiry_date ? dayjs(values.expiry_date).format('YYYY-MM-DD') : null,
      }

      const payload: any = {
        title: values.title,
        department_id: values.department_id,
        // primary location from first selected location, or fallback location_id field
        location_id: selectedLocations.find(l => l.is_primary)?.location_id || values.location_id || null,
        job_type: values.job_type,
        work_mode: values.work_mode,
        priority: values.priority,
        headcount: values.headcount,
        target_date: values.target_date ? dayjs(values.target_date).format('YYYY-MM-DD') : null,
        budget_code: values.budget_code || '',
        is_confidential: values.is_confidential || false,
        experience_min: values.experience_min,
        experience_max: values.experience_max,
        salary_currency: values.salary_currency,
        salary_min: values.salary_min,
        salary_max: values.salary_max,
        salary_visible: values.salary_visible || false,
        description: values.description || '',
        responsibilities: values.responsibilities || '',
        requirements: values.requirements || '',
        skills_required: values.skills_required || [],
        job_owner_id: values.job_owner_id,
        hiring_manager_id: values.hiring_manager_id,
        recruiter_id: values.internal_recruiter_ids?.[0] || null,
        backup_recruiter_id: values.backup_recruiter_id || null,
        coordinator_id: values.coordinator_id || null,
        sourcing_mode: values.sourcing_mode || 'internal_only',
        auto_distribute_to_agencies: values.auto_distribute_to_agencies || false,
        agency_distribution_policy: values.agency_distribution_policy || 'manual',
        approval_chain: approvalRequired ? approvalChain : [],
        prequal_enabled: prequalEnabled,
        prequal_form_id: prequalEnabled ? prequalFormId : null,
        prequal_threshold_override: prequalEnabled ? prequalThreshold : null,
        prequal_pass_action: prequalPassAction,
        prequal_fail_action: prequalFailAction,
        offer_salary_default: values.salary_min,
        offer_currency_default: values.salary_currency,
        metadata,
      }

      const res = isEditMode
        ? await requisitionsApi.update(id!, payload)
        : await requisitionsApi.create(payload)

      const newJobId = (res as any)?.data?.data?.requisition?.id
        || (res as any)?.requisition?.id
        || id

      // Sync multiple locations (diff against existing to remove deleted, add new)
      if (newJobId) {
        try {
          const existingLocs: any[] = (existingLocsData as any)?.data?.locations
            ?? (existingLocsData as any)?.locations ?? []

          // Remove locations that were deleted from the list
          const removedLocs = existingLocs.filter(
            el => !selectedLocations.some(sl => sl.location_id === el.location_id)
          )
          await Promise.all(removedLocs.map(l => jobLocationsApi.remove(newJobId, l.location_id).catch(() => {})))

          // Add new locations (skip ones already saved, identified by having an id)
          const newLocs = selectedLocations.filter(sl => !sl.id)
          await Promise.all(
            newLocs.map(loc =>
              jobLocationsApi.add(newJobId, {
                location_id: loc.location_id,
                location_name: loc.location_name,
                is_primary: loc.is_primary,
              }).catch(() => {})
            )
          )

          // Update primary flag if it changed
          const primaryLoc = selectedLocations.find(l => l.is_primary)
          const existingPrimary = existingLocs.find(l => l.is_primary)
          if (primaryLoc?.id && primaryLoc.location_id !== existingPrimary?.location_id) {
            await jobLocationsApi.add(newJobId, {
              location_id: primaryLoc.location_id,
              location_name: primaryLoc.location_name,
              is_primary: true,
            }).catch(() => {})
          }
        } catch {
          // non-fatal
        }
      }

      // Sync Job Stages
      if (newJobId) {
        try {
          const existingStages = (requisitionData as any)?.stages || []
          
          // Identify removed stages
          const removedStages = existingStages.filter((es: any) => !jobStages.some(js => js.id === es.id))
          await Promise.all(removedStages.map((s: any) => stagesApi.delete(newJobId, s.id).catch(() => {})))

          // Create or update stages
          const savedStages = await Promise.all(jobStages.map(async (stage) => {
            if (stage.id) {
              const { data } = await stagesApi.update(newJobId, stage.id, stage)
              return (data as any)?.stage || stage
            } else {
              const { data } = await stagesApi.create(newJobId, stage)
              return (data as any)?.stage
            }
          }))

          // Final reorder to be sure
          const stageIds = savedStages.filter(s => s?.id).map(s => s.id)
          if (stageIds.length > 0) {
            await stagesApi.reorder(newJobId, stageIds).catch(() => {})
          }
        } catch (err) {
          console.error("Failed to sync stages", err)
          // non-fatal but worth noting
        }
      }

      if (values.interview_package_id) {
        if (values.interview_package_id !== currentBinding?.package_id) {
          await interviewsApi.bindJobPackage(newJobId, values.interview_package_id)
        }
        
        // Update binding with automation overrides if changed
        const binding_payload: any = {
          automation_enabled: values.interview_automation_enabled ?? true,
          auto_pass_enabled: values.interview_auto_pass_enabled ?? true,
          auto_reject_enabled: values.interview_auto_reject_enabled ?? true,
          manual_review_required: values.interview_manual_review_required ?? false,
          rounds_override: roundsOverride,
        }
        
        await interviewsApi.updateJobBinding(newJobId, binding_payload)
      }

      message.success(isEditMode ? 'Job configuration updated' : 'Job created successfully')
      navigate(`/jobs?id=${newJobId}`)
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to save job')
    } finally {
      setLoading(false)
    }
  }

  if (jobLoading) return <div className="h-screen flex items-center justify-center bg-white"><Spin size="large" tip="Initializing Studio..." /></div>

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-50 shadow-soft-sm">
        <div className="flex items-center gap-4">
          <Button icon={<ChevronLeft size={18} />} onClick={() => navigate('/jobs')} className="border-slate-200" />
          <Divider type="vertical" className="h-8 border-slate-200" />
          <div>
            <Title level={4} className="!m-0 text-slate-900 font-black tracking-tight uppercase tracking-widest leading-none">
              {isEditMode ? 'Job Setup Studio' : 'Job Creation Engine'}
            </Title>
            <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] block mt-1">
              {isEditMode ? `Configuring: ${jobData?.job_ref_id || 'REQUISITION'}` : 'New Enterprise Requisition'}
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button icon={<Save size={16} />} className="font-bold text-[11px] uppercase tracking-widest border-slate-200 h-10 px-6 rounded-xl">Save Draft</Button>
          <Button 
            type="primary" 
            onClick={() => currentStep === STEPS.length - 1 ? form.submit() : handleNext()} 
            loading={loading}
            className="bg-indigo-600 border-none font-black text-[11px] uppercase tracking-widest h-10 px-8 rounded-xl shadow-indigo-100 shadow-lg"
          >
            {currentStep === STEPS.length - 1 ? 'Publish & Launch' : 'Save & Continue'}
          </Button>
        </div>
      </header>

      <Layout className="flex-1 bg-transparent">
        <Sider width={300} className="bg-white border-r border-slate-200 hidden lg:block" theme="light">
          <div className="p-8">
            <Steps
              direction="vertical"
              current={currentStep}
              onChange={setCurrentStep}
              className="job-setup-steps"
              items={STEPS.map((step, idx) => ({
                title: <span className="text-[11px] font-black uppercase tracking-widest">{step.title}</span>,
                icon: (
                  <div className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-xl transition-all border",
                    currentStep === idx ? "bg-indigo-600 text-white border-indigo-600 shadow-soft-lg" : 
                    currentStep > idx ? "bg-emerald-50 text-emerald-600 border-emerald-100" : "bg-slate-50 text-slate-400 border-slate-100"
                  )}>
                    {currentStep > idx ? <CheckCircle2 size={16} /> : step.icon}
                  </div>
                )
              }))}
            />
          </div>
        </Sider>

        <Content className="overflow-y-auto custom-scrollbar bg-white">
          <div className="max-w-4xl mx-auto p-12">
            <Form form={form} layout="vertical" onFinish={onFinish} requiredMark="optional">
              
              {/* STEP 1: Basic Info */}
              {currentStep === 0 && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1 text-2xl uppercase">Job Identity & Parameters</Title>
                    <Paragraph className="text-slate-500 font-medium">Define the core identity, requirements, and compensation for this role.</Paragraph>
                  </div>
                  
                  {/* Group 1: Core Identity */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Target size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Core Identity</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Form.Item name="title" label="Job Title" rules={[{ required: true }]}>
                        <Input size="large" className="rounded-xl border-slate-200 h-12 text-lg font-bold" placeholder="e.g. Senior Backend Engineer" />
                      </Form.Item>

                      <Form.Item name="department_id" label="Department" rules={[{ required: true }]}>
                        <Select size="large" className="rounded-xl" placeholder="Select department" options={departments.map((d: any) => ({ label: d.name, value: d.id }))} />
                      </Form.Item>

                      <Form.Item
                        label={
                          <span className="flex items-center gap-1.5">
                            <MapPin size={12} className="text-indigo-500" />
                            Job Locations
                          </span>
                        }
                        required
                        help={selectedLocations.length === 0 ? 'Add at least one location' : undefined}
                        validateStatus={selectedLocations.length === 0 ? 'warning' : ''}
                      >
                        <LocationMultiSelect
                          value={selectedLocations}
                          onChange={setSelectedLocations}
                          locationOptions={locationOptions}
                        />
                      </Form.Item>
                    </div>
                  </Card>

                  {/* Group 2: Hiring Parameters */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Sliders size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Hiring Parameters</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Row gutter={24}>
                        <Col span={8}>
                          <Form.Item name="job_type" label="Employment Type" rules={[{ required: true }]}>
                            <Select size="large" options={[
                              { value: 'full_time', label: 'Full Time' },
                              { value: 'part_time', label: 'Part Time' },
                              { value: 'contract', label: 'Contract' },
                              { value: 'internship', label: 'Internship' },
                              { value: 'freelance', label: 'Freelance' }
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="work_mode" label="Work Mode" rules={[{ required: true }]}>
                            <Select size="large" options={[
                              { value: 'remote', label: 'Remote' },
                              { value: 'onsite', label: 'On-site' },
                              { value: 'hybrid', label: 'Hybrid' }
                            ]} />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item name="priority" label="Priority">
                            <Select size="large" options={[
                              { value: 'low', label: 'Low' },
                              { value: 'medium', label: 'Medium' },
                              { value: 'high', label: 'High' },
                              { value: 'urgent', label: 'Urgent' }
                            ]} />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={24}>
                        <Col span={6}>
                          <Form.Item name="headcount" label="Headcount" rules={[{ required: true }]}>
                            <InputNumber size="large" min={1} className="w-full rounded-xl" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name="target_date" label="Target Hire Date">
                            <DatePicker size="large" className="w-full rounded-xl" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            name="expiry_date"
                            label={
                              <span className="flex items-center gap-1">
                                <Clock size={11} className="text-amber-500" />
                                Posting Expiry
                              </span>
                            }
                            tooltip="Job posting will auto-close after this date"
                          >
                            <DatePicker
                              size="large"
                              className="w-full rounded-xl"
                              disabledDate={(d) => d && d.isBefore(dayjs(), 'day')}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name="budget_code" label="Budget Code">
                            <Input size="large" className="rounded-xl" placeholder="e.g. ENG-2026-04" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <div className="flex items-center gap-6 p-4 bg-slate-50 rounded-2xl border border-slate-100 mt-2">
                        <Form.Item name="is_confidential" valuePropName="checked" noStyle>
                          <Checkbox><span className="text-xs font-bold text-slate-600 uppercase tracking-tight">Confidential Job</span></Checkbox>
                        </Form.Item>
                        <Text className="text-[10px] text-slate-400 font-medium">Restricts visibility to assigned team only.</Text>
                      </div>
                    </div>
                  </Card>

                  {/* Group 3: Experience & Compensation */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <DollarSign size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Experience & Compensation</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item label="Experience Range (Years)">
                            <div className="flex items-center gap-3">
                              <Form.Item name="experience_min" noStyle><InputNumber placeholder="Min" min={0} className="w-full rounded-xl" /></Form.Item>
                              <span className="text-slate-300">—</span>
                              <Form.Item name="experience_max" noStyle><InputNumber placeholder="Max" min={0} className="w-full rounded-xl" /></Form.Item>
                            </div>
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="Annual Salary Bracket">
                            <div className="flex items-center gap-3">
                              <Form.Item name="salary_currency" noStyle rules={[{ required: true }]}>
                                <Select className="w-32 rounded-xl" options={CURRENCIES.map(c => ({ label: c.code, value: c.code }))} />
                              </Form.Item>
                              <Form.Item name="salary_min" noStyle><InputNumber placeholder="Min" min={0} className="w-full rounded-xl" /></Form.Item>
                              <span className="text-slate-300">—</span>
                              <Form.Item name="salary_max" noStyle><InputNumber placeholder="Max" min={0} className="w-full rounded-xl" /></Form.Item>
                            </div>
                          </Form.Item>
                        </Col>
                      </Row>
                      <div className="flex items-center gap-4">
                        <Form.Item name="salary_visible" valuePropName="checked" noStyle>
                          <Checkbox><span className="text-xs font-bold text-slate-600 uppercase tracking-tight">Show salary on job boards</span></Checkbox>
                        </Form.Item>
                      </div>
                    </div>
                  </Card>

                  {/* Group 4: Role Definition */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm bg-white overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText size={14} className="text-indigo-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Role Definition</span>
                      </div>
                      <Button
                        size="small"
                        icon={<Layers size={12} />}
                        onClick={() => setTemplatePickerOpen(true)}
                        className="rounded-lg text-xs font-semibold border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                      >
                        Use JD Template
                      </Button>
                    </div>
                    <div className="p-6 space-y-6">
                      <Form.Item name="skills_required" label="Target Skills">
                        <Select mode="tags" size="large" placeholder="e.g. React, Node.js, System Design" className="rounded-xl" />
                      </Form.Item>
                      
                      <Form.Item name="description" label="The Mission (Description)">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What is the primary goal of this role?" />
                      </Form.Item>

                      <Form.Item name="responsibilities" label="Key Responsibilities">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What will this person do day-to-day?" />
                      </Form.Item>

                      <Form.Item name="requirements" label="Ideal Candidate (Requirements)">
                        <TextArea rows={4} className="rounded-xl p-4" placeholder="What background and experience are you looking for?" />
                      </Form.Item>
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 2: Hiring Team */}
              {currentStep === 1 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1">Hiring Team & Ownership</Title>
                    <p className="text-slate-400 text-sm font-medium">Assign ownership and the core team responsible for this hire.</p>
                  </div>

                  {/* Ownership */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Lock size={13} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Ownership</span>
                    </div>
                    <div className="p-6">
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item name="job_owner_id" label="Job Owner" rules={[{ required: true, message: 'Job owner is required' }]}>
                            <Select
                              size="large"
                              showSearch
                              placeholder="Select job owner"
                              options={users.map((u: any) => ({ label: u.full_name || u.email, value: u.id }))}
                              filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="hiring_manager_id" label="Hiring Manager">
                            <Select
                              size="large"
                              showSearch
                              placeholder="Select hiring manager"
                              allowClear
                              options={users.map((u: any) => ({ label: u.full_name || u.email, value: u.id }))}
                              filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </div>
                  </Card>

                  {/* Recruiters */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <Users size={13} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Recruitment Team</span>
                    </div>
                    <div className="p-6 space-y-4">
                      <Form.Item name="internal_recruiter_ids" label="Primary Recruiters">
                        <Select
                          size="large"
                          mode="multiple"
                          placeholder="Select one or more recruiters"
                          options={users.map((u: any) => ({ label: u.full_name || u.email, value: u.id }))}
                          filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                        />
                      </Form.Item>
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item name="backup_recruiter_id" label="Backup Recruiter" tooltip="Takes over if primary recruiter is unavailable">
                            <Select
                              size="large"
                              showSearch
                              allowClear
                              placeholder="Optional backup recruiter"
                              options={users.map((u: any) => ({ label: u.full_name || u.email, value: u.id }))}
                              filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name="coordinator_id" label="Coordinator" tooltip="Manages scheduling, communication, and logistics">
                            <Select
                              size="large"
                              showSearch
                              allowClear
                              placeholder="Optional coordinator"
                              options={users.map((u: any) => ({ label: u.full_name || u.email, value: u.id }))}
                              filterOption={(input, opt) => (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())}
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 3: Sourcing Setup */}
              {currentStep === 2 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <Title level={3} className="font-black text-slate-900 tracking-tight">Sourcing Configuration</Title>
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm p-2">
                    <Form.Item name="sourcing_mode" label="Sourcing Mode" rules={[{ required: true }]}>
                      <Radio.Group className="w-full">
                        <Row gutter={16}>
                          <Col span={8}><Radio.Button value="internal_only" className="w-full h-16 flex items-center justify-center rounded-xl font-bold text-xs">Internal Only</Radio.Button></Col>
                          <Col span={8}><Radio.Button value="hybrid" className="w-full h-16 flex items-center justify-center rounded-xl font-bold text-xs">Hybrid</Radio.Button></Col>
                          <Col span={8}><Radio.Button value="external_only" className="w-full h-16 flex items-center justify-center rounded-xl font-bold text-xs">Agency Driven</Radio.Button></Col>
                        </Row>
                      </Radio.Group>
                    </Form.Item>
                    <Form.Item name="agency_tenant_ids" label="Assign Agencies"><Select size="large" mode="multiple" options={availableAgencies.map((a: any) => ({ label: a.name, value: a.agency_tenant_id }))} /></Form.Item>
                    <Row gutter={24}>
                      <Col span={12}>
                        <Form.Item name="auto_distribute_to_agencies" valuePropName="checked">
                          <Checkbox>Auto distribute to agencies</Checkbox>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="agency_distribution_policy" label="Distribution Policy">
                          <Select size="large" options={[
                            { value: 'manual', label: 'Manual' },
                            { value: 'performance_ranked', label: 'Performance Ranked' },
                            { value: 'all', label: 'All Preferred Agencies' },
                          ]} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                </div>
              )}

              {/* STEP 4: Workflow & Pipeline */}
              {currentStep === 3 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1">Pipeline & Approval Workflow</Title>
                    <p className="text-slate-400 text-sm font-medium">Configure your custom hiring pipeline and approval requirements.</p>
                  </div>

                  {/* Pipeline stages */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <LayoutGrid size={13} className="text-indigo-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Hiring Pipeline Configuration</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {form.getFieldValue('is_workflow_controlled') && (
                          <Tag color="purple" className="m-0 border-none font-black text-[9px] uppercase px-2 rounded-md">
                            Workflow Controlled
                          </Tag>
                        )}
                        <Tag className="m-0 border-none bg-indigo-50 text-indigo-600 font-black text-[9px] uppercase px-2 rounded-md">
                          {jobStages.length} Stages
                        </Tag>
                      </div>
                    </div>
                    <div className="p-6">
                      {form.getFieldValue('is_workflow_controlled') && (
                        <div className="mb-6 p-4 bg-purple-50 rounded-2xl border border-purple-100 flex items-start gap-3">
                          <Layers size={18} className="text-purple-600 mt-0.5" />
                          <div>
                            <p className="text-xs font-bold text-purple-900 uppercase tracking-tight">Controlled by Workflow Master</p>
                            <p className="text-[11px] text-purple-700 font-medium mt-0.5 leading-relaxed">
                              This job's pipeline stages are defined by the attached orchestration template. Manual editing is disabled to ensure process integrity.
                            </p>
                          </div>
                        </div>
                      )}
                      <JobStageBuilder
                        value={jobStages}
                        onChange={setJobStages}
                        users={users}
                        readOnly={form.getFieldValue('is_workflow_controlled')}
                      />
                    </div>
                  </Card>

                  {/* Approval chain */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <UserCheck size={13} className="text-indigo-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Approval Required</span>
                      </div>
                      <Switch
                        checked={approvalRequired}
                        onChange={(c) => {
                          setApprovalRequired(c)
                          if (!c) setApprovalChain([])
                        }}
                        checkedChildren="ON"
                        unCheckedChildren="OFF"
                      />
                    </div>
                    <div className="p-6">
                      {!approvalRequired ? (
                        <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
                          <div className="w-8 h-8 rounded-xl bg-slate-200 flex items-center justify-center flex-shrink-0">
                            <CheckCircle2 size={16} className="text-slate-400" />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-600">No approval required</p>
                            <p className="text-xs text-slate-400 mt-0.5">Job can be published directly without waiting for sign-off.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-xl border border-amber-100">
                            <AlertTriangle size={13} className="text-amber-500 flex-shrink-0 mt-0.5" />
                            <p className="text-[11px] text-amber-700 font-medium m-0">
                              Job will move to <strong>Pending Approval</strong> when submitted. Each approver must confirm before the job is activated.
                            </p>
                          </div>
                          <ApprovalChainBuilder
                            value={approvalChain}
                            onChange={setApprovalChain}
                            users={users}
                          />
                          {approvalChain.length > 0 && (
                            <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Approval Flow Preview</p>
                              <div className="flex items-center gap-2 flex-wrap">
                                <div className="px-3 py-1.5 bg-indigo-50 rounded-lg border border-indigo-100 text-xs font-bold text-indigo-700">Submitted</div>
                                {approvalChain.filter(a => a.user_id).map((a, i) => (
                                  <React.Fragment key={i}>
                                    <ChevronRight size={12} className="text-slate-300" />
                                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-lg border border-slate-200 text-xs">
                                      {a.is_fallback && <UserCheck size={10} className="text-amber-500" />}
                                      <span className="font-bold text-slate-700">{a.name || 'Approver'}</span>
                                      {a.is_fallback && <span className="text-[9px] text-amber-500 font-bold">FALLBACK</span>}
                                    </div>
                                  </React.Fragment>
                                ))}
                                <ChevronRight size={12} className="text-slate-300" />
                                <div className="px-3 py-1.5 bg-emerald-50 rounded-lg border border-emerald-100 text-xs font-bold text-emerald-700">Active</div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {/* STEP 5: Orchestration (Workflow Master) */}
              {currentStep === 4 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1">Global Orchestration</Title>
                    <p className="text-slate-400 text-sm font-medium">Bind this job to the Workflow Master for end-to-end automation.</p>
                  </div>

                  <WorkflowMasterSelector
                    value={form.getFieldsValue(['workflow_id', 'workflow_template_id', 'workflow_enabled'])}
                    onChange={(v) => form.setFieldsValue(v)}
                    onTemplateSelect={(tplId) => {
                      // Optionally fetch template and update stages
                    }}
                  />
                </div>
              )}

              {/* STEP 6: Prequalification Binding */}
              {currentStep === 5 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div>
                    <Title level={3} className="font-black text-slate-900 tracking-tight mb-1 text-2xl uppercase">Prequalification</Title>
                    <p className="text-slate-500 font-medium text-sm">Attach a prequalification form to screen candidates before they enter the pipeline.</p>
                  </div>

                  {/* Enable toggle */}
                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                      <ShieldCheck size={14} className="text-indigo-600" />
                      <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Prequalification Gate</span>
                    </div>
                    <div className="p-6 space-y-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-black text-slate-700 uppercase tracking-wide">Enable Prequalification</p>
                          <p className="text-xs text-slate-400 font-medium mt-0.5">Candidates must complete a screening form before entering the pipeline</p>
                        </div>
                        <Switch
                          checked={prequalEnabled}
                          onChange={setPrequalEnabled}
                          className={prequalEnabled ? 'bg-indigo-600' : ''}
                        />
                      </div>

                      {prequalEnabled && (
                        <>
                          <div>
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Select Prequalification Form</p>
                            <Select
                              size="large"
                              className="w-full"
                              placeholder="Choose a prequalification template..."
                              value={prequalFormId}
                              onChange={setPrequalFormId}
                              options={prequalForms.map((f: any) => ({ label: f.name, value: f.id }))}
                              allowClear
                              showSearch
                              filterOption={(input, opt) =>
                                (opt?.label as string || '').toLowerCase().includes(input.toLowerCase())
                              }
                            />
                            {prequalForms.length === 0 && (
                              <p className="text-xs text-amber-600 font-bold mt-2 uppercase">
                                No prequalification forms found. Create one in the Prequalification module first.
                              </p>
                            )}
                          </div>

                          <div>
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">
                              Pass Threshold Override
                              <span className="text-slate-300 font-medium normal-case ml-1">(0-100%). Leave blank to use form default)</span>
                            </p>
                            <InputNumber
                              size="large"
                              min={0}
                              max={100}
                              className="w-48"
                              placeholder="e.g. 70"
                              value={prequalThreshold}
                              onChange={(v) => setPrequalThreshold(v)}
                              addonAfter="%"
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </Card>

                  {/* Pass / Fail behavior */}
                  {prequalEnabled && (
                    <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                      <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                        <ArrowUpDown size={14} className="text-indigo-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Pass / Fail Routing</span>
                      </div>
                      <div className="p-6 space-y-6">
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">On Pass</p>
                          <Radio.Group
                            value={prequalPassAction}
                            onChange={e => setPrequalPassAction(e.target.value)}
                            className="flex flex-col gap-3"
                          >
                            <Radio value="advance" className="font-bold text-slate-700">
                              <span className="font-bold uppercase text-sm">Advance to Next Stage</span>
                              <p className="text-xs text-slate-400 ml-6 font-medium">Candidate automatically moves forward in the pipeline</p>
                            </Radio>
                            <Radio value="manual_review" className="font-bold text-slate-700">
                              <span className="font-bold uppercase text-sm">Flag for Manual Review</span>
                              <p className="text-xs text-slate-400 ml-6 font-medium">Recruiter must manually advance — even on pass</p>
                            </Radio>
                          </Radio.Group>
                        </div>

                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">On Fail</p>
                          <Radio.Group
                            value={prequalFailAction}
                            onChange={e => setPrequalFailAction(e.target.value)}
                            className="flex flex-col gap-3"
                          >
                            <Radio value="reject" className="font-bold text-slate-700">
                              <span className="font-bold uppercase text-sm">Auto-Reject</span>
                              <p className="text-xs text-slate-400 ml-6 font-medium">Application is automatically rejected</p>
                            </Radio>
                            <Radio value="hold" className="font-bold text-slate-700">
                              <span className="font-bold uppercase text-sm">Hold — Awaiting Review</span>
                              <p className="text-xs text-slate-400 ml-6 font-medium">Application is held for recruiter decision</p>
                            </Radio>
                            <Radio value="manual_review" className="font-bold text-slate-700">
                              <span className="font-bold uppercase text-sm">Flag for Manual Review</span>
                              <p className="text-xs text-slate-400 ml-6 font-medium">Recruiter is notified to review the failed screening</p>
                            </Radio>
                          </Radio.Group>
                        </div>
                      </div>
                    </Card>
                  )}

                  {/* Summary when disabled */}
                  {!prequalEnabled && (
                    <div className="flex items-center gap-4 p-5 bg-slate-50 rounded-3xl border border-slate-100">
                      <div className="h-10 w-10 bg-slate-100 rounded-2xl flex items-center justify-center flex-shrink-0">
                        <ShieldCheck size={18} className="text-slate-400" />
                      </div>
                      <div>
                        <p className="text-xs font-black text-slate-500 uppercase tracking-widest">No Prequalification Gate</p>
                        <p className="text-[11px] text-slate-400 font-medium mt-0.5">All applicants will enter the pipeline directly without screening.</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* STEP 7: Interview Setup */}
              {currentStep === 6 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <Title level={3} className="font-black text-slate-900 tracking-tight !m-0 uppercase tracking-widest leading-none">Interview Configuration</Title>
                      <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] block mt-1">Bind hiring process & automation rules</Text>
                    </div>
                  </div>

                  <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-50 bg-slate-50/50">
                      <Form.Item name="interview_package_id" label={<span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Select Interview Package Template</span>} className="!mb-0">
                        <Select 
                          size="large" 
                          placeholder="Search or select a package..."
                          options={interviewPackages.map(p => ({ label: p.title, value: p.id }))} 
                          className="w-full"
                          onChange={(val) => {
                            const pkg = interviewPackages.find(p => p.id === val)
                            if (pkg) {
                              setRoundsOverride(pkg.rounds || [])
                            }
                          }}
                        />
                      </Form.Item>
                    </div>

                    {form.getFieldValue('interview_package_id') ? (
                      <div className="p-6 space-y-8">
                        {/* Automation Toggles */}
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Zap size={14} className="text-indigo-600" />
                                <Text className="text-[10px] font-black text-indigo-700 uppercase tracking-widest">Auto-Decisioning</Text>
                              </div>
                              <Form.Item name="interview_automation_enabled" valuePropName="checked" noStyle>
                                <Switch size="small" />
                              </Form.Item>
                            </div>
                            <Text className="text-[10px] text-indigo-400 font-medium block">Enable AI-driven movement between rounds based on scores.</Text>
                          </div>

                          <div className="p-4 bg-amber-50/50 rounded-2xl border border-amber-100">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <UserCheck size={14} className="text-amber-600" />
                                <Text className="text-[10px] font-black text-amber-700 uppercase tracking-widest">Manual Review</Text>
                              </div>
                              <Form.Item name="interview_manual_review_required" valuePropName="checked" noStyle>
                                <Switch size="small" />
                              </Form.Item>
                            </div>
                            <Text className="text-[10px] text-amber-500 font-medium block">Force human review for all round decisions regardless of score.</Text>
                          </div>
                        </div>

                        {/* Round Preview */}
                        <div>
                          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">Pipeline Rounds & Thresholds</Text>
                          <div className="space-y-3">
                            {roundsOverride.map((r, i) => (
                              <div key={i} className="bg-white border border-slate-100 rounded-2xl hover:border-indigo-200 transition-colors group overflow-hidden">
                                <div 
                                  className="flex items-center justify-between p-4 cursor-pointer"
                                  onClick={() => setEditingRoundIndex(editingRoundIndex === i ? null : i)}
                                >
                                  <div className="flex items-center gap-4">
                                    <div className="h-8 w-8 bg-slate-100 rounded-xl flex items-center justify-center font-black text-slate-400 text-xs group-hover:bg-indigo-600 group-hover:text-white transition-all">
                                      {i + 1}
                                    </div>
                                    <div>
                                      <Text className="block text-xs font-black text-slate-700 uppercase">{r.name}</Text>
                                      <div className="flex items-center gap-1.5 mt-1">
                                        <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-black text-[8px] uppercase px-1.5 rounded leading-relaxed">
                                          {typeof r.type === 'string' ? r.type : (r.type as any)?.name || 'Technical'}
                                        </Tag>
                                        {r.auto_pass_enabled && <Zap size={10} className="text-amber-500" />}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-6">
                                    <div className="text-right">
                                      <Text className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Pass Threshold</Text>
                                      <div className="flex items-center gap-2 justify-end">
                                        <Text className="text-xs font-black text-emerald-600">{r.threshold_score}%</Text>
                                      </div>
                                    </div>
                                    <ChevronRight size={14} className={cn("text-slate-300 transition-transform", editingRoundIndex === i && "rotate-90")} />
                                  </div>
                                </div>
                                
                                {editingRoundIndex === i && (
                                  <div className="p-6 bg-slate-50 border-t border-slate-100 space-y-6 animate-in slide-in-from-top-2">
                                    <div className="grid grid-cols-2 gap-6">
                                      <div>
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Round Name</label>
                                        <Input 
                                          value={r.name} 
                                          onChange={e => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].name = e.target.value
                                            setRoundsOverride(newRounds)
                                          }}
                                          className="rounded-xl"
                                        />
                                      </div>
                                      <div>
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Interview Type</label>
                                        <Select 
                                          value={typeof r.type === 'string' ? r.type : r.type?.code}
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].type = val
                                            setRoundsOverride(newRounds)
                                          }}
                                          options={interviewTypes.map(t => ({ label: t.name, value: t.code }))}
                                          className="w-full rounded-xl"
                                        />
                                      </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-6">
                                      <div>
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Question Template</label>
                                        <Select 
                                          value={r.template_id}
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].template_id = val
                                            setRoundsOverride(newRounds)
                                          }}
                                          options={interviewTemplates.map(t => ({ label: t.name, value: t.id }))}
                                          className="w-full rounded-xl"
                                          placeholder="Select template..."
                                          allowClear
                                        />
                                      </div>
                                      <div>
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Pass Threshold (%)</label>
                                        <InputNumber 
                                          min={0} max={100} 
                                          value={r.threshold_score} 
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].threshold_score = val
                                            setRoundsOverride(newRounds)
                                          }}
                                          className="w-full rounded-xl"
                                        />
                                      </div>
                                    </div>

                                    <div className="flex items-center gap-8 p-4 bg-white rounded-2xl border border-slate-100">
                                      <div className="flex items-center gap-2">
                                        <Switch 
                                          size="small" 
                                          checked={r.auto_pass_enabled} 
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].auto_pass_enabled = val
                                            setRoundsOverride(newRounds)
                                          }}
                                        />
                                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Auto Pass</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Switch 
                                          size="small" 
                                          checked={r.auto_reject_enabled} 
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].auto_reject_enabled = val
                                            setRoundsOverride(newRounds)
                                          }}
                                        />
                                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Auto Reject</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Switch 
                                          size="small" 
                                          checked={r.manual_review_required} 
                                          onChange={val => {
                                            const newRounds = [...roundsOverride]
                                            newRounds[i].manual_review_required = val
                                            setRoundsOverride(newRounds)
                                          }}
                                        />
                                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Manual Review</span>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Additional Automation Config */}
                        <div className="pt-4 border-t border-slate-50 grid grid-cols-2 gap-8">
                          <Form.Item name="interview_auto_pass_enabled" valuePropName="checked" label={<span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Global Auto-Advance on Pass</span>} className="!mb-0">
                            <Switch />
                          </Form.Item>
                          <Form.Item name="interview_auto_reject_enabled" valuePropName="checked" label={<span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Global Auto-Reject on Fail</span>} className="!mb-0">
                            <Switch />
                          </Form.Item>
                        </div>
                      </div>
                    ) : (
                      <div className="p-12 text-center">
                        <Workflow size={48} className="text-slate-200 mx-auto mb-4" />
                        <Text className="block text-xs font-bold text-slate-400 uppercase tracking-widest">No Package Selected</Text>
                        <Text className="text-[11px] text-slate-300 block mt-1">Select a template to configure the hiring rounds and automation rules.</Text>
                      </div>
                    )}
                  </Card>
                </div>
              )}

              {/* STEP 8: Automation Setup */}
              {currentStep === 7 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <Title level={3} className="font-black text-slate-900 tracking-tight !m-0 uppercase tracking-widest leading-none">Automation Engine</Title>
                      <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] block mt-1">Configure intelligent process triggers</Text>
                    </div>
                    {form.getFieldValue('is_workflow_controlled') && (
                      <Tag color="purple" className="m-0 border-none font-black text-[10px] uppercase px-3 py-1 rounded-lg">
                        Workflow Controlled
                      </Tag>
                    )}
                  </div>

                  {form.getFieldValue('is_workflow_controlled') && (
                    <div className="p-4 bg-purple-50 rounded-2xl border border-purple-100 flex items-start gap-3">
                      <Layers size={18} className="text-purple-600 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-purple-900 uppercase tracking-tight">Orchestration Lock</p>
                        <p className="text-[11px] text-purple-700 font-medium mt-0.5 leading-relaxed">
                          The active Workflow Master governs automation for this job. Manual overrides are disabled to maintain orchestration integrity.
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* AI Brain Section */}
                    <Card className={cn(
                      "rounded-3xl border-slate-100 shadow-soft-sm transition-all",
                      form.getFieldValue('is_workflow_controlled') ? "opacity-60 grayscale-[0.5]" : "hover:border-indigo-200"
                    )}>
                      <div className="flex items-center justify-between p-4 bg-indigo-50/50 border-b border-slate-100">
                        <div className="flex items-center gap-3">
                          <BrainCircuit size={20} className="text-indigo-600" />
                          <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Hiring AI Brain</span>
                        </div>
                        <Form.Item name="automation_enabled" valuePropName="checked" noStyle>
                          <Switch size="small" disabled={form.getFieldValue('is_workflow_controlled')} />
                        </Form.Item>
                      </div>
                      <div className="p-5 space-y-4">
                        <div className="flex items-center justify-between">
                          <Text className="text-[11px] font-bold text-slate-600 uppercase">Autonomous Orchestration</Text>
                          <Tag color="blue" className="rounded-md border-none font-black text-[8px] uppercase">Active</Tag>
                        </div>
                        <p className="text-[10px] text-slate-400 font-medium leading-relaxed">
                          AI autonomously manages candidate ranking, duplicate detection, and initial outreach based on historical success data.
                        </p>
                      </div>
                    </Card>

                    {/* Lifecyle Automation */}
                    <Card className={cn(
                      "rounded-3xl border-slate-100 shadow-soft-sm transition-all",
                      form.getFieldValue('is_workflow_controlled') ? "opacity-60 grayscale-[0.5]" : "hover:border-indigo-200"
                    )}>
                      <div className="flex items-center justify-between p-4 bg-slate-50/50 border-b border-slate-100">
                        <div className="flex items-center gap-3">
                          <Zap size={20} className="text-slate-600" />
                          <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Lifecycle Triggers</span>
                        </div>
                      </div>
                      <div className="p-5 space-y-5">
                        <div className="flex items-center justify-between">
                          <div>
                            <Text className="block text-[11px] font-bold text-slate-700 uppercase">Auto-Publish</Text>
                            <Text className="text-[9px] text-slate-400 font-medium">Post to boards after approval</Text>
                          </div>
                          <Form.Item name="auto_publish_enabled" valuePropName="checked" noStyle>
                            <Switch size="small" disabled={form.getFieldValue('is_workflow_controlled')} />
                          </Form.Item>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Text className="block text-[11px] font-bold text-slate-700 uppercase">Auto-Assign Recruiter</Text>
                            <Text className="text-[9px] text-slate-400 font-medium">Match to best internal recruiter</Text>
                          </div>
                          <Form.Item name="auto_assign_recruiter" valuePropName="checked" noStyle>
                            <Switch size="small" disabled={form.getFieldValue('is_workflow_controlled')} />
                          </Form.Item>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Text className="block text-[11px] font-bold text-slate-700 uppercase">Onboarding Sync</Text>
                            <Text className="text-[9px] text-slate-400 font-medium">Trigger HR flow on hire</Text>
                          </div>
                          <Form.Item name="onboarding_automation_enabled" valuePropName="checked" noStyle>
                            <Switch size="small" disabled={form.getFieldValue('is_workflow_controlled')} />
                          </Form.Item>
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              )}

              {/* STEP 9: Offer & Hiring Completion */}
              {currentStep === 8 && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <Title level={3} className="font-black text-slate-900 tracking-tight !m-0 uppercase tracking-widest leading-none">Offer & Hiring Foundations</Title>
                      <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] block mt-1">Set defaults for financial offers and job closure rules</Text>
                    </div>
                    {form.getFieldValue('is_workflow_controlled') && (
                      <Tag color="purple" className="m-0 border-none font-black text-[10px] uppercase px-3 py-1 rounded-lg">
                        Workflow Controlled
                      </Tag>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Offer Defaults */}
                    <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                      <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                        <DollarSign size={14} className="text-indigo-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Offer Foundations</span>
                      </div>
                      <div className="p-6 space-y-4">
                        <Row gutter={16}>
                          <Col span={10}>
                            <Form.Item name="offer_currency_default" label={<span className="text-[10px] font-black text-slate-400 uppercase">Currency</span>}>
                              <Select size="large" options={CURRENCIES} disabled={form.getFieldValue('is_workflow_controlled')} />
                            </Form.Item>
                          </Col>
                          <Col span={14}>
                            <Form.Item name="offer_salary_default" label={<span className="text-[10px] font-black text-slate-400 uppercase">Target Base Salary</span>}>
                              <InputNumber className="w-full" size="large" placeholder="e.g. 120000" disabled={form.getFieldValue('is_workflow_controlled')} />
                            </Form.Item>
                          </Col>
                        </Row>
                      </div>
                    </Card>

                    {/* Hiring Completion */}
                    <Card className="rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
                      <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                        <CheckCircle2 size={14} className="text-emerald-600" />
                        <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Hiring Completion</span>
                      </div>
                      <div className="p-6 space-y-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <Text className="block text-[11px] font-bold text-slate-700 uppercase">Auto-Close Job</Text>
                            <Text className="text-[9px] text-slate-400 font-medium">Close requisition when headcount is met</Text>
                          </div>
                          <Form.Item name="auto_close_on_headcount_met" valuePropName="checked" noStyle>
                            <Switch size="small" disabled={form.getFieldValue('is_workflow_controlled')} />
                          </Form.Item>
                        </div>

                        <Form.Item name="hiring_complete_action" label={<span className="text-[10px] font-black text-slate-400 uppercase">Completion Action</span>}>
                          <Select
                            size="large"
                            disabled={form.getFieldValue('is_workflow_controlled')}
                            options={[
                              { value: 'auto_onboarding', label: 'Trigger Onboarding Flow' },
                              { value: 'manual', label: 'Manual Archive Only' },
                              { value: 'archive', label: 'Archive Application' },
                            ]}
                          />
                        </Form.Item>
                      </div>
                    </Card>
                  </div>
                </div>
              )}

              {/* STEP 8: Final Review */}
              {currentStep === STEPS.length - 1 && (
                <div className="animate-in fade-in duration-700 space-y-8 text-center py-12">
                  <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-soft-lg"><CheckCircle2 size={40} /></div>
                  <Title level={2} className="font-black tracking-tight text-slate-900">Configuration Complete</Title>
                  <Paragraph className="text-slate-500 font-medium">Your job requisition is ready for launch. Review final metrics below.</Paragraph>
                  <Card className="text-left rounded-3xl border-slate-100 bg-slate-50/50 p-8 shadow-soft-sm">
                    <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-6">Launch Summary</Text>
                    <div className="grid grid-cols-2 gap-x-12 gap-y-6">
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Title</Text><Text className="font-bold text-slate-800 uppercase text-sm">{form.getFieldValue('title')}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Department</Text><Text className="font-bold text-slate-800 uppercase text-sm">{departments.find((d: any) => d.id === form.getFieldValue('department_id'))?.name || 'N/A'}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Headcount</Text><Text className="font-bold text-indigo-600 uppercase text-lg">{form.getFieldValue('headcount')}</Text></div>
                      <div className="flex flex-col"><Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Priority</Text><Tag className="w-fit font-black text-[9px] uppercase border-none bg-rose-50 text-rose-600">{form.getFieldValue('priority')}</Tag></div>
                      <div className="flex flex-col col-span-2">
                        <Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Locations</Text>
                        <div className="flex flex-wrap gap-2">
                          {selectedLocations.length > 0
                            ? selectedLocations.map(l => (
                                <Tag key={l.location_id} icon={<MapPin size={9} className="inline mr-0.5" />} color={l.is_primary ? 'blue' : 'default'} className="rounded-full">
                                  {l.location_name}{l.is_primary ? ' (Primary)' : ''}
                                </Tag>
                              ))
                            : <Text className="text-slate-400 text-sm">No locations added</Text>
                          }
                        </div>
                      </div>
                      <div className="flex flex-col col-span-2">
                        <Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Approval</Text>
                        {approvalRequired && approvalChain.length > 0 ? (
                          <div className="flex items-center gap-2 flex-wrap">
                            {approvalChain.filter(a => a.user_id).map((a, i) => (
                              <Tag key={i} color="orange" className="rounded-full">{a.name || 'Approver'}</Tag>
                            ))}
                          </div>
                        ) : (
                          <Tag color="green" className="w-fit rounded-full">No approval required — direct publish</Tag>
                        )}
                      </div>
                      <div className="flex flex-col col-span-2">
                        <Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Orchestration</Text>
                        {form.getFieldValue('workflow_enabled') ? (
                          <div className="flex items-center gap-2">
                            <Tag color="purple" className="rounded-full font-black">Workflow Master Active</Tag>
                            <Text className="text-xs font-medium text-slate-500 italic">End-to-end automation enabled</Text>
                          </div>
                        ) : (
                          <Tag color="default" className="w-fit rounded-full">Standard module control</Tag>
                        )}
                      </div>
                      <div className="flex flex-col col-span-2">
                        <Text className="text-[9px] font-black text-slate-400 uppercase mb-1">Prequalification</Text>
                        {prequalEnabled ? (
                          <div className="flex items-center gap-2 flex-wrap">
                            <Tag color="indigo" className="rounded-full font-black">Enabled</Tag>
                            {prequalFormId && (
                              <Tag color="blue" className="rounded-full">
                                {prequalForms.find(f => f.id === prequalFormId)?.name || 'Form selected'}
                              </Tag>
                            )}
                            {prequalThreshold !== null && (
                              <Tag color="default" className="rounded-full">Threshold: {prequalThreshold}%</Tag>
                            )}
                            <Tag color="green" className="rounded-full">Pass → {prequalPassAction.replace('_', ' ')}</Tag>
                            <Tag color="red" className="rounded-full">Fail → {prequalFailAction.replace('_', ' ')}</Tag>
                          </div>
                        ) : (
                          <Tag color="default" className="w-fit rounded-full">No prequalification gate</Tag>
                        )}
                      </div>
                      {form.getFieldValue('is_confidential') && (
                        <div className="flex flex-col col-span-2">
                          <Tag icon={<Lock size={10} className="inline mr-1" />} color="red" className="w-fit rounded-full font-bold">Confidential Job</Tag>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              <div className={cn("mt-12 pt-8 border-t border-slate-200 flex items-center justify-between", currentStep === STEPS.length - 1 ? "hidden" : "")}>
                <Button disabled={currentStep === 0} onClick={handleBack} className="h-12 px-8 rounded-2xl font-black text-[11px] uppercase tracking-widest border-slate-200 text-slate-500 hover:bg-slate-50"><ChevronLeft size={18} className="mr-2" /> Previous</Button>
                <Button type="primary" onClick={handleNext} className="bg-indigo-600 border-none h-12 px-10 rounded-2xl font-black text-[11px] uppercase tracking-widest shadow-indigo-100 shadow-lg">Save & Continue <ChevronRight size={18} className="ml-2" /></Button>
              </div>
            </Form>
          </div>
        </Content>

        <Sider width={320} className="bg-[#F8FAFC] border-l border-slate-200 hidden xl:block p-8" theme="light">
          <div className="sticky top-24 space-y-6">
            <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-soft-sm">
              <div className="flex justify-between items-center mb-2">
                <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Setup Progress</Text>
                <Text className="text-[10px] font-black text-indigo-600">{Math.round((currentStep / (STEPS.length - 1)) * 100)}%</Text>
              </div>
              <Progress percent={Math.round((currentStep / (STEPS.length - 1)) * 100)} strokeColor="#4f46e5" showInfo={false} size="small" />
            </div>
            
            <Alert 
              message={<span className="text-[10px] font-black uppercase text-indigo-700">Studio Intelligence</span>} 
              description={<p className="text-[11px] text-indigo-600/80 font-medium m-0 leading-relaxed">System recommends attaching an 'Engineering Standard' interview package for this role type.</p>} 
              type="info" 
              showIcon 
              icon={<BrainCircuit size={16} />} 
              className="rounded-2xl border-indigo-100 bg-indigo-50/50" 
            />
          </div>
        </Sider>
      </Layout>

      {/* ── JD Template Picker Modal ──────────────────────────────────────── */}
      <Modal
        open={templatePickerOpen}
        onCancel={() => setTemplatePickerOpen(false)}
        footer={null}
        title={
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-indigo-600" />
            <span className="font-bold">Select a JD Template</span>
          </div>
        }
        width={640}
      >
        <div className="mb-4">
          <Input
            placeholder="Search templates…"
            value={templateSearch}
            onChange={(e) => setTemplateSearch(e.target.value)}
            allowClear
          />
        </div>
        {jdTemplates.length === 0 ? (
          <div className="text-center py-10 text-slate-400">
            <Layers size={32} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium">No templates found.</p>
            <p className="text-xs mt-1">
              <a href="/jobs/templates" target="_blank" rel="noreferrer" className="text-indigo-500 hover:underline">
                Create templates in the JD Template Library →
              </a>
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {jdTemplates.map((tpl: any) => (
              <button
                key={tpl.id}
                onClick={() => applyTemplate(tpl)}
                className="w-full text-left p-4 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/40 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 group-hover:text-indigo-700 text-sm">{tpl.name}</span>
                  <span className="text-[10px] text-slate-400">{tpl.usage_count}× used</span>
                </div>
                {tpl.skills_suggested?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {tpl.skills_suggested.slice(0, 4).map((s: string) => (
                      <span key={s} className="text-[10px] bg-slate-100 text-slate-500 rounded px-1.5 py-0.5">{s}</span>
                    ))}
                    {tpl.skills_suggested.length > 4 && (
                      <span className="text-[10px] text-slate-400">+{tpl.skills_suggested.length - 4}</span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
