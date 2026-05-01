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
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useState } from 'react'
import {
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  Play,
  Send,
  UserCheck,
  Calendar,
  DollarSign,
  ArrowRight,
  ExternalLink,
  Target,
  Briefcase,
  Users
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { agencyWorkflowApi } from '@/api/agencyWorkflowApi'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

type AgencyOrchestrationSection =
  | 'instances'
  | 'approvals'
  | 'client-responses'
  | 'interviews'
  | 'offers'
  | 'placements'

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
  if (/completed|approved|accepted|responded|joined|active/.test(normalized)) return 'green'
  if (/pending|waiting|waiting_internal|waiting_client|waiting_candidate|waiting_interview|waiting_offer|reminded/.test(normalized)) return 'gold'
  if (/failed|rejected|cancelled|exhausted|overdue|escalated|breached/.test(normalized)) return 'red'
  return 'default'
}

function InstancesSection() {
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null)
  const instancesQuery = useApiQuery(['agency-orchestration', 'processes'], () => agencyWorkflowApi.listOrchestrationProcesses(), { refetchInterval: 10000 })
  const timelineQuery = useApiQuery(
    ['agency-orchestration', 'timeline', selectedInstanceId],
    () => agencyWorkflowApi.getOrchestrationTimeline(selectedInstanceId as string),
    { enabled: !!selectedInstanceId }
  )

  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow_id', key: 'workflow', render: (v) => <Text strong>{v?.slice(0,8)}</Text> },
    { title: 'Candidate', dataIndex: 'candidate_id', key: 'candidate', render: (v) => <Tag color="blue">{v?.slice(0,8)}</Tag> },
    { title: 'Client', dataIndex: 'client_id', key: 'client', render: (v) => <Tag color="purple">{v?.slice(0,8)}</Tag> },
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
      <Table rowKey="id" columns={columns} dataSource={instancesQuery.data as any[]} loading={instancesQuery.isLoading} />
      
      <Drawer
        title="Agency Process Timeline"
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
                  <Text type="secondary" className="text-xs">{humanize(stage.stage_type)}</Text>
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

