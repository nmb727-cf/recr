import { Switch, Spin, Button, Tag, Tooltip } from 'antd'
import { Bell, Mail, MessageCircle, Smartphone, Settings, Plus, CheckCircle, XCircle, Clock } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { ChannelSetting } from '@/api/notificationControl'
import type { TenantChannelConfig } from '@/api/channelControl'

interface Props {
  channelSettings: ChannelSetting[]
  channelConfigs: TenantChannelConfig[]
  isLoadingSettings: boolean
  isLoadingConfigs: boolean
  onToggle: (channelType: string, enabled: boolean) => Promise<void>
  onEditConfig: (config: TenantChannelConfig) => void
  onNewConfig: (channelType: 'whatsapp' | 'sms' | 'push') => void
}

const CHANNEL_META: Record<string, {
  label: string
  desc: string
  icon: React.ReactNode
  iconColor: string
  canConfigure: boolean
}> = {
  in_app: {
    label: 'In-app notifications',
    desc: 'Real-time alerts shown inside the platform to logged-in users.',
    icon: <Bell className="h-5 w-5" />,
    iconColor: 'bg-indigo-50 text-indigo-500',
    canConfigure: false,
  },
  email: {
    label: 'Email',
    desc: 'Email notifications sent when in-app alerts are unread, or for digest summaries.',
    icon: <Mail className="h-5 w-5" />,
    iconColor: 'bg-blue-50 text-blue-500',
    canConfigure: false,
  },
  whatsapp: {
    label: 'WhatsApp',
    desc: 'WhatsApp messages for high-priority and time-sensitive alerts.',
    icon: <MessageCircle className="h-5 w-5" />,
    iconColor: 'bg-green-50 text-green-500',
    canConfigure: true,
  },
  sms: {
    label: 'SMS',
    desc: 'SMS text messages for critical escalations when other channels are unread.',
    icon: <Smartphone className="h-5 w-5" />,
    iconColor: 'bg-amber-50 text-amber-600',
    canConfigure: true,
  },
  push: {
    label: 'Push notifications',
    desc: 'Browser and mobile push notifications. Architecture is ready — provider config coming soon.',
    icon: <Bell className="h-5 w-5" />,
    iconColor: 'bg-slate-100 text-slate-400',
    canConfigure: true,
  },
}

const CHANNEL_ORDER = ['in_app', 'email', 'whatsapp', 'sms', 'push']

const PROVIDER_LABELS: Record<string, string> = {
  whatsapp_business_api: 'WhatsApp Business API',
  twilio_whatsapp:       'Twilio WhatsApp',
  twilio:                'Twilio SMS',
  generic_http:          'Generic HTTP Gateway',
  web_push:              'Web Push (VAPID)',
  fcm:                   'Firebase FCM',
  apns:                  'Apple APNs',
  mock:                  'Mock / Dev',
}

function ConfigChip({ config, onEdit }: { config: TenantChannelConfig; onEdit: () => void }) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors text-xs',
        config.is_active
          ? 'border-green-200 bg-green-50 hover:bg-green-100'
          : 'border-slate-200 bg-slate-50 hover:bg-slate-100',
      )}
      onClick={onEdit}
    >
      {config.is_active ? (
        <CheckCircle className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
      ) : (
        <XCircle className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
      )}
      <span className="font-medium text-slate-700 truncate max-w-[160px]">
        {PROVIDER_LABELS[config.provider] || config.provider}
      </span>
      {config.sender_identifier && (
        <span className="text-slate-400 font-mono truncate max-w-[100px]">
          {config.sender_identifier}
        </span>
      )}
      <Settings className="h-3 w-3 text-slate-400 flex-shrink-0 ml-auto" />
    </div>
  )
}

export function ChannelSettingsPanel({
  channelSettings,
  channelConfigs,
  isLoadingSettings,
  isLoadingConfigs,
  onToggle,
  onEditConfig,
  onNewConfig,
}: Props) {
  const settingsByType = Object.fromEntries(channelSettings.map((s) => [s.channel_type, s]))
  const configsByType: Record<string, TenantChannelConfig[]> = {}
  for (const cfg of channelConfigs) {
    if (!configsByType[cfg.channel_type]) configsByType[cfg.channel_type] = []
    configsByType[cfg.channel_type].push(cfg)
  }

  const isLoading = isLoadingSettings || isLoadingConfigs

  return (
    <div className="bg-white rounded-xl border border-slate-200">
      <div className="px-5 py-4 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-900">Channel settings</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Enable channels globally and configure their delivery providers.
          Disabling a channel stops all delivery for that channel regardless of individual rule settings.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spin />
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {CHANNEL_ORDER.map((ch) => {
            const meta = CHANNEL_META[ch]
            const setting = settingsByType[ch]
            const isEnabled = setting?.is_enabled ?? false
            const configs = configsByType[ch] ?? []

            return (
              <div key={ch} className="px-5 py-4">
                {/* Top row: icon + label + toggle */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', meta.iconColor)}>
                      {meta.icon}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-900">{meta.label}</p>
                        {ch === 'push' && (
                          <Tag color="default" className="text-[10px] !leading-none">Future-ready</Tag>
                        )}
                        {isEnabled && <Tag color="success" className="text-[10px] !leading-none">Active</Tag>}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{meta.desc}</p>
                    </div>
                  </div>
                  <Tooltip title={!setting ? 'Channel not yet initialized' : undefined}>
                    <Switch
                      checked={isEnabled}
                      size="small"
                      disabled={!setting}
                      onChange={(checked) => onToggle(ch, checked)}
                    />
                  </Tooltip>
                </div>

                {/* Provider configs row */}
                {meta.canConfigure && (
                  <div className="mt-3 ml-13 flex flex-wrap gap-2 pl-[52px]">
                    {configs.map((cfg) => (
                      <ConfigChip key={cfg.id} config={cfg} onEdit={() => onEditConfig(cfg)} />
                    ))}
                    <button
                      onClick={() => onNewConfig(ch as 'whatsapp' | 'sms' | 'push')}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dashed border-slate-300 text-xs text-slate-500 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      {configs.length === 0 ? 'Set up provider' : 'Add provider'}
                    </button>
                  </div>
                )}

                {/* Email: show configured sender info from channel setting */}
                {ch === 'email' && setting?.sender_email && (
                  <div className="mt-2 pl-[52px]">
                    <span className="text-xs text-slate-500">
                      Default sender: <span className="font-medium text-slate-700">{setting.sender_name || setting.sender_email}</span>
                      {' '}<span className="font-mono text-slate-400">({setting.sender_email})</span>
                    </span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
