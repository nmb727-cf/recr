import { Spin } from 'antd'
import { Bell, Mail, Shield, ArrowUpCircle, AlertTriangle, CheckCircle } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { NotificationControlSummary } from '@/api/notificationControl'

interface Props {
  summary?: NotificationControlSummary
  isLoading?: boolean
}

interface CardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  color?: 'indigo' | 'green' | 'amber' | 'red' | 'slate'
}

function Card({ icon, label, value, sub, color = 'indigo' }: CardProps) {
  const colorMap = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green:  'bg-green-50 text-green-600',
    amber:  'bg-amber-50 text-amber-600',
    red:    'bg-red-50 text-red-600',
    slate:  'bg-slate-100 text-slate-500',
  }
  return (
    <div className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center gap-4">
      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', colorMap[color])}>
        {icon}
      </div>
      <div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-slate-900 leading-tight">{value}</p>
        {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export function SummaryCards({ summary, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-center h-[88px]">
            <Spin size="small" />
          </div>
        ))}
      </div>
    )
  }

  if (!summary) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <Card
        icon={<Bell className="h-5 w-5" />}
        label="Total rules"
        value={summary.total_rules}
        color="indigo"
      />
      <Card
        icon={<CheckCircle className="h-5 w-5" />}
        label="Active rules"
        value={summary.active_rules}
        sub={`${summary.total_rules - summary.active_rules} inactive`}
        color="green"
      />
      <Card
        icon={<Mail className="h-5 w-5" />}
        label="Email fallback"
        value={summary.fallback_enabled_count}
        sub="rules with email fallback"
        color="indigo"
      />
      <Card
        icon={<ArrowUpCircle className="h-5 w-5" />}
        label="Escalation"
        value={summary.escalation_enabled_count}
        sub="rules with escalation"
        color="amber"
      />
      <Card
        icon={<AlertTriangle className="h-5 w-5" />}
        label="High priority"
        value={summary.high_priority_count}
        sub="high / critical rules"
        color="red"
      />
      <Card
        icon={<Shield className="h-5 w-5" />}
        label="Email channel"
        value={summary.email_channel_enabled ? 'Enabled' : 'Disabled'}
        color={summary.email_channel_enabled ? 'green' : 'slate'}
      />
    </div>
  )
}
