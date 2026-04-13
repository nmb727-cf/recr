import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert, Avatar, Badge, Button, Empty, Form, Input, Modal,
  Select, Spin, Tabs, Tag, Typography, message,
  Tooltip, Divider, Switch, Timeline, Space
} from 'antd'
import {
  Activity, BadgeCheck, BellDot, Bot, BrainCircuit, Briefcase,
  Building2, Calendar, ChevronRight, ClipboardList, Clock3,
  Database, ExternalLink, FileDown, FileText, Flag,
  History, Link2, Mail, MapPin, MessageSquare,
  Paperclip, Phone, Plus, RefreshCw, Search, Send, Share2,
  Sparkles, Star, Target, Trash2, User, Users, Workflow, ShieldCheck,
  ChevronLeft, Play, Target as TargetIcon, CheckCircle2, X, Settings2, Video, Layers, MousePointerClick, TrendingUp, ArrowUpRight,
  XCircle, Notebook, Zap, DollarSign, Globe
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import { talentPoolsApi, TalentPool } from '@/api/talentPools'
import { communicationsApi, type EmailAccount, type EmailTemplateDef, type QuickReply } from '@/api/communications'
import { organisationApi } from '@/api/organisation'

import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import http from '@/utils/http'
import type {
  CandidateCommandCenter as CCData,
  CandidateSmartRow,
  ActiveWorkEngagement,
  WorkflowMode,
} from '@/types'
import { usePermission } from '@/hooks/usePermission'
import AddCandidateWorkflowModal from '@/components/candidates/AddCandidateWorkflowModal'
import { cn } from '@/utils/cn'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { useAuthStore } from '@/store/authStore'

dayjs.extend(relativeTime)
const { Title, Text, Paragraph } = Typography

// ── Stage chip config (engagement-level states with distinct colours) ─────────

const STAGE_CHIP: Record<string, { bg: string; color: string; label: string }> = {
  new_lead:           { bg: '#eff6ff', color: '#2563eb', label: 'New Lead' },
  contacted:          { bg: '#ecfeff', color: '#0891b2', label: 'Contacted' },
  follow_up:          { bg: '#fefce8', color: '#ca8a04', label: 'Follow Up' },
  qualified:          { bg: '#f0fdf4', color: '#16a34a', label: 'Qualified' },
  nurture:            { bg: '#fefce8', color: '#b45309', label: 'Nurture' },
  dormant:            { bg: '#f1f5f9', color: '#64748b', label: 'Dormant' },
  submitted:          { bg: '#faf5ff', color: '#7c3aed', label: 'Submitted' },
  review:             { bg: '#fdf2f8', color: '#be185d', label: 'Review' },
  interviewing:       { bg: '#fff7ed', color: '#ea580c', label: 'Interviewing' },
  offered:            { bg: '#f0fdf4', color: '#15803d', label: 'Offered' },
  joined:             { bg: '#dcfce7', color: '#15803d', label: 'Joined' },
  rejected:           { bg: '#fef2f2', color: '#dc2626', label: 'Rejected' },
  client_review:      { bg: '#fdf2f8', color: '#be185d', label: 'Review' },
  closed_or_nurture:  { bg: '#fefce8', color: '#b45309', label: 'Nurture' },
  general_pool:       { bg: '#f8fafc', color: '#64748b', label: 'Pool' },
}

const GLOBAL_STATE: Record<string, { bg: string; color: string; label: string }> = {
  open_to_work: { bg: '#f0fdf4', color: '#16a34a', label: 'Open to Work' },
  active:       { bg: '#eef2ff', color: '#6366f1', label: 'Active' },
  in_progress:  { bg: '#eff6ff', color: '#2563eb', label: 'In Progress' },
  nurturing:    { bg: '#fefce8', color: '#b45309', label: 'Nurturing' },
  dormant:      { bg: '#f1f5f9', color: '#64748b', label: 'Dormant' },
  archived:     { bg: '#f8fafc', color: '#94a3b8', label: 'Archived' },
  blacklisted:  { bg: '#fef2f2', color: '#dc2626', label: 'Blacklisted' },
}

const PRIORITY_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  hot:    { color: '#ef4444', bg: '#fef2f2', label: 'Hot' },
  warm:   { color: '#f97316', bg: '#fff7ed', label: 'Warm' },
  cold:   { color: '#94a3b8', bg: '#f8fafc', label: 'Cold' },
  normal: { color: '#6366f1', bg: '#eef2ff', label: 'Normal' },
}

const WORKFLOW_MODE_OPTIONS: Array<{ label: string; value: WorkflowMode }> = [
  { label: 'Manual', value: 'manual' },
  { label: 'Semi Automated', value: 'semi_automated' },
  { label: 'Fully Automated', value: 'fully_automated' },
]

const GENERAL_ENGAGEMENT_STAGE_OPTIONS = [
  'new_lead', 'contacted', 'follow_up', 'qualified', 'nurture', 'dormant',
]

const JOB_ENGAGEMENT_STAGE_OPTIONS = [
  'submitted', 'review', 'interviewing', 'offered', 'joined', 'rejected',
]

