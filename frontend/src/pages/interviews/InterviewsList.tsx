import { useState } from 'react'
import {
  Table, Button, Input, Select, Tag, Space,
  Typography, Row, Col, Card, Drawer, Spin, Empty,
} from 'antd'
import {
  Plus, Search, RefreshCw, ArrowLeft, Calendar, User, Briefcase, Clock
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { interviewsApi } from '@/api/interviews'
import type { Interview, InterviewStatus } from '@/types'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<InterviewStatus, string> = {
  scheduled: 'processing',
  confirmed: 'cyan',
  rescheduled: 'warning',
  in_progress: 'green',
  completed: 'success',
  cancelled: 'error',
  no_show: 'default',
  pending_feedback: 'magenta',
}

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'pending_feedback', label: 'Pending Feedback' },
]

// ─── Interview Detail Component ─────────────────────────────────────────────

function InterviewQuickView({ interview, onOpenFullView }: { interview: Interview, onOpenFullView: () => void }) {
  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 shadow-sm border border-purple-100">
          <Calendar className="h-8 w-8" />
        </div>
        <Tag color={STATUS_COLOR[interview.status]} className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {interview.status.replace(/_/g, ' ')}
        </Tag>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{interview.title}</h2>
      </div>

      <div className="space-y-4 bg-slate-50/50 rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Candidate</span>
            <span className="text-sm font-bold text-slate-700">{interview.candidate_name || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Briefcase className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Job Role</span>
            <span className="text-sm font-bold text-slate-700">{interview.job_title || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Clock className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Scheduled At</span>
            <span className="text-sm font-bold text-slate-700">{dayjs(interview.scheduled_at).format('MMM D, YYYY · h:mm A')}</span>
          </div>
        </div>
      </div>

      <Button type="primary" block className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md mt-4" onClick={onOpenFullView}>
        Open Full Details
      </Button>
    </div>
  )
}

// ─── Main InterviewsList ─────────────────────────────────────────────────────

export default function InterviewsList() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null)
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const [fullViewOpen, setFullViewOpen] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['interviews', statusFilter, search],
    () => interviewsApi.list({
      status: statusFilter || undefined,
      search: search || undefined,
    })
  )

  const interviews: Interview[] = (data as { interviews: Interview[] } | undefined)?.interviews ?? []

  const columns: ColumnsType<Interview> = [
    {
      title: 'Candidate',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      render: (name, record) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 font-bold">
            {name?.charAt(0).toUpperCase()}
          </div>
          <div>
            <Text className="block font-bold text-slate-900 leading-tight">{name || 'Unknown'}</Text>
            <Text className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">{record.job_title}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      width: 160,
      render: (type: string) => <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-md px-2 py-0.5 tracking-wider">{type.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Scheduled At',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      width: 180,
      render: (date: string) => (
        <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
          <Clock className="h-3.5 w-3.5" />
          {dayjs(date).format('MMM D, h:mm A')}
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (s: InterviewStatus) => (
        <Tag color={STATUS_COLOR[s] ?? 'default'} className="m-0 border-none uppercase font-bold text-[9px] tracking-widest px-2 py-0.5 rounded-full">
          {s.replace(/_/g, ' ')}
        </Tag>
      ),
    },
    {
      title: 'Round',
      dataIndex: 'interview_round',
      key: 'interview_round',
      width: 80,
      align: 'center',
      render: (r) => <span className="font-bold text-slate-700">R{r}</span>
    },
  ]

  const handleRowClick = (record: Interview) => {
    setSelectedInterview(record)
    setQuickViewOpen(true)
  }

  const handleCloseAll = () => {
    setQuickViewOpen(false)
    setFullViewOpen(false)
    setSelectedInterview(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <Title level={3} className="!mb-1">Interviews</Title>
          <p className="text-slate-500 mt-1">Manage schedules and feedback for all candidate rounds.</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md">
          Schedule Interview
        </Button>
      </div>

      <Card bordered={false} className="shadow-soft-sm">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={10}>
            <Input
              prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
              placeholder="Search by candidate or job…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              allowClear
              className="h-10 text-sm"
            />
          </Col>
          <Col xs={24} md={6}>
            <Select
              className="w-full h-10"
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
              placeholder="Filter by status"
            />
          </Col>
          <Col>
            <Button icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />} onClick={() => refetch()} className="h-10 rounded-xl font-bold border-slate-200">Refresh</Button>
          </Col>
        </Row>
      </Card>

      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        <Table<Interview>
          columns={columns}
          dataSource={interviews}
          rowKey="id"
          loading={isLoading}
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
      </Card>

      <Drawer
        title={<span className="text-base font-bold text-slate-900">{selectedInterview?.title}</span>}
        open={quickViewOpen}
        onClose={handleCloseAll}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnClose
        closeIcon={null}
        push={fullViewOpen ? { minDistance: 520 } : false}
      >
        {selectedInterview && (
          <>
            <InterviewQuickView 
              interview={selectedInterview} 
              onOpenFullView={() => setFullViewOpen(true)}
            />

            <Drawer
              title={
                <div className="flex items-center gap-3">
                  <span className="text-base font-bold text-slate-900">{selectedInterview.title}</span>
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
              <div className="p-12 text-center border-2 border-dashed border-slate-100 rounded-3xl bg-slate-50/50">
                <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">Detail View Under Construction</p>
                <Title level={4} className="mt-4 !mb-0 text-slate-900">Comprehensive Interview Context</Title>
                <p className="text-slate-500 mt-2">Full feedback history and calendar integration coming soon.</p>
              </div>
            </Drawer>
          </>
        )}
      </Drawer>
    </div>
  )
}
