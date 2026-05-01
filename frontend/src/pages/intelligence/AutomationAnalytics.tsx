import {
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Drawer,
  Empty,
  List,
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
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import {
  Activity,
  BarChart2,
  CheckCircle,
  Clock,
  ExternalLink,
  Info,
  Layers,
  MousePointer2,
  Percent,
  PieChart,
  ShieldAlert,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart as RePieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography
const { RangePicker } = DatePicker

type AnalyticsSubSection = 'overview' | 'workflows' | 'triggers' | 'failures' | 'impact' | 'adoption'

export default function AutomationAnalytics() {
  const [activeTab, setActiveTab] = useState<AnalyticsSubSection>('overview')
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ])

  // Queries
  const overviewQuery = useApiQuery(
    ['automation-analytics', 'overview', dateRange[0].toISOString(), dateRange[1].toISOString()],
    () => intelligenceHubApi.getWorkflowAnalyticsOverview({
      date_from: dateRange[0].toISOString(),
      date_to: dateRange[1].toISOString(),
    })
  )

  const workflowsQuery = useApiQuery(
    ['automation-analytics', 'workflows'],
    () => intelligenceHubApi.listWorkflowAnalytics()
  )

  const detailQuery = useApiQuery(
    ['automation-analytics', 'detail', selectedWorkflowId],
    () => intelligenceHubApi.getWorkflowDetailAnalytics(selectedWorkflowId!),
    { enabled: !!selectedWorkflowId }
  )

  const renderContent = () => {
    const ovData = (overviewQuery.data as any)?.data
    const wfData = (workflowsQuery.data as any)?.data

    switch (activeTab) {
      case 'overview':
        return <OverviewTab data={ovData} loading={overviewQuery.isLoading} />
      case 'workflows':
        return <WorkflowsTab data={wfData || []} loading={workflowsQuery.isLoading} onSelect={setSelectedWorkflowId} />
      case 'triggers':
        return <TriggersTab />
      case 'failures':
        return <FailuresTab />
      case 'impact':
        return <ImpactTab />
      case 'adoption':
        return <AdoptionTab />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
        <div>
          <Title level={3} className="!m-0">Automation Analytics</Title>
          <Text className="text-slate-500">Measure ROI, observability, and performance of your intelligent workflows.</Text>
        </div>
        <RangePicker 
          value={dateRange} 
          onChange={(vals) => vals && setDateRange([vals[0]!, vals[1]!])} 
          className="rounded-xl h-10"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {(['overview', 'workflows', 'triggers', 'failures', 'impact', 'adoption'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-6 py-2 rounded-full text-xs font-black uppercase tracking-widest transition-all",
              activeTab === tab 
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-200" 
                : "bg-white text-slate-500 border border-slate-200 hover:border-slate-300"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {renderContent()}

      <WorkflowDetailDrawer 
        id={selectedWorkflowId} 
        onClose={() => setSelectedWorkflowId(null)} 
        data={(detailQuery.data as any)?.data}
        loading={detailQuery.isLoading}
      />
    </div>
  )
}

function OverviewTab({ data, loading }: { data: any; loading: boolean }) {
  if (loading) return <LoadingState />
  if (!data) return <Empty />

  const metrics = data.execution_metrics
  const impact = data.impact_metrics

  return (
    <div className="space-y-8">
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Total Executions" value={metrics.total} icon={<Zap size={20}/>} color="text-indigo-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Success Rate" value={`${Math.round(metrics.success_rate)}%`} icon={<CheckCircle size={20}/>} color="text-emerald-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Hours Saved" value={Math.round(impact.hours_saved || 0)} icon={<Clock size={20}/>} color="text-amber-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Active Workflows" value={data.active_workflows} icon={<Activity size={20}/>} color="text-blue-600" />
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col lg={16}>
          <Card title="Execution Trend" className="rounded-3xl border-slate-200 shadow-sm overflow-hidden">
             <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                   <AreaChart data={DUMMY_TREND}>
                      <defs>
                        <linearGradient id="colorEx" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8'}} />
                      <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8'}} />
                      <Tooltip />
                      <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorEx)" />
                   </AreaChart>
                </ResponsiveContainer>
             </div>
          </Card>
        </Col>
        <Col lg={8}>
          <Card title="Impact Distribution" className="rounded-3xl border-slate-200 shadow-sm overflow-hidden">
             <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                   <RePieChart>
                      <Pie
                        data={[
                          { name: 'Reminders', value: impact.reminders_sent || 10 },
                          { name: 'Stages', value: impact.stage_movements_automated || 5 },
                          { name: 'Assignments', value: 8 },
                        ]}
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {COLORS.map((color, index) => <Cell key={`cell-${index}`} fill={color} />)}
                      </Pie>
                      <Tooltip />
                      <Legend verticalAlign="bottom" height={36}/>
                   </RePieChart>
                </ResponsiveContainer>
             </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

function WorkflowsTab({ data, loading, onSelect }: { data: any[]; loading: boolean; onSelect: (id: string) => void }) {
  const columns: ColumnsType<any> = [
    { title: 'Workflow Name', dataIndex: 'name', key: 'name', render: (v) => <Text strong className="text-slate-800">{v}</Text> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={v === 'active' ? 'green' : 'default'} className="rounded-full uppercase text-[10px] px-3 font-bold">{v}</Tag> },
    { title: 'Executions', dataIndex: 'executions', key: 'executions', sorter: (a, b) => a.executions - b.executions },
    { title: 'Success Rate', dataIndex: 'success_rate', key: 'sr', render: (v) => <Progress percent={Math.round(v)} size="small" strokeColor={v > 90 ? '#10b981' : v > 70 ? '#f59e0b' : '#ef4444'} /> },
    { title: 'ROI (Hours)', dataIndex: 'impact_hours', key: 'roi', render: (v) => <Text className="font-mono font-bold text-indigo-600">{v}h</Text> },
    { title: 'Action', key: 'action', render: (_, record) => <Button size="small" icon={<ExternalLink size={12}/>} onClick={() => onSelect(record.id)}>Details</Button> },
  ]

  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
       <Table rowKey="id" columns={columns} dataSource={data} loading={loading} pagination={{ pageSize: 10 }} />
    </Card>
  )
}

function TriggersTab() {
  const { data, isLoading } = useApiQuery(['automation-analytics', 'triggers'], () => intelligenceHubApi.getWorkflowAnalyticsTriggers())
  const items = (data as any)?.data || []

  return (
    <Row gutter={[24, 24]}>
      <Col lg={12}>
        <Card title="Top Trigger Events" className="rounded-3xl border-slate-200 shadow-sm">
           <List
             dataSource={items}
             renderItem={(item: any) => (
               <List.Item className="border-b-slate-100">
                  <div className="flex items-center justify-between w-full">
                     <Space>
                        <div className="p-2 rounded-xl bg-orange-50 text-orange-600"><Zap size={16}/></div>
                        <Text strong className="text-slate-700">{item.trigger_event}</Text>
                     </Space>
                     <div className="text-right">
                        <Text className="block font-black text-indigo-600">{item.total_count}</Text>
                        <Text className="text-[10px] text-slate-400 uppercase font-black">Times Fired</Text>
                     </div>
                  </div>
               </List.Item>
             )}
           />
        </Card>
      </Col>
      <Col lg={12}>
        <Card title="Trigger to Execution Conversion" className="rounded-3xl border-slate-200 shadow-sm">
           <div className="space-y-6 py-4">
              {items.slice(0, 4).map((item: any) => (
                <div key={item.trigger_event}>
                   <div className="flex justify-between mb-2">
                      <Text className="text-xs font-bold text-slate-500">{item.trigger_event}</Text>
                      <Text className="text-xs font-black text-indigo-600">{Math.round((item.execution_count / item.total_count) * 100)}% Conversion</Text>
                   </div>
                   <Progress percent={Math.round((item.execution_count / item.total_count) * 100)} strokeColor="#6366f1" trailColor="#f1f5f9" strokeWidth={12} />
                </div>
              ))}
           </div>
        </Card>
      </Col>
    </Row>
  )
}

function FailuresTab() {
  const { data, isLoading } = useApiQuery(['automation-analytics', 'failures'], () => intelligenceHubApi.getWorkflowAnalyticsFailures())
  const items = (data as any)?.data || []

  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow_name', key: 'wf' },
    { title: 'Failure Type', dataIndex: 'failure_type', key: 'type', render: (v) => <Tag color="red">{v}</Tag> },
    { title: 'Insight', dataIndex: 'title', key: 'title' },
    { title: 'Occurrences', dataIndex: 'occurrence_count', key: 'count', render: (v) => <Badge count={v} color="#ef4444" /> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag className="rounded-full">{v.toUpperCase()}</Tag> },
  ]

  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
       <Table rowKey="id" columns={columns} dataSource={items} loading={isLoading} />
    </Card>
  )
}

function ImpactTab() {
  const { data } = useApiQuery(['automation-analytics', 'impact'], () => intelligenceHubApi.getWorkflowAnalyticsImpact())
  const items = (data as any)?.data || []

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
       {items.map((item: any) => (
         <Card key={item.impact_type} className="rounded-3xl border-slate-200 shadow-sm hover:border-indigo-200 transition-colors">
            <Statistic 
              title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{item.impact_type.replace(/_/g, ' ')}</Text>} 
              value={item.total_value} 
              prefix={<div className="p-3 rounded-2xl bg-indigo-50 text-indigo-600 mr-3"><Target size={20}/></div>}
            />
         </Card>
       ))}
    </div>
  )
}

