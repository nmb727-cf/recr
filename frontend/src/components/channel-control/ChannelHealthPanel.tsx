import { useState } from 'react'
import { Button, Spin, Tooltip, Empty } from 'antd'
import { CheckCircle, XCircle, AlertTriangle, RefreshCw, Clock, Zap } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { message as antMessage } from 'antd'
import { cn } from '@/utils/cn'
import { channelControlApi } from '@/api/channelControl'
import { useApiQuery } from '@/hooks/useApiQuery'
import type { ChannelHealthMap, ChannelHealthResult } from '@/api/channelControl'
import dayjs from 'dayjs'

const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  sms:      'SMS',
  push:     'Push',
  email:    'Email',
}

const PROVIDER_LABELS: Record<string, string> = {
  whatsapp_business_api: 'WhatsApp Business API',
  twilio_whatsapp:       'Twilio WhatsApp',
  twilio:                'Twilio SMS',
  generic_http:          'Generic HTTP',
  web_push:              'Web Push (VAPID)',
  fcm:                   'Firebase FCM',
  apns:                  'Apple APNs',
  mock:                  'Mock / Dev',
}

function HealthCard({
  channelType,
  result,
  checkedAt,
}: {
  channelType: string
  result: ChannelHealthResult
  checkedAt: string
}) {
  const { healthy, provider, latency_ms, detail } = result
  return (
    <div className={cn(
      'rounded-xl border p-5 flex flex-col gap-3',
      healthy ? 'border-green-200 bg-green-50/30' : 'border-red-200 bg-red-50/30',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-900">
            {CHANNEL_LABELS[channelType] ?? channelType}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {(PROVIDER_LABELS[provider] ?? provider) || 'Unknown provider'}
          </p>
        </div>
        {healthy ? (
          <div className="flex items-center gap-1.5 text-green-600">
            <CheckCircle className="h-5 w-5" />
            <span className="text-sm font-medium">Healthy</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-red-600">
            <XCircle className="h-5 w-5" />
            <span className="text-sm font-medium">Unhealthy</span>
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        {typeof latency_ms === 'number' && (
          <div className="flex items-center gap-1">
            <Zap className="h-3.5 w-3.5" />
            <span>{latency_ms} ms</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          <span>Checked {checkedAt}</span>
        </div>
      </div>

      {/* Detail message */}
      {detail && (
        <p className={cn(
          'text-xs rounded-lg px-3 py-2',
          healthy ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700',
        )}>
          {detail}
        </p>
      )}
    </div>
  )
}

export function ChannelHealthPanel() {
  const queryClient = useQueryClient()
  const [lastChecked, setLastChecked] = useState<string>('')
  const [isRefreshing, setIsRefreshing] = useState(false)

  const { data: healthData, isLoading } = useApiQuery(
    ['channel-health'],
    () => channelControlApi.getChannelHealth(),
    { staleTime: 30_000 },
  )

  const health = healthData as ChannelHealthMap | undefined

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await queryClient.invalidateQueries({ queryKey: ['channel-health'] })
      setLastChecked(dayjs().format('HH:mm:ss'))
      antMessage.success('Health check refreshed')
    } finally {
      setIsRefreshing(false)
    }
  }

  // Filter out the synthetic 'status' key if no configs found
  const entries = Object.entries(health ?? {}).filter(
    ([k]) => k !== 'status' && !k.startsWith('_'),
  ) as [string, ChannelHealthResult][]

  const checkedAtLabel = lastChecked || dayjs().format('HH:mm')

  return (
    <div className="bg-white rounded-xl border border-slate-200">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Channel health</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time connection check for all configured channel providers.
          </p>
        </div>
        <Button
          size="small"
          icon={<RefreshCw className={cn('h-3.5 w-3.5', isRefreshing && 'animate-spin')} />}
          onClick={handleRefresh}
          loading={isRefreshing}
        >
          Check now
        </Button>
      </div>

      <div className="p-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Spin />
          </div>
        ) : entries.length === 0 ? (
          <Empty
            description={
              <div className="text-center">
                <p className="text-sm text-slate-600">No channel providers configured</p>
                <p className="text-xs text-slate-400 mt-1">
                  Add WhatsApp or SMS providers in the Channel Settings tab to see health status here.
                </p>
              </div>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {entries.map(([channelType, result]) => (
              <HealthCard
                key={channelType}
                channelType={channelType}
                result={result}
                checkedAt={checkedAtLabel}
              />
            ))}
          </div>
        )}

        {/* No-config hint */}
        {!isLoading && entries.length === 0 && health && 'status' in (health as any) && (
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-400 bg-slate-50 rounded-lg px-4 py-3">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{(health as any).status}</span>
          </div>
        )}
      </div>
    </div>
  )
}
