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
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  Layout,
  Play,
  Send,
  UserCheck,
  Calendar,
  DollarSign,
  ArrowRight,
  ExternalLink,
  Pause,
  StopCircle,
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

type OrchestrationSection =
  | 'definitions'
  | 'instances'
  | 'approvals'
  | 'scheduling'
  | 'negotiations'
  | 'handoffs'

const SECTION_ITEMS: Array<{ key: OrchestrationSection; label: string }> = [
  { key: 'definitions', label: 'Process Definitions' },
  { key: 'instances', label: 'Active Instances' },
  { key: 'approvals', label: 'Approval Queue' },
  { key: 'scheduling', label: 'Scheduling Queue' },
  { key: 'negotiations', label: 'Negotiation Queue' },
  { key: 'handoffs', label: 'Handoff Queue' },
]

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
  if (/completed|approved|accepted|booked|sent|active|running/.test(normalized)) return 'green'
  if (/pending|waiting|waiting_human|waiting_approval|waiting_schedule|within_band/.test(normalized)) return 'gold'
  if (/failed|rejected|cancelled|exhausted/.test(normalized)) return 'red'
  return 'default'
}

function OrchestrationHeader({
  section,
  navigate,
}: {
  section: OrchestrationSection
  navigate: ReturnType<typeof useNavigate>
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">Intelligence Hub</Text>
          <Title level={2} className="!mb-0 !mt-0">
            Orchestration Engine
          </Title>
          <Paragraph className="!mb-0 max-w-4xl text-slate-500">
            End-to-End business process orchestration for complex hiring workflows. Coordinate interview rounds, approvals, negotiations, and system handoffs.
          </Paragraph>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {SECTION_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => navigate(`/intelligence/orchestration/${item.key}`)}
            className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.18em] transition ${
              item.key === section
                ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function ActiveInstancesSection() {
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null)
  const instancesQuery = useApiQuery(['orchestration', 'processes'], () => intelligenceHubApi.listOrchestrationProcesses(), {
    refetchInterval: 10000,
  })

  const timelineQuery = useApiQuery(
    ['orchestration', 'timeline', selectedInstanceId],
    () => intelligenceHubApi.getOrchestrationTimeline(selectedInstanceId as string),
    { enabled: !!selectedInstanceId }
  )

  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow_id', key: 'workflow', render: (v) => <Text strong>{v.slice(0,8)}</Text> },
    { title: 'Entity', key: 'entity', render: (_, r) => <Tag color="blue">{humanize(r.entity_type)}: {r.entity_id?.slice(0,8)}</Tag> },
    { title: 'Current Stage', dataIndex: 'current_stage', key: 'stage', render: (v) => <Badge status={v ? 'processing' : 'default'} text={humanize(v) || 'Initiating'} /> },
    { title: 'Status', dataIndex: 'process_status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    { title: 'Started', dataIndex: 'started_at', key: 'started', render: formatDateTime },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button size="small" onClick={() => setSelectedInstanceId(record.id)}>Timeline</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table 
        rowKey="id" 
        columns={columns} 
        dataSource={instancesQuery.data as any[]} 
        loading={instancesQuery.isLoading} 
      />
      
      <Drawer
        title="Process Stage Timeline"
        open={!!selectedInstanceId}
        onClose={() => setSelectedInstanceId(null)}
        width={600}
      >
        {timelineQuery.isLoading ? <Spin /> : (
          <div className="space-y-6">
            <Title level={4}>Execution Roadmap</Title>
            {(timelineQuery.data as any)?.stages?.map((stage: any, i: number) => (
              <div key={stage.id} className="flex gap-4 relative">
                {i < (timelineQuery.data as any).stages.length - 1 && (
                  <div className="absolute left-[11px] top-6 bottom-[-24px] w-[2px] bg-slate-100" />
                )}
                <div className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center z-10",
                  stage.status === 'completed' ? "bg-green-500 text-white" : "bg-slate-200"
                )}>
                  {stage.status === 'completed' ? <CheckCircle2 size={14}/> : <Clock size={14}/>}
                </div>
                <div className="flex-1 pb-8">
                  <div className="flex justify-between items-start">
                    <Text strong className="block">{humanize(stage.stage_key)}</Text>
                    <Tag color={statusColor(stage.status)}>{stage.status.toUpperCase()}</Tag>
                  </div>
                  <Text type="secondary" className="text-xs">{stage.stage_type.replace(/_/g, ' ')}</Text>
                </div>
              </div>
            ))}
            {!(timelineQuery.data as any)?.stages?.length && <Empty description="No stages executed yet." />}
          </div>
        )}
      </Drawer>
    </Card>
  )
}

