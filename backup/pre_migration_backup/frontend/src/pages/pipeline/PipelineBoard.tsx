import { useState, useEffect, useMemo, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Card, Tag, Typography, Spin, Empty, Button,
  Avatar, message, Modal,
  Tabs, Table, Timeline, Badge, Row, Col, Divider, Form, Input as AntInput, DatePicker, InputNumber, Tooltip, Select, Drawer, Space, Radio
} from 'antd'
import {
  Clock,
  Star,
  X,
  ArrowRight,
  Search,
  ChevronRight,
  Mail,
  Phone,
  FileText,
  CheckCircle,
  User,
  Users,
  ExternalLink,
  Plus,
  Calendar,
  DollarSign,
  AlertCircle,
  TrendingUp,
  Layout as LayoutIcon,
  Filter,
  ChevronLeft,
  MoreHorizontal,
  ArrowUpDown,
  Maximize2,
  Minimize2,
  AlertTriangle,
  Zap,
  Briefcase,
  Pin,
  LayoutGrid,
  ChevronDown,
  Layers,
  Eye,
  ShieldCheck,
  BrainCircuit,
  Workflow,
  UserCheck,
  Gavel
} from 'lucide-react'
import dayjs from 'dayjs'
import isToday from 'dayjs/plugin/isToday'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/store/authStore'

import { CustomizeView } from '@/components/common/CustomizeView'
import { useUserPreferences } from '@/hooks/useUserPreferences'

dayjs.extend(relativeTime)
dayjs.extend(isToday)

import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from 'react-beautiful-dnd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { pipelineApi } from '@/api/pipeline'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import { interviewsApi } from '@/api/interviews'
import { agenciesApi } from '@/api/agencies'
import { isJobOwner } from '@/utils/permissions'
import type {
  PipelineData, PipelineStageData as PipelineStageRecord, Application,
  JobRequisition, Candidate, CandidateDetail
} from '@/types'
import { cn } from '@/utils/cn'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { HiringAIBrainDashboard } from '../jobs/JobCommandCenterView'
import WorkflowStatusPanel from '@/components/workflow/WorkflowStatusPanel'

const { Text, Title } = Typography
const { TextArea } = AntInput

type PipelineContext = 'single' | 'my_live' | 'team_live' | 'all_live'

// ─── Sub-components ─────────────────────────────────────────────────────────

const InterviewScheduleModal = ({ 
  visible, 
  onCancel, 
  applicationId, 
  onSuccess 
}: { 
  visible: boolean, 
  onCancel: () => void, 
  applicationId: string,
  onSuccess: () => void
}) => {
  const { t } = useTranslation(['pipeline', 'common'])
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (values: any) => interviewsApi.create({
      application_id: applicationId,
      title: values.title,
      interview_type: values.interview_type,
      scheduled_at: values.scheduled_at.toISOString(),
      duration_minutes: values.duration_minutes,
      interview_round: values.interview_round,
    }),
    onSuccess: () => {
      message.success(t('pipeline:messages.interview_scheduled', 'Interview scheduled'))
      queryClient.invalidateQueries({ queryKey: ['app-interviews', applicationId] })
      onSuccess()
      onCancel()
      form.resetFields()
    },
    onError: (err: any) => {
      message.error(err.response?.data?.message || t('pipeline:messages.interview_schedule_failed', 'Failed to schedule interview'))
    }
  })

  return (
    <Modal
      title={t('pipeline:actions.schedule_interview', 'Schedule Interview')}
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={mutation.isPending}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={{ duration_minutes: 45, interview_round: 1 }}>
        <Form.Item name="title" label={t('pipeline:fields.interview_title', 'Interview Title')} rules={[{ required: true }]}>
          <AntInput placeholder={t('pipeline:placeholders.interview_title', 'e.g. Technical Round 1')} />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="interview_type" label={t('pipeline:fields.type', 'Type')} rules={[{ required: true }]}>
              <Select options={[
                { value: 'technical', label: 'Technical' },
                { value: 'culture', label: 'Culture' },
                { value: 'management', label: 'Management' },
                { value: 'screening', label: 'Screening' }
              ]} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="interview_round" label={t('pipeline:fields.round', 'Round')} rules={[{ required: true }]}>
              <InputNumber className="w-full" min={1} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="scheduled_at" label={t('pipeline:fields.date_time', 'Date & Time')} rules={[{ required: true }]}>
              <DatePicker showTime className="w-full" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="duration_minutes" label={t('pipeline:fields.duration_mins', 'Duration (mins)')} rules={[{ required: true }]}>
              <InputNumber className="w-full" min={15} step={15} />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  )
}

