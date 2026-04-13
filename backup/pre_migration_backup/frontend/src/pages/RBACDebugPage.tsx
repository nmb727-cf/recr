import { useMemo, useState } from 'react'
import { Alert, Badge, Card, Collapse, Descriptions, Empty, Spin, Switch, Table, Tag, Typography } from 'antd'
import { CheckCircleOutlined, LockOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import http from '@/utils/http'
import type { ApiResponse } from '@/types'

const { Title, Text } = Typography

interface PermissionItem {
  code: string
  label?: string
  module: string
  module_label?: string
  resource: string
  action: string
  description: string
  is_active?: boolean
}

interface RBACDebugData {
  current_user: {
    email: string
    role: string
    permission_count: number
    permissions: string[]
  }
  roles: Array<{
    name: string
    display_name: string
    description: string
    permission_count: number
    permissions: PermissionItem[]
  }>
  all_permissions: PermissionItem[]
}

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'red',
  tenant_admin: 'volcano',
  hr_manager: 'orange',
  hiring_manager: 'gold',
  recruiter: 'blue',
  interviewer: 'geekblue',
  viewer: 'default',
  agency_owner: 'purple',
  agency_admin: 'magenta',
  agency_recruiter: 'cyan',
  candidate: 'green',
}

const humanLabel = (p: PermissionItem) => p.label || `${p.action.replace(/_/g, ' ')} ${p.resource}`
const humanModule = (p: PermissionItem) => p.module_label || p.module.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

export default function RBACDebugPage() {
  const user = useAuthStore((s) => s.user)
  const [expandedRole, setExpandedRole] = useState<string | null>(null)
  const [showTechnical, setShowTechnical] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['rbac-debug'],
    queryFn: async () => (await http.get<ApiResponse<RBACDebugData>>('/rbac/debug/')).data.data,
  })

  if (isLoading) return <Spin className="block m-auto mt-20" />
  if (error) return <Alert type="error" message="Failed to load RBAC data" description={String(error)} className="m-6" />
  if (!data) return null

  const { current_user, roles, all_permissions } = data

  const grouped = useMemo(() => {
    return all_permissions.reduce<Record<string, PermissionItem[]>>((acc, p) => {
      const key = humanModule(p)
      if (!acc[key]) acc[key] = []
      acc[key].push(p)
      return acc
    }, {})
  }, [all_permissions])

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Title level={3} className="!mb-1">Roles & Permissions</Title>
          <Text type="secondary">Human-friendly permission catalogue with optional technical inspection.</Text>
        </div>
        <div className="flex items-center gap-2">
          <Text type="secondary">Show technical codes</Text>
          <Switch checked={showTechnical} onChange={setShowTechnical} />
        </div>
      </div>

      <Card title="Current User" extra={<Tag color={ROLE_COLORS[current_user.role] ?? 'default'}>{current_user.role}</Tag>}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Email">{current_user.email}</Descriptions.Item>
          <Descriptions.Item label="Role">{current_user.role}</Descriptions.Item>
          <Descriptions.Item label="Permissions from API"><Badge count={current_user.permission_count} color="blue" /></Descriptions.Item>
          <Descriptions.Item label="Permissions in Store"><Badge count={user?.permissions?.length ?? 0} color={(user?.permissions?.length ?? 0) > 0 ? 'green' : 'red'} /></Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={`System Roles (${roles.length})`}>
        <Collapse
          accordion
          activeKey={expandedRole ?? undefined}
          onChange={(k) => {
            if (Array.isArray(k)) {
              setExpandedRole((k[0] as string) || null)
            } else {
              setExpandedRole((k as string) || null)
            }
          }}
          items={roles.map((role) => ({
            key: role.name,
            label: (
              <div className="flex items-center gap-3">
                <Tag color={ROLE_COLORS[role.name] ?? 'default'}>{role.display_name}</Tag>
                <Badge count={role.permission_count} color="blue" />
                <Text type="secondary" className="text-xs">{role.description}</Text>
                {role.name === current_user.role && <Tag color="green">Current</Tag>}
              </div>
            ),
            children: (
              <div className="space-y-3">
                {Object.entries(
                  role.permissions.reduce<Record<string, PermissionItem[]>>((acc, p) => {
                    const key = humanModule(p)
                    if (!acc[key]) acc[key] = []
                    acc[key].push(p)
                    return acc
                  }, {})
                ).map(([moduleName, perms]) => (
                  <div key={moduleName}>
                    <Text strong>{moduleName}</Text>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {perms.map((p) => (
                        <Tag key={p.code} color="blue">
                          {humanLabel(p)}
                          {showTechnical ? ` (${p.code})` : ''}
                        </Tag>
                      ))}
                    </div>
                  </div>
                ))}
                {role.permissions.length === 0 && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No back-office permissions for this role" />}
              </div>
            ),
          }))}
        />
      </Card>

      <Card title={`Permission Catalogue (${all_permissions.length})`}>
        <Collapse
          items={Object.entries(grouped).map(([moduleName, perms]) => ({
            key: moduleName,
            label: (
              <div className="flex items-center gap-3">
                <Text strong>{moduleName}</Text>
                <Badge count={perms.length} color="geekblue" />
              </div>
            ),
            children: (
              <Table
                size="small"
                pagination={false}
                rowKey="code"
                dataSource={perms}
                columns={[
                  { title: 'Permission', dataIndex: 'label', render: (_: string, row: PermissionItem) => <Text strong>{humanLabel(row)}</Text> },
                  { title: 'Description', dataIndex: 'description', render: (value: string) => value || '—' },
                  ...(showTechnical
                    ? [{ title: 'Code', dataIndex: 'code', render: (v: string) => <Text code className="text-xs">{v}</Text> }]
                    : []),
                  {
                    title: 'You Have It',
                    width: 110,
                    render: (_: unknown, row: PermissionItem) => current_user.permissions.includes(row.code)
                      ? <CheckCircleOutlined className="text-green-500" />
                      : <LockOutlined className="text-slate-300" />,
                  },
                ]}
              />
            ),
          }))}
        />
      </Card>
    </div>
  )
}
