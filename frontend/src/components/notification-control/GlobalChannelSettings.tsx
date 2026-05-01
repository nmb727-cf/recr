import { Switch, Spin, message as antMessage } from 'antd'
import { Smartphone, Mail, MessageCircle, Bell } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { ChannelSetting } from '@/api/notificationControl'

interface Props {
  settings: ChannelSetting[]
  isLoading: boolean
  onToggle: (channelType: string, enabled: boolean) => Promise<void>
}

const CHANNEL_META: Record<string, { label: string; desc: string; icon: React.ReactNode; comingSoon?: boolean }> = {
  in_app: {
    label: 'In-app notifications',
    desc: 'Real-time notifications shown in the platform',
    icon: <Bell className="h-5 w-5" />,
  },
  email: {
    label: 'Email notifications',
    desc: 'Fallback and digest emails when notifications are unread',
    icon: <Mail className="h-5 w-5" />,
  },
  whatsapp: {
    label: 'WhatsApp',
    desc: 'WhatsApp messages for high-priority alerts (requires WhatsApp provider config)',
    icon: <MessageCircle className="h-5 w-5" />,
  },
  sms: {
    label: 'SMS',
    desc: 'SMS escalation for critical notifications (requires SMS provider config)',
    icon: <Smartphone className="h-5 w-5" />,
  },
}

const CHANNEL_ORDER = ['in_app', 'email', 'whatsapp', 'sms']

export function GlobalChannelSettings({ settings, isLoading, onToggle }: Props) {
  const settingsByType = Object.fromEntries(settings.map((s) => [s.channel_type, s]))

  return (
    <div className="bg-white rounded-xl border border-slate-200">
      <div className="px-5 py-4 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-900">Global channel controls</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Disable a channel to stop all notifications of that type, regardless of individual rule settings.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Spin size="small" />
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {CHANNEL_ORDER.map((ch) => {
            const meta = CHANNEL_META[ch]
            const setting = settingsByType[ch]
            const isEnabled = setting?.is_enabled ?? false

            return (
              <div key={ch} className="flex items-center justify-between px-5 py-3.5">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                    isEnabled && !meta.comingSoon ? 'bg-indigo-50 text-indigo-500' : 'bg-slate-100 text-slate-400',
                  )}>
                    {meta.icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-slate-800">{meta.label}</p>
                      {meta.comingSoon && (
                        <span className="text-[10px] bg-slate-100 text-slate-500 rounded-full px-2 py-0.5 font-medium uppercase tracking-wide">
                          Coming soon
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{meta.desc}</p>
                  </div>
                </div>
                <Switch
                  checked={isEnabled}
                  disabled={!!meta.comingSoon}
                  onChange={(checked) => onToggle(ch, checked)}
                  size="small"
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
