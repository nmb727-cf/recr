import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tabs,
  Tag,
  Typography,
  Switch,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useState } from 'react'
import {
  Activity,
  CheckCircle2,
  Clock,
  Code,
  Filter,
  History,
  Info,
  Layers,
  Play,
  Zap,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { agencyWorkflowApi } from '@/api/agencyWorkflowApi'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

type EventTriggersSection = 'registry' | 'subscriptions' | 'logs'

function formatDateTime(value: unknown) {
  if (!value) return 'Not available'
  const parsed = dayjs(String(value))
  return parsed.isValid() ? parsed.format('DD MMM YYYY, HH:mm') : String(value)
}

function humanize(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Not set'
  return String(value).replace(/_/g, ' ')
}

function statusColor(value: unknown) {
  const normalized = String(value ?? '').toLowerCase()
  if (/emitted|consumed|executed|matched|active/.test(normalized)) return 'green'
  if (/ignored|filtered_out|pending/.test(normalized)) return 'gold'
  if (/failed|blocked/.test(normalized)) return 'red'
  return 'default'
}

function RegistrySection() {
  const registryQuery = useApiQuery(['agency-events', 'registry'], agencyWorkflowApi.listEventRegistry)
  const registry = (registryQuery.data as any[]) ?? []

  const columns: ColumnsType<any> = [
    { title: 'Event Name', dataIndex: 'event_name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Key', dataIndex: 'event_key', key: 'key', render: (v) => <Tag font-mono>{v}</Tag> },
    { title: 'Module', dataIndex: 'module_scope', key: 'module', render: humanize },
    { title: 'Status', dataIndex: 'is_active', key: 'status', render: (v) => <Badge status={v ? 'success' : 'default'} text={v ? 'Active' : 'Inactive'} /> },
    { title: 'Schema', dataIndex: 'payload_schema', key: 'schema', render: (v) => <Tooltip title={JSON.stringify(v, null, 2)}><Code size={14}/></Tooltip> },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={registry} loading={registryQuery.isLoading} pagination={false} />
    </Card>
  )
}

function SubscriptionsSection() {
  const subsQuery = useApiQuery(['agency-events', 'subscriptions'], agencyWorkflowApi.listEventSubscriptions)
  const workflowsQuery = useApiQuery(['agency-workflows'], agencyWorkflowApi.listWorkflows)
  
  const subscriptions = (subsQuery.data as any[]) ?? []
  const workflows = (workflowsQuery.data as any[]) ?? []

  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow', key: 'wf', render: (v) => workflows.find(w => w.id === v)?.name || v.slice(0,8) },
    { title: 'Event', dataIndex: 'event_definition', key: 'event', render: (v) => v.slice(0,8) },
    { title: 'Filters', dataIndex: 'trigger_filters', key: 'filters', render: (v) => <Text type="secondary" className="text-xs">{JSON.stringify(v)}</Text> },
    { title: 'Active', dataIndex: 'is_active', key: 'active', render: (v) => <Switch checked={v} disabled size="small" /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: formatDateTime },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={subscriptions} loading={subsQuery.isLoading} />
    </Card>
  )
}

function LogsSection() {
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const logsQuery = useApiQuery(['agency-events', 'logs'], agencyWorkflowApi.listEventLogs, { refetchInterval: 5000 })
  const debugQuery = useApiQuery(['agency-events', 'debug', selectedLogId], () => agencyWorkflowApi.getEventLogDebug(selectedLogId!), { enabled: !!selectedLogId })

  const logs = (logsQuery.data as any[]) ?? []

  const columns: ColumnsType<any> = [
    { title: 'Event', dataIndex: 'event_key', key: 'key', render: humanize },
    { title: 'Entity', key: 'entity', render: (_, r) => `${humanize(r.entity_type)} (${r.entity_id.slice(0,8)})` },
    { title: 'Module', dataIndex: 'source_module', key: 'module' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v.toUpperCase()}</Tag> },
    { title: 'Timestamp', dataIndex: 'created_at', key: 'time', render: formatDateTime },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button size="small" icon={<Info size={14}/>} onClick={() => setSelectedLogId(record.id)}>Debug</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={logs} loading={logsQuery.isLoading} />
      
      <Drawer
        title="Event Debug Trace"
        open={!!selectedLogId}
        onClose={() => setSelectedLogId(null)}
        width={600}
      >
        {debugQuery.isLoading ? <Spin /> : (
          <div className="space-y-6">
            <Title level={4}>Execution Logic</Title>
            {debugQuery.data?.map((trace: any) => (
              <div key={trace.id} className="p-4 rounded-2xl border border-slate-100 bg-slate-50 space-y-2">
                <div className="flex justify-between items-center">
                  <Text strong>Workflow: {trace.workflow.slice(0,8)}</Text>
                  <Tag color={statusColor(trace.decision)}>{trace.decision.toUpperCase()}</Tag>
                </div>
                <Text type="secondary" className="text-xs block">{trace.reason}</Text>
                {trace.trace_payload && <pre className="text-[10px] bg-white p-2 rounded-lg">{JSON.stringify(trace.trace_payload, null, 2)}</pre>}
              </div>
            ))}
            {!debugQuery.data?.length && <Empty description="No traces for this event." />}
          </div>
        )}
      </Drawer>
    </Card>
  )
}

export default function AgencyEventTriggers() {
  const [activeSection, setActiveSection] = useState<EventTriggersSection>('registry')
  const navigate = useNavigate()

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">Agency Intelligence</Text>
            <Title level={2} className="!mb-0 !mt-0">Event Triggers</Title>
            <Paragraph className="!mb-0 max-w-4xl text-slate-500">
              Open Event-Driven Architecture. Agency workflows react to real-time events from talent pools, recruiters, and client submissions.
            </Paragraph>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            { key: 'registry', label: 'Event Registry', icon: <Layers size={14}/> },
            { key: 'subscriptions', label: 'Workflow Subscriptions', icon: <Zap size={14}/> },
            { key: 'logs', label: 'Activity Log', icon: <History size={14}/> },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setActiveSection(item.key as EventTriggersSection)}
              className={`flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.18em] transition ${
                item.key === activeSection
                  ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                  : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800'
              }`}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>
      </div>

      {activeSection === 'registry' && <RegistrySection />}
      {activeSection === 'subscriptions' && <SubscriptionsSection />}
      {activeSection === 'logs' && <LogsSection />}
    </div>
  )
}
