/**
 * CandidateCommandCenter
 *
 * Route:  /candidate/dashboard
 * Access: candidate role only
 *
 * Enterprise Candidate Experience Core — aggregates Applications,
 * Interviews, Offers, Passport, and Activity in one command view.
 *
 * Data sources (no new APIs — all existing):
 *   • candidateApi.listApplications()   → applications, offers (filtered by status)
 *   • interviewsApi.candidateList()      → upcoming / pending / completed buckets
 *   • passportApi.get()                  → profile strength, skills, CV status
 *
 * Offers: derived from applications with status in
 *   [offer_extended, offer_accepted, joined, placement_confirmed].
 *   A dedicated GET /candidate/offers/ endpoint would improve this — deferred.
 *
 * Activity Timeline: synthesised from applications (sorted by updated_at).
 *   A real /candidate/activity/ endpoint is deferred.
 */

import { useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Row, Col, Card, Tag, Skeleton, Empty, Button, Progress, Typography, Tooltip } from 'antd'
import {
  Briefcase, Calendar, Gift, ShieldCheck,
  ChevronRight, TrendingUp, FileText, Star,
  UploadCloud, User, CheckCircle2, Clock,
  Activity, Sparkles, ArrowUpRight, BookOpen,
  Layers, Zap, Bell, BriefcaseBusiness,
  MapPin, Building2, ExternalLink,
} from 'lucide-react'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useAuthStore } from '@/store/authStore'
import { candidateApi } from '@/api/candidate'
import { interviewsApi } from '@/api/interviews'
import { passportApi } from '@/api/passport'
import { notificationsApi } from '@/api/notifications'
import { cn } from '@/utils/cn'
import type { Passport, Notification } from '@/types'

dayjs.extend(relativeTime)
const { Text, Title } = Typography

// ─── Status map ───────────────────────────────────────────────────────────────

const APP_STATUS: Record<string, { label: string; color: string; dot: string }> = {
  applied:              { label: 'Applied',        color: 'blue',     dot: 'bg-blue-500'    },
  sourcing:             { label: 'In Review',      color: 'default',  dot: 'bg-slate-400'   },
  screening:            { label: 'Screening',      color: 'cyan',     dot: 'bg-cyan-500'    },
  shortlisted:          { label: 'Shortlisted',    color: 'geekblue', dot: 'bg-indigo-500'  },
  in_review:            { label: 'In Review',      color: 'orange',   dot: 'bg-orange-500'  },
  interview:            { label: 'Interview',      color: 'purple',   dot: 'bg-purple-500'  },
  interview_scheduled:  { label: 'Interview',      color: 'purple',   dot: 'bg-purple-500'  },
  assessment:           { label: 'Assessment',     color: 'purple',   dot: 'bg-violet-500'  },
  on_hold:              { label: 'On Hold',        color: 'default',  dot: 'bg-slate-400'   },
  offer:                { label: 'Offer',          color: 'gold',     dot: 'bg-amber-500'   },
  offer_extended:       { label: 'Offer',          color: 'gold',     dot: 'bg-amber-500'   },
  offer_accepted:       { label: 'Accepted',       color: 'green',    dot: 'bg-emerald-500' },
  joined:               { label: 'Joined',         color: 'success',  dot: 'bg-emerald-600' },
  placement_confirmed:  { label: 'Confirmed',      color: 'success',  dot: 'bg-emerald-600' },
  placement_cancelled:  { label: 'Cancelled',      color: 'red',      dot: 'bg-rose-500'    },
  rejected:             { label: 'Rejected',       color: 'red',      dot: 'bg-rose-500'    },
  withdrawn:            { label: 'Withdrawn',      color: 'default',  dot: 'bg-slate-400'   },
}

const INTERVIEW_STATUS: Record<string, { label: string; color: string }> = {
  scheduled:        { label: 'Scheduled',        color: 'blue'     },
  confirmed:        { label: 'Confirmed',        color: 'geekblue' },
  in_progress:      { label: 'In Progress',      color: 'orange'   },
  completed:        { label: 'Completed',        color: 'green'    },
  cancelled:        { label: 'Cancelled',        color: 'red'      },
  no_show:          { label: 'No Show',          color: 'red'      },
  pending_feedback: { label: 'Pending Feedback', color: 'gold'     },
}

