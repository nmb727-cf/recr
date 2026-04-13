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
  InputNumber,
  Modal,
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import {
  AlertOutlined,
  BellOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  DashboardOutlined,
  MailOutlined,
  PlusOutlined,
  ReloadOutlined,
  SendOutlined,
  TeamOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import {
  automationNotificationsApi,
  type ChannelHealthMap,
  type DeliveryStatus,
  type EscalationNotification,
  type EscalationStatus,
  type InsightType,
  type NotificationChannel,
  type NotificationDelivery,
  type NotificationPreference,
  type NotificationRule,
  type RuleWritePayload,
} from '@/api/automationNotifications'

const { Title, Text } = Typography
const { Option }     = Select

// ─── Helpers ──────────────────────────────────────────────────────────────────

const CHANNEL_COLORS: Record<string, string> = {
  email: 'blue', whatsapp: 'green', in_app: 'purple', sms: 'orange', push: 'cyan',
}
const STATUS_COLORS: Record<string, string> = {
  sent: 'success', delivered: 'success', failed: 'error',
  queued: 'processing', throttled: 'warning', deduplicated: 'default', skipped: 'default',
}
const ESC_STATUS_COLORS: Record<EscalationStatus, string> = {
  pending: 'warning', sent: 'success', resolved: 'success', cancelled: 'default',
}
const INSIGHT_COLORS: Record<InsightType, string> = {
  high_failure_rate:           'red',
  duplicate_risk:              'orange',
  channel_underperforming:     'gold',
  escalation_spike:            'volcano',
  candidate_non_response_pattern: 'purple',
}

function channelTag(ch: string) {
  return <Tag color={CHANNEL_COLORS[ch] ?? 'default'}>{ch}</Tag>
}

function statusTag(s: DeliveryStatus) {
  const color = STATUS_COLORS[s] ?? 'default'
  const icon  = s === 'sent' || s === 'delivered'
    ? <CheckCircleOutlined />
    : s === 'failed' ? <CloseCircleOutlined />
    : s === 'throttled' ? <ClockCircleOutlined />
    : undefined
  return <Tag color={color} icon={icon}>{s}</Tag>
}

// ─── Tab: Notification Rules ──────────────────────────────────────────────────

function NotificationRules() {
  const qc = useQueryClient()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing]       = useState<NotificationRule | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['wf-notif-rules'],
    queryFn: async () => {
      const res = await automationNotificationsApi.listRules()
      return (res.data as any)?.data?.rules as NotificationRule[]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => automationNotificationsApi.deleteRule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['wf-notif-rules'] }),
  })

  const columns = [
    {
      title: 'Notification Event',
      dataIndex: 'notification_event',
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: 'Recipient',
      dataIndex: 'recipient_type',
      render: (v: string) => <Tag icon={<UserOutlined />}>{v.replace('_', ' ')}</Tag>,
    },
    {
      title: 'Channel',
      dataIndex: 'channel',
      render: (v: string) => channelTag(v),
    },
    {
      title: 'Fallbacks',
      dataIndex: 'fallback_channels',
      render: (v: string[]) => <Space size={4}>{v.map(ch => channelTag(ch))}</Space>,
    },
    {
      title: 'Throttle',
      dataIndex: 'throttle_window_minutes',
      render: (v: number) => v ? <Tag>{v / 60}h window</Tag> : <Tag color="default">None</Tag>,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      render: (v: boolean) => <Badge status={v ? 'success' : 'default'} text={v ? 'Active' : 'Off'} />,
    },
    {
      title: 'Actions',
      render: (_: unknown, row: NotificationRule) => (
        <Space>
          <Button size="small" onClick={() => { setEditing(row); setDrawerOpen(true) }}>Edit</Button>
          <Button
            size="small" danger
            onClick={() => Modal.confirm({
              title: 'Delete this rule?',
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
        <Title level={5} style={{ margin: 0 }}>Notification Rules</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setDrawerOpen(true) }}>
          New Rule
        </Button>
      </div>
      <Table dataSource={data} columns={columns} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 10 }} />
      <RuleDrawer open={drawerOpen} rule={editing} onClose={() => { setDrawerOpen(false); setEditing(null) }} />
    </>
  )
}

