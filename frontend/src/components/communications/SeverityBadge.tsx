import { cn } from '@/utils/cn'
import type { NotificationSeverity } from '@/types/communications'

interface Props {
  severity: NotificationSeverity
  className?: string
}

const CONFIG: Record<NotificationSeverity, { label: string; className: string; dot: string }> = {
  info:     { label: 'Info',     className: 'bg-blue-50 text-blue-700 ring-blue-200',    dot: 'bg-blue-400' },
  medium:   { label: 'Medium',   className: 'bg-amber-50 text-amber-700 ring-amber-200', dot: 'bg-amber-400' },
  high:     { label: 'High',     className: 'bg-orange-50 text-orange-700 ring-orange-200', dot: 'bg-orange-400' },
  critical: { label: 'Critical', className: 'bg-red-50 text-red-700 ring-red-200',       dot: 'bg-red-500' },
}

export function SeverityBadge({ severity, className }: Props) {
  const cfg = CONFIG[severity] ?? CONFIG.info
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset',
        cfg.className,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', cfg.dot)} />
      {cfg.label}
    </span>
  )
}

export function SeverityDot({ severity, className }: { severity: NotificationSeverity; className?: string }) {
  const cfg = CONFIG[severity] ?? CONFIG.info
  return (
    <span
      title={cfg.label}
      className={cn('h-2 w-2 rounded-full flex-shrink-0', cfg.dot, className)}
    />
  )
}