const OFFER_STATUSES = new Set(['offer', 'offer_extended', 'offer_accepted', 'joined', 'placement_confirmed'])

// ─── Helpers ──────────────────────────────────────────────────────────────────

function statusChip(status: string, map: Record<string, { label: string; color: string }>) {
  const s = map[status]
  return (
    <Tag color={s?.color ?? 'default'} style={{ textTransform: 'capitalize', fontSize: 11 }}>
      {s?.label ?? status.replace(/_/g, ' ')}
    </Tag>
  )
}

function interviewTypeLabel(type: string): string {
  const map: Record<string, string> = {
    technical: 'Technical',
    behavioral: 'Behavioral',
    cultural: 'Culture Fit',
    coding: 'Coding',
    system_design: 'System Design',
    hr: 'HR',
    panel: 'Panel',
  }
  return map[type] ?? type?.replace(/_/g, ' ')
}

function getGreeting(firstName?: string): string {
  const h = new Date().getHours()
  const salutation = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
  return firstName ? `${salutation}, ${firstName}` : salutation
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  title, value, subtitle, icon: Icon, color, loading, onClick,
}: {
  title: string
  value: number | string
  subtitle?: string
  icon: React.ElementType
  color: string
  loading?: boolean
  onClick?: () => void
}) {
  return (
    <Card
      bordered={false}
      className={cn(
        'group overflow-hidden transition-all duration-300 hover:shadow-soft-lg',
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
    >
      {loading ? (
        <Skeleton active paragraph={{ rows: 2 }} />
      ) : (
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className={cn('flex h-11 w-11 items-center justify-center rounded-2xl transition-transform duration-300 group-hover:scale-105', color)}>
              <Icon className="h-5 w-5" />
            </div>
            {onClick && (
              <ArrowUpRight className="h-4 w-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
            )}
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{title}</p>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight mt-0.5">{value}</h3>
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          <div className="absolute -right-4 -bottom-4 h-20 w-20 rounded-full bg-slate-50/50 group-hover:bg-slate-100/50 transition-colors duration-300" />
        </div>
      )}
    </Card>
  )
}

// ─── Section Header ───────────────────────────────────────────────────────────

function SectionHeader({
  title, icon: Icon, to, linkLabel,
}: {
  title: string
  icon: React.ElementType
  to?: string
  linkLabel?: string
}) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-bold text-slate-800">{title}</span>
      </div>
      {to && (
        <Link to={to} className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors">
          {linkLabel ?? 'View all'} <ChevronRight className="h-3 w-3" />
        </Link>
      )}
    </div>
  )
}

// ─── My Opportunities ─────────────────────────────────────────────────────────

