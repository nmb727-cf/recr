import {
  Table, Tag, Button, Typography, Card, Tabs, Space, message, Popconfirm,
} from 'antd'
import {
  SyncOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyRelationship } from '@/types'
import { useState } from 'react'

const { Title } = Typography

// ─── Main Component ──────────────────────────────────────────────────────────

export default function MyClients() {
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null)

  const { data, isLoading, refetch } = useApiQuery(['agency', 'my-clients'], () => agenciesApi.listRelationships())
  const relationships = (data as any)?.relationships ?? []
  const pendingRelationships = (relationships as any[]).filter((r) => (r?.status || '').toLowerCase() === 'pending')
  const activeRelationships = (relationships as any[]).filter((r) => (r?.status || '').toLowerCase() === 'active')

  const getClientLabel = (record: any) => {
    const byName =
      record?.company?.name ||
      record?.company_name ||
      record?.client_name ||
      record?.metadata?.company_name
    if (byName) return String(byName)
    const clientId = record?.company_tenant_id || record?.company_id || record?.tenant_id
    if (clientId) return `Company ${String(clientId).slice(0, 8)}`
    return 'Unknown Company'
  }

  const getClientId = (record: any) => (
    record?.company_tenant_id || record?.company_id || record?.tenant_id || record?.id
  )

  const handleAccept = async (relationshipId: string) => {
    try {
      setActionLoadingId(relationshipId)
      await agenciesApi.accept(relationshipId)
      message.success('Client relationship accepted')
      refetch()
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to accept relationship')
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleReject = async (relationshipId: string) => {
    try {
      setActionLoadingId(relationshipId)
      await agenciesApi.deleteRelationship(relationshipId)
      message.success('Pending relationship rejected')
      refetch()
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to reject relationship')
    } finally {
      setActionLoadingId(null)
    }
  }

  const sharedColumns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Client',
      key: 'client',
      render: (_, r) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-50 text-slate-400 flex items-center justify-center shrink-0 font-bold border border-slate-100 text-xs">
            {String(getClientLabel(r)).slice(0, 2).toUpperCase()}
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-slate-900">{getClientLabel(r)}</span>
            <span className="text-[11px] text-slate-400">{String(getClientId(r)).slice(0, 8)}</span>
          </div>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s) => (
        <Tag color={s === 'active' ? 'green' : 'orange'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{s}</Tag>
      )
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      render: (t) => <Tag color="blue" className="m-0 border-none font-bold text-[10px] uppercase rounded-md px-2 py-0.5">{t}</Tag>
    },
    {
      title: 'Commission %',
      dataIndex: 'commission_percentage',
      key: 'comm',
      render: (c) => <span className="font-bold text-slate-700">{c}%</span>
    },
    {
      title: 'SLA hours',
      dataIndex: 'sla_hours',
      key: 'sla',
      render: (h) => <span className="text-sm font-medium text-slate-500">{h}h</span>
    },
    {
      title: 'Partner Since',
      dataIndex: 'created_at',
      key: 'since',
      render: (d) => <span className="text-sm text-slate-500">{dayjs(d).format('MMM D, YYYY')}</span>
    },
  ]

  const pendingColumns: ColumnsType<AgencyRelationship> = [
    ...sharedColumns,
    {
      title: 'Actions',
      key: 'actions',
      width: 190,
      render: (_, r: any) => (
        <Space>
          <Button
            type="primary"
            size="small"
            className="bg-blue-600 border-none"
            loading={actionLoadingId === r.id}
            onClick={() => handleAccept(r.id)}
          >
            Accept
          </Button>
          <Popconfirm
            title="Reject this client relationship?"
            okText="Reject"
            okButtonProps={{ danger: true }}
            onConfirm={() => handleReject(r.id)}
          >
            <Button
              danger
              size="small"
              loading={actionLoadingId === r.id}
            >
              Reject
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Title level={3} className="!mb-1">Clients</Title>
          <p className="text-slate-500 mt-1">Manage pending client relationships and active client accounts.</p>
        </div>
        <Button icon={<SyncOutlined />} onClick={() => refetch()} className="rounded-xl font-bold">Refresh</Button>
      </div>

      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        <Tabs
          defaultActiveKey="pending"
          className="px-4 pt-2"
          items={[
            {
              key: 'pending',
              label: `Pending Invites (${pendingRelationships.length})`,
              children: (
                <Table<AgencyRelationship>
                  columns={pendingColumns}
                  dataSource={pendingRelationships}
                  rowKey="id"
                  loading={isLoading}
                  className="modern-table"
                  locale={{ emptyText: 'No pending client invites' }}
                />
              )
            },
            {
              key: 'active',
              label: `Active Clients (${activeRelationships.length})`,
              children: (
                <Table<AgencyRelationship>
                  columns={sharedColumns}
                  dataSource={activeRelationships}
                  rowKey="id"
                  loading={isLoading}
                  className="modern-table"
                  locale={{ emptyText: 'No active clients yet' }}
                />
              )
            }
          ]}
        />
      </Card>
    </div>
  )
}
