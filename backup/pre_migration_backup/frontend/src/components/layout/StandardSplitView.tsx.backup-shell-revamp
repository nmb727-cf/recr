import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface StandardSplitViewProps {
  isDetailOpen: boolean
  fullListContent: ReactNode
  compactListContent: ReactNode
  detailContent: ReactNode
  leftOpenWidthClass?: string
  rightOpenWidthClass?: string
  className?: string
}

export function StandardSplitView({
  isDetailOpen,
  fullListContent,
  compactListContent,
  detailContent,
  leftOpenWidthClass = 'w-[25%]',
  rightOpenWidthClass = 'w-[75%]',
  className,
}: StandardSplitViewProps) {
  return (
    <div className={cn('flex-1 flex overflow-hidden', className)}>
      <div
        className={cn(
          'panel-transition h-full flex-shrink-0 bg-white',
          isDetailOpen ? `${leftOpenWidthClass} opacity-100` : 'w-full'
        )}
        style={{ transition: 'width 0.3s ease, opacity 0.3s ease' }}
      >
        {isDetailOpen ? compactListContent : fullListContent}
      </div>

      <div
        className={cn(
          'panel-transition h-full bg-white overflow-hidden border-l border-slate-200 shadow-2xl',
          isDetailOpen ? `${rightOpenWidthClass} opacity-100` : 'w-0 opacity-0 pointer-events-none'
        )}
        style={{ transition: 'width 0.3s ease, opacity 0.3s ease' }}
      >
        {isDetailOpen ? detailContent : null}
      </div>
    </div>
  )
}
