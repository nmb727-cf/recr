import { useMemo, useState } from 'react'
import { Button, Card, Input, Select, Space, Table, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

import { useApiQuery } from '@/hooks/useApiQuery'
import { masterAdminApi } from '@/api/masterAdmin'

const { Title } = Typography

export default function MasterAdminTenants() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [tenantType, setTenantType] = useState<string | undefined>()
  const [status, setStatus] = useState<string | undefined>()

  const params = useMemo(() => ({
    search: search || undefined,
    tenant_type: tenantType,
    status,
  }), [search, tenantType, status])

  const { data, refetch, isLoading } = useApiQuery(
    ['master-admin', 'tenants', params],
    () => masterAdminApi.listTenants(params)
  )
  const tenants = (data as any)?.data?.data?.tenants || []

  return (
    <div className="space-y-4">
      <Title level={3} style={{ marginBottom: 0 }}>Tenants</Title>
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="Search tenant"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onSearch={() => refetch()}
            style={{ width: 260 }}
          />
          <Select
            allowClear
            placeholder="Tenant type"
            style={{ width: 180 }}
            value={tenantType}
            onChange={setTenantType}
            options={[
              { value: 'company', label: 'Company' },
              { value: 'agency', label: 'Agency' },
              { value: 'candidate_pool', label: 'Candidate Pool' },
            ]}
          />
          <Select
            allowClear
            placeholder="Status"
            style={{ width: 180 }}
            value={status}
            onChange={setStatus}
            options={[
              { value: 'active', label: 'Active' },
              { value: 'pending', label: 'Pending' },
              { value: 'suspended', label: 'Suspended' },
              { value: 'terminated', label: 'Terminated' },
            ]}
          />
          <Button onClick={() => refetch()}>Apply</Button>
        </Space>

        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={tenants}
          columns={[
            { title: 'Name', dataIndex: 'name' },
            { title: 'Type', dataIndex: 'tenant_type', render: (v: string) => <Tag>{v}</Tag> },
            {
              title: 'Status',
              dataIndex: 'status',
              render: (v: string) => <Tag color={v === 'active' ? 'green' : v === 'suspended' ? 'orange' : v === 'terminated' ? 'red' : 'blue'}>{v}</Tag>,
            },
            {
              title: 'Verification',
              dataIndex: 'verification_state',
              render: (v: string) => <Tag color={v === 'verified' ? 'green' : 'default'}>{v}</Tag>,
            },
            { title: 'Users', dataIndex: ['usage', 'users_total'] },
            { title: 'Jobs', dataIndex: ['usage', 'jobs_total'] },
            { title: 'Candidates', dataIndex: ['usage', 'candidates_total'] },
            { title: 'Created', dataIndex: 'created_at', render: (v: string) => (v ? new Date(v).toLocaleDateString() : '-') },
            {
              title: 'Actions',
              render: (_: any, row: any) => (
                <Button type="link" onClick={() => navigate(`/admin/tenants/${row.id}`)}>
                  Open
                </Button>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
