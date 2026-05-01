import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Empty,
  List,
  Modal,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  AlertOctagon,
  Cpu,
  Database,
  FastForward,
  Heart,
  Info,
  Layers,
  Pause,
  Play,
  Radio,
  RefreshCw,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { automationOsApi } from '@/api/automationOs'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationOS() {
  const [activeTab, setActiveTab] = useState('runtime')

  const runtimeQuery = useApiQuery(['automation-os', 'runtime'], automationOsApi.getRuntimeState, { refetchInterval: 10000 })
  const enginesQuery = useApiQuery(['automation-os', 'engines'], automationOsApi.listEngines)
  const coverageQuery = useApiQuery(['automation-os', 'coverage'], automationOsApi.getBusinessCoverage)
  const eventsQuery = useApiQuery(['automation-os', 'events'], automationOsApi.listOperatingEvents)
  const insightsQuery = useApiQuery(['automation-os', 'insights'], automationOsApi.listOperatingInsights)

  const controlMutation = useApiMutation(
    (action: 'pause-all' | 'resume-all') => automationOsApi.globalControl(action),
    {
      successMessage: 'Global control command executed.',
      invalidateKeys: [['automation-os', 'runtime'], ['automation-os', 'engines']]
    }
  )

  const modeMutation = useApiMutation(
    (mode: string) => automationOsApi.setRuntimeMode(mode),
    {
      successMessage: 'Runtime orchestration mode updated.',
      invalidateKeys: [['automation-os', 'runtime']]
    }
  )

  const isLoading = runtimeQuery.isLoading || enginesQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500 font-medium uppercase tracking-widest text-[10px]">Initializing Automation Kernel...</Text>
        </Space>
      </div>
    )
  }

  const state = (runtimeQuery.data as any)?.data || {}
  const engines = (enginesQuery.data as any)?.data || []
  const coverage = (coverageQuery.data as any)?.data || []
  const events = (eventsQuery.data as any)?.data || []
  const insights = (insightsQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      {/* ══ Kernel Header & Global Controls ═════════════════════════════════ */}
      <div className="flex justify-between items-start bg-slate-900 p-8 rounded-[2.5rem] text-white shadow-2xl">
        <div className="flex gap-6 items-center">
          <div className="h-16 w-16 rounded-2xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/50">
            <Cpu size={32} />
          </div>
          <div>
            <Title level={2} className="!m-0 text-white tracking-tight font-black">Automation OS</Title>
            <Text className="text-indigo-300 text-[10px] font-black uppercase tracking-[0.2em] mt-1 block">Unified Enterprise Orchestration Layer</Text>
          </div>
        </div>

        <Space size={12}>
          <DropdownMenu 
            label="Runtime Mode" 
            value={state.orchestration_mode}
            options={[
              { label: 'Normal', value: 'normal' },
              { label: 'Safe Mode', value: 'safe-mode' },
              { label: 'Maintenance', value: 'maintenance-mode' },
              { label: 'Emergency Override', value: 'emergency-override' },
            ]}
            onSelect={(val) => modeMutation.mutate(val)}
            loading={modeMutation.isPending}
          />
          <Divider type="vertical" className="h-10 bg-slate-700" />
          <Button 
            icon={<Pause size={16}/>} 
            className="rounded-xl h-10 font-bold border-slate-700 bg-slate-800 text-white hover:bg-rose-600 transition-all"
            onClick={() => controlMutation.mutate('pause-all')}
            loading={controlMutation.isPending}
          >Pause All</Button>
          <Button 
            type="primary"
            icon={<Play size={16}/>} 
            className="rounded-xl h-10 font-bold bg-emerald-600 border-none shadow-lg shadow-emerald-500/20"
            onClick={() => controlMutation.mutate('resume-all')}
            loading={controlMutation.isPending}
          >Resume All</Button>
        </Space>
      </div>

      {/* ══ System Telemetry ════════════════════════════════════════════════ */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={4}>
          <MetricCard title="Kernel Status" value={(state.runtime_status ?? 'unknown').toUpperCase()} color={statusColor(state.runtime_status ?? 'unknown')} icon={<Heart size={20}/>} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <MetricCard title="Active Executions" value={state.active_execution_count} color="text-indigo-400" icon={<Activity size={20}/>} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <MetricCard title="Degraded Engines" value={state.degraded_engine_count} color={state.degraded_engine_count > 0 ? "text-rose-400" : "text-emerald-400"} icon={<AlertOctagon size={20}/>} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <MetricCard title="Workload Index" value="Optimal" color="text-blue-400" icon={<Layers size={20}/>} />
        </Col>
        <Col xs={24} lg={8}>
          <Card className="rounded-[2rem] border-slate-200 shadow-sm h-full" bodyStyle={{ padding: '20px' }}>
            <div className="flex justify-between items-center mb-4">
              <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Business Coverage</Text>
              <Text strong className="text-indigo-600">65%</Text>
            </div>
            <Progress percent={65} strokeColor="#6366f1" trailColor="#f1f5f9" strokeWidth={12} showInfo={false} />
            <Text className="text-[10px] text-slate-400 mt-3 block font-medium">35% Manual Gap Detected across 5 modules.</Text>
          </Card>
        </Col>
      </Row>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        className="automation-os-tabs"
        items={[
          {
            key: 'runtime',
            label: <Space><Radio size={16}/><span>Kernel Monitor</span></Space>,
            children: <KernelMonitor engines={engines} events={events} />
          },
          {
            key: 'policies',
            label: <Space><ShieldCheck size={16}/><span>Execution Policies</span></Space>,
            children: <PolicyGrid />
          },
          {
            key: 'coverage',
            label: <Space><Database size={16}/><span>Business Coverage</span></Space>,
            children: <CoverageMap coverage={coverage} insights={insights} />
          }
        ]}
      />
    </div>
  )
}

