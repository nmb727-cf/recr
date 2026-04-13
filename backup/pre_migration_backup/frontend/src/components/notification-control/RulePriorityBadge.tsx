import { cn } from '@/utils/cn'
import type { RulePriority } from '@/api/notificationControl'

interface Props {
  priority: RulePriority
  size?: 'sm' | 'xs'
}

const PRIORITY_STYLES: Record<RulePriority, string> = {
  info:     'bg-slate-100 text-slate-600',
  medium:   'bg-blue-50 text-blue-700',
  high:     'bg-amber-50 text-amber-700',
  critical: 'bg-red-50 text-red-700',
}

const PRIORITY_LABELS: Record<RulePriority, string> = {
  info:     'Info',
  medium:   'Medium',
  high:     'High',
  critical: 'Critical',
}

export function RulePriorityBadge({ priority, size = 'sm' }: Props) {
  return (
    <span className={cn(
      'inline-flex items-center rounded-full font-medium',
      size === 'xs' ? 'text-[10px] px-1.5 py-px' : 'text-xs px-2 py-0.5',
      PRIORITY_STYLES[priority],
    )}>
      {PRIORITY_LABELS[priority]}
    </span>
  )
}