function ApprovalQueueSection() {
  const approvalsQuery = useApiQuery(['orchestration', 'approvals'], () => intelligenceHubApi.listOrchestrationApprovals())
  
  const approveMutation = useApiMutation(
    ({ id, notes }: { id: string; notes?: string }) => intelligenceHubApi.approveOrchestrationRequest(id, { notes }),
    { successMessage: 'Approved successfully', invalidateKeys: [['orchestration']] }
  )

  const rejectMutation = useApiMutation(
    ({ id, notes }: { id: string; notes?: string }) => intelligenceHubApi.rejectOrchestrationRequest(id, { notes }),
    { successMessage: 'Rejected successfully', invalidateKeys: [['orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Process', dataIndex: 'process_instance', key: 'process', render: (v) => v.slice(0,8) },
    { title: 'Type', dataIndex: 'approval_type', key: 'type', render: humanize },
    { title: 'Requested From', dataIndex: 'requested_from_user_id', key: 'user', render: (v) => v.slice(0,8) },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v.toUpperCase()}</Tag> },
    { title: 'Requested At', dataIndex: 'requested_at', key: 'date', render: formatDateTime },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => record.status === 'pending' && (
        <Space>
          <Button size="small" type="primary" onClick={() => approveMutation.mutate({ id: record.id })}>Approve</Button>
          <Button size="small" danger onClick={() => rejectMutation.mutate({ id: record.id })}>Reject</Button>
        </Space>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={approvalsQuery.data as any[]} loading={approvalsQuery.isLoading} />
    </Card>
  )
}

function SchedulingQueueSection() {
  const schedulingQuery = useApiQuery(['orchestration', 'scheduling'], () => intelligenceHubApi.listOrchestrationScheduling())
  
  const bookMutation = useApiMutation(
    ({ id, slot }: { id: string; slot: any }) => intelligenceHubApi.bookOrchestrationSlot(id, { slot_data: slot }),
    { successMessage: 'Booked successfully', invalidateKeys: [['orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Process', dataIndex: 'process_instance', key: 'process', render: (v) => v.slice(0,8) },
    { title: 'Type', dataIndex: 'scheduling_type', key: 'type', render: humanize },
    { title: 'Mode', dataIndex: 'target_mode', key: 'mode', render: (v) => <Tag>{v.toUpperCase()}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    {
      title: 'Action',
      key: 'actions',
      render: (_, record) => record.status !== 'booked' && (
        <Button size="small" icon={<Calendar size={14}/>} onClick={() => bookMutation.mutate({ id: record.id, slot: { start: '2026-04-10T10:00:00Z', end: '2026-04-10T11:00:00Z' } })}>Book Test Slot</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={schedulingQuery.data as any[]} loading={schedulingQuery.isLoading} />
    </Card>
  )
}

function NegotiationQueueSection() {
  const negotiationsQuery = useApiQuery(['orchestration', 'negotiations'], () => intelligenceHubApi.listOrchestrationNegotiations())
  
  const acceptMutation = useApiMutation(
    (id: string) => intelligenceHubApi.acceptOrchestrationNegotiation(id),
    { successMessage: 'Offer accepted', invalidateKeys: [['orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Offer ID', dataIndex: 'offer_id', key: 'offer', render: (v) => v.slice(0,8) },
    { title: 'Round', dataIndex: 'negotiation_round', key: 'round' },
    { title: 'Proposed', dataIndex: 'proposed_amount', key: 'amount', render: (v) => `$${v}` },
    { title: 'Band', key: 'band', render: (_, r) => `$${r.allowed_band_min} - $${r.allowed_band_max}` },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    {
      title: 'Action',
      key: 'actions',
      render: (_, record) => record.status === 'pending' && (
        <Button size="small" type="primary" onClick={() => acceptMutation.mutate(record.id)}>Accept</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={negotiationsQuery.data as any[]} loading={negotiationsQuery.isLoading} />
    </Card>
  )
}

function HandoffQueueSection() {
  const handoffsQuery = useApiQuery(['orchestration', 'handoffs'], () => intelligenceHubApi.listOrchestrationHandoffs())
  
  const sendMutation = useApiMutation(
    (id: string) => intelligenceHubApi.sendOrchestrationHandoff(id),
    { successMessage: 'Handoff triggered', invalidateKeys: [['orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Type', dataIndex: 'handoff_type', key: 'type', render: (v) => <Tag color="purple">{v.toUpperCase()}</Tag> },
    { title: 'Destination', dataIndex: 'destination_system', key: 'dest' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v.toUpperCase()}</Tag> },
    { title: 'Created', dataIndex: 'created_at', key: 'date', render: formatDateTime },
    {
      title: 'Action',
      key: 'actions',
      render: (_, record) => record.status === 'pending' && (
        <Button size="small" icon={<Send size={14}/>} onClick={() => sendMutation.mutate(record.id)}>Send Payload</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={handoffsQuery.data as any[]} loading={handoffsQuery.isLoading} />
    </Card>
  )
}

function ProcessDefinitionsSection() {
  const workflowsQuery = useApiQuery(['orchestration', 'workflows'], () => intelligenceHubApi.listWorkflows())
  const navigate = useNavigate()

  const columns: ColumnsType<any> = [
    { title: 'Process Name', dataIndex: 'name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Trigger', dataIndex: 'trigger_event', key: 'trigger', render: (v) => <Tag color="orange">{humanize(v)}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v?.toUpperCase()}</Tag> },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button size="small" onClick={() => navigate(`/intelligence/workflows/${record.id}/builder`)}>Design Flow</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={workflowsQuery.data as any[]} loading={workflowsQuery.isLoading} />
    </Card>
  )
}

export default function OrchestrationEngine() {
  const params = useParams<{ section?: string }>()
  const navigate = useNavigate()
  const section = (params.section as OrchestrationSection) || 'definitions'

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <OrchestrationHeader section={section} navigate={navigate} />
      
      {section === 'definitions' && <ProcessDefinitionsSection />}
      {section === 'instances' && <ActiveInstancesSection />}
      {section === 'approvals' && <ApprovalQueueSection />}
      {section === 'scheduling' && <SchedulingQueueSection />}
      {section === 'negotiations' && <NegotiationQueueSection />}
      {section === 'handoffs' && <HandoffQueueSection />}
    </div>
  )
}