function MetricCard({ title, value, color, icon }: { title: string, value: string | number, color: string, icon: React.ReactNode }) {
  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm bg-white" bodyStyle={{ padding: '24px' }}>
      <div className="space-y-3">
        <div className={cn("p-2 rounded-xl bg-slate-50 w-fit", color)}>{icon}</div>
        <div>
          <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block">{title}</Text>
          <div className={cn("text-2xl font-black mt-1", color)}>{value}</div>
        </div>
      </div>
    </Card>
  )
}

function DropdownMenu({ label, value, options, onSelect, loading }: { label: string, value: string, options: any[], onSelect: (v: string) => void, loading?: boolean }) {
  return (
    <div className="flex flex-col">
      <Text className="text-[9px] font-black uppercase text-slate-500 tracking-[0.2em] mb-1.5 ml-1">{label}</Text>
      <Select 
        value={value} 
        onChange={onSelect}
        loading={loading}
        className="kernel-select min-w-[180px]"
        options={options}
      />
    </div>
  )
}

function KernelMonitor({ engines, events }: { engines: any[], events: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Engine', key: 'name', render: (_, record) => <Space><Text strong className="text-xs">{record.engine_name}</Text><Tag className="text-[9px] font-black border-none bg-slate-100 uppercase">{record.engine_type}</Tag></Space> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)} className="rounded-full px-3 text-[10px] font-black border-none uppercase">{v}</Tag> },
    { title: 'Priority', dataIndex: 'priority', key: 'prio', align: 'center', render: (v) => <Badge count={v} style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} /> },
    { title: 'Last Heartbeat', dataIndex: 'last_heartbeat_at', key: 'hb', render: (v) => v ? dayjs(v).format('HH:mm:ss') : <Text type="secondary" italic>No signal</Text> },
    { title: 'Actions', key: 'actions', render: () => <Button size="small" type="link">Manage</Button> }
  ]

  return (
    <Row gutter={[24, 24]}>
      <Col lg={16}>
        <Card title="Engine Registry Monitor" className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
          <Table columns={columns} dataSource={engines} rowKey="id" pagination={false} />
        </Card>
      </Col>
      <Col lg={8}>
        <Card title="Operating Events" className="rounded-[2.5rem] border-slate-200 shadow-sm h-full">
          <List
            dataSource={events}
            renderItem={(item: any) => (
              <List.Item className="px-0 border-b-slate-50">
                <List.Item.Meta
                  avatar={<div className={cn("p-2 rounded-xl bg-slate-50", severityColor(item.severity))}><Info size={16}/></div>}
                  title={<Text strong className="text-xs uppercase tracking-tight">{item.event_type}</Text>}
                  description={<Text className="text-[10px] text-slate-500">{item.message}</Text>}
                />
              </List.Item>
            )}
            locale={{ emptyText: <Empty description="No recent operating events." /> }}
          />
        </Card>
      </Col>
    </Row>
  )
}