const FEED_TONE: Record<string, { badge: string; text: string; icon: any; label: string }> = {
  stage: { badge: 'bg-violet-50 text-violet-700', text: 'text-violet-700', icon: Activity, label: 'Stage Changed' },
  interview: { badge: 'bg-orange-50 text-orange-700', text: 'text-orange-700', icon: Calendar, label: 'Interview' },
  submission: { badge: 'bg-blue-50 text-blue-700', text: 'text-blue-700', icon: Send, label: 'Submission' },
  offer: { badge: 'bg-green-50 text-green-700', text: 'text-green-700', icon: TargetIcon, label: 'Offer' },
  rejection: { badge: 'bg-red-50 text-red-700', text: 'text-red-700', icon: XCircle, label: 'Rejection' },
  note: { badge: 'bg-slate-100 text-slate-700', text: 'text-slate-600', icon: ClipboardList, label: 'Note' },
  call: { badge: 'bg-teal-50 text-teal-700', text: 'text-teal-700', icon: Phone, label: 'Call' },
  email: { badge: 'bg-indigo-50 text-indigo-700', text: 'text-indigo-700', icon: Mail, label: 'Email' },
  system: { badge: 'bg-slate-100 text-slate-600', text: 'text-slate-600', icon: Settings2, label: 'System' },
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface GroupedCandidate {
  candidateId: string
  candidateName: string
  candidateRefId?: string
  engagements: ActiveWorkEngagement[]
  dominantPriority: 'hot' | 'warm' | 'cold'
  lastActivity: string | null
  ownerName: string | null
  globalStateKey: string
  engagementSummary: Record<string, number>
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function stageLabel(v?: string) {
  if (!v) return 'Unknown'
  return v.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

function deriveGlobalStateFromEngagements(engagements: ActiveWorkEngagement[]): string {
  const stages = engagements.map((e) => e.stage)
  if (stages.some((s) => ['offered', 'joined'].includes(s))) return 'active'
  if (stages.some((s) => ['submitted', 'review', 'client_review', 'interviewing'].includes(s))) return 'active'
  if (stages.some((s) => ['new_lead', 'contacted', 'follow_up', 'qualified'].includes(s))) return 'in_progress'
  if (stages.every((s) => ['nurture', 'closed_or_nurture'].includes(s))) return 'nurturing'
  return 'dormant'
}

function stageOptionsForEngagement(engagement?: ActiveWorkEngagement | null) {
  if (!engagement) return []
  const options = engagement.job ? JOB_ENGAGEMENT_STAGE_OPTIONS : GENERAL_ENGAGEMENT_STAGE_OPTIONS
  return options.map((s) => ({ value: s, label: stageLabel(s) }))
}

function actionToneKey(actionType?: string, method?: string) {
  const v = `${actionType || ''}`.toLowerCase()
  const m = `${method || ''}`.toLowerCase()
  if (v.includes('stage')) return 'stage'
  if (v.includes('interview')) return 'interview'
  if (v.includes('offer')) return 'offer'
  if (v.includes('reject') || v.includes('withdraw')) return 'rejection'
  if (v.includes('submit') || v.includes('application.created')) return 'submission'
  if (v.includes('call')) return 'call'
  if (v.includes('email') || m === 'email') return 'email'
  if (m === 'system' || v.includes('system')) return 'system'
  return 'note'
}

function groupActiveWorkByCandidates(data: any, mode: string): GroupedCandidate[] {
  if (!data) return []
  let items: any[] = []
  if (mode === 'focus') items = Object.values(data.focus || {}).flat()
  else if (mode === 'board') items = Object.values(data.board || {}).flat()
  else if (mode === 'follow_up_queue') items = data.queue || []

  const map = new Map<string, GroupedCandidate>()
  const priorityOrder: Record<string, number> = { hot: 3, warm: 2, cold: 1 }

  for (const item of items) {
    const cid = item.candidate as string
    if (!cid) continue

    if (!map.has(cid)) {
      map.set(cid, {
        candidateId: cid,
        candidateName: item.candidate_name || 'Unknown',
        candidateRefId: item.candidate_ref_id || '',
        engagements: [],
        dominantPriority: item.priority || 'cold',
        lastActivity: item.last_activity_at || null,
        ownerName: item.owner_name || null,
        globalStateKey: 'dormant',
        engagementSummary: {},
      })
    }

    const grp = map.get(cid)!
    grp.engagements.push(item)
    grp.engagementSummary[item.stage] = (grp.engagementSummary[item.stage] || 0) + 1

    if ((priorityOrder[item.priority] || 0) > (priorityOrder[grp.dominantPriority] || 0)) {
      grp.dominantPriority = item.priority
    }
    if (item.last_activity_at && (!grp.lastActivity || item.last_activity_at > grp.lastActivity)) {
      grp.lastActivity = item.last_activity_at
    }
    if (item.owner_name && !grp.ownerName) grp.ownerName = item.owner_name
  }

  for (const grp of map.values()) {
    grp.globalStateKey = deriveGlobalStateFromEngagements(grp.engagements)
  }

  return Array.from(map.values())
}

// ── Main Workbench ────────────────────────────────────────────────────────────

export default function CandidateWorkbench({ initialSurface }: { initialSurface: 'database' | 'active_work' }) {
  const { t } = useTranslation(['candidates', 'common'])
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canCreateCandidate = usePermission('candidates.candidate.create')

  // ── Workspace state ──────────────────────────────────────────────────────
  const [surface, setSurface] = useState<'database' | 'active_work'>(initialSurface)
  const [activeMode, setActiveMode] = useState<'focus' | 'board' | 'follow_up_queue'>('focus')
  const [search, setSearch] = useState('')

  // ── Selection state ──────────────────────────────────────────────────────
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [selectedEngagementId, setSelectedEngagementId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // ── Modals state ───────────────────────────────────────────────────────
  const [workflowDraft, setWorkflowDraft] = useState<WorkflowMode>('manual')
  const [addOpen, setAddOpen] = useState(false)
  const [addNoteOpen, setAddNoteOpen] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [quickNoteText, setQuickNoteText] = useState('')
  const [submitOpen, setSubmitOpen] = useState(false)
  const [emailComposerOpen, setEmailComposerOpen] = useState(false)
  const [stageChangeOpen, setStageChangeOpen] = useState(false)
  const [stageChangeNote, setStageChangeNote] = useState('')
  const [pendingStage, setPendingStage] = useState<string | null>(null)
  const [pendingFromStage, setPendingFromStage] = useState<string | null>(null)
  const [pendingEngagementId, setPendingEngagementId] = useState<string | null>(null)
  const [stageChangeLoading, setStageChangeLoading] = useState(false)

  // ── Queries ──────────────────────────────────────────────────────────────
  const activeQ = useQuery({
    queryKey: ['candidate-active-work', activeMode],
    queryFn: async () => (await candidatesApi.activeWork({ mode: activeMode })).data.data,
    enabled: surface === 'active_work',
  })

  const workflowQ = useQuery({
    queryKey: ['candidate-workflow-policy'],
    queryFn: async () => (await candidatesApi.getWorkflowPolicy({ scope: 'tenant' })).data.data,
  })

  const commandQ = useQuery({
    queryKey: ['candidate-command-center', selectedCandidateId],
    queryFn: async () => (await candidatesApi.commandCenter(selectedCandidateId!)).data.data,
    enabled: !!selectedCandidateId,
  })

  const groupedActiveItems = useMemo(
    () => (surface === 'active_work' ? groupActiveWorkByCandidates(activeQ.data, activeMode) : []),
    [activeQ.data, activeMode, surface],
  )

  const commandCenter = commandQ.data as CCData | null
  const effectiveMode = workflowQ.data?.effective_workflow_mode || 'manual'

  // ── Effects ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (selectedCandidateId !== null) return
    if (surface === 'active_work' && groupedActiveItems.length > 0) {
      selectCandidate(groupedActiveItems[0].candidateId)
    }
  }, [surface, groupedActiveItems.length]) // eslint-disable-line

  useEffect(() => {
    const firstEng = commandCenter?.tabs?.engagement?.[0]
    if (firstEng && !selectedEngagementId) setSelectedEngagementId(firstEng.id)
  }, [commandCenter?.tabs?.engagement?.length]) // eslint-disable-line

  useEffect(() => {
    if (workflowQ.data?.effective_workflow_mode) setWorkflowDraft(workflowQ.data.effective_workflow_mode)
  }, [workflowQ.data?.effective_workflow_mode])

  // ── Mutations ─────────────────────────────────────────────────────────────
  const updateWorkflow = useMutation({
    mutationFn: () =>
      candidatesApi.updateWorkflowPolicy({ scope: 'tenant', default_candidate_workflow_mode: workflowDraft }),
    onSuccess: () => {
      message.success('Workflow policy updated')
      queryClient.invalidateQueries({ queryKey: ['candidate-workflow-policy'] })
    },
    onError: () => message.error('Failed to update workflow policy'),
  })

  // ── Handlers ──────────────────────────────────────────────────────────────
  const selectCandidate = (id: string) => {
    setSelectedCandidateId(id)
    setSelectedEngagementId(null)
    setActiveTab('overview')
  }

  const handleStageChange = async (stage: string) => {
    if (!selectedCandidateId) return
    const engId = selectedEngagementId ?? commandCenter?.tabs?.engagement?.[0]?.id
    if (!engId) return message.warning('No engagement selected')
    const engagement = commandCenter?.tabs?.engagement?.find((e) => e.id === engId)
    const fromStage = engagement?.stage || null
    if (fromStage === stage) return
    setPendingStage(stage)
    setPendingFromStage(fromStage)
    setPendingEngagementId(engId)
    setStageChangeNote('')
    setStageChangeOpen(true)
  }

  const confirmStageChange = async () => {
    if (!selectedCandidateId || !pendingEngagementId || !pendingStage || !stageChangeNote.trim()) return
    setStageChangeLoading(true)
    try {
      await http.put(`/candidates/${selectedCandidateId}/engagements/${pendingEngagementId}/`, {
        stage: pendingStage,
        note: stageChangeNote.trim(),
      })
      message.success('Stage updated')
      setStageChangeOpen(false)
      queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
      queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to update stage')
    } finally {
      setStageChangeLoading(false)
    }
  }

  const handleAddNote = async (text: string, engagementId?: string | null): Promise<boolean> => {
    if (!selectedCandidateId || !text.trim()) return false
    try {
      await candidatesApi.addNote(selectedCandidateId, {
        note_text: text,
        note_type: 'general',
        engagement: engagementId ?? selectedEngagementId ?? undefined,
      })
      message.success('Note added')
      queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
      return true
    } catch {
      message.error('Failed to add note')
      return false
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-[#F8FAFC] overflow-hidden">

      {/* ══ Level 2 Header (Now primary for this view) ══════════════════════════ */}
      <div className="flex h-11 flex-none items-center justify-between border-b border-slate-100 bg-white px-6">
        <div className="flex items-center gap-1">
          {([
            { value: 'focus', label: 'Focus Mode' },
            { value: 'board', label: 'Kanban Board' },
            { value: 'follow_up_queue', label: 'Action Queue' },
          ] as const).map((opt) => (
            <button
              key={opt.value}
              onClick={() => setActiveMode(opt.value)}
              className={cn(
                "px-3 py-1 text-[10px] font-bold uppercase tracking-widest transition h-11 relative",
                activeMode === opt.value ? "text-indigo-600" : "text-slate-400 hover:text-slate-600"
              )}
            >
              {opt.label}
              {activeMode === opt.value && (
                <div className="absolute bottom-0 left-0 h-0.5 w-full bg-indigo-600 rounded-full" />
              )}
            </button>
          ))}
        </div>
        
        <div className="px-2.5 py-1 rounded-lg bg-indigo-50 border border-indigo-100 text-[10px] font-black text-indigo-600 uppercase tracking-widest">
           {groupedActiveItems.length} Active Tracks
        </div>
      </div>

      {/* ══ 3-Column Body ════════════════════════════════════════════════════ */}
      <div className="flex flex-1 overflow-hidden border-t border-slate-100">

        {/* LEFT: Candidate List Rail (320px) */}
        <div className="flex w-[320px] flex-none flex-col overflow-hidden border-r border-slate-200 bg-[#f8fafc]">
          <div className="flex-none border-b border-slate-200 bg-white p-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100 transition-all shadow-inner">
              <Search size={12} className="text-slate-400 shrink-0" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search candidates..."
                className="flex-1 bg-transparent text-xs text-slate-700 outline-none placeholder-slate-400"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
            {activeQ.isLoading && groupedActiveItems.length === 0 ? (
              <div className="py-12 flex justify-center"><Spin /></div>
            ) : groupedActiveItems.length === 0 ? (
              <Empty className="mt-12" image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span className="text-[10px] font-bold text-slate-400 uppercase">No active candidates</span>} />
            ) : (
              groupedActiveItems.map((grp: GroupedCandidate) => (
                <ActiveWorkListCard
                  key={grp.candidateId}
                  group={grp}
                  selected={selectedCandidateId === grp.candidateId}
                  onSelect={() => selectCandidate(grp.candidateId)}
                />
              ))
            )}
          </div>
        </div>

        {/* CENTER: Command Center (Main Workspace) */}
        <div className="flex flex-1 flex-col overflow-hidden border-r border-slate-200 bg-white">
          {commandQ.isLoading && selectedCandidateId ? (
            <div className="flex flex-1 items-center justify-center bg-slate-50/30">
              <Spin size="large" />
            </div>
          ) : selectedCandidateId && commandCenter ? (
            <CandidateCommandCenterPanel
              commandCenter={commandCenter}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              selectedEngagementId={selectedEngagementId}
              setSelectedEngagementId={setSelectedEngagementId}
              effectiveMode={effectiveMode}
              onStageChange={handleStageChange}
              onAddNote={() => setAddNoteOpen(true)}
              onSubmitToJob={() => setSubmitOpen(true)}
              onOpenEmailComposer={() => setEmailComposerOpen(true)}
            />
          ) : (
            <CommandEmptyState
              isEmpty={groupedActiveItems.length === 0}
              isLoading={activeQ.isLoading}
            />
          )}
        </div>

        {/* RIGHT: Action Rail (280px) */}
        {selectedCandidateId && (
          <ActionPanel
            commandCenter={commandCenter}
            selectedEngagementId={selectedEngagementId}
            setSelectedEngagementId={setSelectedEngagementId}
            quickNoteText={quickNoteText}
            setQuickNoteText={setQuickNoteText}
            onSaveQuickNote={async () => {
              const ok = await handleAddNote(quickNoteText)
              if (ok) setQuickNoteText('')
            }}
            onStageChange={handleStageChange}
            effectiveMode={effectiveMode}
            onOpenEmailComposer={() => setEmailComposerOpen(true)}
          />
        )}
      </div>

      <AddCandidateWorkflowModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        sourceSurface="active_work"
        onCompleted={() => {
          queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
        }}
      />

      <Modal
        title={<div className="flex items-center gap-2"><Zap size={18} className="text-indigo-600" /><span className="font-black uppercase tracking-tight text-slate-800">Confirm Stage Change</span></div>}
        open={stageChangeOpen}
        onCancel={() => setStageChangeOpen(false)}
        onOk={confirmStageChange}
        okText="Confirm Action"
        confirmLoading={stageChangeLoading}
        okButtonProps={{ disabled: !stageChangeNote.trim(), className: 'bg-indigo-600 font-black uppercase text-[10px] tracking-widest h-10 px-6 rounded-xl border-none' }}
        className="rounded-3xl overflow-hidden"
      >
        <div className="space-y-4 pt-4">
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center justify-between">
            <div>
              <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-1">Target Stage</Text>
              <Text className="text-sm font-black text-slate-800 uppercase">{pendingStage?.replace('_', ' ')}</Text>
            </div>
            <ChevronRight size={16} className="text-slate-300" />
          </div>
          <div>
            <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-2 ml-1">Mandatory Rationale / Note</Text>
            <Input.TextArea rows={4} value={stageChangeNote} onChange={(e) => setStageChangeNote(e.target.value)} placeholder="Provide mandatory rationale for this stage change..." className="rounded-2xl border-slate-200 p-4" />
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ── Sub-components for Workbench ─────────────────────────────────────────────

function ActiveWorkListCard({ group, selected, onSelect }: { group: GroupedCandidate; selected: boolean; onSelect: () => void }) {
  const ps = PRIORITY_STYLE[group.dominantPriority] || PRIORITY_STYLE.cold
  const globalState = GLOBAL_STATE[group.globalStateKey] || GLOBAL_STATE.dormant
  const summaryEntries = Object.entries(group.engagementSummary)

  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full rounded-xl border p-3.5 text-left transition-all relative overflow-hidden group mb-1",
        selected
          ? "border-indigo-400 bg-white shadow-sm ring-2 ring-indigo-100"
          : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm"
      )}
    >
      {selected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600 rounded-r-full" />}
      
      <div className="flex items-start gap-3">
        <div className="relative shrink-0 mt-0.5">
          <Avatar size={36} style={{ backgroundColor: avatarColor(group.candidateName) }} className="font-black text-white text-xs border-2 border-white shadow-soft-sm">
            {group.candidateName.charAt(0)}
          </Avatar>
          <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white shadow-soft-sm" style={{ backgroundColor: ps.color }} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className={cn("truncate text-xs font-black tracking-tight leading-tight uppercase transition-colors", selected ? "text-slate-900" : "text-slate-800")}>
              {group.candidateName}
            </div>
            <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest bg-slate-50 px-1 py-0.5 rounded border border-slate-100">{ps.label}</span>
          </div>
          {group.candidateRefId && (
            <div className="mb-1">
              <span className="inline-flex items-center rounded-md border border-indigo-100 bg-indigo-50 px-1.5 py-0.5 text-[8px] font-black uppercase tracking-widest text-indigo-700">
                {group.candidateRefId}
              </span>
            </div>
          )}

          <div className="mt-1 flex items-center gap-2 text-[9px] font-black text-slate-400 uppercase tracking-tighter">
            {group.ownerName && (
              <span className="flex items-center gap-1"><User size={9} className="text-slate-300" />{group.ownerName.split(' ')[0]}</span>
            )}
            <span className="text-slate-200">•</span>
            {group.lastActivity && (
              <span className="flex items-center gap-1"><Clock3 size={9} className="text-slate-300" />{dayjs(group.lastActivity).fromNow(true)}</span>
            )}
          </div>

          <div className="mt-2.5 flex flex-wrap gap-1">
            <span className="rounded-full px-2 py-0.5 text-[8px] font-black uppercase tracking-widest border shadow-soft-sm" style={{ backgroundColor: globalState.bg, color: globalState.color, borderColor: `${globalState.color}20` }}>{globalState.label}</span>
            {summaryEntries.map(([stage, count]) => {
              const chip = STAGE_CHIP[stage]
              if (!chip) return null
              return (
                <span key={stage} className="rounded-full px-2 py-0.5 text-[8px] font-black uppercase tracking-widest border shadow-soft-sm" style={{ backgroundColor: chip.bg, color: chip.color, borderColor: `${chip.color}20` }}>{chip.label}{count > 1 ? ` ×${count}` : ''}</span>
              )
            })}
          </div>
        </div>
      </div>
    </button>
  )
}

function CommandEmptyState({ isEmpty, isLoading }: { isEmpty: boolean; isLoading: boolean }) {
  if (isLoading) return <div className="flex flex-1 items-center justify-center bg-slate-50/30"><Spin size="large" /></div>
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-12 bg-slate-50/30 text-center">
      <div className="h-20 w-20 rounded-[28px] bg-indigo-600 flex items-center justify-center text-white shadow-soft-xl mb-8 transform -rotate-6">
        <TargetIcon size={36} />
      </div>
      <h3 className="text-xl font-black text-slate-900 tracking-tight leading-none uppercase mb-3">Workbench Workspace</h3>
      <p className="text-slate-500 text-sm font-medium leading-relaxed max-w-xs">{isEmpty ? 'Your queue is currently clear.' : 'Select an active profile to begin.'}</p>
    </div>
  )
}

function CandidateCommandCenterPanel({
  commandCenter, activeTab, setActiveTab,
  selectedEngagementId, setSelectedEngagementId,
  effectiveMode, onStageChange, onAddNote, onSubmitToJob, onOpenEmailComposer,
}: any) {
  const c = commandCenter.candidate
  const engagements = commandCenter.tabs?.engagement || []
  const selectedEngagement = engagements.find((e: any) => e.id === selectedEngagementId) || engagements[0] || null

  const globalStateKey = deriveGlobalStateFromEngagements(engagements)
  const globalState = GLOBAL_STATE[globalStateKey] || GLOBAL_STATE.dormant
  
  const tabs = [
    { key: 'overview',      label: <TabLabel icon={<TargetIcon size={11} />} text="Strategy" /> },
    { key: 'resume',        label: <TabLabel icon={<FileText size={11} />} text="Resume" /> },
    { key: 'documents',     label: <TabLabel icon={<Paperclip size={11} />} text="Documents" /> },
    { key: 'engagements',   label: <TabLabel icon={<Layers size={11} />} text={`Tracks (${engagements.length})`} /> },
    { key: 'activity',      label: <TabLabel icon={<Activity size={11} />} text="Feed" /> },
    { key: 'notes',         label: <TabLabel icon={<Notebook size={11} />} text="Insights" /> },
    { key: 'communication', label: <TabLabel icon={<Mail size={11} />} text="Comms" /> },
    { key: 'history',       label: <TabLabel icon={<History size={11} />} text="History" /> },
    { key: 'automation',    label: <TabLabel icon={<BrainCircuit size={11} />} text="AI Logic" /> },
  ]

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-100 bg-white">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="relative shrink-0">
              <Avatar size={52} style={{ backgroundColor: avatarColor(c.full_name) }} className="font-black text-white text-xl shadow-soft-sm ring-4 ring-slate-50">
                {c.full_name.charAt(0)}
              </Avatar>
              <div className="absolute -bottom-1 -right-1 h-5 w-5 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center text-white shadow-soft-sm">
                 <BadgeCheck size={12} />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1 flex-wrap">
                 <Title level={3} className="!m-0 text-slate-900 !text-lg tracking-tight font-black uppercase">{c.full_name}</Title>
                 <span className={cn("px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-[0.12em] border shadow-soft-sm", globalState.bg, globalState.color)}>
                    {globalState.label}
                 </span>
                 {c.candidate_ref_id && (
                   <span className="inline-flex items-center rounded-full border border-indigo-100 bg-indigo-50 px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.12em] text-indigo-700 shadow-soft-sm">
                     {c.candidate_ref_id}
                   </span>
                 )}
              </div>
              <div className="flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                <span className="flex items-center gap-1"><MapPin size={11} /> {c.current_location_city || 'Remote'}</span>
                <span>•</span>
                <span className="flex items-center gap-1"><Briefcase size={11} /> {c.experience_years || '—'} Yrs Exp</span>
                <span>•</span>
                <span className="flex items-center gap-1 text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100"><Zap size={10} fill="currentColor" /> Profile Score: 92%</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2 self-end lg:self-start">
            <button className="flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[10px] font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50 transition-all shadow-soft-sm active:scale-95" onClick={() => setActiveTab('history')}>
              <History size={14} /> Full History
            </button>
            <button onClick={onSubmitToJob} className="flex h-9 items-center gap-2 rounded-xl bg-slate-900 px-5 text-[10px] font-black uppercase tracking-widest text-white hover:bg-slate-800 transition-all shadow-soft-lg active:scale-95">
              <Target size={14} /> Submit to Job
            </button>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-1.5 border-t border-slate-50 pt-4">
          <button onClick={onOpenEmailComposer} className="h-7 rounded-lg border border-slate-200 bg-white px-3 text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-1.5 shadow-none">
            <Mail size={11} /> Outreach
          </button>
          <button className="h-7 rounded-lg border border-slate-200 bg-white px-3 text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-1.5 shadow-none">
            <Phone size={11} /> Audio Call
          </button>
          <button className="h-7 rounded-lg border border-slate-200 bg-white px-3 text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-1.5 shadow-none">
            <Calendar size={11} /> Schedule
          </button>
          <div className="h-4 w-px bg-slate-100 mx-1" />
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-0.5">
            <Workflow size={10} className="text-slate-400 shrink-0" />
            <Select
              size="small"
              variant="borderless"
              placeholder="Move Stage"
              value={selectedEngagement?.stage}
              onChange={onStageChange}
              options={stageOptionsForEngagement(selectedEngagement)}
              style={{ width: 110 }}
              className="text-[9px] font-black uppercase"
            />
          </div>
        </div>
      </div>

      <div className="flex h-10 flex-none items-center border-b border-slate-100 bg-white px-8">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="small"
          className="enterprise-tabs"
          tabBarStyle={{ marginBottom: 0 }}
          items={tabs.map((t) => ({ key: t.key, label: t.label, children: null }))}
        />
      </div>

      <div className="flex-1 overflow-y-auto bg-slate-50/30 custom-scrollbar p-6">
        {activeTab === 'overview'      && <OverviewTab cc={commandCenter} />}
        {activeTab === 'resume'        && <ResumeTab cc={commandCenter} />}
        {activeTab === 'documents'     && <DocumentsTab cc={commandCenter} />}
        {activeTab === 'engagements'   && <EngagementsTab cc={commandCenter} selectedEngagementId={selectedEngagementId} setSelectedEngagementId={setSelectedEngagementId} onStageChange={onStageChange} />}
        {activeTab === 'activity'      && <ActivityTab cc={commandCenter} selectedEngagementId={selectedEngagementId} />}
        {activeTab === 'notes'         && <NotesTab cc={commandCenter} onAddNote={onAddNote} selectedEngagementId={selectedEngagementId} />}
        {activeTab === 'communication' && <CommunicationTab cc={commandCenter} onOpenEmailComposer={onOpenEmailComposer} />}
        {activeTab === 'history'       && <HistoryTab cc={commandCenter} />}
        {activeTab === 'automation'    && <AutomationTab cc={commandCenter} effectiveMode={effectiveMode} />}
      </div>
    </div>
  )
}

function OverviewTab({ cc }: { cc: CCData }) {
  const c = cc.candidate
  return (
    <div className="space-y-6 max-w-4xl animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <section className="bg-white rounded-2xl p-5 border border-slate-100 shadow-soft-sm">
           <h4 className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-4 flex items-center gap-2"><MapPin size={12} /> Geographic & Reach</h4>
           <div className="space-y-3">
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Location</span><span className="text-xs font-black text-slate-700 uppercase">{c.current_location_city || 'Remote'}</span></div>
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Email</span><span className="text-xs font-black text-slate-700">{c.email}</span></div>
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Phone</span><span className="text-xs font-black text-slate-700 uppercase">{c.phone}</span></div>
              <div className="flex justify-between"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">LinkedIn</span><a href={c.linkedin_url || '#'} target="_blank" rel="noreferrer" className="text-xs font-black text-indigo-600 uppercase">View Profile</a></div>
           </div>
        </section>
        <section className="bg-white rounded-2xl p-5 border border-slate-100 shadow-soft-sm">
           <h4 className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-4 flex items-center gap-2"><DollarSign size={12} /> Economics</h4>
           <div className="space-y-3">
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Min Expectation</span><span className="text-xs font-black text-slate-700 uppercase">{c.salary_currency} {c.expected_salary_min?.toLocaleString()}</span></div>
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Max Range</span><span className="text-xs font-black text-slate-700 uppercase">{c.salary_currency} {c.expected_salary_max?.toLocaleString()}</span></div>
              <div className="flex justify-between border-b border-slate-50 pb-2"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Notice Period</span><span className="text-xs font-black text-slate-700 uppercase">{c.notice_period_days || 0} Days</span></div>
              <div className="flex justify-between"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Availability</span><span className="text-xs font-black text-emerald-600 uppercase">Immediate</span></div>
           </div>
        </section>
      </div>

      <section className="bg-white rounded-2xl p-5 border border-slate-100 shadow-soft-sm">
         <h4 className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-4 flex items-center gap-2"><TargetIcon size={12} /> Specialized Intelligence</h4>
         <div className="flex flex-wrap gap-2">
            {(c.skills as string[] || []).map(s => (
              <span key={s} className="px-3 py-1 rounded-xl bg-slate-50 border border-slate-100 text-[10px] font-black text-slate-600 uppercase tracking-widest">{s}</span>
            ))}
         </div>
      </section>
    </div>
  )
}

function ResumeTab({ cc }: { cc: CCData }) {
  const resumeUrl = cc.tabs?.documents?.resume_url
  return (
    <div className="h-full bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-soft-sm flex flex-col">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 shrink-0">
         <div className="flex items-center gap-2">
            <FileText size={14} className="text-indigo-600" />
            <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Document Intelligence Viewer</span>
         </div>
         <div className="flex items-center gap-2">
            <button className="h-7 px-3 rounded-lg border border-slate-200 bg-white text-[9px] font-black uppercase text-slate-600 hover:bg-slate-100 transition-all shadow-none flex items-center gap-1.5" onClick={() => resumeUrl && window.open(resumeUrl, '_blank')}>
               <ExternalLink size={11} /> Open full
            </button>
         </div>
      </div>
      <div className="flex-1">
        {resumeUrl ? (
          <iframe src={resumeUrl} className="h-full w-full border-0" title="Candidate Resume" />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3">
            <div className="h-16 w-16 rounded-2xl bg-slate-50 flex items-center justify-center text-slate-200">
               <FileText size={32} strokeWidth={1} />
            </div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic">No resume artifact found</p>
          </div>
        )}
      </div>
    </div>
  )
}

function DocumentsTab({ cc }: { cc: CCData }) {
  const docs = cc.tabs?.documents || {}
  const c = cc.candidate
  const files = [
    docs.resume_url && { label: 'Resume', url: docs.resume_url, icon: FileText, bg: 'bg-blue-50', color: 'text-blue-500' },
    docs.profile_cv_url && { label: 'Profile CV', url: docs.profile_cv_url, icon: FileDown, bg: 'bg-green-50', color: 'text-green-500' },
    c.linkedin_url && { label: 'LinkedIn', url: c.linkedin_url, icon: Link2, bg: 'bg-sky-50', color: 'text-sky-500' },
  ].filter(Boolean) as Array<{ label: string; url: string; icon: any; bg: string; color: string }>

  return (
    <div className="space-y-3 max-w-4xl">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{files.length} Document Artifacts</span>
        <button className="flex items-center gap-1.5 rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-[10px] font-black uppercase text-slate-500 hover:bg-slate-50 transition-all">
          <Plus size={11} /> Upload New
        </button>
      </div>
      {files.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-white py-12">
          <Paperclip size={24} className="text-slate-300" />
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic">No documents attached</p>
        </div>
      ) : (
        files.map((f) => (
          <div key={f.label} className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-4 shadow-soft-sm hover:shadow-soft-md transition-all">
            <div className="flex items-center gap-4">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${f.bg}`}>
                <f.icon size={18} className={f.color} />
              </div>
              <div>
                <p className="text-xs font-black text-slate-800 uppercase tracking-tight m-0">{f.label}</p>
                <p className="text-[10px] text-slate-400 font-medium truncate max-w-[240px] mt-0.5">{f.url}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => window.open(f.url, '_blank')}
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-indigo-600 transition-all">
                <ExternalLink size={14} />
              </button>
              <button onClick={() => window.open(f.url, '_blank')}
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-indigo-600 transition-all">
                <FileDown size={14} />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

function EngagementsTab({ cc, selectedEngagementId, setSelectedEngagementId, onStageChange }: any) {
  const engagements: ActiveWorkEngagement[] = cc.tabs?.engagement || []
  return (
    <div className="space-y-4 max-w-4xl">
      {engagements.map((eng) => {
        const isSelected = eng.id === selectedEngagementId
        const chip = STAGE_CHIP[eng.stage] || STAGE_CHIP.general_pool
        const ps = PRIORITY_STYLE[eng.priority] || PRIORITY_STYLE.cold

        return (
          <div
            key={eng.id}
            onClick={() => setSelectedEngagementId(eng.id)}
            className={cn(
              "cursor-pointer rounded-2xl border p-5 transition-all relative overflow-hidden group",
              isSelected
                ? "border-indigo-500 bg-white shadow-soft-xl ring-2 ring-indigo-500/5"
                : "border-slate-100 bg-white hover:border-slate-200 hover:shadow-soft-md"
            )}
          >
            {isSelected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600" />}
            
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-soft-sm shrink-0">
                   <Briefcase size={20} />
                </div>
                <div>
                  <p className="text-sm font-black text-slate-900 uppercase tracking-tight m-0">{eng.job_title || 'General Pool'}</p>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">ID: {eng.id.slice(0, 12)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.12em] border shadow-soft-sm" style={{ backgroundColor: chip.bg, color: chip.color, borderColor: `${chip.color}20` }}>{chip.label}</span>
                <span className="rounded-full px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.12em] border shadow-soft-sm" style={{ backgroundColor: ps.bg, color: ps.color, borderColor: `${ps.color}20` }}>{eng.priority}</span>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-4 pt-4 border-t border-slate-50">
               <div><p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Ownership</p><p className="text-xs font-black text-slate-700 uppercase truncate">{eng.owner_name || 'Unassigned'}</p></div>
               <div><p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Velocity</p><p className="text-xs font-black text-slate-700 uppercase truncate">{eng.last_activity_at ? dayjs(eng.last_activity_at).fromNow(true) : '—'}</p></div>
               <div><p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Follow up</p><p className="text-xs font-black text-rose-600 uppercase truncate">Immediate</p></div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ActivityTab({ cc, selectedEngagementId }: any) {
  const structuredActivity = (cc.tabs?.structured_activity || []).map((a: any) => ({ ...a, _kind: 'activity' as const }))
  const feed = [...structuredActivity].sort((a: any, b: any) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-[32px] border border-slate-100 shadow-soft-sm p-10">
      <h3 className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-10 flex items-center gap-2"><Activity size={12} /> Real-time activity stream</h3>
      {feed.length === 0 ? <Empty description="No feed data" /> : (
        <Timeline
          className="enterprise-timeline"
          items={feed.map((act: any, i: number) => {
            const toneKey = actionToneKey(act.action_type, act.method)
            const tone = FEED_TONE[toneKey] || FEED_TONE.system
            return {
              key: i,
              children: (
                <div className="flex flex-col mb-8 group relative pl-2">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <span className={cn("inline-flex items-center px-2 py-0.5 rounded-lg font-black text-[8px] uppercase tracking-widest border shadow-soft-sm", tone.badge)}>{tone.label}</span>
                    <div className="h-1 w-1 rounded-full bg-slate-200 shrink-0" />
                    <Text className="text-slate-700 text-[11px] font-bold uppercase tracking-tight">{(act.action_type || 'Event').replace(/\./g, ' ')}</Text>
                  </div>
                  <div className="flex items-center gap-2">
                    <Avatar size={16} className="bg-slate-900 text-white text-[8px] font-black border-2 border-white shadow-soft-sm shrink-0">{act.actor?.charAt(0)}</Avatar>
                    <Text className="text-[10px] text-slate-500 font-bold italic">By {act.actor || 'System'}</Text>
                    <div className="h-1 w-1 rounded-full bg-slate-200 shrink-0" />
                    <Clock3 size={10} className="text-slate-300" />
                    <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-slate-400">{dayjs(act.created_at).fromNow()}</Text>
                  </div>
                </div>
              ),
              dot: <div className={cn("h-3.5 w-3.5 rounded-full border-4 border-white shadow-soft-md flex items-center justify-center transition-all group-hover:scale-125", tone.badge.split(' ')[0].replace('bg-', 'bg-'))} style={{ backgroundColor: tone.badge.includes('violet') ? '#8b5cf6' : tone.badge.includes('blue') ? '#3b82f6' : '#6366f1' }} />
            }
          })}
        />
      )}
    </div>
  )
}

function HistoryTab({ cc }: { cc: CCData }) {
  const history = cc.tabs?.history || []
  return (
    <div className="max-w-3xl mx-auto bg-white rounded-[32px] border border-slate-100 shadow-soft-sm p-10">
      <h3 className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-10 flex items-center gap-2"><History size={12} /> Global Profile History</h3>
      {history.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No global history recorded" />
      ) : (
        <div className="relative pl-5 space-y-0">
          <div className="absolute left-2 top-0 bottom-0 w-px bg-slate-100" />
          {history.map((item: any, idx: number) => (
            <div key={idx} className="relative mb-6 group">
              <div className="absolute -left-[11px] top-2 h-2 w-2 rounded-full bg-slate-300 ring-4 ring-white group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-2xl border border-slate-50 bg-slate-50/30 p-4 transition-all group-hover:bg-white group-hover:shadow-soft-md">
                <div className="flex items-start justify-between mb-1">
                  <span className="text-xs font-black text-slate-800 uppercase tracking-tight">{item.event || item.action || 'Operational Event'}</span>
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{dayjs(item.created_at || item.timestamp).format('MMM D, YYYY')}</span>
                </div>
                {(item.details || item.description) && (
                  <p className="mt-1 text-[11px] text-slate-500 font-medium leading-relaxed italic">"{item.details || item.description}"</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function NotesTab({ cc, onAddNote, selectedEngagementId }: any) {
  const notes = cc.tabs?.structured_notes || []
  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      <div className="flex justify-end mb-4">
         <button onClick={onAddNote} className="h-9 px-5 rounded-xl bg-slate-900 text-white font-black text-[10px] uppercase tracking-widest hover:bg-slate-800 transition-all shadow-soft-lg flex items-center gap-2 active:scale-95">
            <Plus size={14} /> Add Recruiter Note
         </button>
      </div>
      {notes.map((n: any) => (
        <div key={n.id} className="bg-white rounded-2xl border border-slate-100 p-6 shadow-soft-sm hover:shadow-soft-md transition-shadow">
           <div className="flex items-center justify-between mb-4">
              <span className="px-2 py-0.5 rounded-lg bg-amber-50 text-amber-600 border border-amber-100 font-black text-[8px] uppercase tracking-widest">{n.note_type || 'Insight'}</span>
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">{dayjs(n.created_at).fromNow()}</Text>
           </div>
           <p className="text-xs font-medium text-slate-700 leading-relaxed italic">"{n.content}"</p>
           <div className="mt-4 pt-4 border-t border-slate-50 flex items-center gap-2">
              <Avatar size={18} className="bg-indigo-50 text-indigo-600 font-black text-[8px]">{n.author?.charAt(0)}</Avatar>
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{n.author}</Text>
           </div>
        </div>
      ))}
    </div>
  )
}

function CommunicationTab({ cc, onOpenEmailComposer }: any) {
  const c = cc.candidate
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-12 bg-white rounded-[32px] border border-slate-100 shadow-soft-sm min-h-[400px]">
       <div className="h-16 w-16 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-300 mb-6">
          <Mail size={32} strokeWidth={1.5} />
       </div>
       <div className="text-center mb-8">
          <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest mb-2">Omnichannel Comms</h3>
          <p className="text-xs text-slate-400 font-medium max-w-xs mx-auto">Engage via email or messaging directly from this terminal. Activity is logged automatically.</p>
       </div>
       <button onClick={onOpenEmailComposer} className="h-10 px-8 rounded-xl bg-indigo-600 text-white font-black text-[10px] uppercase tracking-widest hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-100 active:scale-95 flex items-center gap-2">
          <Send size={14} /> Send Official Outreach
       </button>
    </div>
  )
}

function AutomationTab({ cc, effectiveMode }: any) {
  const auto = cc.tabs?.automations
  return (
    <div className="space-y-6 max-w-4xl">
       <div className="bg-slate-900 rounded-[32px] p-8 shadow-soft-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl" />
          <div className="relative z-10 flex items-start justify-between gap-8">
             <div>
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400 mb-4 flex items-center gap-2"><BrainCircuit size={14} /> AI Agent Strategy</h4>
                <p className="text-white text-sm font-medium leading-relaxed max-w-md">Our intelligence engine is currently set to <span className="text-indigo-400 font-black">{effectiveMode.replace(/_/g, ' ').toUpperCase()}</span> for this profile. Automation triggers are active based on the global tenant policy.</p>
             </div>
             <div className="shrink-0 flex flex-col items-end gap-2">
                <span className="px-3 py-1 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[9px] font-black uppercase tracking-widest">Logic Active</span>
                <span className="px-3 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[9px] font-black uppercase tracking-widest">SLA Compliant</span>
             </div>
          </div>
       </div>
       
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: 'Auto Sourcing', on: auto?.automation_enabled },
            { label: 'Smart Suggestions', on: auto?.auto_stage_suggestions_enabled },
            { label: 'Nurture Loop', on: auto?.auto_nurture_enabled },
            { label: 'Feedback Sync', on: true }
          ].map(item => (
            <div key={item.label} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-soft-sm flex items-center justify-between">
               <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{item.label}</span>
               <div className={cn("h-2 w-2 rounded-full", item.on ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" : "bg-slate-200")} />
            </div>
          ))}
       </div>
    </div>
  )
}

// ── Action Panel (Right Rail) ────────────────────────────────────────────────

function ActionPanel({ commandCenter, selectedEngagementId, setSelectedEngagementId, quickNoteText, setQuickNoteText, onSaveQuickNote, onStageChange, onOpenEmailComposer }: any) {
  const engagements = commandCenter?.tabs?.engagement || []
  const selectedEng = engagements.find((e: any) => e.id === selectedEngagementId) || engagements[0] || null

  return (
    <div className="flex w-[280px] flex-none flex-col overflow-hidden border-l border-slate-200 bg-[#f8fafc]">
      <div className="p-4 border-b border-slate-200 bg-white shadow-soft-sm flex items-center gap-2">
        <Layers size={14} className="text-indigo-600" />
        <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-900 leading-none">Operational Rail</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {/* Core Directives */}
        <div className="space-y-2">
          <Text className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400 pl-1 block mb-2">Directives</Text>
          
          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft-sm">
             <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">Selected Engagement</p>
             <Select
                size="small"
                value={selectedEng?.id}
                className="w-full text-[10px] font-black uppercase"
                onChange={id => setSelectedEngagementId(id)}
                options={engagements.map((e: any) => ({ value: e.id, label: e.job_title || 'General' }))}
             />
             <div className="mt-4 pt-4 border-t border-slate-50">
                <div className="flex justify-between items-center"><span className="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">Current Stage</span><span className="text-[10px] font-black text-indigo-600 uppercase">{stageLabel(selectedEng?.stage)}</span></div>
             </div>
          </div>

          <div className="bg-slate-900 rounded-[24px] p-5 shadow-soft-xl border border-slate-800">
             <h4 className="text-[9px] font-black uppercase tracking-widest text-indigo-400 mb-3">Quick Intelligence</h4>
             <Input.TextArea
                rows={3}
                placeholder="Log instant thought..."
                value={quickNoteText}
                onChange={e => setQuickNoteText(e.target.value)}
                className="bg-white/5 border-white/10 text-white text-[10px] rounded-xl placeholder:text-white/20 mb-3"
             />
             <button onClick={onSaveQuickNote} className="w-full py-2 rounded-lg bg-indigo-600 text-white font-black uppercase text-[9px] tracking-widest hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-900/40 active:scale-95">Log Insight</button>
          </div>
        </div>

        {/* High Utility Actions */}
        <div className="space-y-2">
           <Text className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400 pl-1 block mb-2">Instant Ops</Text>
           <div className="grid grid-cols-2 gap-2">
              <button className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 transition-all shadow-soft-sm group active:scale-95" onClick={onOpenEmailComposer}>
                 <Mail size={16} className="text-slate-400 group-hover:text-indigo-600 mb-2" />
                 <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Outreach</span>
              </button>
              <button className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 transition-all shadow-soft-sm group active:scale-95">
                 <Phone size={16} className="text-slate-400 group-hover:text-indigo-600 mb-2" />
                 <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Call Log</span>
              </button>
              <button className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 transition-all shadow-soft-sm group active:scale-95">
                 <Calendar size={16} className="text-slate-400 group-hover:text-indigo-600 mb-2" />
                 <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Schedule</span>
              </button>
              <button className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 transition-all shadow-soft-sm group active:scale-95">
                 <TargetIcon size={16} className="text-slate-400 group-hover:text-indigo-600 mb-2" />
                 <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Priority</span>
              </button>
           </div>
        </div>

        {/* Signals */}
        <div className="space-y-3">
           <Text className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400 pl-1 block mb-2">Velocity Signals</Text>
           <div className="bg-white border border-emerald-100 rounded-2xl p-4 flex gap-3 shadow-soft-sm border-l-4 border-l-emerald-400">
              <TrendingUp size={16} className="text-emerald-500 shrink-0" />
              <div>
                <Text className="block text-[10px] font-black uppercase tracking-widest text-slate-900 mb-1 leading-none">Optimal Path</Text>
                <Text className="text-[10px] font-medium text-slate-500 block leading-tight">Moving 20% faster than role average.</Text>
              </div>
           </div>
        </div>
      </div>
    </div>
  )
}

function TabLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return <span className="flex items-center gap-1.5 py-0.5 text-[10px] font-black uppercase tracking-widest">{icon}{text}</span>
}
