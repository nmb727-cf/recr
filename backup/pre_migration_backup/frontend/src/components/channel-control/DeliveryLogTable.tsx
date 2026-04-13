import { useState } from 'react'
import { Table, Select, Button, Tooltip, Empty, Spin, Input, DatePicker } from 'antd'
import { RotateCcw, ChevronRight, AlertCircle } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { message as antMessage } from 'antd'
import dayjs from 'dayjs'
import { cn } from '@/utils/cn'
import { DeliveryStatusBadge } from './DeliveryStatusBadge'
import { channelControlApi } from '@/api/channelControl'
import { useApiQuery } from '@/hooks/useApiQuery'
import type { CommunicationDelivery, ChannelType, DeliveryStatus } from '@/api/channelControl'

const { RangePicker } = DatePicker

const CHANNEL_OPTIONS = [
  { value: '',          label: 'All channels' },
  { value: 'in_app',   label: 'In-app' },
  { value: 'email',    label: 'Email' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'sms',      label: 'SMS' },
  { value: 'push',     label: 'Push' },
]

const STATUS_OPTIONS = [
  { value: '',          label: 'All statuses' },
  { value: 'pending',   label: 'Pending' },
  { value: 'sent',      label: 'Sent' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'failed',    label: 'Failed' },
  { value: 'deferred',  label: 'Deferred' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'skipped',   label: 'Skipped' },
]

const CHANNEL_LABELS: Record<string, string> = {
  in_app:   'In-app',
  email:    'Email',
  whatsapp: 'WhatsApp',
  sms:      'SMS',
  push:     'Push',
}

const CHANNEL_DOT: Record<string, string> = {
  in_app:   'bg-indigo-400',
  email:    'bg-blue-400',
  whatsapp: 'bg-green-400',
  sms:      'bg-amber-400',
  push:     'bg-teal-400',
}

interface DeliveryDetailRowProps {
  delivery: CommunicationDelivery
  onRetry: (id: string) => void
  isRetrying: boolean
}

function DeliveryDetailRow({ delivery, onRetry, isRetrying }: DeliveryDetailRowProps) {
  return (
    <div className="px-6 py-3 bg-slate-50 border-b border-slate-100 text-xs space-y-1.5">
      {delivery.error_message && (
        <div className="flex items-start gap-2 text-red-700">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
          <span className="font-mono">{delivery.error_message}</span>
        </div>
      )}
      {delivery.external_message_id && (
        <p className="text-slate-500">
          External ID: <span className="font-mono text-slate-700">{delivery.external_message_id}</span>
        </p>
      )}
      {delivery.skip_reason && (
        <p className="text-slate-500">
          Skip reason: <span className="text-slate-700">{delivery.skip_reason}</span>
        </p>
      )}
      {delivery.template_used && (
        <p className="text-slate-500">
          Template: <span className="text-slate-700">{delivery.template_used}</span>
        </p>
      )}
      {(delivery.status === 'failed' || delivery.status === 'deferred') && (
        <Button
          size="small"
          icon={<RotateCcw className="h-3 w-3" />}
          onClick={() => onRetry(delivery.id)}
          loading={isRetrying}
          className="mt-1"
        >
          Retry delivery
        </Button>
      )}
    </div>
  )
}

