import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Empty,
  List,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  AlertCircle,
  AlertOctagon,
  Clock,
  Heart,
  Pulse,
  Radar,
  RefreshCw,
  ShieldAlert,
  Zap,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { automationObservabilityApi } from '@/api/automationObservability'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationObservability() {
  const [activeTab, setActiveTab] = useState('live')

  const liveQuery = useApiQuery(['workflow-observability', 'live'], automationObservabilityApi.getLiveMonitors, { refetchInterval: 5000 })
  const failuresQuery = useApiQuery(['workflow-observability', 'failures'], automationObservabilityApi.getFailures)
  const healthQuery = useApiQuery(['workflow-observability', 'health'], automationObservabilityApi.getDependencies)
  const anomaliesQuery = useApiQuery(['workflow-observability', 'anomalies'], automationObservabilityApi.getAnomalies)

  const isLoading = liveQuery.isLoading || healthQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Connecting to observability streams...</Text>
        </Space>
      </div>
    )
  }

  const live = (liveQuery.data as any)?.data || []
  const failures = (failuresQuery.data as any)?.data || []
  const health = (healthQuery.data as any)?.data || []
  const anomalies = (anomaliesQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-2">
          <Title level={3} className="!m-0">Automation Observability Center</Title>
          <Paragraph className="text-slate-500 max-w-3xl">
            Real-time monitoring and operational health for the entire automation cluster. Track traces, detect anomalies, and monitor dependency heartbeats.
          </Paragraph>
        </div>
        <Button 
          icon={<RefreshCw size={16}/>} 
          className="rounded-xl h-10 font-bold"
          onClick={() => { liveQuery.refetch(); healthQuery.refetch(); }}
        >
          Refresh Stream
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Live Executions" value={live.length} icon={<Activity size={20}/>} color="text-indigo-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Active Anomalies" value={anomalies.length} icon={<Radar size={20}/>} color="text-rose-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Health Status" value={health.every((h:any) => h.status === 'healthy') ? 'HEALTHY' : 'DEGRADED'} icon={<Heart size={20}/>} color={health.every((h:any) => h.status === 'healthy') ? 'text-emerald-600' : 'text-amber-600'} />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="System Latency" value="124ms" icon={<Clock size={20}/>} color="text-blue-600" />
        </Col>
      </Row>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'live',
            label: <Space><Activity size={16}/><span>Live Monitor</span></Space>,
            children: <LiveTable data={live} />
          },
          {
            key: 'failures',
            label: <Space><ShieldAlert size={16}/><span>Failure Logs</span></Space>,
            children: <FailureTable data={failures} />
          },
          {
            key: 'health',
            label: <Space><Zap size={16}/><span>Dependency Health</span></Space>,
            children: <HealthGrid data={health} />
          },
          {
            key: 'anomalies',
            label: <Space><AlertOctagon size={16}/><span>Anomalies</span></Space>,
            children: <AnomalyList data={anomalies} />
          }
        ]}
      />
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: string | number; icon: React.ReactNode; color: string }) {
  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{title}</Text>
          <div className={cn("text-2xl font-black", color)}>{value}</div>
        </div>
        <div className={cn("p-3 rounded-2xl bg-slate-50", color)}>{icon}</div>
      </div>
    </Card>
  )
}

function LiveTable({ data }: { data: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Workflow ID', dataIndex: 'workflow_id', key: 'wf', render: (v) => <Text className="font-mono text-xs">{v.slice(0,8)}</Text> },
    { title: 'Execution ID', dataIndex: 'execution_id', key: 'ex', render: (v) => <Text className="font-mono text-xs">{v.slice(0,8)}</Text> },
    { title: 'Node ID', dataIndex: 'node_id', key: 'node', render: (v) => v ? <Text className="font-mono text-[10px]">{v.slice(0,8)}</Text> : '—' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Badge status="processing" text={v.toUpperCase()} /> },
    { title: 'Duration', dataIndex: 'execution_time_ms', key: 'dur', render: (v) => `${v}ms` },
    { title: 'Started At', dataIndex: 'created_at', key: 'at', render: (v) => dayjs(v).fromNow() }
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No live executions detected." /> }} />
    </Card>
  )
}

function FailureTable({ data }: { data: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow_id', key: 'wf', render: (v) => <Text className="font-mono text-xs">{v.slice(0,8)}</Text> },
    { title: 'Error', dataIndex: 'error_message', key: 'err', render: (v) => <Text type="danger" className="text-xs">{v || 'Unknown error'}</Text> },
    { title: 'Failed At', dataIndex: 'created_at', key: 'at', render: (v) => dayjs(v).format('MMM DD, HH:mm:ss') }
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  )
}

function HealthGrid({ data }: { data: any[] }) {
  return (
    <Row gutter={[24, 24]}>
      {data.map((h) => (
        <Col xs={24} md={12} lg={6} key={h.id}>
          <Card className="rounded-3xl border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <Text strong className="text-xs uppercase text-slate-400">{h.dependency_name}</Text>
              <Tag color={h.status === 'healthy' ? 'green' : 'red'} className="m-0 rounded-full text-[9px] font-black">{h.status.toUpperCase()}</Tag>
            </div>
            <div className="flex items-center gap-2">
              <div className={cn("w-2 h-2 rounded-full", h.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500')} />
              <Text className="text-[10px] text-slate-500">Last check: {dayjs(h.last_checked_at).format('HH:mm:ss')}</Text>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function AnomalyList({ data }: { data: any[] }) {
  if (data.length === 0) return <Card className="rounded-[2rem] border-slate-200 shadow-sm"><Empty description="No system anomalies detected." /></Card>

  return (
    <div className="space-y-4">
      {data.map((a) => (
        <Alert
          key={a.id}
          type={a.severity === 'error' || a.severity === 'critical' ? 'error' : 'warning'}
          showIcon
          icon={<AlertCircle size={18} />}
          message={<Text strong>{humanize(a.anomaly_type)}</Text>}
          description={
            <div className="flex justify-between items-center">
              <Text className="text-sm">{a.description}</Text>
              <Tag className="rounded-xl font-bold">{a.status.toUpperCase()}</Tag>
            </div>
          }
          className="rounded-2xl border-none shadow-sm"
        />
      ))}
    </div>
  )
}

function humanize(value: string) {
  return value.replace(/_/g, ' ').toUpperCase()
}
