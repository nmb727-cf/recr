/**
 * PublicPassportPage — Enterprise Talent Passport
 *
 * Route:  /passport/public/:token
 * Access: No authentication required (AllowAny)
 * API:    GET /api/v1/passport/public/:token/
 */

import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Spin } from 'antd'
import {
  MapPin, Briefcase, GraduationCap, Star, Globe, Linkedin,
  Github, Award, CheckCircle2, Clock, ExternalLink, Hash,
  Twitter, AlertCircle, ShieldOff, FileText, Play,
  Download, Layers, BookOpen, Code2, Sparkles,
  Building2, CalendarDays, Languages, ChevronRight,
  BarChart3, TrendingUp, BookMarked, Heart,
} from 'lucide-react'
import dayjs from 'dayjs'
import { passportApi } from '@/api/passport'

// ─── Types ────────────────────────────────────────────────────────────────────

// Keys in metadata that are internal/system — never displayed as custom fields
const METADATA_SKIP_KEYS = new Set([
  'internal', 'system', 'import_source', 'sync_id', 'merged_from',
  'crm_id', 'ats_id', 'source_id', 'recruiter_notes', 'admin_notes',
])

interface PublicPassport {
  id: string
  passport_number?: string
  headline?: string
  summary?: string
  profile_photo_url?: string
  cover_image_url?: string
  video_intro_url?: string
  current_title?: string
  current_company?: string
  current_location_city?: string
  current_location_country?: string
  experience_years?: number | string
  current_cv_url?: string
  metadata?: Record<string, unknown>
  skills?: string[]
  languages?: string[]
  work_history?: WorkItem[]
  education?: EduItem[]
  certifications?: CertItem[]
  projects?: ProjectItem[]
  publications?: PublicationItem[]
  awards?: AwardItem[]
  volunteer_work?: VolunteerItem[]
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  twitter_url?: string
  behance_url?: string
  dribbble_url?: string
  notice_period_days?: number | null
  preferred_work_mode?: string
  is_actively_looking?: boolean
  open_to_work?: boolean
  identity_verified?: boolean
  background_verified?: boolean
  heat_score?: number
  completeness_score?: number
}

interface WorkItem {
  id?: string
  title?: string
  company?: string
  location?: string
  from_date?: string
  to_date?: string | null
  is_current?: boolean
  description?: string
}

interface EduItem {
  id?: string
  institution?: string
  degree?: string
  field?: string
  year?: number
  grade?: string
}

interface CertItem {
  id?: string
  name?: string
  issuer?: string
  issued_date?: string | null
  credential_url?: string
}

interface ProjectItem {
  id?: string
  name?: string
  description?: string
  url?: string
  skills?: string[]
}

interface PublicationItem {
  id?: string
  title?: string
  publisher?: string
  published_date?: string | null
  url?: string
  description?: string
}

interface AwardItem {
  id?: string
  title?: string
  issuer?: string
  date?: string | null
  description?: string
}

interface VolunteerItem {
  id?: string
  role?: string
  organisation?: string
  from_date?: string | null
  to_date?: string | null
  is_current?: boolean
  description?: string
}

type PageState =
  | { status: 'loading' }
  | { status: 'success'; passport: PublicPassport }
  | { status: 'not_found' }
  | { status: 'inactive' }
  | { status: 'error'; message: string }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getInitials(passport: PublicPassport): string {
  const source = passport.headline ?? passport.current_title ?? ''
  return source
    .split(/\s+/)
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() ?? '')
    .join('') || '?'
}

function formatDateRange(from?: string, to?: string | null, isCurrent?: boolean): string {
  const start = from ? dayjs(from).format('MMM YYYY') : '—'
  const end = isCurrent ? 'Present' : (to ? dayjs(to).format('MMM YYYY') : '—')
  return `${start} – ${end}`
}

function noticePeriodLabel(days?: number | null): string | null {
  if (days == null) return null
  if (days === 0) return 'Immediate'
  if (days <= 7) return `${days}d notice`
  if (days % 30 === 0) return `${days / 30}mo notice`
  if (days < 30) return `${days}d notice`
  return `${Math.round(days / 30)}mo notice`
}

function workModeLabel(mode?: string): string | null {
  if (!mode) return null
  const map: Record<string, string> = {
    remote: 'Remote',
    onsite: 'On-site',
    hybrid: 'Hybrid',
    flexible: 'Flexible',
  }
  return map[mode.toLowerCase()] ?? mode
}