export function DeliveryLogTable() {
  const queryClient = useQueryClient()
  const [channelFilter, setChannelFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [search, setSearch] = useState('')
  const [retryingId, setRetryingId] = useState<string | null>(null)
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  const queryKey = ['channel-deliveries', channelFilter, statusFilter]
  const { data: deliveriesData, isLoading } = useApiQuery(
    queryKey,
    () => channelControlApi.listDeliveries({
      ...(channelFilter ? { channel_type: channelFilter as ChannelType } : {}),
      ...(statusFilter  ? { status: statusFilter as DeliveryStatus }   : {}),
    }),
    { staleTime: 15_000 },
  )

  const rawDeliveries = (deliveriesData as any)?.results ?? []
  const deliveries: CommunicationDelivery[] = search.trim()
    ? rawDeliveries.filter((d: CommunicationDelivery) =>
        d.recipient_user_id?.includes(search) ||
        d.notification_id?.includes(search) ||
        d.template_used?.toLowerCase().includes(search.toLowerCase()) ||
        d.provider?.toLowerCase().includes(search.toLowerCase()),
      )
    : rawDeliveries

  const handleRetry = async (id: string) => {
    setRetryingId(id)
    try {
      await channelControlApi.retryDelivery(id)
      antMessage.success('Retry queued')
      queryClient.invalidateQueries({ queryKey })
    } catch {
      antMessage.error('Failed to queue retry')
    } finally {
      setRetryingId(null)
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedRows((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const columns = [
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (v: string) => (
        <span className="text-xs text-slate-500 whitespace-nowrap">
          {dayjs(v).format('MMM D, HH:mm')}
        </span>
      ),
    },
    {
      title: 'Channel',
      dataIndex: 'channel_type',
      key: 'channel_type',
      width: 110,
      render: (ch: string) => (
        <div className="flex items-center gap-1.5">
          <div className={cn('w-2 h-2 rounded-full flex-shrink-0', CHANNEL_DOT[ch] ?? 'bg-slate-300')} />
          <span className="text-xs font-medium text-slate-700">{CHANNEL_LABELS[ch] ?? ch}</span>
        </div>
      ),
    },
    {
      title: 'Recipient',
      dataIndex: 'recipient_user_id',
      key: 'recipient',
      render: (uid: string | null) => (
        <span className="text-xs font-mono text-slate-500 truncate max-w-[120px] block">
          {uid ? uid.slice(0, 8) + '…' : '—'}
        </span>
      ),
    },
    {
      title: 'Provider',
      dataIndex: 'provider',
      key: 'provider',
      width: 120,
      render: (p: string) => (
        <span className="text-xs text-slate-600 capitalize">{p || '—'}</span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (s: DeliveryStatus) => <DeliveryStatusBadge status={s} />,
    },
    {
      title: 'Attempts',
      dataIndex: 'attempt_number',
      key: 'attempt_number',
      width: 80,
      render: (n: number) => (
        <span className="text-xs text-slate-500">{n}</span>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (p: string) => (
        <span className={cn(
          'text-xs capitalize',
          p === 'critical' ? 'text-red-600 font-medium'
          : p === 'high'  ? 'text-amber-600'
          : 'text-slate-500',
        )}>{p}</span>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 36,
      render: (_: unknown, record: CommunicationDelivery) => (
        <Button
          type="text"
          size="small"
          icon={
            <ChevronRight
              className={cn(
                'h-4 w-4 text-slate-400 transition-transform',
                expandedRows.includes(record.id) && 'rotate-90',
              )}
            />
          }
          onClick={() => toggleExpand(record.id)}
        />
      ),
    },
  ]

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Filters bar */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-100 flex-wrap">
        <h3 className="text-sm font-semibold text-slate-900 flex-shrink-0">Delivery logs</h3>
        <Select
          value={channelFilter}
          onChange={setChannelFilter}
          options={CHANNEL_OPTIONS}
          size="small"
          className="w-36"
          popupMatchSelectWidth={false}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_OPTIONS}
          size="small"
          className="w-36"
          popupMatchSelectWidth={false}
        />
        <Input
          placeholder="Search recipient, provider, template…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          size="small"
          className="w-64"
        />
        <Button
          size="small"
          onClick={() => queryClient.invalidateQueries({ queryKey })}
          icon={<RotateCcw className="h-3.5 w-3.5" />}
          className="ml-auto"
        >
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Spin />
        </div>
      ) : (
        <Table
          dataSource={deliveries}
          columns={columns}
          rowKey="id"
          loading={false}
          pagination={{ pageSize: 50, showSizeChanger: false, size: 'small' }}
          size="small"
          locale={{
            emptyText: (
              <Empty
                description={
                  channelFilter || statusFilter
                    ? 'No deliveries match your filters'
                    : 'No deliveries recorded yet'
                }
              />
            ),
          }}
          expandable={{
            expandedRowKeys: expandedRows,
            expandedRowRender: (record) => (
              <DeliveryDetailRow
                delivery={record}
                onRetry={handleRetry}
                isRetrying={retryingId === record.id}
              />
            ),
            showExpandColumn: false,
          }}
          rowClassName={(record) =>
            record.status === 'failed' || record.status === 'bounced'
              ? 'bg-red-50/40'
              : ''
          }
        />
      )}

      {/* Stats row */}
      {deliveries.length > 0 && (
        <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center gap-4">
          <span className="text-xs text-slate-500">{deliveries.length} records shown</span>
          {['failed', 'deferred'].map((st) => {
            const count = deliveries.filter((d: CommunicationDelivery) => d.status === st).length
            return count > 0 ? (
              <span key={st} className={cn(
                'text-xs font-medium',
                st === 'failed' ? 'text-red-600' : 'text-amber-600',
              )}>
                {count} {st}
              </span>
            ) : null
          })}
        </div>
      )}
    </div>
  )
}
