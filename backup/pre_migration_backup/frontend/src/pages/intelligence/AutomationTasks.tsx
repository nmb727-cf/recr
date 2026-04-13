import { useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
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
  BarChartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FireOutlined,
  PlusOutlined,
  ReloadOutlined,
  RocketOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  automationTasksApi,
  type AssigneeType,
  type TaskAnalytics,
  type TaskEscalation,
  type TaskExecution,
  type TaskPriority,
  type TaskRule,
  type TaskRulePayload,
  type TaskStatus,
} from '@/api/automationTasks'

const { Title, Text } = Typography
const { Option }     = Select
const { TextArea }   = Input

// ─── Helpers ──────────────────────────────────────────────────────────────────

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: 'default', medium: 'blue', high: 'orange', urgent: 'red',
}
const STATUS_COLOR: Record<TaskStatus, string> = {
  pending: 'default', in_progress: 'processing', completed: 'success',
  overdue: 'warning', cancelled: 'default', escalated: 'error',
}
const STATUS_ICON: Partial<Record<TaskStatus, React.ReactNode>> = {
  completed:   <CheckCircleOutlined />,
  overdue:     <ClockCircleOutlined />,
  escalated:   <AlertOutlined />,
  in_progress: <RocketOutlined />,
}

function priorityTag(p: TaskPriority) {
  return <Tag color={PRIORITY_COLOR[p]}>{p.toUpperCase()}</Tag>
}

function statusTag(s: TaskStatus) {
  return (
    <Tag color={STATUS_COLOR[s]} icon={STATUS_ICON[s]}>
      {s.replace('_', ' ')}
    </Tag>
  )
}

function formatDue(dt: string | null) {
  if (!dt) return '—'
  const d   = new Date(dt)
  const now = new Date()
  const overdue = d < now
  return (
    <Text type={overdue ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
      {overdue ? '⚠ ' : ''}{d.toLocaleString()}
    </Text>
  )
}

// ─── Tab: Task Rules ──────────────────────────────────────────────────────────

function TaskRules() {
  const qc = useQueryClient()
  const [open, setOpen]       = useState(false)
  const [editing, setEditing] = useState<TaskRule | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['wf-task-rules'],
    queryFn:  async () => {
      const res = await automationTasksApi.listRules()
      return (res.data as any)?.data?.rules as TaskRule[]
    },
  })

  const delMut = useMutation({
    mutationFn: (id: string) => automationTasksApi.deleteRule(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['wf-task-rules'] }),
  })

  const columns = [
    {
      title: 'Task Title Template',
      dataIndex: 'task_title_template',
      render: (v: string) => <Text code style={{ fontSize: 12 }}>{v}</Text>,
    },
    {
      title: 'Assignee',
      dataIndex: 'assignee_type',
      render: (v: string) => <Tag icon={<UserOutlined />}>{v.replace(/_/g, ' ')}</Tag>,
    },
    { title: 'Priority', dataIndex: 'priority', render: priorityTag },
    {
      title: 'SLA',
      dataIndex: 'due_in_minutes',
      render: (v: number) => <Tag color="blue">{v >= 1440 ? `${v / 1440}d` : `${v}m`}</Tag>,
    },
    {
      title: 'Escalate After',
      dataIndex: 'escalate_after_minutes',
      render: (v: number) => <Tag color="orange">{v >= 1440 ? `${v / 1440}d` : `${v}m`}</Tag>,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      render: (v: boolean) => <Badge status={v ? 'success' : 'default'} text={v ? 'On' : 'Off'} />,
    },
    {
      title: '',
      render: (_: unknown, row: TaskRule) => (
        <Space>
          <Button size="small" onClick={() => { setEditing(row); setOpen(true) }}>Edit</Button>
          <Button size="small" danger onClick={() =>
            Modal.confirm({ title: 'Delete rule?', onOk: () => delMut.mutate(row.id) })
          }>Delete</Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>Task Rules</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setOpen(true) }}>
          New Rule
        </Button>
      </div>
      <Table
        dataSource={data} columns={columns} rowKey="id"
        loading={isLoading} size="middle" pagination={{ pageSize: 10 }}
      />
      <RuleDrawer open={open} rule={editing} onClose={() => { setOpen(false); setEditing(null) }} />
    </>
  )
}

