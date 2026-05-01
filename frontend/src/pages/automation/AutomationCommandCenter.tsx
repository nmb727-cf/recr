import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Input,
  Modal,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  notification,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart2,
  Bell,
  BrainCircuit,
  CheckCircle,
  Clock,
  Copy,
  Edit2,
  ExternalLink,
  Flame,
  Layers,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldOff,
  Zap,
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { automationCommandCenterApi } from '@/api/automationCommandCenter'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { useAuthStore } from '@/store/authStore'

dayjs.extend(relativeTime)

const { Title, Text, Paragraph } = Typography

type Section =
  | 'overview'
  | 'workflows'
  | 'activity'
  | 'suggestions'
  | 'health'
  | 'executions'

type AnyRecord = Record<string, any>

const SECTIONS: Array<{ key: Section; label: string; icon: React.ReactNode }> = [
  { key: 'overview', label: 'Overview', icon: <BarChart2 size={14} /> },
  { key: 'workflows', label: 'Active Workflows', icon: <Zap size={14} /> },
  { key: 'activity', label: 'Activity Feed', icon: <Activity size={14} /> },
  { key: 'suggestions', label: 'AI Suggestions', icon: <BrainCircuit size={14} /> },
  { key: 'health', label: 'Health Monitor', icon: <ShieldAlert size={14} /> },
  { key: 'executions', label: 'Execution Monitor', icon: <Clock size={14} /> },
]

function normalizeSection(s?: string): Section {
  const valid: Section[] = ['overview', 'workflows', 'activity', 'suggestions', 'health', 'executions']
  return valid.includes(s as Section) ? (s as Section) : 'overview'
}

function fmt(value: unknown) {
  if (!value) return '—'
  const d = dayjs(String(value))
  return d.isValid() ? d.format('DD MMM, HH:mm') : String(value)
}

function statusColor(s: unknown) {
  const v = String(s ?? '').toLowerCase()
  if (/active|completed|healthy/.test(v)) return 'green'
  if (/paused|running|pending/.test(v)) return 'gold'
  if (/failed|archived|error/.test(v)) return 'red'
  return 'default'
}

function LoadingBlock() {
  return (
    <div className="flex min-h-[320px] items-center justify-center rounded-3xl border border-slate-200 bg-white">
      <Space direction="vertical" align="center" size={16}>
        <Spin size="large" />
        <Text className="text-slate-500">Loading…</Text>
      </Space>
    </div>
  )
}

