import { cn } from '@/utils/cn'
import type { DeliveryStatus } from '@/api/channelControl'

interface Props {
  status: DeliveryStatus
  size?: 'sm' | 'xs'
}

const STATUS_CONFIG: Record<
  DeliveryStatus,
  { label: string; classes: string }
> = {
  pending:   { label: 'Pending',   classes: 'bg-slate-100 text-slate-600' },
  sent:      { label: 'Sent',      classes: 'bg-blue-50 text-blue-700' },
  delivered: { label: 'Delivered', classes: 'bg-green-50 text-green-700' },
  read:      { label: 'Read',      classes: 'bg-green-100 text-green-800' },
  failed:    { label: 'Failed',    classes: 'bg-red-50 text-red-700' },
  bounced:   { label: 'Bounced',   classes: 'bg-red-100 text-red-800' },
  deferred:  { label: 'Deferred',  classes: 'bg-amber-50 text-amber-700' },
  cancelled: { label: 'Cancelled', classes: 'bg-slate-100 text-slate-500' },
  skipped:   { label: 'Skipped',   classes: 'bg-slate-50 text-slate-400' },
}

export function DeliveryStatusBadge({ status, size = 'sm' }: Props) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, classes: 'bg-slate-100 text-slate-600' }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium leading-none',
        size === 'xs' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs',
        cfg.classes,
      )}
    >
      {cfg.label}
    </span>
  )
}
