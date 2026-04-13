import { Tooltip } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

interface Props {
  datetime?: string | null
  className?: string
  short?: boolean
}

export function RelativeTimeText({ datetime, className, short = false }: Props) {
  if (!datetime) return <span className={cn('text-slate-400', className)}>—</span>
  const d = dayjs(datetime)
  const abs = d.format('MMM D, YYYY HH:mm')
  const rel = short ? d.fromNow(true) : d.fromNow()
  return (
    <Tooltip title={abs}>
      <span className={cn('text-slate-500 text-xs tabular-nums cursor-default', className)}>
        {rel}
      </span>
    </Tooltip>
  )
}