function MyOpportunities({ applications, loading, t }: {
  applications: any[]
  loading: boolean
  t: (k: string, d: string) => string
}) {
  const navigate = useNavigate()
  const active = applications.filter(a =>
    !['rejected', 'withdrawn', 'placement_cancelled'].includes(a.status)
  ).slice(0, 6)

  return (
    <Card bordered={false} className="shadow-soft-sm h-full">
      <SectionHeader
        title={t('cc.opportunities', 'My Opportunities')}
        icon={Briefcase}
        to="/candidate/applications"
        linkLabel={t('cc.view_all', 'View all')}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 5 }} />
      ) : active.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span className="text-sm text-slate-400">{t('cc.no_opportunities', 'No active opportunities')}</span>
          }
        >
          <Button type="primary" size="small" onClick={() => navigate('/candidate/jobs')}>
            {t('cc.browse_jobs', 'Browse Jobs')}
          </Button>
        </Empty>
      ) : (
        <div className="divide-y divide-slate-100">
          {active.map(app => {
            const st = APP_STATUS[app.status]
            const lastActivity = app.updated_at ?? app.applied_at
            return (
              <div
                key={app.id}
                className="flex items-center gap-3 py-3 px-1 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer group"
                onClick={() => navigate('/candidate/applications')}
              >
                {/* Status dot */}
                <div className={cn('h-2 w-2 rounded-full shrink-0 mt-0.5', st?.dot ?? 'bg-slate-400')} />

                {/* Job info */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-slate-900 truncate">
                    {app.job_title ?? t('cc.unknown_job', 'Unknown Role')}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-500 truncate max-w-[140px]">
                      {app.company_name ?? '—'}
                    </span>
                    {lastActivity && (
                      <span className="text-[10px] text-slate-400 shrink-0">
                        · {dayjs(lastActivity).fromNow()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Stage / status */}
                <div className="shrink-0">{statusChip(app.status, APP_STATUS)}</div>

                {/* Quick action */}
                <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-slate-500 transition-colors shrink-0" />
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

// ─── My Interviews ────────────────────────────────────────────────────────────

function MyInterviews({ interviews, loading, t }: {
  interviews: any[]
  loading: boolean
  t: (k: string, d: string) => string
}) {
  const navigate = useNavigate()
  const upcoming = interviews.slice(0, 5)

  return (
    <Card bordered={false} className="shadow-soft-sm h-full">
      <SectionHeader
        title={t('cc.interviews', 'My Interviews')}
        icon={Calendar}
        to="/candidate/interviews"
        linkLabel={t('cc.view_all', 'View all')}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : upcoming.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span className="text-sm text-slate-400">{t('cc.no_interviews', 'No upcoming interviews')}</span>
          }
        />
      ) : (
        <div className="flex flex-col gap-2">
          {upcoming.map(iv => {
            const isToday = iv.scheduled_at && dayjs(iv.scheduled_at).isSame(dayjs(), 'day')
            return (
              <div
                key={iv.id}
                className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 hover:bg-blue-50 border border-transparent hover:border-blue-100 transition-all cursor-pointer"
                onClick={() => navigate(`/candidate/interviews/${iv.id}/instructions?access_token=${iv.candidate_runtime?.token ?? ''}`)}
              >
                {/* Date block */}
                <div className={cn(
                  'flex flex-col items-center justify-center h-10 w-10 rounded-xl shrink-0 text-center',
                  isToday ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-700'
                )}>
                  <div className="text-[10px] font-black uppercase leading-none">
                    {iv.scheduled_at ? dayjs(iv.scheduled_at).format('MMM') : '—'}
                  </div>
                  <div className="text-sm font-black leading-none mt-0.5">
                    {iv.scheduled_at ? dayjs(iv.scheduled_at).format('D') : '—'}
                  </div>
                </div>

                {/* Interview info */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-slate-800 truncate">
                    {iv.title ?? t('cc.interview', 'Interview')}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    {iv.interview_type && (
                      <span className="text-[10px] font-semibold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">
                        {interviewTypeLabel(iv.interview_type)}
                      </span>
                    )}
                    {iv.scheduled_at && (
                      <span className="text-[10px] text-slate-400 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {dayjs(iv.scheduled_at).format('HH:mm')}
                        {iv.duration_minutes ? ` · ${iv.duration_minutes}m` : ''}
                      </span>
                    )}
                    {isToday && (
                      <span className="text-[9px] font-black uppercase tracking-widest text-blue-600 animate-pulse">
                        Today
                      </span>
                    )}
                  </div>
                </div>

                {/* Status */}
                <div className="shrink-0">
                  {statusChip(iv.status ?? 'scheduled', INTERVIEW_STATUS)}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

// ─── My Offers ────────────────────────────────────────────────────────────────

function MyOffers({ offers, loading, t }: {
  offers: any[]
  loading: boolean
  t: (k: string, d: string) => string
}) {
  if (!loading && offers.length === 0) return null

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <SectionHeader
        title={t('cc.offers', 'My Offers')}
        icon={Gift}
        to="/candidate/applications"
        linkLabel={t('cc.view_all', 'View all')}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 2 }} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {offers.map(offer => (
            <div
              key={offer.id}
              className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100 hover:border-amber-300 transition-colors"
            >
              <div className="h-9 w-9 rounded-xl bg-amber-100 flex items-center justify-center shrink-0">
                <Gift className="h-4 w-4 text-amber-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-slate-800 truncate">
                  {offer.job_title ?? t('cc.unknown_job', 'Unknown Role')}
                </div>
                <div className="text-xs text-slate-500 truncate">{offer.company_name ?? '—'}</div>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  {statusChip(offer.status, APP_STATUS)}
                  {offer.joining_date && (
                    <span className="text-[10px] text-slate-500 flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {t('cc.joins', 'Joins')} {dayjs(offer.joining_date).format('D MMM YYYY')}
                    </span>
                  )}
                  {offer.offer_amount && (
                    <span className="text-[10px] font-black text-emerald-700">
                      {offer.offer_currency ?? ''} {Number(offer.offer_amount).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

// ─── Passport Summary ─────────────────────────────────────────────────────────

function PassportSummary({ passport, loading, t }: {
  passport: Passport | undefined
  loading: boolean
  t: (k: string, d: string) => string
}) {
  const navigate = useNavigate()
  const score = passport?.completeness_score ?? 0
  const skillCount = passport?.skills?.length ?? 0
  const expYears = passport?.experience_years
  const hasCv = !!passport?.current_cv_url

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <SectionHeader
        title={t('cc.passport_summary', 'Talent Passport')}
        icon={ShieldCheck}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Score ring */}
          <div className="flex items-center gap-4">
            <Progress
              type="circle"
              percent={Math.round(score)}
              size={72}
              strokeColor={score >= 80 ? '#10b981' : score >= 50 ? '#1E40AF' : '#f59e0b'}
              format={p => <span className="text-sm font-bold">{p}%</span>}
            />
            <div>
              <div className="text-sm font-bold text-slate-800">
                {t('cc.profile_strength', 'Profile Strength')}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {score >= 80
                  ? t('cc.strength_strong', 'Strong — ready to share')
                  : score >= 50
                    ? t('cc.strength_good', 'Good — a few items missing')
                    : t('cc.strength_weak', 'Incomplete — add more info')}
              </div>
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: t('cc.skills', 'Skills'), value: skillCount, icon: Star, color: 'text-amber-600 bg-amber-50' },
              { label: t('cc.experience', 'Exp. Yrs'), value: expYears ?? '—', icon: Briefcase, color: 'text-blue-600 bg-blue-50' },
              { label: t('cc.resume', 'Resume'), value: hasCv ? '✓' : '✗', icon: FileText, color: hasCv ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className={cn('flex flex-col items-center justify-center p-2.5 rounded-xl gap-1', color.split(' ')[1])}>
                <Icon className={cn('h-4 w-4', color.split(' ')[0])} />
                <div className="text-sm font-bold text-slate-800">{value}</div>
                <div className="text-[9px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
              </div>
            ))}
          </div>

          <Button
            type="primary"
            ghost
            block
            onClick={() => navigate('/passport')}
            icon={<ArrowUpRight className="h-4 w-4" />}
          >
            {t('cc.view_passport', 'View Passport')}
          </Button>
        </div>
      )}
    </Card>
  )
}

// ─── Profile Strength Suggestions ────────────────────────────────────────────

function ProfileStrengthSuggestions({ passport, loading, t }: {
  passport: Passport | undefined
  loading: boolean
  t: (k: string, d: string) => string
}) {
  const navigate = useNavigate()

  const suggestions = useMemo(() => {
    if (!passport) return []
    const s: { text: string; icon: React.ElementType; done: boolean }[] = [
      {
        text: t('cc.sug_headline', 'Add a professional headline'),
        icon: User,
        done: !!passport.headline?.trim(),
      },
      {
        text: t('cc.sug_summary', 'Write a professional summary'),
        icon: BookOpen,
        done: !!passport.summary?.trim(),
      },
      {
        text: t('cc.sug_skills', 'Add at least 5 skills'),
        icon: Star,
        done: (passport.skills?.length ?? 0) >= 5,
      },
      {
        text: t('cc.sug_resume', 'Upload your resume / CV'),
        icon: UploadCloud,
        done: !!passport.current_cv_url,
      },
      {
        text: t('cc.sug_experience', 'Add work experience'),
        icon: Briefcase,
        done: (passport.work_history?.length ?? 0) > 0,
      },
      {
        text: t('cc.sug_education', 'Add your education'),
        icon: Layers,
        done: (passport.education?.length ?? 0) > 0,
      },
    ]
    return s
  }, [passport, t])

  const incomplete = suggestions.filter(s => !s.done)
  const score = passport?.completeness_score ?? 0

  if (loading) return <Card bordered={false} className="shadow-soft-sm"><Skeleton active paragraph={{ rows: 4 }} /></Card>
  if (!passport) return null

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="h-4 w-4 text-amber-500" />
        <span className="text-sm font-bold text-slate-800">{t('cc.complete_profile', 'Complete Your Profile')}</span>
        <span className="ml-auto text-xs font-bold text-slate-400">{Math.round(score)}%</span>
      </div>

      <Progress
        percent={Math.round(score)}
        strokeColor={score >= 80 ? '#10b981' : score >= 50 ? '#1E40AF' : '#f59e0b'}
        showInfo={false}
        className="mb-3"
        size="small"
      />

      {incomplete.length === 0 ? (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50 text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          <span className="text-xs font-semibold">{t('cc.profile_complete', 'Profile is complete!')}</span>
        </div>
      ) : (
        <div className="flex flex-col gap-1.5">
          {incomplete.slice(0, 4).map(({ text, icon: Icon }) => (
            <div
              key={text}
              className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors group"
              onClick={() => navigate('/passport')}
            >
              <div className="h-6 w-6 rounded-md bg-slate-100 flex items-center justify-center shrink-0 group-hover:bg-blue-100 transition-colors">
                <Icon className="h-3.5 w-3.5 text-slate-400 group-hover:text-blue-600 transition-colors" />
              </div>
              <span className="text-xs text-slate-600 flex-1">{text}</span>
              <ChevronRight className="h-3 w-3 text-slate-300 group-hover:text-blue-400 transition-colors" />
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

// ─── Activity Timeline ────────────────────────────────────────────────────────

function ActivityTimeline({ applications, loading, t }: {
  applications: any[]
  loading: boolean
  t: (k: string, d: string) => string
}) {
  // Synthesise timeline from latest 5 application events (sorted by updated_at)
  const events = useMemo(() =>
    [...applications]
      .sort((a, b) => dayjs(b.updated_at ?? b.applied_at).valueOf() - dayjs(a.updated_at ?? a.applied_at).valueOf())
      .slice(0, 5)
      .map(app => {
        const st = APP_STATUS[app.status]
        return {
          id: app.id,
          label: `${st?.label ?? app.status.replace(/_/g, ' ')} — ${app.job_title ?? ''}`,
          sub: app.company_name ?? '',
          time: app.updated_at ?? app.applied_at,
          color: app.status === 'rejected' || app.status === 'withdrawn' ? 'bg-rose-400' : st?.dot ?? 'bg-slate-400',
        }
      }), [applications])

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <SectionHeader
        title={t('cc.activity', 'Recent Activity')}
        icon={Activity}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : events.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={<span className="text-sm text-slate-400">{t('cc.no_activity', 'No recent activity')}</span>}
        />
      ) : (
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-2.5 top-3 bottom-3 w-px bg-slate-100" />

          <div className="flex flex-col gap-4">
            {events.map((ev, i) => (
              <div key={ev.id + i} className="flex items-start gap-3 pl-1">
                <div className={cn('h-4 w-4 rounded-full shrink-0 mt-0.5 ring-2 ring-white', ev.color)} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-slate-800 leading-snug">{ev.label}</div>
                  {ev.sub && <div className="text-[10px] text-slate-400 mt-0.5">{ev.sub}</div>}
                  <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {dayjs(ev.time).fromNow()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

// ─── Recent Notifications ─────────────────────────────────────────────────────

const NOTIF_ICON_MAP: Record<string, React.ElementType> = {
  interview:    Calendar,
  application:  Briefcase,
  offer:        Gift,
  passport:     ShieldCheck,
}

function RecentNotifications({ notifications, loading }: {
  notifications: Notification[]
  loading: boolean
}) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  if (!loading && notifications.length === 0) return null

  const handleClick = async (n: Notification) => {
    try {
      await notificationsApi.markRead(n.id)
      queryClient.invalidateQueries({ queryKey: ['candidate', 'notifications'] })
    } catch { /* silent */ }
    if (n.link) navigate(n.link)
  }

  const handleMarkAll = async () => {
    try {
      await notificationsApi.markAllRead()
      queryClient.invalidateQueries({ queryKey: ['candidate', 'notifications'] })
    } catch { /* silent */ }
  }

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-bold text-slate-800">Notifications</span>
          {notifications.length > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1.5 text-[9px] font-black text-white">
              {notifications.length}
            </span>
          )}
        </div>
        {notifications.length > 0 && (
          <button
            onClick={handleMarkAll}
            className="text-[10px] font-semibold text-blue-600 hover:text-blue-800 transition-colors"
          >
            Mark all read
          </button>
        )}
      </div>

      {loading ? (
        <Skeleton active paragraph={{ rows: 3 }} />
      ) : (
        <div className="flex flex-col gap-1.5">
          {notifications.slice(0, 5).map(n => {
            const Icon = NOTIF_ICON_MAP[n.type] ?? Bell
            return (
              <div
                key={n.id}
                onClick={() => handleClick(n)}
                className="flex items-start gap-3 p-3 rounded-xl bg-blue-50/60 border border-blue-100 hover:border-blue-200 hover:bg-blue-50 transition-all cursor-pointer group"
              >
                <div className="h-8 w-8 rounded-lg bg-white border border-blue-100 flex items-center justify-center shrink-0 group-hover:border-blue-200 transition-colors">
                  <Icon className="h-3.5 w-3.5 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-slate-800 leading-snug">{n.title}</div>
                  {n.body && (
                    <div className="text-[10px] text-slate-500 mt-0.5 truncate">{n.body}</div>
                  )}
                  <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {dayjs(n.created_at).fromNow()}
                  </div>
                </div>
                {n.link && (
                  <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-blue-400 shrink-0 transition-colors mt-1" />
                )}
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

// ─── Recommended Jobs ─────────────────────────────────────────────────────────

function RecommendedJobs({ jobs, loading, t }: {
  jobs: any[]
  loading: boolean
  t: (k: string, d: string) => string
}) {
  const navigate = useNavigate()

  return (
    <Card bordered={false} className="shadow-soft-sm">
      <SectionHeader
        title={t('cc.recommended_jobs', 'Jobs For You')}
        icon={BriefcaseBusiness}
        to="/candidate/jobs"
        linkLabel={t('cc.browse_all', 'Browse all')}
      />

      {loading ? (
        <Skeleton active paragraph={{ rows: 3 }} />
      ) : jobs.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span className="text-sm text-slate-400">
              {t('cc.no_jobs', 'No open positions right now')}
            </span>
          }
        >
          <Button type="primary" size="small" onClick={() => navigate('/candidate/jobs')}>
            {t('cc.explore_jobs', 'Explore Jobs')}
          </Button>
        </Empty>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {jobs.slice(0, 4).map((job: any) => {
            const location = job.location ?? job.metadata?.location ?? job.job_location ?? null
            const company  = job.company_name ?? job.tenant_name ?? job.metadata?.company ?? null
            const mode     = job.work_mode ?? job.metadata?.work_mode ?? null
            return (
              <div
                key={job.id}
                className="flex flex-col gap-3 p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:border-blue-200 hover:bg-blue-50/30 transition-all group"
              >
                {/* Icon + title */}
                <div className="flex items-start gap-3">
                  <div className="h-9 w-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 group-hover:border-blue-200 transition-colors">
                    <Briefcase className="h-4 w-4 text-slate-400 group-hover:text-blue-500 transition-colors" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-slate-800 leading-snug line-clamp-2">
                      {job.title ?? t('cc.unknown_job', 'Open Role')}
                    </div>
                    {company && (
                      <div className="flex items-center gap-1 mt-0.5 text-[10px] text-slate-500 font-medium">
                        <Building2 className="h-3 w-3 shrink-0" />
                        <span className="truncate">{company}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap gap-1.5">
                  {location && (
                    <span className="flex items-center gap-0.5 text-[9px] font-semibold text-slate-500 bg-white border border-slate-200 px-1.5 py-0.5 rounded-md">
                      <MapPin className="h-2.5 w-2.5 shrink-0" /> {location}
                    </span>
                  )}
                  {mode && (
                    <span className="text-[9px] font-semibold text-slate-500 bg-white border border-slate-200 px-1.5 py-0.5 rounded-md capitalize">
                      {mode.replace(/_/g, ' ')}
                    </span>
                  )}
                  {job.posted_at && (
                    <span className="text-[9px] text-slate-400 bg-white border border-slate-100 px-1.5 py-0.5 rounded-md">
                      {dayjs(job.posted_at).fromNow()}
                    </span>
                  )}
                </div>

                {/* Apply CTA */}
                <Button
                  size="small"
                  type="primary"
                  ghost
                  block
                  icon={<ExternalLink className="h-3 w-3" />}
                  onClick={() => navigate('/candidate/jobs')}
                  className="!text-[10px] !font-black !uppercase !tracking-widest mt-auto"
                >
                  {t('cc.view_job', 'View & Apply')}
                </Button>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CandidateCommandCenter() {
  const navigate = useNavigate()
  const { t } = useTranslation('dashboard')
  const user = useAuthStore(s => s.user)

  // ── Data fetching ──────────────────────────────────────────────────────────
  const { data: appsData, isLoading: appsLoading } = useApiQuery(
    ['candidate', 'applications'],
    () => candidateApi.listApplications()
  )

  const { data: interviewsData, isLoading: interviewsLoading } = useApiQuery(
    ['candidate', 'interviews-list'],
    () => interviewsApi.candidateList()
  )

  const { data: passportData, isLoading: passportLoading } = useApiQuery(
    ['candidate', 'passport'],
    () => passportApi.get()
  )

  const { data: notificationsData, isLoading: notificationsLoading } = useApiQuery(
    ['candidate', 'notifications'],
    () => notificationsApi.list({ is_read: false })
  )

  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['candidate', 'recommended-jobs'],
    () => candidateApi.recommendedJobs()
  )

  // ── Derived data ───────────────────────────────────────────────────────────
  const applications: any[] = (appsData as any)?.applications ?? []
  const passport: Passport | undefined = (passportData as any)?.passport
  const unreadNotifications: Notification[] = (notificationsData as any)?.notifications ?? []
  const recommendedJobs: any[] = (jobsData as any)?.jobs ?? []

  const upcomingInterviews: any[] = [
    ...((interviewsData as any)?.upcoming_interviews ?? []),
    ...((interviewsData as any)?.pending_interviews ?? []),
  ].slice(0, 6)

  const offers = applications.filter(a => OFFER_STATUSES.has(a.status))
  const activeApps = applications.filter(a => !['rejected', 'withdrawn', 'placement_cancelled'].includes(a.status))

  const completeness = passport?.completeness_score ?? 0

  const isAppsLoading = appsLoading
  const isInterviewsLoading = interviewsLoading
  const isPassportLoading = passportLoading

  // ── Stats ──────────────────────────────────────────────────────────────────
  const stats = [
    {
      title: t('cc.stat_applications', 'Applications'),
      value: activeApps.length,
      subtitle: t('cc.stat_applications_sub', 'Active opportunities'),
      icon: Briefcase,
      color: 'bg-blue-50 text-blue-600',
      loading: isAppsLoading,
      onClick: () => navigate('/candidate/applications'),
    },
    {
      title: t('cc.stat_interviews', 'Interviews'),
      value: upcomingInterviews.length,
      subtitle: t('cc.stat_interviews_sub', 'Upcoming & pending'),
      icon: Calendar,
      color: 'bg-purple-50 text-purple-600',
      loading: isInterviewsLoading,
      onClick: () => navigate('/candidate/interviews'),
    },
    {
      title: t('cc.stat_offers', 'Offers'),
      value: offers.length,
      subtitle: offers.length > 0 ? t('cc.stat_offers_active', 'Waiting for decision') : t('cc.stat_offers_none', 'Keep going!'),
      icon: Gift,
      color: offers.length > 0 ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 text-slate-400',
      loading: isAppsLoading,
      onClick: offers.length > 0 ? () => navigate('/candidate/applications') : undefined,
    },
    {
      title: t('cc.stat_profile', 'Profile Strength'),
      value: `${Math.round(completeness)}%`,
      subtitle: completeness >= 80 ? t('cc.stat_profile_strong', 'Excellent') : t('cc.stat_profile_improve', 'Add more info'),
      icon: TrendingUp,
      color: completeness >= 80 ? 'bg-emerald-50 text-emerald-600' : completeness >= 50 ? 'bg-blue-50 text-blue-600' : 'bg-rose-50 text-rose-600',
      loading: isPassportLoading,
      onClick: () => navigate('/passport'),
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* ── Page header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            {getGreeting(user?.first_name)}
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {t('cc.subtitle', 'Your career command center — track everything in one place.')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Tooltip title={t('cc.browse_jobs_tip', 'Discover new opportunities')}>
            <Button
              icon={<Sparkles className="h-4 w-4" />}
              onClick={() => navigate('/candidate/jobs')}
            >
              {t('cc.browse_jobs', 'Browse Jobs')}
            </Button>
          </Tooltip>
          <Button
            type="primary"
            icon={<ShieldCheck className="h-4 w-4" />}
            onClick={() => navigate('/passport')}
          >
            {t('cc.my_passport', 'My Passport')}
          </Button>
        </div>
      </div>

      {/* ── Summary stats ────────────────────────────────────────────────────── */}
      <Row gutter={[20, 20]}>
        {stats.map((stat, i) => (
          <Col xs={24} sm={12} xl={6} key={i}>
            <StatCard {...stat} />
          </Col>
        ))}
      </Row>

      {/* ── Main body: Opportunities (left) + Passport/Strength (right) ─────── */}
      <Row gutter={[20, 20]} align="stretch">
        <Col xs={24} lg={15}>
          <MyOpportunities applications={applications} loading={isAppsLoading} t={t as any} />
        </Col>
        <Col xs={24} lg={9}>
          <div className="flex flex-col gap-5 h-full">
            <PassportSummary passport={passport} loading={isPassportLoading} t={t as any} />
            <ProfileStrengthSuggestions passport={passport} loading={isPassportLoading} t={t as any} />
          </div>
        </Col>
      </Row>

      {/* ── Notifications (full width, hidden when empty) ────────────────────── */}
      <RecentNotifications
        notifications={unreadNotifications}
        loading={notificationsLoading}
      />

      {/* ── Offers (full width, hidden when empty) ───────────────────────────── */}
      <MyOffers offers={offers} loading={isAppsLoading} t={t as any} />

      {/* ── Interviews (left) + Activity Timeline (right) ───────────────────── */}
      <Row gutter={[20, 20]} align="stretch">
        <Col xs={24} lg={15}>
          <MyInterviews interviews={upcomingInterviews} loading={isInterviewsLoading} t={t as any} />
        </Col>
        <Col xs={24} lg={9}>
          <ActivityTimeline applications={applications} loading={isAppsLoading} t={t as any} />
        </Col>
      </Row>

      {/* ── Recommended Jobs (full width) ────────────────────────────────────── */}
      <RecommendedJobs jobs={recommendedJobs} loading={jobsLoading} t={t as any} />
    </motion.div>
  )
}