// ─── Overview Section ─────────────────────────────────────────────────────────
function OverviewSection() {
  const overviewQuery = useApiQuery(
    ['acc', 'overview'],
    automationCommandCenterApi.getOverview,
    { refetchInterval: 30_000 }
  )
  const healthQuery = useApiQuery(
    ['acc', 'health'],
    automationCommandCenterApi.getHealth,
    { refetchInterval: 30_000 }
  )

  const overview = (overviewQuery.data as AnyRecord) ?? {}
  const health = (healthQuery.data as AnyRecord) ?? {}

  if (overviewQuery.isLoading) return <LoadingBlock />

  const cards = [
    {
      label: 'Active Workflows',
      value: overview.active_workflows ?? 0,
      icon: <Zap size={20} className="text-indigo-500" />,
      color: 'indigo',
    },
    {
      label: 'Executions Today',
      value: overview.executions_today ?? 0,
      icon: <Activity size={20} className="text-blue-500" />,
      color: 'blue',
    },
    {
      label: 'Success Rate',
      value: `${overview.success_rate ?? 0}%`,
      icon: <CheckCircle size={20} className="text-green-500" />,
      color: 'green',
    },
    {
      label: 'Failures Today',
      value: overview.failures_today ?? 0,
      icon: <AlertTriangle size={20} className="text-red-500" />,
      color: 'red',
    },
    {
      label: 'Automation Coverage',
      value: `${overview.automation_coverage ?? 0}%`,
      icon: <Layers size={20} className="text-purple-500" />,
      color: 'purple',
    },
    {
      label: 'Hours Saved Today',
      value: overview.hours_saved ?? 0,
      icon: <Clock size={20} className="text-amber-500" />,
      color: 'amber',
    },
  ]

  return (
    <div className="grid gap-8">
      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        {cards.map((card) => (
          <Col xs={24} sm={12} lg={8} key={card.label}>
            <Card className="rounded-3xl border-slate-200 shadow-sm h-full" bodyStyle={{ padding: '20px 24px' }}>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
                    {card.label}
                  </Text>
                  <div className="text-3xl font-black text-slate-900">{card.value}</div>
                </div>
                <div className="rounded-2xl bg-slate-50 p-3">{card.icon}</div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Module Coverage */}
      <Card className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '24px' }}>
        <div className="mb-6 space-y-1">
          <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
            Module Automation Coverage
          </Text>
          <Title level={4} className="!m-0">Coverage by Module</Title>
        </div>
        <Row gutter={[24, 16]}>
          {[
            { label: 'Candidates', pct: 72 },
            { label: 'Jobs', pct: 55 },
            { label: 'Interviews', pct: 88 },
            { label: 'Offers', pct: 64 },
          ].map((m) => (
            <Col xs={24} sm={12} key={m.label}>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Text className="font-semibold text-slate-700">{m.label}</Text>
                  <Text className="text-slate-500">{m.pct}%</Text>
                </div>
                <Progress
                  percent={m.pct}
                  showInfo={false}
                  strokeColor={m.pct >= 80 ? '#22c55e' : m.pct >= 50 ? '#f59e0b' : '#ef4444'}
                />
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Health Summary */}
      {!healthQuery.isLoading && (
        <Card className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '24px' }}>
          <div className="mb-6 space-y-1">
            <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
              Automation Health
            </Text>
            <Title level={4} className="!m-0">System Health Snapshot</Title>
          </div>
          <Row gutter={[16, 16]}>
            {[
              { label: 'Failing Workflows', value: health.failing_workflows ?? 0, icon: <AlertTriangle size={16} />, color: 'text-red-500' },
              { label: 'Paused Workflows', value: health.paused_workflows ?? 0, icon: <Pause size={16} />, color: 'text-amber-500' },
              { label: 'Conflicts Detected', value: health.conflicts_detected ?? 0, icon: <ShieldAlert size={16} />, color: 'text-orange-500' },
              { label: 'Execution Delays', value: health.execution_delays ?? 0, icon: <Clock size={16} />, color: 'text-purple-500' },
            ].map((h) => (
              <Col xs={12} sm={6} key={h.label}>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-center">
                  <div className={`mb-1 flex justify-center ${h.color}`}>{h.icon}</div>
                  <div className="text-2xl font-black text-slate-900">{h.value}</div>
                  <Text className="text-[10px] text-slate-500">{h.label}</Text>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Quick Create */}
      <QuickAutomationSection />

      {/* Notifications Banner */}
      <NotificationsBanner health={health} />
    </div>
  )
}

// ─── Quick Automation ─────────────────────────────────────────────────────────
function QuickAutomationSection() {
  const navigate = useNavigate()

  const quickItems = [
    { label: 'Candidate Follow-up', trigger: 'candidate_stage_stalled', icon: <Zap size={14} /> },
    { label: 'Interview Reminder', trigger: 'interview_scheduled', icon: <Bell size={14} /> },
    { label: 'Offer Reminder', trigger: 'offer_sent', icon: <RefreshCw size={14} /> },
    { label: 'Recruiter Assignment', trigger: 'job_posted', icon: <Play size={14} /> },
    { label: 'SLA Escalation', trigger: 'sla_breached', icon: <Flame size={14} /> },
  ]

  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '24px' }}>
      <div className="mb-6 space-y-1">
        <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
          Quick Automation
        </Text>
        <Title level={4} className="!m-0">Create Automation Instantly</Title>
        <Paragraph className="!mb-0 text-slate-500">
          One-click workflow creation from proven automation patterns.
        </Paragraph>
      </div>
      <div className="flex flex-wrap gap-3">
        {quickItems.map((item) => (
          <Button
            key={item.label}
            icon={item.icon}
            onClick={() => navigate('/workflows/workflows')}
            className="rounded-2xl border-indigo-200 bg-indigo-50 font-semibold text-indigo-700 hover:bg-indigo-100"
          >
            {item.label}
          </Button>
        ))}
      </div>
    </Card>
  )
}

// ─── Notifications Banner ─────────────────────────────────────────────────────
function NotificationsBanner({ health }: { health: AnyRecord }) {
  const alerts: string[] = []
  if ((health.failing_workflows ?? 0) > 0)
    alerts.push(`${health.failing_workflows} workflow(s) are failing and need attention.`)
  if ((health.conflicts_detected ?? 0) > 0)
    alerts.push(`${health.conflicts_detected} trigger conflict(s) detected across active workflows.`)
  if ((health.execution_delays ?? 0) > 0)
    alerts.push(`${health.execution_delays} execution(s) are delayed beyond 30 minutes.`)

  if (alerts.length === 0) return null

  return (
    <div className="space-y-2">
      {alerts.map((msg, i) => (
        <Alert
          key={i}
          type="warning"
          showIcon
          icon={<Bell size={16} />}
          message={msg}
          className="rounded-2xl"
        />
      ))}
    </div>
  )
}

// ─── Workflows Section ────────────────────────────────────────────────────────
function WorkflowsSection() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterPriority, setFilterPriority] = useState<string | undefined>()

  const workflowsQuery = useApiQuery(
    ['acc', 'workflows', search, filterStatus, filterPriority],
    () =>
      automationCommandCenterApi.listWorkflows({
        search: search || undefined,
        status: filterStatus,
        priority: filterPriority,
      }),
    { refetchInterval: 15_000 }
  )

  const toggleMutation = useApiMutation(
    (id: string) => intelligenceHubApi.toggleAutomation(id),
    {
      successMessage: 'Workflow status updated.',
      errorMessage: 'Failed to update workflow.',
      invalidateKeys: [['acc', 'workflows']],
    }
  )

  const workflows = (workflowsQuery.data as AnyRecord[]) ?? []

  const columns: ColumnsType<AnyRecord> = [
    {
      title: 'Workflow Name',
      dataIndex: 'name',
      key: 'name',
      render: (v, record) => (
        <div className="space-y-0.5">
          <Text strong className="text-slate-900">{v}</Text>
          {record.is_critical && (
            <div>
              <Tag color="red" className="text-[10px]">CRITICAL</Tag>
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Trigger',
      dataIndex: 'trigger',
      key: 'trigger',
      render: (v) => <Tag color="blue">{String(v).replace(/_/g, ' ').toUpperCase()}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v) => <Tag color={statusColor(v)}>{String(v).toUpperCase()}</Tag>,
    },
    {
      title: 'Executions Today',
      dataIndex: 'executions_today',
      key: 'executions_today',
      render: (v) => <Text>{v}</Text>,
    },
    {
      title: 'Success Rate',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (v) => (
        <div className="flex items-center gap-2">
          <Progress
            percent={Number(v)}
            size="small"
            showInfo={false}
            strokeColor={Number(v) >= 80 ? '#22c55e' : Number(v) >= 50 ? '#f59e0b' : '#ef4444'}
            className="w-16"
          />
          <Text className="text-xs">{v}%</Text>
        </div>
      ),
    },
    {
      title: 'Last Run',
      dataIndex: 'last_run',
      key: 'last_run',
      render: (v) => <Text className="text-xs text-slate-500">{fmt(v)}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="Edit">
            <Button
              size="small"
              icon={<Edit2 size={12} />}
              onClick={() => navigate(`/intelligence/workflows/${record.id}/builder`)}
              className="rounded-lg"
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? 'Pause' : 'Activate'}>
            <Button
              size="small"
              icon={record.status === 'active' ? <Pause size={12} /> : <Play size={12} />}
              onClick={() => toggleMutation.mutate(record.id)}
              loading={toggleMutation.isPending}
              className="rounded-lg"
            />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button
              size="small"
              icon={<Copy size={12} />}
              onClick={() => navigate('/workflows/templates')}
              className="rounded-lg"
            />
          </Tooltip>
          <Tooltip title="Analytics">
            <Button
              size="small"
              icon={<BarChart2 size={12} />}
              onClick={() => navigate('/automation-analytics')}
              className="rounded-lg"
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div className="grid gap-6">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="Search workflows…"
          prefix={<Search size={14} className="text-slate-400" />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64 rounded-xl"
          allowClear
        />
        <Select
          placeholder="Status"
          allowClear
          className="w-36"
          value={filterStatus}
          onChange={setFilterStatus}
          options={[
            { label: 'Active', value: 'active' },
            { label: 'Paused', value: 'paused' },
            { label: 'Draft', value: 'draft' },
            { label: 'Archived', value: 'archived' },
          ]}
        />
        <Select
          placeholder="Priority"
          allowClear
          className="w-36"
          value={filterPriority}
          onChange={setFilterPriority}
          options={[
            { label: 'High', value: 'high' },
            { label: 'Medium', value: 'medium' },
            { label: 'Low', value: 'low' },
          ]}
        />
        <div className="ml-auto flex gap-2">
          <Button
            icon={<Plus size={14} />}
            type="primary"
            onClick={() => navigate('/workflows/workflows')}
            className="rounded-xl font-semibold"
          >
            Create Workflow
          </Button>
          <Button
            icon={<ExternalLink size={14} />}
            onClick={() => navigate('/workflows/templates')}
            className="rounded-xl font-semibold"
          >
            Import Template
          </Button>
        </div>
      </div>

      <Card className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={workflows}
          loading={workflowsQuery.isLoading}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          locale={{ emptyText: <Empty description="No workflows found" /> }}
        />
      </Card>
    </div>
  )
}

// ─── Activity Feed ────────────────────────────────────────────────────────────
function ActivityFeedSection() {
  const activityQuery = useApiQuery(
    ['acc', 'activity'],
    () => automationCommandCenterApi.getActivity({ limit: 60 }),
    { refetchInterval: 15_000 }
  )

  const events = (activityQuery.data as AnyRecord[]) ?? []

  const columns: ColumnsType<AnyRecord> = [
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      render: (v) => (
        <Tooltip title={fmt(v)}>
          <Text className="text-xs text-slate-500">{dayjs(v).fromNow()}</Text>
        </Tooltip>
      ),
      width: 120,
    },
    {
      title: 'Workflow',
      dataIndex: 'workflow_name',
      key: 'workflow_name',
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: 'Action / Trigger',
      dataIndex: 'action',
      key: 'action',
      render: (v) => <Tag color="blue">{String(v).replace(/_/g, ' ').toUpperCase()}</Tag>,
    },
    {
      title: 'Entity',
      key: 'entity',
      render: (_, r) => (
        <Text className="text-xs text-slate-500">
          {r.entity_type} · {String(r.entity_id).slice(0, 8)}…
        </Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v) => <Tag color={statusColor(v)}>{String(v).toUpperCase()}</Tag>,
    },
  ]

  if (activityQuery.isLoading) return <LoadingBlock />

  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="px-6 pt-6 pb-4 border-b border-slate-100">
        <Title level={4} className="!m-0">Recent Automation Events</Title>
        <Text className="text-slate-500">Live feed of automation activity across all modules.</Text>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={events}
        loading={activityQuery.isLoading}
        pagination={{ pageSize: 25, showSizeChanger: false }}
        locale={{ emptyText: <Empty description="No automation events yet" /> }}
      />
    </Card>
  )
}

