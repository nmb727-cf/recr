import React, { useState } from 'react'
import { 
  Typography, 
  Card, 
  Tag, 
  Table, 
  Spin, 
  Alert, 
  Empty, 
  Tabs, 
  Button, 
  Statistic, 
  List, 
  Badge,
  Space,
  Tooltip,
  Progress,
  Modal,
  Form,
  Input,
  Switch,
  notification
} from 'antd'
import { 
  ShieldCheck, 
  Activity, 
  Clock, 
  UserCheck, 
  Zap, 
  AlertTriangle, 
  FileText, 
  Settings,
  RefreshCw,
  History,
  Undo2,
  Lock,
  Eye
} from 'lucide-react'
import { useApiQuery, useApiMutation } from '@/hooks/useApiQuery'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import dayjs from 'dayjs'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function WorkflowGovernance() {
  const [activeTab, setActiveTab] = useState('health')
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null)

  const { data: healthData, isLoading: loadingHealth } = useApiQuery(
    ['workflow-governance-health'],
    () => intelligenceHubApi.getWorkflowHealth()
  )

  const { data: approvalsData, isLoading: loadingApprovals, refetch: refetchApprovals } = useApiQuery(
    ['workflow-approvals'],
    () => intelligenceHubApi.listWorkflowApprovals(),
    { enabled: activeTab === 'approvals' }
  )

  const { data: auditData, isLoading: loadingAudit } = useApiQuery(
    ['workflow-audit-logs'],
    () => intelligenceHubApi.listWorkflowAuditLogs(),
    { enabled: activeTab === 'audit' }
  )

  const health = (healthData as any)?.data || { total_24h: 0, failed_24h: 0, paused_workflows: 0, pending_approvals: 0, active_workflows: 0 }
  const approvals = (approvalsData as any)?.data || []
  const auditLogs = (auditData as any)?.data || []

  return (
    <div className="flex flex-col gap-8">
      
      {/* ─── Governance Header ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <Text className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400">Enterprise Safety & Control</Text>
          <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">Workflow Governance</Title>
        </div>
        <div className="flex items-center gap-3">
           <Tag className="m-0 rounded-full bg-slate-900 text-emerald-400 px-4 py-1.5 border-none font-black text-[10px] uppercase tracking-widest flex items-center gap-2">
             <Lock size={12} /> Compliance Engine Active
           </Tag>
        </div>
      </div>

      {/* ─── Tabs ─── */}
      <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <div className="px-8 pt-8 border-b border-slate-100 bg-white">
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            items={[
              { 
                key: 'health', 
                label: <TabLabel label="Health Dashboard" icon={<Activity size={14}/>} />,
                children: <HealthSection health={health} loading={loadingHealth} />
              },
              { 
                key: 'approvals', 
                label: <TabLabel label="Approval Queue" icon={<UserCheck size={14}/>} />,
                children: <ApprovalsSection approvals={approvals} loading={loadingApprovals} onRefresh={refetchApprovals} />
              },
              { 
                key: 'audit', 
                label: <TabLabel label="Audit Ledger" icon={<History size={14}/>} />,
                children: <AuditSection logs={auditLogs} loading={loadingAudit} />
              },
              {
                key: 'safety',
                label: <TabLabel label="Safety Rules" icon={<ShieldCheck size={14}/>} />,
                children: <div className="p-10 text-center"><Empty description="Select a workflow to manage its safety rules" /></div>
              }
            ]}
          />
        </div>
      </Card>
    </div>
  )
}

function HealthSection({ health, loading }: any) {
  if (loading) return <div className="p-20 text-center"><Spin size="large" /></div>

  return (
    <div className="p-8 space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
         <MetricCard label="Active Workflows" value={health.active_workflows} color="indigo" />
         <MetricCard label="Runs (24h)" value={health.total_24h} color="blue" />
         <MetricCard label="Failure Rate" value={`${((health.failed_24h / (health.total_24h || 1)) * 100).toFixed(1)}%`} color={health.failed_24h > 0 ? "rose" : "emerald"} />
         <MetricCard label="Pending Approvals" value={health.pending_approvals} color="amber" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
         <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title="System Reliability">
            <div className="space-y-6 p-2">
               <div>
                  <div className="flex justify-between mb-2">
                     <Text className="text-xs font-bold text-slate-600">Workflow Uptime</Text>
                     <Text className="text-xs font-black text-emerald-600">99.98%</Text>
                  </div>
                  <Progress percent={99.9} showInfo={false} strokeColor="#10b981" />
               </div>
               <div>
                  <div className="flex justify-between mb-2">
                     <Text className="text-xs font-bold text-slate-600">Safety Guard Hits</Text>
                     <Text className="text-xs font-black text-amber-600">{health.paused_workflows} Paused</Text>
                  </div>
                  <Progress percent={health.paused_workflows > 0 ? 80 : 100} showInfo={false} strokeColor="#f59e0b" />
               </div>
            </div>
         </Card>
         <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title="Governance Status">
            <div className="flex items-center justify-center h-32">
               <div className="text-center">
                  <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
                     <ShieldCheck size={24} />
                  </div>
                  <Text className="text-sm font-black text-slate-800">All Systems Compliant</Text>
                  <Paragraph className="text-[10px] text-slate-400 mt-1">No critical safety violations in last 7 days</Paragraph>
               </div>
            </div>
         </Card>
      </div>
    </div>
  )
}

