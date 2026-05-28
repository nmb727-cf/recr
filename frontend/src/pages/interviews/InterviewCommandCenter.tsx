import { useState, useMemo } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Table, Tag, Form, Typography, Avatar, Modal, message,
  Select, Input, InputNumber, Tooltip, Switch, DatePicker,
} from 'antd'
import {
  // Nav / Layout
  Home, List, LayoutGrid, Database, ClipboardList, BarChart2,
  // Actions
  Plus, X, RefreshCw, Search, ChevronRight, ArrowRight, ExternalLink,
  // Status / data
  Activity, CheckCircle2, Play, Calendar, Clock, AlertCircle, TrendingUp, Flag,
  // Interview types — core
  Video, Monitor, Phone, MessageSquare, Film, MonitorPlay,
  // Interview types — technical
  Code, Code2, Share2, AlertTriangle, Pencil, Network,
  // Interview types — people
  Users, UserCheck, Heart, Briefcase, Award, Brain,
  // Interview types — special
  Shield, GraduationCap, DoorOpen, Wand2, CheckSquare, Globe,
  // Misc
  GitBranch, Zap, Layers, FileText, Building2, Target, Settings2, Cpu, Workflow,
  Link,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { interviewsApi } from '@/api/interviews'
import { prequalificationApi } from '@/api/prequalification'
import type { Interview } from '@/types'
import { cn } from '@/utils/cn'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import InterviewScorecards from '@/pages/interviews/InterviewScorecards'
import InterviewSchedulingEngine from '@/pages/interviews/InterviewSchedulingEngine'
import InterviewAutomation from '@/pages/interviews/InterviewAutomation'
import InterviewLiveCenter from '@/pages/interviews/InterviewLiveCenter'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'
import { getCategoryOptions, getInterviewTypeCategory, getInterviewTypeLabel, INTERVIEW_TYPE_CATEGORIES, type InterviewTypeCategory } from '@/utils/interviewTypeUx'

dayjs.extend(relativeTime)
const { Title, Text, Paragraph } = Typography

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION TYPES & NAV CONFIG
// ═══════════════════════════════════════════════════════════════════════════════

type ActiveSection =
  | 'home' | 'flows' | 'types' | 'scorecards' | 'templates'
  | 'prequalification' | 'skill-matching' | 'scheduling' | 'live' | 'automation' | 'operations' | 'analytics'

const NAV_ITEMS: { key: ActiveSection; label: string; icon: React.ElementType; desc: string; badge?: string }[] = [
  { key: 'home',             label: 'Dashboard',         icon: Home,          desc: 'Interview operations dashboard' },
  { key: 'flows',            label: 'Interview Flows',   icon: GitBranch,     desc: 'Multi-stage pipelines' },
  { key: 'types',            label: 'Types Registry',    icon: Database,      desc: '40 interview engines', badge: '40' },
  { key: 'scorecards',       label: 'Scorecards',        icon: ClipboardList, desc: 'Reusable evaluation system' },
  { key: 'templates',        label: 'Templates',         icon: LayoutGrid,    desc: 'Reusable configs' },
  { key: 'scheduling',       label: 'Scheduling',        icon: Calendar,      desc: 'Flexible scheduling engine' },
  { key: 'live',             label: 'Live Interviews',   icon: MonitorPlay,   desc: 'Real-time interview execution' },
  { key: 'automation',       label: 'Automation',        icon: Workflow,      desc: 'Rule-based workflow engine' },
  { key: 'prequalification', label: 'Pre-Qualification', icon: ClipboardList, desc: 'Forms & knockout rules' },
  { key: 'skill-matching',   label: 'Skill Matching',    icon: Zap,           desc: 'Fit score & routing' },
  { key: 'operations',       label: 'Operations',        icon: List,          desc: 'All interviews + actions' },
  { key: 'analytics',        label: 'Analytics',         icon: BarChart2,     desc: 'Funnel & performance' },
]

// ═══════════════════════════════════════════════════════════════════════════════
// 40-TYPE ENGINE REGISTRY
// ═══════════════════════════════════════════════════════════════════════════════

type EngineEntry = { icon: React.ElementType; color: string; bg: string; desc: string; category: string }

const ENGINE_REGISTRY: Record<string, EngineEntry> = {
  // ── Screening (3) ─────────────────────────────────────────────────────────
  recruiter_screening:      { icon: UserCheck,    color: 'text-green-600',   bg: 'bg-green-50',   desc: 'Initial recruiter-led qualification call',         category: 'Screening' },
  ai_screening:             { icon: Cpu,          color: 'text-purple-600',  bg: 'bg-purple-50',  desc: 'Automated AI-driven candidate screening',          category: 'Screening' },
  phone_interview:          { icon: Phone,        color: 'text-slate-600',   bg: 'bg-slate-100',  desc: 'Structured phone-based interview',                 category: 'Screening' },

  // ── Video (3) ─────────────────────────────────────────────────────────────
  one_way_video:            { icon: Video,        color: 'text-blue-600',    bg: 'bg-blue-50',    desc: 'Candidate records async video responses',          category: 'Video' },
  prerecorded_video:        { icon: MonitorPlay,  color: 'text-indigo-600',  bg: 'bg-indigo-50',  desc: 'Pre-recorded questions delivered to candidate',    category: 'Video' },
  live_video:               { icon: Monitor,      color: 'text-sky-600',     bg: 'bg-sky-50',     desc: 'Real-time synchronous video interview',            category: 'Video' },

  // ── Async (1) ─────────────────────────────────────────────────────────────
  async_text_interview:     { icon: MessageSquare,color: 'text-teal-600',    bg: 'bg-teal-50',    desc: 'Text-based async Q&A via chat interface',          category: 'Async' },

  // ── Technical (7) ─────────────────────────────────────────────────────────
  technical_interview:      { icon: Settings2,    color: 'text-emerald-600', bg: 'bg-emerald-50', desc: 'Deep technical skills and domain knowledge probe', category: 'Technical' },
  coding_interview:         { icon: Code,         color: 'text-green-700',   bg: 'bg-green-50',   desc: 'Live or recorded coding challenge',                category: 'Technical' },
  system_design:            { icon: Network,      color: 'text-cyan-600',    bg: 'bg-cyan-50',    desc: 'Architecture and system design evaluation',        category: 'Technical' },
  take_home_assignment:     { icon: FileText,     color: 'text-amber-600',   bg: 'bg-amber-50',   desc: 'Offline project or assignment submission',         category: 'Assessment' },
  debugging_interview:      { icon: AlertTriangle,color: 'text-red-600',     bg: 'bg-red-50',     desc: 'Find and fix bugs in provided codebase',           category: 'Technical' },
  whiteboard_interview:     { icon: Pencil,       color: 'text-orange-600',  bg: 'bg-orange-50',  desc: 'Problem-solving on shared whiteboard',             category: 'Technical' },
  technical_panel:          { icon: Code2,        color: 'text-blue-700',    bg: 'bg-blue-50',    desc: 'Multiple technical interviewers in session',       category: 'Technical' },

  // ── Behavioral (2) ────────────────────────────────────────────────────────
  behavioral_interview:     { icon: Brain,        color: 'text-violet-600',  bg: 'bg-violet-50',  desc: 'STAR-based past behavior assessment',              category: 'Behavioral' },
  cultural_fit:             { icon: Heart,        color: 'text-pink-600',    bg: 'bg-pink-50',    desc: 'Values alignment and culture assessment',          category: 'Behavioral' },

  // ── HR / People (4) ───────────────────────────────────────────────────────
  hr_interview:             { icon: UserCheck,    color: 'text-indigo-600',  bg: 'bg-indigo-50',  desc: 'HR-led competency and culture discussion',         category: 'HR' },
  leadership_interview:     { icon: TrendingUp,   color: 'text-amber-600',   bg: 'bg-amber-50',   desc: 'Leadership capability and style evaluation',       category: 'HR' },
  executive_interview:      { icon: Award,        color: 'text-yellow-600',  bg: 'bg-yellow-50',  desc: 'C-suite or VP level strategic discussion',         category: 'HR' },
  hiring_manager_interview: { icon: Briefcase,    color: 'text-slate-600',   bg: 'bg-slate-100',  desc: 'Direct hiring manager qualification round',        category: 'HR' },

  // ── Panel / Group (6) ─────────────────────────────────────────────────────
  panel_interview:          { icon: Users,        color: 'text-indigo-600',  bg: 'bg-indigo-50',  desc: 'Multiple interviewers evaluating simultaneously',  category: 'Panel' },
  sequential_round:         { icon: List,         color: 'text-blue-600',    bg: 'bg-blue-50',    desc: 'Multiple one-on-ones in sequence',                 category: 'Panel' },
  stakeholder_interview:    { icon: Link,         color: 'text-teal-600',    bg: 'bg-teal-50',    desc: 'Interview with cross-functional stakeholders',     category: 'Panel' },
  bar_raiser:               { icon: BarChart2,    color: 'text-emerald-600', bg: 'bg-emerald-50', desc: 'Amazon-style raising-the-bar evaluation',          category: 'Panel' },
  final_round:              { icon: Flag,         color: 'text-red-600',     bg: 'bg-red-50',     desc: 'Final decision-making round interview',            category: 'Panel' },
  group_discussion:         { icon: Users,        color: 'text-teal-600',    bg: 'bg-teal-50',    desc: 'Group candidate interaction and assessment',        category: 'Panel' },

  // ── Assessment (5) ────────────────────────────────────────────────────────
  mcq_assessment:           { icon: CheckSquare,  color: 'text-blue-600',    bg: 'bg-blue-50',    desc: 'Multiple choice knowledge assessment',              category: 'Assessment' },
  aptitude_test:            { icon: Brain,        color: 'text-purple-600',  bg: 'bg-purple-50',  desc: 'Numerical, verbal and abstract reasoning',          category: 'Assessment' },
  psychometric_test:        { icon: Activity,     color: 'text-amber-600',   bg: 'bg-amber-50',   desc: 'Personality and cognitive trait evaluation',        category: 'Assessment' },
  cognitive_test:           { icon: Cpu,          color: 'text-indigo-600',  bg: 'bg-indigo-50',  desc: 'Cognitive ability and mental agility test',         category: 'Assessment' },
  language_assessment:      { icon: Globe,        color: 'text-teal-600',    bg: 'bg-teal-50',    desc: 'Language proficiency and communication test',       category: 'Assessment' },

  // ── Simulation (5) ────────────────────────────────────────────────────────
  case_study:               { icon: FileText,     color: 'text-rose-600',    bg: 'bg-rose-50',    desc: 'Structured problem-solving with real data',         category: 'Simulation' },
  role_play:                { icon: Wand2,        color: 'text-orange-600',  bg: 'bg-orange-50',  desc: 'Simulated real-world scenario acting',              category: 'Simulation' },
  work_sample_test:         { icon: ClipboardList,color: 'text-green-600',   bg: 'bg-green-50',   desc: 'Actual job task performance sample',                category: 'Simulation' },
  presentation_interview:   { icon: Monitor,      color: 'text-blue-600',    bg: 'bg-blue-50',    desc: 'Prepared topic or project presentation',            category: 'Simulation' },
  portfolio_review:         { icon: Layers,       color: 'text-indigo-600',  bg: 'bg-indigo-50',  desc: 'Review and discuss candidate portfolio work',       category: 'Simulation' },

  // ── Special Formats (5) ───────────────────────────────────────────────────
  assessment_center:        { icon: Building2,    color: 'text-slate-600',   bg: 'bg-slate-100',  desc: 'Full-day multi-exercise assessment event',          category: 'Special' },
  mock_interview:           { icon: Shield,       color: 'text-gray-500',    bg: 'bg-gray-100',   desc: 'Practice/preparation interview simulation',         category: 'Special' },
  campus_hiring:            { icon: GraduationCap,color: 'text-violet-600',  bg: 'bg-violet-50',  desc: 'University campus recruitment drive',               category: 'Special' },
  walkin_drive:             { icon: DoorOpen,     color: 'text-amber-600',   bg: 'bg-amber-50',   desc: 'Open walk-in interview event for high-volume',      category: 'Special' },
}

// ─── Type options list (for selects) ──────────────────────────────────────────
const TYPE_SELECT_OPTIONS = Object.entries(ENGINE_REGISTRY).map(([code]) => ({
  value: code,
  label: getInterviewTypeLabel(code),
  category: getInterviewTypeCategory(code),
}))

const MODE_OPTIONS = [
  { value: 'native',          label: 'Native (TOS)' },
  { value: 'third_party',     label: 'Third-Party Integration' },
  { value: 'external_manual', label: 'External / Manual' },
]

const AI_ENGINE_CODES = new Set([
  'ai_screening',
  'one_way_video',
  'prerecorded_video',
  'async_text_interview',
])

const TECHNICAL_ENGINE_CODES = new Set([
  'technical_interview',
  'coding_interview',
  'system_design',
  'debugging_interview',
  'technical_panel',
])

const HUMAN_ENGINE_CODES = new Set([
  'hr_interview',
  'hiring_manager',
  'hiring_manager_interview',
  'behavioral',
  'behavioral_interview',
  'panel',
  'panel_interview',
  'stakeholder',
  'stakeholder_interview',
  'final_round',
  'leadership',
  'leadership_interview',
  'executive',
  'executive_interview',
  'culture_fit',
  'cultural_fit',
])

const ASSESSMENT_ENGINE_CODES = new Set([
  'mcq_assessment',
  'aptitude',
  'aptitude_test',
  'case_study',
  'take_home_assignment',
  'work_sample',
  'work_sample_test',
  'language',
  'language_assessment',
  'cognitive',
  'cognitive_test',
  'cognitive_assessment',
  'psychometric',
  'psychometric_test',
  'psychometric_assessment',
  'file_submission_assignment',
])

const PREQUALIFICATION_ENGINE_CODES = new Set([
  'eligibility_screening',
])

const SCREENING_ENGINE_CODES = new Set([
  'recruiter_screening',
  'phone_interview',
])

type RegistryDevelopmentStatus = 'built' | 'partial' | 'not_developed'

function getRegistryDevelopment(typeCode: string) {
  if (SCREENING_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Screening Interview Engine',
      route: `/interviews/screening?type=${typeCode}`,
      notes: 'Routes into the screening interview engine.',
    }
  }

  if (typeCode === 'prerecorded_video') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Video Interview Engine',
      route: '/interviews/video?type=prerecorded_video',
      notes: 'Routes into the dedicated video interview engine.',
    }
  }

  if (typeCode === 'live_video') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Video Interview Engine',
      route: '/interviews/video?type=live_video',
      notes: 'Routes into the dedicated video interview engine.',
    }
  }

  if (typeCode === 'whiteboard_interview') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Whiteboard Interview Engine',
      route: '/interviews/whiteboard?type=whiteboard_interview',
      notes: 'Routes into the dedicated whiteboard interview engine.',
    }
  }

  if (typeCode === 'sequential_round') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Sequential Round Interview Engine',
      route: '/interviews/sequential-round?type=sequential_round',
      notes: 'Routes into the dedicated sequential round engine.',
    }
  }

  if (typeCode === 'group_discussion') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Group Discussion Interview Engine',
      route: '/interviews/group-discussion?type=group_discussion',
      notes: 'Routes into the dedicated group discussion engine.',
    }
  }

  if (typeCode === 'bar_raiser') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Bar Raiser Interview Engine',
      route: '/interviews/bar-raiser?type=bar_raiser',
      notes: 'Routes into the dedicated bar raiser interview engine.',
    }
  }

  if (typeCode === 'role_play') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Role Play Interview Engine',
      route: '/interviews/role-play?type=role_play',
      notes: 'Routes into the dedicated role play engine.',
    }
  }

  if (typeCode === 'presentation_interview') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Presentation Interview Engine',
      route: '/interviews/presentation-interview?type=presentation_interview',
      notes: 'Routes into the dedicated presentation interview engine.',
    }
  }

  if (typeCode === 'portfolio_review') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Portfolio Review Interview Engine',
      route: '/interviews/portfolio-review?type=portfolio_review',
      notes: 'Routes into the dedicated portfolio review engine.',
    }
  }

  if (typeCode === 'assessment_center') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Assessment Center Engine',
      route: '/interviews/assessment-center?type=assessment_center',
      notes: 'Routes into the dedicated assessment center engine.',
    }
  }

  if (typeCode === 'walkin_drive') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Walk-in Drive Engine',
      route: '/interviews/walkin-drive?type=walkin_drive',
      notes: 'Routes into the dedicated walk-in drive engine.',
    }
  }

  if (typeCode === 'campus_hiring') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Campus Hiring Engine',
      route: '/interviews/campus-hiring?type=campus_hiring',
      notes: 'Routes into the dedicated campus hiring engine.',
    }
  }

  if (typeCode === 'mock_interview') {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Mock Interview Engine',
      route: '/interviews/mock-interview?type=mock_interview',
      notes: 'Routes into the dedicated mock interview engine.',
    }
  }

  if (AI_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'AI Interview Engine',
      route: `/interviews/ai?type=${typeCode}`,
      notes: 'Routes into the AI interview engine.',
    }
  }

  if (TECHNICAL_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Technical Interview Engine',
      route: `/interviews/technical?type=${typeCode}`,
      notes: 'Routes into the technical interview engine.',
    }
  }

  if (HUMAN_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Human Interview Engine',
      route: `/interviews/human?type=${typeCode}`,
      notes: 'Routes into the human interview engine.',
    }
  }

  if (ASSESSMENT_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Assessment Engine',
      route: `/interviews/assessments?type=${typeCode}`,
      notes: 'Routes into the assessment engine.',
    }
  }

  if (PREQUALIFICATION_ENGINE_CODES.has(typeCode)) {
    return {
      status: 'built' as RegistryDevelopmentStatus,
      badge: 'Built',
      intendedEngine: 'Prequalification Engine',
      route: `/interviews/prequalification?type=${typeCode}`,
      notes: 'Routes into the prequalification engine.',
    }
  }

  return {
    status: 'not_developed' as RegistryDevelopmentStatus,
    badge: 'Not Developed',
    intendedEngine: 'Future Type-Specific Engine',
    route: null,
    notes: 'This registry item is visible but does not yet have a dedicated engine.',
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SHARED SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

function StatCard({ label, value, icon: Icon, color, bg }: {
  label: string; value: number | string; icon: React.ElementType; color: string; bg: string
}) {
  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-soft-sm flex items-center gap-4">
      <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center shrink-0', bg, color)}>
        <Icon size={20} />
      </div>
      <div>
        <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-0.5">{label}</Text>
        <Text className="block font-black text-slate-900 text-xl leading-none">{value}</Text>
      </div>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, subtitle, action }: {
  icon: React.ElementType; title: string; subtitle?: string; action?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-soft-sm shadow-indigo-100">
          <Icon size={17} />
        </div>
        <div>
          <h2 className="text-sm font-black text-slate-900 uppercase tracking-tight leading-none">{title}</h2>
          {subtitle && <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{subtitle}</Text>}
        </div>
      </div>
      {action}
    </div>
  )
}

