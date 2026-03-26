import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert, Avatar, Badge, Button, Empty, Form, Input, Modal,
  Select, Spin, Tabs, Tag, Typography, message,
  Tooltip, Divider, Switch,
} from 'antd'
import {
  Activity, BadgeCheck, BellDot, Bot, BrainCircuit, Briefcase,
  Building2, Calendar, ChevronRight, ClipboardList, Clock3,
  Database, ExternalLink, FileDown, FileText, Flag,
  History, Link2, Mail, MapPin, MessageSquare,
  Paperclip, Phone, Plus, RefreshCw, Search, Send, Share2,
  Sparkles, Star, Target, Trash2, User, Users, Workflow, ShieldCheck,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { candidatesApi } from '@/api/candidates'
import { talentPoolsApi, TalentPool } from '@/api/talentPools'
import { communicationsApi, type EmailAccount, type EmailTemplateDef, type QuickReply } from '@/api/communications'

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

dayjs.extend(relativeTime)

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
  // Legacy aliases for backward display compatibility.
  client_review:      { bg: '#fdf2f8', color: '#be185d', label: 'Review' },
  closed_or_nurture:  { bg: '#fefce8', color: '#b45309', label: 'Nurture' },
  general_pool:       { bg: '#f8fafc', color: '#64748b', label: 'Pool' },
}

// ── Global candidate state config (person-level truth) ────────────────────────

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

function formatProtectionDate(value?: string | null, format = 'DD MMM YYYY') {
  if (!value) return 'Agreement release'
  const parsed = dayjs(value)
  return parsed.isValid() ? parsed.format(format) : value
}

