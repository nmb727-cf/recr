import { useMemo } from 'react'
import { Card, Col, Row, Statistic, Table, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

import { useApiQuery } from '@/hooks/useApiQuery'
import { masterAdminApi } from '@/api/masterAdmin'

const { Title, Text } = Typography

export default function MasterAdminDashboard() {
  const navigate = useNavigate()
  const { data: tenantsRes } = useApiQuery(['master-admin', 'tenants'], () => masterAdminApi.listTenants())
  const { data: auditRes } = useApiQuery(['master-admin', 'audit'], () => masterAdminApi.listAudit({ limit: 20 }))

  const tenants = (tenantsRes as any)?.data?.data?.tenants || []
  const auditEntries = (auditRes as any)?.data?.data?.audit_entries || []

  const stats = useMemo(() => {
    const total = tenants.length
    const active = tenants.filter((t: any) => t.status === 'active').length
    const suspended = tenants.filter((t: any) => t.status === 'suspended').length
    const unverified = tenants.filter((t: any) => t.verification_state !== 'verified').length
    return { total, active, suspended, unverified }
  }, [tenants])

  return (
    <div className="space-y-4">
      <div>
        <Title level={3} style={{ marginBottom: 0 }}>Master Admin Control Plane</Title>
        <Text type="secondary">Platform operations, tenant governance, and audit visibility.</Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}><Card><Statistic title="Total Tenants" value={stats.total} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title="Active Tenants" value={stats.active} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title="Suspended Tenants" value={stats.suspended} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title="Unverified Tenants" value={stats.unverified} /></Card></Col>
      </Row>

      <Card title="Recent Admin Audit">
        <Table
          size="small"
          rowKey="id"
          pagination={false}
          dataSource={auditEntries.slice(0, 10)}
          columns={[
            { title: 'Action', dataIndex: 'action_type' },
            { title: 'Target', dataIndex: 'target_type' },
            { title: 'Target ID', dataIndex: 'target_id', render: (v: string) => v || '-' },
            { title: 'When', dataIndex: 'created_at', render: (v: string) => (v ? new Date(v).toLocaleString() : '-') },
          ]}
          onRow={(record: any) => ({
            onClick: () => {
              if (record.target_type === 'tenant' && record.target_id) navigate(`/admin/tenants/${record.target_id}`)
            },
          })}
        />
      </Card>
    </div>
  )
}