function EmptyState({ icon: Icon, title, subtitle, cta, onCta }: {
  icon: React.ElementType; title: string; subtitle?: string; cta?: string; onCta?: () => void
}) {
  return (
    <div className="py-16 text-center bg-white rounded-2xl border border-dashed border-slate-200">
      <Icon className="h-10 w-10 text-slate-200 mx-auto mb-3" />
      <Text className="block font-black text-slate-400 uppercase tracking-widest text-sm mb-1">{title}</Text>
      {subtitle && <Text className="block text-slate-300 text-xs font-bold mb-5">{subtitle}</Text>}
      {cta && onCta && (
        <button onClick={onCta}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 active:scale-95 transition-all">
          <Plus size={13} /> {cta}
        </button>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// INTERVIEW DETAIL DRAWER
// ═══════════════════════════════════════════════════════════════════════════════

function InterviewDetailDrawer({ interview, onClose }: { interview: Interview; onClose: () => void }) {
  const { data: detailData } = useApiQuery(
    ['interview-detail-cc', interview?.id],
    () => interviewsApi.get(interview.id),
    { enabled: !!interview?.id }
  )
  const panelists = (detailData as any)?.panelists ?? []
  const decision = (detailData as any)?.interview?.decision

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/90 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Avatar size={44} className="bg-indigo-600 text-white font-bold border-none shadow-soft-md">
            {interview.candidate_id?.charAt(0).toUpperCase() || 'I'}
          </Avatar>
          <div>
            <div className="flex items-center gap-3 mb-0.5">
              <Title level={4} className="!m-0 text-slate-900">Interview Details</Title>
              <Tag color={getStatusStyle(interview.status, 'application').antColor}
                className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                {formatStatusLabel(interview.status)}
              </Tag>
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              Round {interview.interview_round} · {formatStatusLabel(interview.interview_type)}
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a href={`/interviews/${interview.id}/kit`} className="rounded-lg border border-slate-200 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-indigo-600 hover:bg-indigo-50">Kit</a>
          <a href={`/interviews/${interview.id}/feedback`} className="rounded-lg border border-slate-200 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-indigo-600 hover:bg-indigo-50">Feedback</a>
          <button onClick={onClose}
            className="h-9 w-9 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:bg-slate-50">
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
            <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Schedule</Text>
            <div className="flex items-center gap-2 mb-1.5">
              <Calendar className="h-3.5 w-3.5 text-indigo-600" />
              <Text className="font-bold text-slate-700 text-xs">
                {interview.scheduled_at ? dayjs(interview.scheduled_at).format('MMM D, YYYY') : 'TBD'}
              </Text>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-indigo-600" />
              <Text className="font-bold text-slate-700 text-xs">
                {interview.scheduled_at ? dayjs(interview.scheduled_at).format('h:mm A') : 'TBD'}
              </Text>
            </div>
          </div>
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
            <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Meeting</Text>
            {interview.meeting_link || interview.interview_link ? (
              <a href={interview.meeting_link || interview.interview_link} target="_blank" rel="noreferrer"
                className="flex items-center gap-2 font-bold text-indigo-600 underline text-xs">
                <Video size={13} /> Join Meeting
              </a>
            ) : (
              <Text className="text-slate-400 italic text-xs">No link provided</Text>
            )}
          </div>
        </div>

        <div>
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Panelists</Text>
          <div className="space-y-1.5">
            {panelists.length > 0 ? panelists.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between p-3 rounded-xl bg-white border border-slate-100">
                <div className="flex items-center gap-2.5">
                  <Avatar size={22} className="bg-slate-100 text-slate-600 font-bold border-none shrink-0 text-[9px]">
                    {p.interviewer_id?.charAt(0)}
                  </Avatar>
                  <Text className="text-xs font-bold text-slate-700">#{p.interviewer_id.slice(0, 8)}</Text>
                </div>
                <Tag className="m-0 border-none bg-indigo-50 text-indigo-600 font-black text-[8px] uppercase">{p.role}</Tag>
              </div>
            )) : (
              <div className="py-4 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                <Text className="text-slate-300 font-bold uppercase text-[9px] tracking-widest">No panelists assigned</Text>
              </div>
            )}
          </div>
        </div>

        {decision && (
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-3 opacity-10 text-white"><CheckCircle2 size={40} /></div>
            <Text className="block text-[10px] font-black uppercase text-indigo-400 tracking-widest mb-3">Final Decision</Text>
            <div className={cn("inline-block px-3 py-1 rounded-lg font-black text-[10px] uppercase tracking-widest border mb-3",
              decision.decision === 'hire' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20")}>
              {decision.decision}
            </div>
            <Paragraph className="text-white/70 text-xs italic leading-relaxed m-0">
              "{decision.notes || 'No notes.'}"
            </Paragraph>
          </div>
        )}
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════

function HomeSection({ interviews, isLoading, onNavigateTo }: {
  interviews: Interview[]; isLoading: boolean; onNavigateTo: (s: ActiveSection) => void
}) {
  const now = dayjs()
  const startOfToday = now.startOf('day')
  const endOfToday = now.endOf('day')

  const stats = useMemo(() => ({
    today: interviews.filter(i => i.scheduled_at && !dayjs(i.scheduled_at).isBefore(startOfToday) && !dayjs(i.scheduled_at).isAfter(endOfToday)).length,
    scheduled: interviews.filter(i => i.status === 'scheduled').length,
    completed: interviews.filter(i => i.status === 'completed').length,
    pending: interviews.filter(i => ['scheduled', 'rescheduled', 'in_progress'].includes(i.status)).length,
    failed: interviews.filter(i => ['cancelled', 'no_show'].includes(i.status)).length,
    rescheduled: interviews.filter(i => i.status === 'rescheduled').length,
  }), [endOfToday, interviews, startOfToday])

  const upcoming = useMemo(() =>
    interviews
      .filter(i => i.scheduled_at && ['scheduled', 'rescheduled', 'confirmed'].includes(i.status) && dayjs(i.scheduled_at).isAfter(now))
      .sort((a, b) => dayjs(a.scheduled_at).diff(dayjs(b.scheduled_at)))
      .slice(0, 6), [interviews, now])

  const queue = useMemo(() => ({
    waiting: interviews.filter(i => i.status === 'scheduled' && i.scheduled_at && dayjs(i.scheduled_at).isAfter(now)).slice(0, 5),
    ready: interviews.filter(i => ['scheduled', 'rescheduled'].includes(i.status) && i.scheduled_at && dayjs(i.scheduled_at).diff(now, 'minute') <= 30 && dayjs(i.scheduled_at).isAfter(now.subtract(15, 'minute'))).slice(0, 5),
    delayed: interviews.filter(i => ['scheduled', 'rescheduled'].includes(i.status) && i.scheduled_at && dayjs(i.scheduled_at).isBefore(now)).slice(0, 5),
  }), [interviews, now])

  const recentActivity = useMemo(() => {
    return [...interviews]
      .sort((a, b) => dayjs(b.updated_at).valueOf() - dayjs(a.updated_at).valueOf())
      .slice(0, 8)
      .map((item) => {
        let label = 'Interview updated'
        if (item.status === 'completed') label = 'Interview completed'
        else if (item.status === 'rescheduled') label = 'Interview rescheduled'
        else if (item.decision) label = 'Decision made'
        else if ((item.feedback_count || 0) > 0) label = 'Feedback submitted'
        return { item, label }
      })
  }, [interviews])

  const distribution = useMemo(() => {
    const buckets = { ai: 0, technical: 0, human: 0, assessments: 0 }
    interviews.forEach((interview) => {
      const category = getInterviewTypeCategory(interview.interview_type)
      if (category === 'AI') buckets.ai += 1
      else if (category === 'Technical') buckets.technical += 1
      else if (category === 'Assessment') buckets.assessments += 1
      else buckets.human += 1
    })
    return buckets
  }, [interviews])

  const performance = useMemo(() => {
    const completed = interviews.filter(i => i.status === 'completed')
    const pass = completed.filter(i => ['hire', 'strong_recommend', 'recommend', 'pass', 'shortlist'].includes((i.decision?.decision || i.recommendation || '').toLowerCase())).length
    const reject = completed.filter(i => ['reject', 'rejected', 'concern'].includes((i.decision?.decision || i.recommendation || '').toLowerCase())).length
    const pendingDecision = completed.filter(i => !i.decision).length
    return {
      passRate: completed.length ? Math.round((pass / completed.length) * 100) : 0,
      rejectRate: completed.length ? Math.round((reject / completed.length) * 100) : 0,
      pendingDecision,
    }
  }, [interviews])

  function interviewStage(item: Interview) {
    return String((item.metadata as any)?.stage_name || `Round ${item.interview_round || 1}`)
  }

  function interviewerLabel(item: Interview) {
    const panelists = Array.isArray((item as any).panelists) ? (item as any).panelists : []
    if (panelists.length) return `${panelists.length} interviewer${panelists.length > 1 ? 's' : ''}`
    if (Array.isArray(item.interviewers) && item.interviewers.length) return `${item.interviewers.length} interviewer${item.interviewers.length > 1 ? 's' : ''}`
    return 'Unassigned'
  }

  function QueuePanel({ title, icon: Icon, color, items, emptyMsg }: {
    title: string; icon: React.ElementType; color: string; items: Interview[]; emptyMsg: string
  }) {
    return (
      <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm flex flex-col">
        <div className="px-4 py-3 border-b border-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon size={13} className={color} />
            <Text className="font-black text-slate-800 text-[10px] uppercase tracking-widest">{title}</Text>
          </div>
          <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-black text-[9px] uppercase">{items.length}</Tag>
        </div>
        <div className="flex-1 px-4 py-2">
          {items.length === 0 ? (
            <div className="py-5 text-center"><Text className="text-slate-300 text-[9px] font-bold uppercase">{emptyMsg}</Text></div>
          ) : items.map((item) => (
            <div key={item.id} className="flex items-center justify-between py-2.5 border-b border-slate-50 last:border-0">
              <div className="min-w-0">
                <Text className="block font-bold text-slate-800 text-[10px] truncate">{item.candidate_name || item.candidate_id?.slice(0, 8) || 'Candidate'}</Text>
                <Text className="block text-[9px] text-slate-400 font-bold uppercase truncate">{getInterviewTypeLabel(item.interview_type)}</Text>
              </div>
              <Text className="text-[9px] font-bold text-slate-400 shrink-0 ml-2">{item.scheduled_at ? dayjs(item.scheduled_at).format('HH:mm') : '-'}</Text>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <SectionHeader
        icon={Home}
        title="Dashboard"
        subtitle="Enterprise operations view across scheduling, interviews, flows, scorecards, and decisions"
      />

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-6">
        <StatCard label="Today"         value={stats.today}        icon={Calendar}     color="text-indigo-600"  bg="bg-indigo-50" />
        <StatCard label="Scheduled"     value={stats.scheduled}    icon={Clock}        color="text-blue-600"    bg="bg-blue-50" />
        <StatCard label="Completed"     value={stats.completed}    icon={CheckCircle2} color="text-emerald-600" bg="bg-emerald-50" />
        <StatCard label="Pending"       value={stats.pending}      icon={AlertCircle}  color="text-amber-600"   bg="bg-amber-50" />
        <StatCard label="Failed"        value={stats.failed}       icon={X}            color="text-rose-600"    bg="bg-rose-50" />
        <StatCard label="Rescheduled"   value={stats.rescheduled}  icon={RefreshCw}    color="text-cyan-600"    bg="bg-cyan-50" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-soft-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-50 flex items-center justify-between">
            <Text className="font-black text-slate-800 text-[10px] uppercase tracking-widest">Upcoming Interviews</Text>
            <button onClick={() => onNavigateTo('scheduling')} className="text-[9px] font-black uppercase tracking-widest text-indigo-600 hover:text-indigo-700">Open Scheduling</button>
          </div>
          <div className="divide-y divide-slate-50">
            {upcoming.length === 0 ? (
              <div className="py-10 text-center"><Text className="text-slate-300 text-[10px] font-bold uppercase">No upcoming interviews</Text></div>
            ) : upcoming.map((item) => (
              <div key={item.id} className="grid grid-cols-5 gap-3 px-4 py-3">
                <div className="min-w-0">
                  <Text className="block font-bold text-slate-800 text-[10px] truncate">{item.candidate_name || item.candidate_id?.slice(0, 8) || 'Candidate'}</Text>
                  <Text className="block text-[9px] text-slate-400 font-bold uppercase truncate">{item.job_title || 'Interview candidate'}</Text>
                </div>
                <div className="min-w-0">
                  <Text className="block text-[9px] font-black uppercase text-slate-400">Type</Text>
                  <Text className="block text-[10px] font-bold text-slate-800 truncate">{getInterviewTypeLabel(item.interview_type)}</Text>
                </div>
                <div className="min-w-0">
                  <Text className="block text-[9px] font-black uppercase text-slate-400">Interviewer</Text>
                  <Text className="block text-[10px] font-bold text-slate-800 truncate">{interviewerLabel(item)}</Text>
                </div>
                <div>
                  <Text className="block text-[9px] font-black uppercase text-slate-400">Time</Text>
                  <Text className="block text-[10px] font-bold text-slate-800">{item.scheduled_at ? dayjs(item.scheduled_at).format('MMM D, HH:mm') : '-'}</Text>
                </div>
                <div className="min-w-0">
                  <Text className="block text-[9px] font-black uppercase text-slate-400">Stage</Text>
                  <Text className="block text-[10px] font-bold text-slate-800 truncate">{interviewStage(item)}</Text>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Interview Performance</Text>
          <div className="space-y-3">
            <div className="rounded-2xl border border-slate-100 p-3">
              <Text className="block text-[9px] font-black uppercase text-slate-400">Pass Rate</Text>
              <Text className="block text-2xl font-black text-emerald-600">{performance.passRate}%</Text>
            </div>
            <div className="rounded-2xl border border-slate-100 p-3">
              <Text className="block text-[9px] font-black uppercase text-slate-400">Reject Rate</Text>
              <Text className="block text-2xl font-black text-rose-600">{performance.rejectRate}%</Text>
            </div>
            <div className="rounded-2xl border border-slate-100 p-3">
              <Text className="block text-[9px] font-black uppercase text-slate-400">Pending Decisions</Text>
              <Text className="block text-2xl font-black text-amber-600">{performance.pendingDecision}</Text>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <QueuePanel title="Waiting Interviews" icon={Clock} color="text-blue-600" items={queue.waiting} emptyMsg="No waiting interviews" />
        <QueuePanel title="Ready Interviews" icon={Play} color="text-emerald-600" items={queue.ready} emptyMsg="No ready interviews" />
        <QueuePanel title="Delayed Interviews" icon={AlertCircle} color="text-rose-600" items={queue.delayed} emptyMsg="No delayed interviews" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-soft-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-50 flex items-center justify-between">
            <Text className="font-black text-slate-800 text-[10px] uppercase tracking-widest">Recent Activity</Text>
            <button onClick={() => onNavigateTo('operations')} className="text-[9px] font-black uppercase tracking-widest text-indigo-600 hover:text-indigo-700">Open Operations</button>
          </div>
          <div className="divide-y divide-slate-50">
            {recentActivity.map(({ item, label }) => (
              <div key={item.id} className="flex items-center justify-between px-4 py-3">
                <div className="min-w-0">
                  <Text className="block text-[10px] font-bold text-slate-800 truncate">{label}</Text>
                  <Text className="block text-[9px] text-slate-400 font-bold uppercase truncate">{item.title || getInterviewTypeLabel(item.interview_type)} • {item.candidate_name || item.candidate_id?.slice(0, 8)}</Text>
                </div>
                <Text className="text-[9px] font-bold text-slate-400 shrink-0 ml-3">{dayjs(item.updated_at).fromNow()}</Text>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Interview Types Distribution</Text>
          <div className="space-y-3">
            {[
              { label: 'AI Interviews', value: distribution.ai, color: 'bg-purple-500' },
              { label: 'Technical Interviews', value: distribution.technical, color: 'bg-emerald-500' },
              { label: 'Human Interviews', value: distribution.human, color: 'bg-blue-500' },
              { label: 'Assessments', value: distribution.assessments, color: 'bg-amber-500' },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between mb-1">
                  <Text className="text-[10px] font-black uppercase tracking-widest text-slate-500">{item.label}</Text>
                  <Text className="text-[10px] font-black text-slate-800">{item.value}</Text>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className={cn('h-full rounded-full', item.color)} style={{ width: `${interviews.length ? (item.value / interviews.length) * 100 : 0}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Quick Access</Text>
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          {NAV_ITEMS.filter(n => n.key !== 'home').map(item => (
            <button key={item.key} onClick={() => onNavigateTo(item.key)}
              className="bg-white rounded-2xl p-4 border border-slate-100 shadow-soft-sm text-left hover:border-indigo-200 hover:bg-indigo-50/20 group transition-all">
              <div className="h-8 w-8 rounded-xl bg-slate-100 group-hover:bg-indigo-100 flex items-center justify-center text-slate-500 group-hover:text-indigo-600 mb-3 transition-all">
                <item.icon size={15} />
              </div>
              <Text className="block font-black text-slate-800 text-[10px] uppercase tracking-tight">{item.label}</Text>
              <Text className="block text-[9px] font-bold text-slate-400 mt-0.5">{item.desc}</Text>
              {item.badge && <span className="mt-1.5 inline-block px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-[7px] font-black">{item.badge} types</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: FLOWS — now persisted to backend
// ═══════════════════════════════════════════════════════════════════════════════

const AI_FLOW_TEMPLATE_TYPES = [
  'ai_screening',
  'ai_behavioral',
  'ai_technical',
  'async_text',
  'async_audio',
  'one_way_video',
] as const

type FlowStageConfig = {
  id: string
  name: string
  type_code: string
  mode: string
  order: number
  selection_category?: InterviewTypeCategory
  ai_template_id?: string
  ai_template_name?: string
  ai_interview_type?: string
  ai_duration_minutes?: number
  ai_response_mode?: string
  ai_outcome_rules?: Array<{
    label: string
    min_score: number
    max_score: number
    route_action: string
    next_stage_mapping?: string
  }>
  trigger_mode?: 'auto_trigger' | 'manual_trigger'
  recruiter_review_required?: boolean
  notify_recruiter?: boolean
  generate_interview_link?: boolean
  send_candidate_notification?: boolean
  update_candidate_status?: boolean
}

const createDefaultFlowStage = (order: number): FlowStageConfig => ({
  id: String(Date.now() + order),
  name: `Stage ${order}`,
  type_code: 'live_video',
  mode: 'native',
  order,
  selection_category: getInterviewTypeCategory('live_video'),
  trigger_mode: 'manual_trigger',
  recruiter_review_required: false,
  notify_recruiter: false,
  generate_interview_link: true,
  send_candidate_notification: true,
  update_candidate_status: true,
})

function FlowsSection() {
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [flowName, setFlowName] = useState('')
  const [flowDesc, setFlowDesc] = useState('')
  const [stages, setStages] = useState<FlowStageConfig[]>([
    {
      id: '1',
      name: 'Stage 1 – Screening',
      type_code: 'recruiter_screening',
      mode: 'native',
      order: 1,
      selection_category: getInterviewTypeCategory('recruiter_screening'),
      trigger_mode: 'manual_trigger',
      recruiter_review_required: false,
      notify_recruiter: false,
      generate_interview_link: true,
      send_candidate_notification: true,
      update_candidate_status: true,
    },
  ])
  const [saving, setSaving] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['interview-flows-list'],
    () => interviewsApi.listFlows()
  )
  const flows: any[] = (data as any)?.flows ?? []
  const { data: templatesData } = useApiQuery(
    ['interview-templates-list'],
    () => interviewsApi.listTemplates()
  )
  const aiTemplates: any[] = ((templatesData as any)?.templates ?? []).filter((template: any) =>
    AI_FLOW_TEMPLATE_TYPES.includes(template.interview_type)
  )

  const addStage = () => setStages(prev => [
    ...prev,
    createDefaultFlowStage(prev.length + 1),
  ])

  const removeStage = (id: string) => setStages(prev => prev.filter(s => s.id !== id))

  const updateStage = (id: string, field: keyof FlowStageConfig, value: any) =>
    setStages(prev => prev.map(s => s.id === id ? { ...s, [field]: value } : s))

  const updateStageType = (id: string, typeCode: string) =>
    setStages(prev => prev.map((stage) => {
      if (stage.id !== id) return stage
      if (typeCode === 'ai_interview') {
        return {
          ...stage,
          type_code: typeCode,
          mode: 'native',
          selection_category: 'AI',
          name: stage.ai_template_name ? `AI Interview – ${stage.ai_template_name}` : stage.name || 'AI Interview',
          trigger_mode: stage.trigger_mode || 'auto_trigger',
          recruiter_review_required: stage.recruiter_review_required ?? true,
          notify_recruiter: stage.notify_recruiter ?? true,
          generate_interview_link: stage.generate_interview_link ?? true,
          send_candidate_notification: stage.send_candidate_notification ?? true,
          update_candidate_status: stage.update_candidate_status ?? true,
        }
      }

      return {
        ...stage,
        type_code: typeCode,
        selection_category: getInterviewTypeCategory(typeCode),
        ai_template_id: undefined,
        ai_template_name: undefined,
        ai_interview_type: undefined,
        ai_duration_minutes: undefined,
        ai_response_mode: undefined,
        ai_outcome_rules: undefined,
      }
    }))

  const selectAITemplate = (id: string, templateId: string) =>
    setStages(prev => prev.map((stage) => {
      if (stage.id !== id) return stage
      const template = aiTemplates.find((entry: any) => entry.id === templateId)
      const meta = template?.metadata?.ai_interview || {}
      const setup = meta.setup || {}
      const outcomes = meta.outcome_routing?.outcomes || []

      return {
        ...stage,
        ai_template_id: templateId,
        ai_template_name: template?.name || '',
        ai_interview_type: setup.interview_type || template?.interview_type || '',
        ai_duration_minutes: setup.duration_minutes || template?.duration_minutes || 0,
        ai_response_mode: setup.response_mode || template?.questions?.[0]?.type || '',
        ai_outcome_rules: outcomes.map((rule: any) => ({
          label: rule.label,
          min_score: Number(rule.min_score || 0),
          max_score: Number(rule.max_score || 100),
          route_action: rule.route_action || 'manual_review_queue',
          next_stage_mapping: rule.next_stage_mapping || '',
        })),
        name: `AI Interview – ${template?.name || 'Template'}`,
      }
    }))

  const saveFlow = async () => {
    if (!flowName.trim()) { message.error('Flow name is required'); return }
    if (stages.length === 0) { message.error('Add at least one stage'); return }
    if (stages.some((stage) => stage.type_code === 'ai_interview' && !stage.ai_template_id)) {
      message.error('Select an AI interview template for every AI Interview stage')
      return
    }
    setSaving(true)
    try {
      const normalizedStages = stages.map((stage, index) => ({ ...stage, order: index + 1 }))
      await interviewsApi.createFlow({
        name: flowName,
        description: flowDesc,
        stages: normalizedStages,
        metadata: {
          ai_flow_integration: true,
          candidate_trigger_defaults: {
            generate_interview_link: true,
            send_candidate_notification: true,
            update_candidate_status: true,
          },
        },
      })
      message.success('Interview flow saved')
      queryClient.invalidateQueries({ queryKey: ['interview-flows-list'] })
      setCreateOpen(false)
      setFlowName(''); setFlowDesc('')
      setStages([{
        id: '1',
        name: 'Stage 1 – Screening',
        type_code: 'recruiter_screening',
        mode: 'native',
        order: 1,
        selection_category: getInterviewTypeCategory('recruiter_screening'),
        trigger_mode: 'manual_trigger',
        recruiter_review_required: false,
        notify_recruiter: false,
        generate_interview_link: true,
        send_candidate_notification: true,
        update_candidate_status: true,
      }])
    } catch { message.error('Failed to save flow') }
    finally { setSaving(false) }
  }

  const deleteFlow = async (id: string) => {
    try {
      await interviewsApi.deleteFlow(id)
      message.success('Flow removed')
      queryClient.invalidateQueries({ queryKey: ['interview-flows-list'] })
    } catch { message.error('Failed to delete flow') }
  }

  const stageColor = (code: string) => code === 'ai_interview' ? 'text-purple-600' : ENGINE_REGISTRY[code]?.color ?? 'text-slate-600'
  const stageBg    = (code: string) => code === 'ai_interview' ? 'bg-purple-50' : ENGINE_REGISTRY[code]?.bg ?? 'bg-slate-100'
  const stageTypeLabel = (stage: any) => stage.type_code === 'ai_interview'
    ? `AI interview${stage.ai_template_name ? ` • ${stage.ai_template_name}` : ''}`
    : stage.type_code?.replace(/_/g, ' ')

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <SectionHeader
        icon={GitBranch}
        title="Interview Flows"
        subtitle="Define reusable multi-stage interview pipelines"
        action={
          <div className="flex items-center gap-2">
            <button onClick={() => refetch()} className="h-8 w-8 flex items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-400 hover:bg-slate-50">
              <RefreshCw size={13} className={cn(isLoading && 'animate-spin')} />
            </button>
            <button onClick={() => setCreateOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all">
              <Plus size={14} /> Create Flow
            </button>
          </div>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-20"><RefreshCw size={20} className="animate-spin text-slate-300" /></div>
      ) : flows.length === 0 ? (
        <EmptyState icon={GitBranch} title="No flows yet" subtitle="Design interview pipelines with ordered stages" cta="Create Your First Flow" onCta={() => setCreateOpen(true)} />
      ) : (
        <div className="space-y-4">
          {flows.map(flow => (
            <div key={flow.id} className="bg-white rounded-2xl border border-slate-200 shadow-soft-sm overflow-hidden">
              <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <Text className="font-black text-slate-900 text-sm">{flow.name}</Text>
                  {flow.description && <Text className="block text-xs text-slate-400 font-medium mt-0.5">{flow.description}</Text>}
                </div>
                <div className="flex items-center gap-2">
                  <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-black text-[9px] uppercase">{flow.stage_count} stages</Tag>
                  <button onClick={() => deleteFlow(flow.id)} className="h-7 w-7 flex items-center justify-center rounded-lg text-slate-300 hover:text-rose-400 hover:bg-rose-50 transition-all">
                    <X size={13} />
                  </button>
                </div>
              </div>
              <div className="px-5 py-4 flex items-center gap-2 flex-wrap">
                {(flow.stages ?? []).map((stage: any, idx: number) => (
                  <div key={stage.id ?? idx} className="flex items-center gap-2">
                    <div className={cn("px-3 py-2 rounded-xl border border-slate-100 text-center min-w-[76px]", stageBg(stage.type_code))}>
                      <Text className={cn("block text-[8px] font-black uppercase tracking-widest opacity-60", stageColor(stage.type_code))}>S{idx + 1}</Text>
                      <Text className={cn("block text-[10px] font-black", stageColor(stage.type_code))}>{stage.name}</Text>
                      <Text className={cn("block text-[8px] font-bold opacity-60 mt-0.5", stageColor(stage.type_code))}>
                        {stageTypeLabel(stage)}
                      </Text>
                    </div>
                    {idx < (flow.stages ?? []).length - 1 && <ArrowRight size={12} className="text-slate-300 shrink-0" />}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        title={<span className="font-black text-slate-900 uppercase tracking-tight">Create Interview Flow</span>}
        open={createOpen} onCancel={() => setCreateOpen(false)} onOk={saveFlow}
        okText="Save Flow" confirmLoading={saving} width={820} destroyOnHidden
        styles={{ body: { maxHeight: '78vh', overflowY: 'auto', paddingRight: 8 } }}
      >
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest mb-1.5">Flow Name *</label>
              <Input value={flowName} onChange={e => setFlowName(e.target.value)} placeholder="e.g. Backend Engineer Pipeline" className="h-10 rounded-xl" />
            </div>
            <div>
              <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest mb-1.5">Description</label>
              <Input value={flowDesc} onChange={e => setFlowDesc(e.target.value)} placeholder="Optional description..." className="h-10 rounded-xl" />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest">Stages</label>
              <button onClick={addStage} className="text-[10px] font-black uppercase text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
                <Plus size={11} /> Add Stage
              </button>
            </div>
            <div className="max-h-[52vh] space-y-2 overflow-y-auto pr-1">
              {stages.map((stage, idx) => (
                <div key={stage.id} className="rounded-xl bg-slate-50 border border-slate-100 p-3 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-[9px] font-black shrink-0">{idx + 1}</div>
                    <Input value={stage.name} onChange={e => updateStage(stage.id, 'name', e.target.value)}
                      placeholder="Stage name" className="h-8 rounded-lg flex-1 text-xs font-bold" />
                    <Select value={stage.mode} onChange={v => updateStage(stage.id, 'mode', v)}
                      options={MODE_OPTIONS} className="w-36 h-8" />
                    {stages.length > 1 && (
                      <button onClick={() => removeStage(stage.id)} className="text-slate-300 hover:text-rose-400 transition-colors shrink-0"><X size={13} /></button>
                    )}
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-3">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Stage Type Selection</p>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                      <Select
                        value={stage.selection_category || getInterviewTypeCategory(stage.type_code)}
                        options={(['AI', 'Human', 'Technical', 'Assessment', 'Screening', 'Advanced'] as InterviewTypeCategory[]).map((category) => ({
                          value: category,
                          label: category,
                        }))}
                        onChange={(value) => updateStage(stage.id, 'selection_category', value)}
                      />
                      <Select
                        value={stage.type_code}
                        options={[
                          ...((stage.selection_category || getInterviewTypeCategory(stage.type_code)) === 'AI'
                            ? [{ value: 'ai_interview', label: 'AI Interview' }]
                            : []),
                          ...TYPE_SELECT_OPTIONS
                            .filter((option) => option.category === (stage.selection_category || getInterviewTypeCategory(stage.type_code)))
                            .map((option) => ({ value: option.value, label: option.label })),
                        ]}
                        onChange={(value) => updateStageType(stage.id, value)}
                      />
                    </div>
                  </div>

                  {stage.type_code === 'ai_interview' && (
                    <div className="max-h-[44vh] overflow-y-auto rounded-xl border border-purple-100 bg-white p-4 space-y-4 pr-2">
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <div>
                          <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest mb-1.5">Select AI Interview Template</label>
                          <Select
                            value={stage.ai_template_id}
                            onChange={(value) => selectAITemplate(stage.id, value)}
                            options={aiTemplates.map((template: any) => ({
                              value: template.id,
                              label: template.name,
                            }))}
                            placeholder="Choose reusable AI interview template"
                            className="h-10"
                            showSearch
                            optionFilterProp="label"
                          />
                        </div>
                        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Template Summary</p>
                          <p className="mt-2 text-xs font-bold text-slate-900">{stage.ai_template_name || 'No AI template selected'}</p>
                          <p className="mt-1 text-[11px] text-slate-500">
                            {stage.ai_interview_type ? stage.ai_interview_type.replace(/_/g, ' ') : 'Type pending'} • {stage.ai_duration_minutes || 0}m • {stage.ai_response_mode ? stage.ai_response_mode.replace(/_/g, ' ') : 'response pending'}
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="rounded-xl border border-slate-200 p-3">
                          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3">Stage Configuration</p>
                          <div className="space-y-3">
                            <div>
                              <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest mb-1.5">Trigger</label>
                              <Select
                                value={stage.trigger_mode}
                                onChange={(value) => updateStage(stage.id, 'trigger_mode', value)}
                                options={[
                                  { value: 'auto_trigger', label: 'Auto trigger' },
                                  { value: 'manual_trigger', label: 'Manual trigger' },
                                ]}
                                className="h-10"
                              />
                            </div>
                            <div className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                              <span className="text-xs font-bold text-slate-700">Recruiter review required</span>
                              <Switch checked={Boolean(stage.recruiter_review_required)} onChange={(checked) => updateStage(stage.id, 'recruiter_review_required', checked)} />
                            </div>
                            <div className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                              <span className="text-xs font-bold text-slate-700">Notify recruiter</span>
                              <Switch checked={Boolean(stage.notify_recruiter)} onChange={(checked) => updateStage(stage.id, 'notify_recruiter', checked)} />
                            </div>
                          </div>
                        </div>

                        <div className="rounded-xl border border-slate-200 p-3">
                          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3">Candidate Trigger</p>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                              <span className="text-xs font-bold text-slate-700">Generate interview link</span>
                              <Switch checked={Boolean(stage.generate_interview_link)} onChange={(checked) => updateStage(stage.id, 'generate_interview_link', checked)} />
                            </div>
                            <div className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                              <span className="text-xs font-bold text-slate-700">Send notification</span>
                              <Switch checked={Boolean(stage.send_candidate_notification)} onChange={(checked) => updateStage(stage.id, 'send_candidate_notification', checked)} />
                            </div>
                            <div className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                              <span className="text-xs font-bold text-slate-700">Update status</span>
                              <Switch checked={Boolean(stage.update_candidate_status)} onChange={(checked) => updateStage(stage.id, 'update_candidate_status', checked)} />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="max-h-[18vh] overflow-y-auto rounded-xl border border-slate-200 p-3 pr-2">
                        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Outcome Integration</p>
                        <div className="mt-3 space-y-2">
                          {(stage.ai_outcome_rules ?? []).length > 0 ? (
                            stage.ai_outcome_rules?.map((rule, ruleIndex) => (
                              <div key={`${stage.id}-${ruleIndex}`} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-xs">
                                <span className="font-bold text-slate-900">{rule.min_score}-{rule.max_score}: {rule.label}</span>
                                <span className="text-slate-500">{rule.route_action.replace(/_/g, ' ')}{rule.next_stage_mapping ? ` • ${rule.next_stage_mapping}` : ''}</span>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-500">Select a template to load Step 5 outcome logic for routing, reject, and manual review behavior.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="max-h-[24vh] overflow-y-auto rounded-xl border border-slate-100 bg-slate-50 p-4 pr-2">
            <div className="flex items-center justify-between mb-3">
              <label className="block text-[10px] font-black uppercase text-slate-500 tracking-widest">Flow Preview</label>
              <Tag className="m-0 border-none bg-white text-slate-500 font-black text-[9px] uppercase">{stages.length} stages</Tag>
            </div>
            <div className="space-y-2">
              {stages.map((stage, idx) => (
                <div key={`preview-${stage.id}`} className="flex items-center gap-2">
                  <div className={cn("px-3 py-2 rounded-xl border border-slate-100 text-center min-w-[116px]", stageBg(stage.type_code))}>
                    <Text className={cn("block text-[8px] font-black uppercase tracking-widest opacity-60", stageColor(stage.type_code))}>S{idx + 1}</Text>
                    <Text className={cn("block text-[10px] font-black", stageColor(stage.type_code))}>
                      {stage.type_code === 'ai_interview' ? (stage.ai_template_name || 'AI Interview') : stage.name}
                    </Text>
                    <Text className={cn("block text-[8px] font-bold opacity-60 mt-0.5", stageColor(stage.type_code))}>
                      {stage.type_code === 'ai_interview'
                        ? `AI interview • ${stage.ai_interview_type ? stage.ai_interview_type.replace(/_/g, ' ') : 'template pending'}`
                        : stage.type_code.replace(/_/g, ' ')}
                    </Text>
                  </div>
                  {idx < stages.length - 1 && <ArrowRight size={12} className="text-slate-300 shrink-0" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: TYPES REGISTRY — 40 engines, grouped by category
// ═══════════════════════════════════════════════════════════════════════════════

function TypesRegistrySection() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<InterviewTypeCategory>('All')

  const { data, isLoading, refetch } = useApiQuery(
    ['interview-types-list'],
    () => interviewsApi.listTypes()
  )
  const apiTypes: any[] = (data as any)?.types ?? []

  // Merge API types with registry metadata
  const merged = useMemo(() => {
    const apiMap = new Map(apiTypes.map((t: any) => [t.code, t]))
    return Object.entries(ENGINE_REGISTRY).map(([code, meta]) => {
      const apiEntry = apiMap.get(code)
      const development = getRegistryDevelopment(code)
      return {
        code,
        name: apiEntry?.name ?? code.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
        description: apiEntry?.description ?? meta.desc,
        is_active: apiEntry?.is_active ?? false,
        registered: !!apiEntry,
        id: apiEntry?.id,
        uxCategory: getInterviewTypeCategory(code),
        developmentStatus: development.status,
        developmentBadge: development.badge,
        intendedEngine: development.intendedEngine,
        engineRoute: development.route,
        developmentNotes: development.notes,
        ...meta,
      }
    })
  }, [apiTypes])

  const filtered = merged.filter(t => {
    const matchSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.code.includes(search.toLowerCase())
    const matchCat = activeCategory === 'All' || t.uxCategory === activeCategory
    return matchSearch && matchCat
  })

  const handleCreate = async (values: any) => {
    setSubmitting(true)
    try {
      await interviewsApi.createType(values)
      message.success('Interview type registered')
      queryClient.invalidateQueries({ queryKey: ['interview-types-list'] })
      setCreateOpen(false)
      form.resetFields()
    } catch { message.error('Failed to register type') }
    finally { setSubmitting(false) }
  }

  const registeredCount = merged.filter(t => t.registered).length

  const handleRegistryCardClick = (type: any) => {
    if (!type.registered) {
      form.setFieldsValue({
        name: type.name,
        code: type.code,
        description: type.description,
      })
      setCreateOpen(true)
      return
    }

    if (type.engineRoute) {
      if (type.developmentStatus === 'partial') {
        message.warning(`${type.name} is partially built. Opening the available engine shell.`)
      }
      navigate(type.engineRoute)
      return
    }

    message.info(`${type.name} is not developed yet. Intended engine: ${type.intendedEngine}.`)
  }

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <SectionHeader
        icon={Database}
        title="Types Registry"
        subtitle={`${registeredCount} of 40 interview engines registered`}
        action={
          <div className="flex items-center gap-2">
            <button onClick={() => navigate('/interviews/questions')}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-600 hover:border-indigo-200 hover:text-indigo-600 transition-all">
              <FileText size={13} /> Question Bank
            </button>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5">
              <Search size={13} className="text-slate-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search types..."
                className="bg-transparent text-[11px] font-bold text-slate-700 outline-none placeholder-slate-400 uppercase tracking-widest w-28" />
            </div>
            <button onClick={() => setCreateOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all">
              <Plus size={14} /> Register
            </button>
          </div>
        }
      />

      {/* Progress bar */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-4">
        <div className="flex items-center justify-between mb-2">
          <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Registry Coverage</Text>
          <Text className="text-[10px] font-black text-indigo-600">{registeredCount}/40 engines</Text>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: `${(registeredCount / 40) * 100}%` }} />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><RefreshCw size={20} className="animate-spin text-slate-300" /></div>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-2">
              {(['All', ...INTERVIEW_TYPE_CATEGORIES] as InterviewTypeCategory[]).map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setActiveCategory(cat)}
                  className={cn(
                    'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition',
                    activeCategory === cat
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-slate-200 bg-white hover:border-slate-300',
                  )}
                >
                  <div>
                    <p className="text-xs font-black uppercase tracking-widest text-slate-900">{cat}</p>
                    <p className="text-[11px] text-slate-500">{cat === 'All' ? 'All registered interview engines' : `${getCategoryOptions(cat).length} mapped types`}</p>
                  </div>
                  <Tag color={activeCategory === cat ? 'blue' : 'default'}>
                    {cat === 'All' ? merged.length : filtered.filter((item) => item.uxCategory === cat).length}
                  </Tag>
                </button>
              ))}
            </div>
          </div>
          <div className="col-span-12 lg:col-span-9">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {filtered.map(type => (
                <button
                  key={type.code}
                  type="button"
                  onClick={() => handleRegistryCardClick(type)}
                  className={cn("bg-white rounded-2xl border p-4 transition-all group text-left",
                    !type.registered || type.developmentStatus === 'not_developed'
                      ? "border-dashed border-slate-200 opacity-90 hover:border-slate-300 cursor-pointer"
                      : "border-slate-100 shadow-soft-sm hover:border-indigo-200 hover:shadow-soft-md cursor-pointer")}>
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center', type.bg, type.color)}>
                      <type.icon size={17} />
                    </div>
                    <div className="flex items-center gap-1">
                      <Tag
                        color={type.developmentStatus === 'built' ? 'success' : type.developmentStatus === 'partial' ? 'gold' : 'default'}
                        className="m-0 border-none font-black text-[7px] uppercase tracking-widest px-1.5 py-0.5 rounded-full"
                      >
                        {type.developmentBadge}
                      </Tag>
                      <ChevronRight className={cn(
                        "h-3.5 w-3.5 transition-colors",
                        type.developmentStatus === 'not_developed'
                          ? 'text-slate-200 group-hover:text-slate-300'
                          : 'text-slate-300 group-hover:text-indigo-500',
                      )} />
                    </div>
                  </div>
                  <Text className="block font-black text-slate-900 text-[11px] leading-tight mb-1">{type.name}</Text>
                  <Tag className="m-0 border-none bg-slate-50 text-slate-400 font-mono text-[7px] uppercase mb-2 max-w-full truncate">{type.code}</Tag>
                  <Text className="block text-[9px] text-slate-400 font-medium leading-relaxed line-clamp-2">{type.description}</Text>
                  <Text className="block mt-2 text-[9px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    {type.developmentStatus === 'not_developed'
                      ? `Intended engine: ${type.intendedEngine}`
                      : type.developmentNotes}
                  </Text>
                  <div className="mt-2 text-[8px] font-black uppercase tracking-widest text-slate-300">{type.uxCategory}</div>
                </button>
              ))}
              {filtered.length === 0 ? (
                <div className="col-span-full rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
                  <Text className="text-sm font-bold text-slate-500">No interview types found for this category.</Text>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      <Modal
        title={<span className="font-black text-slate-900 uppercase tracking-tight">Register Interview Type</span>}
        open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()}
        confirmLoading={submitting} destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-6">
          <Form.Item name="name" label="Type Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Executive Panel Interview" className="h-10 rounded-xl" />
          </Form.Item>
          <Form.Item name="code" label="Type Code" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" placeholder="Select from registry or enter custom code"
              options={TYPE_SELECT_OPTIONS} className="h-10" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="What does this interview engine do?" className="rounded-xl" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: TEMPLATES
// ═══════════════════════════════════════════════════════════════════════════════

function TemplatesSection() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data, isLoading } = useApiQuery(['interview-templates-list'], () => interviewsApi.listTemplates())
  const templates: any[] = (data as any)?.templates ?? []
  const { data: typesData } = useApiQuery(['interview-types-list'], () => interviewsApi.listTypes())
  const apiTypes: any[] = (typesData as any)?.types ?? []

  const filtered = templates.filter((t: any) => t.name.toLowerCase().includes(search.toLowerCase()))

  const handleCreate = async (values: any) => {
    setSubmitting(true)
    try {
      await interviewsApi.createTemplate(values)
      message.success('Template created')
      queryClient.invalidateQueries({ queryKey: ['interview-templates-list'] })
      setCreateOpen(false); form.resetFields()
    } catch { message.error('Failed to create template') }
    finally { setSubmitting(false) }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Template', dataIndex: 'name', key: 'name',
      render: (name) => (
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 shrink-0"><FileText size={14} /></div>
          <Text className="font-bold text-slate-900 text-sm">{name}</Text>
        </div>
      ),
    },
    { title: 'Type', dataIndex: 'interview_type', key: 'type',
      render: t => <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[9px] uppercase">{formatStatusLabel(t)}</Tag> },
    { title: 'Duration', dataIndex: 'duration_minutes', key: 'dur',
      render: m => <div className="flex items-center gap-1.5 text-slate-500 font-bold text-xs"><Clock size={11} /> {m}m</div> },
    { title: 'Scoring', dataIndex: 'scoring_type', key: 'score',
      render: s => <Text className="text-slate-400 text-xs font-medium capitalize">{s?.replace('_', ' ')}</Text> },
    { title: 'Status', dataIndex: 'is_active', key: 'status',
      render: a => <Tag color={a ? 'success' : 'default'} className="m-0 border-none font-black text-[8px] uppercase tracking-widest px-2 py-0.5 rounded-full">{a ? 'Active' : 'Off'}</Tag> },
    { title: '', key: 'arrow', width: 40, align: 'right' as const, render: () => <ChevronRight className="h-4 w-4 text-slate-300" /> },
  ]

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <SectionHeader icon={LayoutGrid} title="Interview Templates"
        subtitle="Reusable configurations linked to type engines"
        action={
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5">
              <Search size={13} className="text-slate-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
                className="bg-transparent text-[11px] font-bold text-slate-700 outline-none placeholder-slate-400 uppercase tracking-widest w-28" />
            </div>
            <button onClick={() => setCreateOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all">
              <Plus size={14} /> New Template
            </button>
          </div>
        }
      />
      <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-md overflow-hidden">
        <Table columns={columns} dataSource={filtered} rowKey="id" loading={isLoading}
          pagination={{ pageSize: 12, hideOnSinglePage: true }} className="enterprise-table"
          locale={{ emptyText: <EmptyState icon={FileText} title="No templates yet" subtitle="Create reusable interview configurations" cta="New Template" onCta={() => setCreateOpen(true)} /> }} />
      </div>
      <Modal title={<span className="font-black text-slate-900 uppercase tracking-tight">Create Template</span>}
        open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()}
        confirmLoading={submitting} destroyOnHidden width={560}>
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-5">
          <div className="grid grid-cols-2 gap-3">
            <Form.Item name="name" label="Template Name" rules={[{ required: true }]}>
              <Input placeholder="e.g. Senior Backend Eval" className="h-10 rounded-xl" />
            </Form.Item>
            <Form.Item name="interview_type" label="Interview Type" rules={[{ required: true }]}>
              <Select className="h-10" showSearch optionFilterProp="label"
                options={apiTypes.length > 0
                  ? apiTypes.map((t: any) => ({ value: t.code, label: t.name }))
                  : TYPE_SELECT_OPTIONS} />
            </Form.Item>
            <Form.Item name="duration_minutes" label="Duration (min)" initialValue={30}>
              <InputNumber min={5} max={300} className="w-full h-10 rounded-xl" />
            </Form.Item>
            <Form.Item name="scoring_type" label="Scoring" initialValue="numeric">
              <Select className="h-10" options={[
                { value: 'numeric', label: 'Numeric (0–100)' },
                { value: 'pass_fail', label: 'Pass / Fail' },
                { value: 'criteria', label: 'Criteria-Based' },
              ]} />
            </Form.Item>
          </div>
          <Form.Item name="instructions" label="Instructions">
            <Input.TextArea rows={3} placeholder="Guidance for the interviewer..." className="rounded-xl" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: PRE-QUALIFICATION
// ═══════════════════════════════════════════════════════════════════════════════

function PrequalificationSection() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data, isLoading } = useApiQuery(['prequal-forms-list'], () => prequalificationApi.listForms())
  const forms: any[] = (data as any)?.forms ?? []

  const handleCreate = async (values: any) => {
    setSubmitting(true)
    try {
      const res = await prequalificationApi.createForm(values)
      const newForm = (res as any)?.data?.form ?? (res as any)?.form
      message.success('Form created')
      queryClient.invalidateQueries({ queryKey: ['prequal-forms-list'] })
      setCreateOpen(false); form.resetFields()
      if (newForm?.id) {
        navigate(`/interviews/prequalification/forms/${newForm.id}/builder`)
      }
    } catch { message.error('Failed to create form') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <SectionHeader icon={ClipboardList} title="Pre-Qualification Engine"
        subtitle="Knockout forms with yes/no flows and routing rules"
        action={
          <button onClick={() => setCreateOpen(true)}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all">
            <Plus size={14} /> New Form
          </button>
        }
      />

      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: ClipboardList, color: 'text-blue-600',    bg: 'bg-blue-50',    title: 'Form Builder',     desc: 'Create sections + typed question blocks' },
          { icon: GitBranch,    color: 'text-amber-600',   bg: 'bg-amber-50',   title: 'Routing Rules',    desc: 'If No → Reject. If Yes → Next Question.' },
          { icon: Shield,       color: 'text-emerald-600', bg: 'bg-emerald-50', title: 'Knockout Logic',   desc: 'Auto-disqualify on mandatory thresholds' },
        ].map(item => (
          <div key={item.title} className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-4">
            <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center mb-3', item.bg, item.color)}><item.icon size={17} /></div>
            <Text className="block font-black text-slate-900 text-sm mb-1">{item.title}</Text>
            <Text className="block text-[10px] text-slate-400 font-medium leading-relaxed">{item.desc}</Text>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/30 flex items-center justify-between">
          <Text className="font-black text-slate-700 text-[10px] uppercase tracking-widest">Active Forms</Text>
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{forms.length} forms</Text>
        </div>
        {isLoading ? (
          <div className="py-10 text-center"><RefreshCw size={16} className="animate-spin text-slate-300 mx-auto" /></div>
        ) : forms.length === 0 ? (
          <div className="py-10 text-center">
            <ClipboardList className="h-7 w-7 text-slate-200 mx-auto mb-2" />
            <Text className="text-slate-300 text-xs font-bold">No forms yet</Text>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {forms.map((f: any) => (
              <div key={f.id} onClick={() => navigate(`/interviews/prequalification/forms/${f.id}/builder`)}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50 cursor-pointer group transition-all">
                <div className="flex items-center gap-3">
                  <div className="h-7 w-7 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600"><ClipboardList size={13} /></div>
                  <div>
                    <Text className="block font-bold text-slate-800 text-xs">{f.name}</Text>
                    <Text className="block text-[9px] text-slate-400 font-bold uppercase">{f.description || 'No description'}</Text>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Tag color={f.is_active ? 'success' : 'default'} className="m-0 border-none font-black text-[8px] uppercase tracking-widest px-2 py-0.5 rounded-full">{f.is_active ? 'Active' : 'Off'}</Tag>
                  <ArrowRight size={12} className="text-slate-300 group-hover:text-indigo-400 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal title={<span className="font-black text-slate-900 uppercase tracking-tight">Create Form</span>}
        open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()}
        confirmLoading={submitting} destroyOnHidden width={460}>
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-5">
          <Form.Item name="name" label="Form Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Engineering Candidate Screener" className="h-10 rounded-xl" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="What is this form used for?" className="rounded-xl" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: SKILL MATCHING
// ═══════════════════════════════════════════════════════════════════════════════

function SkillMatchingSection() {
  const [mustHave, setMustHave] = useState<string[]>(['Python', 'System Design', 'SQL'])
  const [preferred, setPreferred] = useState<string[]>(['Kubernetes', 'Kafka', 'AWS'])
  const [fitThreshold, setFitThreshold] = useState(70)
  const [newMust, setNewMust] = useState('')
  const [newPref, setNewPref] = useState('')

  const addSkill = (type: 'm' | 'p') => {
    if (type === 'm' && newMust.trim()) { setMustHave(p => [...p, newMust.trim()]); setNewMust('') }
    else if (type === 'p' && newPref.trim()) { setPreferred(p => [...p, newPref.trim()]); setNewPref('') }
  }

  const barColor = fitThreshold >= 70 ? '#10b981' : fitThreshold >= 40 ? '#f59e0b' : '#ef4444'

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <SectionHeader icon={Zap} title="Skill Matching" subtitle="Define must-have and preferred skills for intelligent routing" />

      <div className="grid grid-cols-2 gap-5">
        {[
          { label: 'Must-Have Skills', icon: Shield, color: 'text-rose-600', bg: 'bg-rose-50', badge: 'Required', badgeCls: 'bg-rose-50 text-rose-600', items: mustHave, setItems: setMustHave, val: newMust, setVal: setNewMust, type: 'm' as const, tagCls: 'bg-rose-50 border-rose-100 text-rose-700' },
          { label: 'Preferred Skills', icon: Award,  color: 'text-blue-600',  bg: 'bg-blue-50',  badge: 'Bonus',    badgeCls: 'bg-blue-50 text-blue-600',  items: preferred, setItems: setPreferred, val: newPref, setVal: setNewPref, type: 'p' as const, tagCls: 'bg-blue-50 border-blue-100 text-blue-700' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-2xl border border-slate-200 shadow-soft-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className={cn("h-7 w-7 rounded-lg flex items-center justify-center", s.bg, s.color)}><s.icon size={13} /></div>
              <Text className="font-black text-slate-900 text-[10px] uppercase tracking-widest">{s.label}</Text>
              <span className={cn("ml-auto px-2 py-0.5 rounded-full text-[8px] font-black uppercase", s.badgeCls)}>{s.badge}</span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3 min-h-[32px]">
              {s.items.map(skill => (
                <div key={skill} className={cn("flex items-center gap-1 px-2.5 py-1 rounded-full border text-[10px] font-black", s.tagCls)}>
                  {skill}
                  <button onClick={() => s.setItems(p => p.filter(x => x !== skill))} className="opacity-50 hover:opacity-100 ml-0.5"><X size={9} /></button>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Input value={s.val} onChange={e => s.setVal(e.target.value)} onPressEnter={() => addSkill(s.type)}
                placeholder="Add skill..." className="h-8 rounded-lg text-xs font-bold flex-1" />
              <button onClick={() => addSkill(s.type)} className={cn("h-8 w-8 rounded-lg flex items-center justify-center transition-all", s.bg, s.color, "hover:opacity-80")}><Plus size={13} /></button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600"><TrendingUp size={13} /></div>
            <Text className="font-black text-slate-900 text-[10px] uppercase tracking-widest">Fit Score Threshold</Text>
          </div>
          <InputNumber value={fitThreshold} onChange={v => setFitThreshold(v ?? 0)} min={0} max={100}
            formatter={v => `${v}%`} parser={v => Number(v?.replace('%', '') ?? 0)}
            className="w-20 h-8 rounded-lg text-center font-black" />
        </div>
        <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden mb-2">
          <div className="h-full rounded-full transition-all" style={{ width: `${fitThreshold}%`, backgroundColor: barColor }} />
        </div>
        <div className="flex justify-between">
          <Text className="text-[8px] font-black text-slate-300 uppercase">0%</Text>
          <Text className="text-[8px] font-black text-slate-300 uppercase">100%</Text>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-sm p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="h-7 w-7 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600"><GitBranch size={13} /></div>
          <Text className="font-black text-slate-900 text-[10px] uppercase tracking-widest">Route Recommendation</Text>
          <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-50 border border-amber-100 text-amber-600 text-[7px] font-black uppercase">Coming Soon</span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'High Fit', score: `≥ ${fitThreshold}%`, action: 'Auto-advance to next round', cls: 'border-emerald-200 bg-emerald-50/50 text-emerald-700' },
            { label: 'Partial Fit', score: `40–${fitThreshold - 1}%`, action: 'Flag for recruiter review', cls: 'border-amber-200 bg-amber-50/50 text-amber-700' },
            { label: 'Low Fit', score: '< 40%', action: 'Auto-reject with reason', cls: 'border-rose-200 bg-rose-50/50 text-rose-700' },
          ].map(r => (
            <div key={r.label} className={cn("rounded-xl border p-3", r.cls)}>
              <Text className="block font-black text-[10px] uppercase tracking-widest mb-0.5">{r.label}</Text>
              <Text className="block text-[9px] font-bold opacity-60 mb-1">Score {r.score}</Text>
              <Text className="block text-[10px] font-bold">{r.action}</Text>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

function OperationsSection({ interviews, isLoading, refetch, statusFilter, setStatusFilter, search, setSearch }: {
  interviews: Interview[]; isLoading: boolean; refetch: () => void
  statusFilter: string; setStatusFilter: (v: string) => void
  search: string; setSearch: (v: string) => void
}) {
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null)

  const columns: ColumnsType<Interview> = [
    { title: 'ID', dataIndex: 'id', key: 'id',
      render: id => <Text className="font-bold text-slate-400 text-[10px] uppercase">#{id.slice(0, 8)}</Text> },
    { title: 'Type', dataIndex: 'interview_type', key: 'type',
      render: t => <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-black text-[9px] uppercase tracking-widest">{formatStatusLabel(t)}</Tag> },
    { title: 'Round', dataIndex: 'interview_round', key: 'round',
      render: r => <Text className="font-bold text-slate-500 text-xs">R{r}</Text> },
    { title: 'Scheduled', dataIndex: 'scheduled_at', key: 'sched',
      render: d => (
        <div>
          <Text className="block font-bold text-slate-700 text-xs">{d ? dayjs(d).format('MMM D, YYYY') : 'TBD'}</Text>
          <Text className="block text-[10px] text-slate-400">{d ? dayjs(d).format('h:mm A') : ''}</Text>
        </div>
      ) },
    { title: 'Status', dataIndex: 'status', key: 'status',
      render: s => <Tag color={getStatusStyle(s, 'application').antColor}
        className="m-0 border-none uppercase font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full">{formatStatusLabel(s)}</Tag> },
    { title: 'Score', dataIndex: 'feedback_average_score', key: 'score',
      render: s => s ? <span className="font-black text-indigo-600 text-xs bg-indigo-50 px-2 py-1 rounded-lg">{s}/100</span> : <span className="text-slate-200 font-bold">—</span> },
    { title: '', key: 'arrow', width: 40, align: 'right' as const, render: () => <ChevronRight className="h-4 w-4 text-slate-300" /> },
  ]

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-slate-100 bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 transition-all">
            <Search size={13} className="text-slate-400" />
            <input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)}
              className="bg-transparent text-[11px] font-bold text-slate-700 outline-none placeholder-slate-400 uppercase tracking-widest w-36" />
          </div>
          <Select placeholder="Status" className="w-32" options={STATUS_OPTIONS}
            onChange={setStatusFilter} allowClear value={statusFilter || undefined} />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => refetch()} className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50">
            <RefreshCw size={12} className={cn(isLoading && 'animate-spin')} />
          </button>
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{interviews.length} records</Text>
        </div>
      </div>

      <div className="flex-1 overflow-hidden relative">
        <StandardSplitView
          isDetailOpen={!!selectedInterview}
          compactListContent={
            <div className="flex flex-col h-full bg-white border-r border-slate-200 overflow-y-auto">
              {interviews.map(item => (
                <div key={item.id} onClick={() => setSelectedInterview(item)}
                  className={cn("p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
                    item.id === selectedInterview?.id ? "bg-indigo-50/50 border-l-indigo-600" : "bg-white border-l-transparent hover:bg-slate-50")}>
                  <div className="flex items-center gap-3">
                    <Avatar className="bg-slate-100 text-slate-600 font-bold border-none shrink-0">
                      {item.candidate_id?.charAt(0).toUpperCase()}
                    </Avatar>
                    <div className="min-w-0">
                      <p className="m-0 font-bold text-slate-900 text-xs truncate">#{item.id.slice(0, 8)}</p>
                      <Text className="text-[10px] text-slate-400 font-bold uppercase truncate">R{item.interview_round} · {formatStatusLabel(item.interview_type)}</Text>
                    </div>
                  </div>
                </div>
              ))}
              {interviews.length === 0 && !isLoading && (
                <div className="py-16 text-center"><Text className="text-slate-300 text-xs font-bold">No interviews found</Text></div>
              )}
            </div>
          }
          fullListContent={
            <div className="h-full overflow-y-auto p-4 pt-0">
              <Table columns={columns} dataSource={interviews} rowKey="id" loading={isLoading}
                pagination={{ pageSize: 15, hideOnSinglePage: true }} className="enterprise-table"
                onRow={record => ({ onClick: () => setSelectedInterview(record), className: 'cursor-pointer' })} />
            </div>
          }
          detailContent={selectedInterview
            ? <InterviewDetailDrawer interview={selectedInterview} onClose={() => setSelectedInterview(null)} />
            : null}
        />
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION: ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════

function AnalyticsSection({ interviews }: { interviews: Interview[] }) {
  const defaultRange: [dayjs.Dayjs, dayjs.Dayjs] = [dayjs().subtract(29, 'day').startOf('day'), dayjs().endOf('day')]
  const [range, setRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>(defaultRange)
  const [typeCategoryFilter, setTypeCategoryFilter] = useState<'all' | InterviewTypeCategory>('all')
  const [granularity, setGranularity] = useState<'day' | 'week' | 'month'>('day')

  const filteredInterviews = useMemo(() => {
    const [start, end] = range
    return interviews.filter(interview => {
      const sourceDate = interview.scheduled_at || interview.created_at || interview.updated_at
      if (!sourceDate) return false
      const stamp = dayjs(sourceDate)
      if (stamp.isBefore(start) || stamp.isAfter(end)) return false
      if (typeCategoryFilter === 'all') return true
      return getInterviewTypeCategory(interview.interview_type) === typeCategoryFilter
    })
  }, [interviews, range, typeCategoryFilter])

  const analytics = useMemo(() => {
    const total = filteredInterviews.length
    const decisionLabel = (interview: Interview) => {
      const decision = interview.decision as any
      const raw = String(decision?.recommendation || decision?.outcome || decision?.decision || decision?.status || '').toLowerCase()
      if (raw.includes('offer') || raw.includes('hire') || raw.includes('pass') || raw.includes('strong_recommend') || raw.includes('recommend')) return 'pass'
      if (raw.includes('reject') || raw.includes('decline')) return 'reject'
      if (raw.includes('review') || raw.includes('neutral') || raw.includes('concern')) return 'pending'
      return interview.status === 'rejected' ? 'reject' : 'pending'
    }

    const groupedVolume = filteredInterviews.reduce((acc: Record<string, number>, interview) => {
      const stamp = dayjs(interview.scheduled_at || interview.created_at || interview.updated_at)
      const key = granularity === 'month'
        ? stamp.format('MMM YYYY')
        : granularity === 'week'
          ? `${stamp.startOf('week').format('DD MMM')} W`
          : stamp.format('DD MMM')
      acc[key] = (acc[key] || 0) + 1
      return acc
    }, {})

    const byType = filteredInterviews.reduce((acc: Record<string, number>, interview) => {
      const label = getInterviewTypeLabel(interview.interview_type)
      acc[label] = (acc[label] || 0) + 1
      return acc
    }, {})

    const byTypeCategory = filteredInterviews.reduce((acc: Record<string, number>, interview) => {
      const category = getInterviewTypeCategory(interview.interview_type) || 'other'
      acc[category] = (acc[category] || 0) + 1
      return acc
    }, {})

    const passes = filteredInterviews.filter(i => decisionLabel(i) === 'pass').length
    const rejects = filteredInterviews.filter(i => decisionLabel(i) === 'reject').length
    const pendingDecisions = filteredInterviews.filter(i => decisionLabel(i) === 'pending').length
    const hires = filteredInterviews.filter(i => {
      const decision = i.decision as any
      const raw = String(decision?.recommendation || decision?.outcome || decision?.decision || decision?.status || '').toLowerCase()
      return raw.includes('hire') || raw.includes('offer')
    }).length

    const interviewerMap = new Map<string, { activity: number; pass: number; reject: number; pending: number }>()
    filteredInterviews.forEach(interview => {
      const interviewers = interview.interviewers?.length ? interview.interviewers : ['Unassigned']
      const outcome = decisionLabel(interview)
      interviewers.forEach(name => {
        const current = interviewerMap.get(name) || { activity: 0, pass: 0, reject: 0, pending: 0 }
        current.activity += 1
        current[outcome] += 1
        interviewerMap.set(name, current)
      })
    })

    const interviewerRows = Array.from(interviewerMap.entries())
      .map(([name, value]) => ({
        key: name,
        interviewer: name,
        activity: value.activity,
        passRate: value.activity ? Math.round((value.pass / value.activity) * 100) : 0,
        rejectRate: value.activity ? Math.round((value.reject / value.activity) * 100) : 0,
        decisionPattern: value.pending > value.pass && value.pending > value.reject ? 'Review-heavy' : value.pass >= value.reject ? 'Forward-leaning' : 'Strict',
      }))
      .sort((a, b) => b.activity - a.activity)

    const typePerformance = Object.entries(byTypeCategory).map(([category, count]) => {
      const groupItems = filteredInterviews.filter(i => getInterviewTypeCategory(i.interview_type) === category)
      const groupPasses = groupItems.filter(i => decisionLabel(i) === 'pass').length
      return {
        key: category,
        category,
        volume: count,
        successRate: count ? Math.round((groupPasses / count) * 100) : 0,
      }
    }).sort((a, b) => b.volume - a.volume)

    const schedulingHours = filteredInterviews
      .filter(i => i.created_at && i.scheduled_at)
      .map(i => dayjs(i.scheduled_at).diff(dayjs(i.created_at), 'hour', true))
      .filter(v => Number.isFinite(v) && v >= 0)
    const completionHours = filteredInterviews
      .filter(i => i.scheduled_at && i.updated_at && i.status === 'completed')
      .map(i => dayjs(i.updated_at).diff(dayjs(i.scheduled_at), 'hour', true))
      .filter(v => Number.isFinite(v) && v >= 0)
    const decisionHours = filteredInterviews
      .filter(i => i.scheduled_at && i.updated_at && i.decision)
      .map(i => dayjs(i.updated_at).diff(dayjs(i.scheduled_at), 'hour', true))
      .filter(v => Number.isFinite(v) && v >= 0)
    const average = (values: number[]) => values.length ? Math.round((values.reduce((sum, v) => sum + v, 0) / values.length) * 10) / 10 : 0

    const scoreRows = filteredInterviews
      .map(i => ({
        key: i.id,
        candidate: i.candidate_name || i.candidate_id || `Candidate ${i.id.slice(0, 6)}`,
        type: getInterviewTypeLabel(i.interview_type),
        score: i.feedback_average_score ?? ((i.metadata as any)?.scorecard_score ?? (i.metadata as any)?.ai_score ?? 0),
        recommendation: String((i.decision as any)?.recommendation || (i.decision as any)?.outcome || 'pending').replace(/_/g, ' '),
      }))
      .filter(row => Number(row.score) > 0)
      .sort((a, b) => Number(b.score) - Number(a.score))

    const dimensionMap = filteredInterviews.reduce((acc: Record<string, { total: number; count: number }>, interview) => {
      const dimensions = (interview.metadata as any)?.scorecard_dimensions || (interview.metadata as any)?.dimension_scores || []
      if (Array.isArray(dimensions)) {
        dimensions.forEach((dimension: any) => {
          const name = String(dimension?.name || dimension?.dimension || 'Unnamed').trim()
          const score = Number(dimension?.score ?? dimension?.value ?? 0)
          if (!name || !Number.isFinite(score)) return
          acc[name] = acc[name] || { total: 0, count: 0 }
          acc[name].total += score
          acc[name].count += 1
        })
      }
      return acc
    }, {})

    const dimensionTrends = Object.entries(dimensionMap)
      .map(([name, value]) => ({
        key: name,
        name,
        averageScore: Math.round((value.total / value.count) * 10) / 10,
        observations: value.count,
      }))
      .sort((a, b) => b.averageScore - a.averageScore)

    return {
      total,
      passes,
      rejects,
      pendingDecisions,
      hires,
      groupedVolume,
      byType,
      byTypeCategory,
      interviewerRows,
      typePerformance,
      funnel: {
        prequalificationToInterview: filteredInterviews.filter(i => ['recruiter_screening', 'phone_interview'].includes(i.interview_type)).length,
        interviewToOffer: hires,
        interviewToReject: rejects,
      },
      time: {
        timeToSchedule: average(schedulingHours),
        timeToComplete: average(completionHours),
        timeToDecision: average(decisionHours),
      },
      scoreRows,
      dimensionTrends,
      passRate: total ? Math.round((passes / total) * 100) : 0,
      rejectRate: total ? Math.round((rejects / total) * 100) : 0,
      hireRate: total ? Math.round((hires / total) * 100) : 0,
    }
  }, [filteredInterviews, granularity])

  function MetricBars({ data, total, colorClass, valueFormatter }: {
    data: Record<string, number>
    total: number
    colorClass?: string
    valueFormatter?: (key: string, value: number, pct: number) => string
  }) {
    return (
      <div className="space-y-2.5">
        {Object.entries(data).length === 0 ? (
          <div className="py-8 text-center"><Text className="text-slate-300 text-xs font-bold">No data in selected range</Text></div>
        ) : (
          Object.entries(data).sort((a, b) => b[1] - a[1]).map(([key, count]) => {
            const pct = total > 0 ? Math.round((count / total) * 100) : 0
            return (
              <div key={key}>
                <div className="flex justify-between gap-4 mb-1">
                  <Text className="text-[10px] font-black uppercase text-slate-600 tracking-widest">{key}</Text>
                  <Text className="text-[10px] font-black text-slate-400 text-right">
                    {valueFormatter ? valueFormatter(key, count, pct) : `${count} (${pct}%)`}
                  </Text>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className={cn('h-full rounded-full', colorClass ?? 'bg-indigo-500')} style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })
        )}
      </div>
    )
  }

  const interviewerColumns: ColumnsType<any> = [
    { title: 'Interviewer', dataIndex: 'interviewer', key: 'interviewer', render: (value: string) => <Text className="font-bold text-slate-800">{value}</Text> },
    { title: 'Activity', dataIndex: 'activity', key: 'activity' },
    { title: 'Pass Rate', dataIndex: 'passRate', key: 'passRate', render: (value: number) => `${value}%` },
    { title: 'Reject Rate', dataIndex: 'rejectRate', key: 'rejectRate', render: (value: number) => `${value}%` },
    { title: 'Decision Pattern', dataIndex: 'decisionPattern', key: 'decisionPattern', render: (value: string) => <Tag color="blue">{value}</Tag> },
  ]

  const scoreColumns: ColumnsType<any> = [
    { title: 'Candidate', dataIndex: 'candidate', key: 'candidate', render: (value: string) => <Text className="font-bold text-slate-800">{value}</Text> },
    { title: 'Interview Type', dataIndex: 'type', key: 'type' },
    { title: 'Score', dataIndex: 'score', key: 'score', render: (value: number) => <Tag color={value >= 75 ? 'green' : value >= 50 ? 'gold' : 'red'}>{Math.round(value)}</Tag> },
    { title: 'Recommendation', dataIndex: 'recommendation', key: 'recommendation', render: (value: string) => <Text className="capitalize text-slate-600">{value}</Text> },
  ]

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <SectionHeader
        icon={BarChart2}
        title="Analytics"
        subtitle="Interview volume, outcomes, interviewer behavior and scorecard trends"
        action={(
          <div className="flex items-center gap-2">
            <Select
              size="small"
              value={granularity}
              onChange={value => setGranularity(value)}
              options={[
                { value: 'day', label: 'Daily' },
                { value: 'week', label: 'Weekly' },
                { value: 'month', label: 'Monthly' },
              ]}
              className="w-28"
            />
            <Select
              size="small"
              value={typeCategoryFilter}
              onChange={value => setTypeCategoryFilter(value)}
              options={[
                { value: 'all', label: 'All Types' },
                ...INTERVIEW_TYPE_CATEGORIES.flatMap((category) =>
                  getCategoryOptions(category).map(option => ({ value: option.value, label: option.label })),
                ),
              ]}
              className="w-40"
            />
            <DatePicker.RangePicker
              size="small"
              allowClear={false}
              value={range}
              onChange={value => {
                if (value?.[0] && value?.[1]) setRange([value[0].startOf('day'), value[1].endOf('day')])
              }}
            />
          </div>
        )}
      />

      <div className="grid grid-cols-2 xl:grid-cols-6 gap-4">
        <StatCard label="Interviews" value={analytics.total} icon={Activity} color="text-indigo-600" bg="bg-indigo-50" />
        <StatCard label="Pass Rate" value={`${analytics.passRate}%`} icon={CheckCircle2} color="text-emerald-600" bg="bg-emerald-50" />
        <StatCard label="Reject Rate" value={`${analytics.rejectRate}%`} icon={X} color="text-rose-600" bg="bg-rose-50" />
        <StatCard label="Pending Decisions" value={analytics.pendingDecisions} icon={AlertCircle} color="text-amber-600" bg="bg-amber-50" />
        <StatCard label="Hire Rate" value={`${analytics.hireRate}%`} icon={TrendingUp} color="text-blue-600" bg="bg-blue-50" />
        <StatCard label="Avg Time To Decision" value={`${analytics.time.timeToDecision || 0}h`} icon={Clock} color="text-cyan-600" bg="bg-cyan-50" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Interview Volume</Text>
          <MetricBars data={analytics.groupedVolume} total={analytics.total} colorClass="bg-indigo-500" />
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Interview Types By Volume</Text>
          <MetricBars data={analytics.byType} total={analytics.total} colorClass="bg-violet-500" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5 space-y-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest">Pass / Reject Metrics</Text>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Passed', value: analytics.passes, color: 'text-emerald-600', bg: 'bg-emerald-50', icon: CheckCircle2 },
              { label: 'Rejected', value: analytics.rejects, color: 'text-rose-600', bg: 'bg-rose-50', icon: X },
              { label: 'Pending', value: analytics.pendingDecisions, color: 'text-amber-600', bg: 'bg-amber-50', icon: AlertCircle },
              { label: 'Hired / Offer', value: analytics.hires, color: 'text-blue-600', bg: 'bg-blue-50', icon: Award },
            ].map(item => (
              <div key={item.label} className={cn('rounded-xl p-4 flex items-center gap-3', item.bg)}>
                <item.icon size={18} className={item.color} />
                <div>
                  <Text className={cn('block font-black text-xl leading-none', item.color)}>{item.value}</Text>
                  <Text className="block text-[9px] font-black uppercase tracking-widest text-slate-500 mt-0.5">{item.label}</Text>
                </div>
              </div>
            ))}
          </div>
          <MetricBars data={analytics.byTypeCategory} total={analytics.total} colorClass="bg-emerald-500" />
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5 space-y-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest">Interview Type Performance</Text>
          <div className="space-y-3">
            {analytics.typePerformance.length === 0 ? (
              <div className="py-8 text-center"><Text className="text-slate-300 text-xs font-bold">No performance data yet</Text></div>
            ) : analytics.typePerformance.map(item => (
              <div key={item.key} className="rounded-xl border border-slate-100 p-4">
                <div className="flex items-center justify-between mb-2">
                  <Text className="font-black text-slate-800 capitalize">{item.category}</Text>
                  <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{item.volume} interviews</Text>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                  <div className="h-full rounded-full bg-indigo-500" style={{ width: `${item.successRate}%` }} />
                </div>
                <Text className="text-[10px] font-black uppercase tracking-widest text-slate-500">{item.successRate}% success</Text>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5 space-y-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest">Funnel Analytics</Text>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Prequal → Interview', value: analytics.funnel.prequalificationToInterview, bg: 'bg-indigo-50', color: 'text-indigo-600' },
              { label: 'Interview → Offer', value: analytics.funnel.interviewToOffer, bg: 'bg-emerald-50', color: 'text-emerald-600' },
              { label: 'Interview → Reject', value: analytics.funnel.interviewToReject, bg: 'bg-rose-50', color: 'text-rose-600' },
            ].map(item => (
              <div key={item.label} className={cn('rounded-xl p-4', item.bg)}>
                <Text className={cn('block font-black text-2xl leading-none', item.color)}>{item.value}</Text>
                <Text className="block mt-1 text-[9px] font-black uppercase tracking-widest text-slate-500">{item.label}</Text>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5 space-y-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest">Time Analytics</Text>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Time To Schedule', value: `${analytics.time.timeToSchedule}h`, bg: 'bg-cyan-50', color: 'text-cyan-700' },
              { label: 'Time To Complete', value: `${analytics.time.timeToComplete}h`, bg: 'bg-blue-50', color: 'text-blue-700' },
              { label: 'Time To Decision', value: `${analytics.time.timeToDecision}h`, bg: 'bg-violet-50', color: 'text-violet-700' },
            ].map(item => (
              <div key={item.label} className={cn('rounded-xl p-4', item.bg)}>
                <Text className={cn('block font-black text-2xl leading-none', item.color)}>{item.value}</Text>
                <Text className="block mt-1 text-[9px] font-black uppercase tracking-widest text-slate-500">{item.label}</Text>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Interviewer Performance</Text>
          <Table
            rowKey="key"
            size="small"
            pagination={{ pageSize: 5, hideOnSinglePage: true }}
            columns={interviewerColumns}
            dataSource={analytics.interviewerRows}
          />
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5 space-y-4">
          <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest">Scorecard Analytics</Text>
          {analytics.dimensionTrends.length > 0 ? (
            <div className="space-y-3">
              {analytics.dimensionTrends.slice(0, 6).map(item => (
                <div key={item.key}>
                  <div className="flex justify-between mb-1">
                    <Text className="text-[10px] font-black uppercase tracking-widest text-slate-600">{item.name}</Text>
                    <Text className="text-[10px] font-black text-slate-400">{item.averageScore} avg · {item.observations} obs</Text>
                  </div>
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(item.averageScore, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center">
              <Text className="text-slate-400 text-xs font-bold">No dimension-level scorecard data is attached yet</Text>
            </div>
          )}
          <Table
            rowKey="key"
            size="small"
            pagination={{ pageSize: 5, hideOnSinglePage: true }}
            columns={scoreColumns}
            dataSource={analytics.scoreRows}
          />
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-soft-sm p-5">
        <Text className="block text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Analytics Coverage</Text>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Interviews In Range', value: analytics.total, color: 'text-indigo-600', bg: 'bg-indigo-50', icon: Activity },
            { label: 'Scored Interviews', value: analytics.scoreRows.length, color: 'text-emerald-600', bg: 'bg-emerald-50', icon: ClipboardList },
            { label: 'Dimension Trends', value: analytics.dimensionTrends.length, color: 'text-amber-600', bg: 'bg-amber-50', icon: BarChart2 },
          ].map(item => (
            <div key={item.label} className={cn('rounded-xl p-4 flex items-center gap-3', item.bg)}>
              <item.icon size={18} className={item.color} />
              <div>
                <Text className={cn('block font-black text-xl leading-none', item.color)}>{item.value}</Text>
                <Text className="block text-[9px] font-black uppercase tracking-widest text-slate-500 mt-0.5">{item.label}</Text>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN: Interview Command Center
// ═══════════════════════════════════════════════════════════════════════════════

export default function InterviewCommandCenter() {
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawSection = searchParams.get('s') as ActiveSection | null
  const pathSectionMap: Record<string, ActiveSection> = {
    '/interviews/live': 'live',
    '/interviews/analytics': 'analytics',
    '/interviews/automation': 'automation',
    '/interviews/scheduling': 'scheduling',
    '/interviews/scorecards': 'scorecards',
    '/interviews/templates': 'templates',
    '/interviews/prequalification': 'prequalification',
  }
  const activeSection: ActiveSection = NAV_ITEMS.some(n => n.key === rawSection)
    ? rawSection!
    : pathSectionMap[location.pathname] || 'home'

  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const navigateTo = (section: ActiveSection) => setSearchParams({ s: section }, { replace: true })

  const { data, isLoading, refetch } = useApiQuery(
    ['interviews-cc-list', statusFilter, search],
    () => interviewsApi.list({ status: statusFilter || undefined, search: search || undefined })
  )
  const interviews: Interview[] = (data as any)?.interviews ?? []

  const activeNav = NAV_ITEMS.find(n => n.key === activeSection)!

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6 z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
            <Calendar size={17} />
          </div>
          <div>
            <h1 className="text-sm font-black text-slate-900 tracking-tight leading-none uppercase">Interview Command Center</h1>
            <Text className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">{activeNav.desc}</Text>
          </div>
          <div className="ml-3 h-5 w-px bg-slate-200" />
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
              {interviews.length} active · 40 type engines
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => refetch()}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 transition-all">
            <RefreshCw size={12} className={cn(isLoading && 'animate-spin')} />
          </button>
          <button onClick={() => navigateTo('scheduling')}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all">
            <Plus size={13} /> Schedule Interview
          </button>
        </div>
      </div>

      {/* ── Body ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left sidebar nav */}
        <nav className="w-[196px] flex-none border-r border-slate-200 bg-white overflow-y-auto py-3 shrink-0">
          <div className="px-4 mb-2">
            <Text className="text-[8px] font-black uppercase tracking-widest text-slate-300">Sections</Text>
          </div>
          {NAV_ITEMS.map(item => (
            <button key={item.key} onClick={() => navigateTo(item.key)}
              className={cn("w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl transition-all text-left group relative mx-0",
                activeSection === item.key ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-700")}>
              {activeSection === item.key && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-indigo-600 rounded-r-full" />
              )}
              <div className={cn("h-7 w-7 rounded-lg flex items-center justify-center shrink-0 transition-all",
                activeSection === item.key ? "bg-indigo-600 text-white shadow-soft-sm" : "bg-slate-100 text-slate-400 group-hover:bg-slate-200")}>
                <item.icon size={13} />
              </div>
              <div className="min-w-0 flex-1">
                <Text className={cn("block text-[10px] font-black uppercase tracking-tight leading-tight truncate",
                  activeSection === item.key ? "text-indigo-700" : "text-slate-700")}>
                  {item.label}
                </Text>
              </div>
              {item.badge && (
                <span className="shrink-0 px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-[7px] font-black">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-hidden bg-[#F8FAFC]">
          {activeSection === 'home'            && <HomeSection interviews={interviews} isLoading={isLoading} onNavigateTo={navigateTo} />}
          {activeSection === 'flows'           && <FlowsSection />}
          {activeSection === 'types'           && <TypesRegistrySection />}
          {activeSection === 'scorecards'      && <InterviewScorecards embedded />}
          {activeSection === 'templates'       && <TemplatesSection />}
          {activeSection === 'scheduling'      && <InterviewSchedulingEngine />}
          {activeSection === 'live'            && <InterviewLiveCenter embedded />}
          {activeSection === 'automation'      && <InterviewAutomation embedded />}
          {activeSection === 'prequalification'&& <PrequalificationSection />}
          {activeSection === 'skill-matching'  && <SkillMatchingSection />}
          {activeSection === 'operations'      && (
            <OperationsSection interviews={interviews} isLoading={isLoading} refetch={refetch}
              statusFilter={statusFilter} setStatusFilter={setStatusFilter} search={search} setSearch={setSearch} />
          )}
          {activeSection === 'analytics'       && <AnalyticsSection interviews={interviews} />}
        </main>
      </div>
    </div>
  )
}
