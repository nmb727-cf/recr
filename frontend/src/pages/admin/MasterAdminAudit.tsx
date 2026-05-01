import { useState } from 'react'
import { Button, Card, Input, Select, Space, Table, Tag, Typography } from 'antd'

import { useApiQuery } from '@/hooks/useApiQuery'
import { masterAdminApi } from '@/api/masterAdmin'

const { Title } = Typography

export default function MasterAdminAudit() {
  const [actionType, setActionType] = useState<string | undefined>()
  const [targetType, setTargetType] = useState<string | undefined>()
  const [tenantId, setTenantId] = useState('')

  const { data, refetch, isLoading } = useApiQuery(
    ['master-admin', 'audit', actionType, targetType, tenantId],
    () => masterAdminApi.listAudit({
      action_type: actionType,
      target_type: targetType,
      tenant_id: tenantId || undefined,
      limit: 200,
    })
  )

  const rows = (data as any)?.data?.data?.audit_entries || []

  return (
    <div className="space-y-4">
      <Title level={3} style={{ marginBottom: 0 }}>Admin Audit</Title>
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            allowClear
            placeholder="Action type"
            style={{ width: 260 }}
            value={actionType}
            onChange={setActionType}
            options={[
              { value: 'master_admin.tenant_verified', label: 'Tenant Verified' },
              { value: 'master_admin.tenant_suspended', label: 'Tenant Suspended' },
              { value: 'master_admin.tenant_reactivated', label: 'Tenant Reactivated' },
              { value: 'master_admin.tenant_deactivated', label: 'Tenant Deactivated' },
              { value: 'master_admin.tenant_feature_flags_updated', label: 'Feature Flags Updated' },
              { value: 'master_admin.tenant_limits_updated', label: 'Limits Updated' },
              { value: 'master_admin.platform_setting_updated', label: 'Platform Setting Updated' },
            ]}
          />
          <Select
            allowClear
            placeholder="Target type"
            style={{ width: 180 }}
            value={targetType}
            onChange={setTargetType}
            options={[
              { value: 'tenant', label: 'Tenant' },
              { value: 'platform_setting', label: 'Platform Setting' },
            ]}
          />
          <Input
            placeholder="Tenant ID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            style={{ width: 320 }}
          />
          <Button onClick={() => refetch()}>Apply</Button>
        </Space>

        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={rows}
          columns={[
            { title: 'Action', dataIndex: 'action_type', render: (v: string) => <Tag>{v}</Tag> },
            { title: 'Actor', dataIndex: 'actor_id', render: (v: string) => v || '-' },
            { title: 'Target', dataIndex: 'target_type' },
            { title: 'Target ID', dataIndex: 'target_id', render: (v: string) => v || '-' },
            { title: 'When', dataIndex: 'created_at', render: (v: string) => (v ? new Date(v).toLocaleString() : '-') },
          ]}
        />
      </Card>
    </div>
  )
}