function RuleDrawer({ open, rule, onClose }: { open: boolean; rule: NotificationRule | null; onClose: () => void }) {
  const qc     = useQueryClient()
  const [form] = Form.useForm()
  const isEdit = !!rule

  const saveMutation = useMutation({
    mutationFn: (payload: RuleWritePayload) =>
      isEdit
        ? automationNotificationsApi.updateRule(rule!.id, payload)
        : automationNotificationsApi.createRule(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-notif-rules'] })
      onClose()
      form.resetFields()
    },
  })

  return (
    <Drawer
      title={isEdit ? 'Edit Notification Rule' : 'New Notification Rule'}
      open={open}
      onClose={onClose}
      width={560}
      extra={
        <Button type="primary" onClick={() => form.validateFields().then(v => saveMutation.mutate(v))} loading={saveMutation.isPending}>
          Save
        </Button>
      }
    >
      <Form form={form} layout="vertical" initialValues={rule ?? { fallback_channels: [], is_active: true }}>
        <Form.Item name="workflow_id" label="Workflow ID" rules={[{ required: true }]}>
          <Input placeholder="UUID of the workflow" />
        </Form.Item>
        <Form.Item name="notification_event" label="Notification Event" rules={[{ required: true }]}>
          <Input placeholder="e.g. candidate.interview_scheduled" />
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="recipient_type" label="Recipient Type" rules={[{ required: true }]}>
              <Select>
                {['candidate','assigned_recruiter','hiring_manager','recruiter_manager','agency_contact','custom_user','workflow_owner'].map(r =>
                  <Option key={r} value={r}>{r.replace('_', ' ')}</Option>
                )}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="channel" label="Primary Channel" rules={[{ required: true }]}>
              <Select>
                {['email','whatsapp','in_app','sms','push'].map(ch =>
                  <Option key={ch} value={ch}>{channelTag(ch)}</Option>
                )}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="fallback_channels" label="Fallback Channels (ordered)">
          <Select mode="multiple">
            {['email','whatsapp','in_app'].map(ch =>
              <Option key={ch} value={ch}>{channelTag(ch)}</Option>
            )}
          </Select>
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="throttle_window_minutes" label="Throttle Window (mins)">
              <InputNumber min={0} style={{ width: '100%' }} placeholder="0 = off" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="send_delay_minutes" label="Send Delay (mins)">
              <InputNumber min={0} style={{ width: '100%' }} placeholder="0 = immediate" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="dedupe_key_template" label="Dedup Key Template">
          <Input placeholder="e.g. reminder:{candidate_id}:{job_id}" />
        </Form.Item>
        <Form.Item name="is_active" label="Active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

// ─── Tab: Delivery Log ────────────────────────────────────────────────────────

function DeliveryLog() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState<{ channel?: string; status?: string }>({})

  const { data, isLoading } = useQuery({
    queryKey: ['wf-notif-deliveries', filters],
    queryFn: async () => {
      const res = await automationNotificationsApi.listDeliveries({ ...filters, limit: 100 } as any)
      return (res.data as any)?.data as { deliveries: NotificationDelivery[]; meta: any }
    },
  })

  const retryMutation = useMutation({
    mutationFn: (id: string) => automationNotificationsApi.retryDelivery(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['wf-notif-deliveries'] }),
  })

  const columns = [
    {
      title: 'Time',
      dataIndex: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
      sorter: true,
    },
    { title: 'Recipient', dataIndex: 'recipient_email', render: (v: string) => v || '—' },
    { title: 'Channel', dataIndex: 'channel', render: channelTag },
    { title: 'Status',  dataIndex: 'status',  render: statusTag },
    {
      title: 'Retries',
      dataIndex: 'retry_count',
      render: (v: number) => v > 0 ? <Tag color="orange">{v}×</Tag> : '—',
    },
    {
      title: 'Failure Reason',
      dataIndex: 'failure_reason',
      ellipsis: true,
      render: (v: string) => v ? <Text type="danger" style={{ fontSize: 12 }}>{v}</Text> : '—',
    },
    {
      title: '',
      render: (_: unknown, row: NotificationDelivery) =>
        (row.status === 'failed' || row.status === 'queued') ? (
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => retryMutation.mutate(row.id)}
            loading={retryMutation.isPending}
          >
            Retry
          </Button>
        ) : null,
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <Select allowClear placeholder="Filter by channel" style={{ width: 160 }} onChange={v => setFilters(f => ({ ...f, channel: v }))}>
          {['email','whatsapp','in_app'].map(ch => <Option key={ch} value={ch}>{ch}</Option>)}
        </Select>
        <Select allowClear placeholder="Filter by status" style={{ width: 160 }} onChange={v => setFilters(f => ({ ...f, status: v }))}>
          {['queued','sent','delivered','failed','throttled','deduplicated','skipped'].map(s =>
            <Option key={s} value={s}>{s}</Option>
          )}
        </Select>
      </div>
      <Table
        dataSource={data?.deliveries}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        size="small"
      />
    </>
  )
}

