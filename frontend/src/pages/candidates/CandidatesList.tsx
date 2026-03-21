import { useState } from 'react'
import {
  Table, Button, Input, Typography, Row, Col, Card, Drawer, Skeleton, Tag,
} from 'antd'
import {
  Search,
  Plus,
  MapPin,
  Clock,
  MoreHorizontal,
  RefreshCw,
  ArrowLeft
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import type { Candidate } from '@/types'
import { cn } from '@/utils/cn'
import CandidateQuickView from './CandidateQuickView'
import CandidateFullView from './CandidateFullView'

const { Text } = Typography

export default function CandidatesList() {
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table')
  
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const [fullViewOpen, setFullViewOpen] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['candidates', search],
    () => candidatesApi.list({ search: search || undefined })
  )

  const candidates = (data as { candidates: Candidate[] } | undefined)?.candidates ?? []

  const columns: ColumnsType<Candidate> = [
    {
      title: 'Candidate Name',
      key: 'name',
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 font-bold text-sm">
            {record.full_name?.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <Text className="block font-bold text-slate-900 leading-tight truncate">
              {record.full_name || 'Unnamed'}
            </Text>
            <Text className="text-xs text-slate-400 font-medium truncate">{record.email}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Current Role',
      key: 'role',
      render: (_, record) => (
        <div className="min-w-0">
          <Text className="block font-semibold text-slate-700 text-sm truncate">
            {record.current_title || '—'}
          </Text>
          <Text className="text-xs text-slate-400 font-medium truncate">{record.current_company}</Text>
        </div>
      ),
    },
    {
      title: 'Skills',
      dataIndex: 'skills',
      key: 'skills',
      render: (skills: string[]) => (
        <div className="flex flex-wrap gap-1.5 max-w-[200px]">
          {skills?.slice(0, 2).map(s => (
            <div key={s} className="bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-md px-1.5 py-0.5 tracking-wider">
              {s}
            </div>
          ))}
          {skills?.length > 2 && (
            <span className="text-[10px] font-bold text-slate-400">+{skills.length - 2}</span>
          )}
        </div>
      ),
    },
    {
      title: 'Location',
      key: 'location',
      width: 160,
      render: (_, record) => (
        <div className="flex items-center gap-1.5 text-slate-500">
          <MapPin className="h-3.5 w-3.5 shrink-0" />
          <span className="text-sm truncate">
            {[record.current_location_city, record.current_location_country].filter(Boolean).join(', ') || '—'}
          </span>
        </div>
      ),
    },
    {
      title: 'Exp.',
      dataIndex: 'experience_years',
      key: 'experience_years',
      width: 80,
      align: 'center',
      render: (y) => <span className="font-bold text-slate-700">{y ? `${parseFloat(y)}y` : '—'}</span>,
    },
    {
      title: 'Added',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 130,
      render: (d) => (
        <div className="flex items-center gap-2 text-slate-500">
          <Clock className="h-3.5 w-3.5" />
          <span className="text-sm">{dayjs(d).format('MMM D, YYYY')}</span>
        </div>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      align: 'right',
      render: () => (
        <Button 
          type="text" 
          icon={<MoreHorizontal className="h-5 w-5 text-slate-400" />} 
          className="hover:bg-slate-100 rounded-lg h-9 w-9 flex items-center justify-center"
        />
      ),
    },
  ]

  const handleRowClick = (record: Candidate) => {
    setSelectedCandidate(record)
    setQuickViewOpen(true)
  }

  const handleCloseAll = () => {
    setQuickViewOpen(false)
    setFullViewOpen(false)
    setSelectedCandidate(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Candidates</h1>
          <p className="text-slate-500 mt-1">Total database of candidates across all sources.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />} onClick={() => refetch()} className="h-10 rounded-xl font-bold">Sync</Button>
          <Button type="primary" icon={<Plus className="h-4 w-4" />} className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md">Add Candidate</Button>
        </div>
      </div>

      {/* Filters */}
      <Card bordered={false} className="shadow-soft-sm">
        <Input
          prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
          placeholder="Search by name, email, skills, or title…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          className="h-10 text-sm max-w-md"
        />
      </Card>

      {/* Table */}
      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[...Array(5)].map((_, i) => <Skeleton key={i} active avatar paragraph={{ rows: 1 }} />)}
          </div>
        ) : (
          <Table<Candidate>
            columns={columns}
            dataSource={candidates}
            rowKey="id"
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              className: "cursor-pointer transition-colors hover:bg-slate-50",
            })}
            pagination={{
              pageSize: 15,
              showSizeChanger: false,
              className: "px-6 py-4 border-t border-slate-100 m-0",
            }}
            className="modern-table"
          />
        )}
      </Card>

      {/* Level 1: Quick View Drawer */}
      <Drawer
        title={<span className="text-base font-bold text-slate-900">{selectedCandidate?.full_name}</span>}
        open={quickViewOpen}
        onClose={handleCloseAll}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnClose
        closeIcon={null}
        push={fullViewOpen ? { minDistance: 520 } : false}
      >
        {selectedCandidate && (
          <>
            <CandidateQuickView 
              candidateId={selectedCandidate.id} 
              onClose={handleCloseAll}
              onOpenFullView={() => setFullViewOpen(true)}
            />

            {/* Level 2: Full View Drawer (Nested) */}
            <Drawer
              title={
                <div className="flex items-center gap-3">
                  <span className="text-base font-bold text-slate-900">{selectedCandidate.full_name}</span>
                  <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase px-2 py-0.5 rounded-md tracking-wider">Full Profile</Tag>
                </div>
              }
              open={fullViewOpen}
              onClose={() => setFullViewOpen(false)}
              width={900}
              styles={{ body: { padding: '40px' } }}
              destroyOnClose
              closeIcon={null}
              extra={
                <Button 
                  type="text" 
                  icon={<ArrowLeft className="h-4 w-4" />} 
                  className="flex items-center gap-2 font-bold text-slate-500 hover:text-blue-600"
                  onClick={() => setFullViewOpen(false)}
                >
                  Back to Quick View
                </Button>
              }
            >
              <CandidateFullView candidateId={selectedCandidate.id} />
            </Drawer>
          </>
        )}
      </Drawer>
    </div>
  )
}