// ─── AI Suggestions ───────────────────────────────────────────────────────────
function AISuggestionsSection() {
  const navigate = useNavigate()

  const suggestionsQuery = useApiQuery(
    ['acc', 'suggestions'],
    automationCommandCenterApi.getAISuggestions,
    { refetchInterval: 60_000 }
  )

  const dismissMutation = useApiMutation(
    (id: string) => intelligenceHubApi.dismissSuggestion(id),
    {
      successMessage: 'Suggestion dismissed.',
      errorMessage: 'Failed to dismiss.',
      invalidateKeys: [['acc', 'suggestions']],
    }
  )

  const suggestions = (suggestionsQuery.data as AnyRecord[]) ?? []

  if (suggestionsQuery.isLoading) return <LoadingBlock />

  if (suggestions.length === 0) {
    return (
      <Card className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '48px 24px' }}>
        <Empty
          description="No pending AI suggestions"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {suggestions.map((s) => (
        <Card
          key={s.id}
          className="rounded-3xl border-slate-200 shadow-sm"
          bodyStyle={{ padding: '20px 24px' }}
        >
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <BrainCircuit size={16} className="shrink-0 text-indigo-500" />
                <Text strong className="text-slate-900 leading-snug">{s.title}</Text>
              </div>
              <Tag color={s.confidence_band === 'high' ? 'green' : s.confidence_band === 'low' ? 'red' : 'gold'}>
                {String(s.confidence_band ?? 'medium').toUpperCase()}
              </Tag>
            </div>

            {s.summary && (
              <Paragraph className="!mb-0 text-sm text-slate-500">{s.summary}</Paragraph>
            )}

            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <Tag color="purple" className="text-[10px]">{s.source_module}</Tag>
              <span>{dayjs(s.created_at).fromNow()}</span>
            </div>

            <div className="flex gap-2">
              <Button
                type="primary"
                size="small"
                icon={<Plus size={12} />}
                onClick={() => navigate('/workflows/workflows')}
                className="rounded-xl font-semibold flex-1"
              >
                Create Automation
              </Button>
              <Button
                size="small"
                onClick={() => dismissMutation.mutate(s.id)}
                loading={dismissMutation.isPending}
                className="rounded-xl"
              >
                Dismiss
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

// ─── Health Monitor ───────────────────────────────────────────────────────────
function HealthSection() {
  const healthQuery = useApiQuery(
    ['acc', 'health'],
    automationCommandCenterApi.getHealth,
    { refetchInterval: 20_000 }
  )

  const health = (healthQuery.data as AnyRecord) ?? {}

  if (healthQuery.isLoading) return <LoadingBlock />

  const indicators = [
    {
      label: 'Workflows Failing',
      value: health.failing_workflows ?? 0,
      icon: <AlertTriangle size={20} />,
      color: (health.failing_workflows ?? 0) > 0 ? 'text-red-500 bg-red-50' : 'text-green-500 bg-green-50',
      severity: (health.failing_workflows ?? 0) > 0 ? 'error' : 'success',
    },
    {
      label: 'Workflows Paused',
      value: health.paused_workflows ?? 0,
      icon: <Pause size={20} />,
      color: (health.paused_workflows ?? 0) > 0 ? 'text-amber-500 bg-amber-50' : 'text-green-500 bg-green-50',
      severity: (health.paused_workflows ?? 0) > 0 ? 'warning' : 'success',
    },
    {
      label: 'Conflicts Detected',
      value: health.conflicts_detected ?? 0,
      icon: <ShieldAlert size={20} />,
      color: (health.conflicts_detected ?? 0) > 0 ? 'text-orange-500 bg-orange-50' : 'text-green-500 bg-green-50',
      severity: (health.conflicts_detected ?? 0) > 0 ? 'warning' : 'success',
    },
    {
      label: 'Execution Delays (>30m)',
      value: health.execution_delays ?? 0,
      icon: <Clock size={20} />,
      color: (health.execution_delays ?? 0) > 0 ? 'text-purple-500 bg-purple-50' : 'text-green-500 bg-green-50',
      severity: (health.execution_delays ?? 0) > 0 ? 'warning' : 'success',
    },
  ]

  return (
    <div className="grid gap-6">
      <Row gutter={[16, 16]}>
        {indicators.map((ind) => (
          <Col xs={24} sm={12} key={ind.label}>
            <Card className="rounded-3xl border-slate-200 shadow-sm h-full" bodyStyle={{ padding: '20px 24px' }}>
              <div className="flex items-center gap-4">
                <div className={`rounded-2xl p-3 ${ind.color}`}>{ind.icon}</div>
                <div>
                  <div className="text-3xl font-black text-slate-900">{ind.value}</div>
                  <Text className="text-slate-500">{ind.label}</Text>
                </div>
                {ind.value > 0 && (
                  <Badge
                    status={ind.severity as any}
                    className="ml-auto"
                  />
                )}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {(health.failing_workflows ?? 0) > 0 && (
        <Alert
          type="error"
          showIcon
          icon={<AlertTriangle size={16} />}
          message={`${health.failing_workflows} workflow(s) are currently failing.`}
          description="Go to the Active Workflows section to investigate and take action."
          className="rounded-2xl"
        />
      )}
      {(health.conflicts_detected ?? 0) > 0 && (
        <Alert
          type="warning"
          showIcon
          icon={<ShieldAlert size={16} />}
          message={`${health.conflicts_detected} trigger conflict(s) detected.`}
          description="Multiple workflows share the same trigger event. Review to avoid duplicate actions."
          className="rounded-2xl"
        />
      )}
      {(health.execution_delays ?? 0) > 0 && (
        <Alert
          type="warning"
          showIcon
          icon={<Clock size={16} />}
          message={`${health.execution_delays} execution(s) are delayed beyond 30 minutes.`}
          description="These executions may be stalled. Check the Execution Monitor for details."
          className="rounded-2xl"
        />
      )}
    </div>
  )
}

// ─── Execution Monitor ────────────────────────────────────────────────────────
function ExecutionMonitorSection() {
  const executionsQuery = useApiQuery(
    ['acc', 'executions'],
    automationCommandCenterApi.getExecutions,
    { refetchInterval: 10_000 }
  )

  const executions = (executionsQuery.data as AnyRecord[]) ?? []

  const columns: ColumnsType<AnyRecord> = [
    {
      title: 'Workflow',
      dataIndex: 'workflow',
      key: 'workflow',
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: 'Entity',
      key: 'entity',
      render: (_, r) => (
        <Text className="text-xs text-slate-500">
          {r.entity_type} · {String(r.entity_id).slice(0, 8)}…
        </Text>
      ),
    },
    {
      title: 'Step',
      dataIndex: 'step',
      key: 'step',
      render: (v) => <Tag color="blue">Step {v}</Tag>,
      width: 90,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (v) => <Text className="text-xs text-slate-500">{fmt(v)}</Text>,
    },
    {
      title: 'Duration',
      dataIndex: 'duration_seconds',
      key: 'duration_seconds',
      render: (v) => {
        const m = Math.floor(Number(v) / 60)
        const s = Number(v) % 60
        const label = m > 0 ? `${m}m ${s}s` : `${s}s`
        return (
          <Text className={`text-xs ${Number(v) > 1800 ? 'text-red-500 font-bold' : 'text-slate-500'}`}>
            {label}
          </Text>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v) => (
        <Badge
          status="processing"
          text={<Tag color={statusColor(v)}>{String(v).toUpperCase()}</Tag>}
        />
      ),
    },
  ]

  if (executionsQuery.isLoading) return <LoadingBlock />

  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-slate-100">
        <div>
          <Title level={4} className="!m-0">Running Executions</Title>
          <Text className="text-slate-500">
            Live view of workflows currently executing.{' '}
            <Badge status="processing" text="Auto-refreshes every 10s" className="text-xs" />
          </Text>
        </div>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={executions}
        loading={executionsQuery.isLoading}
        pagination={false}
        locale={{ emptyText: <Empty description="No running executions" /> }}
      />
    </Card>
  )
}

// ─── Global Controls Modal ────────────────────────────────────────────────────
function GlobalControlsModal({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const [notifApi, contextHolder] = notification.useNotification()

  const pauseAll = useApiMutation(
    automationCommandCenterApi.pauseAll,
    {
      successMessage: 'All workflows paused.',
      errorMessage: 'Failed to pause workflows.',
      invalidateKeys: [['acc']],
    }
  )

  const resumeAll = useApiMutation(
    automationCommandCenterApi.resumeAll,
    {
      successMessage: 'All workflows resumed.',
      errorMessage: 'Failed to resume workflows.',
      invalidateKeys: [['acc']],
    }
  )

  const emergencyStop = useApiMutation(
    automationCommandCenterApi.emergencyStop,
    {
      successMessage: 'Emergency stop applied.',
      errorMessage: 'Emergency stop failed.',
      invalidateKeys: [['acc']],
    }
  )

  return (
    <>
      {contextHolder}
      <Modal
        open={open}
        onCancel={onClose}
        footer={null}
        title={
          <div className="flex items-center gap-2">
            <ShieldOff size={18} className="text-red-500" />
            <span>Automation Global Controls</span>
          </div>
        }
        className="rounded-3xl"
        width={480}
      >
        <div className="space-y-4 py-4">
          <Alert
            type="warning"
            showIcon
            message="Admin-only controls"
            description="These actions affect all workflows across the entire tenant. Use with caution."
            className="rounded-2xl"
          />

          <div className="space-y-3">
            <Button
              block
              size="large"
              icon={<Pause size={16} />}
              onClick={() => { pauseAll.mutate(undefined); onClose() }}
              loading={pauseAll.isPending}
              className="rounded-2xl h-12 font-semibold border-amber-300 text-amber-700 hover:bg-amber-50"
            >
              Pause All Automation
            </Button>

            <Button
              block
              size="large"
              icon={<Play size={16} />}
              onClick={() => { resumeAll.mutate(undefined); onClose() }}
              loading={resumeAll.isPending}
              className="rounded-2xl h-12 font-semibold border-green-300 text-green-700 hover:bg-green-50"
            >
              Resume All Automation
            </Button>

            <Button
              block
              size="large"
              danger
              icon={<ShieldOff size={16} />}
              onClick={() => {
                Modal.confirm({
                  title: 'Emergency Stop',
                  content:
                    'This will immediately deactivate ALL workflows and stop all running executions. This action cannot be undone automatically. Continue?',
                  okText: 'Yes, Emergency Stop',
                  okButtonProps: { danger: true },
                  onOk: () => { emergencyStop.mutate(undefined); onClose() },
                })
              }}
              loading={emergencyStop.isPending}
              className="rounded-2xl h-12 font-bold"
            >
              Emergency Stop
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function AutomationCommandCenter() {
  const { section } = useParams<{ section?: string }>()
  const navigate = useNavigate()
  const activeSection = normalizeSection(section)
  const [globalControlsOpen, setGlobalControlsOpen] = useState(false)

  const user = useAuthStore((s) => s.user)
  const isAdmin = ['super_admin', 'tenant_admin'].includes(user?.role ?? '')

  const sectionMap: Record<Section, React.ReactNode> = {
    overview: <OverviewSection />,
    workflows: <WorkflowsSection />,
    activity: <ActivityFeedSection />,
    suggestions: <AISuggestionsSection />,
    health: <HealthSection />,
    executions: <ExecutionMonitorSection />,
  }

  return (
    <div className="grid gap-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">
              Intelligence Hub
            </Text>
            <Title level={2} className="!mb-0 !mt-0">
              Automation Command Center
            </Title>
            <Paragraph className="!mb-0 max-w-4xl text-slate-500">
              Central control panel for all automation. Monitor workflows, track executions, act on AI insights, and manage automation health in real time.
            </Paragraph>
          </div>

          {isAdmin && (
            <Button
              icon={<ShieldOff size={14} />}
              danger
              onClick={() => setGlobalControlsOpen(true)}
              className="rounded-2xl font-semibold shrink-0"
            >
              Global Controls
            </Button>
          )}
        </div>

        {/* Section Nav */}
        <div className="flex flex-wrap gap-2">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              type="button"
              onClick={() => navigate(`/automation-center/${s.key}`)}
              className={`flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.18em] transition ${
                s.key === activeSection
                  ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                  : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800'
              }`}
            >
              {s.icon}
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Section Content */}
      {sectionMap[activeSection]}

      {/* Global Controls Modal */}
      <GlobalControlsModal
        open={globalControlsOpen}
        onClose={() => setGlobalControlsOpen(false)}
      />
    </div>
  )
}
