import React, { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar, Button, Checkbox, Dropdown, Empty, Form, Input,
  Modal, Select, Spin, Tooltip, message, Table, Tag,
} from 'antd'
import type { ColumnsType, TableRowSelection } from 'antd/es/table/interface'
import {
  Activity, AlertTriangle, BadgeCheck, Bot, Briefcase,
  ChevronDown, Clock3, Copy, Database, Download, ExternalLink,
  Filter, MapPin, MoreHorizontal, Plus, RefreshCw, Search,
  Settings2, Sparkles, Target, Trash2, User,
  Users, XCircle, Zap, BookOpen,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { talentPoolsApi } from '@/api/talentPools'
import { requisitionsApi } from '@/api/jobs'
import http from '@/utils/http'
import type { CandidateSmartRow, CandidateCommandCenter as CCData } from '@/types'
import { usePermission } from '@/hooks/usePermission'

dayjs.extend(relativeTime)

// ── Constants ─────────────────────────────────────────────────────────────────

const SEARCH_MODES = [
  { key: 'all', label: 'All Candidates' },
  { key: 'search', label: 'Search' },
  { key: 'match_job', label: 'Match to Job' },
  { key: 'duplicates', label: 'Duplicates' },
  { key: 'needs_review', label: 'Needs Review' },
] as const

type SearchMode = typeof SEARCH_MODES[number]['key']

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
  'candidate', 'experience', 'location', 'skills',
  'owner', 'last_activity', 'readiness', 'fit', 'source',
  'engagements', 'passport', 'actions',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function avatarColor(name: string) {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#14b8a6', '#3b82f6']
  return colors[(name?.charCodeAt(0) || 0) % colors.length]
}

function scoreColor(score: number | null | undefined): { bg: string; color: string } {
  if (score == null) return { bg: '#f1f5f9', color: '#94a3b8' }
  if (score >= 75) return { bg: '#f0fdf4', color: '#15803d' }
  if (score >= 50) return { bg: '#fefce8', color: '#b45309' }
  return { bg: '#fef2f2', color: '#dc2626' }
}

function noticePeriodLabel(days?: number | null) {
  if (!days) return 'Immediate'
  if (days <= 15) return '≤ 15 days'
  if (days <= 30) return '1 month'
  if (days <= 60) return '2 months'
  return `${days}d`
}

function mapCandidateListItemToSmartRow(candidate: any): CandidateSmartRow {
  const firstName = candidate?.first_name || ''
  const lastName = candidate?.last_name || ''
  const fullName = `${firstName} ${lastName}`.trim() || candidate?.full_name || 'Unnamed Candidate'
  return {
    id: String(candidate?.id || ''),
    name: fullName,
    current_title: candidate?.current_title || '',
    company: candidate?.current_company || '',
    experience: candidate?.experience_years != null ? Number(candidate.experience_years) : null,
    location: [candidate?.current_location_city, candidate?.current_location_country].filter(Boolean).join(', '),
    source: candidate?.source || candidate?.source_type || '',
    source_type: candidate?.source_type || '',
    owner: candidate?.owner_user_id || null,
    owner_name: null,
    last_touch: candidate?.last_contact_at || null,
    last_activity: candidate?.last_activity_at || candidate?.updated_at || null,
    signals: {
      readiness_score: candidate?.readiness_score ?? null,
      fit_score: candidate?.fit_score ?? null,
      warning_signals: [],
    },
    job_engagement_summary: {},
    skills: candidate?.skills || [],
    passport_linked: Boolean(candidate?.passport_linked || candidate?.passport_id),
    is_duplicate: Boolean(candidate?.is_duplicate || candidate?.duplicate_of),
    notice_period_days: candidate?.notice_period_days ?? null,
    availability_status: candidate?.availability_status ?? null,
    open_engagements: 0,
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
    return v !== '' && v !== null
  }).length

  return (
    <div className="flex flex-col overflow-hidden bg-white">
      {/* Rail header */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Filter size={13} className="text-slate-500" />
          <span className="text-xs font-bold text-slate-700">Filters</span>
          {activeCount > 0 && (
            <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
              {activeCount}
            </span>
          )}
        </div>
        {activeCount > 0 && (
          <button onClick={onClear} className="text-[11px] text-indigo-500 hover:text-indigo-700 font-medium">
            Clear all
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        <FilterSection title="Skills">
          <Input
            size="small"
            placeholder="e.g. Python, React..."
            value={filters.skills}
            onChange={e => onChange({ skills: e.target.value })}
            allowClear
          />
        </FilterSection>

        <FilterSection title="Experience">
          <div className="flex items-center gap-2">
            <Input
              size="small"
              type="number"
              min={0}
              placeholder="Min yrs"
              value={filters.experience_min}
              onChange={e => onChange({ experience_min: e.target.value })}
              style={{ width: 80 }}
            />
            <span className="text-slate-400 text-xs">to</span>
            <Input
              size="small"
              type="number"
              min={0}
              placeholder="Max yrs"
              value={filters.experience_max}
              onChange={e => onChange({ experience_max: e.target.value })}
              style={{ width: 80 }}
            />
          </div>
        </FilterSection>

        <FilterSection title="Location">
          <Input
            size="small"
            placeholder="City or country..."
            value={filters.location}
            onChange={e => onChange({ location: e.target.value })}
            allowClear
            prefix={<MapPin size={11} className="text-slate-400" />}
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
      </div>
    </div>
  )
}

// ── ContextPanel ──────────────────────────────────────────────────────────────

function ContextPanel({
  candidateId,
  row,
  onClose,
  onAddToActive,
  onAddToPool,
  onSubmitToJob,
}: {
  candidateId: string
  row: CandidateSmartRow
  onClose: () => void
  onAddToActive: () => void
  onAddToPool: () => void
  onSubmitToJob: () => void
}) {
  const commandQ = useQuery({
    queryKey: ['candidate-command-center', candidateId],
    queryFn: async () => (await candidatesApi.commandCenter(candidateId)).data.data,
    enabled: !!candidateId,
  })
  const cc = commandQ.data as CCData | null
  const { bg: rBg, color: rColor } = scoreColor(row.signals?.readiness_score)
  const { bg: fBg, color: fColor } = scoreColor(row.signals?.fit_score)
  const warnings = row.signals?.warning_signals || []

  return (
    <div className="flex w-[300px] flex-none flex-col border-l border-slate-200 bg-white overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 bg-slate-50">
        <div className="flex items-center gap-2">
          <Bot size={13} className="text-indigo-500" />
          <span className="text-xs font-bold text-slate-700">Candidate Brief</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <XCircle size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Identity block */}
        <div className="px-4 py-4 border-b border-slate-100">
          <div className="flex items-start gap-3">
            <Avatar
              size={42}
              style={{ backgroundColor: avatarColor(row.name), flexShrink: 0 }}
              className="font-bold text-white text-sm"
            >
              {(row.name || '?').charAt(0)}
            </Avatar>
            <div className="min-w-0">
              <div className="font-bold text-sm text-slate-900 truncate">{row.name}</div>
              <div className="text-xs text-slate-500 truncate">{row.current_title || '—'}</div>
              <div className="text-xs text-slate-400 mt-0.5">{row.company || ''}</div>
            </div>
          </div>
          {/* Meta row */}
          <div className="mt-3 flex flex-wrap gap-2">
            {row.location && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500">
                <MapPin size={10} />{row.location}
              </span>
            )}
            {row.experience != null && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500">
                <Briefcase size={10} />{row.experience}yr exp
              </span>
            )}
            {row.notice_period_days != null && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500">
                <Clock3 size={10} />{noticePeriodLabel(row.notice_period_days)}
              </span>
            )}
          </div>
        </div>

        {/* AI Scores */}
        <div className="px-4 py-3 border-b border-slate-100">
          <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 mb-2">AI Signals</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg p-2.5" style={{ backgroundColor: rBg }}>
              <div className="text-[10px] font-medium" style={{ color: rColor }}>Readiness</div>
              <div className="text-lg font-black mt-0.5" style={{ color: rColor }}>
                {row.signals?.readiness_score ?? '—'}
              </div>
            </div>
            <div className="rounded-lg p-2.5" style={{ backgroundColor: fBg }}>
              <div className="text-[10px] font-medium" style={{ color: fColor }}>Fit Score</div>
              <div className="text-lg font-black mt-0.5" style={{ color: fColor }}>
                {row.signals?.fit_score ?? '—'}
              </div>
            </div>
          </div>
          {warnings.length > 0 && (
            <div className="mt-2 space-y-1">
              {warnings.slice(0, 3).map((w, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[11px] text-amber-700">
                  <AlertTriangle size={10} className="shrink-0" />{w}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Skills */}
        {(row.skills || []).length > 0 && (
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 mb-2">Skills</p>
            <div className="flex flex-wrap gap-1">
              {(row.skills || []).map((s, i) => (
                <span key={i} className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700 font-medium">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Engagements summary */}
        {Object.keys(row.job_engagement_summary || {}).length > 0 && (
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 mb-2">Active Engagements</p>
            <div className="space-y-1">
              {Object.entries(row.job_engagement_summary || {}).map(([stage, count]) => (
                <div key={stage} className="flex items-center justify-between text-xs">
                  <span className="text-slate-600 capitalize">{stage.replace(/_/g, ' ')}</span>
                  <span className="font-semibold text-slate-800">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI summary from command center */}
        {commandQ.isLoading && (
          <div className="flex items-center justify-center py-4">
            <Spin size="small" />
          </div>
        )}
        {(cc as any)?.summary && (
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 mb-2">AI Summary</p>
            <p className="text-[11px] text-slate-600 leading-relaxed">{(cc as any).summary}</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex-none border-t border-slate-200 p-3 space-y-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 mb-1">Quick Actions</p>
        <button
          onClick={onAddToActive}
          className="flex w-full items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700 transition"
        >
          <Zap size={12} /> Add to Active Work
        </button>
        <button
          onClick={onSubmitToJob}
          className="flex w-full items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
        >
          <Target size={12} /> Match to Job
        </button>
        <button
          onClick={onAddToPool}
          className="flex w-full items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
        >
          <Users size={12} /> Add to Pool
        </button>
        <a
          href={`/candidates/${candidateId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-full items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
        >
          <ExternalLink size={12} /> Full Profile
        </a>
      </div>
    </div>
  )
}

// ── BulkActionsBar ────────────────────────────────────────────────────────────

function BulkActionsBar({
  count, onClear, onAddToActive, onAddToPool, onExport, onArchive, onAssign,
}: {
  count: number
  onClear: () => void
  onAddToActive: () => void
  onAddToPool: () => void
  onExport: () => void
  onArchive: () => void
  onAssign: () => void
}) {
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
      <button
        onClick={onExport}
        className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-white px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 transition"
      >
        <Download size={11} /> Export
      </button>
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
  { key: 'experience', label: 'Experience' },
  { key: 'location', label: 'Location' },
  { key: 'skills', label: 'Skills Snapshot' },
  { key: 'owner', label: 'Owner' },
  { key: 'last_activity', label: 'Last Activity' },
  { key: 'readiness', label: 'Readiness Score' },
  { key: 'fit', label: 'AI Fit Score' },
  { key: 'source', label: 'Source' },
  { key: 'engagements', label: 'Open Engagements' },
  { key: 'passport', label: 'Passport' },
  { key: 'notice', label: 'Notice Period' },
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
  const [filterRailOpen, setFilterRailOpen] = useState(true)
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [savedSearchOpen, setSavedSearchOpen] = useState(false)
  const [colConfigOpen, setColConfigOpen] = useState(false)
  const [visibleCols, setVisibleCols] = useState<string[]>(DEFAULT_VISIBLE_COLS)
  const [addOpen, setAddOpen] = useState(false)
  const [addForm] = Form.useForm()
  const [addToPoolOpen, setAddToPoolOpen] = useState(false)
  const [poolTargetId, setPoolTargetId] = useState<string | null>(null)
  const [submitToJobOpen, setSubmitToJobOpen] = useState(false)
  const [submitTargetId, setSubmitTargetId] = useState<string | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [sortField, setSortField] = useState<string>('last_activity')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

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
    limit: 200,
  }), [apiView, searchText, filters.source_type, filters.owner, filters.passport_linked, filters.has_duplicates, searchMode])

  // ── Queries ────────────────────────────────────────────────────────────
  const dbQ = useQuery({
    queryKey: ['candidate-database-v2', apiParams],
    queryFn: async () => {
      const response = await candidatesApi.database(apiParams)
      const requestUrl = `${response.config.baseURL || ''}${response.config.url || ''}`
      const requestParams = response.config.params || {}
      const payload = response.data?.data

      console.debug('[CandidateDatabase] request URL:', requestUrl)
      console.debug('[CandidateDatabase] query params:', requestParams)
      console.debug('[CandidateDatabase] response payload:', payload)

      return payload
    },
    staleTime: 30_000,
  })

  const fallbackListQ = useQuery({
    queryKey: ['candidate-list-fallback-v1', { search: searchText || '' }],
    queryFn: async () => (await candidatesApi.list({ search: searchText || undefined })).data.data,
    enabled: dbQ.isError || (
      dbQ.isSuccess &&
      (
        (Array.isArray((dbQ.data as any)?.items) && (dbQ.data as any).items.length === 0) ||
        (Array.isArray((dbQ.data as any)?.results) && (dbQ.data as any).results.length === 0) ||
        (Array.isArray((dbQ.data as any)?.candidates) && (dbQ.data as any).candidates.length === 0)
      )
    ),
    staleTime: 30_000,
  })

  const apiRows = useMemo((): CandidateSmartRow[] => {
    const payload: any = dbQ.data
    if (!payload) return []
    if (Array.isArray(payload.items)) return payload.items
    if (Array.isArray(payload.results)) return payload.results
    if (Array.isArray(payload.candidates)) return payload.candidates.map(mapCandidateListItemToSmartRow)
    return []
  }, [dbQ.data])

  const fallbackRows = useMemo((): CandidateSmartRow[] => {
    const candidates = (fallbackListQ.data as any)?.candidates
    if (!Array.isArray(candidates)) return []
    return candidates.map(mapCandidateListItemToSmartRow)
  }, [fallbackListQ.data])

  const sourceRows = apiRows.length > 0 ? apiRows : fallbackRows

  useEffect(() => {
    setCurrentPage(1)
  }, [searchMode, searchText, filters, pageSize])

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
    () => filteredRows.find(r => r.id === selectedCandidateId) || null,
    [filteredRows, selectedCandidateId],
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
    } catch {
      message.error('Failed to submit to job')
    }
  }

  const createCandidate = useMutation({
    mutationFn: (payload: any) => candidatesApi.create(payload),
    onSuccess: () => {
      message.success('Candidate added')
      setAddOpen(false)
      addForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['candidate-database-v2'] })
    },
    onError: (err: any) => message.error(err?.response?.data?.message || 'Failed to add candidate'),
  })

  const submitAddCandidate = async () => {
    const v = await addForm.validateFields()
    createCandidate.mutate({
      first_name: v.first_name, last_name: v.last_name,
      email: v.email || '', phone: v.phone || '',
      current_title: v.current_title || '', current_company: v.current_company || '',
      experience_years: v.experience_years, current_location_city: v.location || '',
      source: v.source || 'company', entry_method: 'quick_add',
    })
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

  const tableColumns = useMemo((): ColumnsType<CandidateSmartRow> => {
    const allCols: ColumnsType<CandidateSmartRow> = [
      {
        key: 'candidate',
        title: makeHeader('name', 'Candidate'),
        width: 220,
        fixed: 'left' as const,
        render: (_, row) => (
          <div className="flex items-center gap-2.5 min-w-0">
            <Avatar
              size={28}
              style={{ backgroundColor: avatarColor(row.name), flexShrink: 0 }}
              className="font-bold text-white text-xs"
            >
              {(row.name || '?').charAt(0)}
            </Avatar>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-slate-900 truncate leading-tight">{row.name}</div>
              <div className="text-[11px] text-slate-500 truncate leading-tight">{row.current_title || <span className="text-slate-300">No title</span>}</div>
            </div>
            {row.is_duplicate && (
              <Tooltip title="Duplicate risk">
                <Copy size={11} className="shrink-0 text-amber-500" />
              </Tooltip>
            )}
          </div>
        ),
      },
      {
        key: 'experience',
        title: makeHeader('experience', 'Exp'),
        width: 70,
        render: (_, row) => (
          <span className="text-xs text-slate-700">{row.experience != null ? `${row.experience}yr` : '—'}</span>
        ),
      },
      {
        key: 'location',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Location</span>,
        width: 130,
        render: (_, row) => (
          <div className="flex items-center gap-1 text-xs text-slate-600 truncate">
            {row.location ? <><MapPin size={10} className="shrink-0 text-slate-400" />{row.location}</> : '—'}
          </div>
        ),
      },
      {
        key: 'skills',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Skills</span>,
        width: 200,
        render: (_, row) => {
          const skills = row.skills || []
          if (!skills.length) return <span className="text-slate-300 text-xs">—</span>
          return (
            <div className="flex flex-wrap gap-1">
              {skills.slice(0, 3).map((s, i) => (
                <span key={i} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600 font-medium">
                  {s}
                </span>
              ))}
              {skills.length > 3 && (
                <span className="text-[10px] text-slate-400">+{skills.length - 3}</span>
              )}
            </div>
          )
        },
      },
      {
        key: 'owner',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Owner</span>,
        width: 110,
        render: (_, row) => (
          <span className="text-xs text-slate-600 truncate">
            {(row as any).owner_name || (row.owner ? '—' : <span className="text-slate-300">Unassigned</span>)}
          </span>
        ),
      },
      {
        key: 'last_activity',
        title: makeHeader('last_activity', 'Last Activity'),
        width: 110,
        render: (_, row) => {
          const la = row.last_activity || row.last_touch
          return (
            <span className="text-[11px] text-slate-500">
              {la ? dayjs(la).fromNow() : '—'}
            </span>
          )
        },
      },
      {
        key: 'readiness',
        title: makeHeader('readiness', 'Readiness'),
        width: 85,
        align: 'center' as const,
        render: (_, row) => (
          <ScoreChip
            score={row.signals?.readiness_score}
            label="Readiness"
            explanation="Measures how ready the candidate is to be placed based on profile completeness and engagement history."
          />
        ),
      },
      {
        key: 'fit',
        title: makeHeader('fit', 'Fit'),
        width: 75,
        align: 'center' as const,
        render: (_, row) => (
          <ScoreChip
            score={row.signals?.fit_score}
            label="AI Fit Score"
            explanation="AI-computed match score based on skills, experience, and job requirements."
          />
        ),
      },
      {
        key: 'source',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Source</span>,
        width: 100,
        render: (_, row) => (
          <span className="text-[11px] text-slate-500 capitalize">
            {row.source_type || row.source || '—'}
          </span>
        ),
      },
      {
        key: 'engagements',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Engagements</span>,
        width: 100,
        align: 'center' as const,
        render: (_, row) => {
          const count = (row as any).open_engagements || Object.values(row.job_engagement_summary || {}).reduce((a: number, b: number) => a + b, 0)
          return count > 0 ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-bold text-indigo-600">
              <Activity size={9} />{count}
            </span>
          ) : (
            <span className="text-slate-300 text-[11px]">—</span>
          )
        },
      },
      {
        key: 'passport',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Passport</span>,
        width: 80,
        align: 'center' as const,
        render: (_, row) => (
          row.passport_linked ? (
            <Tooltip title="Passport linked">
              <BadgeCheck size={15} className="text-green-500 mx-auto" />
            </Tooltip>
          ) : (
            <span className="text-slate-200 text-[11px]">—</span>
          )
        ),
      },
      {
        key: 'notice',
        title: <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-[0.08em]">Notice</span>,
        width: 90,
        render: (_, row) => (
          <span className="text-[11px] text-slate-500">
            {noticePeriodLabel(row.notice_period_days)}
          </span>
        ),
      },
      {
        key: 'actions',
        title: '',
        width: 50,
        fixed: 'right' as const,
        render: (_, row) => (
          <Dropdown
            trigger={['click']}
            menu={{
              items: [
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
                { type: 'divider' },
                {
                  key: 'profile',
                  icon: <ExternalLink size={12} />,
                  label: 'View Full Profile',
                  onClick: () => window.open(`/candidates/${row.id}`, '_blank'),
                },
              ],
            }}
          >
            <button className="flex items-center justify-center rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition">
              <MoreHorizontal size={14} />
            </button>
          </Dropdown>
        ),
      },
    ]
    return allCols.filter(c => {
      const colKey = c.key as string
      const colDef = ALL_COLUMNS.find(a => a.key === colKey)
      if (colDef?.fixed) return true
      return visibleCols.includes(colKey)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleCols, sortField, sortDir])

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
    return v !== '' && v !== null
  }).length

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
        {/* Main search input */}
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 focus-within:border-indigo-300 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100 transition">
          <Search size={14} className="shrink-0 text-slate-400" />
          <input
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            placeholder="Search candidates by name, title, company, skills..."
            className="flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder-slate-400"
          />
          {searchText && (
            <button onClick={() => setSearchText('')} className="text-slate-400 hover:text-slate-600">
              <XCircle size={14} />
            </button>
          )}
        </div>

        {/* Search type toggle */}
        <div className="flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-100 p-0.5">
          {(['keyword', 'semantic'] as const).map(type => (
            <button
              key={type}
              onClick={() => setSearchInputType(type)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition capitalize ${
                searchInputType === type
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {type === 'keyword' ? 'Keyword' : <span className="flex items-center gap-1"><Bot size={10} />Semantic</span>}
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
          <button className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
            <BookOpen size={12} /> Saved <ChevronDown size={11} />
          </button>
        </Dropdown>

        {/* Filter toggle */}
        <button
          onClick={() => setFilterRailOpen(v => !v)}
          className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
            filterRailOpen
              ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
              : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Filter size={12} />
          Filters
          {activeFilterCount > 0 && (
            <span className="rounded-full bg-indigo-600 px-1.5 text-[10px] font-bold text-white">{activeFilterCount}</span>
          )}
        </button>
      </div>

      {/* ── Mode Tabs ════════════════════════════════════════════════════════ */}
      <div className="flex h-9 flex-none items-center gap-1 border-b border-slate-100 bg-white px-5">
        {SEARCH_MODES.map(mode => (
          <button
            key={mode.key}
            onClick={() => setSearchMode(mode.key)}
            className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
              searchMode === mode.key
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            {mode.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[11px] text-slate-400">
            {dbQ.isLoading ? 'Loading...' : `${filteredRows.length} candidates`}
          </span>
        </div>
      </div>

      {/* ── Body: Filter Rail + Table + Context Panel ════════════════════════ */}
      <div className="flex flex-1 overflow-hidden">

        {/* Zone B: Left Filter Rail */}
        {filterRailOpen && (
          <div className="flex w-[220px] flex-none flex-col overflow-hidden border-r border-slate-200">
            <FilterRail
              filters={filters}
              onChange={partial => setFilters(prev => ({ ...prev, ...partial }))}
              onClear={() => setFilters(EMPTY_FILTERS)}
              memberOptions={[]}
            />
          </div>
        )}

        {/* Zone C: Center Results Table */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-none border-b border-slate-100 bg-slate-50 px-4 py-2 text-[11px] text-slate-600">
            <span className="font-semibold">Debug:</span>{' '}
            total returned={sourceRows.length}
            {' · '}
            first 3={sourceRows.slice(0, 3).map(r => r.name || r.id).join(', ') || 'none'}
          </div>

          {/* Bulk actions bar */}
          {selectedRowKeys.length > 0 && (
            <div className="flex-none px-4 py-2 bg-white border-b border-slate-100">
              <BulkActionsBar
                count={selectedRowKeys.length}
                onClear={() => setSelectedRowKeys([])}
                onAddToActive={handleBulkAddToActive}
                onAddToPool={() => { setAddToPoolOpen(true) }}
                onExport={() => message.info('Export coming soon')}
                onArchive={() => message.info('Archive coming soon')}
                onAssign={() => message.info('Assign owner coming soon')}
              />
            </div>
          )}

          <div className="flex-1 overflow-auto">
            <Table<CandidateSmartRow>
              dataSource={filteredRows}
              columns={tableColumns}
              rowKey="id"
              rowSelection={rowSelection}
              size="small"
              loading={dbQ.isLoading}
              scroll={{ x: 1000, y: 'calc(100vh - 280px)' }}
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
                  <span className="text-[11px] text-slate-500">{range[0]}–{range[1]} of {total}</span>
                ),
                size: 'small',
              }}
              sticky
              onRow={row => ({
                onClick: () => {
                  if (selectedCandidateId === row.id) {
                    setSelectedCandidateId(null)
                  } else {
                    setSelectedCandidateId(row.id)
                  }
                },
                className: `cursor-pointer transition-colors ${
                  selectedCandidateId === row.id ? 'bg-indigo-50' : 'hover:bg-slate-50'
                }`,
              })}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <div className="text-center">
                        <p className="text-slate-600 font-medium">No candidates found</p>
                        <p className="text-slate-400 text-xs mt-1">Adjust your search or filters</p>
                      </div>
                    }
                  />
                ),
              }}
            />
          </div>
        </div>

        {/* Zone D: Right Context Panel */}
        {selectedCandidateId && selectedRow && (
          <ContextPanel
            candidateId={selectedCandidateId}
            row={selectedRow}
            onClose={() => setSelectedCandidateId(null)}
            onAddToActive={() => handleAddToActive(selectedCandidateId)}
            onAddToPool={() => { setPoolTargetId(selectedCandidateId); setAddToPoolOpen(true) }}
            onSubmitToJob={() => { setSubmitTargetId(selectedCandidateId); setSubmitToJobOpen(true) }}
          />
        )}
      </div>

      {/* ── Add Candidate Modal ──────────────────────────────────────────── */}
      <Modal
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        onOk={submitAddCandidate}
        okText="Add Candidate"
        title="Add Candidate"
        confirmLoading={createCandidate.isPending}
        width={640}
      >
        <Form layout="vertical" form={addForm} className="pt-2">
          <div className="grid grid-cols-2 gap-3">
            <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="email" label="Email"><Input /></Form.Item>
            <Form.Item name="phone" label="Phone"><Input /></Form.Item>
            <Form.Item name="current_title" label="Current Title"><Input /></Form.Item>
            <Form.Item name="current_company" label="Company"><Input /></Form.Item>
            <Form.Item name="experience_years" label="Experience (yrs)"><Input type="number" min={0} /></Form.Item>
            <Form.Item name="location" label="Location"><Input /></Form.Item>
          </div>
        </Form>
      </Modal>

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
