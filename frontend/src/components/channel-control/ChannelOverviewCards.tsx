import { Spin, Tooltip } from 'antd'
import { Mail, MessageCircle, Smartphone, Bell, Activity, AlertTriangle, ArrowDownCircle } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { ChannelSetting } from '@/api/notificationControl'
import type { ChannelStats, TenantChannelConfig } from '@/api/channelControl'
import type { NotificationControlSummary } from '@/api/notificationControl'

interface Props {
  channelSettings: ChannelSetting[]
  channelStats?: ChannelStats
  channelConfigs: TenantChannelConfig[]
  summary?: NotificationControlSummary
  isLoading: boolean
}

interface CardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  color?: 'indigo' | 'green' | 'amber' | 'red' | 'slate' | 'emerald' | 'teal'
  tooltip?: string
}

const colorMap: Record<string, string> = {
  indigo:  'bg-indigo-50 text-indigo-600',
  green:   'bg-green-50 text-green-600',
  amber:   'bg-amber-50 text-amber-700',
  red:     'bg-red-50 text-red-600',
  slate:   'bg-slate-100 text-slate-400',
  emerald: 'bg-emerald-50 text-emerald-600',
  teal:    'bg-teal-50 text-teal-600',
}

function Card({ icon, label, value, sub, color = 'indigo', tooltip }: CardProps) {
  const card = (
    <div className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center gap-4 min-w-0">
      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', colorMap[color])}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 font-medium truncate">{label}</p>
        <p className="text-xl font-bold text-slate-900 leading-tight">{value}</p>
        {sub && <p className="text-[11px] text-slate-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  )
  return tooltip ? <Tooltip title={tooltip}>{card}</Tooltip> : card
}

function channelStatus(settings: ChannelSetting[], type: string): { enabled: boolean; label: string; color: string } {
  const s = settings.find((x) => x.channel_type === type)
  if (!s) return { enabled: false, label: 'Not configured', color: 'slate' }
  return s.is_enabled
    ? { enabled: true, label: 'Active', color: 'green' }
    : { enabled: false, label: 'Disabled', color: 'slate' }
}

function totalFailed(stats?: ChannelStats): number {
  if (!stats) return 0
  let total = 0
  for (const ch of Object.values(stats.channels)) {
    total += (ch['failed'] ?? 0) + (ch['bounced'] ?? 0)
  }
  return total
}

export function ChannelOverviewCards({ channelSettings, channelStats, channelConfigs, summary, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-center h-[88px]">
            <Spin size="small" />
          </div>
        ))}
      </div>
    )
  }

  const email = channelStatus(channelSettings, 'email')
  const whatsapp = channelStatus(channelSettings, 'whatsapp')
  const sms = channelStatus(channelSettings, 'sms')
  const push = channelStatus(channelSettings, 'push')

  const configuredCount = channelConfigs.filter((c) => c.is_active).length
  const failed = totalFailed(channelStats)
  const fallbackCount = summary?.fallback_enabled_count ?? 0

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
      <Card
        icon={<Mail className="h-5 w-5" />}
        label="Email"
        value={email.label}
        color={email.color as any}
      />
      <Card
        icon={<MessageCircle className="h-5 w-5" />}
        label="WhatsApp"
        value={whatsapp.label}
        color={whatsapp.color as any}
        tooltip={!whatsapp.enabled ? 'Configure WhatsApp provider to enable' : undefined}
      />
      <Card
        icon={<Smartphone className="h-5 w-5" />}
        label="SMS"
        value={sms.label}
        color={sms.color as any}
        tooltip={!sms.enabled ? 'Configure SMS provider to enable' : undefined}
      />
      <Card
        icon={<Bell className="h-5 w-5" />}
        label="Push"
        value={push.enabled ? 'Active' : 'Future-ready'}
        sub="Architecture ready"
        color={push.enabled ? 'teal' : 'slate'}
      />
      <Card
        icon={<Activity className="h-5 w-5" />}
        label="Active providers"
        value={configuredCount}
        sub="configured channels"
        color="indigo"
      />
      <Card
        icon={<AlertTriangle className="h-5 w-5" />}
        label="Failed (7 days)"
        value={failed}
        sub="across all channels"
        color={failed > 0 ? 'red' : 'green'}
        tooltip="Failed + bounced deliveries in the last 7 days"
      />
      <Card
        icon={<ArrowDownCircle className="h-5 w-5" />}
        label="Fallback rules"
        value={fallbackCount}
        sub="rules with fallback"
        color="amber"
      />
      <Card
        icon={<Bell className="h-5 w-5" />}
        label="In-app"
        value={channelStatus(channelSettings, 'in_app').label}
        color={channelStatus(channelSettings, 'in_app').color as any}
      />
    </div>
  )
}
