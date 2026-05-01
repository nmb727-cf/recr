import { useNavigate } from 'react-router-dom'
import { cn } from '@/utils/cn'
import { ENTITY_LABELS, ENTITY_ROUTES } from '@/types/communications'
import {
  User, Briefcase, Calendar, FileText, Building2, Gift, Link2,
} from 'lucide-react'

interface Props {
  entityType?: string | null
  entityId?: string | null
  label?: string
  className?: string
  clickable?: boolean
}

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  candidate: User,
  application: FileText,
  job: Briefcase,
  interview: Calendar,
  offer: Gift,
  agency_submission: Building2,
  agency_relationship: Building2,
}

const CHIP_COLORS: Record<string, string> = {
  candidate:          'bg-violet-50 text-violet-700 ring-violet-200',
  application:        'bg-indigo-50 text-indigo-700 ring-indigo-200',
  job:                'bg-blue-50 text-blue-700 ring-blue-200',
  interview:          'bg-orange-50 text-orange-700 ring-orange-200',
  offer:              'bg-emerald-50 text-emerald-700 ring-emerald-200',
  agency_submission:  'bg-teal-50 text-teal-700 ring-teal-200',
  agency_relationship:'bg-teal-50 text-teal-700 ring-teal-200',
}

export function EntityContextChip({ entityType, entityId, label, className, clickable = false }: Props) {
  const navigate = useNavigate()
  if (!entityType) return null

  const Icon = ICONS[entityType] ?? Link2
  const displayLabel = label || ENTITY_LABELS[entityType] || entityType
  const colorClass = CHIP_COLORS[entityType] ?? 'bg-slate-50 text-slate-700 ring-slate-200'

  const handleClick = () => {
    if (!clickable || !entityId) return
    const base = ENTITY_ROUTES[entityType]
    if (base) navigate(`${base}/${entityId}`)
  }

  return (
    <span
      onClick={handleClick}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset',
        colorClass,
        clickable && entityId ? 'cursor-pointer hover:opacity-80 transition-opacity' : '',
        className,
      )}
    >
      <Icon className="h-3 w-3" />
      {displayLabel}
    </span>
  )
}