function isVideoEmbeddable(url: string): { type: 'youtube' | 'vimeo' | 'link'; embedUrl?: string } {
  const yt = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
  if (yt) return { type: 'youtube', embedUrl: `https://www.youtube.com/embed/${yt[1]}` }
  const vm = url.match(/vimeo\.com\/(\d+)/)
  if (vm) return { type: 'vimeo', embedUrl: `https://player.vimeo.com/video/${vm[1]}` }
  return { type: 'link' }
}

// ─── Loading / Error States ───────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <Spin size="large" />
      <div className="text-sm font-medium text-slate-400 tracking-wide">Loading profile…</div>
    </div>
  )
}

function NotFoundState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-5 text-center px-4">
      <div className="h-16 w-16 rounded-2xl bg-rose-50 flex items-center justify-center shadow-sm">
        <AlertCircle size={28} className="text-rose-400" />
      </div>
      <div>
        <div className="text-xl font-black text-slate-800">Link not found</div>
        <div className="text-sm text-slate-400 mt-2 max-w-sm leading-relaxed">
          This passport link is invalid or has been removed. Check the URL or contact the person who shared it.
        </div>
      </div>
      <a href="/register/candidate" className="px-5 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-black uppercase tracking-widest hover:bg-blue-700 transition-colors">
        Create Your Own Passport
      </a>
    </div>
  )
}

function InactiveState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-5 text-center px-4">
      <div className="h-16 w-16 rounded-2xl bg-amber-50 flex items-center justify-center shadow-sm">
        <ShieldOff size={28} className="text-amber-400" />
      </div>
      <div>
        <div className="text-xl font-black text-slate-800">This passport is private</div>
        <div className="text-sm text-slate-400 mt-2 max-w-sm leading-relaxed">
          The owner has made this passport private or the share link has been revoked.
        </div>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-5 text-center px-4">
      <div className="h-16 w-16 rounded-2xl bg-slate-100 flex items-center justify-center shadow-sm">
        <AlertCircle size={28} className="text-slate-400" />
      </div>
      <div>
        <div className="text-xl font-black text-slate-800">Something went wrong</div>
        <div className="text-sm text-slate-400 mt-2 max-w-sm">{message}</div>
      </div>
    </div>
  )
}

// ─── Page Header ──────────────────────────────────────────────────────────────

