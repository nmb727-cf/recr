import { Tooltip, Tag } from 'antd'
import { ArrowRight, Clock, AlertTriangle } from 'lucide-react'
import { cn } from '@/utils/cn'

/**
 * Displays the default channel routing policy by priority.
 * This mirrors the hardcoded defaults in channel_routing.py.
 * Per-trigger overrides are managed via Notification Rules (Trigger Mapping tab).
 */

interface ChannelChip {
  type: string
  label: string
  color: string
}

interface RoutingRow {
  priority: string
  priorityColor: string
  priorityLabel: string
  immediate: ChannelChip[]
  fallback: ChannelChip[]
  fallbackDelay?: string
  escalation: ChannelChip[]
  escalationDelay?: string
  description: string
}

const CH: Record<string, ChannelChip> = {
  in_app:   { type: 'in_app',   label: 'In-app',   color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  email:    { type: 'email',    label: 'Email',    color: 'bg-blue-50 text-blue-700 border-blue-200' },
  whatsapp: { type: 'whatsapp', label: 'WhatsApp', color: 'bg-green-50 text-green-700 border-green-200' },
  sms:      { type: 'sms',      label: 'SMS',      color: 'bg-amber-50 text-amber-700 border-amber-200' },
}

const ROWS: RoutingRow[] = [
  {
    priority: 'info',
    priorityColor: 'bg-slate-100 text-slate-600',
    priorityLabel: 'Info',
    immediate: [CH.in_app],
    fallback: [],
    escalation: [],
    description: 'Informational alerts shown in-app only. No follow-up.',
  },
  {
    priority: 'low',
    priorityColor: 'bg-slate-100 text-slate-600',
    priorityLabel: 'Low',
    immediate: [CH.in_app],
    fallback: [],
    escalation: [],
    description: 'Low-importance alerts — in-app only. No follow-up needed.',
  },
  {
    priority: 'medium',
    priorityColor: 'bg-blue-50 text-blue-700',
    priorityLabel: 'Medium',
    immediate: [CH.in_app, CH.email],
    fallback: [CH.email],
    fallbackDelay: '40 min',
    escalation: [],
    description: 'Standard alerts. Email sent immediately as fallback; a reminder sent after 40 min if unread.',
  },
  {
    priority: 'high',
    priorityColor: 'bg-amber-50 text-amber-700',
    priorityLabel: 'High',
    immediate: [CH.in_app, CH.email],
    fallback: [CH.whatsapp],
    fallbackDelay: '10 min',
    escalation: [],
    escalationDelay: '1 hr after fallback',
    description: 'Time-sensitive alerts. WhatsApp follow-up after 10 min if unread.',
  },
  {
    priority: 'critical',
    priorityColor: 'bg-red-50 text-red-700',
    priorityLabel: 'Critical',
    immediate: [CH.in_app, CH.email],
    fallback: [CH.whatsapp],
    fallbackDelay: '1 min',
    escalation: [CH.sms],
    escalationDelay: '5 min after WhatsApp',
    description: 'Urgent escalations. WhatsApp after 1 min, SMS escalation after 5 min if still unread.',
  },
]

function ChannelChipEl({ chip }: { chip: ChannelChip }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-medium', chip.color)}>
      {chip.label}
    </span>
  )
}

function ChainCell({
  chips,
  delay,
  fallbackLabel,
}: {
  chips: ChannelChip[]
  delay?: string
  fallbackLabel?: string
}) {
  if (chips.length === 0) return <span className="text-slate-300 text-xs">—</span>

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center flex-wrap gap-1">
        {chips.map((c) => <ChannelChipEl key={c.type} chip={c} />)}
      </div>
      {delay && (
        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <Clock className="h-3 w-3" />
          {fallbackLabel ? `${fallbackLabel} after ` : 'after '}
          <span className="font-medium text-slate-600">{delay}</span>
          <span>if unread</span>
        </div>
      )}
    </div>
  )
}

export function ChannelRoutingTable() {
  return (
    <div className="bg-white rounded-xl border border-slate-200">
      <div className="px-5 py-4 border-b border-slate-100">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Channel routing by priority</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Default routing policy applied to all notifications. Override per-trigger via Notification Rules.
            </p>
          </div>
          <Tooltip title="These are system defaults. To override a specific trigger, use the Trigger Mapping tab.">
            <div className="flex items-center gap-1 text-xs text-slate-400 cursor-help">
              <AlertTriangle className="h-3.5 w-3.5" />
              Read-only defaults
            </div>
          </Tooltip>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide w-24">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Immediate channels</th>
              <th className="px-2 py-3 w-6"></th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Fallback</th>
              <th className="px-2 py-3 w-6"></th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Escalation</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide hidden xl:table-cell">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {ROWS.map((row) => (
              <tr key={row.priority} className="hover:bg-slate-50 transition-colors">
                <td className="px-5 py-3.5">
                  <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', row.priorityColor)}>
                    {row.priorityLabel}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex items-center flex-wrap gap-1">
                    {row.immediate.map((c) => <ChannelChipEl key={c.type} chip={c} />)}
                  </div>
                </td>
                <td className="px-2 py-3.5 text-slate-300">
                  {row.fallback.length > 0 && <ArrowRight className="h-4 w-4" />}
                </td>
                <td className="px-4 py-3.5">
                  <ChainCell chips={row.fallback} delay={row.fallbackDelay} />
                </td>
                <td className="px-2 py-3.5 text-slate-300">
                  {row.escalation.length > 0 && <ArrowRight className="h-4 w-4" />}
                </td>
                <td className="px-4 py-3.5">
                  <ChainCell chips={row.escalation} delay={row.escalationDelay} />
                </td>
                <td className="px-5 py-3.5 text-xs text-slate-500 hidden xl:table-cell max-w-xs">
                  {row.description}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 rounded-b-xl">
        <p className="text-[11px] text-slate-400">
          <strong>How it works:</strong> When a notification is created, the engine immediately sends via the immediate channels.
          If the notification remains unread after the fallback delay, the fallback channel fires.
          If still unread after the escalation delay, the escalation channel fires.
          Reading the notification cancels all pending follow-up deliveries.
        </p>
      </div>
    </div>
  )
}
