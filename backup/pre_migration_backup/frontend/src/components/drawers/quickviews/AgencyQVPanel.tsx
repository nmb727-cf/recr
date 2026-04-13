import { Button, Tag } from 'antd'
import { Building2, Globe, Mail } from 'lucide-react'
import type { AgencyRelationship, AgencyStatus } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const STATUS_COLOR: Record<AgencyStatus, string> = {
  pending: 'orange', active: 'green', suspended: 'red', terminated: 'default',
}

export default function AgencyQVPanel({ relationship }: { relationship: AgencyRelationship }) {
  const openFullView = useDrawerStore(s => s.openFullView)
  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 shadow-sm border border-blue-100 font-bold text-2xl">
          {relationship.agency?.name?.charAt(0).toUpperCase()}
        </div>
        <Tag color={STATUS_COLOR[relationship.status]} className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {relationship.status}
        </Tag>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{relationship.agency?.name}</h2>
      </div>
      <div className="space-y-4 bg-slate-50/50 rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div className="flex items-center gap-3">
          <Building2 className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Industry</span>
            <span className="text-sm font-bold text-slate-700">{relationship.agency?.industry || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Mail className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Contact Email</span>
            <span className="text-sm font-bold text-slate-700">{relationship.agency?.contact_email || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Globe className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tier</span>
            <span className="text-sm font-bold text-slate-700 capitalize">{relationship.tier}</span>
          </div>
        </div>
      </div>
      <Button type="primary" block className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md mt-4" onClick={() => openFullView()}>
        Open Relationship Details
      </Button>
    </div>
  )
}