function AdoptionTab() {
  const { data } = useApiQuery(['automation-analytics', 'adoption'], () => intelligenceHubApi.getWorkflowAnalyticsAdoption())
  const stats = (data as any)?.data || {}

  return (
    <Row gutter={[24, 24]}>
      <Col lg={8}>
        <Card className="rounded-3xl border-slate-200 shadow-sm text-center py-8">
           <Progress type="dashboard" percent={Math.round(stats.adoption_rate || 0)} strokeColor="#6366f1" width={160} strokeWidth={10} />
           <Title level={4} className="mt-4 !mb-0">Adoption Rate</Title>
           <Text className="text-slate-400">Percentage of active workflows</Text>
        </Card>
      </Col>
      <Col lg={16}>
        <div className="grid grid-cols-2 gap-6 h-full">
           <Card className="rounded-3xl border-slate-200 shadow-sm flex items-center">
              <Statistic title="Total Workflows" value={stats.total_workflows} prefix={<Layers className="text-slate-400 mr-2" size={20}/>} />
           </Card>
           <Card className="rounded-3xl border-slate-200 shadow-sm flex items-center">
              <Statistic title="Active Now" value={stats.active_workflows} valueStyle={{color: '#10b981'}} prefix={<Zap className="text-emerald-500 mr-2" size={20}/>} />
           </Card>
        </div>
      </Col>
    </Row>
  )
}