function protectionScopeLabel(scope?: string | null) {
  if (!scope) return 'Not Protected'
  if (scope === 'job_only') return 'Job Only'
  if (scope === 'view_only') return 'View Only'
  if (scope === 'limited_company_access') return 'Limited Company Access'
  return scope.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
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

const FEED_TONE: Record<string, { badge: string; text: string; icon: string; label: string }> = {
  stage: { badge: 'bg-violet-50 text-violet-700', text: 'text-violet-700', icon: '🟣', label: 'Stage Changed' },
  interview: { badge: 'bg-orange-50 text-orange-700', text: 'text-orange-700', icon: '🟠', label: 'Interview' },
  submission: { badge: 'bg-blue-50 text-blue-700', text: 'text-blue-700', icon: '🔵', label: 'Submission' },
  offer: { badge: 'bg-green-50 text-green-700', text: 'text-green-700', icon: '🟢', label: 'Offer' },
  rejection: { badge: 'bg-red-50 text-red-700', text: 'text-red-700', icon: '🔴', label: 'Rejection' },
  note: { badge: 'bg-slate-100 text-slate-700', text: 'text-slate-600', icon: '📝', label: 'Note' },
  call: { badge: 'bg-teal-50 text-teal-700', text: 'text-teal-700', icon: '📞', label: 'Call' },
  email: { badge: 'bg-indigo-50 text-indigo-700', text: 'text-indigo-700', icon: '📧', label: 'Email' },
  system: { badge: 'bg-slate-100 text-slate-600', text: 'text-slate-600', icon: '⚙️', label: 'System' },
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface GroupedCandidate {
  candidateId: string
  candidateName: string
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

function modeColor(mode: WorkflowMode) {
  if (mode === 'fully_automated') return 'green'
  if (mode === 'semi_automated') return 'gold'
  return 'default'
}

function nextBestAction(stage?: string) {
  const map: Record<string, string> = {
    new_lead: 'Send first outreach',
    contacted: 'Schedule follow-up',
    follow_up: 'Call candidate',
    qualified: 'Submit to job',
    nurture: 'Add to nurture sequence',
    dormant: 'Re-engage candidate',
    submitted: 'Prep for interview',
    review: 'Follow up with hiring team',
    interviewing: 'Debrief & next round',
    offered: 'Offer negotiation',
  }
  return map[stage || ''] || 'Review & update stage'
}

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

/** Derive person-level global state from CandidateSmartRow fields */
function deriveGlobalStateKey(row: CandidateSmartRow & { is_actively_looking?: boolean }): string {
  if ((row as any).is_actively_looking) return 'open_to_work'
  const s = row.engagement_stage
  if (!s) return 'dormant'
  if (['offered', 'joined'].includes(s)) return 'active'
  if (['submitted', 'review', 'interviewing'].includes(s)) return 'active'
  if (['new_lead', 'contacted', 'follow_up', 'qualified'].includes(s)) return 'in_progress'
  if (s === 'nurture' || s === 'closed_or_nurture') return 'nurturing'
  return 'dormant'
}

/** Derive person-level global state from active work engagements */
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

/** Flatten all active work items from any mode into a flat list */
function flattenActiveWork(data: any, mode: string): any[] {
  if (!data) return []
  if (mode === 'focus') return Object.values(data.focus || {}).flat() as any[]
  if (mode === 'board') return Object.values(data.board || {}).flat() as any[]
  if (mode === 'follow_up_queue') return data.queue || []
  return []
}

/** Group flat active work items by candidate — one entry per person */
function groupActiveWorkByCandidates(data: any, mode: string): GroupedCandidate[] {
  const flat = flattenActiveWork(data, mode)
  const map = new Map<string, GroupedCandidate>()
  const priorityOrder: Record<string, number> = { hot: 3, warm: 2, cold: 1 }

  for (const item of flat) {
    const cid = item.candidate as string
    if (!cid) continue

    if (!map.has(cid)) {
      map.set(cid, {
        candidateId: cid,
        candidateName: item.candidate_name || 'Unknown',
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

type WorkbenchProps = { initialSurface: 'database' | 'active_work' }

export default function CandidateWorkbench({ initialSurface }: WorkbenchProps) {
  useTranslation(['candidates', 'common'])
  const canCreateCandidate = usePermission('candidates.candidate.create')
  const navigate = useNavigate()

  // ── Workspace state ──────────────────────────────────────────────────────
  const [surface, setSurface] = useState<'database' | 'active_work'>(initialSurface)
  const [activeMode, setActiveMode] = useState<'focus' | 'board' | 'follow_up_queue'>('focus')
  const [savedView, setSavedView] = useState('all_candidates')
  const [search, setSearch] = useState('')

  // ── Selection state ──────────────────────────────────────────────────────
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [selectedEngagementId, setSelectedEngagementId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // ── Settings state ───────────────────────────────────────────────────────
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

  const queryClient = useQueryClient()

  // ── Queries ──────────────────────────────────────────────────────────────
  const savedViewsQ = useQuery({
    queryKey: ['candidate-saved-views'],
    queryFn: async () => (await candidatesApi.savedViews()).data.data.views,
  })

  const databaseQ = useQuery({
    queryKey: ['candidate-database', savedView, search],
    queryFn: async () =>
      (await candidatesApi.database({ view: savedView, search: search || undefined, limit: 100 })).data.data,
    enabled: surface === 'database',
  })

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

  // ── Computed lists ────────────────────────────────────────────────────────
  const listItems = useMemo(
    () => (surface === 'database' ? ((databaseQ.data?.items || []) as CandidateSmartRow[]) : []),
    [databaseQ.data, surface],
  )

  const groupedActiveItems = useMemo(
    () => (surface === 'active_work' ? groupActiveWorkByCandidates(activeQ.data, activeMode) : []),
    [activeQ.data, activeMode, surface],
  )

  const isListLoading = surface === 'database' ? databaseQ.isLoading : activeQ.isLoading
  const commandCenter = commandQ.data as CCData | null
  const effectiveMode = workflowQ.data?.effective_workflow_mode || 'manual'

  // ── Effects ───────────────────────────────────────────────────────────────

  // Clear selection when switching surface
  useEffect(() => {
    setSelectedCandidateId(null)
    setSelectedEngagementId(null)
  }, [surface])

  // Auto-select first candidate once list loads
  useEffect(() => {
    if (selectedCandidateId !== null) return
    if (surface === 'database' && listItems.length > 0) {
      selectCandidate(listItems[0].id)
    } else if (surface === 'active_work' && groupedActiveItems.length > 0) {
      selectCandidate(groupedActiveItems[0].candidateId)
    }
  }, [surface, selectedCandidateId, listItems.length, groupedActiveItems.length]) // eslint-disable-line

  // Sync selectedEngagementId to first engagement when command center loads
  useEffect(() => {
    const firstEng = commandCenter?.tabs?.engagement?.[0]
    if (firstEng) setSelectedEngagementId(firstEng.id)
  }, [commandCenter?.tabs?.engagement?.length]) // eslint-disable-line

  // Sync workflow draft
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

  const openEmailComposer = () => {
    const email = commandCenter?.candidate?.email
    if (!email) {
      message.warning('Candidate has no email')
      return
    }
    setEmailComposerOpen(true)
  }

  /** Stage change always acts on the explicitly selected engagement */
  const handleStageChange = async (stage: string) => {
    if (!selectedCandidateId) return
    const engId = selectedEngagementId ?? commandCenter?.tabs?.engagement?.[0]?.id
    if (!engId) return message.warning('No engagement selected — open the Engagements tab to select one')
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
      setPendingStage(null)
      setPendingFromStage(null)
      setPendingEngagementId(null)
      setStageChangeNote('')
      queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
      queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
      queryClient.invalidateQueries({ queryKey: ['candidate-database'] })
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to update stage')
    } finally {
      setStageChangeLoading(false)
    }
  }

  const handleAddToActiveWork = async () => {
    if (!selectedCandidateId) return
    try {
      await http.post(`/candidates/${selectedCandidateId}/engagements/`, { stage: 'new_lead' })
      message.success('Added to Active Work')
      queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
      queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
      queryClient.invalidateQueries({ queryKey: ['candidate-database'] })
    } catch {
      message.error('Failed to add to active work')
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
    <div className="-m-8 flex flex-col bg-[#f8fafc]" style={{ height: 'calc(100vh - 64px)' }}>

      {/* ══ Level 1: Workspace Scope ══════════════════════════════════════════ */}
      <div className="flex h-12 flex-none items-center justify-between border-b border-slate-200 bg-white px-5 shadow-sm">
        <div className="flex items-center gap-3">
          <Sparkles size={15} className="text-indigo-600" />
          <span className="text-sm font-black text-slate-800 tracking-tight">Talent Hub</span>
          <div className="mx-1 h-4 w-px bg-slate-200" />
          {/* Database | Active Work — workspace scope switcher */}
          <div className="flex items-center gap-0.5 rounded-xl bg-slate-100 p-1">
            <button
              onClick={() => navigate('/candidates')}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition text-slate-500 hover:text-slate-700"
            >
              <Database size={12} /> Database
            </button>
            <button
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-sm"
            >
              <Activity size={12} /> Active Work
            </button>
          </div>
        </div>

        {/* Right side: workflow mode + actions */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1">
            <Select
              size="small"
              variant="borderless"
              style={{ width: 128 }}
              value={workflowDraft}
              onChange={setWorkflowDraft}
              options={WORKFLOW_MODE_OPTIONS}
            />
            <button
              onClick={() => updateWorkflow.mutate()}
              disabled={updateWorkflow.isPending}
              className="rounded-md bg-indigo-600 px-2.5 py-0.5 text-[11px] font-bold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {updateWorkflow.isPending ? '...' : 'Save'}
            </button>
          </div>
          <button
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['candidate-database'] })
              queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
            }}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
          >
            <RefreshCw size={13} />
          </button>
          {canCreateCandidate && (
            <button
              onClick={() => setAddOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700"
            >
              <Plus size={13} /> Add Candidate
            </button>
          )}
        </div>
      </div>

      {/* ══ Level 2: View Mode (Active Work only) ════════════════════════════ */}
      {surface === 'active_work' && (
        <div className="flex h-9 flex-none items-center gap-2 border-b border-slate-100 bg-slate-50 px-5">
          <span className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400 mr-1">View Mode</span>
          <div className="flex items-center gap-1">
            {([
              { value: 'focus', label: 'Focus' },
              { value: 'board', label: 'Board' },
              { value: 'follow_up_queue', label: 'Queue' },
            ] as const).map((opt) => (
              <button
                key={opt.value}
                onClick={() => setActiveMode(opt.value)}
                className={`rounded-lg px-3 py-1 text-[11px] font-semibold transition ${
                  activeMode === opt.value
                    ? 'bg-white text-indigo-700 shadow-sm border border-indigo-100'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ══ 3-Column Body ════════════════════════════════════════════════════ */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT: Candidate List */}
        <CandidateListPanel
          surface={surface}
          savedView={savedView}
          setSavedView={setSavedView}
          search={search}
          setSearch={setSearch}
          savedViewsQ={savedViewsQ}
          listItems={listItems}
          groupedActiveItems={groupedActiveItems}
          isLoading={isListLoading}
          selectedId={selectedCandidateId}
          onSelect={selectCandidate}
        />

        {/* CENTER: Command Center */}
        <div className="flex flex-1 flex-col overflow-hidden border-x border-slate-200 bg-white">
          {commandQ.isLoading && selectedCandidateId ? (
            <div className="flex flex-1 items-center justify-center">
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
              onAddToActiveWork={handleAddToActiveWork}
              onSubmitToJob={() => setSubmitOpen(true)}
              onOpenEmailComposer={openEmailComposer}
            />
          ) : (
            <CommandEmptyState
              isEmpty={surface === 'database' ? listItems.length === 0 : groupedActiveItems.length === 0}
              isLoading={isListLoading}
            />
          )}
        </div>

        {/* RIGHT: Action Panel */}
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
          onOpenEmailComposer={openEmailComposer}
        />
      </div>

      <AddCandidateWorkflowModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        sourceSurface={surface}
        onCompleted={() => {
          queryClient.invalidateQueries({ queryKey: ['candidate-database'] })
          queryClient.invalidateQueries({ queryKey: ['candidate-saved-views'] })
          queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
        }}
      />

      {/* ── Add Note Modal ───────────────────────────────────────────────────── */}
      <Modal open={addNoteOpen} onCancel={() => setAddNoteOpen(false)}
        onOk={async () => { const ok = await handleAddNote(noteText); if (ok) { setNoteText(''); setAddNoteOpen(false) } }}
        okText="Save Note" title="Add Recruiter Note">
        <Input.TextArea rows={4} value={noteText} onChange={(e) => setNoteText(e.target.value)}
          placeholder="Write recruiter note..." className="mt-2" />
      </Modal>

      <Modal
        open={stageChangeOpen}
        title="Confirm Stage Change"
        onCancel={() => {
          setStageChangeOpen(false)
          setStageChangeNote('')
          setPendingStage(null)
          setPendingFromStage(null)
          setPendingEngagementId(null)
        }}
        onOk={confirmStageChange}
        okText="Confirm"
        confirmLoading={stageChangeLoading}
        okButtonProps={{ disabled: !stageChangeNote.trim() }}
      >
        <div className="space-y-3 pt-1">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Current Stage</p>
              <p className="text-sm font-semibold text-slate-800">{stageLabel(pendingFromStage || undefined)}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Target Stage</p>
              <p className="text-sm font-semibold text-slate-800">{stageLabel(pendingStage || undefined)}</p>
            </div>
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Mandatory Note</p>
            <Input.TextArea
              rows={3}
              value={stageChangeNote}
              onChange={(e) => setStageChangeNote(e.target.value)}
              placeholder="Enter reason for this stage change"
            />
          </div>
        </div>
      </Modal>

            <AddToPoolModal />

{/* ── Submit to Job Modal ──────────────────────────────────────────────── */}
      {selectedCandidateId && commandCenter && (
        <SubmitToJobModal
          open={submitOpen}
          candidateId={selectedCandidateId}
          candidateName={commandCenter.candidate.full_name}
          candidate={commandCenter.candidate}
          existingEngagements={commandCenter.tabs?.engagement || []}
          onClose={() => setSubmitOpen(false)}
          onSuccess={() => {
            setSubmitOpen(false)
            queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
            queryClient.invalidateQueries({ queryKey: ['candidate-active-work'] })
            queryClient.invalidateQueries({ queryKey: ['candidate-database'] })
          }}
        />
      )}
      {selectedCandidateId && commandCenter && (
        <EmailComposerModal
          open={emailComposerOpen}
          onClose={() => setEmailComposerOpen(false)}
          candidateId={selectedCandidateId}
          candidateName={commandCenter.candidate.full_name}
          candidateEmail={commandCenter.candidate.email || ''}
          activeJobId={commandCenter.tabs?.engagement?.find(e => e.is_active && e.job)?.job ?? undefined}
          onSent={() => {
            queryClient.invalidateQueries({ queryKey: ['candidate-command-center', selectedCandidateId] })
          }}
        />
      )}
    </div>
  )
}

// ── Candidate List Panel (Left 300px) ─────────────────────────────────────────

function CandidateListPanel({ surface, savedView, setSavedView, search, setSearch, savedViewsQ, listItems, groupedActiveItems, isLoading, selectedId, onSelect }: any) {
  return (
    <div className="flex w-[300px] flex-none flex-col overflow-hidden border-r border-slate-200 bg-[#f8fafc]">
      {/* Search bar */}
      <div className="flex-none border-b border-slate-200 bg-white p-3">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100">
          <Search size={12} className="text-slate-400 shrink-0" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search candidates..."
            className="flex-1 bg-transparent text-xs text-slate-700 outline-none placeholder-slate-400"
          />
        </div>
      </div>

      {/* Saved views (database only) */}
      {surface === 'database' && (
        <div className="flex-none border-b border-slate-100 px-3 py-2">
          <p className="mb-1.5 text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">Saved Views</p>
          <div className="space-y-0.5">
            {(savedViewsQ.data || []).map((v: any) => (
              <button key={v.key} onClick={() => setSavedView(v.key)}
                className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                  savedView === v.key ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'}`}>
                <span className="truncate">{v.label}</span>
                {v.count > 0 && (
                  <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${savedView === v.key ? 'bg-indigo-200 text-indigo-700' : 'bg-slate-200 text-slate-500'}`}>
                    {v.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Count header */}
      <div className="flex-none border-b border-slate-100 bg-white px-3 py-2">
        <span className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">
          {surface === 'database'
            ? `${listItems.length} Candidates`
            : `${groupedActiveItems.length} Active Candidates`}
        </span>
      </div>

      {/* Scrollable candidate list */}
      <div className="flex-1 overflow-y-auto">
        <Spin spinning={isLoading}>
          <div className="space-y-1 p-2">
            {surface === 'database' ? (
              listItems.length === 0 && !isLoading ? (
                <Empty className="mt-10" image={Empty.PRESENTED_IMAGE_SIMPLE} description="No candidates in this view" />
              ) : (
                listItems.map((row: CandidateSmartRow) => (
                  <DatabaseListCard
                    key={row.id}
                    row={row}
                    selected={selectedId === row.id}
                    onSelect={() => onSelect(row.id)}
                  />
                ))
              )
            ) : (
              groupedActiveItems.length === 0 && !isLoading ? (
                <Empty className="mt-10" image={Empty.PRESENTED_IMAGE_SIMPLE} description="No active candidates" />
              ) : (
                groupedActiveItems.map((grp: GroupedCandidate) => (
                  <ActiveWorkListCard
                    key={grp.candidateId}
                    group={grp}
                    selected={selectedId === grp.candidateId}
                    onSelect={() => onSelect(grp.candidateId)}
                  />
                ))
              )
            )}
          </div>
        </Spin>
      </div>
    </div>
  )
}

function DatabaseListCard({ row, selected, onSelect }: { row: CandidateSmartRow; selected: boolean; onSelect: () => void }) {
  const globalState = GLOBAL_STATE[deriveGlobalStateKey(row)] || GLOBAL_STATE.dormant
  const stageChip = STAGE_CHIP[row.engagement_stage || '']
  const lastTouch = (row as any).last_activity || (row as any).last_touch

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-xl border p-3 text-left transition-all ${
        selected
          ? 'border-indigo-400 bg-white shadow-sm ring-2 ring-indigo-100'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start gap-2.5">
        <Avatar
          size={36}
          style={{ backgroundColor: avatarColor(row.name || ''), flexShrink: 0 }}
          className="font-bold text-white text-sm"
        >
          {(row.name || '?').charAt(0)}
        </Avatar>

        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-bold text-slate-900">{row.name}</div>
          <div className="truncate text-[11px] text-slate-500 mt-0.5">{row.current_title || 'No title'}</div>

          {/* Owner + last activity */}
          <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
            {row.owner && <span className="flex items-center gap-0.5"><span className="h-1.5 w-1.5 rounded-full bg-slate-300" />{String(row.owner).slice(0, 10)}</span>}
            {lastTouch && <span className="flex items-center gap-0.5"><Clock3 size={9} />{dayjs(lastTouch).fromNow()}</span>}
          </div>

          {/* State chips */}
          <div className="mt-1.5 flex flex-wrap items-center gap-1">
            {/* Global state — person-level truth */}
            <span
              className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
              style={{ backgroundColor: globalState.bg, color: globalState.color }}
            >
              {globalState.label}
            </span>
            {/* Engagement state — job-level truth */}
            {stageChip && (
              <span
                className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
                style={{ backgroundColor: stageChip.bg, color: stageChip.color }}
              >
                {stageChip.label}
              </span>
            )}
            {Object.entries(row.job_engagement_summary || {}).map(([stage, count]) => {
              const chip = STAGE_CHIP[stage]
              if (!chip || !count) return null
              return (
                <span
                  key={`job-${stage}`}
                  className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
                  style={{ backgroundColor: chip.bg, color: chip.color }}
                >
                  {chip.label}: {count}
                </span>
              )
            })}
          </div>
        </div>

        {selected && <ChevronRight size={14} className="mt-1 shrink-0 text-indigo-400" />}
      </div>
    </button>
  )
}

function ActiveWorkListCard({ group, selected, onSelect }: { group: GroupedCandidate; selected: boolean; onSelect: () => void }) {
  const ps = PRIORITY_STYLE[group.dominantPriority] || PRIORITY_STYLE.cold
  const globalState = GLOBAL_STATE[group.globalStateKey] || GLOBAL_STATE.dormant
  const summaryEntries = Object.entries(group.engagementSummary)

  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-xl border p-3 text-left transition-all ${
        selected
          ? 'border-indigo-400 bg-white shadow-sm ring-2 ring-indigo-100'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start gap-2.5">
        <div className="relative shrink-0">
          <Avatar
            size={36}
            style={{ backgroundColor: avatarColor(group.candidateName) }}
            className="font-bold text-white text-sm"
          >
            {group.candidateName.charAt(0)}
          </Avatar>
          {/* Priority dot */}
          <span
            className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white"
            style={{ backgroundColor: ps.color }}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-bold text-slate-900">{group.candidateName}</div>

          {/* Owner + last activity */}
          <div className="mt-0.5 flex items-center gap-2 text-[10px] text-slate-400">
            {group.ownerName && (
              <span className="flex items-center gap-0.5">
                <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                {group.ownerName.slice(0, 10)}
              </span>
            )}
            {group.lastActivity && (
              <span className="flex items-center gap-0.5"><Clock3 size={9} />{dayjs(group.lastActivity).fromNow()}</span>
            )}
          </div>

          {/* Global state — person-level truth */}
          <div className="mt-1.5 flex flex-wrap gap-1">
            <span
              className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
              style={{ backgroundColor: globalState.bg, color: globalState.color }}
            >
              {globalState.label}
            </span>

            {/* Engagement summary chips — job-level truth */}
            {summaryEntries.map(([stage, count]) => {
              const chip = STAGE_CHIP[stage]
              if (!chip) return null
              return (
                <span
                  key={stage}
                  className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
                  style={{ backgroundColor: chip.bg, color: chip.color }}
                >
                  {chip.label}{count > 1 ? ` ×${count}` : ''}
                </span>
              )
            })}
          </div>
        </div>
      </div>
    </button>
  )
}

// ── Command Empty State ───────────────────────────────────────────────────────

function CommandEmptyState({ isEmpty, isLoading }: { isEmpty: boolean; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }
  if (isEmpty) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
          <Users size={28} className="text-slate-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-600">No candidates found</p>
          <p className="mt-1 text-xs text-slate-400">Try a different view or add a new candidate.</p>
        </div>
      </div>
    )
  }
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50">
        <Users size={28} className="text-indigo-300" />
      </div>
      <div>
        <p className="text-sm font-bold text-slate-600">Select a Candidate</p>
        <p className="mt-1 text-xs text-slate-400">Click any candidate in the list to open their Command Center.</p>
      </div>
    </div>
  )
}

// ── Candidate Command Center Panel (Center) ───────────────────────────────────

function CandidateCommandCenterPanel({
  commandCenter, activeTab, setActiveTab,
  selectedEngagementId, setSelectedEngagementId,
  effectiveMode, onStageChange, onAddNote, onAddToActiveWork, onSubmitToJob, onOpenEmailComposer,
}: {
  commandCenter: CCData
  activeTab: string
  setActiveTab: (t: string) => void
  selectedEngagementId: string | null
  setSelectedEngagementId: (id: string) => void
  effectiveMode: WorkflowMode
  onStageChange: (s: string) => void
  onAddNote: () => void
  onAddToActiveWork: () => void
  onSubmitToJob: () => void
  onOpenEmailComposer: () => void
}) {
  const c = commandCenter.candidate
  const { data: poolMembershipsData } = useQuery({
    queryKey: ['candidate-pools', c.id],
    queryFn: () => talentPoolsApi.getCandidatePools(c.id),
  })
  const engagements = commandCenter.tabs?.engagement || []
  const currentPools = poolMembershipsData?.data?.data?.talent_pools || []
  const selectedEngagement = engagements.find((e) => e.id === selectedEngagementId) || engagements[0]

  // Derive person-level global state from candidate data
  const globalStateKey = (() => {
    if ((c as any).is_actively_looking) return 'open_to_work'
    if (engagements.length > 0) return deriveGlobalStateFromEngagements(engagements)
    return 'dormant'
  })()
  const globalState = GLOBAL_STATE[globalStateKey] || GLOBAL_STATE.dormant
  const hasPassport = !!c.passport_id
  const dominantPriority = engagements.reduce<'hot' | 'warm' | 'cold'>(
    (best, e) => {
      const order: Record<string, number> = { hot: 3, warm: 2, cold: 1 }
      return (order[e.priority] || 0) > (order[best] || 0) ? e.priority : best
    },
    'cold',
  )
  const ps = PRIORITY_STYLE[dominantPriority] || PRIORITY_STYLE.cold

  const tabs = [
    { key: 'overview',      label: <TabLabel icon={<Star size={12} />}        text="Overview" /> },
    { key: 'resume',        label: <TabLabel icon={<FileText size={12} />}     text="Resume" /> },
    { key: 'engagements',   label: <TabLabel icon={<Briefcase size={12} />}    text={`Engagements${engagements.length ? ` (${engagements.length})` : ''}`} /> },
    { key: 'activity',      label: <TabLabel icon={<Activity size={12} />}     text="Activity" /> },
    { key: 'notes',         label: <TabLabel icon={<ClipboardList size={12} />} text="Notes" /> },
    { key: 'communication', label: <TabLabel icon={<MessageSquare size={12} />} text="Communication" /> },
    { key: 'documents',     label: <TabLabel icon={<Paperclip size={12} />}    text="Documents" /> },
    { key: 'history',       label: <TabLabel icon={<History size={12} />}      text="History" /> },
    { key: 'automation',    label: <TabLabel icon={<BrainCircuit size={12} />} text="Automation" /> },
  ]

  return (
    <div className="flex h-full flex-col overflow-hidden">

      {/* ── Sticky Candidate Header ─────────────────────────────────────────── */}
      <div className="flex-none border-b border-slate-200 bg-white px-6 pt-4 pb-0">

        {/* Hero row: avatar + identity */}
        <div className="mb-3 flex items-start gap-4">
          <div className="relative shrink-0">
            <Avatar
              size={52}
              style={{ backgroundColor: avatarColor(c.full_name) }}
              className="font-black text-white text-xl shadow-sm ring-4 ring-slate-100"
            >
              {c.full_name.charAt(0)}
            </Avatar>
            {hasPassport && (
              <Tooltip title="Passport verified">
                <div className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 ring-2 ring-white">
                  <BadgeCheck size={10} className="text-white" />
                </div>
              </Tooltip>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h1 className="text-base font-black text-slate-900 leading-tight">{c.full_name}</h1>
                <p className="mt-0.5 text-sm text-slate-500">
                  {c.current_title || 'No title'}
                  {c.current_company && <span className="text-slate-300"> · </span>}
                  {c.current_company && <span>{c.current_company}</span>}
                </p>
              </div>
              <Tooltip title="View full profile">
                <button className="shrink-0 mt-0.5 text-slate-400 hover:text-slate-600">
                  <ExternalLink size={14} />
                </button>
              </Tooltip>
            </div>

            {/* Candidate meta — PERSON-LEVEL truth (not engagement) */}
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {/* Global state chip — primary identity */}
              <span
                className="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ring-1"
                style={{ backgroundColor: globalState.bg, color: globalState.color, borderColor: `${globalState.color}30` }}
              >
                {globalState.label}
              </span>

              {/* Priority */}
              <span
                className="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase"
                style={{ backgroundColor: ps.bg, color: ps.color }}
              >
                {ps.label}
              </span>

              {c.experience_years != null && (
                <MetaBadge icon={<Briefcase size={10} />} label={`${c.experience_years} yrs`} />
              )}
              {(c.current_location_city || c.current_location_country) && (
                <MetaBadge icon={<MapPin size={10} />} label={[c.current_location_city, c.current_location_country].filter(Boolean).join(', ')} />
              )}
              {c.availability_date && (
                <MetaBadge icon={<Calendar size={10} />} label={`Avail ${dayjs(c.availability_date).format('MMM D')}`} />
              )}
              {c.owner_user_id && (
                <MetaBadge icon={<User size={10} />} label={c.owner_user_id.slice(0, 10)} />
              )}
              {hasPassport && (
                <MetaBadge icon={<BadgeCheck size={10} />} label="Passport" color="emerald" />
              )}
              {c.is_agency_protected && (
                <span className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-violet-50 px-2.5 py-0.5 text-[10px] font-bold uppercase text-violet-700">
                  <ShieldCheck size={10} />
                  Agency Protected
                </span>
              )}
            </div>

            <div className="mt-3">
              <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">Pools</p>
              {currentPools.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {currentPools.map((pool: TalentPool) => (
                    <span
                      key={pool.id}
                      className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-slate-700"
                    >
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: pool.color || '#cbd5e1' }} />
                      {pool.name}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-slate-400">No pool memberships yet.</p>
              )}
            </div>
          </div>
        </div>

        {/* Primary Action Bar */}
        <div className="mb-3 flex flex-wrap items-center gap-1">
          <ActionBtn icon={<Phone size={12} />} label="Call"
            onClick={() => c.phone && window.open(`tel:${c.phone}`)} />
          <ActionBtn icon={<Mail size={12} />} label="Email"
            onClick={onOpenEmailComposer}
            disabled={!c.email}
            disabledReason="Candidate has no email" />
          <ActionBtn icon={<Calendar size={12} />} label="Schedule"
            onClick={() => message.info('Schedule feature coming soon')} />
          <ActionBtn icon={<Send size={12} />} label="Submit" primary
            onClick={onSubmitToJob} />
          <ActionBtn icon={<ClipboardList size={12} />} label="Add Note" onClick={onAddNote} />
          {/* Move Stage acts on selectedEngagement */}
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1">
            <Workflow size={10} className="text-slate-400 shrink-0" />
            <Select
              size="small"
              variant="borderless"
              placeholder={selectedEngagement ? stageLabel(selectedEngagement.stage) : 'Move Stage'}
              value={selectedEngagement?.stage}
              onChange={onStageChange}
              options={stageOptionsForEngagement(selectedEngagement)}
              style={{ width: 118, fontSize: 11 }}
            />
          </div>
          <ActionBtn icon={<Share2 size={12} />} label="Share"
            onClick={() => { navigator.clipboard.writeText(window.location.href); message.success('Link copied') }} />
          <ActionBtn icon={<Users size={12} />} label="Add to Pool" onClick={() => (window as any).openAddToPoolModal?.(c.id)} />
        </div>

        {/* Tab bar — renders inside header, content is below */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="small"
          tabBarStyle={{ marginBottom: 0 }}
          items={tabs.map((t) => ({ key: t.key, label: t.label, children: null }))}
        />
      </div>

      {/* ── Tab Content ────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto bg-[#f8fafc] p-5">
        {activeTab === 'overview'      && <OverviewTab cc={commandCenter} />}
        {activeTab === 'resume'        && <ResumeTab cc={commandCenter} />}
        {activeTab === 'engagements'   && (
          <EngagementsTab
            cc={commandCenter}
            selectedEngagementId={selectedEngagementId}
            setSelectedEngagementId={setSelectedEngagementId}
            onStageChange={onStageChange}
          />
        )}
        {activeTab === 'activity'      && <ActivityTab cc={commandCenter} selectedEngagementId={selectedEngagementId} />}
        {activeTab === 'notes'         && <NotesTab cc={commandCenter} onAddNote={onAddNote} selectedEngagementId={selectedEngagementId} />}
        {activeTab === 'communication' && <CommunicationTab cc={commandCenter} onOpenEmailComposer={onOpenEmailComposer} />}
        {activeTab === 'documents'     && <DocumentsTab cc={commandCenter} />}
        {activeTab === 'history'       && <HistoryTab cc={commandCenter} />}
        {activeTab === 'automation'    && <AutomationTab cc={commandCenter} effectiveMode={effectiveMode} />}
      </div>
    </div>
  )
}

function TabLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return <span className="flex items-center gap-1.5 py-0.5 text-[11px]">{icon}{text}</span>
}

function MetaBadge({ icon, label, color }: { icon: React.ReactNode; label: string; color?: 'emerald' }) {
  const cls = color === 'emerald' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'
  return (
    <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${cls}`}>
      {icon} {label}
    </span>
  )
}

function ActionBtn({
  icon,
  label,
  onClick,
  primary,
  disabled,
  disabledReason,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  primary?: boolean
  disabled?: boolean
  disabledReason?: string
}) {
  const btn = (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-[11px] font-semibold transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 ${
        primary
          ? 'border-indigo-500 bg-indigo-600 text-white hover:bg-indigo-700'
          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
      }`}
    >
      {icon} {label}
    </button>
  )

  if (disabled && disabledReason) {
    return <Tooltip title={disabledReason}>{btn}</Tooltip>
  }
  return btn
}

// ── Tab: Overview ─────────────────────────────────────────────────────────────

function OverviewTab({ cc }: { cc: CCData }) {
  const c = cc.candidate
  return (
    <div className="space-y-4">
      {c.is_agency_protected && (
        <SectionCard title="Protection Status" icon={<ShieldCheck size={13} className="text-violet-500" />}>
          <div className="grid grid-cols-2 gap-2">
            <InfoCell label="Status" value="Agency Protected" />
            <InfoCell label="Protected Until" value={formatProtectionDate(c.protected_until)} />
            <InfoCell label="Scope" value={protectionScopeLabel(c.protection_scope)} />
            <InfoCell label="Note" value="Candidate cannot be reused outside agreed scope during protection period." />
          </div>
        </SectionCard>
      )}

      <SectionCard title="Contact" icon={<User size={13} className="text-blue-500" />}>
        <div className="grid grid-cols-2 gap-2">
          <InfoCell label="Email" value={c.email} />
          <InfoCell label="Phone" value={c.phone} href={`tel:${c.phone}`} />
          <InfoCell label="Location" value={[c.current_location_city, c.current_location_country].filter(Boolean).join(', ')} />
          <InfoCell label="LinkedIn" value={c.linkedin_url ? 'View Profile' : undefined} href={c.linkedin_url || undefined} />
          <InfoCell label="WhatsApp" value={c.whatsapp} href={c.whatsapp ? `https://wa.me/${c.whatsapp}` : undefined} />
          <InfoCell label="Nationality" value={(c as any).nationality} />
        </div>
      </SectionCard>

      <SectionCard title="Professional" icon={<Briefcase size={13} className="text-purple-500" />}>
        <div className="grid grid-cols-2 gap-2">
          <InfoCell label="Experience" value={c.experience_years != null ? `${c.experience_years} years` : undefined} />
          <InfoCell label="Notice Period" value={c.notice_period_days != null ? `${c.notice_period_days} days` : undefined} />
          <InfoCell label="Availability" value={c.availability_date ? dayjs(c.availability_date).format('MMM D, YYYY') : undefined} />
          <InfoCell label="Source" value={c.source} />
          <InfoCell label="Source Detail" value={c.source_detail} />
          <InfoCell label="Owner" value={c.owner_user_id} />
        </div>
      </SectionCard>

      <SectionCard title="Compensation" icon={<Star size={13} className="text-amber-500" />}>
        <div className="grid grid-cols-2 gap-2">
          <InfoCell label="Salary Min" value={c.expected_salary_min ? `${c.salary_currency || ''} ${c.expected_salary_min}`.trim() : undefined} />
          <InfoCell label="Salary Max" value={c.expected_salary_max ? `${c.salary_currency || ''} ${c.expected_salary_max}`.trim() : undefined} />
          <InfoCell label="Currency" value={c.salary_currency} />
        </div>
      </SectionCard>

      {Array.isArray(c.skills) && c.skills.length > 0 && (
        <SectionCard title="Skills" icon={<Target size={13} className="text-green-500" />}>
          <div className="flex flex-wrap gap-1.5">
            {(c.skills as string[]).map((s) => (
              <span key={s} className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-medium text-indigo-700">{s}</span>
            ))}
          </div>
        </SectionCard>
      )}

      {Array.isArray(c.languages) && c.languages.length > 0 && (
        <SectionCard title="Languages" icon={<MessageSquare size={13} className="text-cyan-500" />}>
          <div className="flex flex-wrap gap-1.5">
            {(c.languages as string[]).map((l) => (
              <span key={l} className="rounded-full bg-cyan-50 px-2.5 py-0.5 text-[11px] font-medium text-cyan-700">{l}</span>
            ))}
          </div>
        </SectionCard>
      )}

      {Array.isArray(c.tags) && c.tags.length > 0 && (
        <SectionCard title="Tags" icon={<Flag size={13} className="text-rose-500" />}>
          <div className="flex flex-wrap gap-1.5">
            {(c.tags as string[]).map((tag) => (
              <span key={tag} className="rounded-full bg-rose-50 px-2.5 py-0.5 text-[11px] font-medium text-rose-700">{tag}</span>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  )
}

// ── Tab: Resume ───────────────────────────────────────────────────────────────

function ResumeTab({ cc }: { cc: CCData }) {
  const resumeUrl = cc.tabs?.documents?.resume_url
  return (
    <div className="flex flex-col gap-3" style={{ minHeight: 560 }}>
      <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
        <span className="text-xs font-bold text-slate-700">Resume Viewer</span>
        <div className="flex items-center gap-2">
          {resumeUrl && (
            <button onClick={() => window.open(resumeUrl, '_blank')}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-[11px] font-semibold text-slate-600 hover:bg-slate-50">
              <ExternalLink size={11} /> Open in tab
            </button>
          )}
          <button onClick={() => resumeUrl && window.open(resumeUrl, '_blank')}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-[11px] font-semibold text-slate-600 hover:bg-slate-50">
            <FileDown size={11} /> Download
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" style={{ minHeight: 500 }}>
        {resumeUrl ? (
          <iframe src={resumeUrl} className="h-full w-full" title="Candidate Resume"
            style={{ border: 'none', minHeight: 500 }} />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 py-20">
            <FileText size={28} className="text-slate-300" />
            <div className="text-center">
              <p className="text-sm font-semibold text-slate-500">No Resume Uploaded</p>
              <p className="mt-1 text-xs text-slate-400">Upload a resume to view it here</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Tab: Engagements ──────────────────────────────────────────────────────────
// Each row = one job/client engagement track. Clicking selects that engagement
// for stage actions. Stage changes are scoped to the selected engagement only.

function EngagementsTab({ cc, selectedEngagementId, setSelectedEngagementId, onStageChange }: {
  cc: CCData
  selectedEngagementId: string | null
  setSelectedEngagementId: (id: string) => void
  onStageChange: (stage: string) => void
}) {
  const engagements: ActiveWorkEngagement[] = cc.tabs?.engagement || []
  const jobsMatches: any[] = cc.tabs?.jobs_matches || []

  return (
    <div className="space-y-4">
      {/* Instruction banner */}
      {engagements.length > 0 && (
        <div className="flex items-center gap-2 rounded-xl border border-blue-100 bg-blue-50 px-4 py-2.5">
          <Workflow size={13} className="text-blue-500 shrink-0" />
          <p className="text-[11px] text-blue-700 font-medium">
            Click an engagement to select it. Stage changes in the action bar apply to the selected engagement only.
          </p>
        </div>
      )}

      {/* Active Engagements */}
      <SectionCard
        title={`Active Engagements (${engagements.length})`}
        icon={<Briefcase size={13} className="text-indigo-500" />}
      >
        {engagements.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No active engagements — add candidate to Active Work to begin tracking" />
        ) : (
          <div className="space-y-2">
            {engagements.map((eng) => {
              const isSelected = eng.id === selectedEngagementId
              const chip = STAGE_CHIP[eng.stage] || STAGE_CHIP.general_pool
              const ps = PRIORITY_STYLE[eng.priority] || PRIORITY_STYLE.cold

              return (
                <div
                  key={eng.id}
                  onClick={() => setSelectedEngagementId(eng.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition-all ${
                    isSelected
                      ? 'border-indigo-400 bg-indigo-50/50 ring-2 ring-indigo-100'
                      : 'border-slate-100 bg-white hover:border-slate-200 hover:shadow-sm'
                  }`}
                >
                  {/* Engagement header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-indigo-600 text-xs">
                        {(eng.job_title || 'J').charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-slate-800 truncate">
                          {eng.job_title || 'General Pool Position'}
                        </p>
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                          #{eng.id.slice(0, 12)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span
                        className="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase"
                        style={{ backgroundColor: chip.bg, color: chip.color }}
                      >
                        {chip.label}
                      </span>
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase"
                        style={{ backgroundColor: ps.bg, color: ps.color }}
                      >
                        {eng.priority}
                      </span>
                    </div>
                  </div>

                  {/* Engagement meta row */}
                  <div className="mt-3 grid grid-cols-3 gap-x-4 gap-y-1.5 border-t border-slate-100 pt-3">
                    <div>
                      <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Owner</p>
                      <p className="text-[11px] font-semibold text-slate-700 truncate">{eng.owner_name || '—'}</p>
                    </div>
                    <div>
                      <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Last Activity</p>
                      <p className="text-[11px] font-semibold text-slate-700">
                        {eng.last_activity_at ? dayjs(eng.last_activity_at).fromNow() : '—'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Follow Up</p>
                      <p className={`text-[11px] font-semibold truncate ${eng.follow_up_at && dayjs(eng.follow_up_at).isBefore(dayjs()) ? 'text-red-600' : 'text-slate-700'}`}>
                        {eng.follow_up_at ? dayjs(eng.follow_up_at).format('MMM D') : '—'}
                      </p>
                    </div>
                  </div>

                  {/* Next action suggestion */}
                  <div className="mt-2 flex items-center gap-1.5">
                    <Target size={10} className="text-indigo-400 shrink-0" />
                    <p className="text-[10px] text-indigo-600 font-medium">{nextBestAction(eng.stage)}</p>
                  </div>

                  {/* Stage change controls — only on selected engagement */}
                  {isSelected && (
                    <div className="mt-3 flex items-center gap-2 border-t border-indigo-100 pt-3">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">Move Stage</span>
                      <Select
                        size="small"
                        value={eng.stage}
                        onChange={onStageChange}
                        options={stageOptionsForEngagement(eng).map((s) => ({
                          value: s.value,
                          label: (
                            <span style={{ color: STAGE_CHIP[s.value]?.color || '#64748b', fontWeight: 600, fontSize: 11 }}>
                              {s.label}
                            </span>
                          ),
                        }))}
                        style={{ flex: 1 }}
                        className="flex-1"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </SectionCard>

      {/* Job matches (read-only, non-active) */}
      {jobsMatches.filter((j) => !engagements.find((e) => e.job === j.job_id)).length > 0 && (
        <SectionCard title="Job Matches" icon={<Star size={13} className="text-emerald-500" />}>
          <div className="space-y-2">
            {jobsMatches
              .filter((j) => !engagements.find((e) => e.job === j.job_id))
              .map((j) => {
                const chip = STAGE_CHIP[j.stage] || STAGE_CHIP.general_pool
                return (
                  <div key={j.job_id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 font-bold text-emerald-600 text-xs">M</div>
                      <div>
                        <p className="text-xs font-semibold text-slate-800">{(j as any).job_title || 'Job Match'}</p>
                        <p className="text-[10px] font-mono text-slate-400">{j.job_id?.slice(0, 16)}</p>
                      </div>
                    </div>
                    <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase"
                      style={{ backgroundColor: chip.bg, color: chip.color }}>
                      {chip.label}
                    </span>
                  </div>
                )
              })}
          </div>
        </SectionCard>
      )}

      {/* Companies */}
      {cc.candidate.current_company && (
        <SectionCard title="Companies" icon={<Building2 size={13} className="text-orange-500" />}>
          <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-50 font-bold text-orange-600 text-xs">
                {cc.candidate.current_company.charAt(0)}
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800">{cc.candidate.current_company}</p>
                <p className="text-[10px] text-slate-400">Current employer</p>
              </div>
            </div>
            <span className="rounded-full bg-orange-50 px-2.5 py-0.5 text-[10px] font-bold uppercase text-orange-600">Current</span>
          </div>
        </SectionCard>
      )}

      {/* Agency */}
      {cc.candidate.source === 'agency' && (
        <SectionCard title="Agency" icon={<Users size={13} className="text-purple-500" />}>
          <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-50 font-bold text-purple-600 text-xs">A</div>
              <div>
                <p className="text-xs font-semibold text-slate-800">{cc.candidate.source_detail || 'Agency'}</p>
                <p className="text-[10px] text-slate-400">Sourced via agency</p>
              </div>
            </div>
            <span className="rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold uppercase text-purple-600">Agency</span>
          </div>
        </SectionCard>
      )}
    </div>
  )
}

// ── Tab: Activity ─────────────────────────────────────────────────────────────

function ActivityTab({ cc, selectedEngagementId }: { cc: CCData; selectedEngagementId: string | null }) {
  const [filter, setFilter] = useState<'this_engagement' | 'all_engagements' | 'notes' | 'activity' | 'system'>('this_engagement')
  const structuredActivity = (cc.tabs?.structured_activity || []).map((a: any) => ({ ...a, _kind: 'activity' as const }))
  const structuredNotes = (cc.tabs?.structured_notes || []).map((n: any) => ({
    ...n,
    action_type: 'note.added',
    actor: n.author || 'System',
    method: 'manual',
    metadata_json: { note_type: n.note_type, content: n.content },
    _kind: 'note' as const,
  }))

  const feed = [...structuredActivity, ...structuredNotes]
    .filter((item: any) => {
      if (filter === 'this_engagement') {
        if (!selectedEngagementId) return !item.engagement_id
        return item.engagement_id === selectedEngagementId
      }
      if (filter === 'notes') return item._kind === 'note'
      if (filter === 'activity') return item._kind === 'activity'
      if (filter === 'system') return `${item.method || ''}`.toLowerCase() === 'system' || `${item.actor_type || ''}`.toLowerCase() === 'system'
      return true
    })
    .sort((a: any, b: any) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())

  return (
    <SectionCard title="Activity Timeline" icon={<Activity size={13} className="text-indigo-500" />}>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {[
          ['this_engagement', 'This Engagement'],
          ['all_engagements', 'All Engagements'],
          ['notes', 'Notes'],
          ['activity', 'Activity'],
          ['system', 'System'],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key as any)}
            className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${filter === key ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
          >
            {label}
          </button>
        ))}
      </div>
      {feed.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No activity for selected filter" />
      ) : (
        <div className="space-y-2.5">
          {feed.map((item: any, idx: number) => {
            const toneKey = item._kind === 'note' ? 'note' : actionToneKey(item.action_type, item.method)
            const tone = FEED_TONE[toneKey] || FEED_TONE.system
            return (
              <div key={`${item._kind}-${idx}`} className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
                <div className="mb-1 flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${tone.badge}`}>
                    {tone.icon} {tone.label}
                  </span>
                  <span className="text-[10px] text-slate-400">{dayjs(item.created_at).format('h:mm A')}</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  {(item.context_type === 'job' ? 'Job engagement' : 'General')}{' '}
                  • {(item.method || 'manual').toString().replace(/_/g, ' ')} • {dayjs(item.created_at).fromNow()}
                </p>
                <p className="mt-0.5 text-[11px] font-semibold text-slate-700">{item.actor || 'System'}</p>
                {item._kind === 'note' && (
                  <p className="mt-1 text-xs text-slate-600 leading-relaxed">{item.content}</p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </SectionCard>
  )
}

// ── Tab: Notes ────────────────────────────────────────────────────────────────

function NotesTab({ cc, onAddNote, selectedEngagementId }: { cc: CCData; onAddNote: () => void; selectedEngagementId: string | null }) {
  const [scope, setScope] = useState<'this_engagement' | 'all_engagements'>('this_engagement')
  const notes = cc.tabs?.structured_notes || []
  const filteredNotes = notes.filter((n: any) => {
    if (scope === 'all_engagements') return true
    if (!selectedEngagementId) return !n.engagement_id
    return n.engagement_id === selectedEngagementId
  })
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{filteredNotes.length} Notes</span>
        <button onClick={onAddNote}
          className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-[11px] font-bold text-white hover:bg-indigo-700">
          <Plus size={11} /> Add Note
        </button>
      </div>
      <div className="flex gap-1.5">
        {[
          ['this_engagement', 'This Engagement'],
          ['all_engagements', 'All'],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setScope(key as any)}
            className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${scope === key ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
          >
            {label}
          </button>
        ))}
      </div>
      {filteredNotes.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-white py-10">
          <ClipboardList size={24} className="text-slate-300" />
          <p className="text-xs text-slate-400">No notes yet</p>
          <button onClick={onAddNote}
            className="rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-50">
            Add first note
          </button>
        </div>
      ) : (
        filteredNotes.map((n: any) => (
          <div key={n.id} className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[9px] font-bold uppercase text-amber-600">
                {n.note_type || 'General'}
              </span>
              <span className="text-[10px] text-slate-400">{dayjs(n.created_at).fromNow()}</span>
            </div>
            <p className="text-[10px] text-slate-500 mb-1">
              {(n.context_type === 'job' ? 'Job engagement' : 'General')} • {dayjs(n.created_at).format('h:mm A')}
            </p>
            <p className="text-xs leading-relaxed text-slate-700">{n.content}</p>
            {n.author && (
              <p className="mt-2 flex items-center gap-1 text-[10px] text-slate-400">
                <User size={9} /> {n.author}
              </p>
            )}
          </div>
        ))
      )}
    </div>
  )
}

// ── Tab: Communication ────────────────────────────────────────────────────────

function CommunicationTab({ cc, onOpenEmailComposer }: { cc: CCData; onOpenEmailComposer: () => void }) {
  const comm = cc.tabs?.communication
  const c = cc.candidate
  const [tab, setTab] = useState<'emails' | 'messages'>('emails')

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Last Contact</p>
          <p className="mt-1 text-sm font-semibold text-slate-700">
            {comm?.last_contact_at ? dayjs(comm.last_contact_at).format('MMM D, YYYY') : 'Never'}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Next Follow-up</p>
          <p className={`mt-1 text-sm font-semibold ${comm?.next_follow_up_at && dayjs(comm.next_follow_up_at).isBefore(dayjs()) ? 'text-red-600' : 'text-slate-700'}`}>
            {comm?.next_follow_up_at ? dayjs(comm.next_follow_up_at).format('MMM D, h:mm A') : 'Not scheduled'}
          </p>
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
        {(['emails', 'messages'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-semibold transition ${tab === t ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
            {t === 'emails' ? <Mail size={12} /> : <MessageSquare size={12} />}
            {t === 'emails' ? 'Emails' : 'Messages'}
          </button>
        ))}
      </div>

      {tab === 'emails' && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 bg-white py-10">
          <Mail size={24} className="text-slate-300" />
          <div className="text-center">
            <p className="text-xs font-semibold text-slate-500">No email threads yet</p>
            <p className="mt-1 text-[11px] text-slate-400">Email conversations will appear here</p>
          </div>
          <Tooltip title={!c.email ? 'Candidate has no email' : undefined}>
            <button onClick={onOpenEmailComposer}
              disabled={!c.email}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-[11px] font-bold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">
              Send First Email
            </button>
          </Tooltip>
        </div>
      )}

      {tab === 'messages' && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 bg-white py-10">
          <MessageSquare size={24} className="text-slate-300" />
          <div className="text-center">
            <p className="text-xs font-semibold text-slate-500">No messages yet</p>
            <p className="mt-1 text-[11px] text-slate-400">WhatsApp & SMS conversations will appear here</p>
          </div>
          {c.whatsapp && (
            <button onClick={() => window.open(`https://wa.me/${c.whatsapp}`)}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-[11px] font-bold text-slate-600 hover:bg-slate-50">
              Open WhatsApp
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ── Tab: Documents ────────────────────────────────────────────────────────────

function DocumentsTab({ cc }: { cc: CCData }) {
  const docs = cc.tabs?.documents || {}
  const c = cc.candidate
  const files = [
    docs.resume_url && { label: 'Resume', url: docs.resume_url, icon: FileText, bg: 'bg-blue-50', color: 'text-blue-500' },
    docs.profile_cv_url && { label: 'Profile CV', url: docs.profile_cv_url, icon: FileDown, bg: 'bg-green-50', color: 'text-green-500' },
    c.linkedin_url && { label: 'LinkedIn', url: c.linkedin_url, icon: Link2, bg: 'bg-sky-50', color: 'text-sky-500' },
  ].filter(Boolean) as Array<{ label: string; url: string; icon: any; bg: string; color: string }>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{files.length} Documents</span>
        <button className="flex items-center gap-1.5 rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-50">
          <Plus size={11} /> Upload
        </button>
      </div>
      {files.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-white py-10">
          <Paperclip size={24} className="text-slate-300" />
          <p className="text-xs text-slate-400">No documents</p>
        </div>
      ) : (
        files.map((f) => (
          <div key={f.label} className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-3.5 shadow-sm hover:shadow-md transition">
            <div className="flex items-center gap-3">
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${f.bg}`}>
                <f.icon size={15} className={f.color} />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800">{f.label}</p>
                <p className="text-[10px] text-slate-400 truncate max-w-[180px]">{f.url}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => window.open(f.url, '_blank')}
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:bg-slate-50">
                <ExternalLink size={11} />
              </button>
              <button onClick={() => window.open(f.url, '_blank')}
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:bg-slate-50">
                <FileDown size={11} />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

// ── Tab: History ──────────────────────────────────────────────────────────────

function HistoryTab({ cc }: { cc: CCData }) {
  const history = cc.tabs?.history || []
  return (
    <SectionCard title="Global Candidate History" icon={<History size={13} className="text-slate-500" />}>
      {history.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No history recorded" />
      ) : (
        <div className="relative pl-5 space-y-0">
          <div className="absolute left-2 top-0 bottom-0 w-px bg-slate-200" />
          {history.map((item: any, idx: number) => (
            <div key={idx} className="relative mb-4">
              <div className="absolute -left-[11px] top-2 h-2 w-2 rounded-full bg-slate-300 ring-2 ring-white" />
              <div className="rounded-lg border border-slate-100 bg-white p-3">
                <div className="flex items-start justify-between">
                  <span className="text-xs font-semibold text-slate-700">{item.event || item.action || 'Event'}</span>
                  <span className="text-[10px] text-slate-400">{dayjs(item.created_at || item.timestamp).format('MMM D, YYYY')}</span>
                </div>
                {(item.details || item.description) && (
                  <p className="mt-1 text-xs text-slate-500">{item.details || item.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  )
}

// ── Tab: Automation ───────────────────────────────────────────────────────────

function AutomationTab({ cc, effectiveMode }: { cc: CCData; effectiveMode: WorkflowMode }) {
  const auto = cc.tabs?.automations
  if (!auto) return <Empty description="Automation data unavailable" />
  return (
    <div className="space-y-4">
      {/* AI strategy hero */}
      <div className="relative overflow-hidden rounded-2xl bg-indigo-600 p-5 text-white">
        <Bot className="absolute -right-4 -bottom-4 h-28 w-28 opacity-10" />
        <div className="relative z-10">
          <div className="mb-2 flex items-center gap-2">
            <BrainCircuit size={16} />
            <span className="text-xs font-black uppercase tracking-widest">AI Strategy</span>
          </div>
          <p className="text-indigo-100 text-xs leading-relaxed mb-4">
            Mode: <span className="font-bold text-white uppercase">{stageLabel(auto.workflow_mode)}</span>.{' '}
            Suggestions {auto.behavior?.suggestions_enabled ? 'ON' : 'OFF'}.
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Nurture', on: auto.auto_nurture_enabled },
              { label: 'Follow-up', on: auto.auto_followup_enabled },
            ].map(({ label, on }) => (
              <div key={label} className="rounded-xl bg-white/10 p-3 border border-white/10">
                <p className="text-[9px] font-bold uppercase opacity-60 mb-0.5">{label}</p>
                <p className="text-xs font-black">{on ? 'ACTIVE' : 'INACTIVE'}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <SectionCard title="Automation Toggles" icon={<BrainCircuit size={13} className="text-indigo-500" />}>
        <div className="space-y-2.5">
          {[
            { label: 'Automation Engine', on: auto.automation_enabled },
            { label: 'Stage Suggestions', on: auto.auto_stage_suggestions_enabled },
            { label: 'Auto Nurture', on: auto.auto_nurture_enabled },
            { label: 'Auto Follow-up', on: auto.auto_followup_enabled },
          ].map(({ label, on }) => (
            <div key={label} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3.5 py-2.5">
              <span className="text-xs font-semibold text-slate-700">{label}</span>
              <Switch size="small" checked={on} disabled />
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Workflow Policy" icon={<Workflow size={13} className="text-slate-500" />}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-700">Effective Mode</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Global default applied to this candidate</p>
          </div>
          <Tag color={modeColor(effectiveMode)} className="font-bold uppercase text-[10px]">
            {stageLabel(effectiveMode)}
          </Tag>
        </div>
      </SectionCard>
    </div>
  )
}

// ── Action Panel (Right 268px) ────────────────────────────────────────────────

function ActionPanel({
  commandCenter, selectedEngagementId, setSelectedEngagementId, quickNoteText, setQuickNoteText,
  onSaveQuickNote, onStageChange, effectiveMode, onOpenEmailComposer,
}: {
  commandCenter: CCData | null
  selectedEngagementId: string | null
  setSelectedEngagementId: (id: string | null) => void
  quickNoteText: string
  setQuickNoteText: (v: string) => void
  onSaveQuickNote: () => void
  onStageChange: (s: string) => void
  effectiveMode: WorkflowMode
  onOpenEmailComposer: () => void
}) {
  const c = commandCenter?.candidate
  const engagements = commandCenter?.tabs?.engagement || []
  const selectedEng = engagements.find((e) => e.id === selectedEngagementId) || engagements[0] || null
  const structuredActivity = commandCenter?.tabs?.structured_activity || []
  const recentActivity = structuredActivity
    .filter((a: any) => {
      if (!selectedEng?.id) return !a.engagement_id
      return a.engagement_id === selectedEng.id
    })
    .slice(0, 5)

  return (
    <div className="flex w-[268px] flex-none flex-col overflow-hidden border-l border-slate-200 bg-white">
      <div className="flex-none border-b border-slate-100 px-4 py-2.5">
        <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">Action Panel</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[9px] font-black uppercase tracking-wider text-slate-400 mb-1.5">Working On</p>
          <p className="text-xs font-bold text-slate-800 truncate">{selectedEng?.job_title || 'General Candidate Track'}</p>
          <p className="text-[10px] text-slate-500 truncate">{c?.current_company || 'Company / Client'}</p>
          <p className="text-[10px] text-slate-500">Stage: <span className="font-semibold text-slate-700">{stageLabel(selectedEng?.stage || 'new_lead')}</span></p>
          {selectedEng?.owner_name && (
            <p className="text-[10px] text-slate-500">Owner: <span className="font-semibold text-slate-700">{selectedEng.owner_name}</span></p>
          )}
          <div className="mt-2">
            <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1">Select Engagement</p>
            <Select
              size="small"
              value={selectedEng?.id}
              placeholder="Select engagement"
              onChange={(id) => setSelectedEngagementId(id)}
              options={engagements.map((eng: any) => ({
                value: eng.id,
                label: `${eng.job_title || 'General'} — ${stageLabel(eng.stage)}`,
              }))}
              className="w-full"
            />
          </div>
        </div>

        {/* Next Action */}
        <div className="rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-white p-3.5">
          <div className="mb-2 flex items-center gap-1.5">
            <Target size={12} className="text-indigo-500" />
            <span className="text-[9px] font-black uppercase tracking-wider text-indigo-600">Next Action</span>
          </div>

          {c ? (
            <>
              <p className="text-xs font-bold text-slate-800 mb-2">{nextBestAction(selectedEng?.stage)}</p>

              <div className="space-y-1.5">
                <button onClick={() => c.phone && window.open(`tel:${c.phone}`)}
                  className="flex w-full items-center gap-2 rounded-lg border border-indigo-200 bg-white px-3 py-2 text-[11px] font-semibold text-indigo-700 hover:bg-indigo-50 transition">
                  <Phone size={11} /> Call {c.first_name}
                </button>
                <Tooltip title={!c.email ? 'Candidate has no email' : undefined}>
                  <button onClick={onOpenEmailComposer}
                    disabled={!c.email}
                    className="flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 transition disabled:cursor-not-allowed disabled:opacity-50">
                    <Mail size={11} /> Send Email
                  </button>
                </Tooltip>
                <button onClick={() => message.info('Schedule feature coming soon')}
                  className="flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 transition">
                  <Calendar size={11} /> Schedule Interview
                </button>
              </div>

              {/* Quick stage move for selected engagement */}
              {selectedEng && (
                <div className="mt-2.5 pt-2.5 border-t border-indigo-100">
                  <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Move Stage</p>
                  <Select
                    size="small"
                    value={selectedEng.stage}
                    onChange={onStageChange}
                    options={stageOptionsForEngagement(selectedEng)}
                    className="w-full"
                  />
                </div>
              )}
            </>
          ) : (
            <p className="text-center text-xs text-slate-400 py-4">Select a candidate</p>
          )}
        </div>

        {/* Quick Note */}
        <div className="rounded-xl border border-slate-200 bg-white p-3.5">
          <div className="mb-2 flex items-center gap-1.5">
            <ClipboardList size={12} className="text-amber-500" />
            <span className="text-[9px] font-black uppercase tracking-wider text-amber-600">Quick Note</span>
          </div>
          <textarea
            rows={3}
            value={quickNoteText}
            onChange={(e) => setQuickNoteText(e.target.value)}
            disabled={!c}
            placeholder={c ? `Note for ${c.first_name}...` : 'Select a candidate...'}
            className="w-full resize-none rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700 outline-none placeholder-slate-400 focus:border-indigo-300 focus:bg-white focus:ring-2 focus:ring-indigo-100 disabled:opacity-50"
          />
          <button
            onClick={onSaveQuickNote}
            disabled={!c || !quickNoteText.trim()}
            className="mt-2 w-full rounded-lg bg-amber-500 py-1.5 text-[11px] font-bold text-white hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            Save Note
          </button>
        </div>

        {/* Recent Activity */}
        <div className="rounded-xl border border-slate-200 bg-white p-3.5">
          <div className="mb-2.5 flex items-center gap-1.5">
            <Activity size={12} className="text-slate-400" />
            <span className="text-[9px] font-black uppercase tracking-wider text-slate-400">Recent Activity</span>
          </div>
          {recentActivity.length === 0 ? (
            <p className="py-3 text-center text-[11px] text-slate-400">
              {c ? 'No recent activity' : 'Select a candidate'}
            </p>
          ) : (
            <div className="space-y-2">
              {recentActivity.map((item: any, idx: number) => (
                <div key={idx} className="rounded-lg border border-slate-100 bg-slate-50 p-2">
                  <div className="min-w-0">
                    {(() => {
                      const tone = FEED_TONE[actionToneKey(item.action_type, item.method)] || FEED_TONE.system
                      return (
                        <>
                          <p className={`truncate text-[11px] font-semibold ${tone.text}`}>{tone.icon} {tone.label}</p>
                          <p className="text-[10px] text-slate-400">{(item.context_type === 'job' ? 'Job' : 'General')} • {(item.method || 'manual')} • {dayjs(item.created_at).fromNow()}</p>
                          <p className="text-[10px] text-slate-500">{item.actor || 'System'}</p>
                        </>
                      )
                    })()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Workflow indicator */}
        {c && (
          <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
            <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Workflow</span>
            <Tag color={modeColor(effectiveMode)} className="m-0 border-none text-[9px] font-bold uppercase px-2">
              {stageLabel(effectiveMode)}
            </Tag>
          </div>
        )}
      </div>
    </div>
  )
}

function EmailComposerModal({
  open,
  onClose,
  candidateId,
  candidateName,
  candidateEmail,
  activeJobId,
  onSent,
}: {
  open: boolean
  onClose: () => void
  candidateId: string
  candidateName: string
  candidateEmail: string
  activeJobId?: string
  onSent: () => void
}) {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [unresolvedTags, setUnresolvedTags] = useState<string[]>([])

  const { data: accountsData, isLoading: accountsLoading } = useQuery({
    queryKey: ['email_accounts_candidate_composer'],
    queryFn: async () => (await communicationsApi.listEmailAccounts()).data.data,
    enabled: open,
  })
  const { data: preferencesData } = useQuery({
    queryKey: ['email_preferences_candidate_composer'],
    queryFn: async () => (await communicationsApi.getEmailPreferences()).data.data,
    enabled: open,
  })
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['email_templates_candidate_composer'],
    queryFn: async () => (await communicationsApi.listEmailTemplates()).data.data,
    enabled: open,
  })
  const { data: quickRepliesData, isLoading: quickRepliesLoading } = useQuery({
    queryKey: ['quick_replies_candidate_composer'],
    queryFn: async () => (await communicationsApi.listQuickReplies()).data.data,
    enabled: open,
  })

  const accounts = ((accountsData as any)?.email_accounts || []) as EmailAccount[]
  const templates = ((templatesData as any)?.email_templates || []) as EmailTemplateDef[]
  const quickReplies = ((quickRepliesData as any)?.quick_replies || []) as QuickReply[]
  const preferences = (preferencesData as any)?.email_preferences
  const connectedAccounts = accounts.filter((a) => a.status === 'connected' && a.can_send)
  const noConnectedEmail = connectedAccounts.length === 0

  useEffect(() => {
    if (!open) return
    const defaultFromPreference = preferences?.default_sender_account
    const defaultFromAccount = connectedAccounts.find((a) => a.is_default_sender)?.id
    const firstAvailable = connectedAccounts[0]?.id
    form.setFieldsValue({
      to: candidateEmail,
      senderAccountId: defaultFromPreference || defaultFromAccount || firstAvailable,
      subject: '',
      body: '',
      templateId: undefined,
      quickReplyId: undefined,
      allowFallback: preferences?.allow_system_fallback !== false,
    })
  }, [open, form, candidateEmail, preferences?.default_sender_account, preferences?.allow_system_fallback, connectedAccounts])

  const renderTemplateMutation = useMutation({
    mutationFn: (payload: Parameters<typeof communicationsApi.renderTemplate>[0]) =>
      communicationsApi.renderTemplate(payload),
  })

  const sendMutation = useMutation({
    mutationFn: (payload: any) => communicationsApi.sendEmail(payload),
    onSuccess: () => {
      message.success('Email sent')
      queryClient.invalidateQueries({ queryKey: ['email_messages_candidate_composer', candidateId] })
      onSent()
      onClose()
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Failed to send email')
    },
  })

  const applyTemplate = async (templateId?: string) => {
    if (!templateId) return
    const currentSubject = form.getFieldValue('subject') || ''
    const currentBody = form.getFieldValue('body') || ''
    if (currentSubject || currentBody) {
      const confirmed = await new Promise<boolean>((resolve) => {
        Modal.confirm({
          title: 'Replace content?',
          content: 'Applying this template will overwrite the current subject and body.',
          okText: 'Replace',
          cancelText: 'Keep editing',
          onOk: () => resolve(true),
          onCancel: () => resolve(false),
        })
      })
      if (!confirmed) return
    }
    try {
      const res = await renderTemplateMutation.mutateAsync({
        template_id: templateId,
        candidate_id: candidateId,
        job_id: activeJobId,
      })
      const d = (res.data.data as any) || {}
      form.setFieldsValue({
        subject: d.rendered_subject || '',
        body: d.rendered_body_text || '',
      })
      setUnresolvedTags(d.unresolved_tags || [])
    } catch {
      message.warning('Unable to load template')
    }
  }

  const applyQuickReply = (quickReplyId?: string) => {
    if (!quickReplyId) return
    const selected = quickReplies.find((q) => q.id === quickReplyId)
    if (!selected) return
    const currentSubject = form.getFieldValue('subject') || ''
    const currentBody = form.getFieldValue('body') || ''
    form.setFieldValue('subject', selected.subject_template || currentSubject)
    form.setFieldValue('body', selected.body_text || currentBody)
  }

  const handleSend = async () => {
    const values = await form.validateFields()
    await sendMutation.mutateAsync({
      email_type: 'business',
      message_purpose: 'candidate_outreach',
      recipients: [candidateEmail],
      related_object_type: 'candidate',
      related_object_id: candidateId,
      subject: values.subject,
      body_text: values.body,
      preferred_sender_account_id: values.senderAccountId || undefined,
      template_id: values.templateId || undefined,
      quick_reply_template_id: values.quickReplyId || undefined,
      allow_fallback: values.allowFallback !== false,
      track_delivery: true,
    })
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      onOk={handleSend}
      okText="Send Email"
      confirmLoading={sendMutation.isPending}
      title={`Email ${candidateName}`}
      width={760}
      destroyOnClose
    >
      <div className="space-y-3 pt-2">
        {noConnectedEmail && (
          <Alert
            type="warning"
            showIcon
            message="No email connected. System fallback will be used"
          />
        )}
        {unresolvedTags.length > 0 && (
          <Alert
            type="info"
            showIcon
            message={`Some template tags couldn't be resolved: ${unresolvedTags.map(t => `{{${t}}}`).join(', ')}. Review before sending.`}
          />
        )}
        <Form form={form} layout="vertical">
          <div className="grid grid-cols-2 gap-3">
            <Form.Item label="To" name="to">
              <Input value={candidateEmail} disabled />
            </Form.Item>
            <Form.Item label="From account" name="senderAccountId">
              <Select
                loading={accountsLoading}
                allowClear
                placeholder={noConnectedEmail ? 'No connected sender' : 'Select sender'}
                options={connectedAccounts.map((a) => ({
                  value: a.id,
                  label: `${a.from_name || a.display_name || a.email_address} <${a.email_address}>`,
                }))}
              />
            </Form.Item>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Form.Item label="Template" name="templateId">
              <Select
                loading={templatesLoading || renderTemplateMutation.isPending}
                allowClear
                showSearch
                placeholder="Select template"
                onChange={(value) => applyTemplate(value)}
                options={templates.map((t) => ({ value: t.id, label: t.name }))}
              />
            </Form.Item>
            <Form.Item label="Quick Reply" name="quickReplyId">
              <Select
                loading={quickRepliesLoading}
                allowClear
                showSearch
                placeholder="Select quick reply"
                onChange={(value) => applyQuickReply(value)}
                options={quickReplies.map((q) => ({ value: q.id, label: q.name }))}
              />
            </Form.Item>
          </div>
          <Form.Item label="Subject" name="subject" rules={[{ required: true, message: 'Subject is required' }]}>
            <Input placeholder="Enter subject" />
          </Form.Item>
          <Form.Item label="Body" name="body" rules={[{ required: true, message: 'Body is required' }]}>
            <Input.TextArea rows={10} placeholder="Write your email..." />
          </Form.Item>
          <Form.Item name="allowFallback" valuePropName="checked">
            <Switch checkedChildren="Fallback On" unCheckedChildren="Fallback Off" />
          </Form.Item>
        </Form>
      </div>
    </Modal>
  )
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function SectionCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <span className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">{title}</span>
      </div>
      {children}
    </div>
  )
}

function InfoCell({ label, value, href }: { label: string; value?: string | null; href?: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
      {value ? (
        href ? (
          <a href={href} target="_blank" rel="noopener noreferrer"
            className="mt-0.5 block truncate text-[11px] font-semibold text-indigo-600 hover:text-indigo-700">
            {value}
          </a>
        ) : (
          <p className="mt-0.5 truncate text-[11px] font-semibold text-slate-700">{value}</p>
        )
      ) : (
        <p className="mt-0.5 text-[11px] text-slate-300">—</p>
      )}
    </div>
  )
}

// ── Submit to Job Modal ───────────────────────────────────────────────────────

type JobSummary = { id: string; title: string; status: string; department?: string; location?: string; job_type?: string }

function SubmitToJobModal({
  open,
  candidateId,
  candidateName,
  candidate,
  existingEngagements,
  onClose,
  onSuccess,
}: {
  open: boolean
  candidateId: string
  candidateName: string
  candidate: CCData['candidate']
  existingEngagements: ActiveWorkEngagement[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [jobSearch, setJobSearch] = useState('')
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [submittedJobTitle, setSubmittedJobTitle] = useState('')

  // Load active + approved jobs
  const jobsQ = useQuery({
    queryKey: ['requisitions-for-submit'],
    queryFn: async () => {
      const [activeRes, approvedRes] = await Promise.all([
        requisitionsApi.list({ status: 'active' }),
        requisitionsApi.list({ status: 'approved' }),
      ])
      const active = (activeRes.data?.data as any)?.requisitions ?? []
      const approved = (approvedRes.data?.data as any)?.requisitions ?? []
      // Deduplicate
      const seen = new Set<string>()
      return [...active, ...approved].filter((j: any) => { if (seen.has(j.id)) return false; seen.add(j.id); return true }) as JobSummary[]
    },
    enabled: open,
  })

  // Already submitted job IDs (from existing engagements at 'submitted' stage or above)
  const alreadySubmittedJobIds = new Set(
    existingEngagements
      .filter((e) => e.job && ['submitted', 'review', 'client_review', 'interviewing', 'offered', 'joined'].includes(e.stage))
      .map((e) => e.job as string),
  )

  const filteredJobs = (jobsQ.data || []).filter((j) => {
    if (!jobSearch.trim()) return true
    const q = jobSearch.toLowerCase()
    return j.title?.toLowerCase().includes(q) || j.department?.toLowerCase().includes(q)
  })

  const selectedJob = (jobsQ.data || []).find((j) => j.id === selectedJobId)

  const reset = () => {
    setSelectedJobId(null)
    setNote('')
    setSubmitted(false)
    setSubmittedJobTitle('')
    setJobSearch('')
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleSubmit = async () => {
    if (!selectedJobId || !selectedJob) return
    setSubmitting(true)
    try {
      // 1. Create formal application record in pipeline
      await pipelineApi.createApplication({
        candidate_id: candidateId,
        requisition_id: selectedJobId,
        source: 'recruiter',
        source_detail: 'manual_submit',
      })

      // 2. Create / update engagement to track in command center engagements tab
      try {
        await http.post(`/candidates/${candidateId}/engagements/`, {
          stage: 'submitted',
          job: selectedJobId,
          job_title: selectedJob.title,
          priority: 'warm',
        })
      } catch {
        // Engagement may already exist — not fatal
      }

      // 3. Attach note if provided
      if (note.trim()) {
        try {
          await candidatesApi.addNote(candidateId, {
            note_text: `Submitted to job: ${selectedJob.title}. ${note}`,
            note_type: 'submission',
          })
        } catch {
          // Note failure is non-fatal
        }
      }

      setSubmittedJobTitle(selectedJob.title)
      setSubmitted(true)
    } catch (err: any) {
      message.error(err?.response?.data?.message || err?.response?.data?.error || 'Submission failed — please try again')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      footer={null}
      width={640}
      title={null}
      destroyOnClose
      bodyStyle={{ padding: 0 }}
    >
      {submitted ? (
        // ── Success state ──────────────────────────────────────────────────
        <div className="flex flex-col items-center justify-center gap-4 py-14 px-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100">
            <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p className="text-base font-black text-slate-900">Submitted Successfully</p>
            <p className="mt-1 text-sm text-slate-500">
              <span className="font-semibold text-slate-700">{candidateName}</span> has been submitted to{' '}
              <span className="font-semibold text-indigo-700">{submittedJobTitle}</span>.
            </p>
            <p className="mt-1 text-xs text-slate-400">This submission now appears in the Engagements tab and pipeline.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => { reset(); onSuccess() }}
              className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-bold text-white hover:bg-indigo-700"
            >
              Done
            </button>
            <button
              onClick={reset}
              className="rounded-xl border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            >
              Submit to Another Job
            </button>
          </div>
        </div>
      ) : (
        // ── Submit flow ────────────────────────────────────────────────────
        <div className="flex flex-col">
          {/* Header */}
          <div className="border-b border-slate-200 bg-white px-6 py-4">
            <p className="text-base font-black text-slate-900">Submit to Job</p>
            <p className="mt-0.5 text-xs text-slate-500">
              Submitting <span className="font-semibold text-slate-700">{candidateName}</span> — select an active job below
            </p>
          </div>

          <div className="flex" style={{ minHeight: 420 }}>
            {/* Left: job list */}
            <div className="flex w-72 flex-none flex-col border-r border-slate-200 bg-slate-50">
              <div className="border-b border-slate-200 p-3">
                <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100">
                  <Search size={12} className="text-slate-400 shrink-0" />
                  <input
                    value={jobSearch}
                    onChange={(e) => setJobSearch(e.target.value)}
                    placeholder="Search jobs..."
                    className="flex-1 bg-transparent text-xs outline-none placeholder-slate-400"
                    autoFocus
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {jobsQ.isLoading ? (
                  <div className="flex items-center justify-center py-10">
                    <Spin size="small" />
                  </div>
                ) : filteredJobs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
                    <Briefcase size={22} className="text-slate-300" />
                    <p className="text-xs text-slate-400">No active jobs found</p>
                  </div>
                ) : (
                  filteredJobs.map((job) => {
                    const isAlreadySubmitted = alreadySubmittedJobIds.has(job.id)
                    const isSelected = selectedJobId === job.id
                    return (
                      <button
                        key={job.id}
                        onClick={() => !isAlreadySubmitted && setSelectedJobId(job.id)}
                        disabled={isAlreadySubmitted}
                        className={`w-full rounded-xl border p-3 text-left transition-all mb-1 ${
                          isSelected
                            ? 'border-indigo-400 bg-white ring-2 ring-indigo-100 shadow-sm'
                            : isAlreadySubmitted
                            ? 'border-slate-100 bg-slate-100 opacity-50 cursor-not-allowed'
                            : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="truncate text-xs font-bold text-slate-800">{job.title}</p>
                            {job.department && (
                              <p className="truncate text-[10px] text-slate-400 mt-0.5">{job.department}</p>
                            )}
                          </div>
                          {isAlreadySubmitted ? (
                            <span className="shrink-0 rounded-full bg-purple-50 px-2 py-0.5 text-[9px] font-bold text-purple-600">Submitted</span>
                          ) : (
                            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                              job.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600'
                            }`}>
                              {job.status}
                            </span>
                          )}
                        </div>
                        {job.job_type && (
                          <p className="mt-1 text-[10px] text-slate-400 uppercase tracking-wide">{job.job_type.replace(/_/g, ' ')}</p>
                        )}
                      </button>
                    )
                  })
                )}
              </div>
            </div>

            {/* Right: confirmation + note */}
            <div className="flex flex-1 flex-col bg-white">
              {candidate.is_agency_protected && (
                <div className="border-b border-violet-100 bg-violet-50 px-5 py-3">
                  <div className="flex items-start gap-2">
                    <ShieldCheck size={15} className="mt-0.5 shrink-0 text-violet-600" />
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-violet-700">Agency Protected</p>
                      <p className="mt-1 text-xs font-semibold text-slate-700">
                        Protected Until: {formatProtectionDate(candidate.protected_until)} · Scope: {protectionScopeLabel(candidate.protection_scope)}
                      </p>
                      <p className="text-xs text-slate-600">
                        Candidate cannot be reused outside agreed scope during protection period. Unsupported job submissions will be blocked.
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {selectedJob ? (
                <>
                  {/* Selected job details */}
                  <div className="border-b border-slate-100 p-5">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-black text-indigo-600">
                        {selectedJob.title.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-black text-slate-900">{selectedJob.title}</p>
                        {selectedJob.department && <p className="text-xs text-slate-500 mt-0.5">{selectedJob.department}</p>}
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                            selectedJob.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600'
                          }`}>
                            {selectedJob.status}
                          </span>
                          {selectedJob.job_type && (
                            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-medium text-slate-500 uppercase">
                              {selectedJob.job_type.replace(/_/g, ' ')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Submission note */}
                  <div className="flex-1 p-5">
                    <label className="block text-xs font-bold text-slate-600 mb-1.5">
                      Submission Note <span className="font-normal text-slate-400">(optional)</span>
                    </label>
                    <textarea
                      rows={4}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      placeholder={`e.g. Strong match for ${selectedJob.title} — candidate is actively interviewing, move quickly.`}
                      className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-700 outline-none placeholder-slate-400 focus:border-indigo-300 focus:bg-white focus:ring-2 focus:ring-indigo-100"
                    />
                    <p className="mt-2 text-[10px] text-slate-400">
                      Note will be saved to candidate history as a submission record.
                    </p>
                  </div>

                  {/* Footer actions */}
                  <div className="border-t border-slate-100 px-5 py-4 flex items-center justify-between">
                    <button onClick={handleClose}
                      className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50">
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={submitting}
                      className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-60"
                    >
                      {submitting ? (
                        <>
                          <Spin size="small" />
                          <span>Submitting...</span>
                        </>
                      ) : (
                        <>
                          <Send size={13} />
                          <span>Submit {candidateName.split(' ')[0]}</span>
                        </>
                      )}
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50">
                    <Briefcase size={24} className="text-indigo-300" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-600">Select a job</p>
                    <p className="mt-1 text-xs text-slate-400">Choose an active job from the list to submit this candidate</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}

function PoolsTab({ candidateId }: { candidateId: string }) {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['candidate-pools', candidateId],
    queryFn: () => talentPoolsApi.getCandidatePools(candidateId)
  })

  const pools = data?.data?.data?.talent_pools || []

  const handleRemove = async (poolId: string) => {
    try {
      await talentPoolsApi.bulkRemove(poolId, { candidate_ids: [candidateId] })
      message.success('Removed from pool')
      queryClient.invalidateQueries({ queryKey: ['candidate-pools', candidateId] })
    } catch (err) {
      message.error('Failed to remove from pool')
    }
  }

  if (isLoading) return <div className="p-4">Loading pools...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-700">Talent Pool Memberships</h3>
      </div>
      
      {pools.length > 0 ? (
        <div className="grid gap-3">
          {pools.map((pool: TalentPool) => (
            <div key={pool.id} className="flex items-center justify-between p-3 bg-white rounded-xl border border-slate-100 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-2 h-8 rounded-full" style={{ backgroundColor: pool.color || '#e2e8f0' }} />
                <div>
                  <div className="text-sm font-bold text-slate-900">{pool.name}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">{pool.pool_type}</div>
                </div>
              </div>
              <Button type="text" danger size="small" icon={<Trash2 size={14} />} onClick={() => handleRemove(pool.id)} />
            </div>
          ))}
        </div>
      ) : (
        <Empty description="No pool memberships yet." className="py-10 bg-white rounded-2xl border border-dashed border-slate-200" />
      )}
    </div>
  )
}

function AddToPoolModal() {
  const [open, setOpen] = useState(false)
  const [candidateId, setCandidateId] = useState<string | null>(null)
  const [selectedPools, setSelectedPools] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()

  const { data: poolsData } = useQuery({
    queryKey: ['talent-pools-all'],
    queryFn: () => talentPoolsApi.list()
  })

  const { data: currentPoolsData, isLoading: loadingCurrentPools } = useQuery({
    queryKey: ['candidate-pools', candidateId],
    queryFn: () => talentPoolsApi.getCandidatePools(candidateId!),
    enabled: !!candidateId,
  })

  const pools = poolsData?.data?.data?.talent_pools || []
  const currentPools = currentPoolsData?.data?.data?.talent_pools || []
  const currentPoolIds = new Set(currentPools.map((pool: TalentPool) => pool.id))
  const availablePools = pools.filter((pool: TalentPool) => !currentPoolIds.has(pool.id))

  React.useEffect(() => {
    (window as any).openAddToPoolModal = (id: string) => {
      setCandidateId(id)
      setSelectedPools([])
      setOpen(true)
    }
  }, [])

  const handleAdd = async () => {
    if (!candidateId || selectedPools.length === 0) return
    try {
      setLoading(true)
      for (const poolId of selectedPools) {
        await talentPoolsApi.bulkAdd(poolId, { candidate_ids: [candidateId] })
      }
      message.success('Added to pools')
      setOpen(false)
      setSelectedPools([])
      queryClient.invalidateQueries({ queryKey: ['candidate-pools', candidateId] })
      queryClient.invalidateQueries({ queryKey: ['talent-pools-all'] })
      queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
    } catch (err) {
      message.error('Failed to add to pools')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold">Add Candidate to Talent Pools</span>}
      open={open}
      onCancel={() => setOpen(false)}
      onOk={handleAdd}
      confirmLoading={loading}
      okText="Add to Pools"
      okButtonProps={{ disabled: selectedPools.length === 0, className: 'bg-indigo-600' }}
    >
      <div className="py-4 space-y-5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-slate-500">Select one or more available pools for this candidate.</p>
          <span className="text-xs font-bold text-slate-700">{selectedPools.length} selected</span>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Already In</p>
          {loadingCurrentPools ? (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-400">Loading current memberships...</div>
          ) : currentPools.length > 0 ? (
            <div className="space-y-2">
              {currentPools.map((pool: TalentPool) => (
                <div key={pool.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 opacity-80">
                  <div className="flex items-center gap-3">
                    <div className="h-3 w-3 rounded-full" style={{ backgroundColor: pool.color || '#cbd5e1' }} />
                    <div>
                      <div className="text-sm font-semibold text-slate-800">{pool.name}</div>
                      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Already added</div>
                    </div>
                  </div>
                  <Tag>Already in pool</Tag>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white px-3 py-4 text-sm text-slate-400">No current pool memberships.</div>
          )}
        </div>

        <div>
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Available Pools</p>
          {availablePools.length > 0 ? (
            <div className="space-y-2">
              {availablePools.map((pool: TalentPool) => {
                const selected = selectedPools.includes(pool.id)
                return (
                  <button
                    key={pool.id}
                    type="button"
                    onClick={() =>
                      setSelectedPools((current) =>
                        current.includes(pool.id)
                          ? current.filter((id) => id !== pool.id)
                          : [...current, pool.id]
                      )
                    }
                    className={`flex w-full items-center justify-between rounded-xl border px-3 py-3 text-left transition ${
                      selected
                        ? 'border-indigo-300 bg-indigo-50 ring-2 ring-indigo-100'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: pool.color || '#cbd5e1' }} />
                      <div>
                        <div className="text-sm font-semibold text-slate-800">{pool.name}</div>
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{pool.pool_type}</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={selected}
                      readOnly
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600"
                    />
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white px-3 py-4 text-sm text-slate-400">No available pools in this tenant.</div>
          )}
        </div>
      </div>
    </Modal>
  )
}