function ApprovalsSection({ approvals, loading, onRefresh }: any) {
  const decideMutation = useApiMutation(
    ({ id, status, comment }: any) => intelligenceHubApi.decideWorkflowApproval(id, { status, comment }),
    {
      successMessage: 'Approval decision recorded',
      onSuccess: onRefresh
    }
  )

  const columns = [
    { 
      title: 'Workflow', 
      dataIndex: 'workflow_name', 
      render: (v: any, record: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{v || 'Critical Automation'}</Text>
          <Text type="secondary" className="text-[10px]">Version {record.version_number || '1.0'}</Text>
        </Space>
      )
    },
    { title: 'Requested By', dataIndex: 'requested_by', render: (v: any) => <Text className="text-xs font-bold text-slate-500">{v?.slice(0,8) || 'SYSTEM'}</Text> },
    { title: 'Requested At', dataIndex: 'created_at', render: (v: any) => <Text className="text-xs text-slate-400">{dayjs(v).fromNow()}</Text> },
    { 
      title: 'Actions', 
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" type="primary" className="bg-emerald-600 rounded-lg text-[10px] font-black uppercase" onClick={() => decideMutation.mutate({ id: record.id, status: 'approved' })}>Approve</Button>
          <Button size="small" danger className="rounded-lg text-[10px] font-black uppercase" onClick={() => decideMutation.mutate({ id: record.id, status: 'rejected' })}>Reject</Button>
        </Space>
      )
    }
  ]

  return (
    <div className="p-8">
      <Table 
        dataSource={approvals} 
        columns={columns} 
        loading={loading} 
        rowKey="id"
        pagination={false}
        locale={{ emptyText: <Empty description="No pending approvals" /> }}
      />
    </div>
  )
}

function AuditSection({ logs, loading }: any) {
  const rollbackMutation = useApiMutation(
    (id: string) => intelligenceHubApi.rollbackWorkflowExecution(id),
    { successMessage: 'Rollback initiated' }
  )

  const columns = [
    { 
      title: 'Action', 
      dataIndex: 'action', 
      render: (v: any) => <Tag className="m-0 border-none bg-slate-100 text-slate-700 font-black text-[10px] uppercase px-3 rounded-lg">{v}</Tag> 
    },
    { title: 'Workflow', dataIndex: 'workflow_name', render: (v: any) => <Text className="text-xs font-bold text-slate-700">{v || 'System'}</Text> },
    { title: 'Performed By', dataIndex: 'performed_by', render: (v: any) => <Text className="text-xs font-bold text-slate-500">{v?.slice(0,8) || 'SYSTEM'}</Text> },
    { title: 'Timestamp', dataIndex: 'timestamp', render: (v: any) => <Text className="text-xs text-slate-400 font-bold">{dayjs(v).format('MMM DD, HH:mm:ss')}</Text> },
    { 
      title: 'Action', 
      key: 'rollback',
      render: (_: any, record: any) => (
        record.action === 'executed' && (
          <Tooltip title="Rollback this execution">
            <Button size="small" icon={<Undo2 size={12}/>} onClick={() => rollbackMutation.mutate(record.execution_id)} loading={rollbackMutation.isPending} />
          </Tooltip>
        )
      )
    }
  ]

  return (
    <div className="p-8">
      <Table 
        dataSource={logs} 
        columns={columns} 
        loading={loading} 
        rowKey="id"
        pagination={{ pageSize: 15 }}
      />
    </div>
  )
}

function TabLabel({ label, icon }: any) {
  return (
    <div className="flex items-center gap-2 px-1">
       <span className="text-slate-500">{icon}</span>
       <span className="text-[11px] font-black uppercase tracking-widest">{label}</span>
    </div>
  )
}

function MetricCard({ label, value, color }: any) {
  return (
    <Card className="rounded-3xl border-slate-100 shadow-soft-sm">
       <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1 tracking-widest">{label}</Text>
       <Text className={cn("text-3xl font-black", `text-${color}-600`)}>{value}</Text>
    </Card>
  )
}