function WorkflowDetailDrawer({ id, onClose, data, loading }: { id: string | null; onClose: () => void; data: any; loading: boolean }) {
  return (
    <Drawer
      title={<div className="flex items-center gap-2"><BarChart2 size={18} className="text-indigo-600"/> Workflow Observability Detail</div>}
      width={640}
      onClose={onClose}
      open={!!id}
      className="rounded-l-[2.5rem]"
    >
      {loading ? <LoadingState /> : data ? (
        <div className="space-y-8">
           <div className="p-6 rounded-3xl bg-slate-50 border border-slate-100">
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Workflow Detail</Text>
              <Title level={4} className="!m-0 mt-1">{data.name}</Title>
              <Text className="text-[10px] font-mono text-slate-400">{data.workflow_id}</Text>
           </div>

           <div className="space-y-4">
              <Text className="text-xs font-black uppercase text-slate-400 tracking-widest">Execution Trend (30 Days)</Text>
              <div className="h-[200px] w-full">
                 <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.trends}>
                       <XAxis dataKey="date" hide />
                       <Tooltip />
                       <Area type="monotone" dataKey="count" stroke="#6366f1" fill="#e0e7ff" />
                    </AreaChart>
                 </ResponsiveContainer>
              </div>
           </div>

           <div className="grid grid-cols-2 gap-4">
              <Card size="small" title="Trigger Efficiency" className="rounded-2xl">
                 {(data.triggers || []).map((t: any) => (
                   <div key={t.event} className="flex justify-between py-1">
                      <Text className="text-xs">{t.event}</Text>
                      <Text strong className="text-xs">{t.count}</Text>
                   </div>
                 ))}
              </Card>
              <Card size="small" title="Impact Summary" className="rounded-2xl">
                 {(data.impacts || []).map((i: any) => (
                   <div key={i.type} className="flex justify-between py-1">
                      <Text className="text-xs capitalize">{i.type.replace(/_/g, ' ')}</Text>
                      <Text strong className="text-xs text-emerald-600">{i.value}{i.unit === 'hours' ? 'h' : ''}</Text>
                   </div>
                 ))}
              </Card>
           </div>

           <div className="space-y-4">
              <Text className="text-xs font-black uppercase text-slate-400 tracking-widest">Failure Insights</Text>
              {data.failure_insights && data.failure_insights.length > 0 ? data.failure_insights.map((fi: any) => (
                <div key={fi.type} className="p-4 rounded-2xl bg-rose-50 border border-rose-100 flex items-start gap-4">
                   <ShieldAlert size={18} className="text-rose-500 mt-1" />
                   <div>
                      <Text strong className="text-rose-700 block">{fi.title}</Text>
                      <Text className="text-[10px] text-rose-600">Occurred {fi.count} times recently.</Text>
                   </div>
                </div>
              )) : <Empty description="No failure patterns detected." />}
           </div>
        </div>
      ) : <Empty />}
    </Drawer>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: React.ReactNode; icon: React.ReactNode; color: string }) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</Text>
          <div className={cn("text-2xl font-black mt-1", color)}>{value}</div>
        </div>
        <div className={cn("p-3 rounded-2xl bg-slate-50", color)}>{icon}</div>
      </div>
    </Card>
  )
}

function LoadingState() {
  return <div className="p-20 text-center"><Spin size="large" /><br/><Text className="mt-4 block text-slate-400">Computing analytics layer...</Text></div>
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#3b82f6', '#ec4899', '#8b5cf6']
const DUMMY_TREND = Array.from({length: 30}).map((_, i) => ({
  date: dayjs().subtract(30-i, 'days').format('MMM DD'),
  count: Math.floor(Math.random() * 50) + 10,
  success: Math.floor(Math.random() * 45) + 5,
}))
