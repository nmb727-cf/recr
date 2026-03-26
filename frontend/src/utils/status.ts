export type StatusContext =
  | 'job'
  | 'agency'
  | 'application'
  | 'candidate_activity'
  | 'generic'

const STATUS_STYLE_MAP: Record<StatusContext, Record<string, { antColor: string; softClass: string; dotClass: string }>> = {
  job: {
    draft: { antColor: 'default', softClass: 'bg-slate-100 text-slate-700', dotClass: 'bg-slate-400' },
    pending_approval: { antColor: 'orange', softClass: 'bg-amber-50 text-amber-700', dotClass: 'bg-amber-400' },
    approved: { antColor: 'blue', softClass: 'bg-blue-50 text-blue-700', dotClass: 'bg-blue-400' },
    active: { antColor: 'green', softClass: 'bg-emerald-50 text-emerald-700', dotClass: 'bg-emerald-500' },
    paused: { antColor: 'orange', softClass: 'bg-amber-50 text-amber-700', dotClass: 'bg-amber-400' },
    in_guarantee_period: { antColor: 'gold', softClass: 'bg-amber-50 text-amber-800', dotClass: 'bg-amber-500' },
    closed: { antColor: 'red', softClass: 'bg-rose-50 text-rose-700', dotClass: 'bg-rose-400' },
    cancelled: { antColor: 'default', softClass: 'bg-slate-100 text-slate-500', dotClass: 'bg-slate-300' },
  },
  agency: {
    pending: { antColor: 'orange', softClass: 'bg-amber-50 text-amber-700', dotClass: 'bg-amber-400' },
    active: { antColor: 'green', softClass: 'bg-emerald-50 text-emerald-700', dotClass: 'bg-emerald-500' },
    suspended: { antColor: 'red', softClass: 'bg-rose-50 text-rose-700', dotClass: 'bg-rose-400' },
    terminated: { antColor: 'default', softClass: 'bg-slate-100 text-slate-500', dotClass: 'bg-slate-300' },
  },
  application: {
    completed: { antColor: 'green', softClass: 'bg-emerald-50 text-emerald-700', dotClass: 'bg-emerald-500' },
    cancelled: { antColor: 'red', softClass: 'bg-rose-50 text-rose-700', dotClass: 'bg-rose-400' },
    rejected: { antColor: 'red', softClass: 'bg-rose-50 text-rose-700', dotClass: 'bg-rose-400' },
    default: { antColor: 'blue', softClass: 'bg-blue-50 text-blue-700', dotClass: 'bg-blue-400' },
  },
  candidate_activity: {
    active: { antColor: 'green', softClass: 'bg-emerald-50 text-emerald-700', dotClass: 'bg-emerald-500' },
    passive: { antColor: 'default', softClass: 'bg-slate-100 text-slate-600', dotClass: 'bg-slate-400' },
  },
  generic: {},
}

export function formatStatusLabel(value?: string | null): string {
  if (!value) return 'Unknown'
  return value.replace(/_/g, ' ')
}

export function getStatusStyle(value: string | undefined | null, context: StatusContext = 'generic') {
  const key = String(value || '').toLowerCase()
  const contextMap = STATUS_STYLE_MAP[context] ?? {}
  if (contextMap[key]) return contextMap[key]
  if (context === 'application' && contextMap.default) return contextMap.default
  return { antColor: 'default', softClass: 'bg-slate-100 text-slate-600', dotClass: 'bg-slate-400' }
}
