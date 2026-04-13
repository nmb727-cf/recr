import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Button,
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
  Calendar,
  Copy,
  Eye,
  Monitor,
  MonitorPlay,
  Plus,
  Settings2,
  ShieldCheck,
  Trash2,
  Video,
  Workflow,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Text } = Typography
const { TextArea } = Input

type VideoSubtype = 'prerecorded_video' | 'live_video'
type WizardStep = 'setup' | 'configuration' | 'evaluation' | 'routing'

type VideoDraft = {
  id: string | null
  name: string
  video_type: VideoSubtype
  duration_minutes: number
  description: string
  is_active: boolean
  configuration: {
    question_recording_enabled: boolean
    response_time_limit_seconds: number
    retry_limit: number
    interviewer_selection: string[]
    live_scheduling_mode: 'manual' | 'system_availability' | 'candidate_self'
    meeting_integration: string
  }
  evaluation: {
    scorecard_template_id: string
    pass_threshold: number
    reject_threshold: number
  }
  routing: {
    pass_action: 'move_to_next_stage' | 'manual_review'
    reject_action: 'reject'
    manual_review_enabled: boolean
    next_stage_name: string
  }
}

type InterviewVideoEngineProps = {
  embedded?: boolean
}

const WIZARD_STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'setup', label: '1. Setup', icon: Settings2 },
  { key: 'configuration', label: '2. Configuration', icon: Video },
  { key: 'evaluation', label: '3. Evaluation', icon: ShieldCheck },
  { key: 'routing', label: '4. Routing', icon: Workflow },
]

const VIDEO_TYPES: Array<{
  value: VideoSubtype
  label: string
  icon: React.ElementType
  guidance: {
    description: string
    defaultDuration: number
  }
}> = [
  {
    value: 'prerecorded_video',
    label: 'Prerecorded Video',
    icon: MonitorPlay,
    guidance: {
      description: 'Asynchronous recorded responses with question recording, time limits, and retry control.',
      defaultDuration: 20,
    },
  },
  {
    value: 'live_video',
    label: 'Live Video',
    icon: Monitor,
    guidance: {
      description: 'Synchronous live video interviews with interviewer assignment and scheduling shell.',
      defaultDuration: 45,
    },
  },
]

function createDraft(type: VideoSubtype = 'prerecorded_video'): VideoDraft {
  const config = VIDEO_TYPES.find((item) => item.value === type) || VIDEO_TYPES[0]
  return {
    id: null,
    name: '',
    video_type: config.value,
    duration_minutes: config.guidance.defaultDuration,
    description: '',
    is_active: true,
    configuration: {
      question_recording_enabled: config.value === 'prerecorded_video',
      response_time_limit_seconds: config.value === 'prerecorded_video' ? 120 : 0,
      retry_limit: config.value === 'prerecorded_video' ? 1 : 0,
      interviewer_selection: [],
      live_scheduling_mode: 'manual',
      meeting_integration: '',
    },
    evaluation: {
      scorecard_template_id: '',
      pass_threshold: 75,
      reject_threshold: 45,
    },
    routing: {
      pass_action: 'move_to_next_stage',
      reject_action: 'reject',
      manual_review_enabled: true,
      next_stage_name: 'next_interview_stage',
    },
  }
}

function parseTemplate(record: any): VideoDraft {
  const meta = record?.metadata?.video_interview || {}
  const setup = meta.setup || {}
  const configuration = meta.configuration || {}
  const evaluation = meta.evaluation || {}
  const routing = meta.routing || {}
  const type = (setup.video_type || record?.interview_type || 'prerecorded_video') as VideoSubtype
  const base = createDraft(type === 'live_video' ? 'live_video' : 'prerecorded_video')
  return {
    ...base,
    id: record.id,
    name: record.name || '',
    duration_minutes: record.duration_minutes || base.duration_minutes,
    description: record.description || '',
    is_active: record.is_active ?? true,
    configuration: {
      ...base.configuration,
      question_recording_enabled: configuration.question_recording_enabled ?? base.configuration.question_recording_enabled,
      response_time_limit_seconds: Number(configuration.response_time_limit_seconds ?? base.configuration.response_time_limit_seconds),
      retry_limit: Number(configuration.retry_limit ?? base.configuration.retry_limit),
      interviewer_selection: Array.isArray(configuration.interviewer_selection) ? configuration.interviewer_selection : [],
      live_scheduling_mode: configuration.live_scheduling_mode || 'manual',
      meeting_integration: configuration.meeting_integration || '',
    },
    evaluation: {
      scorecard_template_id: evaluation.scorecard_template_id || '',
      pass_threshold: Number(evaluation.pass_threshold ?? 75),
      reject_threshold: Number(evaluation.reject_threshold ?? 45),
    },
    routing: {
      pass_action: routing.pass_action || 'move_to_next_stage',
      reject_action: 'reject',
      manual_review_enabled: routing.manual_review_enabled ?? true,
      next_stage_name: routing.next_stage_name || 'next_interview_stage',
    },
  }
}