const MakeOfferModal = ({ 
  visible, 
  onCancel, 
  applicationId, 
  onSuccess 
}: { 
  visible: boolean, 
  onCancel: () => void, 
  applicationId: string,
  onSuccess: () => void
}) => {
  const { t } = useTranslation(['pipeline', 'common'])
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (values: any) =>
      pipelineApi.makeOffer(applicationId, {
        offer_amount: Number(values.offer_amount || 0),
        currency: values.currency || 'INR',
        joining_date: values.joining_date?.format('YYYY-MM-DD'),
        notes: values.notes || '',
      }),
    onSuccess: () => {
      message.success(t('pipeline:messages.offer_created', 'Offer created and sent'))
      queryClient.invalidateQueries({ queryKey: ['application', 'full', applicationId] })
      onSuccess()
      onCancel()
      form.resetFields()
    },
    onError: (err: any) => {
      message.error(err.response?.data?.message || t('pipeline:messages.offer_failed', 'Failed to make offer'))
    }
  })

  return (
    <Modal
      title={t('pipeline:actions.create_offer', 'Create Offer')}
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={mutation.isPending}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={{ currency: 'INR' }}>
        <Row gutter={16}>
          <Col span={16}>
            <Form.Item name="offer_amount" label={t('pipeline:fields.annual_ctc', 'Annual CTC')} rules={[{ required: true }]}>
              <InputNumber className="w-full" formatter={value => `₹ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="currency" label={t('pipeline:fields.currency', 'Currency')}>
              <Select options={[{ value: 'INR', label: 'INR' }, { value: 'USD', label: 'USD' }]} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="joining_date" label={t('pipeline:fields.joining_date', 'Expected Joining Date')} rules={[{ required: true }]}>
          <DatePicker className="w-full" />
        </Form.Item>
        <Form.Item
          name="notes"
          label={t('pipeline:fields.offer_notes', 'Offer Notes')}
          rules={[{ required: true, message: 'A note is required for stage change' }]}
        >
          <TextArea rows={3} placeholder={t('pipeline:placeholders.offer_notes', 'Add any special conditions...')} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

const ApplicationDetailPanel = ({ applicationId, onClose, onRefresh, requisitionStages, isOwner }: { applicationId: string, onClose: () => void, onRefresh: () => void, requisitionStages: any[], isOwner: boolean }) => {
  const { t } = useTranslation(['pipeline', 'common'])
  const navigate = useNavigate()
  const [interviewModalVisible, setInterviewModalVisible] = useState(false)
  const [offerModalVisible, setOfferModalVisible] = useState(false)
  const [stageModalOpen, setStageModalOpen] = useState(false)
  const [stageAction, setStageAction] = useState<'move' | 'shortlist' | 'reject' | 'note' | 'hold' | null>(null)
  const [targetStageId, setTargetStageId] = useState<string | null>(null)
  const [targetStageLabel, setTargetStageLabel] = useState<string>('')
  const [stageNote, setStageNote] = useState('')
  const [stageSubmitting, setStageSubmitting] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['application', 'full', applicationId],
    () => pipelineApi.getApplication(applicationId),
    { enabled: !!applicationId }
  )

  const application = (data as any)?.application as Application
  const stageHistory = (data as any)?.stage_history || []
  
  const { data: candidateData } = useApiQuery(
    ['candidate', 'full', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id),
    { enabled: !!application?.candidate_id }
  )

  const candidate = (candidateData as any)?.candidate as CandidateDetail

  const { data: interviewsData, isLoading: interviewsLoading } = useApiQuery(
    ['app-interviews', applicationId],
    () => interviewsApi.list({ application_id: applicationId }),
    { enabled: !!applicationId }
  )

  const user = useAuthStore((s) => s.user)

  const handleMoveStage = async (stageId: string) => {
    const stage = requisitionStages.find((s: any) => s.stage.id === stageId)?.stage
    setTargetStageId(stageId)
    setTargetStageLabel(stage?.name || 'Target Stage')
    setStageAction('move')
    setStageNote('')
    setStageModalOpen(true)
  }

  const handleShortlist = async () => {
    setTargetStageId(null)
    setTargetStageLabel('Shortlisted')
    setStageAction('shortlist')
    setStageNote('')
    setStageModalOpen(true)
  }

  const handleReject = async () => {
    setTargetStageId(null)
    setTargetStageLabel('Rejected')
    setStageAction('reject')
    setStageNote('')
    setStageModalOpen(true)
  }

  const handleHold = () => {
    setTargetStageId(null)
    setTargetStageLabel('Placed on Hold')
    setStageAction('hold')
    setStageNote('')
    setStageModalOpen(true)
  }

  const handleAddNote = () => {
    setTargetStageId(null)
    setTargetStageLabel('Add Internal Note')
    setStageAction('note')
    setStageNote('')
    setStageModalOpen(true)
  }

  const handleAssignOwner = async (ownerId: string) => {
    try {
      await pipelineApi.updateApplication(applicationId, { 
        metadata: { ...application.metadata, assigned_owner_id: ownerId } 
      })
      message.success('Owner assigned successfully')
      refetch()
    } catch (err) {
      message.error('Failed to assign owner')
    }
  }

  const confirmStageAction = async () => {
    if (!stageAction || (!stageNote.trim() && stageAction !== 'note')) return
    setStageSubmitting(true)
    try {
      if (stageAction === 'move' && targetStageId) {
        await pipelineApi.moveStage(applicationId, targetStageId, stageNote.trim())
        message.success(t('pipeline:messages.application_moved', 'Application moved'))
      } else if (stageAction === 'shortlist') {
        await pipelineApi.shortlist(applicationId, stageNote.trim())
        message.success(t('pipeline:messages.candidate_shortlisted', 'Candidate shortlisted'))
      } else if (stageAction === 'reject') {
        await pipelineApi.reject(applicationId, stageNote.trim())
        message.success(t('pipeline:messages.candidate_rejected', 'Candidate rejected'))
      } else if (stageAction === 'hold') {
        await pipelineApi.updateApplication(applicationId, { status: 'on_hold', metadata: { ...application.metadata, hold_reason: stageNote.trim() } })
        message.success('Candidate placed on hold')
      } else if (stageAction === 'note') {
        await pipelineApi.moveStage(applicationId, application.current_stage_id || '', stageNote.trim())
        message.success('Internal note added')
      }
      setStageModalOpen(false)
      setStageAction(null)
      setTargetStageId(null)
      setTargetStageLabel('')
      setStageNote('')
      onRefresh()
      refetch()
    } catch (err: any) {
      message.error(err?.response?.data?.message || t('pipeline:messages.application_move_failed', 'Failed to perform action'))
    } finally {
      setStageSubmitting(false)
    }
  }

  if (isLoading) return <div className="p-20 text-center"><Spin size="large" /></div>
  if (!application) return <Empty description={t('pipeline:empty.application_not_found', 'Application not found')} />

  const lastUpdate = dayjs(application.updated_at)
  const ageHours = dayjs().diff(lastUpdate, 'hour')
  const timeInStage = lastUpdate.fromNow(true)
  const isOverdue = ageHours > 48
  const interviewList = Array.isArray((interviewsData as any)?.interviews) ? (interviewsData as any).interviews : []
  const upcomingInterview = interviewList.find((i: any) => i.status === 'scheduled')

  const tabItems = [
    {
      key: 'workbench',
      label: 'Workbench Dashboard',
      children: (
        <div className="p-6 space-y-6">
          {/* ── 1. Pipeline Actions Section ──────────────────────────────── */}
          <Card size="small" className="rounded-2xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Workflow size={14} className="text-indigo-600" />
                <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Pipeline Orchestration</span>
              </div>
              <Tag className="m-0 border-none bg-indigo-100 text-indigo-600 font-black text-[9px] uppercase px-2 rounded-md">
                {application.status}
              </Tag>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">Current Stage</Text>
                  <Select 
                    className="w-full workbench-select"
                    placeholder="Move to Stage..."
                    value={application.current_stage_id}
                    onChange={handleMoveStage}
                    options={requisitionStages.map((s: any) => ({ value: s.stage.id, label: s.stage.name }))}
                    disabled={!isOwner}
                  />
                </div>
                <div>
                  <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">Decision Owner</Text>
                  <Select
                    className="w-full workbench-select"
                    placeholder="Assign Owner..."
                    defaultValue={application.metadata?.assigned_owner_id}
                    onChange={handleAssignOwner}
                    options={[{ label: 'Assign to Me', value: user?.id || '' }, { label: 'Unassigned', value: '' }]}
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  block 
                  type="primary"
                  className="h-9 rounded-xl font-black text-[10px] uppercase tracking-widest bg-blue-600 border-none shadow-sm shadow-blue-100" 
                  icon={<Gavel size={14} />}
                  onClick={() => navigate(`/hiring-decisions?applicationId=${applicationId}`)}
                >
                  Hiring Decision
                </Button>
                <Button block className="h-9 rounded-xl font-black text-[10px] uppercase tracking-widest border-slate-200 text-slate-600" onClick={handleHold}>Place on Hold</Button>
              </div>
              <Button block icon={<FileText size={14} />} className="h-9 rounded-xl font-black text-[10px] uppercase tracking-widest border-slate-200 text-slate-600" onClick={handleAddNote}>Record Note</Button>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-6">
            {/* ── 2. Automation Section ────────────────────────────────── */}
            <Card size="small" className="rounded-2xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
              <div className="px-4 py-3 bg-indigo-50/50 border-b border-indigo-100 flex items-center gap-2">
                <BrainCircuit size={14} className="text-indigo-600" />
                <span className="text-[10px] font-black uppercase text-indigo-700 tracking-widest">Automation</span>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Text className="text-[10px] font-bold text-slate-500 uppercase">Decision Mode</Text>
                  <Tag className="m-0 border-none bg-emerald-50 text-emerald-600 font-black text-[8px] uppercase px-1.5 rounded">Real-time</Tag>
                </div>
                <div className="flex items-start gap-2 text-indigo-600">
                  <Zap size={12} fill="currentColor" className="mt-0.5 shrink-0" />
                  <Text className="text-[9px] font-black uppercase tracking-tight leading-tight">
                    {application.metadata?.automation_triggered ? 'Auto-moved via engine' : 'Awaiting trigger events'}
                  </Text>
                </div>
              </div>
            </Card>

            {/* ── 3. SLA Section ────────────────────────────────────────── */}
            <Card size="small" className="rounded-2xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
              <div className="px-4 py-3 bg-rose-50/50 border-b border-rose-100 flex items-center gap-2">
                <ShieldCheck size={14} className="text-rose-600" />
                <span className="text-[10px] font-black uppercase text-rose-700 tracking-widest">SLA Health</span>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex flex-col">
                  <Text className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Time in Stage</Text>
                  <Text className={cn("text-sm font-black uppercase", isOverdue ? "text-rose-600" : "text-slate-700")}>{timeInStage}</Text>
                </div>
                <div className="flex items-center gap-2">
                  <div className={cn("h-1.5 w-1.5 rounded-full", isOverdue ? "bg-rose-500 animate-pulse" : "bg-emerald-500")} />
                  <Text className="text-[9px] font-black uppercase">{isOverdue ? 'Overdue Breach' : 'Velocity: Healthy'}</Text>
                </div>
              </div>
            </Card>
          </div>

          <WorkflowStatusPanel
            entityId={application.id}
            entityType="application"
            title="Workflow Status"
            maxTimelineItems={6}
          />

          {/* ── 4. Interview Section ────────────────────────────────────── */}
          <Card size="small" className="rounded-2xl border-slate-100 shadow-soft-sm overflow-hidden" styles={{ body: { padding: 0 } }}>
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar size={14} className="text-blue-600" />
                <span className="text-[10px] font-black uppercase text-slate-600 tracking-widest">Interview Workbench</span>
              </div>
              {upcomingInterview && <Badge status="processing" text={<span className="text-[9px] font-black text-blue-600 uppercase">Live Round</span>} />}
            </div>
            <div className="p-4">
              {upcomingInterview ? (
                <div className="p-3 bg-blue-50 rounded-xl border border-blue-100 flex items-center justify-between">
                  <div className="min-w-0">
                    <Text className="block text-[11px] font-black text-blue-700 uppercase truncate">{upcomingInterview.title}</Text>
                    <Text className="text-[10px] font-bold text-blue-500 uppercase">{dayjs(upcomingInterview.scheduled_at).format('MMM D · HH:mm')}</Text>
                  </div>
                  <Button size="small" type="primary" className="bg-blue-600 border-none font-black text-[9px] uppercase tracking-widest rounded-lg h-8 px-4 shadow-sm">Trigger Now</Button>
                </div>
              ) : (
                <div className="text-center py-6 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <Text className="text-[10px] font-bold text-slate-400 uppercase block mb-3">No rounds scheduled for this candidate</Text>
                  <Button icon={<Plus size={14} />} className="h-9 rounded-xl font-black text-[10px] uppercase tracking-widest border-slate-200 text-indigo-600 bg-white" onClick={() => setInterviewModalVisible(true)}>Schedule Interview</Button>
                </div>
              )}
            </div>
          </Card>

          {/* Timeline Summary */}
          <div>
            <Title level={5} className="!text-[10px] !font-black !uppercase !tracking-widest !text-slate-400 !mb-4 ml-1">Recent Activity</Title>
            <Timeline 
              className="ml-2"
              items={[
                ...stageHistory.slice(0, 3).map((h: any) => ({
                  dot: <div className="h-4 w-4 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100"><CheckCircle className="h-2 w-2" /></div>,
                  children: (
                    <div className="pb-4">
                      <Text className="block font-bold text-slate-800 text-[11px] uppercase tracking-tight">Moved to {h.to_status?.replace('_', ' ')}</Text>
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">{dayjs(h.moved_at).fromNow()}</p>
                    </div>
                  )
                }))
              ]}
            />
          </div>
        </div>
      )
    },
    {
      key: 'profile',
      label: 'Full Profile',
      children: (
        <div className="p-6">
          <div className="mb-8">
            <Title level={5} className="!text-[10px] !font-black !uppercase !tracking-widest !text-slate-400 !mb-4">Candidate Summary</Title>
            <Text className="text-slate-600 leading-relaxed block bg-slate-50/50 p-4 rounded-2xl border border-slate-100">
              {candidate?.profile?.summary || 'No professional summary available for this candidate.'}
            </Text>
          </div>
          <Card title={<span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Match Analysis</span>} bordered={false} className="shadow-soft-sm mb-8 rounded-2xl">
            <div className="flex items-center gap-8">
              <div className="text-center">
                <div className="text-4xl font-black text-emerald-600 tracking-tight">{application.match_score || 0}%</div>
                <div className="text-[9px] font-bold text-slate-400 uppercase mt-1 tracking-widest">AI Score</div>
              </div>
              <div className="h-14 w-[1px] bg-slate-100" />
              <div className="flex-1">
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Candidate demonstrates strong alignment with core technical requirements and culture fit. High proficiency in role-specific skills noted.
                </p>
              </div>
            </div>
          </Card>
          <div className="space-y-4">
            <Title level={5} className="!text-[10px] !font-black !uppercase !tracking-widest !text-slate-400 !m-0">Contact & Source</Title>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <Text className="text-[9px] font-bold text-slate-400 uppercase block mb-1">Email</Text>
                <Text className="text-xs font-bold text-slate-700">{candidate?.email || 'N/A'}</Text>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <Text className="text-[9px] font-bold text-slate-400 uppercase block mb-1">Source</Text>
                <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-bold text-[9px] uppercase px-2">{application.source || 'Direct'}</Tag>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ]

  return (
    <div className="flex flex-col h-full bg-white shadow-2xl">
      {/* ── 1. QUICK DECISION BAR (TOP) ────────────────────────────────── */}
      <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between shrink-0 sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Avatar size={48} className="bg-indigo-600 text-white font-black border-2 border-slate-700 text-xl">
              {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
            </Avatar>
            <div className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full bg-emerald-500 border-2 border-slate-900 shadow-sm" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-black text-white uppercase tracking-tight truncate m-0">{candidate?.first_name} {candidate?.last_name}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <Tag className="m-0 border-none bg-emerald-500/10 text-emerald-400 font-black text-[8px] uppercase px-1.5 rounded">
                {application.match_score || 0}% Match
              </Tag>
              <Text className="text-[9px] font-bold text-slate-500 uppercase tracking-widest truncate max-w-[150px]">{candidate?.current_title || 'No Title'}</Text>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            onClick={handleShortlist}
            className="bg-emerald-600 border-none text-white font-black text-[9px] uppercase tracking-widest h-9 px-4 rounded-xl hover:bg-emerald-500 transition-colors"
            icon={<Star size={12} fill="white" />}
            disabled={!isOwner || application.status === 'shortlisted'}
          >
            Shortlist
          </Button>
          <Button 
            danger 
            onClick={handleReject}
            className="bg-rose-600 border-none text-white font-black text-[9px] uppercase tracking-widest h-9 px-4 rounded-xl hover:bg-rose-500 transition-colors"
            icon={<X size={12} />}
            disabled={!isOwner}
          >
            Reject
          </Button>
          <Divider type="vertical" className="h-6 border-slate-700 mx-1" />
          <Button icon={<X size={18} />} onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-xl border-slate-700 bg-slate-800 text-slate-400 hover:text-white" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar bg-white">
        <Tabs 
          defaultActiveKey="workbench" 
          items={tabItems} 
          className="workbench-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9', height: '44px' }}
        />
      </div>

      {/* Action Modals */}
      <InterviewScheduleModal visible={interviewModalVisible} onCancel={() => setInterviewModalVisible(false)} applicationId={applicationId} onSuccess={() => { onRefresh(); refetch(); }} />
      <MakeOfferModal visible={offerModalVisible} onCancel={() => setOfferModalVisible(false)} applicationId={applicationId} onSuccess={() => { onRefresh(); refetch(); }} />
      
      <Modal
        title={<div className="flex items-center gap-2"><Zap size={18} className="text-indigo-600" /><span className="font-black uppercase tracking-tight text-slate-800">{stageAction === 'note' ? 'Record Interaction' : 'Confirm Workbench Decision'}</span></div>}
        open={stageModalOpen}
        onCancel={() => setStageModalOpen(false)}
        onOk={confirmStageAction}
        okText="Confirm Decision"
        confirmLoading={stageSubmitting}
        okButtonProps={{ disabled: !stageNote.trim() && stageAction !== 'note', className: 'bg-indigo-600 font-black uppercase text-[10px] tracking-widest h-10 px-6 rounded-xl border-none' }}
        className="rounded-3xl overflow-hidden"
      >
        <div className="space-y-4 pt-4">
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center justify-between">
            <div>
              <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-1">Proposed Outcome</Text>
              <Text className="text-sm font-black text-slate-800 uppercase">{targetStageLabel}</Text>
            </div>
            {stageAction === 'move' && <ChevronRight size={16} className="text-slate-300" />}
          </div>
          <div>
            <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-2 ml-1">Professional Context / Reason</Text>
            <TextArea rows={4} value={stageNote} onChange={(e) => setStageNote(e.target.value)} placeholder="Provide rationale for this decision..." className="rounded-2xl border-slate-200 p-4" />
          </div>
        </div>
      </Modal>
    </div>
  )
}

interface PipelineStageData {
  stage: {
    id: string
    name: string
    stage_order: number
    action_deadline_hours?: number
  }
  applications: Application[]
  stats: {
    count: number
    overdue: number
    newToday: number
  }
}

// ─── Main PipelineBoard ──────────────────────────────────────────────────────

export default function PipelineBoard({ jobId: externalJobId, isSubView = false }: { jobId?: string, isSubView?: boolean }) {
  const { t } = useTranslation(['pipeline', 'common'])
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  
  const { pages } = useUserPreferences()
  const pagePrefs = pages['pipeline'] || { hiddenColumns: [], hiddenSections: [], density: 'comfortable' }
  const isCompact = pagePrefs.density === 'compact'
  
  const isStatsHidden = pagePrefs.hiddenSections.includes('stats')
  const isBrainHidden = pagePrefs.hiddenSections.includes('brain')
  const isSwitcherHidden = pagePrefs.hiddenSections.includes('switcher')

  // Workspace Context State
  const [pipelineContext, setPipelineContext] = useState<PipelineContext>('single')
  const [selectedJobId, setSelectedJobId] = useState<string>(externalJobId || searchParams.get('job') || '')
  const [viewMode, setViewMode] = useState<'board' | 'list'>('board')

  // Sync state when prop changes
  useEffect(() => {
    if (externalJobId) {
      setSelectedJobId(externalJobId)
      setPipelineContext('single')
    }
  }, [externalJobId])
  
  const [boardState, setBoardState] = useState<Record<string, PipelineStageData>>({})
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null)
  
  // Operational State
  const [candidateSearch, setCandidateSearch] = useState('')
  const viewDensity = pagePrefs.density as 'comfortable' | 'compact'
  const [sortBy, setSortBy] = useState<'match' | 'recent' | 'aging'>('match')

  const [boardStageModalOpen, setBoardStageModalOpen] = useState(false)
  const [boardStageNote, setBoardStageNote] = useState('')
  const [boardStageSubmitting, setBoardStageSubmitting] = useState(false)
  const [pendingBoardMove, setPendingBoardMove] = useState<{
    applicationId: string
    currentStageLabel: string
    targetStageId: string
    targetStageLabel: string
  } | null>(null)

  const user = useAuthStore((s) => s.user)

  // Fetch all live requisitions for the switcher
  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['jobs-live'],
    () => requisitionsApi.list({ status: 'active' })
  )
  const liveJobs: JobRequisition[] =
    (jobsData as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []

  // Fetch specific requisition (only for single job context)
  const { data: requisitionData } = useApiQuery(
    ['requisition', 'minimal', selectedJobId],
    () => requisitionsApi.get(selectedJobId),
    { enabled: pipelineContext === 'single' && !!selectedJobId }
  )
  const requisition = (requisitionData as any)?.requisition as JobRequisition
  const isOwner = isJobOwner(user, requisition)

  // Multi-context application fetching
  const { data: appsData, isLoading: appsLoading, refetch: refetchApps } = useApiQuery(
    ['pipeline-apps', pipelineContext, selectedJobId],
    () => {
      if (pipelineContext === 'single' && selectedJobId) {
        return pipelineApi.getPipeline(selectedJobId) as any
      }
      // For multi-job context, we fetch list of applications and build grouping
      return pipelineApi.listApplications({ status: 'active' }) as any
    },
    { enabled: pipelineContext !== 'single' || !!selectedJobId }
  )
  const { data: agencyDashboardData } = useApiQuery(
    ['agency-intelligence-pipeline'],
    () => agenciesApi.getDashboardIntelligence(),
    { retry: false, refetchOnWindowFocus: false, staleTime: 60_000 }
  )
  const pipelineAgencyIntelligence = (agencyDashboardData as any)?.intelligence?.pipeline ?? (agencyDashboardData as any)?.data?.intelligence?.pipeline

  // Fetch all candidates for name lookup
  const { data: candidatesData } = useApiQuery(
    ['candidates', 'all'],
    () => candidatesApi.list()
  )
  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as { candidates: Candidate[] } | undefined)?.candidates ?? []).map((c) => [c.id, c])
  )

  const jobMap = useMemo(() => new Map<string, JobRequisition>(liveJobs.map(j => [j.id, j])), [liveJobs])

  // Process data based on context
  const processedStages = useMemo(() => {
    if (pipelineContext === 'single' && (appsData as any)?.pipeline) {
      const board = (appsData as any).pipeline as Record<string, PipelineStageRecord>
      return Object.values(board).filter(s => s && s.stage).sort((a, b) => a.stage.stage_order - b.stage.stage_order).map(s => {
        let apps = s.applications || []
        if (candidateSearch) {
          apps = apps.filter(app => {
            const cand = candidateMap.get(app.candidate_id)
            return cand?.full_name?.toLowerCase().includes(candidateSearch.toLowerCase()) || 
                   cand?.current_title?.toLowerCase().includes(candidateSearch.toLowerCase())
          })
        }
        const overdue = apps.filter((app: any) => dayjs().diff(dayjs(app.updated_at), 'hour') > 48).length
        const newToday = apps.filter((app: any) => dayjs(app.created_at).isToday()).length
        return { ...s, applications: apps, stats: { count: apps.length, overdue, newToday } }
      })
    }

    // Multi-job context processing
    const allApps = (appsData as any)?.applications || (appsData as any)?.data?.applications || []
    const filteredApps = allApps.filter((app: Application) => {
      const jId = app.requisition_id || (app as any).job_id
      const job = jobMap.get(jId)
      if (!job) return false
      if (pipelineContext === 'my_live') return job.created_by === user?.id
      if (pipelineContext === 'all_live') return true
      return true
    }).filter((app: Application) => {
      if (!candidateSearch) return true
      const cand = candidateMap.get(app.candidate_id)
      return cand?.full_name?.toLowerCase().includes(candidateSearch.toLowerCase()) || 
             cand?.current_title?.toLowerCase().includes(candidateSearch.toLowerCase())
    })

    // Standard columns for multi-view
    const standardStages = [
      { id: 'applied', name: 'Applied', type: 'applied' },
      { id: 'screening', name: 'Screening', type: 'screening' },
      { id: 'interview', name: 'Interview', type: 'interview' },
      { id: 'offer', name: 'Offer', type: 'offer' },
      { id: 'hired', name: 'Hired', type: 'joined' }
    ]

    return standardStages.map(st => {
      const apps = filteredApps.filter((app: any) => {
        const status = (app.status || 'applied').toLowerCase()
        const stageName = (app.stage_name || '').toLowerCase()
        return status.includes(st.type) || status === st.id || 
               stageName.includes(st.type) || (st.id === 'hired' && (status === 'joined' || status === 'hired'))
      })
      const overdue = apps.filter((app: any) => dayjs().diff(dayjs(app.updated_at), 'hour') > 48).length
      const newToday = apps.filter((app: any) => dayjs(app.created_at).isToday()).length
      return {
        stage: st,
        applications: apps,
        stats: { count: apps.length, overdue, newToday }
      }
    })
  }, [appsData, pipelineContext, candidateSearch, candidateMap, jobMap, user])

  const workspaceStats = useMemo(() => {
    let total = 0
    let bottleneck: any = null
    let maxCount = -1
    let needsReview = 0
    let interviewPending = 0
    let offerPending = 0
    let overdue = 0
    let recent = 0
    let stalled = 0
    let automationCount = 0
    
    // SLA Breakdown
    let slaOnTrack = 0
    let slaDueSoon = 0 // Within 12h of breach
    let slaOverdue = 0
    let slaEscalated = 0

    processedStages.forEach((s: any) => {
      if (!s || !s.stage) return
      total += s.stats.count
      if (s.stats.count > maxCount) {
        maxCount = s.stats.count
        bottleneck = s.stage.name
      }
      
      const stageType = s.stage.type || s.stage.id
      if (stageType === 'applied' || stageType === 'screening') needsReview += s.stats.count
      if (stageType === 'interview') interviewPending += s.stats.count
      if (stageType === 'offer' || stageType === 'offer_extended') offerPending += s.stats.count
      
      s.applications.forEach((app: any) => {
        const lastUpdate = dayjs(app.updated_at)
        const ageHours = dayjs().diff(lastUpdate, 'hour')
        const ageDays = dayjs().diff(lastUpdate, 'day')
        
        // Use stage-specific deadline or default to 48h
        const deadlineHours = s.stage.action_deadline_hours || 48
        
        if (ageHours > deadlineHours) {
          slaOverdue++
          overdue++
          if (ageHours > deadlineHours * 2) slaEscalated++
        } else if (ageHours > deadlineHours - 12) {
          slaDueSoon++
        } else {
          slaOnTrack++
        }

        if (ageDays > 4) stalled++
        if (dayjs(app.created_at).isToday()) recent++
        
        // Automation detection
        if (app.metadata?.automation_triggered || app.metadata?.workflow_mode === 'automated') {
          automationCount++
        }
      })
    })
    
    return { 
      total, 
      bottleneck, 
      needsReview, 
      interviewPending, 
      offerPending, 
      overdue, 
      recent,
      stalled,
      automationCount,
      sla: {
        onTrack: slaOnTrack,
        dueSoon: slaDueSoon,
        overdue: slaOverdue,
        escalated: slaEscalated
      }
    }
  }, [processedStages])

  const [showBrainDashboard, setShowBrainDashboard] = useState(false)

  useEffect(() => {
    if (selectedJobId && pipelineContext === 'single') {
      setSearchParams({ job: selectedJobId }, { replace: true })
    }
  }, [selectedJobId, setSearchParams, pipelineContext])

  const handleDragEnd = async (result: DropResult) => {
    if (pipelineContext !== 'single' || !isOwner) {
      message.warning(t('pipeline:ownership.owner_only'))
      return
    }
    const { source, destination, draggableId } = result
    if (!destination || source.droppableId === destination.droppableId) return

    setPendingBoardMove({
      applicationId: draggableId,
      currentStageLabel: 'Current Stage',
      targetStageId: destination.droppableId,
      targetStageLabel: 'Target Stage',
    })
    setBoardStageNote('')
    setBoardStageModalOpen(true)
  }

  const confirmBoardMove = async () => {
    if (!pendingBoardMove || !boardStageNote.trim()) return
    setBoardStageSubmitting(true)
    try {
      await pipelineApi.moveStage(
        pendingBoardMove.applicationId,
        pendingBoardMove.targetStageId,
        boardStageNote.trim(),
      )
      message.success(t('pipeline:messages.application_moved', 'Application moved'))
      setBoardStageModalOpen(false)
      setPendingBoardMove(null)
      setBoardStageNote('')
      refetchApps()
    } catch (err: any) {
      message.error(err?.response?.data?.message || t('pipeline:messages.application_move_failed', 'Failed to move application'))
    } finally {
      setBoardStageSubmitting(false)
    }
  }

  return (
    <div className={cn(
      "flex flex-1 flex-col overflow-hidden bg-[#F8FAFC] h-full",
      !isSubView && "-m-6 h-[calc(100vh-56px)]"
    )}>
      
      {/* ── Pipeline Action Center Header ───────────────────────────────────── */}
      <div className="px-6 py-3 border-b border-slate-200/60 bg-white z-30 shadow-soft-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            {!isSubView && (
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm">
                <Layers size={20} />
              </div>
            )}
            <div>
               <div className="flex items-center gap-3">
                 <h1 className="text-sm font-black text-slate-900 uppercase tracking-widest leading-none">
                   {isSubView ? 'Pipeline View' : 'Pipeline Action Center'}
                 </h1>
                 {selectedJobId && !isBrainHidden && (
                   <button 
                     onClick={() => setShowBrainDashboard(!showBrainDashboard)}
                     className={cn(
                       "flex items-center gap-1.5 px-2 py-0.5 rounded-lg border transition-all animate-in fade-in zoom-in duration-500",
                       showBrainDashboard ? "bg-indigo-600 border-indigo-600 text-white" : "bg-indigo-50 border-indigo-100 text-indigo-600 hover:bg-indigo-100"
                     )}
                   >
                     <BrainCircuit size={12} />
                     <span className="text-[10px] font-black uppercase tracking-widest">Hiring Brain</span>
                   </button>
                 )}
               </div>
               {!isSwitcherHidden && (
                 <>
                   {pipelineContext === 'single' && requisition && (
                     <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.12em] bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100/50">{requisition.job_ref_id || 'REF-ID'}</span>
                        <div className="h-1 w-1 rounded-full bg-slate-300" />
                        <span className="text-[11px] font-bold text-slate-500 uppercase truncate max-w-[250px]">{requisition.title}</span>
                        {requisition.workflow_enabled && (
                          <>
                            <div className="h-1 w-1 rounded-full bg-slate-300" />
                            <Tag color="purple" className="m-0 border-none font-black text-[9px] uppercase px-2 rounded-md leading-relaxed">
                              Workflow Master Governing
                            </Tag>
                          </>
                        )}
                        <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-black text-[9px] uppercase rounded-full px-2 ml-1">
                           {requisition.status || 'Active'}
                        </Tag>
                     </div>
                   )}
                   {pipelineContext !== 'single' && !isSubView && (
                     <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                           {pipelineContext === 'my_live' ? 'My Live Pipeline' : 'Team Live Pipeline'}
                        </span>
                     </div>
                   )}
                 </>
               )}
            </div>
          </div>

          <div className="flex items-center gap-3">
             <CustomizeView 
               pageId="pipeline"
               columns={[]}
               sections={[
                 { id: 'switcher', label: 'Context Switcher' },
                 { id: 'stats', label: 'Pipeline Metrics' },
                 { id: 'brain', label: 'Hiring Brain Dashboard' },
               ]}
             />
             <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1 border border-slate-200/50">
               <button 
                 onClick={() => setViewMode('board')}
                 className={cn(
                   "px-3 py-1.5 text-[9px] font-black uppercase tracking-widest transition-all rounded-md flex items-center gap-1.5",
                   viewMode === 'board' ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
                 )}
               >
                 <LayoutGrid size={12} /> Board
               </button>
               <button 
                 onClick={() => setViewMode('list')}
                 className={cn(
                   "px-3 py-1.5 text-[9px] font-black uppercase tracking-widest transition-all rounded-md flex items-center gap-1.5",
                   viewMode === 'list' ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
                 )}
               >
                 <Briefcase size={12} /> List
               </button>
             </div>
             <Button type="primary" size="small" className="h-9 bg-indigo-600 border-none rounded-xl font-black text-[10px] uppercase tracking-widest px-5 shadow-indigo-100 shadow-lg">
                Bulk Actions
             </Button>
          </div>
        </div>

        {/* Top Strip: Metrics */}
        {!isStatsHidden && (
          <div className="grid grid-cols-6 gap-3 pt-1">
             {[
               { label: 'Total Active', value: workspaceStats.total, color: 'slate' },
               { label: 'Needs Review', value: workspaceStats.needsReview, color: 'blue' },
               { label: 'Interviewing', value: workspaceStats.interviewPending, color: 'purple' },
               { label: 'Active Offers', value: workspaceStats.offerPending, color: 'amber' },
               { label: 'Overdue > 48h', value: workspaceStats.overdue, color: 'rose' },
               { label: 'Bottleneck', value: workspaceStats.bottleneck || 'None', color: 'indigo', isText: true },
             ].map((stat, i) => (
               <div key={i} className="px-3 py-2 bg-slate-50/50 rounded-xl border border-slate-100 flex flex-col justify-center">
                  <Text className="text-[8px] font-black text-slate-400 uppercase tracking-tighter mb-1">{stat.label}</Text>
                  <Text className={cn("text-base font-black leading-none", stat.isText ? "text-[10px] truncate uppercase" : `text-${stat.color}-600`)}>
                    {stat.value}
                  </Text>
               </div>
             ))}
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {showBrainDashboard && selectedJobId && (
          <div className="px-6 py-4 bg-white border-b border-slate-200 animate-in slide-in-from-top duration-500">
            <HiringAIBrainDashboard jobId={selectedJobId} />
          </div>
        )}

        {/* ── Intelligence Row ────────────────────────────────────────────────── */}
        <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-5 gap-4 shrink-0 bg-[#F8FAFC]">
          <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-soft-sm hover:border-indigo-200 transition-colors">
             <div className="flex items-center gap-2 mb-3">
                <Zap size={14} className="text-amber-500 fill-amber-500" />
                <div className="flex-1">
                  <Text className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Urgent Actions</Text>
                </div>
                <Badge count={workspaceStats.needsReview + workspaceStats.overdue} size="small" style={{ backgroundColor: '#4f46e5', fontSize: '9px', fontWeight: 'black' }} />
             </div>
             <div className="space-y-2">
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Review Pending</span>
                   <span className="text-slate-700">{workspaceStats.needsReview}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Interview Tasks</span>
                   <span className="text-slate-700">{workspaceStats.interviewPending}</span>
                </div>
             </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-soft-sm hover:border-rose-200 transition-colors">
             <div className="flex items-center gap-2 mb-3">
                <ShieldCheck size={14} className="text-rose-500" />
                <div className="flex-1">
                  <Text className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">SLA Engine</Text>
                </div>
                <Badge status={workspaceStats.sla.overdue > 0 ? 'error' : 'processing'} />
             </div>
             <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                   <span>On Track</span>
                   <span className="text-emerald-600 font-black">{workspaceStats.sla.onTrack}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                   <span>Overdue</span>
                   <span className="text-rose-600 font-black">{workspaceStats.sla.overdue}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                   <span>Due Soon</span>
                   <span className="text-amber-600 font-black">{workspaceStats.sla.dueSoon}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                   <span>Escalated</span>
                   <span className="text-rose-800 font-black">{workspaceStats.sla.escalated}</span>
                </div>
             </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-soft-sm hover:border-amber-200 transition-colors">
             <div className="flex items-center gap-2 mb-3">
                <Clock size={14} className="text-amber-500" />
                <div className="flex-1">
                  <Text className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Stalled Leads</Text>
                </div>
                <Badge count={workspaceStats.stalled} size="small" style={{ backgroundColor: '#f59e0b', fontSize: '9px', fontWeight: 'black' }} />
             </div>
             <div className="space-y-2">
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Inactive {'>'} 4 Days</span>
                   <span className="text-amber-600">{workspaceStats.stalled}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Recent Momentum</span>
                   <span className="text-emerald-600">+{workspaceStats.recent}</span>
                </div>
             </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-soft-sm hover:border-indigo-200 transition-colors">
             <div className="flex items-center gap-2 mb-3">
                <BrainCircuit size={14} className="text-indigo-600" />
                <div className="flex-1">
                  <Text className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Automation</Text>
                </div>
                <div className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
             </div>
             <div className="flex items-center justify-between">
                <div>
                   <Text className="text-2xl font-black text-slate-800 leading-none">{workspaceStats.automationCount}</Text>
                   <Text className="text-[9px] font-black text-slate-400 uppercase block mt-1.5">Auto-Movements</Text>
                </div>
                <div className="text-right">
                   <div className="flex items-center gap-1 justify-end">
                      <CheckCircle size={12} className="text-emerald-500" />
                      <Text className="text-[11px] font-black text-emerald-600 uppercase tracking-tighter">Active</Text>
                   </div>
                   <Text className="text-[9px] font-black text-slate-400 uppercase block mt-0.5">Decision Engine</Text>
                </div>
             </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-soft-sm hover:border-blue-200 transition-colors">
             <div className="flex items-center gap-2 mb-3">
                <Users size={14} className="text-blue-600" />
                <div className="flex-1">
                  <Text className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Agency Intelligence</Text>
                </div>
                <Badge status="processing" />
             </div>
             <div className="space-y-2">
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Agency Share</span>
                   <span className="text-blue-600">{Number(pipelineAgencyIntelligence?.candidate_source_intelligence?.agency_share || 0).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Success Rate</span>
                   <span className="text-emerald-600">{Number(pipelineAgencyIntelligence?.agency_contribution?.[0]?.success_rate || 0).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase">
                   <span>Top Agency</span>
                   <span className="truncate pl-2 text-slate-700">{pipelineAgencyIntelligence?.agency_contribution?.[0]?.agency_name || 'None'}</span>
                </div>
             </div>
          </div>
        </div>

        {/* ── Main Workspace Area ─────────────────────────────────────────────── */}
        <div className="flex-1 overflow-hidden">
          {appsLoading ? (
            <div className="h-full flex items-center justify-center bg-white/50 backdrop-blur-sm z-50"><Spin size="large" /></div>
          ) : viewMode === 'list' ? (
            <PipelineListView 
              processedStages={processedStages} 
              onSelect={(id) => setSelectedAppId(id)} 
              candidateMap={candidateMap}
              jobMap={jobMap}
            />
          ) : (
            <div className="h-full overflow-x-auto px-6 pb-6 scrollbar-thin">
              <DragDropContext onDragEnd={handleDragEnd}>
                <div className="flex gap-5 h-full items-start min-w-max">
                  {processedStages.map((stageData: any) => (
                    <div key={stageData.stage.id} className="flex flex-col w-[280px] shrink-0 h-full max-h-full bg-slate-200/20 rounded-3xl border border-slate-200/50 overflow-hidden group/stage shadow-sm">
                      <div className="px-4 py-3.5 bg-white border-b border-slate-100 shrink-0 flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className={cn("h-2.5 w-2.5 rounded-full shadow-sm", 
                            stageData.stage.id === 'applied' ? 'bg-blue-500' :
                            stageData.stage.id === 'interview' ? 'bg-purple-500' :
                            stageData.stage.id === 'offer' ? 'bg-amber-500' :
                            stageData.stage.id === 'hired' ? 'bg-emerald-500' : 'bg-indigo-600'
                          )} />
                          <Text className="font-black text-slate-800 text-[10px] uppercase tracking-[0.12em]">{stageData.stage.name}</Text>
                        </div>
                        <Badge count={stageData.stats.count} showZero size="small" style={{ backgroundColor: '#f8fafc', color: '#64748b', boxShadow: 'none', fontWeight: '900', fontSize: '10px', border: '1px solid #e2e8f0' }} />
                      </div>

                      <Droppable droppableId={stageData.stage.id}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={cn(
                              "flex-1 overflow-y-auto p-3 space-y-3 transition-colors custom-scrollbar", 
                              snapshot.isDraggingOver ? "bg-indigo-50/40" : ""
                            )}
                          >
                            {stageData.applications.length === 0 ? (
                              <div className="h-32 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-white/40 group-hover/stage:border-indigo-200 transition-colors">
                                 <Plus size={20} className="text-slate-300 mb-2" />
                                 <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center px-4">Drag candidates here to move stage</Text>
                              </div>
                            ) : (
                              stageData.applications.map((app: any, i: number) => (
                                <Draggable key={app.id} draggableId={app.id} index={i} isDragDisabled={!isOwner}>
                                  {(p, s) => (
                                    <CandidateCard p={p} s={s} app={app} candidateMap={candidateMap} viewDensity={viewDensity} onSelect={() => setSelectedAppId(app.id)} />
                                  )}
                                </Draggable>
                              ))
                            )}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  ))}
                </div>
              </DragDropContext>
            </div>
          )}
        </div>
      </div>

      {/* ── Candidate Intel Drawer ───────────────────────────────────────────── */}
      <Drawer
        open={!!selectedAppId}
        onClose={() => setSelectedAppId(null)}
        width={840}
        styles={{ body: { padding: 0 } }}
        closable={false}
        className="pipeline-detail-drawer"
      >
        {selectedAppId && (
          <ApplicationDetailPanel
            applicationId={selectedAppId}
            onClose={() => setSelectedAppId(null)}
            onRefresh={() => {
              refetchApps()
              setSelectedAppId(selectedAppId)
            }}
            requisitionStages={processedStages}
            isOwner={isOwner}
          />
        )}
      </Drawer>

      <Modal
        title={t('pipeline:actions.confirm_stage_change', 'Confirm Stage Change')}
        open={boardStageModalOpen}
        onCancel={() => {
          setBoardStageModalOpen(false)
          setPendingBoardMove(null)
          setBoardStageNote('')
        }}
        onOk={confirmBoardMove}
        okText={t('common:actions.confirm', 'Confirm')}
        confirmLoading={boardStageSubmitting}
        okButtonProps={{ disabled: !boardStageNote.trim() }}
        className="rounded-3xl overflow-hidden"
      >
        <div className="space-y-4 pt-4">
          <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Target Stage</p>
              <p className="text-sm font-bold text-blue-600">{pendingBoardMove?.targetStageLabel || '—'}</p>
            </div>
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 ml-1">Mandatory Note</p>
            <TextArea
              rows={4}
              value={boardStageNote}
              onChange={(e) => setBoardStageNote(e.target.value)}
              placeholder="Provide context for this movement..."
              className="rounded-2xl"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

function PipelineListView({ processedStages, onSelect, candidateMap, jobMap }: any) {
  const { t } = useTranslation(['pipeline', 'common'])
  
  const allApps = useMemo(() => {
    return processedStages.flatMap((s: any) => s.applications.map((a: any) => ({
      ...a,
      stageName: s.stage.name,
      stageId: s.stage.id
    })))
  }, [processedStages])

  const columns = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_: any, app: any) => {
        const candidate = candidateMap.get(app.candidate_id)
        return (
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => onSelect(app.id)}>
            <Avatar size={32} className="bg-slate-100 text-indigo-600 font-black text-[10px]">
              {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
            </Avatar>
            <div>
              <Text className="block font-black text-slate-800 text-[11px] uppercase tracking-tight">
                {candidate?.first_name} {candidate?.last_name}
              </Text>
              <Text className="text-[10px] text-slate-400 font-bold uppercase">{candidate?.current_title || 'No Title'}</Text>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Current Stage',
      dataIndex: 'stageName',
      key: 'stage',
      render: (name: string) => (
        <Tag className="m-0 border-none bg-indigo-50 text-indigo-600 font-black text-[9px] uppercase px-2 rounded-md">
          {name}
        </Tag>
      )
    },
    {
      title: 'Job Requisition',
      dataIndex: 'requisition_id',
      key: 'job',
      render: (jobId: string) => {
        const job = jobMap.get(jobId)
        return <Text className="text-[10px] font-bold text-slate-600 uppercase truncate max-w-[150px] block">{job?.title || 'Unknown'}</Text>
      }
    },
    {
      title: 'Match Score',
      dataIndex: 'match_score',
      key: 'match',
      align: 'center' as const,
      render: (score: number) => (
        <Text className={cn("text-[11px] font-black", score > 80 ? "text-emerald-600" : "text-slate-600")}>
          {score || 0}%
        </Text>
      )
    },
    {
      title: 'Last Activity',
      dataIndex: 'updated_at',
      key: 'activity',
      render: (date: string) => {
        const isOverdue = dayjs().diff(dayjs(date), 'hour') > 48
        return (
          <div className="flex flex-col">
            <Text className={cn("text-[10px] font-bold", isOverdue ? "text-rose-500" : "text-slate-600")}>
              {dayjs(date).fromNow()}
            </Text>
            <Text className="text-[8px] text-slate-400 font-black uppercase tracking-wider">
              {dayjs(date).format('MMM D')}
            </Text>
          </div>
        )
      }
    },
    {
      title: '',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, app: any) => (
        <Button 
          type="text" 
          size="small" 
          icon={<ChevronRight size={14} className="text-slate-300" />} 
          onClick={() => onSelect(app.id)}
        />
      )
    }
  ]

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <Table 
        dataSource={allApps} 
        columns={columns} 
        rowKey="id" 
        pagination={{ pageSize: 20, position: ['bottomCenter'] }}
        className="modern-table-dense"
        size="small"
      />
    </div>
  )
}

function CandidateCard({ p, s, app, candidateMap, viewDensity, isDragDisabled, onSelect }: any) {
  const candidate = candidateMap.get(app.candidate_id)
  const isOverdue = dayjs().diff(dayjs(app.updated_at), 'hour') > 48
  const isNew = dayjs(app.created_at).isToday()
  const isStalled = dayjs().diff(dayjs(app.updated_at), 'day') > 4
  
  const getRecommendation = () => {
    if (app.status === 'applied' || app.status === 'screening') return 'Review Candidate'
    if (app.status === 'interview') return 'Schedule Next Round'
    if (app.status === 'offer_extended') return 'Follow up on Offer'
    if (isStalled) return 'Nudge Recruiter'
    return 'View Details'
  }

  return (
    <div
      ref={p?.innerRef}
      {...p?.draggableProps}
      {...p?.dragHandleProps}
      onClick={onSelect}
      className={cn(
        "bg-white rounded-2xl border transition-all cursor-pointer relative group",
        viewDensity === 'comfortable' ? "p-4" : "p-3",
        s?.isDragging ? "rotate-2 scale-105 shadow-2xl z-50 ring-2 ring-indigo-500/30" : "border-slate-200/60 hover:border-indigo-300 hover:shadow-lg",
        isDragDisabled && "cursor-default",
        isOverdue && "border-l-4 border-l-rose-400",
        isStalled && !isOverdue && "border-l-4 border-l-amber-400"
      )}
    >
      {isNew && (
        <div className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-indigo-600 shadow-[0_0_8px_rgba(79,70,229,0.6)]" />
      )}

      <div className="flex items-start gap-3">
        <Avatar 
          size={viewDensity === 'comfortable' ? 36 : 32} 
          className="bg-slate-50 text-indigo-600 font-black border-none shrink-0 text-[10px] shadow-sm"
        >
          {candidate?.first_name?.charAt(0) || '?'}{candidate?.last_name?.charAt(0) || ''}
        </Avatar>
        
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <Text className="block font-black text-slate-900 text-[11px] leading-tight truncate uppercase tracking-tight">
              {candidate?.full_name || candidate?.first_name ? `${candidate.first_name} ${candidate.last_name || ''}` : 'Unknown Candidate'}
            </Text>
            {app.metadata?.automation_triggered && <Zap size={10} className="text-indigo-500 shrink-0" />}
          </div>
          <div className="flex items-center gap-1">
            <Text className="text-[10px] text-slate-400 font-bold truncate block leading-tight uppercase tracking-tighter">
              {candidate?.current_title || 'No Title'}
            </Text>
            {isStalled && <Tooltip title="Stalled > 4 days"><AlertTriangle size={10} className="text-amber-500" /></Tooltip>}
          </div>
        </div>
      </div>

      <div className={cn("flex items-center justify-between border-t border-slate-50 pt-2.5", viewDensity === 'comfortable' ? "mt-4" : "mt-3")}>
        <div className="flex items-center gap-2">
          {app.metadata?.assigned_owner_id && (
            <Tooltip title="Recruiter Assigned">
              <UserCheck size={10} className="text-emerald-500" />
            </Tooltip>
          )}
          <div className={cn(
            "text-[10px] font-black px-1.5 py-0.5 rounded",
            (app.match_score || 0) > 80 ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-500"
          )}>
            {app.match_score || 0}%
          </div>
          <div className="flex items-center gap-1 opacity-60">
             <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-bold text-[8px] uppercase px-1.5 rounded">
                {app.source || 'Direct'}
             </Tag>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          <Clock className={cn("h-3 w-3", isOverdue ? "text-rose-400" : "text-slate-300")} />
          <span className={cn("text-[9px] font-black uppercase tracking-wider", isOverdue ? "text-rose-500" : "text-slate-400")}>
            {app.updated_at ? dayjs(app.updated_at).fromNow(true) : '—'}
          </span>
        </div>
      </div>

      {/* Recommendation Badge */}
      <div className="mt-2 flex items-center gap-1.5">
        <div className="h-1 w-1 rounded-full bg-indigo-400" />
        <Text className="text-[8px] font-black text-indigo-500 uppercase tracking-widest">{getRecommendation()}</Text>
      </div>

      {/* Quick Actions on Hover */}
      <div className="absolute inset-0 bg-white/95 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3 z-10 px-4">
         <Tooltip title="View Intel">
            <Button shape="circle" icon={<Eye size={14} />} className="border-slate-200 text-slate-500 shadow-sm" onClick={(e) => { e.stopPropagation(); onSelect(); }} />
         </Tooltip>
         <Tooltip title="Schedule">
            <Button shape="circle" icon={<Calendar size={14} />} className="border-indigo-100 text-indigo-600 bg-indigo-50 shadow-sm" />
         </Tooltip>
         <Tooltip title="Reject">
            <Button shape="circle" icon={<X size={14} />} className="border-rose-100 text-rose-600 bg-rose-50 shadow-sm" />
         </Tooltip>
         <Button type="primary" size="small" className="bg-indigo-600 border-none rounded-lg font-black text-[9px] uppercase tracking-widest h-8 px-3 shadow-indigo-100 shadow-lg flex items-center gap-1">
            Move <ChevronRight size={10} />
         </Button>
      </div>
    </div>
  )
}
