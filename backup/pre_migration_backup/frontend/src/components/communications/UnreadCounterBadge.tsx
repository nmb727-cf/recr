import { cn } from '@/utils/cn'

interface Props {
  count: number
  max?: number
  className?: string
  size?: 'sm' | 'md'
}

export function UnreadCounterBadge({ count, max = 99, className, size = 'sm' }: Props) {
  if (count <= 0) return null
  const display = count > max ? `${max}+` : String(count)
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full font-semibold bg-indigo-600 text-white',
        size === 'sm' ? 'min-w-[18px] h-[18px] px-1 text-[10px]' : 'min-w-[22px] h-[22px] px-1.5 text-xs',
        className,
      )}
    >
      {display}
    </span>
  )
}
