import { useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import {
  AuditOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LockOutlined,
  PlusOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  TableOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import {
  automationPermissionsApi,
  type AuditDecision,
  type AuditLog,
  type PermissionPolicy,
  type PolicyWritePayload,
  type RestrictedAction,
  type RoleMatrix,
  type Severity,
} from '@/api/automationPermissions'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// ─── Helpers ──────────────────────────────────────────────────────────────────

function severityColor(s: Severity): string {
  return { low: 'green', medium: 'orange', high: 'volcano', critical: 'red' }[s] ?? 'default'
}

function decisionBadge(d: AuditDecision) {
  if (d === 'allowed')           return <Tag icon={<CheckCircleOutlined />} color="success">Allowed</Tag>
  if (d === 'approval_required') return <Tag icon={<ClockCircleOutlined />} color="warning">Needs Approval</Tag>
  return                                <Tag icon={<CloseCircleOutlined />} color="error">Denied</Tag>
}

function permissionTag(level: string) {
  if (level === 'allow')            return <Tag color="success">Allow</Tag>
  if (level === 'require_approval') return <Tag color="warning">Approval</Tag>
  return                                   <Tag color="error">Deny</Tag>
}

// ─── Resource / action choices for policy builder ─────────────────────────────

const RESOURCES = [
  'workflow', 'workflow_template', 'workflow_execution',
  'workflow_governance', 'workflow_analytics', 'automation_center',
]
const ACTIONS = [
  'view', 'create', 'edit', 'delete', 'activate', 'pause', 'archive',
  'duplicate', 'import_template', 'emergency_stop', 'rollback',
  'approve', 'dry_run', 'view_logs', 'view_analytics',
]
const ROLES = [
  'tenant_admin', 'hr_manager', 'recruiter',
  'hiring_manager', 'interviewer', 'viewer',
]

// ─── Tab: Policy List ─────────────────────────────────────────────────────────

function PolicyList() {
  const qc = useQueryClient()
  const [builderOpen, setBuilderOpen]     = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<PermissionPolicy | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-permission-policies'],
    queryFn: async () => {
      const res = await automationPermissionsApi.listPolicies()
      return (res.data as any)?.data?.policies as PermissionPolicy[]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => automationPermissionsApi.deletePolicy(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflow-permission-policies'] }),
  })

  const columns = [
    { title: 'Policy Name', dataIndex: 'name', key: 'name', render: (v: string) => <Text strong>{v}</Text> },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) => v ? <Badge status="success" text="Active" /> : <Badge status="default" text="Inactive" />,
    },
    {
      title: 'Rules',
      key: 'rules',
      render: (_: unknown, row: PermissionPolicy) => <Tag>{row.rules?.length ?? 0} rules</Tag>,
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, row: PermissionPolicy) => (
        <Space>
          <Button
            size="small"
            icon={<SettingOutlined />}
            onClick={() => { setEditingPolicy(row); setBuilderOpen(true) }}
          >
            Edit
          </Button>
          <Button
            size="small"
            danger
            onClick={() => Modal.confirm({
              title: 'Delete this policy?',
              onOk: () => deleteMutation.mutate(row.id),
            })}
          >
            Delete
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>Permission Policies</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { setEditingPolicy(null); setBuilderOpen(true) }}
        >
          New Policy
        </Button>
      </div>
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
        size="middle"
      />
      <PolicyBuilder
        open={builderOpen}
        policy={editingPolicy}
        onClose={() => { setBuilderOpen(false); setEditingPolicy(null) }}
      />
    </>
  )
}

// ─── Tab: Policy Builder Drawer ───────────────────────────────────────────────