function RuleDrawer({ open, rule, onClose }: { open: boolean; rule: TaskRule | null; onClose: () => void }) {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const isEdit = !!rule

  const saveMut = useMutation({
    mutationFn: (p: TaskRulePayload) =>
      isEdit ? automationTasksApi.updateRule(rule!.id, p) : automationTasksApi.createRule(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-task-rules'] })
      onClose()
      form.resetFields()
    },
  })

  return (
    <Drawer
      title={isEdit ? 'Edit Task Rule' : 'New Task Rule'}
      open={open} onClose={onClose} width={540}
      extra={
        <Button type="primary" loading={saveMut.isPending}
          onClick={() => form.validateFields().then(v => saveMut.mutate(v))}>
          Save
        </Button>
      }
    >
      <Form form={form} layout="vertical" initialValues={rule ?? { priority: 'medium', due_in_minutes: 1440, escalate_after_minutes: 2880, is_active: true }}>
        <Form.Item name="workflow_id" label="Workflow ID" rules={[{ required: true }]}>
          <Input placeholder="UUID of the workflow" />
        </Form.Item>
        <Form.Item name="task_title_template" label="Title Template" rules={[{ required: true }]}>
          <Input placeholder='e.g. Review {{candidate_name}} for {{job_title}}' />
        </Form.Item>
        <Form.Item name="task_description_template" label="Description Template">
          <TextArea rows={3} placeholder='e.g. Candidate applied via {{source}}.' />
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="assignee_type" label="Assignee Type" rules={[{ required: true }]}>
              <Select>
                {(['assigned_recruiter','hiring_manager','recruiter_manager','workflow_owner','specific_user','dynamic_field'] as AssigneeType[]).map(t =>
                  <Option key={t} value={t}>{t.replace(/_/g, ' ')}</Option>
                )}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="priority" label="Priority">
              <Select>
                {(['low','medium','high','urgent'] as TaskPriority[]).map(p =>
                  <Option key={p} value={p}>{priorityTag(p)}</Option>
                )}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="assignee_field" label="Assignee Field (for dynamic_field)">
          <Input placeholder="e.g. candidate.recruiter_id" />
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="due_in_minutes" label="SLA (minutes)">
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="escalate_after_minutes" label="Escalate After (minutes)">
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="is_active" label="Active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

// ─── Tab: Task Executions ─────────────────────────────────────────────────────

function TaskExecutions() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState<{ status?: TaskStatus; priority?: TaskPriority }>({})

  const { data, isLoading } = useQuery({
    queryKey: ['wf-task-executions', filters],
    queryFn:  async () => {
      const res = await automationTasksApi.listExecutions({ ...filters, limit: 100 } as any)
      return (res.data as any)?.data as { executions: TaskExecution[]; meta: any }
    },
  })

  const completeMut = useMutation({
    mutationFn: (id: string) => automationTasksApi.completeTask(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['wf-task-executions'] }),
  })

  const columns = [
    {
      title: 'Task',
      dataIndex: 'task_title',
      render: (v: string) => <Text strong style={{ fontSize: 13 }}>{v}</Text>,
    },
    {
      title: 'Assignee',
      dataIndex: 'assignee_user_id',
      render: (v: string | null) => v ? <Text copyable={{ text: v }}>{v.slice(0, 8)}…</Text> : <Text type="secondary">Unassigned</Text>,
    },
    { title: 'Priority', dataIndex: 'priority', render: priorityTag },
    {
      title: 'Due',
      dataIndex: 'due_at',
      render: formatDue,
    },
    { title: 'Status',  dataIndex: 'status',    render: statusTag },
    {
      title: 'Escalated',
      dataIndex: 'escalated',
      render: (v: boolean) => v ? <Tag color="error" icon={<AlertOutlined />}>Yes</Tag> : '—',
    },
    {
      title: '',
      render: (_: unknown, row: TaskExecution) =>
        !['completed', 'cancelled'].includes(row.status) ? (
          <Button
            size="small" type="primary" icon={<CheckCircleOutlined />}
            onClick={() => completeMut.mutate(row.id)}
            loading={completeMut.isPending}
          >
            Complete
          </Button>
        ) : null,
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <Select allowClear placeholder="Filter by status" style={{ width: 160 }}
          onChange={v => setFilters(f => ({ ...f, status: v }))}>
          {(['pending','in_progress','completed','overdue','escalated'] as TaskStatus[]).map(s =>
            <Option key={s} value={s}>{s.replace('_', ' ')}</Option>
          )}
        </Select>
        <Select allowClear placeholder="Filter by priority" style={{ width: 160 }}
          onChange={v => setFilters(f => ({ ...f, priority: v }))}>
          {(['low','medium','high','urgent'] as TaskPriority[]).map(p =>
            <Option key={p} value={p}>{p}</Option>
          )}
        </Select>
        <Button icon={<ReloadOutlined />} onClick={() => qc.invalidateQueries({ queryKey: ['wf-task-executions'] })}>
          Refresh
        </Button>
      </div>
      <Table
        dataSource={data?.executions} columns={columns} rowKey="id"
        loading={isLoading} size="middle" pagination={{ pageSize: 20 }}
      />
    </>
  )
}

// ─── Tab: Escalation Dashboard ────────────────────────────────────────────────

function EscalationDashboard() {
  const { data: execData } = useQuery({
    queryKey: ['wf-task-executions-escalated'],
    queryFn:  async () => {
      const res = await automationTasksApi.listExecutions({ escalated: true, limit: 50 } as any)
      return (res.data as any)?.data?.executions as TaskExecution[]
    },
  })

  const { data: overdueData } = useQuery({
    queryKey: ['wf-task-executions-overdue'],
    queryFn:  async () => {
      const res = await automationTasksApi.listExecutions({ status: 'overdue', limit: 50 } as any)
      return (res.data as any)?.data?.executions as TaskExecution[]
    },
  })

  const { data: urgentData } = useQuery({
    queryKey: ['wf-task-executions-urgent'],
    queryFn:  async () => {
      const res = await automationTasksApi.listExecutions({ priority: 'urgent', limit: 50 } as any)
      return (res.data as any)?.data?.executions as TaskExecution[]
    },
  })

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={8}>
        <Card
          title={<Space><AlertOutlined style={{ color: '#ff4d4f' }} /><Text strong>Escalated</Text></Space>}
          size="small"
        >
          {execData?.length ? (
            execData.slice(0, 8).map(t => (
              <div key={t.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Text style={{ fontSize: 12 }}>{t.task_title}</Text>
                <div><Tag color="error">L{t.escalations?.length ?? 1}</Tag>{formatDue(t.due_at)}</div>
              </div>
            ))
          ) : <Text type="secondary">No escalated tasks</Text>}
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card
          title={<Space><ClockCircleOutlined style={{ color: '#faad14' }} /><Text strong>Overdue</Text></Space>}
          size="small"
        >
          {overdueData?.length ? (
            overdueData.slice(0, 8).map(t => (
              <div key={t.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Text style={{ fontSize: 12 }}>{t.task_title}</Text>
                <div>{priorityTag(t.priority)}{formatDue(t.due_at)}</div>
              </div>
            ))
          ) : <Text type="secondary">No overdue tasks</Text>}
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card
          title={<Space><FireOutlined style={{ color: '#ff4d4f' }} /><Text strong>Urgent</Text></Space>}
          size="small"
        >
          {urgentData?.length ? (
            urgentData.slice(0, 8).map(t => (
              <div key={t.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Text style={{ fontSize: 12 }}>{t.task_title}</Text>
                <div>{statusTag(t.status)}</div>
              </div>
            ))
          ) : <Text type="secondary">No urgent tasks</Text>}
        </Card>
      </Col>
    </Row>
  )
}

// ─── Tab: Task Analytics ──────────────────────────────────────────────────────

function TaskAnalyticsTab() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['wf-task-analytics'],
    queryFn:  async () => {
      const res = await automationTasksApi.getAnalytics()
      return (res.data as any)?.data?.analytics as TaskAnalytics
    },
  })

  const slaTrackerMut = useMutation({
    mutationFn: () => automationTasksApi.trackSLA(),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['wf-task-analytics', 'wf-task-executions'] }),
  })

  if (isLoading || !data) return <Card loading />

  const priorityColors: Record<string, string> = { low: '#52c41a', medium: '#1890ff', high: '#fa8c16', urgent: '#ff4d4f' }

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="Total Tasks" value={data.total} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Completed" value={data.completed} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Overdue" value={data.overdue} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Escalated" value={data.escalated} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="Completion Rate" size="small">
            <Progress
              type="circle"
              percent={data.completion_rate}
              strokeColor={data.completion_rate >= 70 ? '#52c41a' : '#faad14'}
              format={p => `${p}%`}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="By Priority" size="small">
            {Object.entries(data.by_priority || {}).map(([p, count]) => (
              <div key={p} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Tag color={priorityColors[p] ?? 'default'}>{p}</Tag>
                  <Text>{count as number}</Text>
                </div>
                <Progress
                  percent={data.total ? Math.round((count as number) / data.total * 100) : 0}
                  strokeColor={priorityColors[p]}
                  size="small"
                  showInfo={false}
                />
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 16 }}>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => slaTrackerMut.mutate()}
          loading={slaTrackerMut.isPending}
        >
          Run SLA Tracker Now
        </Button>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = [
  { key: 'rules',       label: 'Task Rules',    icon: <RocketOutlined /> },
  { key: 'executions',  label: 'Executions',    icon: <CheckCircleOutlined /> },
  { key: 'escalations', label: 'Escalations',   icon: <AlertOutlined /> },
  { key: 'analytics',   label: 'Analytics',     icon: <BarChartOutlined /> },
]

export default function AutomationTasks() {
  const [activeTab, setActiveTab] = useState('rules')

  return (
    <div style={{ padding: '24px', background: '#f8fafc', minHeight: '100vh' }}>
      <div style={{ marginBottom: 16 }}>
        <Space align="start">
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <RocketOutlined style={{ fontSize: 22, color: '#fff' }} />
          </div>
          <div>
            <Title level={3} style={{ margin: 0 }}>Task Automation</Title>
            <Text type="secondary">
              Auto-create, assign, escalate and track tasks across workflow executions
            </Text>
          </div>
        </Space>
      </div>

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
        {activeTab === 'rules'       && <TaskRules />}
        {activeTab === 'executions'  && <TaskExecutions />}
        {activeTab === 'escalations' && <EscalationDashboard />}
        {activeTab === 'analytics'   && <TaskAnalyticsTab />}
      </Card>
    </div>
  )
}
