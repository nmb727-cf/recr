import { Tag, Divider, Typography } from 'antd'
import {
  SolutionOutlined, CalendarOutlined, ClockCircleOutlined,
  DollarCircleOutlined, CheckCircleOutlined, CloseCircleOutlined,
  MinusCircleOutlined, TrophyOutlined, EnvironmentOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'
import type { ApplicationStatus } from '@/types'

dayjs.extend(relativeTime)

const { Title, Text, Paragraph } = Typography

// ─── Status config ─────────────────────────────────────────────────────────────

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

const PIPELINE_STEPS = [
  { label: 'Applied',      step: 0 },
  { label: 'Screening',    step: 1 },
  { label: 'Shortlisted',  step: 2 },
  { label: 'Interview',    step: 3 },
  { label: 'Offer',        step: 4 },
  { label: 'Joined',       step: 5 },
]

type StatusVisual = {
  label: string
  color: string
  step: number
  bg: string
  text: string
  dot: string
  terminal?: boolean
  terminalType?: 'positive' | 'negative' | 'neutral'
}

// ─── Pipeline visual ───────────────────────────────────────────────────────────

function PipelineVisual({ current }: { current: number }) {
  return (
    <div className="relative">
      <div className="flex items-start justify-between relative">
        {/* connector line */}
        <div className="absolute top-3 left-4 right-4 h-0.5 bg-slate-200 z-0" />
        <div
          className="absolute top-3 left-4 h-0.5 bg-blue-400 z-0 transition-all"
          style={{ width: `${Math.min((current / (PIPELINE_STEPS.length - 1)) * 100, 100)}%` }}
        />
        {PIPELINE_STEPS.map(({ label, step }) => {
          const done    = step < current
          const active  = step === current
          return (
            <div key={label} className="flex flex-col items-center gap-1.5 z-10 flex-1 min-w-0">
              <div className={cn(
                'h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all',
                done   ? 'bg-blue-500 border-blue-500'
                : active ? 'bg-white border-blue-500 shadow-sm shadow-blue-200'
                : 'bg-white border-slate-300'
              )}>
                {done ? (
                  <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : active ? (
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                ) : null}
              </div>
              <span className={cn(
                'text-[9px] font-bold uppercase tracking-wide text-center leading-none px-0.5',
                active ? 'text-blue-600' : done ? 'text-blue-400' : 'text-slate-400'
              )}>
                {label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Panel ─────────────────────────────────────────────────────────────────────

export default function CandidateApplicationQVPanel({ data }: { data: any }) {
  const st = STATUS_MAP[data.status] ?? {
    label: data.status, color: 'default', step: 0,
    bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400',
  }

  const isPositive = st.terminalType === 'positive'
  const isNegative = st.terminalType === 'negative'
  const isActive   = !st.terminal

  const hasOffer = ['offer', 'offer_extended', 'offer_accepted', 'joined', 'placement_confirmed'].includes(data.status)
    && data.offer_amount

  const lastActivity = data.updated_at ?? data.created_at
  const didUpdate    = lastActivity !== data.created_at

  return (
    <div className="space-y-6">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-col items-center text-center gap-3">
        <div className={cn(
          'h-16 w-16 rounded-2xl flex items-center justify-center shadow-sm border',
          isPositive ? 'bg-emerald-50 border-emerald-200'
          : isNegative ? 'bg-rose-50 border-rose-100'
          : 'bg-blue-50 border-blue-100'
        )}>
          {isPositive
            ? <TrophyOutlined style={{ fontSize: 28, color: '#059669' }} />
            : isNegative
              ? <CloseCircleOutlined style={{ fontSize: 28, color: '#e11d48' }} />
              : <SolutionOutlined style={{ fontSize: 28, color: '#2563eb' }} />
          }
        </div>

        <div>
          <div className="text-xl font-black text-slate-900 leading-tight mb-1">
            {data.jobTitle || 'Position'}
          </div>
          <span className={cn(
            'inline-block text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full border',
            st.bg, st.text,
            isPositive ? 'border-emerald-200'
            : isNegative ? 'border-rose-200'
            : st.terminal ? 'border-slate-200'
            : 'border-blue-200'
          )}>
            {st.label}
          </span>
        </div>
      </div>

      {/* ── Meta chips ────────────────────────────────────────────────────── */}
      {(data.jobType || data.workMode || (data.salaryVisible && data.salaryMin)) && (
        <div className="flex flex-wrap gap-2 justify-center">
          {data.jobType && (
            <Tag className="m-0 capitalize text-xs">{data.jobType.replace(/_/g, ' ')}</Tag>
          )}
          {data.workMode && (
            <Tag icon={<EnvironmentOutlined />} className="m-0 capitalize text-xs">
              {data.workMode.replace(/_/g, ' ')}
            </Tag>
          )}
          {data.salaryVisible && data.salaryMin && (
            <Tag icon={<DollarCircleOutlined />} color="green" className="m-0 text-xs">
              {data.salaryCurrency} {Number(data.salaryMin).toLocaleString()}
              {data.salaryMax ? ` – ${Number(data.salaryMax).toLocaleString()}` : '+'}
            </Tag>
          )}
        </div>
      )}

      {/* ── Pipeline progress — active applications only ───────────────────── */}
      {isActive && st.step >= 0 && (
        <>
          <Divider className="!my-2" />
          <div>
            <Title level={5} className="!mb-4 !text-slate-500 !text-xs !font-black !uppercase !tracking-widest">
              Hiring Progress
            </Title>
            <PipelineVisual current={st.step} />
          </div>
        </>
      )}

      {/* ── Offer details ─────────────────────────────────────────────────── */}
      {hasOffer && (
        <>
          <Divider className="!my-2" />
          <div className="rounded-2xl overflow-hidden border border-amber-200">
            <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border-b border-amber-200">
              <TrophyOutlined style={{ color: '#d97706', fontSize: 16 }} />
              <Text className="text-sm font-black text-amber-800">Offer Details</Text>
            </div>
            <div className="px-4 py-3 bg-white space-y-2">
              <div className="flex items-center justify-between">
                <Text className="text-xs text-slate-500">Offer Amount</Text>
                <Text className="text-sm font-black text-emerald-700">
                  {data.offer_currency} {Number(data.offer_amount).toLocaleString()}
                </Text>
              </div>
              {data.offer_expires_at && (
                <div className="flex items-center justify-between">
                  <Text className="text-xs text-slate-500">Expires</Text>
                  <Text className="text-xs text-slate-700">{dayjs(data.offer_expires_at).format('D MMM YYYY')}</Text>
                </div>
              )}
              <div className="flex items-center justify-between">
                <Text className="text-xs text-slate-500">Status</Text>
                {data.offer_accepted_at ? (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700">
                    <CheckCircleOutlined /> Accepted {dayjs(data.offer_accepted_at).format('D MMM')}
                  </span>
                ) : data.offer_rejected_at ? (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-600">
                    <CloseCircleOutlined /> Declined {dayjs(data.offer_rejected_at).format('D MMM')}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-700">
                    Awaiting your response
                  </span>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Rejection reason ──────────────────────────────────────────────── */}
      {data.status === 'rejected' && data.rejection_reason && (
        <>
          <Divider className="!my-2" />
          <div className="rounded-2xl overflow-hidden border border-rose-100">
            <div className="flex items-center gap-2 px-4 py-3 bg-rose-50 border-b border-rose-100">
              <CloseCircleOutlined style={{ color: '#e11d48', fontSize: 15 }} />
              <Text className="text-sm font-black text-rose-800">Feedback</Text>
            </div>
            <div className="px-4 py-3 bg-white">
              <Paragraph className="text-xs text-slate-600 leading-relaxed !mb-0">
                {data.rejection_reason}
              </Paragraph>
            </div>
          </div>
        </>
      )}

      {/* ── Withdrawn reason ──────────────────────────────────────────────── */}
      {data.status === 'withdrawn' && data.withdrawn_reason && (
        <>
          <Divider className="!my-2" />
          <div className="rounded-2xl overflow-hidden border border-slate-200">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-200">
              <MinusCircleOutlined style={{ color: '#64748b', fontSize: 15 }} />
              <Text className="text-sm font-black text-slate-700">Withdrawal Note</Text>
            </div>
            <div className="px-4 py-3 bg-white">
              <Paragraph className="text-xs text-slate-500 leading-relaxed !mb-0">
                {data.withdrawn_reason}
              </Paragraph>
            </div>
          </div>
        </>
      )}

      {/* ── Timeline ──────────────────────────────────────────────────────── */}
      <Divider className="!my-2" />
      <div>
        <Title level={5} className="!mb-3 !text-slate-500 !text-xs !font-black !uppercase !tracking-widest">
          Activity
        </Title>
        <div className="relative pl-5 space-y-4">
          {/* vertical line */}
          <div className="absolute left-1.5 top-1 bottom-1 w-px bg-slate-200" />

          <div className="relative flex items-start gap-3">
            <div className="absolute left-[-14px] h-4 w-4 rounded-full bg-blue-500 border-2 border-white shadow-sm" />
            <div>
              <div className="text-xs font-bold text-slate-800">Application submitted</div>
              <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                <CalendarOutlined /> {dayjs(data.created_at).format('D MMMM YYYY [at] h:mm A')}
              </div>
            </div>
          </div>

          {didUpdate && (
            <div className="relative flex items-start gap-3">
              <div className={cn(
                'absolute left-[-14px] h-4 w-4 rounded-full border-2 border-white shadow-sm',
                st.dot
              )} />
              <div>
                <div className="text-xs font-bold text-slate-800">
                  Status updated to <span className={cn('font-black', st.text)}>{st.label}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                  <ClockCircleOutlined /> {dayjs(lastActivity).format('D MMMM YYYY [at] h:mm A')}
                  <span className="text-slate-300">·</span>
                  {dayjs(lastActivity).fromNow()}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

    </div>
  )
}
