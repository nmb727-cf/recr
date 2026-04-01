import { useState } from 'react'
import {
  Button, Input, Typography, Card,
  Tag, Spin, Badge, message, Modal, Table,
  Tooltip, Avatar, Divider, Empty, Space
} from 'antd'
import {
  Plus,
  Search,
  Calendar,
  MapPin,
  Users,
  RefreshCw,
  MoreVertical,
  Copy,
  Archive,
  Eye,
  Edit,
  Zap,
  Globe,
  Briefcase
} from 'lucide-react'
import dayjs from 'dayjs'
import { useTranslation } from 'react-i18next'
import { cn } from '@/utils/cn'
import { useNavigate } from 'react-router-dom'
import WalkinDriveWizard from './WalkinDriveWizard'

const { Text, Title } = Typography

export default function WalkinDrivesList() {
  const { t } = useTranslation(['interviews', 'common'])
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [isWizardOpen, setIsWizardOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Mock data for initial implementation
  const [drives] = useState([
    {
      id: '1',
      name: 'Q2 Engineering Mega Drive',
      role: 'Full Stack Engineer',
      date: '2026-04-15',
      location: 'Bangalore Office',
      mode: 'onsite',
      status: 'upcoming',
      candidateCount: 120,
      lastUpdated: '2026-04-01T10:00:00Z'
    },
    {
      id: '2',
      name: 'Graduate Campus Hiring 2026',
      role: 'Associate Software Engineer',
      date: '2026-05-10',
      location: 'Virtual',
      mode: 'virtual',
      status: 'draft',
      candidateCount: 450,
      lastUpdated: '2026-04-01T12:00:00Z'
    }
  ])

  const columns = [
    {
      title: 'Drive Name',
      key: 'name',
      render: (_: any, record: any) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <Zap size={20} />
          </div>
          <div>
            <Text className="block font-black text-slate-800 uppercase tracking-tight">{record.name}</Text>
            <Text className="text-[10px] text-slate-400 font-bold uppercase">{record.id}</Text>
          </div>
        </div>
      )
    },
    {
      title: 'Role / Domain',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <div className="flex items-center gap-2">
          <Briefcase size={14} className="text-slate-400" />
          <Text className="text-xs font-bold text-slate-600">{role}</Text>
        </div>
      )
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => (
        <div className="flex items-center gap-2">
          <Calendar size={14} className="text-slate-400" />
          <Text className="text-xs font-bold text-slate-600">{dayjs(date).format('MMM D, YYYY')}</Text>
        </div>
      )
    },
    {
      title: 'Location / Mode',
      key: 'location',
      render: (_: any, record: any) => (
        <div className="flex items-center gap-2">
          {record.mode === 'virtual' ? <Globe size={14} className="text-blue-500" /> : <MapPin size={14} className="text-orange-500" />}
          <Text className="text-xs font-bold text-slate-600 uppercase tracking-tighter">{record.location}</Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: any = {
          upcoming: 'bg-blue-50 text-blue-600 border-blue-100',
          draft: 'bg-slate-50 text-slate-500 border-slate-100',
          active: 'bg-emerald-50 text-emerald-600 border-emerald-100',
          archived: 'bg-rose-50 text-rose-600 border-rose-100',
        }
        return (
          <span className={cn("px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest border", colors[status] || colors.draft)}>
            {status}
          </span>
        )
      }
    },
    {
      title: 'Candidates',
      dataIndex: 'candidateCount',
      key: 'candidates',
      align: 'center' as const,
      render: (count: number) => (
        <div className="flex flex-col items-center">
          <Text className="text-sm font-black text-slate-800">{count}</Text>
          <Text className="text-[9px] text-slate-400 font-black uppercase tracking-widest">Registered</Text>
        </div>
      )
    },
    {
      title: 'Last Updated',
      dataIndex: 'lastUpdated',
      key: 'updated',
      render: (date: string) => (
        <Text className="text-[10px] text-slate-400 font-medium">{dayjs(date).fromNow()}</Text>
      )
    },
    {
      title: '',
      key: 'actions',
      align: 'right' as const,
      render: () => (
        <Space>
          <Tooltip title="Preview">
            <Button type="text" size="small" icon={<Eye size={14} />} className="text-slate-400" />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button type="text" size="small" icon={<Copy size={14} />} className="text-slate-400" />
          </Tooltip>
          <Button type="text" size="small" icon={<MoreVertical size={14} />} className="text-slate-400" />
        </Space>
      )
    }
  ]

  return (
    <div className="p-6 bg-[#F8FAFC] min-h-[calc(100vh-56px)]">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="text-indigo-600" size={20} />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight uppercase tracking-widest">Walk-in Drive Registry</h1>
          </div>
          <p className="text-slate-500 text-xs font-bold uppercase tracking-widest opacity-60">High-Volume Interview Event Engine</p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            onClick={() => setIsWizardOpen(true)}
            type="primary" 
            icon={<Plus size={16} />} 
            className="h-10 px-6 bg-indigo-600 hover:bg-indigo-700 border-none rounded-xl shadow-indigo-100 shadow-xl font-black text-[10px] uppercase tracking-widest"
          >
            Create Walk-in Drive
          </Button>
          <Button 
            icon={<RefreshCw size={16} className={cn(isLoading && "animate-spin")} />} 
            className="h-10 w-10 flex items-center justify-center rounded-xl border-slate-200 text-slate-400" 
          />
        </div>
      </div>

      <div className="mb-6 flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search drives by name, role or location..."
            className="w-full h-11 pl-10 pr-4 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 outline-none focus:border-indigo-300 transition-all shadow-soft-sm"
          />
        </div>
        <div className="flex gap-2">
           {['All', 'Upcoming', 'Active', 'Draft', 'Archived'].map(f => (
             <button key={f} className="px-4 h-11 rounded-xl bg-white border border-slate-200 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:bg-slate-50 transition-all shadow-soft-sm">
               {f}
             </button>
           ))}
        </div>
      </div>

      <Card className="rounded-3xl border-none shadow-soft-lg overflow-hidden" bodyStyle={{ padding: 0 }}>
        <Table 
          dataSource={drives} 
          columns={columns} 
          rowKey="id" 
          pagination={{ pageSize: 10, position: ['bottomCenter'] }}
          className="modern-table"
        />
      </Card>

      <WalkinDriveWizard 
        open={isWizardOpen} 
        onClose={() => setIsWizardOpen(false)} 
        onSuccess={() => {
          setIsWizardOpen(false)
          message.success('Walk-in Drive created successfully')
        }} 
      />
    </div>
  )
}