function CoverageMap({ coverage, insights }: { coverage: any[], insights: any[] }) {
  return (
    <Row gutter={[24, 24]}>
      <Col lg={14}>
        <Card title="Module Automation Coverage" className="rounded-[2.5rem] border-slate-200 shadow-sm h-full">
          <div className="space-y-8 py-4">
            {coverage.map((c: any) => (
              <div key={c.module_scope} className="space-y-2">
                <div className="flex justify-between items-center px-1">
                  <Text strong className="text-xs uppercase tracking-widest">{c.module_scope}</Text>
                  <Text className="text-[10px] font-black text-indigo-500">{c.automation_coverage_percent}% COVERED</Text>
                </div>
                <Progress percent={c.automation_coverage_percent} strokeColor="#6366f1" trailColor="#f1f5f9" showInfo={false} size="small" />
              </div>
            ))}
          </div>
        </Card>
      </Col>
      <Col lg={10}>
        <Card title="Operating Insights" className="rounded-[2.5rem] border-slate-200 shadow-sm h-full">
          <div className="space-y-4">
            {insights.map((ins: any) => (
              <div key={ins.id} className="p-5 rounded-3xl bg-indigo-50/30 border border-indigo-100 flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <Tag color="indigo" className="m-0 rounded-full font-black text-[9px] uppercase">{ins.insight_type}</Tag>
                  <Tag color={ins.impact_level === 'high' ? 'volcano' : 'blue'} className="m-0 border-none text-[9px] font-black">{ins.impact_level.toUpperCase()} IMPACT</Tag>
                </div>
                <h4 className="text-sm font-black uppercase tracking-tight text-slate-900 m-0">{ins.title}</h4>
                <Paragraph className="text-xs text-slate-600 m-0 leading-relaxed">{ins.description}</Paragraph>
                <div className="p-3 bg-white rounded-2xl border border-indigo-100">
                  <Text className="text-[10px] font-black text-indigo-600 uppercase block mb-1">Recommendation</Text>
                  <Text className="text-xs">{ins.recommendation}</Text>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </Col>
    </Row>
  )
}

function PolicyGrid() {
  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm">
      <Empty description="No custom execution policies defined. Default kernel policies active." className="py-12" />
    </Card>
  )
}

function statusColor(status: string) {
  const s = status.toLowerCase()
  if (s === 'healthy' || s === 'active') return 'success'
  if (s === 'degraded' || s === 'paused') return 'warning'
  if (s === 'failed' || s === 'emergency_mode') return 'error'
  return 'default'
}

function severityColor(severity: string) {
  const s = severity.toLowerCase()
  if (s === 'info') return 'text-blue-500'
  if (s === 'warning') return 'text-amber-500'
  if (s === 'error' || s === 'critical') return 'text-rose-500'
  return 'text-slate-400'
}