function PolicyBuilder({
  open,
  policy,
  onClose,
}: {
  open: boolean
  policy: PermissionPolicy | null
  onClose: () => void
}) {
  const qc   = useQueryClient()
  const [form] = Form.useForm()
  const isEdit = !!policy

  const saveMutation = useMutation({
    mutationFn: (payload: PolicyWritePayload) =>
      isEdit
        ? automationPermissionsApi.updatePolicy(policy!.id, payload)
        : automationPermissionsApi.createPolicy(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow-permission-policies'] })
      onClose()
      form.resetFields()
    },
  })

  function handleSave() {
    form.validateFields().then((values) => {
      saveMutation.mutate(values)
    })
  }

  return (
    <Drawer
      title={isEdit ? `Edit Policy: ${policy!.name}` : 'New Permission Policy'}
      open={open}
      onClose={onClose}
      width={640}
      extra={
        <Button type="primary" onClick={handleSave} loading={saveMutation.isPending}>
          Save Policy
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={policy ?? { is_active: true, rules: [] }}
      >
        <Form.Item name="name" label="Policy Name" rules={[{ required: true }]}>
          <Input placeholder="e.g. Enterprise Standard Policy" />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <TextArea rows={2} placeholder="Describe this policy's scope..." />
        </Form.Item>
        <Form.Item name="is_active" label="Active" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Title level={5}>Permission Rules</Title>
        <Form.List name="rules">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name }) => (
                <Card
                  key={key}
                  size="small"
                  style={{ marginBottom: 12 }}
                  extra={<Button size="small" danger onClick={() => remove(name)}>Remove</Button>}
                >
                  <Row gutter={12}>
                    <Col span={12}>
                      <Form.Item name={[name, 'role_code']} label="Role" rules={[{ required: true }]}>
                        <Select placeholder="Select role">
                          {ROLES.map(r => <Option key={r} value={r}>{r}</Option>)}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name={[name, 'module_scope']} label="Module Scope">
                        <Input placeholder="e.g. candidates" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name={[name, 'resource_type']} label="Resource" rules={[{ required: true }]}>
                        <Select placeholder="Select resource">
                          {RESOURCES.map(r => <Option key={r} value={r}>{r}</Option>)}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name={[name, 'action_type']} label="Action" rules={[{ required: true }]}>
                        <Select placeholder="Select action">
                          {ACTIONS.map(a => <Option key={a} value={a}>{a}</Option>)}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={24}>
                      <Form.Item name={[name, 'permission_level']} label="Permission Level" rules={[{ required: true }]}>
                        <Select>
                          <Option value="allow"><Tag color="success">Allow</Tag></Option>
                          <Option value="deny"><Tag color="error">Deny</Tag></Option>
                          <Option value="require_approval"><Tag color="warning">Require Approval</Tag></Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                </Card>
              ))}
              <Button
                type="dashed"
                block
                icon={<PlusOutlined />}
                onClick={() => add({ conditions: {}, permission_level: 'deny' })}
              >
                Add Rule
              </Button>
            </>
          )}
        </Form.List>
      </Form>
    </Drawer>
  )
}

// ─── Tab: Restricted Actions ──────────────────────────────────────────────────

function RestrictedActions() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-restricted-actions'],
    queryFn: async () => {
      const res = await automationPermissionsApi.listRestrictedActions()
      return (res.data as any)?.data?.restricted_actions as RestrictedAction[]
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<RestrictedAction> }) =>
      automationPermissionsApi.updateRestrictedAction(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflow-restricted-actions'] }),
  })

  const columns = [
    {
      title: 'Action Key',
      dataIndex: 'action_key',
      key: 'action_key',
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (v: Severity) => <Tag color={severityColor(v)}>{v.toUpperCase()}</Tag>,
    },
    {
      title: 'Approval Required',
      dataIndex: 'requires_approval',
      key: 'requires_approval',
      render: (v: boolean, row: RestrictedAction) => (
        <Switch
          checked={v}
          onChange={(checked) => updateMutation.mutate({ id: row.id, payload: { requires_approval: checked } })}
          size="small"
        />
      ),
    },
    {
      title: 'Admin Only',
      dataIndex: 'requires_admin',
      key: 'requires_admin',
      render: (v: boolean, row: RestrictedAction) => (
        <Switch
          checked={v}
          onChange={(checked) => updateMutation.mutate({ id: row.id, payload: { requires_admin: checked } })}
          size="small"
        />
      ),
    },
  ]

  return (
    <>
      <Alert
        type="warning"
        icon={<WarningOutlined />}
        showIcon
        message="These actions require elevated permissions. Changes take effect immediately."
        style={{ marginBottom: 16 }}
      />
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </>
  )
}

// ─── Tab: Audit Logs ──────────────────────────────────────────────────────────

