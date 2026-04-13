import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Tag, Typography, Spin, Button } from 'antd'
import {
  SyncOutlined, ArrowRightOutlined, SolutionOutlined,
  CalendarOutlined, ClockCircleOutlined, DollarCircleOutlined,
  CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined,
  TrophyOutlined, RightOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { candidateApi } from '@/api/candidate'
import { useDrawerStore } from '@/store/drawerStore'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text, Paragraph } = Typography

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_MAP: Record<string, {
  label: string; color: string; step: number
  bg: string; text: string; dot: string
  terminal?: boolean; terminalType?: 'positive' | 'negative' | 'neutral'
}> = {
  applied:             { label: 'Applied',        color: 'blue',     step: 0, bg: 'bg-blue-50',    text: 'text-blue-700',    dot: 'bg-blue-500'    },
  sourcing:            { label: 'Under Review',   color: 'default',  step: 0, bg: 'bg-slate-100',  text: 'text-slate-600',   dot: 'bg-slate-400'   },
  screening:           { label: 'Screening',      color: 'cyan',     step: 1, bg: 'bg-cyan-50',    text: 'text-cyan-700',    dot: 'bg-cyan-500'    },
  shortlisted:         { label: 'Shortlisted',    color: 'geekblue', step: 2, bg: 'bg-indigo-50',  text: 'text-indigo-700',  dot: 'bg-indigo-500'  },
  in_review:           { label: 'In Review',      color: 'orange',   step: 2, bg: 'bg-orange-50',  text: 'text-orange-700',  dot: 'bg-orange-500'  },
  interview:           { label: 'Interview',      color: 'purple',   step: 3, bg: 'bg-purple-50',  text: 'text-purple-700',  dot: 'bg-purple-500'  },
  interview_scheduled: { label: 'Interview',      color: 'purple',   step: 3, bg: 'bg-purple-50',  text: 'text-purple-700',  dot: 'bg-purple-500'  },
  assessment:          { label: 'Assessment',     color: 'purple',   step: 3, bg: 'bg-violet-50',  text: 'text-violet-700',  dot: 'bg-violet-500'  },
  on_hold:             { label: 'On Hold',        color: 'default',  step: 2, bg: 'bg-slate-100',  text: 'text-slate-600',   dot: 'bg-slate-400',  terminal: true, terminalType: 'neutral'  },
  offer:               { label: 'Offer Received', color: 'gold',     step: 4, bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-500'   },
  offer_extended:      { label: 'Offer Received', color: 'gold',     step: 4, bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-500'   },
  offer_accepted:      { label: 'Offer Accepted', color: 'green',    step: 4, bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', terminal: true, terminalType: 'positive' },
  joined:              { label: 'Joined',         color: 'success',  step: 5, bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-600', terminal: true, terminalType: 'positive' },
  placement_confirmed: { label: 'Confirmed',      color: 'success',  step: 5, bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-600', terminal: true, terminalType: 'positive' },
  placement_cancelled: { label: 'Cancelled',      color: 'red',      step: -1, bg: 'bg-rose-50',   text: 'text-rose-700',    dot: 'bg-rose-500',   terminal: true, terminalType: 'negative' },
  rejected:            { label: 'Not Selected',   color: 'red',      step: -1, bg: 'bg-rose-50',   text: 'text-rose-700',    dot: 'bg-rose-500',   terminal: true, terminalType: 'negative' },
  withdrawn:           { label: 'Withdrawn',      color: 'default',  step: -1, bg: 'bg-slate-100', text: 'text-slate-600',   dot: 'bg-slate-400',  terminal: true, terminalType: 'neutral'  },
}

const PIPELINE_STEPS = ['Applied', 'Screening', 'Shortlisted', 'Interview', 'Offer', 'Joined']

// ─── Pipeline bar ─────────────────────────────────────────────────────────────

function PipelineBar({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {PIPELINE_STEPS.map((label, i) => (
        <div key={label} className="flex items-center gap-0.5 flex-1 min-w-0">
          <div className={cn(
            'h-1 flex-1 rounded-full transition-all',
            i <= step ? 'bg-blue-500' : 'bg-slate-200'
          )} />
          {i < PIPELINE_STEPS.length - 1 && (
            <div className={cn('h-1 w-1 rounded-full shrink-0', i < step ? 'bg-blue-500' : 'bg-slate-200')} />
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Application card ─────────────────────────────────────────────────────────

function ApplicationCard({ app, onClick }: { app: any; onClick: () => void }) {
  const st = STATUS_MAP[app.status] ?? {
    label: (app.status ?? '').replace(/_/g, ' '), color: 'default', step: 0,
    bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400',
  }

  const lastActivity = app.updated_at ?? app.created_at
  const isTerminal = st.terminal
  const isPositive = st.terminalType === 'positive'
  const isNegative = st.terminalType === 'negative'

  const hasOffer = ['offer_extended', 'offer_accepted', 'joined', 'placement_confirmed'].includes(app.status)
    && app.offer_amount

  return (
    <div
      onClick={onClick}
      className={cn(
        'group flex flex-col gap-4 rounded-2xl border p-5 cursor-pointer transition-all hover:shadow-md',
        isPositive ? 'bg-emerald-50/40 border-emerald-200 hover:border-emerald-300'
        : isNegative ? 'bg-rose-50/30 border-rose-100 hover:border-rose-200'
        : isTerminal ? 'bg-slate-50 border-slate-200 hover:border-slate-300'
        : 'bg-white border-slate-200 hover:border-blue-200 hover:bg-blue-50/20'
      )}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          {/* Icon */}
          <div className={cn(
            'h-11 w-11 rounded-xl flex items-center justify-center shrink-0 border',
            isPositive ? 'bg-emerald-100 border-emerald-200'
            : isNegative ? 'bg-rose-100 border-rose-100'
            : 'bg-blue-50 border-blue-100'
          )}>
            {isPositive
              ? <TrophyOutlined style={{ fontSize: 20, color: '#059669' }} />
              : isNegative
                ? <CloseCircleOutlined style={{ fontSize: 20, color: '#e11d48' }} />
                : <SolutionOutlined style={{ fontSize: 20, color: '#2563eb' }} />
            }
          </div>

          {/* Title + tags */}
          <div className="min-w-0">
            <div className="text-base font-black text-slate-900 leading-snug truncate">
              {app.job_title || app.jobTitle || 'Position'}
            </div>
            <div className="flex items-center gap-1.5 mt-1 flex-wrap">
              {app.jobType && (
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                  {app.jobType.replace(/_/g, ' ')}
                </span>
              )}
              {app.workMode && (
                <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  {app.workMode.replace(/_/g, ' ')}
                </span>
              )}
              {app.salaryVisible && app.salaryMin && (
                <span className="text-[10px] font-black text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                  <DollarCircleOutlined style={{ fontSize: 9 }} />
                  {app.salaryCurrency} {Number(app.salaryMin).toLocaleString()}
                  {app.salaryMax ? `–${Number(app.salaryMax).toLocaleString()}` : '+'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Status badge + chevron */}
        <div className="flex items-center gap-2 shrink-0">
          <span className={cn(
            'text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full border',
            st.bg, st.text,
            isPositive ? 'border-emerald-200'
            : isNegative ? 'border-rose-200'
            : isTerminal ? 'border-slate-200'
            : 'border-blue-200'
          )}>
            {st.label}
          </span>
          <RightOutlined className="text-slate-300 group-hover:text-slate-500 transition-colors" style={{ fontSize: 10 }} />
        </div>
      </div>

      {/* ── Pipeline bar — only for active applications ─────────────── */}
      {!isTerminal && st.step >= 0 && (
        <PipelineBar step={st.step} />
      )}

      {/* ── Offer teaser ─────────────────────────────────────────────── */}
      {hasOffer && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200">
          <TrophyOutlined style={{ color: '#d97706', fontSize: 14 }} />
          <Text className="text-xs font-bold text-amber-800">
            Offer:{' '}
            {app.offer_currency} {Number(app.offer_amount).toLocaleString()}
            {app.offer_accepted_at ? ' · Accepted' : app.offer_rejected_at ? ' · Declined' : ' · Awaiting response'}
          </Text>
        </div>
      )}

      {/* ── Rejection note ───────────────────────────────────────────── */}
      {app.status === 'rejected' && app.rejection_reason && (
        <div className="flex items-start gap-2 px-3 py-2 rounded-xl bg-rose-50 border border-rose-100">
          <CloseCircleOutlined style={{ color: '#e11d48', fontSize: 13, marginTop: 2 }} />
          <Text className="text-xs text-rose-700 leading-relaxed">{app.rejection_reason}</Text>
        </div>
      )}

      {/* ── Withdrawn note ───────────────────────────────────────────── */}
      {app.status === 'withdrawn' && app.withdrawn_reason && (
        <div className="flex items-start gap-2 px-3 py-2 rounded-xl bg-slate-100 border border-slate-200">
          <MinusCircleOutlined style={{ color: '#64748b', fontSize: 13, marginTop: 2 }} />
          <Text className="text-xs text-slate-600 leading-relaxed">{app.withdrawn_reason}</Text>
        </div>
      )}

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100">
        <div className="flex items-center gap-3 text-[10px] text-slate-400 font-medium">
          <span className="flex items-center gap-1">
            <CalendarOutlined /> Applied {dayjs(app.created_at).format('D MMM YYYY')}
          </span>
          {lastActivity !== app.created_at && (
            <span className="flex items-center gap-1">
              <ClockCircleOutlined /> Updated {dayjs(lastActivity).fromNow()}
            </span>
          )}
        </div>
        <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest group-hover:text-blue-800 transition-colors">
          View Details →
        </span>
      </div>
    </div>
  )
}

// ─── Status filter tabs ───────────────────────────────────────────────────────

const FILTER_TABS = [
  { key: 'all',      label: 'All' },
  { key: 'active',   label: 'Active' },
  { key: 'offer',    label: 'Offers' },
  { key: 'closed',   label: 'Closed' },
]

function filterApps(apps: any[], tab: string): any[] {
  if (tab === 'all') return apps
  if (tab === 'active') return apps.filter(a =>
    ['applied', 'sourcing', 'screening', 'shortlisted', 'in_review',
     'interview', 'interview_scheduled', 'assessment', 'on_hold'].includes(a.status)
  )
  if (tab === 'offer') return apps.filter(a =>
    ['offer', 'offer_extended', 'offer_accepted'].includes(a.status)
  )
  if (tab === 'closed') return apps.filter(a =>
    ['joined', 'placement_confirmed', 'placement_cancelled', 'rejected', 'withdrawn'].includes(a.status)
  )
  return apps
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function MyApplications() {
  const [applicationsWithJobs, setApplicationsWithJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const openQuickView = useDrawerStore(s => s.openQuickView)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const appsResponse = await candidateApi.listApplications()
      // CandidateApplicationSerializer already includes job_title and company_name
      const applications: any[] = appsResponse.data?.data?.applications ?? []

      // Sort by most recent activity first
      applications.sort((a, b) =>
        dayjs(b.updated_at ?? b.created_at).valueOf() - dayjs(a.updated_at ?? a.created_at).valueOf()
      )

      setApplicationsWithJobs(applications)
    } catch {
      // silent failure — empty list shown
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const visible = filterApps(applicationsWithJobs, activeTab)

  const counts = {
    all:    applicationsWithJobs.length,
    active: filterApps(applicationsWithJobs, 'active').length,
    offer:  filterApps(applicationsWithJobs, 'offer').length,
    closed: filterApps(applicationsWithJobs, 'closed').length,
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <Spin size="large" />
        <Text type="secondary" className="text-sm">Loading your applications…</Text>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <Title level={3} className="!mb-0.5">My Applications</Title>
          <Text type="secondary" className="text-sm">
            {applicationsWithJobs.length === 0
              ? 'No applications yet'
              : `${applicationsWithJobs.length} application${applicationsWithJobs.length > 1 ? 's' : ''} · sorted by latest activity`}
          </Text>
        </div>
        <Button icon={<SyncOutlined />} onClick={fetchData} className="rounded-xl font-bold shrink-0">
          Refresh
        </Button>
      </div>

      {applicationsWithJobs.length === 0 ? (
        /* ── Empty state ────────────────────────────────────────────────── */
        <div className="flex flex-col items-center text-center py-20 rounded-3xl border border-dashed border-slate-200 bg-slate-50">
          <div className="h-20 w-20 bg-white rounded-full border border-slate-200 flex items-center justify-center mx-auto mb-5 shadow-sm">
            <SolutionOutlined style={{ fontSize: 36, color: '#cbd5e1' }} />
          </div>
          <Title level={4} className="!mb-2 text-slate-800">No applications yet</Title>
          <Paragraph className="text-slate-500 mb-6 max-w-xs text-sm">
            Start exploring open roles and apply to positions that match your skills.
          </Paragraph>
          <Link to="/candidate/jobs">
            <Button type="primary" size="large" className="rounded-xl font-bold h-11 px-8 bg-blue-600 border-none">
              Browse Jobs <ArrowRightOutlined />
            </Button>
          </Link>
        </div>
      ) : (
        <>
          {/* ── Filter tabs ───────────────────────────────────────────────── */}
          <div className="flex items-center gap-1 mb-5 bg-slate-100 rounded-xl p-1">
            {FILTER_TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-widest transition-all flex-1 justify-center',
                  activeTab === tab.key
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                )}
              >
                {tab.label}
                {counts[tab.key as keyof typeof counts] > 0 && (
                  <span className={cn(
                    'text-[9px] font-black px-1.5 py-0.5 rounded-full',
                    activeTab === tab.key ? 'bg-blue-100 text-blue-700' : 'bg-slate-200 text-slate-500'
                  )}>
                    {counts[tab.key as keyof typeof counts]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* ── Application list ──────────────────────────────────────────── */}
          {visible.length === 0 ? (
            <div className="text-center py-12 rounded-2xl border border-dashed border-slate-200">
              <Text type="secondary" className="text-sm">No applications in this category</Text>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {visible.map(app => (
                <ApplicationCard
                  key={app.id}
                  app={app}
                  onClick={() => openQuickView('candidate_application', app)}
                />
              ))}
            </div>
          )}

          {/* ── Offer callout if any offers ───────────────────────────────── */}
          {counts.offer > 0 && activeTab !== 'offer' && (
            <div
              className="mt-4 flex items-center justify-between px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 cursor-pointer hover:border-amber-300 transition-colors"
              onClick={() => setActiveTab('offer')}
            >
              <div className="flex items-center gap-2">
                <TrophyOutlined style={{ color: '#d97706', fontSize: 16 }} />
                <Text className="text-sm font-bold text-amber-800">
                  You have {counts.offer} offer{counts.offer > 1 ? 's' : ''} awaiting review
                </Text>
              </div>
              <RightOutlined style={{ color: '#d97706', fontSize: 11 }} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