function serializeDraft(draft: VideoDraft, existing: any = {}) {
  return {
    name: draft.name,
    description: draft.description,
    interview_type: draft.video_type,
    duration_minutes: draft.duration_minutes,
    instructions: draft.description,
    scoring_type: draft.evaluation.scorecard_template_id ? 'criteria' : 'numeric',
    is_active: draft.is_active,
    metadata: {
      ...(existing.metadata || {}),
      video_interview: {
        setup: {
          video_type: draft.video_type,
        },
        configuration: draft.configuration,
        evaluation: draft.evaluation,
        routing: draft.routing,
        usage: existing.metadata?.video_interview?.usage || { linked_jobs: [], linked_flows: [], linked_stages: [] },
        integrations: {
          scheduling_engine: true,
          integration_engine: true,
          scorecard_engine: true,
          flow_engine: true,
        },
      },
    },
  }
}

export default function InterviewVideoEngine({ embedded = false }: InterviewVideoEngineProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const requestedType = new URLSearchParams(location.search).get('type')
  const initialType = useMemo<VideoSubtype>(() => requestedType === 'live_video' ? 'live_video' : 'prerecorded_video', [requestedType])

  const [isBuilderOpen, setIsBuilderOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [activeStep, setActiveStep] = useState<WizardStep>('setup')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draft, setDraft] = useState<VideoDraft>(createDraft(initialType))

  const { data: templatesData, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const { data: scorecardsData } = useApiQuery(['interview-scorecards'], () => interviewsApi.listScorecards())
  const { data: flowsData } = useApiQuery(['interview-flows-list'], () => interviewsApi.listFlows())

  const allTemplates = (templatesData as any)?.templates ?? []
  const scorecards = (scorecardsData as any)?.scorecards ?? []
  const flows = (flowsData as any)?.flows ?? []

  const videoTemplates = allTemplates.filter((template: any) => {
    const meta = template?.metadata || {}
    return meta?.video_interview || ['prerecorded_video', 'live_video'].includes(template?.interview_type)
  })

  const selectedTemplate = videoTemplates.find((template: any) => template.id === selectedTemplateId) ?? null
  const selectedScorecard = scorecards.find((scorecard: any) => scorecard.id === draft.evaluation.scorecard_template_id) ?? null
  const guidance = VIDEO_TYPES.find((item) => item.value === draft.video_type) || VIDEO_TYPES[0]
  const stepIndex = WIZARD_STEPS.findIndex((step) => step.key === activeStep)

  const usageMap = useMemo(() => {
    return new Map(
      videoTemplates.map((template: any) => {
        const meta = template?.metadata?.video_interview || {}
        const usage = meta.usage || {}
        const usageCount =
          (Array.isArray(usage.linked_jobs) ? usage.linked_jobs.length : 0) +
          (Array.isArray(usage.linked_flows) ? usage.linked_flows.length : 0) +
          (Array.isArray(usage.linked_stages) ? usage.linked_stages.length : 0) +
          flows.filter((flow: any) => (flow?.stages || []).some((stage: any) => stage?.template_id === template.id)).length
        return [template.id, usageCount]
      }),
    )
  }, [flows, videoTemplates])

  useEffect(() => {
    if (!selectedTemplate) return
    setDraft(parseTemplate(selectedTemplate))
  }, [selectedTemplate])

  useEffect(() => {
    if (!requestedType || isBuilderOpen) return
    const nextType = requestedType === 'live_video' ? 'live_video' : requestedType === 'prerecorded_video' ? 'prerecorded_video' : null
    if (!nextType) return
    setDraft(createDraft(nextType))
    setSelectedTemplateId(null)
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }, [requestedType, isBuilderOpen])

  const updateDraft = (updater: (current: VideoDraft) => VideoDraft) => {
    setDraft((current) => updater(current))
  }

  const openCreate = (type: VideoSubtype = initialType) => {
    setSelectedTemplateId(null)
    setDraft(createDraft(type))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const editTemplate = (template: any) => {
    setSelectedTemplateId(template.id)
    setDraft(parseTemplate(template))
    setActiveStep('setup')
    setIsBuilderOpen(true)
  }

  const duplicateTemplate = async (template: any) => {
    try {
      const next = parseTemplate(template)
      await interviewsApi.createTemplate(serializeDraft({ ...next, id: null, name: `${next.name || template.name} Copy`, is_active: false }, template))
      message.success('Video interview duplicated')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch {
      message.error('Failed to duplicate video interview')
    }
  }

  const archiveTemplate = async (template: any) => {
    try {
      await interviewsApi.updateTemplate(template.id, { ...template, is_active: false })
      message.success('Video interview archived')
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
    } catch {
      message.error('Failed to archive video interview')
    }
  }

  const saveDraft = async () => {
    setSaving(true)
    try {
      const payload = serializeDraft(draft, selectedTemplate)
      if (selectedTemplate?.id) {
        await interviewsApi.updateTemplate(selectedTemplate.id, payload)
        message.success('Video interview updated')
      } else {
        await interviewsApi.createTemplate(payload)
        message.success('Video interview created')
      }
      await queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setIsBuilderOpen(false)
      setSelectedTemplateId(null)
    } catch {
      message.error('Failed to save video interview')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Interview Name',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, record: any) => (
        <div>
          <p className="m-0 font-black text-slate-900">{value}</p>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{record.interview_type?.replace(/_/g, ' ')}</Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      render: (value: string) => <Tag color="blue">{value?.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Duration',
      dataIndex: 'duration_minutes',
      key: 'duration_minutes',
      render: (value: number) => `${value || 0}m`,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => <Tag color={value ? 'green' : 'default'}>{value ? 'Active' : 'Archived'}</Tag>,
    },
    {
      title: 'Usage Count',
      key: 'usage',
      render: (_, record: any) => usageMap.get(record.id) || 0,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (value: string) => value ? new Date(value).toLocaleDateString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: any) => (
        <div className="flex items-center gap-2">
          <Button size="small" onClick={() => editTemplate(record)}>Edit</Button>
          <Button size="small" onClick={() => duplicateTemplate(record)}>Duplicate</Button>
          <Button size="small" onClick={() => archiveTemplate(record)}>Archive</Button>
          <Button size="small" onClick={() => { setSelectedTemplateId(record.id); setPreviewOpen(true) }}>Preview</Button>
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
            <Text className="block text-[10px] font-black uppercase tracking-[0.24em] text-indigo-500">ICC-VIDEO-INTERVIEW-ENGINE-01</Text>
            <h2 className="m-0 mt-1 text-2xl font-black text-slate-900">Video Interviews</h2>
            <Text className="text-slate-500">Dedicated engine for prerecorded and live video interviews.</Text>
          </div>
          <Button type="primary" icon={<Plus size={14} />} onClick={() => openCreate()}>Create Video Interview</Button>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm">
          <Table rowKey="id" columns={columns} dataSource={videoTemplates} loading={isLoading} pagination={{ pageSize: 8, hideOnSinglePage: true }} />
        </div>

        <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={720} title="Video Interview Preview">
          {selectedTemplate ? (
            <div className="space-y-4">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Template</Text>
                <p className="mt-1 mb-0 text-lg font-black text-slate-900">{selectedTemplate.name}</p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Type</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.interview_type?.replace(/_/g, ' ')}</Text>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Duration</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.duration_minutes || 0}m</Text>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                  <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</Text>
                  <Text className="font-bold text-slate-800">{selectedTemplate.metadata?.video_interview?.evaluation?.scorecard_template_id ? 'Linked' : 'Not linked'}</Text>
                </div>
              </div>
            </div>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a video interview first" />
          )}
        </Modal>
      </div>
    )
  }

  return (
    <div className={containerClass}>
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => {
            setIsBuilderOpen(false)
            setSelectedTemplateId(null)
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
        >
          <ArrowLeft size={14} />
          Back to Video Interviews
        </button>
        <Button type="primary" onClick={saveDraft} loading={saving}>Save Video Interview</Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[240px_minmax(0,1fr)_320px] gap-5 items-start">
        <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-soft-sm sticky top-0">
          <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3">Wizard Steps</Text>
          <div className="space-y-2">
            {WIZARD_STEPS.map((step) => (
              <button
                key={step.key}
                onClick={() => setActiveStep(step.key)}
                className={cn(
                  'w-full rounded-xl border px-3 py-3 text-left transition',
                  activeStep === step.key ? 'border-indigo-200 bg-indigo-50' : 'border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50',
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center', activeStep === step.key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-400')}>
                    <step.icon size={16} />
                  </div>
                  <Text className="font-bold text-slate-800">{step.label.replace(/^\d+\.\s*/, '')}</Text>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-soft-sm">
          {activeStep === 'setup' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 1</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Setup</h3>
                <Text className="text-slate-500">{guidance.guidance.description}</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Interview Name</Text>
                  <Input value={draft.name} onChange={(event) => updateDraft((current) => ({ ...current, name: event.target.value }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Video Type</Text>
                  <Select
                    value={draft.video_type}
                    options={VIDEO_TYPES.map((item) => ({ value: item.value, label: item.label }))}
                    onChange={(value) => updateDraft((current) => ({ ...createDraft(value), id: current.id, name: current.name, description: current.description, evaluation: current.evaluation, routing: current.routing }))}
                  />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Duration</Text>
                  <InputNumber min={10} max={90} className="w-full" value={draft.duration_minutes} onChange={(value) => updateDraft((current) => ({ ...current, duration_minutes: Number(value || 0) }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Status</Text>
                  <Select value={draft.is_active ? 'active' : 'archived'} options={[{ value: 'active', label: 'Active' }, { value: 'archived', label: 'Archived' }]} onChange={(value) => updateDraft((current) => ({ ...current, is_active: value === 'active' }))} />
                </div>
                <div className="md:col-span-2">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Description</Text>
                  <TextArea rows={4} value={draft.description} onChange={(event) => updateDraft((current) => ({ ...current, description: event.target.value }))} />
                </div>
              </div>
            </div>
          )}

          {activeStep === 'configuration' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 2</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Configuration</h3>
                <Text className="text-slate-500">
                  {draft.video_type === 'prerecorded_video'
                    ? 'Configure question recording, response time limits, and retry rules.'
                    : 'Configure interviewer assignment, live scheduling, and meeting integration.'}
                </Text>
              </div>

              {draft.video_type === 'prerecorded_video' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-3 flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                    <div>
                      <Text className="block font-bold text-slate-800">Question Recording</Text>
                      <Text className="text-slate-500">Enable recorded candidate responses against prompted questions.</Text>
                    </div>
                    <Select value={draft.configuration.question_recording_enabled ? 'yes' : 'no'} options={[{ value: 'yes', label: 'Enabled' }, { value: 'no', label: 'Disabled' }]} onChange={(value) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, question_recording_enabled: value === 'yes' } }))} className="w-28" />
                  </div>
                  <div>
                    <Text className="block mb-1 text-xs font-bold text-slate-600">Response Time Limit</Text>
                    <InputNumber min={30} max={600} className="w-full" value={draft.configuration.response_time_limit_seconds} onChange={(value) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, response_time_limit_seconds: Number(value || 0) } }))} />
                  </div>
                  <div>
                    <Text className="block mb-1 text-xs font-bold text-slate-600">Retry Limit</Text>
                    <InputNumber min={0} max={5} className="w-full" value={draft.configuration.retry_limit} onChange={(value) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, retry_limit: Number(value || 0) } }))} />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-3">
                    <Text className="block mb-1 text-xs font-bold text-slate-600">Interviewer Selection</Text>
                    <Select
                      mode="tags"
                      value={draft.configuration.interviewer_selection}
                      onChange={(value) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, interviewer_selection: value } }))}
                      placeholder="Add interviewers"
                    />
                  </div>
                  <div>
                    <Text className="block mb-1 text-xs font-bold text-slate-600">Live Scheduling</Text>
                    <Select
                      value={draft.configuration.live_scheduling_mode}
                      options={[
                        { value: 'manual', label: 'Manual' },
                        { value: 'system_availability', label: 'System Availability' },
                        { value: 'candidate_self', label: 'Candidate Self Scheduling' },
                      ]}
                      onChange={(value) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, live_scheduling_mode: value } }))}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Text className="block mb-1 text-xs font-bold text-slate-600">Meeting Integration Shell</Text>
                    <Input value={draft.configuration.meeting_integration} onChange={(event) => updateDraft((current) => ({ ...current, configuration: { ...current.configuration, meeting_integration: event.target.value } }))} placeholder="zoom / google_meet / teams / native" />
                  </div>
                </div>
              )}
            </div>
          )}

          {activeStep === 'evaluation' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 3</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Evaluation</h3>
                <Text className="text-slate-500">Attach a scorecard and define pass or reject thresholds.</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-3">
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Scorecard Template</Text>
                  <Select allowClear value={draft.evaluation.scorecard_template_id || undefined} options={scorecards.map((scorecard: any) => ({ value: scorecard.id, label: scorecard.name }))} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, scorecard_template_id: value || '' } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Pass Threshold</Text>
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.pass_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, pass_threshold: Number(value || 0) } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Reject Threshold</Text>
                  <InputNumber min={0} max={100} className="w-full" value={draft.evaluation.reject_threshold} onChange={(value) => updateDraft((current) => ({ ...current, evaluation: { ...current.evaluation, reject_threshold: Number(value || 0) } }))} />
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Linked Scorecard</Text>
                <Text className="font-bold text-slate-800">{selectedScorecard?.name || 'No scorecard attached'}</Text>
              </div>
            </div>
          )}

          {activeStep === 'routing' && (
            <div className="space-y-5">
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Step 4</Text>
                <h3 className="m-0 mt-1 text-xl font-black text-slate-900">Routing</h3>
                <Text className="text-slate-500">Control next-stage movement, reject behavior, and manual review routing.</Text>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Pass Action</Text>
                  <Select value={draft.routing.pass_action} options={[{ value: 'move_to_next_stage', label: 'Move to Next Stage' }, { value: 'manual_review', label: 'Manual Review' }]} onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, pass_action: value } }))} />
                </div>
                <div>
                  <Text className="block mb-1 text-xs font-bold text-slate-600">Next Stage</Text>
                  <Input value={draft.routing.next_stage_name} onChange={(event) => updateDraft((current) => ({ ...current, routing: { ...current.routing, next_stage_name: event.target.value } }))} />
                </div>
                <div className="md:col-span-2 flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                  <div>
                    <Text className="block font-bold text-slate-800">Manual Review Enabled</Text>
                    <Text className="text-slate-500">Borderline candidates can be routed into review before the next stage.</Text>
                  </div>
                  <Select value={draft.routing.manual_review_enabled ? 'yes' : 'no'} options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} onChange={(value) => updateDraft((current) => ({ ...current, routing: { ...current.routing, manual_review_enabled: value === 'yes' } }))} className="w-24" />
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-5">
            <Button disabled={stepIndex === 0} onClick={() => setActiveStep(WIZARD_STEPS[Math.max(0, stepIndex - 1)].key)}>Back</Button>
            <div className="flex items-center gap-2">
              <Button onClick={() => setPreviewOpen(true)}>Preview</Button>
              <Button type="primary" disabled={stepIndex === WIZARD_STEPS.length - 1} onClick={() => setActiveStep(WIZARD_STEPS[Math.min(WIZARD_STEPS.length - 1, stepIndex + 1)].key)}>Next</Button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-soft-sm sticky top-0 space-y-5">
          <div>
            <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Video Summary</Text>
            <p className="mt-2 mb-0 text-lg font-black text-slate-900">{draft.name || 'Untitled Video Interview'}</p>
            <p className="mt-1 mb-0 text-sm text-slate-500">{draft.video_type.replace(/_/g, ' ')} · {draft.duration_minutes}m</p>
          </div>
          <div className="rounded-xl bg-slate-950 p-4 text-white">
            <Text className="block text-[10px] font-black uppercase tracking-widest text-white/50">Runtime Preview</Text>
            <p className="mt-3 mb-0 text-lg font-black">{draft.name || 'Video Interview'}</p>
            <p className="mt-1 mb-0 text-sm text-white/70">
              {draft.video_type === 'prerecorded_video'
                ? `${draft.configuration.response_time_limit_seconds}s per response · ${draft.configuration.retry_limit} retries`
                : `${draft.configuration.live_scheduling_mode.replace(/_/g, ' ')} · ${draft.configuration.meeting_integration || 'integration pending'}`}
            </p>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Scorecard</Text>
              <Text className="font-bold text-slate-800">{selectedScorecard?.name || 'No scorecard linked'}</Text>
            </div>
            <div className="rounded-xl border border-slate-100 p-4">
              <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-400">Routing</Text>
              <Text className="font-bold text-slate-800">{draft.routing.pass_action.replace(/_/g, ' ')}</Text>
              <Text className="block text-slate-500">Next stage: {draft.routing.next_stage_name}</Text>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