function AuditLogs() {
  const [filters, setFilters] = useState<{ decision?: AuditDecision }>({})

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['workflow-access-audit', filters],
    queryFn: async () => {
      const res = await automationPermissionsApi.getAuditLogs({ ...filters, limit: 100 })
      return (res.data as any)?.data?.audit_logs as AuditLog[]
    },
  })

  const columns = [
    {
      title: 'User',
      dataIndex: 'user_id',
      key: 'user_id',
      render: (v: string) => <Text copyable={{ text: v }}>{v.slice(0, 8)}…</Text>,
    },
    {
      title: 'Workflow',
      dataIndex: 'workflow_id',
      key: 'workflow_id',
      render: (v: string | null) => v ? <Text copyable={{ text: v }}>{v.slice(0, 8)}…</Text> : '—',
    },
    {
      title: 'Action',
      dataIndex: 'action_attempted',
      key: 'action_attempted',
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Decision',
      dataIndex: 'decision',
      key: 'decision',
      render: (v: AuditDecision) => decisionBadge(v),
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
      sorter: true,
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <Select
          allowClear
          placeholder="Filter by decision"
          style={{ width: 200 }}
          onChange={(v) => setFilters(f => ({ ...f, decision: v }))}
        >
          <Option value="allowed">Allowed</Option>
          <Option value="denied">Denied</Option>
          <Option value="approval_required">Needs Approval</Option>
        </Select>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
      </div>
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        size="small"
      />
    </>
  )
}

// ─── Tab: Role Matrix ─────────────────────────────────────────────────────────

function RoleMatrixView() {
  const { data, isLoading } = useQuery({
    queryKey: ['workflow-permission-matrix'],
    queryFn: async () => {
      const res = await automationPermissionsApi.getRoleMatrix()
      return (res.data as any)?.data?.matrix as RoleMatrix
    },
  })

  if (isLoading) return <Card loading />
  if (!data) return null

  const roles = Object.keys(data)
  // Collect all unique permission keys
  const allKeys = Array.from(new Set(roles.flatMap(r => Object.keys(data[r]))))

  // Build table columns: first col = resource.action, then one per role
  const columns = [
    {
      title: 'Resource · Action',
      dataIndex: 'key',
      key: 'key',
      fixed: 'left' as const,
      width: 260,
      render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text>,
    },
    ...roles.map(role => ({
      title: <Text style={{ fontSize: 12 }}>{role}</Text>,
      dataIndex: role,
      key: role,
      width: 130,
      render: (v: string) => permissionTag(v),
    })),
  ]

  const tableData = allKeys.map(key => ({
    key,
    ...Object.fromEntries(roles.map(r => [r, data[r][key] ?? 'deny'])),
  }))

  return (
    <Table
      dataSource={tableData}
      columns={columns}
      rowKey="key"
      scroll={{ x: 'max-content' }}
      pagination={{ pageSize: 30 }}
      size="small"
      bordered
    />
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = [
  { key: 'policies',          label: 'Policies',           icon: <SafetyCertificateOutlined /> },
  { key: 'restricted',        label: 'Restricted Actions', icon: <LockOutlined /> },
  { key: 'audit',             label: 'Access Audit',       icon: <AuditOutlined /> },
  { key: 'matrix',            label: 'Role Matrix',        icon: <TableOutlined /> },
]

export default function AutomationPermissions() {
  const [activeTab, setActiveTab] = useState('policies')

  return (
    <div style={{ padding: '24px', background: '#f8fafc', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Space align="start">
          <div
            style={{
              width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, #1e40af, #3b82f6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <LockOutlined style={{ fontSize: 22, color: '#fff' }} />
          </div>
          <div>
            <Title level={3} style={{ margin: 0 }}>Automation Permissions</Title>
            <Text type="secondary">Role-based access control for workflows and automations</Text>
          </div>
        </Space>
      </div>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {TABS.map(t => (
          <Button
            key={t.key}
            type={activeTab === t.key ? 'primary' : 'default'}
            icon={t.icon}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </Button>
        ))}
      </div>

      {/* Tab content */}
      <Card bodyStyle={{ padding: 20 }}>
        {activeTab === 'policies'   && <PolicyList />}
        {activeTab === 'restricted' && <RestrictedActions />}
        {activeTab === 'audit'      && <AuditLogs />}
        {activeTab === 'matrix'     && <RoleMatrixView />}
      </Card>
    </div>
  )
}

// ─── Re-exported hook for builder / command center integration ────────────────

/**
 * Use this hook inside any component to check if the current user
 * can perform an action on a workflow.
 *
 * Example:
 *   const { data } = usePermissionCheck({ action: 'activate', workflow_id: id })
 *   if (!data?.allowed) return <Tooltip title={data?.reason}><Button disabled>Activate</Button></Tooltip>
 */
export function usePermissionCheck(payload: { action: string; workflow_id?: string; resource_type?: string }) {
  return useQuery({
    queryKey: ['permission-check', payload],
    queryFn: async () => {
      const res = await automationPermissionsApi.checkPermission(payload)
      return (res.data as any)?.data as {
        allowed: boolean
        requires_approval: boolean
        decision: AuditDecision
        reason: string
      }
    },
    staleTime: 30_000,
  })
}
