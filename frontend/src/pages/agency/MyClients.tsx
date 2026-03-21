import {
  Table, Tag, Button, Typography, Card,
} from 'antd'
import {
  SyncOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyRelationship } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const { Title } = Typography

// ─── Main Component ──────────────────────────────────────────────────────────

export default function MyClients() {
  const openQuickView = useDrawerStore(s => s.openQuickView)

  const { data, isLoading, refetch } = useApiQuery(['agency', 'my-clients'], () => agenciesApi.listRelationships())
  const clients = (data as any)?.relationships ?? []

  const columns: ColumnsType<AgencyRelationship> = [
    {
      title: 'Client ID',
      key: 'client',
      render: (_, r) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-50 text-slate-400 flex items-center justify-center shrink-0 font-bold border border-slate-100 text-xs">
            {r.tenant_id.slice(0, 2).toUpperCase()}
          </div>
          <span className="font-bold text-slate-900">{r.tenant_id.slice(0, 8)}</span>
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Title level={3} className="!mb-1">My Clients</Title>
          <p className="text-slate-500 mt-1">Manage enterprise client relationships and contract terms.</p>
        </div>
        <Button icon={<SyncOutlined />} onClick={() => refetch()} className="rounded-xl font-bold">Refresh</Button>
      </div>

      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        <Table<AgencyRelationship>
          columns={columns}
          dataSource={clients}
          rowKey="id"
          loading={isLoading}
          onRow={(r) => ({
            onClick: () => openQuickView('agency_client', r),
            className: "cursor-pointer transition-colors hover:bg-slate-50"
          })}
          className="modern-table"
        />
      </Card>
    </div>
  )
}