function ApprovalsSection() {
  const approvalsQuery = useApiQuery(['agency-orchestration', 'approvals'], () => agencyWorkflowApi.listOrchestrationApprovals())
  
  const approveMutation = useApiMutation(
    (id: string) => agencyWorkflowApi.approveOrchestrationRequest(id, {}),
    { successMessage: 'Approved', invalidateKeys: [['agency-orchestration']] }
  )

  const rejectMutation = useApiMutation(
    (id: string) => agencyWorkflowApi.rejectOrchestrationRequest(id, {}),
    { successMessage: 'Rejected', invalidateKeys: [['agency-orchestration']] }
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
          <Button size="small" type="primary" onClick={() => approveMutation.mutate(record.id)}>Approve</Button>
          <Button size="small" danger onClick={() => rejectMutation.mutate(record.id)}>Reject</Button>
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

function ClientResponsesSection() {
  const responsesQuery = useApiQuery(['agency-orchestration', 'client-responses'], () => agencyWorkflowApi.listOrchestrationClientResponses())
  
  const followupMutation = useApiMutation(
    (id: string) => agencyWorkflowApi.followupClientResponse(id),
    { successMessage: 'Follow-up triggered', invalidateKeys: [['agency-orchestration']] }
  )

  const completeMutation = useApiMutation(
    (id: string) => agencyWorkflowApi.completeClientResponse(id),
    { successMessage: 'Marked as responded', invalidateKeys: [['agency-orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Process', dataIndex: 'process_instance', key: 'process', render: (v) => v.slice(0,8) },
    { title: 'Response Type', dataIndex: 'response_type', key: 'type', render: humanize },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v.toUpperCase()}</Tag> },
    { title: 'Last Followup', dataIndex: 'last_followup_at', key: 'followup', render: formatDateTime },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => record.status !== 'responded' && (
        <Space>
          <Button size="small" onClick={() => followupMutation.mutate(record.id)}>Send Reminder</Button>
          <Button size="small" type="primary" onClick={() => completeMutation.mutate(record.id)}>Mark Responded</Button>
        </Space>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={responsesQuery.data as any[]} loading={responsesQuery.isLoading} />
    </Card>
  )
}

function OffersSection() {
  const offersQuery = useApiQuery(['agency-orchestration', 'offers'], () => agencyWorkflowApi.listOrchestrationOffers())
  
  const acceptMutation = useApiMutation(
    (id: string) => agencyWorkflowApi.acceptOrchestrationOffer(id),
    { successMessage: 'Offer accepted', invalidateKeys: [['agency-orchestration']] }
  )

  const columns: ColumnsType<any> = [
    { title: 'Candidate', dataIndex: 'candidate_id', key: 'candidate', render: (v) => v.slice(0,8) },
    { title: 'Client', dataIndex: 'client_id', key: 'client', render: (v) => v.slice(0,8) },
    { title: 'Round', dataIndex: 'negotiation_round', key: 'round' },
    { title: 'Proposed', dataIndex: 'proposed_amount', key: 'amount', render: (v) => v ? `$${v}` : '—' },
    { title: 'Offer Status', dataIndex: 'offer_status', key: 'offer_status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    { title: 'Process Status', dataIndex: 'status', key: 'status', render: (v) => <Tag>{humanize(v).toUpperCase()}</Tag> },
    {
      title: 'Action',
      key: 'actions',
      render: (_, record) => record.status === 'active' && (
        <Button size="small" type="primary" onClick={() => acceptMutation.mutate(record.id)}>Accept</Button>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={offersQuery.data as any[]} loading={offersQuery.isLoading} />
    </Card>
  )
}

function PlacementsSection() {
  const placementsQuery = useApiQuery(['agency-orchestration', 'placements'], () => agencyWorkflowApi.listOrchestrationPlacements())

  const columns: ColumnsType<any> = [
    { title: 'Candidate', dataIndex: 'candidate_id', key: 'candidate', render: (v) => v.slice(0,8) },
    { title: 'Client', dataIndex: 'client_id', key: 'client', render: (v) => v.slice(0,8) },
    { title: 'Placement Status', dataIndex: 'placement_status', key: 'p_status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    { title: 'Guarantee Status', dataIndex: 'guarantee_status', key: 'g_status', render: (v) => <Tag color={statusColor(v)}>{humanize(v).toUpperCase()}</Tag> },
    { title: 'Start Date', dataIndex: 'guarantee_start_date', key: 'start' },
    { title: 'End Date', dataIndex: 'guarantee_end_date', key: 'end' },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={placementsQuery.data as any[]} loading={placementsQuery.isLoading} />
    </Card>
  )
}

export default function AgencyOrchestrationEngine() {
  const [activeSection, setActiveSection] = useState<AgencyOrchestrationSection>('instances')
  const navigate = useNavigate()

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">Agency Intelligence</Text>
            <Title level={2} className="!mb-0 !mt-0">Orchestration Engine</Title>
            <Paragraph className="!mb-0 max-w-4xl text-slate-500">
              End-to-End agency process orchestration. Manage submissions, client responses, interview coordination, and placement guarantees.
            </Paragraph>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-2">
          {[
            { key: 'instances', label: 'Active Processes', icon: <Layers size={14}/> },
            { key: 'approvals', label: 'Internal Approvals', icon: <UserCheck size={14}/> },
            { key: 'client-responses', label: 'Client Responses', icon: <Send size={14}/> },
            { key: 'offers', label: 'Offers', icon: <DollarSign size={14}/> },
            { key: 'placements', label: 'Placements & Guarantees', icon: <Target size={14}/> },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setActiveSection(item.key as AgencyOrchestrationSection)}
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

      {activeSection === 'instances' && <InstancesSection />}
      {activeSection === 'approvals' && <ApprovalsSection />}
      {activeSection === 'client-responses' && <ClientResponsesSection />}
      {activeSection === 'offers' && <OffersSection />}
      {activeSection === 'placements' && <PlacementsSection />}
    </div>
  )
}
