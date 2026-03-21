import { useState } from 'react'
import {
  Table, Button, Input, Select, Typography, Row, Col, Card, Drawer,
  Skeleton, Tag,
} from 'antd'
import {
  Plus,
  Search,
  MoreHorizontal,
  Briefcase,
  MapPin,
  Clock,
  Download,
  LayoutGrid,
  List as ListIcon,
  RefreshCw,
  ArrowLeft
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import type { JobRequisition, RequisitionStatus } from '@/types'
import { cn } from '@/utils/cn'
import JobQuickView from './JobQuickView'
import JobFullView from './JobFullView'

const { Title, Text } = Typography

// ─── Status Config ──────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<RequisitionStatus, { label: string, color: string, dot: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
  pending_approval: { label: 'Pending', color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  approved: { label: 'Approved', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-400' },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  closed: { label: 'Closed', color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300' },
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobsList() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table')
  
  const [selectedJob, setSelectedJob] = useState<JobRequisition | null>(null)
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const [fullViewOpen, setFullViewOpen] = useState(false)
  const [initialTab, setInitialTab] = useState('overview')

  const { data, isLoading, refetch } = useApiQuery(
    ['jobs', statusFilter, search],
    () => requisitionsApi.list({
      status: statusFilter || undefined,
      search: search || undefined,
    })
  )

  const requisitions = (data as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []

  const columns: ColumnsType<JobRequisition> = [
    {
      title: 'Job Role',
      dataIndex: 'title',
      key: 'title',
      render: (title, record) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <Briefcase className="h-5 w-5" />
          </div>
          <div>
            <Text className="block font-bold text-slate-900 leading-tight">{title}</Text>
            <div className="flex items-center gap-2 mt-1">
              <span className="flex items-center gap-1 text-[11px] text-slate-400 font-medium uppercase tracking-wider">
                <MapPin className="h-3 w-3" /> {record.location_id || 'Remote'}
              </span>
              <span className="h-1 w-1 rounded-full bg-slate-200" />
              <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
                {record.job_type.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: RequisitionStatus) => {
        const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft
        return (
          <div className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold", config.color)}>
            <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
            {config.label}
          </div>
        )
      },
    },
    {
      title: 'Headcount',
      dataIndex: 'headcount',
      key: 'headcount',
      width: 120,
      align: 'center',
      render: (count) => (
        <div className="flex flex-col items-center">
          <Text className="font-bold text-slate-900">{count}</Text>
          <Text className="text-[10px] text-slate-400 font-bold uppercase">Positions</Text>
        </div>
      ),
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => (
        <div className="flex items-center gap-2 text-slate-500">
          <Clock className="h-3.5 w-3.5" />
          <span className="text-sm">{dayjs(date).format('MMM D, YYYY')}</span>
        </div>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 80,
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

  const handleRowClick = (record: JobRequisition) => {
    setSelectedJob(record)
    setQuickViewOpen(true)
  }

  const handleOpenFullView = (tab = 'overview') => {
    setInitialTab(tab)
    setFullViewOpen(true)
  }

  const handleCloseAll = () => {
    setQuickViewOpen(false)
    setFullViewOpen(false)
    setSelectedJob(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Job Requisitions</h1>
          <p className="text-slate-500 mt-1">Manage and track all open roles across your organization.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button icon={<Download className="h-4 w-4" />} className="flex items-center gap-2 font-bold h-10 rounded-xl">Export</Button>
          <Button type="primary" icon={<Plus className="h-4 w-4" />} className="flex items-center gap-2 font-bold h-10 rounded-xl bg-blue-600 border-none shadow-soft-md">Create Job</Button>
        </div>
      </div>

      {/* Filters Card */}
      <Card bordered={false} className="shadow-soft-sm">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={10}>
            <Input
              prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
              placeholder="Search by role, location, or department..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 text-sm"
              allowClear
            />
          </Col>
          <Col xs={12} md={6}>
            <Select
              className="w-full h-10"
              placeholder="Filter by Status"
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
              options={[
                { value: 'active', label: 'Active Roles' },
                { value: 'pending_approval', label: 'Pending Approval' },
                { value: 'draft', label: 'Drafts' },
                { value: 'closed', label: 'Closed' },
              ]}
            />
          </Col>
          <Col xs={12} md={8}>
            <div className="flex items-center justify-end gap-2">
              <div className="bg-slate-100 p-1 rounded-lg flex">
                <Button 
                  type={viewMode === 'table' ? 'primary' : 'text'} 
                  size="small" 
                  icon={<ListIcon className="h-4 w-4" />} 
                  onClick={() => setViewMode('table')}
                  className={cn("h-8 w-8 p-0 border-none", viewMode === 'table' ? "bg-white text-blue-600 shadow-sm" : "text-slate-500")}
                />
                <Button 
                  type={viewMode === 'grid' ? 'primary' : 'text'} 
                  size="small" 
                  icon={<LayoutGrid className="h-4 w-4" />} 
                  onClick={() => setViewMode('grid')}
                  className={cn("h-8 w-8 p-0 border-none", viewMode === 'grid' ? "bg-white text-blue-600 shadow-sm" : "text-slate-500")}
                />
              </div>
              <Button 
                icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />} 
                onClick={() => refetch()}
                className="h-10 w-10 p-0 flex items-center justify-center rounded-xl border-slate-200"
              />
            </div>
          </Col>
        </Row>
      </Card>

      {/* Table Content */}
      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} active avatar paragraph={{ rows: 1 }} />
            ))}
          </div>
        ) : requisitions.length > 0 ? (
          <Table<JobRequisition>
            columns={columns}
            dataSource={requisitions}
            rowKey="id"
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              className: "cursor-pointer transition-colors hover:bg-slate-50",
            })}
            pagination={{
              pageSize: 10,
              showSizeChanger: false,
              className: "px-6 py-4 border-t border-slate-100 m-0",
            }}
            className="modern-table"
          />
        ) : (
          <div className="py-20 flex flex-col items-center justify-center text-center">
            <div className="h-20 w-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
              <Briefcase className="h-10 w-10 text-slate-200" />
            </div>
            <Title level={4} className="text-slate-900 mb-1">No requisitions found</Title>
            <p className="text-slate-500 max-w-xs mx-auto mb-6">We couldn't find any job requisitions matching your current filters.</p>
            <Button type="primary" onClick={() => { setSearch(''); setStatusFilter(''); }}>Clear all filters</Button>
          </div>
        )}
      </Card>

      {/* Level 1: Quick View Drawer */}
      <Drawer
        title={<span className="text-base font-bold text-slate-900">{selectedJob?.title}</span>}
        open={quickViewOpen}
        onClose={handleCloseAll}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnClose
        closeIcon={null}
        push={fullViewOpen ? { minDistance: 520 } : false}
      >
        {selectedJob && (
          <>
            <JobQuickView 
              jobId={selectedJob.id} 
              onClose={handleCloseAll}
              onOpenFullView={handleOpenFullView}
              onRefresh={refetch}
            />

            {/* Level 2: Full View Drawer (Nested) */}
            <Drawer
              title={
                <div className="flex items-center gap-3">
                  <span className="text-base font-bold text-slate-900">{selectedJob.title}</span>
                  <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase px-2 py-0.5 rounded-md tracking-wider">Full View</Tag>
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
              <JobFullView jobId={selectedJob.id} onRefresh={refetch} initialTab={initialTab} />
            </Drawer>
          </>
        )}
      </Drawer>
    </div>
  )
}