function PageHeader({ passport, scrolled }: { passport?: PublicPassport; scrolled: boolean }) {
  return (
    <header className={`sticky top-0 z-20 transition-all duration-200 ${
      scrolled
        ? 'bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm'
        : 'bg-white/80 backdrop-blur-sm border-b border-transparent'
    }`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-sm">
            <FileText size={13} className="text-white" />
          </div>
          <span className="font-black text-slate-900 text-xs uppercase tracking-[0.15em]">TalentOS</span>
        </div>

        {/* Scrolled identity pill */}
        {scrolled && passport?.headline && (
          <div className="hidden sm:flex items-center gap-2 flex-1 min-w-0 max-w-xs">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-[9px] font-black shrink-0">
              {getInitials(passport)}
            </div>
            <span className="text-xs font-black text-slate-700 truncate">{passport.headline}</span>
          </div>
        )}

        {/* CTA */}
        <a
          href="/register/candidate"
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 transition-colors shadow-sm shrink-0"
        >
          <Sparkles size={10} />
          Create Your Passport
        </a>
      </div>
    </header>
  )
}

// ─── Hero Cover Band ──────────────────────────────────────────────────────────

function HeroCover({ passport }: { passport: PublicPassport }) {
  const initials = getInitials(passport)
  const location = [passport.current_location_city, passport.current_location_country].filter(Boolean).join(', ')

  const socialLinks = [
    { url: passport.linkedin_url, Icon: Linkedin, label: 'LinkedIn', color: 'hover:text-[#0A66C2]' },
    { url: passport.github_url, Icon: Github, label: 'GitHub', color: 'hover:text-slate-900' },
    { url: passport.portfolio_url, Icon: Globe, label: 'Portfolio', color: 'hover:text-emerald-600' },
    { url: passport.twitter_url, Icon: Twitter, label: 'Twitter / X', color: 'hover:text-sky-500' },
    { url: passport.behance_url, Icon: Layers, label: 'Behance', color: 'hover:text-blue-500' },
    { url: passport.dribbble_url, Icon: BookOpen, label: 'Dribbble', color: 'hover:text-pink-500' },
  ].filter(l => !!l.url)

  return (
    <div className="relative">
      {/* Cover strip */}
      <div
        className="h-36 sm:h-44 w-full rounded-2xl overflow-hidden"
        style={{
          background: passport.cover_image_url
            ? `url(${passport.cover_image_url}) center/cover no-repeat`
            : 'linear-gradient(135deg, #1e3a5f 0%, #1e40af 40%, #4f46e5 70%, #7c3aed 100%)',
        }}
      >
        {/* Subtle overlay for text contrast if cover image exists */}
        {passport.cover_image_url && (
          <div className="absolute inset-0 bg-gradient-to-b from-black/20 to-black/50 rounded-2xl" />
        )}
      </div>

      {/* Profile card floated over cover */}
      <div className="px-5 sm:px-8 -mt-12 sm:-mt-14 relative z-10">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-5 sm:p-7">
          <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 items-start sm:items-end">
            {/* Avatar */}
            <div className="-mt-12 sm:-mt-16 shrink-0">
              {passport.profile_photo_url ? (
                <img
                  src={passport.profile_photo_url}
                  alt="Profile"
                  className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl object-cover border-4 border-white shadow-xl"
                />
              ) : (
                <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-black border-4 border-white shadow-xl">
                  {initials}
                </div>
              )}
            </div>

            {/* Identity block */}
            <div className="flex-1 min-w-0 pt-1 sm:pt-0">
              {passport.headline && (
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 leading-snug">
                  {passport.headline}
                </h1>
              )}

              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                {(passport.current_title || passport.current_company) && (
                  <div className="flex items-center gap-1.5 text-sm text-slate-500 font-semibold">
                    <Building2 size={13} className="text-slate-400 shrink-0" />
                    {[passport.current_title, passport.current_company].filter(Boolean).join(' · ')}
                  </div>
                )}
                {location && (
                  <div className="flex items-center gap-1 text-sm text-slate-400">
                    <MapPin size={12} className="shrink-0" />
                    {location}
                  </div>
                )}
              </div>

              {/* Status badges */}
              <div className="flex flex-wrap items-center gap-2 mt-3">
                {passport.is_actively_looking && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-[9px] font-black uppercase tracking-widest text-emerald-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Actively Looking
                  </span>
                )}
                {passport.open_to_work && !passport.is_actively_looking && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-[9px] font-black uppercase tracking-widest text-blue-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                    Open to Work
                  </span>
                )}
                {passport.identity_verified && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-50 border border-violet-200 text-[9px] font-black uppercase tracking-widest text-violet-700">
                    <CheckCircle2 size={9} />
                    Identity Verified
                  </span>
                )}
                {passport.background_verified && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-50 border border-teal-200 text-[9px] font-black uppercase tracking-widest text-teal-700">
                    <CheckCircle2 size={9} />
                    Background Verified
                  </span>
                )}
                {passport.passport_number && (
                  <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-slate-100 text-[9px] font-bold text-slate-400 tracking-widest">
                    <Hash size={8} />
                    {passport.passport_number}
                  </span>
                )}
              </div>
            </div>

            {/* Social links — desktop right */}
            {socialLinks.length > 0 && (
              <div className="hidden sm:flex items-center gap-1.5 shrink-0 self-center">
                {socialLinks.map(({ url, Icon, label, color }) => (
                  <a
                    key={label}
                    href={url!}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={label}
                    className={`p-2 rounded-xl border border-slate-200 text-slate-400 transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm ${color}`}
                  >
                    <Icon size={15} />
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Social links — mobile below */}
          {socialLinks.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4 sm:hidden pt-4 border-t border-slate-100">
              {socialLinks.map(({ url, Icon, label, color }) => (
                <a
                  key={label}
                  href={url!}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-500 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all ${color}`}
                >
                  <Icon size={11} /> {label}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Key Metrics Strip ────────────────────────────────────────────────────────

function KeyMetricsBar({ passport }: { passport: PublicPassport }) {
  const metrics = [
    passport.experience_years != null && {
      icon: TrendingUp,
      value: `${passport.experience_years} yrs`,
      label: 'Experience',
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    workModeLabel(passport.preferred_work_mode) && {
      icon: MapPin,
      value: workModeLabel(passport.preferred_work_mode)!,
      label: 'Work Mode',
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    noticePeriodLabel(passport.notice_period_days) && {
      icon: CalendarDays,
      value: noticePeriodLabel(passport.notice_period_days)!,
      label: 'Availability',
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    (passport.skills?.length ?? 0) > 0 && {
      icon: Star,
      value: `${passport.skills!.length} Skills`,
      label: 'Expertise',
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    (passport.languages?.length ?? 0) > 0 && {
      icon: Languages,
      value: `${passport.languages!.length} Language${passport.languages!.length > 1 ? 's' : ''}`,
      label: 'Fluent In',
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
  ].filter(Boolean) as Array<{ icon: React.ElementType; value: string; label: string; color: string; bg: string }>

  if (!metrics.length) return null

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm px-5 py-4">
      <div className="flex flex-wrap gap-3 sm:gap-0 sm:divide-x sm:divide-slate-100">
        {metrics.map(({ icon: Icon, value, label, color, bg }, i) => (
          <div key={i} className="flex items-center gap-3 sm:px-5 first:sm:pl-0 last:sm:pr-0 min-w-[120px] flex-1">
            <div className={`h-9 w-9 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
              <Icon size={15} className={color} />
            </div>
            <div>
              <div className={`text-sm font-black ${color}`}>{value}</div>
              <div className="text-[9px] font-black uppercase tracking-widest text-slate-400">{label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Section Wrapper ──────────────────────────────────────────────────────────

function Section({ title, icon: Icon, accent, children }: {
  title: string
  icon: React.ElementType
  accent?: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className={`flex items-center gap-2.5 px-5 py-3.5 border-b border-slate-100 ${accent ?? ''}`}>
        <Icon size={14} className="text-slate-500" />
        <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-600">{title}</span>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

// ─── About Me ─────────────────────────────────────────────────────────────────

function AboutMe({ summary }: { summary: string }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-slate-100 bg-gradient-to-r from-blue-50/60 to-transparent">
        <FileText size={14} className="text-blue-500" />
        <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-600">About</span>
      </div>
      <div className="px-6 py-5 relative">
        <div className="absolute top-3 left-4 text-6xl leading-none text-blue-100 font-serif select-none">"</div>
        <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line relative z-10 pl-4">
          {summary}
        </p>
      </div>
    </div>
  )
}

// ─── Experience ───────────────────────────────────────────────────────────────

function ExperienceSection({ items }: { items: WorkItem[] }) {
  return (
    <Section title="Experience" icon={Briefcase}>
      <div className="flex flex-col gap-5">
        {items.map((item, i) => (
          <div key={item.id ?? i} className={`flex gap-4 ${i < items.length - 1 ? 'pb-5 border-b border-slate-100' : ''}`}>
            {/* Timeline dot */}
            <div className="relative flex flex-col items-center shrink-0 pt-1">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                <Building2 size={13} className="text-slate-500" />
              </div>
              {i < items.length - 1 && (
                <div className="w-px flex-1 bg-slate-100 mt-2 mb-[-20px]" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="text-sm font-black text-slate-800">{item.title ?? '—'}</div>
              <div className="text-[11px] font-semibold text-slate-500 mt-0.5">
                {item.company}
                {item.location ? ` · ${item.location}` : ''}
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-medium">
                <Clock size={9} />
                {formatDateRange(item.from_date, item.to_date, item.is_current)}
                {item.is_current && (
                  <span className="px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-[8px] font-black text-emerald-700 uppercase tracking-widest">
                    Current
                  </span>
                )}
              </div>
              {item.description && (
                <p className="mt-2 text-xs text-slate-500 leading-relaxed">{item.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Education ────────────────────────────────────────────────────────────────

function EducationSection({ items }: { items: EduItem[] }) {
  return (
    <Section title="Education" icon={GraduationCap}>
      <div className="flex flex-col gap-4">
        {items.map((item, i) => (
          <div key={item.id ?? i} className={`flex gap-4 ${i < items.length - 1 ? 'pb-4 border-b border-slate-100' : ''}`}>
            <div className="h-9 w-9 rounded-xl bg-violet-50 flex items-center justify-center shrink-0 mt-0.5">
              <GraduationCap size={14} className="text-violet-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-black text-slate-800">
                {item.degree}{item.field ? ` · ${item.field}` : ''}
              </div>
              <div className="text-[11px] font-semibold text-slate-500 mt-0.5">{item.institution}</div>
              <div className="flex items-center gap-2 mt-1">
                {item.year && (
                  <span className="text-[10px] font-medium text-slate-400">{item.year}</span>
                )}
                {item.grade && (
                  <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-[9px] font-black text-slate-600">
                    {item.grade}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Certifications ───────────────────────────────────────────────────────────

function CertificationsSection({ items }: { items: CertItem[] }) {
  return (
    <Section title="Certifications" icon={Award}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((item, i) => (
          <div key={item.id ?? i}
            className="flex items-center gap-3 p-3 rounded-xl bg-amber-50/50 border border-amber-100 hover:border-amber-200 transition-colors">
            <div className="h-9 w-9 rounded-xl bg-amber-100 flex items-center justify-center shrink-0">
              <Award size={14} className="text-amber-600" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] font-black text-slate-800 truncate">{item.name}</div>
              <div className="text-[10px] text-slate-400 font-medium">
                {item.issuer}{item.issued_date ? ` · ${dayjs(item.issued_date).format('MMM YYYY')}` : ''}
              </div>
            </div>
            {item.credential_url && (
              <a href={item.credential_url} target="_blank" rel="noopener noreferrer"
                className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-white transition-all shrink-0">
                <ExternalLink size={11} />
              </a>
            )}
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Projects ─────────────────────────────────────────────────────────────────

function ProjectsSection({ items }: { items: ProjectItem[] }) {
  return (
    <Section title="Projects & Portfolio" icon={Code2}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {items.map((item, i) => (
          <div key={item.id ?? i}
            className="flex flex-col gap-2 p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-200 hover:bg-blue-50/30 transition-all group">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-lg bg-white border border-slate-200 flex items-center justify-center shrink-0 group-hover:border-blue-200 transition-colors">
                  <Layers size={12} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
                </div>
                <div className="text-sm font-black text-slate-800">{item.name}</div>
              </div>
              {item.url && (
                <a href={item.url} target="_blank" rel="noopener noreferrer"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-white transition-all shrink-0">
                  <ChevronRight size={12} />
                </a>
              )}
            </div>
            {item.description && (
              <p className="text-[11px] text-slate-500 leading-relaxed">{item.description}</p>
            )}
            {(item.skills?.length ?? 0) > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {item.skills!.map(s => (
                  <span key={s} className="px-1.5 py-0.5 rounded bg-blue-100 text-[9px] font-black text-blue-700">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Publications ─────────────────────────────────────────────────────────────

function PublicationsSection({ items }: { items: PublicationItem[] }) {
  return (
    <Section title="Publications" icon={BookMarked}>
      <div className="flex flex-col gap-4">
        {items.map((item, i) => (
          <div key={item.id ?? i} className={`flex gap-4 ${i < items.length - 1 ? 'pb-4 border-b border-slate-100' : ''}`}>
            <div className="h-9 w-9 rounded-xl bg-blue-50 flex items-center justify-center shrink-0 mt-0.5">
              <BookMarked size={14} className="text-blue-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-black text-slate-800">{item.title}</div>
              {item.publisher && (
                <div className="text-[11px] font-semibold text-slate-500 mt-0.5">{item.publisher}</div>
              )}
              {item.published_date && (
                <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-medium">
                  <Clock size={9} />
                  {dayjs(item.published_date).format('MMM YYYY')}
                </div>
              )}
              {item.description && (
                <p className="mt-2 text-xs text-slate-500 leading-relaxed">{item.description}</p>
              )}
              {item.url && (
                <a href={item.url} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-[10px] text-blue-600 hover:text-blue-800 hover:underline font-semibold">
                  Read Publication <ExternalLink size={9} />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Awards ───────────────────────────────────────────────────────────────────

function AwardsSection({ items }: { items: AwardItem[] }) {
  return (
    <Section title="Awards & Recognition" icon={Award}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((item, i) => (
          <div key={item.id ?? i}
            className="flex items-start gap-3 p-3 rounded-xl bg-amber-50/50 border border-amber-100 hover:border-amber-200 transition-colors">
            <div className="h-9 w-9 rounded-xl bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
              <Award size={14} className="text-amber-600" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] font-black text-slate-800">{item.title}</div>
              {item.issuer && (
                <div className="text-[10px] text-slate-500 font-medium mt-0.5">{item.issuer}</div>
              )}
              {item.date && (
                <div className="text-[10px] text-slate-400 mt-0.5">{dayjs(item.date).format('MMM YYYY')}</div>
              )}
              {item.description && (
                <p className="text-[10px] text-slate-500 leading-relaxed mt-1">{item.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Volunteer Work ───────────────────────────────────────────────────────────

function VolunteerSection({ items }: { items: VolunteerItem[] }) {
  return (
    <Section title="Volunteer Work" icon={Heart}>
      <div className="flex flex-col gap-5">
        {items.map((item, i) => (
          <div key={item.id ?? i} className={`flex gap-4 ${i < items.length - 1 ? 'pb-5 border-b border-slate-100' : ''}`}>
            <div className="h-8 w-8 rounded-xl bg-rose-50 flex items-center justify-center shrink-0 mt-0.5">
              <Heart size={13} className="text-rose-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-black text-slate-800">{item.role ?? '—'}</div>
              <div className="text-[11px] font-semibold text-slate-500 mt-0.5">{item.organisation}</div>
              {(item.from_date || item.to_date || item.is_current) && (
                <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-medium">
                  <Clock size={9} />
                  {formatDateRange(item.from_date ?? undefined, item.to_date, item.is_current)}
                </div>
              )}
              {item.description && (
                <p className="mt-2 text-xs text-slate-500 leading-relaxed">{item.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Video Intro ──────────────────────────────────────────────────────────────

function VideoIntroSection({ url }: { url: string }) {
  const videoInfo = isVideoEmbeddable(url)

  return (
    <Section title="Video Introduction" icon={Play}>
      {videoInfo.embedUrl ? (
        <div className="relative aspect-video w-full rounded-xl overflow-hidden bg-black shadow-sm">
          <iframe
            src={videoInfo.embedUrl}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="absolute inset-0 w-full h-full"
            title="Video Introduction"
          />
        </div>
      ) : (
        <a href={url} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all group">
          <div className="h-10 w-10 rounded-xl bg-blue-100 flex items-center justify-center shrink-0 group-hover:bg-blue-200 transition-colors">
            <Play size={16} className="text-blue-600 ml-0.5" />
          </div>
          <div>
            <div className="text-sm font-black text-slate-700 group-hover:text-blue-700 transition-colors">
              Watch Video Introduction
            </div>
            <div className="text-[10px] text-slate-400 font-medium truncate max-w-xs">{url}</div>
          </div>
          <ExternalLink size={14} className="text-slate-300 group-hover:text-blue-400 ml-auto shrink-0 transition-colors" />
        </a>
      )}
    </Section>
  )
}

// ─── Resume / CV ──────────────────────────────────────────────────────────────

function ResumeSection({ url }: { url: string }) {
  return (
    <Section title="Resume / CV" icon={FileText}>
      <a href={url} target="_blank" rel="noopener noreferrer"
        className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 hover:border-blue-400 hover:shadow-sm transition-all group">
        <div className="h-12 w-12 rounded-xl bg-white border border-blue-200 flex items-center justify-center shrink-0 shadow-sm group-hover:shadow transition-shadow">
          <FileText size={18} className="text-blue-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-black text-slate-800 group-hover:text-blue-700 transition-colors">
            View / Download Resume
          </div>
          <div className="text-[10px] text-slate-400 font-medium mt-0.5">
            Click to open in a new tab
          </div>
        </div>
        <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest shrink-0 group-hover:bg-blue-700 transition-colors">
          <Download size={10} />
          CV
        </div>
      </a>
    </Section>
  )
}

// ─── Custom Fields ────────────────────────────────────────────────────────────

function isUrl(value: string): boolean {
  try { return /^https?:\/\//i.test(value) } catch { return false }
}

function toLabel(key: string): string {
  return key
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, c => c.toUpperCase())
    .trim()
}

function CustomFieldValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === '') return null

  if (Array.isArray(value)) {
    const items = value.filter(v => v !== null && v !== undefined && v !== '')
    if (!items.length) return null
    return (
      <div className="flex flex-wrap gap-1.5 mt-0.5">
        {items.map((item, i) => (
          <span key={i} className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-[10px] font-black text-slate-600">
            {String(item)}
          </span>
        ))}
      </div>
    )
  }

  if (typeof value === 'boolean') {
    return (
      <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest ${
        value ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
               : 'bg-slate-100 border border-slate-200 text-slate-500'
      }`}>
        {value ? 'Yes' : 'No'}
      </span>
    )
  }

  const str = String(value)
  if (typeof value === 'string' && isUrl(str)) {
    return (
      <a href={str} target="_blank" rel="noopener noreferrer"
        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium break-all">
        {str} <ExternalLink size={10} className="shrink-0" />
      </a>
    )
  }

  return <span className="text-xs text-slate-700 font-medium">{str}</span>
}

function CustomFieldsSection({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata).filter(([key, val]) => {
    if (METADATA_SKIP_KEYS.has(key)) return false
    if (val === null || val === undefined || val === '') return false
    if (Array.isArray(val) && val.length === 0) return false
    if (typeof val === 'object' && !Array.isArray(val)) return false // skip nested objects
    return true
  })

  if (!entries.length) return null

  return (
    <Section title="Additional Information" icon={Sparkles}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {entries.map(([key, value]) => (
          <div key={key} className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">
              {toLabel(key)}
            </div>
            <CustomFieldValue value={value} />
          </div>
        ))}
      </div>
    </Section>
  )
}

// ─── Sidebar (Skills + Languages + Stats) ────────────────────────────────────

function ProfileSidebar({ passport }: { passport: PublicPassport }) {
  const hasSkills = (passport.skills?.length ?? 0) > 0
  const hasLanguages = (passport.languages?.length ?? 0) > 0
  const hasScore = (passport.completeness_score ?? 0) > 0 || (passport.heat_score ?? 0) > 0

  if (!hasSkills && !hasLanguages && !hasScore) return null

  return (
    <aside className="flex flex-col gap-4">
      {/* Skills */}
      {hasSkills && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Star size={13} className="text-amber-500" />
            <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-500">Skills</span>
            <span className="ml-auto text-[10px] font-black text-slate-300">{passport.skills!.length}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {passport.skills!.map(s => (
              <span key={s}
                className="px-2 py-0.5 rounded-lg bg-blue-50 border border-blue-100 text-[10px] font-black text-blue-700 hover:bg-blue-100 transition-colors cursor-default">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Languages */}
      {hasLanguages && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Languages size={13} className="text-rose-500" />
            <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-500">Languages</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {passport.languages!.map(l => (
              <span key={l}
                className="px-2 py-0.5 rounded-lg bg-rose-50 border border-rose-100 text-[10px] font-black text-rose-700">
                {l}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Passport Score */}
      {hasScore && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={13} className="text-slate-400" />
            <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-500">Passport Score</span>
          </div>
          {(passport.completeness_score ?? 0) > 0 && (
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-slate-400 font-semibold">Profile Completeness</span>
                <span className="text-[11px] font-black text-slate-700">{passport.completeness_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all"
                  style={{ width: `${passport.completeness_score}%` }}
                />
              </div>
            </div>
          )}
          {(passport.heat_score ?? 0) > 0 && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-slate-400 font-semibold">Market Demand</span>
                <span className="text-[11px] font-black text-slate-700">{passport.heat_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-500 transition-all"
                  style={{ width: `${passport.heat_score}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </aside>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PublicPassportPage() {
  const { token } = useParams<{ token: string }>()
  const [state, setState] = useState<PageState>({ status: 'loading' })
  const [scrolled, setScrolled] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = document.documentElement
    const handler = () => setScrolled(el.scrollTop > 60)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  useEffect(() => {
    if (!token) { setState({ status: 'not_found' }); return }

    passportApi.getPublic(token)
      .then((res: any) => {
        const passport: PublicPassport = res?.data?.data?.passport ?? res?.data?.passport
        if (!passport) { setState({ status: 'not_found' }); return }
        setState({ status: 'success', passport })
      })
      .catch((err: any) => {
        const status = err?.response?.status
        if (status === 404) setState({ status: 'not_found' })
        else if (status === 403) setState({ status: 'inactive' })
        else setState({ status: 'error', message: 'Failed to load this passport. Please try again later.' })
      })
  }, [token])

  const passport = state.status === 'success' ? state.passport : undefined

  return (
    <div className="min-h-screen bg-[#F1F4F9]" ref={scrollRef}>
      <PageHeader passport={passport} scrolled={scrolled} />

      <main className="max-w-6xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8">
        {state.status === 'loading' && <LoadingState />}
        {state.status === 'not_found' && <NotFoundState />}
        {state.status === 'inactive' && <InactiveState />}
        {state.status === 'error' && <ErrorState message={state.message} />}

        {state.status === 'success' && (() => {
          const { passport } = state
          const hasSummary      = !!passport.summary?.trim()
          const hasExperience   = (passport.work_history?.length ?? 0) > 0
          const hasEducation    = (passport.education?.length ?? 0) > 0
          const hasCerts        = (passport.certifications?.length ?? 0) > 0
          const hasProjects     = (passport.projects?.length ?? 0) > 0
          const hasPublications = (passport.publications?.length ?? 0) > 0
          const hasAwards       = (passport.awards?.length ?? 0) > 0
          const hasVolunteer    = (passport.volunteer_work?.length ?? 0) > 0
          const hasVideo        = !!passport.video_intro_url?.trim()
          const hasCv           = !!passport.current_cv_url?.trim()
          const hasCustomFields = !!passport.metadata &&
                                  typeof passport.metadata === 'object' &&
                                  !Array.isArray(passport.metadata) &&
                                  Object.keys(passport.metadata).length > 0
          const hasSidebar      = (passport.skills?.length ?? 0) > 0 ||
                                  (passport.languages?.length ?? 0) > 0 ||
                                  (passport.completeness_score ?? 0) > 0
          const hasAnyMetric    = passport.experience_years != null ||
                                  !!passport.preferred_work_mode ||
                                  passport.notice_period_days != null ||
                                  (passport.skills?.length ?? 0) > 0 ||
                                  (passport.languages?.length ?? 0) > 0
          const hasAnyContent   = hasSummary || hasExperience || hasEducation || hasCerts || hasProjects || hasPublications || hasAwards || hasVolunteer || hasVideo || hasCv || hasCustomFields

          return (
            <div className="flex flex-col gap-5">
              {/* Hero */}
              <HeroCover passport={passport} />

              {/* Key metrics strip */}
              {hasAnyMetric && <KeyMetricsBar passport={passport} />}

              {/* Body */}
              <div className={`grid gap-5 items-start ${hasSidebar ? 'grid-cols-1 lg:grid-cols-[280px_1fr]' : 'grid-cols-1'}`}>

                {/* Left sidebar */}
                {hasSidebar && <ProfileSidebar passport={passport} />}

                {/* Main content */}
                <div className="flex flex-col gap-4 min-w-0">
                  {hasSummary && <AboutMe summary={passport.summary!} />}
                  {hasExperience && <ExperienceSection items={passport.work_history!} />}
                  {hasEducation && <EducationSection items={passport.education!} />}
                  {hasCerts && <CertificationsSection items={passport.certifications!} />}
                  {hasProjects && <ProjectsSection items={passport.projects!} />}
                  {hasPublications && <PublicationsSection items={passport.publications!} />}
                  {hasAwards && <AwardsSection items={passport.awards!} />}
                  {hasVolunteer && <VolunteerSection items={passport.volunteer_work!} />}
                  {hasVideo && <VideoIntroSection url={passport.video_intro_url!} />}
                  {hasCv && <ResumeSection url={passport.current_cv_url!} />}
                  {hasCustomFields && <CustomFieldsSection metadata={passport.metadata!} />}

                  {/* Empty state — only if absolutely nothing */}
                  {!hasAnyContent && (
                    <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                      <div className="h-12 w-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                        <FileText size={20} className="text-slate-300" />
                      </div>
                      <div className="text-slate-400 text-xs font-black uppercase tracking-widest">
                        Profile details not yet added
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="text-center py-8 mt-2">
                <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white border border-slate-200 shadow-sm">
                  <div className="h-4 w-4 rounded bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center">
                    <FileText size={8} className="text-white" />
                  </div>
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                    Powered by TalentOS ·{' '}
                    <a href="/register/candidate" className="text-blue-500 hover:text-blue-700 transition-colors">
                      Create Your Talent Passport
                    </a>
                  </span>
                </div>
              </div>
            </div>
          )
        })()}
      </main>
    </div>
  )
}
