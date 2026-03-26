import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar, Button, Checkbox, Dropdown, Empty, Input,
  Divider, Modal, Select, Spin, Table, Tabs, Tooltip, message,
} from 'antd'
import type { ColumnsType, TableRowSelection } from 'antd/es/table/interface'
import {
  Activity, AlertTriangle, BadgeCheck, Bot, Briefcase,
  ChevronDown, Clock3, Copy, Database, Download, ExternalLink,
  Filter, MapPin, MoreHorizontal, Plus, RefreshCw, Search,
  Settings2, Sparkles, Target, Trash2, User, FileText,
  Users, XCircle, Zap, BookOpen, Maximize2, Minimize2, ShieldCheck,
  History, Notebook, Mail, Phone, Linkedin,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { talentPoolsApi } from '@/api/talentPools'
import { requisitionsApi } from '@/api/jobs'
import http from '@/utils/http'
import type { CandidateSmartRow, CandidateCommandCenter as CCData } from '@/types'
import { usePermission } from '@/hooks/usePermission'
import AddCandidateWorkflowModal from '@/components/candidates/AddCandidateWorkflowModal'

dayjs.extend(relativeTime)

// ── Constants ─────────────────────────────────────────────────────────────────

const SEARCH_MODES = [
  { key: 'all', label: 'All Candidates' },
  { key: 'search', label: 'Talent Search' },
  { key: 'match_job', label: 'Job Matching' },
  { key: 'duplicates', label: 'Data Health' },
  { key: 'needs_review', label: 'Needs Review' },
] as const

type SearchMode = typeof SEARCH_MODES[number]['key']
type CandidateViewMode = 'list' | 'compact' | 'card'
type ProtectionStatusFilter = 'all' | 'protected' | 'not_protected'

const CANDIDATE_DB_VIEW_MODE_KEY = 'candidate-database-view-mode'

const STATIC_SAVED_SEARCHES = [
  { key: 'react_bangalore', label: 'React 5+ yrs · Bangalore' },
  { key: 'immediate_joiners', label: 'Immediate joiners' },
  { key: 'python_remote', label: 'Python · Remote' },
  { key: 'prev_interviewees', label: 'Previous interviewees' },
]

const SOURCE_OPTIONS = [
  { value: 'company', label: 'Direct' },
  { value: 'agency', label: 'Agency' },
  { value: 'referral', label: 'Referral' },
  { value: 'job_board', label: 'Job Board' },
  { value: 'passport', label: 'Passport' },
  { value: 'linkedin', label: 'LinkedIn' },
]

const AVAILABILITY_OPTIONS = [
  { value: 'immediately', label: 'Immediately' },
  { value: 'notice_period', label: 'Serving Notice' },
  { value: '1_month', label: '1 Month' },
  { value: '3_months', label: '3 Months' },
]

const DEFAULT_VISIBLE_COLS = [
  'candidate', 'skills', 'availability', 'fit', 'readiness', 
  'engagements', 'source', 'owner', 'last_activity', 'actions',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

function scoreColor(score: number | null | undefined): { bg: string; color: string; border: string } {
  if (score == null) return { bg: '#f1f5f9', color: '#94a3b8', border: '#e2e8f0' }
  if (score >= 80) return { bg: '#f0fdf4', color: '#15803d', border: '#dcfce7' }
  if (score >= 50) return { bg: '#fefce8', color: '#b45309', border: '#fef9c3' }
  return { bg: '#fef2f2', color: '#dc2626', border: '#fee2e2' }
}

function scoreBadge(score: number | null | undefined) {
  if (score == null) return <span className="text-slate-300">—</span>
  const { bg, color, border } = scoreColor(score)
  return (
    <span 
      className="inline-flex items-center justify-center min-w-[32px] rounded-full px-2 py-0.5 text-[11px] font-bold border"
      style={{ backgroundColor: bg, color, borderColor: border }}
    >
      {score}
    </span>
  )
}

function availabilityBadge(status: string | null | undefined, days?: number | null) {
  const label = status || noticePeriodLabel(days)
  if (!label) return <span className="text-slate-300">—</span>
  
  let colorClass = 'bg-slate-50 text-slate-600 border-slate-200'
  const lowLabel = label.toLowerCase()
  
  if (lowLabel.includes('immediate')) colorClass = 'bg-emerald-50 text-emerald-700 border-emerald-200'
  else if (lowLabel.includes('15 days')) colorClass = 'bg-blue-50 text-blue-700 border-blue-200'
  else if (lowLabel.includes('1 month') || lowLabel.includes('30 days')) colorClass = 'bg-indigo-50 text-indigo-700 border-indigo-200'
  else if (lowLabel.includes('passive')) colorClass = 'bg-slate-50 text-slate-500 border-slate-200'
  
  return (
    <span className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-bold border uppercase tracking-tight ${colorClass}`}>
      {label}
    </span>
  )
}

function noticePeriodLabel(days?: number | null) {
  if (!days) return 'Immediate'
  if (days <= 15) return '≤ 15 days'
  if (days <= 30) return '1 month'
  if (days <= 60) return '2 months'
  return `${days}d`
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

function protectionMessage(candidate: Pick<CandidateSmartRow, 'protected_until'>) {
  return `Candidate is protected under agency agreement until ${formatProtectionDate(candidate.protected_until)}`
}

function extractApiErrorMessage(error: any, fallback: string) {
  const payload = error?.response?.data
  return payload?.message || payload?.error || fallback
}

function ProtectionBadge({
  candidate,
  compact = false,
}: {
  candidate: Pick<CandidateSmartRow, 'is_agency_protected' | 'protected_until'>
  compact?: boolean
}) {
  if (!candidate.is_agency_protected) return null
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-violet-700">
      <ShieldCheck size={compact ? 11 : 12} />
      <span>Agency Protected</span>
      {candidate.protected_until && (
        <span className="normal-case tracking-normal text-violet-500">
          Until {formatProtectionDate(candidate.protected_until, compact ? 'DD MMM' : 'DD MMM YYYY')}
        </span>
      )}
    </span>
  )
}

function ProtectionStatusPanel({
  candidate,
  compact = false,
}: {
  candidate: Pick<CandidateSmartRow, 'is_agency_protected' | 'protected_until' | 'protection_scope'>
  compact?: boolean
}) {
  if (!candidate.is_agency_protected) return null
  return (
    <div className={`rounded-xl border border-violet-200 bg-violet-50/80 ${compact ? 'p-3' : 'p-4'}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-violet-600">Protection Status</p>
          <p className="mt-1 text-sm font-bold text-violet-900">Agency Protected</p>
        </div>
        <ProtectionBadge candidate={candidate} compact />
      </div>
      <div className={`mt-3 grid gap-2 ${compact ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3'}`}>
        <div className="rounded-lg bg-white/80 px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wider text-violet-500">Status</p>
          <p className="mt-1 text-xs font-semibold text-slate-700">Agency Protected</p>
        </div>
        <div className="rounded-lg bg-white/80 px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wider text-violet-500">Protected Until</p>
          <p className="mt-1 text-xs font-semibold text-slate-700">{formatProtectionDate(candidate.protected_until)}</p>
        </div>
        <div className="rounded-lg bg-white/80 px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wider text-violet-500">Scope</p>
          <p className="mt-1 text-xs font-semibold text-slate-700">{protectionScopeLabel(candidate.protection_scope)}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-600">
        Candidate cannot be reused outside the agreed scope during the protection period.
      </p>
    </div>
  )
}

function mapCandidateListItemToSmartRow(candidate: any): CandidateSmartRow {
  const firstName = candidate?.first_name || ''
  const lastName = candidate?.last_name || ''
  const fullName =
    candidate?.name ||
    `${firstName} ${lastName}`.trim() ||
    candidate?.full_name ||
    'Unnamed Candidate'
  const incomingSignals = candidate?.signals || {}
  return {
    id: String(candidate?.id || ''),
    name: fullName,
    current_title: candidate?.current_title || candidate?.headline || '',
    company: candidate?.company || candidate?.current_company || '',
    experience:
      candidate?.experience != null
        ? Number(candidate.experience)
        : candidate?.experience_years != null
          ? Number(candidate.experience_years)
          : null,
    location:
      candidate?.location ||
      [candidate?.current_location_city, candidate?.current_location_country].filter(Boolean).join(', '),
    source: candidate?.source || candidate?.source_type || '',
    source_type: candidate?.source_type || '',
    owner: candidate?.owner || candidate?.owner_user_id || candidate?.assigned_to || null,
    owner_name: candidate?.owner_name || null,
    last_touch: candidate?.last_touch || candidate?.last_contact_at || null,
    last_activity: candidate?.last_activity || candidate?.last_activity_at || candidate?.updated_at || null,
    signals: {
      readiness_score: incomingSignals?.readiness_score ?? candidate?.readiness_score ?? null,
      fit_score: incomingSignals?.fit_score ?? candidate?.fit_score ?? null,
      completeness_score:
        incomingSignals?.completeness_score ??
        candidate?.completeness_score ??
        candidate?.profile_completeness ??
        null,
      warning_signals: incomingSignals?.warning_signals || candidate?.warning_signals || [],
    },
    job_engagement_summary: candidate?.job_engagement_summary || {},
    skills: candidate?.skills || [],
    pools: candidate?.pools || [],
    resume_url: candidate?.resume_url || candidate?.cv_url || null,
    passport_linked: Boolean(candidate?.passport_linked || candidate?.passport_id),
    is_duplicate: Boolean(candidate?.is_duplicate || candidate?.duplicate_of),
    notice_period_days: candidate?.notice_period_days ?? null,
    availability_status: candidate?.availability_status ?? null,
    open_engagements: candidate?.open_engagements ?? 0,
    is_agency_protected: Boolean(candidate?.is_agency_protected),
    protected_until: candidate?.protected_until ?? null,
    protection_scope: candidate?.protection_scope ?? null,
  }
}

function mapActiveWorkItemToSmartRow(item: any): CandidateSmartRow {
  return {
    id: String(item?.candidate || item?.candidate_id || ''),
    name: item?.candidate_name || 'Unnamed Candidate',
    current_title: item?.current_title || '',
    company: item?.current_company || '',
    experience: item?.experience_years != null ? Number(item.experience_years) : null,
    location: [item?.city, item?.country].filter(Boolean).join(', '),
    source: item?.source || '',
    source_type: item?.source_type || '',
    owner: item?.owner_user_id || null,
    owner_name: item?.owner_name || null,
    last_touch: item?.last_contact_at || null,
    last_activity: item?.last_activity_at || item?.updated_at || null,
    signals: {
      readiness_score: item?.readiness_score ?? null,
      fit_score: item?.fit_score ?? null,
      completeness_score: item?.completeness_score ?? null,
      warning_signals: item?.warning_signals || [],
    },
    job_engagement_summary: item?.stage ? { [item.stage]: 1 } : {},
    skills: item?.skills || [],
    pools: item?.pools || [],
    resume_url: item?.resume_url || null,
    passport_linked: Boolean(item?.passport_linked),
    is_duplicate: Boolean(item?.is_duplicate),
    notice_period_days: item?.notice_period_days ?? null,
    availability_status: item?.availability_status ?? null,
    open_engagements: item?.open_engagements ?? 1,
    is_agency_protected: Boolean(item?.is_agency_protected),
    protected_until: item?.protected_until ?? null,
    protection_scope: item?.protection_scope ?? null,
  }
}

// ── ScoreChip ─────────────────────────────────────────────────────────────────

function ScoreChip({
  score, label, explanation,
}: { score?: number | null; label: string; explanation?: string }) {
  const { bg, color } = scoreColor(score)
  const chip = (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold cursor-default"
      style={{ backgroundColor: bg, color }}
    >
      {score != null ? score : '—'}
    </span>
  )
  if (!explanation && score == null) return chip
  return (
    <Tooltip
      title={
        <div className="space-y-1">
          <div className="font-semibold">{label}: {score ?? 'N/A'}</div>
          {explanation && <div className="text-xs opacity-80">{explanation}</div>}
        </div>
      }
    >
      {chip}
    </Tooltip>
  )
}

// ── FilterSection ─────────────────────────────────────────────────────────────

function FilterSection({
  title, children, defaultOpen = true,
}: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border-b border-slate-100 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 hover:bg-slate-50 transition"
      >
        <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">{title}</span>
        <ChevronDown
          size={13}
          className={`text-slate-400 transition-transform ${open ? '' : '-rotate-90'}`}
        />
      </button>
      {open && <div className="px-4 pb-3 space-y-2">{children}</div>}
    </div>
  )
}

// ── FilterRail ────────────────────────────────────────────────────────────────

interface FilterState {
  skills: string
  experience_min: string
  experience_max: string
  location: string
  source_type: string
  owner: string
  last_activity_days: string
  passport_linked: boolean | null
  has_duplicates: boolean | null
  readiness_min: string
  fit_min: string
  availability: string
  notice_max_days: string
  protection_status: ProtectionStatusFilter
}

const EMPTY_FILTERS: FilterState = {
  skills: '',
  experience_min: '',
  experience_max: '',
  location: '',
  source_type: '',
  owner: '',
  last_activity_days: '',
  passport_linked: null,
  has_duplicates: null,
  readiness_min: '',
  fit_min: '',
  availability: '',
  notice_max_days: '',
  protection_status: 'all',
}

function FilterRail({
  filters, onChange, onClear, memberOptions,
}: {
  filters: FilterState
  onChange: (f: Partial<FilterState>) => void
  onClear: () => void
  memberOptions: { value: string; label: string }[]
}) {
  const activeCount = Object.entries(filters).filter(([, v]) => {
    if (typeof v === 'boolean') return v !== null
    if (v === 'all') return false
    return v !== '' && v !== null
  }).length

  return (
    <div className="flex flex-col h-full overflow-hidden bg-white border-r border-slate-200 shadow-sm">
      {/* Rail header */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-slate-500" />
          <span className="text-xs font-bold text-slate-800 uppercase tracking-tight">Advanced Filters</span>
          {activeCount > 0 && (
            <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white shadow-sm">
              {activeCount}
            </span>
          )}
        </div>
        {activeCount > 0 && (
          <button onClick={onClear} className="text-[11px] text-indigo-600 hover:text-indigo-800 font-bold uppercase tracking-tight">
            Reset
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <FilterSection title="Skills & Tags">
          <Input
            size="small"
            placeholder="e.g. Python, React..."
            value={filters.skills}
            onChange={e => onChange({ skills: e.target.value })}
            allowClear
            className="rounded-md border-slate-200 focus:border-indigo-300"
          />
        </FilterSection>

        <FilterSection title="Experience Range">
          <div className="flex items-center gap-2">
            <Input
              size="small"
              type="number"
              min={0}
              placeholder="Min"
              value={filters.experience_min}
              onChange={e => onChange({ experience_min: e.target.value })}
              className="rounded-md border-slate-200"
            />
            <span className="text-slate-400 text-xs">—</span>
            <Input
              size="small"
              type="number"
              min={0}
              placeholder="Max"
              value={filters.experience_max}
              onChange={e => onChange({ experience_max: e.target.value })}
              className="rounded-md border-slate-200"
            />
          </div>
        </FilterSection>

        <FilterSection title="Target Location">
          <Input
            size="small"
            placeholder="City or country..."
            value={filters.location}
            onChange={e => onChange({ location: e.target.value })}
            allowClear
            prefix={<MapPin size={12} className="text-slate-400" />}
            className="rounded-md border-slate-200"
          />
        </FilterSection>

        <FilterSection title="Notice Period">
          <Select
            size="small"
            style={{ width: '100%' }}
            placeholder="Max notice period"
            allowClear
            value={filters.notice_max_days || undefined}
            onChange={v => onChange({ notice_max_days: v || '' })}
            options={[
              { value: '0', label: 'Immediate' },
              { value: '15', label: '≤ 15 days' },
              { value: '30', label: '≤ 1 month' },
              { value: '60', label: '≤ 2 months' },
              { value: '90', label: '≤ 3 months' },
            ]}
          />
        </FilterSection>

        <FilterSection title="Source">
          <Select
            size="small"
            style={{ width: '100%' }}
            placeholder="Any source"
            allowClear
            value={filters.source_type || undefined}
            onChange={v => onChange({ source_type: v || '' })}
            options={SOURCE_OPTIONS}
          />
        </FilterSection>

        <FilterSection title="Owner">
          <Select
            size="small"
            style={{ width: '100%' }}
            placeholder="Any owner"
            allowClear
            value={filters.owner || undefined}
            onChange={v => onChange({ owner: v || '' })}
            options={[
              { value: 'me', label: 'Assigned to me' },
              { value: 'unassigned', label: 'Unassigned' },
              ...memberOptions,
            ]}
          />
        </FilterSection>

        <FilterSection title="Last Activity">
          <Select
            size="small"
            style={{ width: '100%' }}
            placeholder="Any time"
            allowClear
            value={filters.last_activity_days || undefined}
            onChange={v => onChange({ last_activity_days: v || '' })}
            options={[
              { value: '7', label: 'Last 7 days' },
              { value: '30', label: 'Last 30 days' },
              { value: '90', label: 'Last 90 days' },
              { value: '180', label: 'Last 6 months' },
            ]}
          />
        </FilterSection>

        <FilterSection title="AI Scores" defaultOpen={false}>
          <div className="space-y-2">
            <div>
              <p className="text-[10px] text-slate-500 mb-1">Readiness ≥</p>
              <Input
                size="small"
                type="number"
                min={0}
                max={100}
                placeholder="e.g. 60"
                value={filters.readiness_min}
                onChange={e => onChange({ readiness_min: e.target.value })}
              />
            </div>
            <div>
              <p className="text-[10px] text-slate-500 mb-1">Fit Score ≥</p>
              <Input
                size="small"
                type="number"
                min={0}
                max={100}
                placeholder="e.g. 70"
                value={filters.fit_min}
                onChange={e => onChange({ fit_min: e.target.value })}
              />
            </div>
          </div>
        </FilterSection>

        <FilterSection title="Profile Flags" defaultOpen={false}>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={filters.passport_linked === true}
                onChange={e => onChange({ passport_linked: e.target.checked ? true : null })}
              />
              <span className="text-xs text-slate-700">Passport linked</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={filters.has_duplicates === true}
                onChange={e => onChange({ has_duplicates: e.target.checked ? true : null })}
              />
              <span className="text-xs text-slate-700">Has duplicate risk</span>
            </label>
          </div>
        </FilterSection>

        <FilterSection title="Availability" defaultOpen={false}>
          <Select
            size="small"
            style={{ width: '100%' }}
            placeholder="Any availability"
            allowClear
            value={filters.availability || undefined}
            onChange={v => onChange({ availability: v || '' })}
            options={AVAILABILITY_OPTIONS}
          />
        </FilterSection>

        <FilterSection title="Protection" defaultOpen={false}>
          <Select
            size="small"
            style={{ width: '100%' }}
            value={filters.protection_status}
            onChange={(value) => onChange({ protection_status: value })}
            options={[
              { value: 'all', label: 'All' },
              { value: 'protected', label: 'Agency Protected' },
              { value: 'not_protected', label: 'Not Protected' },
            ]}
          />
        </FilterSection>
      </div>
    </div>
  )
}

// ── CandidateFocusView ────────────────────────────────────────────────────────

function CandidateFocusView({
  candidateId,
  row,
  onBack,
  onAddToActive,
  onAddToPool,
  onSubmitToJob,
}: {
  candidateId: string
  row: CandidateSmartRow
  onBack: () => void
  onAddToActive: () => void
  onAddToPool: () => void
  onSubmitToJob: () => void
}) {
  const queryClient = useQueryClient()
  const commandQ = useQuery({
    queryKey: ['candidate-command-center', candidateId],
    queryFn: async () => (await candidatesApi.commandCenter(candidateId)).data.data,
    enabled: !!candidateId,
  })
  const cc = commandQ.data as CCData | null
  const [activeTab, setActiveTab] = useState('overview')
  const [intelPanelOpen, setIntelPanelOpen] = useState(true)
  const ccTabs = (cc as any)?.tabs || {}
  const engagements = Array.isArray(ccTabs.engagement) ? ccTabs.engagement : []
  const notes = Array.isArray(ccTabs.structured_notes) ? ccTabs.structured_notes : []
  const structuredActivity = Array.isArray(ccTabs.structured_activity) ? ccTabs.structured_activity : []
  const historyItems = Array.isArray(ccTabs.history) ? ccTabs.history : []
  const documents = ccTabs.documents || {}

  const { color: rColor } = scoreColor(row.signals?.readiness_score)
  const { color: fColor } = scoreColor(row.signals?.fit_score)
  const { color: cColor } = scoreColor(row.signals?.completeness_score)
  const candidateDetail: any = (cc as any)?.candidate || {}
  const protectionCandidate = {
    is_agency_protected: candidateDetail?.is_agency_protected ?? row.is_agency_protected,
    protected_until: candidateDetail?.protected_until ?? row.protected_until,
    protection_scope: candidateDetail?.protection_scope ?? row.protection_scope,
  }
  const formatValue = (v: any) => (v === null || v === undefined || v === '' ? '—' : String(v))
  const expectedSalary = candidateDetail.expected_salary_min || candidateDetail.expected_salary_max
    ? `${candidateDetail.expected_salary_min || '—'} - ${candidateDetail.expected_salary_max || '—'} ${candidateDetail.salary_currency || ''}`.trim()
    : '—'
  const topTags = Array.isArray(candidateDetail.tags) ? candidateDetail.tags : (row.skills || []).slice(0, 3)

  return (
    <div className="flex flex-1 flex-col bg-white overflow-hidden animate-in fade-in duration-500">
      {/* 1. Sticky Intelligence Header */}
      <div className="sticky top-0 z-30 border-b border-slate-200 bg-white shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07),0_10px_20px_-2px_rgba(0,0,0,0.04)]">
        <div className="flex h-14 items-center justify-between border-b border-slate-800/10 bg-slate-900 px-6 text-white">
          <div className="flex items-center gap-4">
            <button 
              onClick={onBack}
              className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 text-xs font-black uppercase tracking-widest hover:bg-white/20 transition-all border border-white/10"
            >
              <ChevronDown size={16} className="rotate-90" /> Back to Search
            </button>
            <div className="h-6 w-px bg-white/20 mx-2" />
            <div className="flex items-center gap-3">
               <Avatar
                 size={32}
                 style={{ backgroundColor: avatarColor(row.name) }}
                 className="font-black border border-white/20 shadow-sm"
               >
                 {(row.name || '?').charAt(0)}
               </Avatar>
               <div className="min-w-0">
                  <h2 className="text-sm font-black truncate tracking-tight leading-none mb-1">{row.name}</h2>
                  <p className="text-[10px] font-bold text-slate-400 truncate uppercase tracking-widest leading-none">{row.current_title || 'Expert Professional'}</p>
                  {protectionCandidate.is_agency_protected && (
                    <div className="mt-2">
                      <ProtectionBadge candidate={protectionCandidate} compact />
                    </div>
                  )}
               </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
             <button onClick={onAddToActive} className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-black uppercase tracking-wider hover:bg-indigo-500 shadow-lg transition-all active:scale-95"><Zap size={14} /> Active</button>
             <button onClick={onSubmitToJob} className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-wider hover:bg-white/20 transition-all active:scale-95"><Target size={14} /> Match</button>
             <button onClick={onAddToPool} className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-wider hover:bg-white/20 transition-all active:scale-95"><Users size={14} /> Pool</button>
           </div>
        </div>

        <div className="grid grid-cols-1 gap-3 bg-gradient-to-r from-slate-50 to-white px-6 py-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <div className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Candidate Identity</div>
            <div className="space-y-1">
              <div className="text-sm font-black tracking-tight text-slate-900">{row.name}</div>
              <div className="text-xs font-bold text-slate-600">{row.current_title || 'Professional'}</div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-semibold text-slate-500">
                <span className="inline-flex items-center gap-1"><MapPin size={11} />{row.location || 'Remote'}</span>
                <span className="inline-flex items-center gap-1"><Briefcase size={11} />{row.experience ? `${row.experience} Years` : 'N/A'}</span>
                <span className="inline-flex items-center gap-1"><Clock3 size={11} />{row.availability_status || noticePeriodLabel(row.notice_period_days)}</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <div className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Decision Signals</div>
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl bg-slate-50 px-2 py-2 text-center">
                <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Fit</div>
                <div className="text-lg font-black tabular-nums" style={{ color: fColor }}>{row.signals?.fit_score ?? '—'}</div>
              </div>
              <div className="rounded-xl bg-slate-50 px-2 py-2 text-center">
                <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Ready</div>
                <div className="text-lg font-black tabular-nums" style={{ color: rColor }}>{row.signals?.readiness_score ?? '—'}</div>
              </div>
              <div className="rounded-xl bg-slate-50 px-2 py-2 text-center">
                <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Profile</div>
                <div className="text-lg font-black tabular-nums" style={{ color: cColor }}>{row.signals?.completeness_score ?? '—'}</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <div className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Activity Summary</div>
            <div className="space-y-1.5 text-[11px] font-semibold text-slate-600">
              <div className="flex items-center justify-between"><span>Active Engagements</span><span className="font-black text-indigo-600">{row.open_engagements || 0}</span></div>
              <div className="flex items-center justify-between"><span>Pool Membership</span><span className="font-black text-slate-800">{row.pools?.length || 0}</span></div>
              <div className="flex items-center justify-between"><span>Last Activity</span><span className="font-black text-slate-800">{row.last_activity ? dayjs(row.last_activity).fromNow() : 'Never'}</span></div>
            </div>
            {!!(cc as any)?.summary && (
              <div className="mt-2 line-clamp-2 rounded-xl bg-indigo-50 px-2.5 py-2 text-[11px] font-medium italic text-indigo-700">
                {(cc as any).summary}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden bg-slate-50/30 p-4 lg:p-5">
        <div className="mb-3 hidden items-center justify-end md:flex lg:hidden">
          <button
            onClick={() => setIntelPanelOpen(v => !v)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-black uppercase tracking-wider text-slate-700 hover:bg-slate-50"
          >
            {intelPanelOpen ? 'Hide Intelligence' : 'Show Intelligence'}
          </button>
        </div>

        <div className="grid h-full min-h-0 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_360px]">
          <div className="min-h-0 overflow-y-auto custom-scrollbar space-y-4 pr-0 lg:pr-1">
            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden min-h-[620px]">
            <div className="px-8 border-b border-slate-100 bg-white sticky top-0 z-10">
              <Tabs 
                activeKey={activeTab} 
                onChange={setActiveTab}
                className="candidate-focus-tabs"
                items={[
                  { key: 'overview', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Overview</span> },
                  { key: 'resume', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Resume</span> },
                  { key: 'intelligence', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Intelligence</span> },
                  { key: 'engagements', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Engagements</span> },
                  { key: 'pools', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Pools</span> },
                  { key: 'documents', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Documents</span> },
                  { key: 'notes', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Notes</span> },
                  { key: 'activity', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">Activity</span> },
                  { key: 'history', label: <span className="text-[11px] font-black uppercase tracking-widest py-4 block">History</span> },
                ]}
              />
            </div>

            <div className="p-8">
               {activeTab === 'overview' && (
                 <div className="space-y-6 animate-in slide-in-from-bottom-2 duration-500">
                   <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                     <div className="grid grid-cols-1 gap-2 text-sm font-semibold text-slate-800 md:grid-cols-2 md:gap-4">
                       <div>
                         <span className="text-slate-500">Email: </span>
                         <span>{formatValue(candidateDetail.email)}</span>
                       </div>
                       <div>
                         <span className="text-slate-500">Phone: </span>
                         <span>{formatValue(candidateDetail.phone || candidateDetail.phone_number)}</span>
                       </div>
                     </div>
                   </div>

                   <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                     <div className="rounded-2xl border border-slate-200 p-4">
                       <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Basic Information</h4>
                       <div className="space-y-2 text-xs">
                         <div className="flex justify-between"><span className="text-slate-500">Full Name</span><span className="font-semibold text-slate-800">{formatValue(row.name)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Current Role</span><span className="font-semibold text-slate-800">{formatValue(row.current_title)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Experience</span><span className="font-semibold text-slate-800">{formatValue(row.experience ? `${row.experience} Years` : null)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Current Company</span><span className="font-semibold text-slate-800">{formatValue(row.company || candidateDetail.current_company)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Location</span><span className="font-semibold text-slate-800">{formatValue(row.location)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Notice Period</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.notice_period_days ?? row.notice_period_days)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Expected Salary</span><span className="font-semibold text-slate-800">{expectedSalary}</span></div>
                       </div>
                     </div>

                     <div className="rounded-2xl border border-slate-200 p-4">
                       <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Contact Details</h4>
                       <div className="space-y-2 text-xs">
                         <div className="flex justify-between"><span className="text-slate-500">Email</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.email)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Phone</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.phone || candidateDetail.phone_number)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Alternate Phone</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.whatsapp)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">LinkedIn</span><span className="font-semibold text-slate-800 truncate max-w-[220px]">{formatValue(candidateDetail.linkedin_url)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Portfolio</span><span className="font-semibold text-slate-800 truncate max-w-[220px]">{formatValue(candidateDetail.profile?.portfolio_url || candidateDetail.portfolio_url)}</span></div>
                       </div>
                     </div>

                     <div className="rounded-2xl border border-slate-200 p-4">
                       <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Professional Details</h4>
                       <div className="space-y-2 text-xs">
                         <div className="flex justify-between"><span className="text-slate-500">Skills</span><span className="font-semibold text-slate-800 text-right">{formatValue((row.skills || []).join(', '))}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Industry</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.industry)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Department</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.department)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Employment Type</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.employment_type)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Work Preference</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.work_mode_preference)}</span></div>
                       </div>
                     </div>

                     <div className="rounded-2xl border border-slate-200 p-4">
                       <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Source Information</h4>
                       <div className="space-y-2 text-xs">
                         <div className="flex justify-between"><span className="text-slate-500">Source</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.source || row.source)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Added By</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.created_by)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Added Date</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.created_at ? dayjs(candidateDetail.created_at).format('DD MMM YYYY') : null)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Agency / Company</span><span className="font-semibold text-slate-800">{formatValue(row.company || candidateDetail.current_company)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Tags</span><span className="font-semibold text-slate-800 text-right">{formatValue(topTags.join(', '))}</span></div>
                       </div>
                     </div>

                     <div className="rounded-2xl border border-slate-200 p-4 lg:col-span-2">
                       <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">System Information</h4>
                       <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-xs">
                         <div className="flex justify-between"><span className="text-slate-500">Candidate State</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.candidate_state || candidateDetail.lifecycle_state)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Pool Type</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.candidate_pool)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Active Status</span><span className="font-semibold text-slate-800">{formatValue(candidateDetail.is_in_active_work)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Last Activity</span><span className="font-semibold text-slate-800">{formatValue(row.last_activity ? dayjs(row.last_activity).fromNow() : null)}</span></div>
                         <div className="flex justify-between"><span className="text-slate-500">Owner / Recruiter</span><span className="font-semibold text-slate-800">{formatValue(row.owner_name || candidateDetail.owner_user_id)}</span></div>
                       </div>
                     </div>
                   </div>
                 </div>
               )}

               {activeTab === 'resume' && (
                 <div className="h-[800px] bg-slate-100 rounded-2xl border border-slate-200 flex flex-col animate-in zoom-in-95 duration-300">
                    <div className="flex-none p-4 bg-slate-900 flex items-center justify-between text-white rounded-t-2xl">
                       <div className="flex items-center gap-3">
                          <FileText size={18} className="text-indigo-400" />
                          <span className="text-xs font-black uppercase tracking-widest">Candidate_Resume_Final.pdf</span>
                       </div>
                       <button 
                         onClick={() => row.resume_url && window.open(row.resume_url, '_blank')}
                         className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all"
                       >
                          <Download size={14} /> Download Original
                       </button>
                    </div>
                    <div className="flex-1 flex items-center justify-center">
                       {row.resume_url ? (
                         <iframe 
                           src={row.resume_url} 
                           className="w-full h-full border-0 rounded-b-2xl" 
                           title="Resume Preview"
                         />
                       ) : (
                         <div className="text-center">
                            <FileText size={48} className="mx-auto text-slate-300 mb-4" />
                            <p className="text-slate-500 font-bold uppercase tracking-widest">Resume document not found on server</p>
                         </div>
                       )}
                    </div>
                 </div>
               )}

               {activeTab === 'intelligence' && (
                 <div className="animate-in fade-in duration-300 space-y-6">
                   <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                     <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                       <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Fit Score</p>
                       <p className="mt-1 text-3xl font-black tabular-nums" style={{ color: fColor }}>{row.signals?.fit_score ?? '—'}</p>
                     </div>
                     <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                       <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Readiness</p>
                       <p className="mt-1 text-3xl font-black tabular-nums" style={{ color: rColor }}>{row.signals?.readiness_score ?? '—'}</p>
                     </div>
                     <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                       <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Profile Completeness</p>
                       <p className="mt-1 text-3xl font-black tabular-nums" style={{ color: cColor }}>{row.signals?.completeness_score ?? '—'}</p>
                     </div>
                   </div>
                   <div className="rounded-2xl border border-slate-200 p-5">
                     <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Risk And Signals</p>
                     {(row.signals?.warning_signals || []).length > 0 ? (
                       <div className="mt-3 flex flex-wrap gap-2">
                         {(row.signals?.warning_signals || []).map((signal, idx) => (
                           <span key={`${signal}-${idx}`} className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-wide text-amber-700">
                             {String(signal)}
                           </span>
                         ))}
                       </div>
                     ) : (
                       <p className="mt-3 text-xs font-semibold text-slate-500">No risk flags available.</p>
                     )}
                   </div>
                   {!!(cc as any)?.summary && (
                     <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5">
                       <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">AI Summary</p>
                       <p className="mt-2 text-sm leading-relaxed text-indigo-800">{(cc as any).summary}</p>
                     </div>
                   )}
                 </div>
               )}

               {activeTab === 'engagements' && (
                 <div className="animate-in fade-in duration-300 space-y-4">
                   <div className="flex items-center justify-between">
                     <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">Active Engagements</h4>
                     <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-widest text-indigo-700">
                       {engagements.length} records
                     </span>
                   </div>
                   {engagements.length > 0 ? (
                     <div className="space-y-3">
                       {engagements.map((eng: any, idx: number) => (
                         <div key={eng.id || idx} className="rounded-2xl border border-slate-200 p-4">
                           <div className="flex items-center justify-between gap-3">
                             <div>
                               <p className="text-sm font-black text-slate-900">{eng.job_title || eng.title || 'Untitled Engagement'}</p>
                               <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{eng.stage || eng.status || 'Unknown Stage'}</p>
                             </div>
                             <span className="text-[11px] font-semibold text-slate-500">{eng.updated_at ? dayjs(eng.updated_at).fromNow() : 'No updates'}</span>
                           </div>
                         </div>
                       ))}
                     </div>
                   ) : (
                     <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-10 text-center">
                       <p className="text-xs font-bold uppercase tracking-widest text-slate-500">No engagement timeline available</p>
                     </div>
                   )}
                 </div>
               )}

               {activeTab === 'pools' && (
                 <div className="animate-in fade-in duration-300 space-y-4">
                   <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">Pool Membership</h4>
                   {(row.pools || []).length > 0 ? (
                     <div className="flex flex-wrap gap-2">
                       {(row.pools || []).map((pool: any, idx: number) => (
                         <span key={pool?.id || idx} className="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-black uppercase tracking-wider text-indigo-700">
                           {pool?.name || String(pool)}
                         </span>
                       ))}
                     </div>
                   ) : (
                     <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-10 text-center">
                       <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Candidate is not in any pool</p>
                     </div>
                   )}
                 </div>
               )}

               {activeTab === 'documents' && (
                 <div className="animate-in fade-in duration-300 space-y-3">
                   <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">Documents</h4>
                   <div className="rounded-2xl border border-slate-200 p-4">
                     <div className="flex items-center justify-between">
                       <div>
                         <p className="text-xs font-black uppercase tracking-wider text-slate-700">Resume</p>
                         <p className="text-[11px] font-semibold text-slate-500">{row.resume_url || documents.resume_url ? 'Available' : 'Not Available'}</p>
                       </div>
                       {(row.resume_url || documents.resume_url) && (
                         <button
                           onClick={() => window.open(row.resume_url || documents.resume_url, '_blank')}
                           className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[10px] font-black uppercase tracking-wider text-slate-700 hover:bg-slate-50"
                         >
                           Open
                         </button>
                       )}
                     </div>
                   </div>
                 </div>
               )}

               {activeTab === 'notes' && (
                 <div className="animate-in fade-in duration-300 space-y-3">
                   <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">Notes</h4>
                   {notes.length > 0 ? (
                     notes.slice(0, 20).map((note: any, idx: number) => (
                       <div key={note.id || idx} className="rounded-2xl border border-slate-200 p-4">
                         <p className="text-xs font-semibold text-slate-700">{note.note || note.text || 'Note'}</p>
                         <p className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">{note.created_at ? dayjs(note.created_at).fromNow() : 'Timestamp unavailable'}</p>
                       </div>
                     ))
                   ) : (
                     <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-10 text-center">
                       <p className="text-xs font-bold uppercase tracking-widest text-slate-500">No structured notes found</p>
                     </div>
                   )}
                 </div>
               )}

               {activeTab === 'activity' && (
                 <div className="animate-in fade-in duration-300 space-y-3">
                   <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">Activity</h4>
                   {structuredActivity.length > 0 ? (
                     structuredActivity.slice(0, 30).map((item: any, idx: number) => (
                       <div key={item.id || idx} className="rounded-2xl border border-slate-200 p-4">
                         <div className="flex items-start justify-between gap-3">
                           <p className="text-xs font-semibold text-slate-700">{item.description || item.event || item.title || 'Activity Event'}</p>
                           <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wider text-slate-400">{item.created_at ? dayjs(item.created_at).fromNow() : ''}</span>
                         </div>
                       </div>
                     ))
                   ) : (
                     <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-10 text-center">
                       <p className="text-xs font-bold uppercase tracking-widest text-slate-500">No activity feed available</p>
                     </div>
                   )}
                 </div>
               )}

               {activeTab === 'history' && (
                 <div className="animate-in fade-in duration-300 space-y-3">
                   <h4 className="text-sm font-black uppercase tracking-widest text-slate-800">History</h4>
                   {historyItems.length > 0 ? (
                     historyItems.slice(0, 30).map((item: any, idx: number) => (
                       <div key={item.id || idx} className="rounded-2xl border border-slate-200 p-4">
                         <div className="flex items-start justify-between gap-3">
                           <p className="text-xs font-semibold text-slate-700">{item.label || item.title || item.event || 'History Event'}</p>
                           <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wider text-slate-400">{item.created_at ? dayjs(item.created_at).fromNow() : ''}</span>
                         </div>
                       </div>
                     ))
                   ) : (
                     <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-10 text-center">
                       <p className="text-xs font-bold uppercase tracking-widest text-slate-500">No history timeline available</p>
                     </div>
                   )}
                 </div>
               )}
              </div>
            </div>
          </div>

          <aside className={`${intelPanelOpen ? 'block' : 'hidden'} lg:block min-h-0 overflow-y-auto custom-scrollbar`}>
            <div className="rounded-3xl border border-indigo-200 bg-white shadow-sm">
              <div className="border-b border-indigo-100 bg-indigo-50 px-4 py-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500">AI Intelligence Panel</p>
              </div>
              <div className="space-y-4 p-4">
                {protectionCandidate.is_agency_protected && (
                  <ProtectionStatusPanel candidate={protectionCandidate} compact />
                )}
                <section className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">AI Summary</p>
                  {commandQ.isLoading ? (
                    <div className="mt-2 space-y-2">
                      <div className="h-2.5 w-full animate-pulse rounded bg-slate-100" />
                      <div className="h-2.5 w-5/6 animate-pulse rounded bg-slate-100" />
                    </div>
                  ) : (
                    <p className="mt-2 text-xs leading-relaxed text-slate-700">
                      {(cc as any)?.summary || 'AI summary is not available yet for this candidate.'}
                    </p>
                  )}
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Decision Signals</p>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Fit</div>
                      <div className="text-lg font-black tabular-nums" style={{ color: fColor }}>{row.signals?.fit_score ?? '—'}</div>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Readiness</div>
                      <div className="text-lg font-black tabular-nums" style={{ color: rColor }}>{row.signals?.readiness_score ?? '—'}</div>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Profile</div>
                      <div className="text-lg font-black tabular-nums" style={{ color: cColor }}>{row.signals?.completeness_score ?? '—'}</div>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <div className="text-[9px] font-black uppercase tracking-wider text-slate-400">Risk</div>
                      <div className="text-lg font-black tabular-nums text-amber-600">{(row.signals?.warning_signals || []).length}</div>
                    </div>
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Usage Context</p>
                  <div className="mt-2 space-y-1.5 text-[11px] font-semibold text-slate-600">
                    <div className="flex items-center justify-between"><span>Active Engagements</span><span className="font-black text-indigo-600">{row.open_engagements || 0}</span></div>
                    <div className="flex items-center justify-between"><span>Pools</span><span className="font-black text-slate-800">{row.pools?.length || 0}</span></div>
                    <div className="flex items-center justify-between"><span>Last Activity</span><span className="font-black text-slate-800">{row.last_activity ? dayjs(row.last_activity).fromNow() : 'Never'}</span></div>
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">AI Suggestions</p>
                  <div className="mt-2 space-y-2">
                    <button onClick={onSubmitToJob} className="w-full rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-left text-[11px] font-black uppercase tracking-wider text-indigo-700 hover:bg-indigo-100">
                      Match To Job
                    </button>
                    <button onClick={onAddToPool} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-[11px] font-black uppercase tracking-wider text-slate-700 hover:bg-slate-50">
                      Add To Pool
                    </button>
                    <button onClick={onAddToActive} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-[11px] font-black uppercase tracking-wider text-slate-700 hover:bg-slate-50">
                      Engage Candidate
                    </button>
                  </div>
                </section>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

// ── BulkActionsBar ────────────────────────────────────────────────────────────

function BulkActionsBar({
  count, onClear, onAddToActive, onAddToPool, onExport, onArchive, onAssign, exportDisabled, exportDisabledReason,
}: {
  count: number
  onClear: () => void
  onAddToActive: () => void
  onAddToPool: () => void
  onExport: () => void
  onArchive: () => void
  onAssign: () => void
  exportDisabled?: boolean
  exportDisabledReason?: string
}) {
  const exportButton = (
    <button
      onClick={onExport}
      disabled={exportDisabled}
      className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-white px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 transition disabled:cursor-not-allowed disabled:opacity-50"
    >
      <Download size={11} /> Export
    </button>
  )

  return (
    <div className="flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2 shadow-sm">
      <span className="text-xs font-bold text-indigo-700">{count} selected</span>
      <div className="h-4 w-px bg-indigo-200 mx-1" />
      <button
        onClick={onAddToActive}
        className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-indigo-700 transition"
      >
        <Zap size={11} /> Active Work
      </button>
      <button
        onClick={onAddToPool}
        className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-white px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 transition"
      >
        <Users size={11} /> Add to Pool
      </button>
      <button
        onClick={onAssign}
        className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-white px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 transition"
      >
        <User size={11} /> Assign Owner
      </button>
      {exportDisabled && exportDisabledReason ? (
        <Tooltip title={exportDisabledReason}>{exportButton}</Tooltip>
      ) : exportButton}
      <button
        onClick={onArchive}
        className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50 transition"
      >
        <Trash2 size={11} /> Archive
      </button>
      <button onClick={onClear} className="ml-auto text-slate-400 hover:text-slate-600">
        <XCircle size={14} />
      </button>
    </div>
  )
}

// ── Column Config Modal ────────────────────────────────────────────────────────

const ALL_COLUMNS = [
  { key: 'candidate', label: 'Candidate', fixed: true },
  { key: 'skills', label: 'Skills' },
  { key: 'availability', label: 'Availability' },
  { key: 'fit', label: 'Fit Score' },
  { key: 'readiness', label: 'Readiness' },
  { key: 'engagements', label: 'Engagements' },
  { key: 'source', label: 'Source' },
  { key: 'owner', label: 'Owner' },
  { key: 'last_activity', label: 'Last Activity' },
  { key: 'actions', label: 'Actions', fixed: true },
]

// ── Main: CandidateDatabase ───────────────────────────────────────────────────

export default function CandidateDatabase() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canCreate = usePermission('candidates.candidate.create')

  // ── State ──────────────────────────────────────────────────────────────
  const [searchMode, setSearchMode] = useState<SearchMode>('all')
  const [searchText, setSearchText] = useState('')
  const [searchInputType, setSearchInputType] = useState<'keyword' | 'semantic'>('keyword')
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [savedSearchOpen, setSavedSearchOpen] = useState(false)
  const [colConfigOpen, setColConfigOpen] = useState(false)
  const [visibleCols, setVisibleCols] = useState<string[]>(DEFAULT_VISIBLE_COLS)
  const [addOpen, setAddOpen] = useState(false)
  const [addToPoolOpen, setAddToPoolOpen] = useState(false)
  const [poolTargetId, setPoolTargetId] = useState<string | null>(null)
  const [submitToJobOpen, setSubmitToJobOpen] = useState(false)
  const [submitTargetId, setSubmitTargetId] = useState<string | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [sortField, setSortField] = useState<string>('last_activity')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [viewModePreference, setViewModePreference] = useState<CandidateViewMode>(() => {
    if (typeof window === 'undefined') return 'list'
    const raw = window.localStorage.getItem(CANDIDATE_DB_VIEW_MODE_KEY)
    return raw === 'compact' || raw === 'card' || raw === 'list' ? raw : 'list'
  })
  const [filterRailCollapsed, setFilterRailCollapsed] = useState(false)
  const [viewMode, setViewMode] = useState<'search' | 'focus'>('search')
  const searchBodyRef = useRef<HTMLDivElement | null>(null)
  const searchScrollTopRef = useRef(0)
  const previousFilterRailCollapsedRef = useRef(false)

  // ── Derived API params ─────────────────────────────────────────────────
  const apiView = useMemo(() => {
    if (searchMode === 'duplicates') return 'duplicates'
    if (searchMode === 'needs_review') return 'missing_contact_info'
    return 'all_candidates'
  }, [searchMode])

  const apiParams = useMemo(() => ({
    view: apiView,
    search: searchText || undefined,
    source_type: filters.source_type || undefined,
    owner: filters.owner || undefined,
    passport_linked: filters.passport_linked === true ? true : undefined,
    duplicates: searchMode === 'duplicates' ? true : (filters.has_duplicates === true ? true : undefined),
    protection_status: filters.protection_status !== 'all' ? filters.protection_status : undefined,
    limit: 200,
  }), [apiView, searchText, filters.source_type, filters.owner, filters.passport_linked, filters.has_duplicates, filters.protection_status, searchMode])

  // ── Queries ────────────────────────────────────────────────────────────
  const dbQ = useQuery({
    queryKey: ['candidate-database-v2', apiParams],
    queryFn: async () => {
      const response = await candidatesApi.database(apiParams)
      const payload = response.data?.data

      return payload
    },
    staleTime: 30_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  // Keep Candidate Database on the dedicated database endpoint only.
  // The legacy /candidates/ list endpoint is unstable in this surface.
  const enableLegacyListFallback = true

  const fallbackListQ = useQuery({
    queryKey: ['candidate-list-fallback-v1', { search: searchText || '' }],
    queryFn: async () => (await candidatesApi.list({ search: searchText || undefined })).data.data,
    enabled: enableLegacyListFallback && (dbQ.isError || (
      dbQ.isSuccess &&
      (
        (Array.isArray((dbQ.data as any)?.items) && (dbQ.data as any).items.length === 0) ||
        (Array.isArray((dbQ.data as any)?.results) && (dbQ.data as any).results.length === 0) ||
        (Array.isArray((dbQ.data as any)?.candidates) && (dbQ.data as any).candidates.length === 0)
      )
    )),
    staleTime: 30_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const apiRows = useMemo((): CandidateSmartRow[] => {
    const payload: any = dbQ.data
    if (!payload) return []
    let items = []
    if (Array.isArray(payload.items)) items = payload.items
    else if (Array.isArray(payload.results)) items = payload.results
    else if (Array.isArray(payload.candidates)) items = payload.candidates
    return items.map(mapCandidateListItemToSmartRow)
  }, [dbQ.data])

  const fallbackRows = useMemo((): CandidateSmartRow[] => {
    const candidates = (fallbackListQ.data as any)?.candidates
    if (!Array.isArray(candidates)) return []
    return candidates.map(mapCandidateListItemToSmartRow)
  }, [fallbackListQ.data])

  const shouldEnableActiveFallback = useMemo(() => {
    const dbUnavailable = dbQ.isError || (dbQ.isSuccess && apiRows.length === 0)
    const listUnavailable = !enableLegacyListFallback || fallbackListQ.isError || (fallbackListQ.isSuccess && fallbackRows.length === 0)
    return dbUnavailable && listUnavailable
  }, [dbQ.isError, dbQ.isSuccess, apiRows.length, fallbackListQ.isError, fallbackListQ.isSuccess, fallbackRows.length, enableLegacyListFallback])

  const activeWorkFallbackQ = useQuery({
    queryKey: ['candidate-active-work-fallback-v1'],
    queryFn: async () => (await candidatesApi.activeWork({ mode: 'focus' })).data.data,
    enabled: shouldEnableActiveFallback,
    staleTime: 30_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const activeFallbackRows = useMemo((): CandidateSmartRow[] => {
    const data: any = activeWorkFallbackQ.data
    if (!data) return []

    const focusFlat = Object.values(data?.focus || {}).flat() as any[]
    const boardFlat = Object.values(data?.board || {}).flat() as any[]
    const queueFlat = Array.isArray(data?.queue) ? data.queue : []
    const flat = [...focusFlat, ...boardFlat, ...queueFlat]
    if (flat.length === 0) return []

    const byId = new Map<string, CandidateSmartRow>()
    flat.forEach((item: any) => {
      const id = String(item?.candidate || item?.candidate_id || '')
      if (!id) return

      if (!byId.has(id)) {
        byId.set(id, mapActiveWorkItemToSmartRow(item))
        return
      }

      const prev = byId.get(id)!
      const stage = item?.stage
      const nextSummary = { ...(prev.job_engagement_summary || {}) }
      if (stage) nextSummary[stage] = (nextSummary[stage] || 0) + 1
      byId.set(id, {
        ...prev,
        open_engagements: (prev.open_engagements || 0) + 1,
        job_engagement_summary: nextSummary,
        last_activity:
          item?.last_activity_at && (!prev.last_activity || item.last_activity_at > prev.last_activity)
            ? item.last_activity_at
            : prev.last_activity,
      })
    })

    return Array.from(byId.values())
  }, [activeWorkFallbackQ.data])

  const sourceRows = apiRows.length > 0
    ? apiRows
    : fallbackRows.length > 0
      ? fallbackRows
      : activeFallbackRows

  useEffect(() => {
    setCurrentPage(1)
  }, [searchMode, searchText, filters, pageSize, fallbackRows.length, activeFallbackRows.length, apiRows.length])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(CANDIDATE_DB_VIEW_MODE_KEY, viewModePreference)
    }
  }, [viewModePreference])

  const poolsQ = useQuery({
    queryKey: ['talent-pools-list'],
    queryFn: async () => (await talentPoolsApi.list()).data.data?.talent_pools || [],
    enabled: addToPoolOpen,
  })

  const jobsQ = useQuery({
    queryKey: ['requisitions-list'],
    queryFn: async () => (await requisitionsApi.list({ status: 'approved' })).data.data?.requisitions || [],
    enabled: submitToJobOpen,
  })

  // ── Client-side filtering ──────────────────────────────────────────────
  const filteredRows = useMemo(() => {
    let rows: CandidateSmartRow[] = sourceRows

    if (filters.skills) {
      const terms = filters.skills.toLowerCase().split(',').map(s => s.trim()).filter(Boolean)
      rows = rows.filter(r =>
        terms.some(t => (r.skills || []).some(s => s.toLowerCase().includes(t)))
      )
    }
    if (filters.experience_min) {
      const min = parseFloat(filters.experience_min)
      rows = rows.filter(r => r.experience != null && r.experience >= min)
    }
    if (filters.experience_max) {
      const max = parseFloat(filters.experience_max)
      rows = rows.filter(r => r.experience != null && r.experience <= max)
    }
    if (filters.location) {
      const loc = filters.location.toLowerCase()
      rows = rows.filter(r => r.location?.toLowerCase().includes(loc))
    }
    if (filters.last_activity_days) {
      const days = parseInt(filters.last_activity_days)
      const cutoff = dayjs().subtract(days, 'day')
      rows = rows.filter(r => {
        const la = r.last_activity || r.last_touch
        return la ? dayjs(la).isAfter(cutoff) : false
      })
    }
    if (filters.readiness_min) {
      const min = parseInt(filters.readiness_min)
      rows = rows.filter(r => (r.signals?.readiness_score ?? 0) >= min)
    }
    if (filters.fit_min) {
      const min = parseInt(filters.fit_min)
      rows = rows.filter(r => (r.signals?.fit_score ?? 0) >= min)
    }
    if (filters.notice_max_days) {
      const max = parseInt(filters.notice_max_days)
      if (max === 0) {
        rows = rows.filter(r => !r.notice_period_days)
      } else {
        rows = rows.filter(r => !r.notice_period_days || r.notice_period_days <= max)
      }
    }
    if (filters.availability) {
      rows = rows.filter(r => r.availability_status === filters.availability)
    }
    if (filters.protection_status === 'protected') {
      rows = rows.filter(r => r.is_agency_protected)
    }
    if (filters.protection_status === 'not_protected') {
      rows = rows.filter(r => !r.is_agency_protected)
    }

    // Sort
    rows = [...rows].sort((a, b) => {
      let av: any, bv: any
      if (sortField === 'last_activity') {
        av = a.last_activity || a.last_touch || ''
        bv = b.last_activity || b.last_touch || ''
      } else if (sortField === 'experience') {
        av = a.experience ?? -1
        bv = b.experience ?? -1
      } else if (sortField === 'readiness') {
        av = a.signals?.readiness_score ?? -1
        bv = b.signals?.readiness_score ?? -1
      } else if (sortField === 'fit') {
        av = a.signals?.fit_score ?? -1
        bv = b.signals?.fit_score ?? -1
      } else if (sortField === 'name') {
        av = a.name || ''
        bv = b.name || ''
      } else {
        return 0
      }
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })

    return rows
  }, [sourceRows, filters, sortField, sortDir])

  const selectedRow = useMemo(
    () => sourceRows.find(r => r.id === selectedCandidateId) || null,
    [sourceRows, selectedCandidateId],
  )
  const selectedRows = useMemo(
    () => sourceRows.filter((row) => selectedRowKeys.includes(row.id)),
    [sourceRows, selectedRowKeys],
  )
  const selectedProtectedRows = useMemo(
    () => selectedRows.filter((row) => row.is_agency_protected),
    [selectedRows],
  )
  const submitTargetCandidate = useMemo(
    () => sourceRows.find((row) => row.id === submitTargetId) || null,
    [sourceRows, submitTargetId],
  )

  // ── Handlers ───────────────────────────────────────────────────────────
  const handleAddToActive = async (candidateId: string) => {
    try {
      await http.post(`/candidates/${candidateId}/engagements/`, { stage: 'new_lead' })
      message.success('Added to Active Work')
      queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })
    } catch {
      message.error('Failed to add to Active Work')
    }
  }

  const handleBulkAddToActive = async () => {
    try {
      await Promise.all(selectedRowKeys.map(id =>
        http.post(`/candidates/${id}/engagements/`, { stage: 'new_lead' }).catch(() => null)
      ))
      message.success(`${selectedRowKeys.length} candidates added to Active Work`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })
    } catch {
      message.error('Some additions failed')
    }
  }

  const handleAddToPool = async (candidateId: string, poolId: string) => {
    try {
      await talentPoolsApi.bulkAdd(poolId, { candidate_ids: [candidateId] })
      message.success('Added to pool')
      setAddToPoolOpen(false)
      setPoolTargetId(null)
    } catch {
      message.error('Failed to add to pool')
    }
  }

  const handleSubmitToJob = async (candidateId: string, jobId: string) => {
    try {
      await http.post(`/candidates/${candidateId}/engagements/`, { stage: 'submitted', job: jobId })
      message.success('Submitted to job')
      setSubmitToJobOpen(false)
      setSubmitTargetId(null)
      setSelectedJobId(null)
      queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })
    } catch (error: any) {
      message.error(extractApiErrorMessage(error, 'Failed to submit to job'))
    }
  }

  const handleBulkExport = () => {
    if (selectedProtectedRows.length > 0) {
      const firstProtected = selectedProtectedRows[0]
      message.error(protectionMessage(firstProtected))
      return
    }
    message.info('Export coming soon')
  }

  const handleColToggle = (key: string) => {
    setVisibleCols(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  // ── Table columns ──────────────────────────────────────────────────────
  const sortIndicator = (field: string) => {
    if (sortField !== field) return null
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  const makeHeader = (field: string, label: string) => (
    <button
      className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 hover:text-slate-900 uppercase tracking-[0.08em]"
      onClick={() => {
        if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortField(field); setSortDir('desc') }
      }}
    >
      {label}{sortIndicator(field)}
    </button>
  )

  const rowActionItems = (row: CandidateSmartRow) => ([
    {
      key: 'active',
      icon: <Zap size={12} />,
      label: 'Add to Active Work',
      onClick: () => handleAddToActive(row.id),
    },
    {
      key: 'pool',
      icon: <Users size={12} />,
      label: 'Add to Pool',
      onClick: () => { setPoolTargetId(row.id); setAddToPoolOpen(true) },
    },
    {
      key: 'job',
      icon: <Target size={12} />,
      label: 'Match to Job',
      onClick: () => { setSubmitTargetId(row.id); setSubmitToJobOpen(true) },
    },
    { type: 'divider' as const },
    {
      key: 'profile',
      icon: <ExternalLink size={12} />,
      label: 'View Full Profile',
      onClick: () => window.open(`/candidates/${row.id}`, '_blank'),
    },
  ])

  const actionMenuButton = (row: CandidateSmartRow) => (
    <Dropdown trigger={['click']} menu={{ items: rowActionItems(row) }}>
      <button className="flex items-center justify-center rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition">
        <MoreHorizontal size={14} />
      </button>
    </Dropdown>
  )

  const tableColumns = useMemo((): ColumnsType<CandidateSmartRow> => {
    const listCols: ColumnsType<CandidateSmartRow> = [
      {
        key: 'candidate',
        title: makeHeader('name', 'Candidate'),
        width: 340,
        fixed: 'left' as const,
        render: (_, row) => (
          <div className="flex flex-col gap-1 py-1">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-sm font-bold text-slate-900 truncate">{row.name}</span>
              <span className="text-[11px] font-semibold text-slate-500 truncate">
                {row.current_title || '—'}
              </span>
            </div>
            {row.is_agency_protected && <ProtectionBadge candidate={row} compact />}
            <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500 font-semibold">
              <span>{row.location || 'Remote'}</span>
              <span>•</span>
              <span>{row.experience != null ? `${row.experience} yr` : 'Exp N/A'}</span>
              {row.is_agency_protected && (
                <>
                  <span>•</span>
                  <span>Protected Until {formatProtectionDate(row.protected_until, 'DD MMM')}</span>
                  <span>•</span>
                  <span>Scope: {protectionScopeLabel(row.protection_scope)}</span>
                </>
              )}
            </div>
          </div>
        ),
      },
      {
        key: 'skills',
        title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Skills</span>,
        width: 150,
        render: (_, row) => {
          const skills = row.skills || []
          if (!skills.length) return <span className="text-slate-300 text-[10px]">N/A</span>
          return (
            <div className="flex flex-wrap gap-1">
              {skills.slice(0, 2).map((s, i) => (
                <span key={i} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600 font-semibold border border-slate-200/50">
                  {s}
                </span>
              ))}
              {skills.length > 2 && <span className="text-[10px] text-slate-400 font-semibold">+{skills.length - 2}</span>}
            </div>
          )
        },
      },
      {
        key: 'availability',
        title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Availability</span>,
        width: 100,
        render: (_, row) => availabilityBadge(row.availability_status, row.notice_period_days),
      },
      {
        key: 'fit',
        title: makeHeader('fit', 'Fit'),
        width: 60,
        align: 'center' as const,
        render: (_, row) => scoreBadge(row.signals?.fit_score),
      },
      {
        key: 'readiness',
        title: makeHeader('readiness', 'Readiness'),
        width: 70,
        align: 'center' as const,
        render: (_, row) => scoreBadge(row.signals?.readiness_score),
      },
      {
        key: 'engagements',
        title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Engagements</span>,
        width: 110,
        render: (_, row) => (
          <span className="text-[10px] font-semibold text-slate-700">{row.open_engagements || 0}</span>
        ),
      },
      {
        key: 'source',
        title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Source</span>,
        width: 90,
        render: (_, row) => (
          <span className="text-[10px] font-semibold text-slate-500 uppercase px-1.5 py-0.5 bg-slate-100 rounded border border-slate-200">
            {row.source_type || row.source || 'Direct'}
          </span>
        ),
      },
      {
        key: 'owner',
        title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Owner</span>,
        width: 100,
        render: (_, row) => (
          <span className="text-[10px] text-slate-600 font-semibold truncate">
            {row.owner_name || (row.owner ? 'Assigned' : <span className="text-slate-300 italic">Unassigned</span>)}
          </span>
        ),
      },
      {
        key: 'last_activity',
        title: makeHeader('last_activity', 'Last Activity'),
        width: 100,
        render: (_, row) => {
          const la = row.last_activity || row.last_touch
          return <span className="text-[10px] text-slate-500 font-semibold">{la ? dayjs(la).fromNow() : '—'}</span>
        },
      },
      {
        key: 'actions',
        title: '',
        width: 40,
        fixed: 'right' as const,
        render: (_, row) => actionMenuButton(row),
      },
    ]

    if (viewModePreference === 'compact') {
      return [
        {
          key: 'candidate',
          title: makeHeader('name', 'Candidate'),
          width: 260,
          render: (_, row) => (
            <div className="text-[11px] leading-tight">
              <div className="font-semibold text-slate-900 truncate">{row.name}</div>
              <div className="text-slate-500 truncate">{row.location || 'Remote'} • {row.experience != null ? `${row.experience}y` : 'N/A'}</div>
              {row.is_agency_protected && (
                <div className="mt-1">
                  <ProtectionBadge candidate={row} compact />
                </div>
              )}
            </div>
          ),
        },
        {
          key: 'availability',
          title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Availability</span>,
          width: 90,
          render: (_, row) => availabilityBadge(row.availability_status, row.notice_period_days),
        },
        {
          key: 'fit',
          title: makeHeader('fit', 'Fit'),
          width: 55,
          align: 'center' as const,
          render: (_, row) => scoreBadge(row.signals?.fit_score),
        },
        {
          key: 'source',
          title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Source</span>,
          width: 90,
          render: (_, row) => <span className="text-[10px] font-semibold text-slate-600">{row.source_type || row.source || 'Direct'}</span>,
        },
        {
          key: 'owner',
          title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Owner</span>,
          width: 100,
          render: (_, row) => <span className="text-[10px] font-semibold text-slate-600 truncate">{row.owner_name || 'Unassigned'}</span>,
        },
        {
          key: 'engagements',
          title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Eng</span>,
          width: 60,
          align: 'center' as const,
          render: (_, row) => <span className="text-[10px] font-semibold">{row.open_engagements || 0}</span>,
        },
        {
          key: 'actions',
          title: '',
          width: 40,
          render: (_, row) => actionMenuButton(row),
        },
      ]
    }

    if (viewModePreference === 'card') {
      return [
        {
          key: 'candidate_card',
          title: <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Candidates</span>,
          render: (_, row) => (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 my-1">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-bold text-slate-900 truncate">{row.name}</div>
                  <div className="text-xs font-semibold text-slate-500 truncate">{row.current_title || '—'}</div>
                </div>
                {actionMenuButton(row)}
              </div>
              <div className="mt-2 text-[11px] text-slate-600 font-semibold">
                {row.location || 'Remote'} • {row.experience != null ? `${row.experience} years` : 'Exp N/A'}
              </div>
              {row.is_agency_protected && (
                <div className="mt-2">
                  <ProtectionBadge candidate={row} compact />
                </div>
              )}
              <div className="mt-2 flex flex-wrap gap-1.5">
                {(row.skills || []).slice(0, 4).map((s, i) => (
                  <span key={i} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">{s}</span>
                ))}
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] font-semibold text-slate-600">
                <div>Availability: {row.availability_status || noticePeriodLabel(row.notice_period_days)}</div>
                <div>Source: {row.source_type || row.source || 'Direct'}</div>
                <div>Owner: {row.owner_name || 'Unassigned'}</div>
                <div>Engagements: {row.open_engagements || 0}</div>
                {row.is_agency_protected && <div>Protected Until: {formatProtectionDate(row.protected_until, 'DD MMM')}</div>}
                {row.is_agency_protected && <div>Scope: {protectionScopeLabel(row.protection_scope)}</div>}
              </div>
            </div>
          ),
        },
      ]
    }

    return listCols.filter(c => {
      const colKey = c.key as string
      const colDef = ALL_COLUMNS.find(a => a.key === colKey)
      if (colDef?.fixed) return true
      return visibleCols.includes(colKey)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleCols, sortField, sortDir, viewModePreference])

  const rowSelection: TableRowSelection<CandidateSmartRow> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys as string[]),
    columnWidth: 36,
    renderCell: (checked, record, index, originNode) => (
      <div onClick={e => e.stopPropagation()}>{originNode}</div>
    ),
  }

  const activeFilterCount = Object.entries(filters).filter(([, v]) => {
    if (typeof v === 'boolean') return v !== null
    if (v === 'all') return false
    return v !== '' && v !== null
  }).length
  const tableRowDensityClass =
    viewModePreference === 'compact' ? '[&>td]:py-1' :
    viewModePreference === 'card' ? '[&>td]:py-2' :
    '[&>td]:py-2'

  const enterFocusMode = (candidateId: string) => {
    previousFilterRailCollapsedRef.current = filterRailCollapsed
    searchScrollTopRef.current = searchBodyRef.current?.scrollTop ?? 0
    setSelectedCandidateId(candidateId)
    setFilterRailCollapsed(true)
    setViewMode('focus')
  }

  const exitFocusMode = () => {
    setViewMode('search')
    setFilterRailCollapsed(previousFilterRailCollapsedRef.current)
    requestAnimationFrame(() => {
      if (searchBodyRef.current) {
        searchBodyRef.current.scrollTop = searchScrollTopRef.current
      }
    })
  }

  return (
    <div className="-m-8 flex flex-col bg-[#f8fafc]" style={{ height: 'calc(100vh - 64px)' }}>

      {/* ── Zone A: Top Bar ══════════════════════════════════════════════════ */}
      <div className="flex h-12 flex-none items-center justify-between border-b border-slate-200 bg-white px-5 shadow-sm">
        <div className="flex items-center gap-3">
          <Sparkles size={15} className="text-indigo-600" />
          <span className="text-sm font-black text-slate-800 tracking-tight">Talent Hub</span>
          <div className="mx-1 h-4 w-px bg-slate-200" />
          {/* Surface switcher */}
          <div className="flex items-center gap-0.5 rounded-xl bg-slate-100 p-1">
            <button
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-sm"
            >
              <Database size={12} /> Database
            </button>
            <button
              onClick={() => navigate('/candidates/active')}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 transition"
            >
              <Activity size={12} /> Active Work
            </button>
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-100 p-0.5 shadow-sm">
            {(['list', 'compact', 'card'] as CandidateViewMode[]).map(mode => (
              <button
                key={mode}
                onClick={() => setViewModePreference(mode)}
                className={`rounded-md px-2.5 py-1 text-xs font-bold uppercase tracking-tighter transition ${
                  viewModePreference === mode ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
          <Tooltip title="Configure columns">
            <button
              onClick={() => setColConfigOpen(true)}
              className="flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              <Settings2 size={12} /> Columns
            </button>
          </Tooltip>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
          >
            <RefreshCw size={13} />
          </button>
          {canCreate && (
            <button
              onClick={() => setAddOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700"
            >
              <Plus size={13} /> Add Candidate
            </button>
          )}
        </div>
      </div>

      {/* ── Zone A: Search Bar ══════════════════════════════════════════════ */}
      <div className="flex flex-none items-center gap-3 border-b border-slate-200 bg-white px-5 py-2.5">
        {/* Filter toggle button (Collapsible rail) */}
        <button
          onClick={() => setFilterRailCollapsed(v => !v)}
          className={`flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-bold transition-all uppercase tracking-tighter ${
            !filterRailCollapsed
              ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
              : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Filter size={13} />
          {filterRailCollapsed ? 'Filters' : 'Hide Filters'}
        </button>

        {/* Main search input */}
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 focus-within:border-indigo-300 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100 transition shadow-sm">
          <Search size={14} className="shrink-0 text-slate-400" />
          <input
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            placeholder="Search candidates by name, title, skills..."
            className="flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder-slate-400 font-medium"
          />
          {searchText && (
            <button onClick={() => setSearchText('')} className="text-slate-400 hover:text-slate-600">
              <XCircle size={14} />
            </button>
          )}
        </div>

        {/* Search type toggle */}
        <div className="flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-100 p-0.5 shadow-sm">
          {(['keyword', 'semantic'] as const).map(type => (
            <button
              key={type}
              onClick={() => setSearchInputType(type)}
              className={`rounded-md px-3 py-1 text-xs font-bold transition uppercase tracking-tighter ${
                searchInputType === type
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {type === 'keyword' ? 'Keyword' : <span className="flex items-center gap-1"><Bot size={12} />Semantic AI</span>}
            </button>
          ))}
        </div>

        {/* Saved searches */}
        <Dropdown
          open={savedSearchOpen}
          onOpenChange={setSavedSearchOpen}
          trigger={['click']}
          menu={{
            items: STATIC_SAVED_SEARCHES.map(s => ({
              key: s.key,
              label: s.label,
              onClick: () => { setSearchText(s.label); setSavedSearchOpen(false) },
            })),
          }}
        >
          <button className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50 uppercase tracking-tighter">
            <BookOpen size={13} /> Saved Searches <ChevronDown size={12} />
          </button>
        </Dropdown>
      </div>

      {/* ── Mode Tabs ════════════════════════════════════════════════════════ */}
      <div className="flex h-10 flex-none items-center gap-1 border-b border-slate-100 bg-white px-5">
        {SEARCH_MODES.map(mode => (
          <button
            key={mode.key}
            onClick={() => setSearchMode(mode.key)}
            className={`rounded-lg px-4 py-1.5 text-xs font-bold transition uppercase tracking-widest ${
              searchMode === mode.key
                ? 'bg-slate-900 text-white shadow-md'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            {mode.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
            {dbQ.isLoading
              ? 'Querying Database...'
              : dbQ.isError && sourceRows.length > 0
                ? `Fallback data loaded · ${filteredRows.length} talents`
                : dbQ.isError
                  ? 'Database temporarily unavailable'
                  : `FOUND ${filteredRows.length} TALENTS`}
          </span>
        </div>
      </div>

      {/* ── Body: Search Mode / Focus Mode ═══════════════════════════════════ */}
      <div className="flex flex-1 overflow-y-auto relative">
        {viewMode === 'focus' && selectedCandidateId && selectedRow ? (
          <CandidateFocusView
            candidateId={selectedCandidateId}
            row={selectedRow}
            onBack={exitFocusMode}
            onAddToActive={() => handleAddToActive(selectedCandidateId)}
            onAddToPool={() => { setPoolTargetId(selectedCandidateId); setAddToPoolOpen(true) }}
            onSubmitToJob={() => { setSubmitTargetId(selectedCandidateId); setSubmitToJobOpen(true) }}
          />
        ) : (
          <>

            {/* Zone B: Collapsible Filter Rail */}
            <div
              className={`flex-none overflow-hidden transition-all duration-300 ease-in-out bg-white border-r border-slate-200 z-10 shadow-lg ${
                filterRailCollapsed ? 'w-0 border-r-0' : 'w-[260px]'
              }`}
            >
              <FilterRail
                filters={filters}
                onChange={partial => setFilters(prev => ({ ...prev, ...partial }))}
                onClear={() => setFilters(EMPTY_FILTERS)}
                memberOptions={[]}
              />
            </div>

            {/* Zone C: Center Results Table */}
            <div className="flex flex-1 flex-col bg-white">

              {/* Bulk actions bar */}
              {selectedRowKeys.length > 0 && (
                <div className="flex-none px-6 py-3 bg-indigo-50/50 border-b border-indigo-100">
                  <BulkActionsBar
                    count={selectedRowKeys.length}
                    onClear={() => setSelectedRowKeys([])}
                    onAddToActive={handleBulkAddToActive}
                    onAddToPool={() => { setAddToPoolOpen(true) }}
                    onExport={handleBulkExport}
                    onArchive={() => message.info('Archive coming soon')}
                    onAssign={() => message.info('Assign owner coming soon')}
                    exportDisabled={selectedProtectedRows.length > 0}
                    exportDisabledReason={
                      selectedProtectedRows.length > 0
                        ? `${selectedProtectedRows.length} selected candidate${selectedProtectedRows.length > 1 ? 's are' : ' is'} agency protected and cannot be exported.`
                        : undefined
                    }
                  />
                </div>
              )}

              <div ref={searchBodyRef} className="flex-1">
                <Table<CandidateSmartRow>
                  dataSource={filteredRows}
                  columns={tableColumns}
                  rowKey="id"
                  rowSelection={rowSelection}
                  size="small"
                  loading={dbQ.isLoading}
                  scroll={{ x: 1400 }}
                  pagination={{
                    current: currentPage,
                    pageSize,
                    showSizeChanger: true,
                    onChange: (page, nextSize) => {
                      setCurrentPage(page)
                      if (nextSize && nextSize !== pageSize) {
                        setPageSize(nextSize)
                        setCurrentPage(1)
                      }
                    },
                    showTotal: (total, range) => (
                      <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">{range[0]}–{range[1]} / {total} TOTAL</span>
                    ),
                    size: 'small',
                  }}
                  onRow={row => ({
                    onClick: () => enterFocusMode(row.id),
                    className: `cursor-pointer transition-all duration-200 group ${tableRowDensityClass} ${
                      selectedCandidateId === row.id
                        ? 'bg-indigo-50/80 !border-l-4 !border-l-indigo-600 shadow-sm'
                        : 'hover:bg-slate-50 border-l-4 border-l-transparent'
                    }`,
                  })}
                  locale={{
                    emptyText: (
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description={
                          <div className="text-center p-8">
                            <Database size={32} className={`mx-auto mb-4 ${dbQ.isError ? 'text-amber-300' : 'text-slate-200'}`} />
                            <p className="text-slate-900 font-black uppercase tracking-widest">
                              {dbQ.isError ? 'Candidate database unavailable' : 'No candidates matching search criteria'}
                            </p>
                            <p className="text-slate-400 text-xs mt-2 uppercase font-bold">
                              {dbQ.isError ? 'Server error from /candidates/database/. try refresh after backend fix.' : 'Try adjusting filters or using semantic AI search'}
                            </p>
                          </div>
                        }
                      />
                    ),
                  }}
                />
              </div>
            </div>
          </>
        )}
      </div>

      <AddCandidateWorkflowModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        sourceSurface="database"
        onCompleted={() => {
          queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })
          queryClient.invalidateQueries({ queryKey: ['candidate-list'] })
        }}
      />

      {/* ── Add to Pool Modal ──────────────────────────────────────────────── */}
      <Modal
        open={addToPoolOpen}
        onCancel={() => { setAddToPoolOpen(false); setPoolTargetId(null) }}
        title="Add to Talent Pool"
        footer={null}
        width={440}
      >
        <div className="space-y-2 pt-2">
          {poolsQ.isLoading ? (
            <Spin />
          ) : (poolsQ.data || []).length === 0 ? (
            <Empty description="No talent pools yet" />
          ) : (
            (poolsQ.data || []).map((pool: any) => (
              <button
                key={pool.id}
                onClick={() => {
                  const cid = poolTargetId || (selectedRowKeys.length > 0 ? null : selectedCandidateId)
                  if (cid) {
                    handleAddToPool(cid, pool.id)
                  } else {
                    // Bulk add
                    talentPoolsApi.bulkAdd(pool.id, { candidate_ids: selectedRowKeys }).catch(() => null).then(() => Promise.resolve())
                      .then(() => { message.success(`${selectedRowKeys.length} added to pool`); setAddToPoolOpen(false) })
                  }
                }}
                className="flex w-full items-center gap-3 rounded-xl border border-slate-200 px-4 py-3 text-left hover:border-indigo-200 hover:bg-indigo-50 transition"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100">
                  <Users size={14} className="text-indigo-600" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-800">{pool.name}</div>
                  <div className="text-xs text-slate-500">{pool.candidate_count ?? 0} candidates</div>
                </div>
              </button>
            ))
          )}
        </div>
      </Modal>

      {/* ── Submit to Job Modal ────────────────────────────────────────────── */}
      <Modal
        open={submitToJobOpen}
        onCancel={() => { setSubmitToJobOpen(false); setSubmitTargetId(null); setSelectedJobId(null) }}
        onOk={() => {
          if (submitTargetId && selectedJobId) handleSubmitToJob(submitTargetId, selectedJobId)
        }}
        okButtonProps={{ disabled: !selectedJobId }}
        okText="Submit to Job"
        title="Match to Job"
        width={480}
      >
        <div className="pt-2 space-y-3">
          {submitTargetCandidate?.is_agency_protected && (
            <div className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-3">
              <div className="flex items-start gap-2">
                <ShieldCheck size={15} className="mt-0.5 shrink-0 text-violet-600" />
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-violet-700">Agency Protected</p>
                  <p className="mt-1 text-xs font-semibold text-slate-700">
                    Protected Until: {formatProtectionDate(submitTargetCandidate.protected_until)}
                  </p>
                  <p className="text-xs font-semibold text-slate-700">
                    Scope: {protectionScopeLabel(submitTargetCandidate.protection_scope)}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">
                    Candidate cannot be reused outside the agreed scope during the protection period. Unsupported job submissions will be blocked by the backend.
                  </p>
                </div>
              </div>
            </div>
          )}
          <p className="text-xs text-slate-500">Select a job to submit this candidate against:</p>
          {jobsQ.isLoading ? <Spin /> : (
            <Select
              style={{ width: '100%' }}
              placeholder="Select job..."
              value={selectedJobId}
              onChange={setSelectedJobId}
              options={(jobsQ.data || []).map((j: any) => ({
                value: j.id,
                label: `${j.title}${j.department ? ` · ${j.department}` : ''}`,
              }))}
              showSearch
              filterOption={(input, option) =>
                String(option?.label || '').toLowerCase().includes(input.toLowerCase())
              }
            />
          )}
        </div>
      </Modal>

      {/* ── Column Config Modal ───────────────────────────────────────────── */}
      <Modal
        open={colConfigOpen}
        onCancel={() => setColConfigOpen(false)}
        title="Configure Columns"
        footer={<button onClick={() => setColConfigOpen(false)} className="rounded-lg bg-slate-800 px-4 py-1.5 text-sm font-semibold text-white hover:bg-slate-700">Done</button>}
        width={400}
      >
        <div className="grid grid-cols-2 gap-2 pt-2">
          {ALL_COLUMNS.map(col => (
            <label
              key={col.key}
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition ${
                col.fixed ? 'opacity-50 cursor-not-allowed border-slate-100 bg-slate-50' :
                visibleCols.includes(col.key) ? 'border-indigo-200 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Checkbox
                checked={col.fixed || visibleCols.includes(col.key)}
                disabled={!!col.fixed}
                onChange={() => !col.fixed && handleColToggle(col.key)}
              />
              <span className="text-xs font-medium text-slate-700">{col.label}</span>
            </label>
          ))}
        </div>
      </Modal>
    </div>
  )
}
