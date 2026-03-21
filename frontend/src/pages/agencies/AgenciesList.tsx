import { useState } from 'react'
import {
  Table, Tag, Button, Space, Typography, Row, Col, Card, Drawer, 
  Spin, Empty, Tabs,
} from 'antd'
import {
  Plus, ReloadOutlined, Building2, Globe, Mail, Phone, ArrowLeft
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyRelationship, AgencyAssignment, AgencyStatus, AgencyTier } from '@/types'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<AgencyStatus, string> = {
  pending: 'orange',
  active: 'green',
  suspended: 'red',
  terminated: 'default',
}

const TIER_COLOR: Record<AgencyTier, string> = {
  bronze: 'orange',
  silver: 'blue',
  gold: 'gold',
  platinum: 'purple',
}

// ─── Agency Quick View Component ───────────────────────────────────────────

function AgencyQuickView({ relationship, onOpenFullView }: { relationship: AgencyRelationship, onOpenFullView: () => void }) {
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

      <Button type="primary" block className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md mt-4" onClick={onOpenFullView}>
        Open Relationship Details
      </Button>
    </div>
  )
}

// ─── Assignments Table ────────────────────────────────────────────────────────

function AssignmentsList() {
  const { data, isLoading } = useApiQuery(['agency_assignments'], () => agenciesApi.listAssignments())
  const assignments = (data as { assignments: AgencyAssignment[] } | undefined)?.assignments ?? []

  const columns: ColumnsType<AgencyAssignment> = [
    {
      title: 'Job Title',
      dataIndex: 'job_title',
      key: 'job_title',
      render: (t) => <Text className="font-bold text-slate-900">{t}</Text>,
    },
    {
      title: 'Agency',
      dataIndex: 'agency_name',
      key: 'agency_name',
    },
    {
      title: 'Submissions',
      key: 'submissions',
      render: (_, r) => <Space className="font-bold">{r.submissions_count} / {r.max_submissions}</Space>,
    },
    {
      title: 'Deadline',
      dataIndex: 'deadline',
      key: 'deadline',
      render: (d) => <span className="text-slate-500 font-medium">{dayjs(d).format('MMM D, YYYY')}</span>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s) => (
        <Tag color={s === 'active' ? 'green' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{s}</Tag>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={assignments}
      rowKey="id"
      loading={isLoading}
      size="middle"
      pagination={{ pageSize: 10 }}
      className="modern-table"
    />
  )
}

// ─── Main Agencies Page ───────────────────────────────────────────────────────

export default function AgenciesList() {
  const [selectedRel, setSelectedRel] = useState<AgencyRelationship | null>(null)
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const [fullViewOpen, setFullViewOpen] = useState(false)
  const [inviteOpen, setInviteOpen] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(['agencies'], () => agenciesApi.listRelationships())
  const relationships = (data as { relationships: AgencyRelationship[] } | undefined)?.relationships ?? []

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Agency Name',
      key: 'name',
      render: (_, r) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-50 text-slate-400 flex items-center justify-center shrink-0 font-bold border border-slate-100">
            {r.agency?.name?.charAt(0).toUpperCase()}
          </div>
          <Text className="font-bold text-slate-900">{r.agency?.name || 'N/A'}</Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: AgencyStatus) => (
        <Tag color={STATUS_COLOR[s]} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{s}</Tag>
      ),
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      render: (t: AgencyTier) => (
        <Tag color={TIER_COLOR[t] ?? 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{t}</Tag>
      ),
    },
    {
      title: 'Comm %',
      dataIndex: 'commission_percentage',
      key: 'commission',
      render: (c) => <span className="font-bold text-slate-700">{c}%</span>,
    },
    {
      title: 'SLA (hrs)',
      dataIndex: 'sla_submission_hours',
      key: 'sla',
      render: (h) => <span className="text-slate-500 font-medium">{h ? `${h}h` : 'N/A'}</span>,
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created',
      render: (d) => <span className="text-slate-500 font-medium">{d ? dayjs(d).format('MMM D, YYYY') : 'N/A'}</span>,
    },
  ]

  const handleRowClick = (record: AgencyRelationship) => {
    setSelectedRel(record)
    setQuickViewOpen(true)
  }

  const handleCloseAll = () => {
    setQuickViewOpen(false)
    setFullViewOpen(false)
    setSelectedRel(null)
  }

  return (
    <div className="space-y-6">
      <Row align="middle" justify="space-between">
        <Col>
          <Title level={3} className="!mb-1">Agency Management</Title>
          <p className="text-slate-500 mt-1">Configure external recruiting partnerships and job assignments.</p>
        </Col>
        <Col>
          <Space>
            <Button icon={<Plus className="h-4 w-4" />} type="primary" className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md" onClick={() => setInviteOpen(true)}>
              Invite Agency
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs
        defaultActiveKey="agencies"
        className="modern-tabs"
        items={[
          {
            key: 'agencies',
            label: 'Agency Partners',
            children: (
              <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
                <Table
                  columns={columns}
                  dataSource={relationships}
                  rowKey="id"
                  loading={isLoading}
                  onRow={(record) => ({
                    onClick: () => handleRowClick(record),
                    className: "cursor-pointer transition-colors hover:bg-slate-50",
                  })}
                  pagination={{ pageSize: 15, className: "px-6 py-4" }}
                  className="modern-table"
                />
              </Card>
            ),
          },
          {
            key: 'assignments',
            label: 'Job Assignments',
            children: (
              <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
                <AssignmentsList />
              </Card>
            ),
          },
        ]}
      />

      <Drawer
        title={<span className="text-base font-bold text-slate-900">{selectedRel?.agency?.name}</span>}
        open={quickViewOpen}
        onClose={handleCloseAll}
        width={480}
        styles={{ body: { padding: '32px 24px' } }}
        destroyOnClose
        closeIcon={null}
        push={fullViewOpen ? { minDistance: 520 } : false}
      >
        {selectedRel && (
          <>
            <AgencyQuickView 
              relationship={selectedRel} 
              onOpenFullView={() => setFullViewOpen(true)}
            />

            <Drawer
              title={
                <div className="flex items-center gap-3">
                  <span className="text-base font-bold text-slate-900">{selectedRel.agency?.name}</span>
                  <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase px-2 py-0.5 rounded-md tracking-wider">Relationship Details</Tag>
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
                <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">Relationship Deep Dive</p>
                <Title level={4} className="mt-4 !mb-0 text-slate-900">Contract & Performance Analytics</Title>
                <p className="text-slate-500 mt-2">Historical data, active pipelines, and financial terms coming soon.</p>
              </div>
            </Drawer>
          </>
        )}
      </Drawer>
    </div>
  )
}