// ─── Tab: Escalation Log ──────────────────────────────────────────────────────

function EscalationLog() {
  const { data, isLoading } = useQuery({
    queryKey: ['wf-notif-escalations'],
    queryFn: async () => {
      const res = await automationNotificationsApi.listEscalations()
      return (res.data as any)?.data?.escalations as EscalationNotification[]
    },
  })

  const columns = [
    { title: 'Level', dataIndex: 'escalation_level', render: (v: number) => <Tag color="volcano">L{v}</Tag> },
    {
      title: 'Reason',
      dataIndex: 'trigger_reason',
      ellipsis: true,
    },
    {
      title: 'Target',
      dataIndex: 'target_recipient_type',
      render: (v: string) => <Tag icon={<TeamOutlined />}>{v.replace('_', ' ')}</Tag>,
    },
    { title: 'Channel', dataIndex: 'channel', render: channelTag },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (v: EscalationStatus) => <Tag color={ESC_STATUS_COLORS[v]}>{v}</Tag>,
    },
    {
      title: 'Sent At',
      dataIndex: 'sent_at',
      render: (v: string | null) => v ? new Date(v).toLocaleString() : '—',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
    },
  ]

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="id"
      loading={isLoading}
      pagination={{ pageSize: 20 }}
      size="middle"
    />
  )
}

// ─── Tab: Channel Health ──────────────────────────────────────────────────────

function ChannelHealthDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['wf-notif-channel-health'],
    queryFn: async () => {
      const res = await automationNotificationsApi.getChannelHealth()
      return (res.data as any)?.data?.channel_health as ChannelHealthMap
    },
  })

  if (isLoading) return <Card loading />
  if (!data) return null

  const channels = (['email', 'whatsapp', 'in_app'] as NotificationChannel[])

  return (
    <Row gutter={[16, 16]}>
      {channels.map(ch => {
        const h = data[ch]
        if (!h) return null
        return (
          <Col xs={24} sm={12} lg={8} key={ch}>
            <Card
              title={
                <Space>
                  <MailOutlined />
                  <Text strong>{ch.replace('_', ' ').toUpperCase()}</Text>
                </Space>
              }
              size="small"
            >
              <Row gutter={8}>
                <Col span={12}><Statistic title="Total Sent" value={h.total} /></Col>
                <Col span={12}><Statistic title="Delivered" value={h.sent} /></Col>
              </Row>
              <div style={{ marginTop: 12 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Delivery Rate</Text>
                <Progress
                  percent={h.delivery_rate}
                  strokeColor={h.delivery_rate >= 80 ? '#52c41a' : h.delivery_rate >= 50 ? '#faad14' : '#ff4d4f'}
                  size="small"
                />
              </div>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Failure Rate</Text>
                <Progress
                  percent={h.failure_rate}
                  strokeColor="#ff4d4f"
                  size="small"
                />
              </div>
              <div style={{ marginTop: 8 }}>
                <Tag color="orange">Fallbacks: {h.fallback_used}</Tag>
                <Tag color="red">Failed: {h.failed}</Tag>
              </div>
            </Card>
          </Col>
        )
      })}
    </Row>
  )
}

// ─── Tab: User Preferences ────────────────────────────────────────────────────

function UserPreferences() {
  const { data, isLoading } = useQuery({
    queryKey: ['wf-notif-preferences'],
    queryFn: async () => {
      const res = await automationNotificationsApi.listPreferences()
      return (res.data as any)?.data?.preferences as NotificationPreference[]
    },
  })

  const columns = [
    {
      title: 'User ID',
      dataIndex: 'user_id',
      render: (v: string) => <Text copyable={{ text: v }}>{v.slice(0, 8)}…</Text>,
    },
    { title: 'Notification Type', dataIndex: 'notification_type', render: (v: string) => <Text code>{v}</Text> },
    {
      title: 'Preferred Channels',
      dataIndex: 'preferred_channels',
      render: (v: string[]) => <Space size={4}>{v.map(ch => channelTag(ch))}</Space>,
    },
    {
      title: 'Quiet Hours',
      render: (_: unknown, row: NotificationPreference) =>
        row.quiet_hours_start
          ? <Tag color="blue">{row.quiet_hours_start} – {row.quiet_hours_end}</Tag>
          : <Tag color="default">None</Tag>,
    },
    {
      title: 'Escalation Override',
      dataIndex: 'allow_escalation_override',
      render: (v: boolean) => <Badge status={v ? 'success' : 'default'} text={v ? 'Yes' : 'No'} />,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      render: (v: boolean) => <Badge status={v ? 'success' : 'default'} />,
    },
  ]

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="id"
      loading={isLoading}
      pagination={{ pageSize: 15 }}
      size="middle"
    />
  )
}

// ─── Insight badges in header ─────────────────────────────────────────────────

function InsightBanner() {
  const { data } = useQuery({
    queryKey: ['wf-notif-insights'],
    queryFn: async () => {
      const res = await automationNotificationsApi.listInsights()
      return (res.data as any)?.data?.insights as { insight_type: InsightType; title: string; description: string }[]
    },
  })

  if (!data?.length) return null

  return (
    <div style={{ marginBottom: 16 }}>
      {data.slice(0, 3).map((insight, i) => (
        <Alert
          key={i}
          type={insight.insight_type === 'high_failure_rate' ? 'error' : 'warning'}
          icon={<WarningOutlined />}
          showIcon
          message={insight.title}
          description={insight.description}
          style={{ marginBottom: 8 }}
          closable
        />
      ))}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = [
  { key: 'rules',       label: 'Rules',          icon: <BellOutlined /> },
  { key: 'deliveries',  label: 'Delivery Log',   icon: <SendOutlined /> },
  { key: 'escalations', label: 'Escalations',    icon: <AlertOutlined /> },
  { key: 'health',      label: 'Channel Health', icon: <DashboardOutlined /> },
  { key: 'preferences', label: 'Preferences',    icon: <UserOutlined /> },
]

export default function AutomationNotifications() {
  const [activeTab, setActiveTab] = useState('rules')

  return (
    <div style={{ padding: '24px', background: '#f8fafc', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Space align="start">
          <div
            style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <BellOutlined style={{ fontSize: 22, color: '#fff' }} />
          </div>
          <div>
            <Title level={3} style={{ margin: 0 }}>Notification Orchestration</Title>
            <Text type="secondary">
              Multi-channel workflow communication — routing, throttling, retries &amp; escalations
            </Text>
          </div>
        </Space>
      </div>

      <InsightBanner />

      {/* Tab nav */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
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

      <Card bodyStyle={{ padding: 20 }}>
        {activeTab === 'rules'       && <NotificationRules />}
        {activeTab === 'deliveries'  && <DeliveryLog />}
        {activeTab === 'escalations' && <EscalationLog />}
        {activeTab === 'health'      && <ChannelHealthDashboard />}
        {activeTab === 'preferences' && <UserPreferences />}
      </Card>
    </div>
  )
}
