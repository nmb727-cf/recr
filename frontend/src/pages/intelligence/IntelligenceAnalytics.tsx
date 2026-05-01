import {
  Card,
  Col,
  Divider,
  Empty,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  BarChart2,
  CheckCircle,
  Clock,
  PieChart,
  ShieldAlert,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react'
import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

export default function IntelligenceAnalytics() {
  const [days, setDays] = useState(30)

  const overviewQuery = useApiQuery(
    ['intelligence-analytics', 'overview', days],
    () => intelligenceHubApi.getAnalyticsOverview({ days }),
    { refetchOnWindowFocus: false }
  )

  const suggestionsQuery = useApiQuery(
    ['intelligence-analytics', 'suggestions', days],
    () => intelligenceHubApi.getAnalyticsSuggestions({ days }),
    { refetchOnWindowFocus: false }
  )

  const policiesQuery = useApiQuery(
    ['intelligence-analytics', 'policies'],
    () => intelligenceHubApi.getAnalyticsPolicies(),
    { refetchOnWindowFocus: false }
  )

  const executionsQuery = useApiQuery(
    ['intelligence-analytics', 'executions', days],
    () => intelligenceHubApi.getAnalyticsExecutions({ days }),
    { refetchOnWindowFocus: false }
  )

  const isLoading = overviewQuery.isLoading || suggestionsQuery.isLoading || policiesQuery.isLoading || executionsQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Loading intelligence analytics...</Text>
        </Space>
      </div>
    )
  }

  const overview = (overviewQuery.data as any)?.data || {}
  const suggestionData = (suggestionsQuery.data as any)?.data || {}
  const policiesData = (policiesQuery.data as any)?.data || {}
  const executionsData = (executionsQuery.data as any)?.data || {}

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <Title level={3} className="!m-0">Intelligence Analytics</Title>
          <Text className="text-slate-500">Performance and effectiveness of AI automation and intelligence policies.</Text>
        </div>
        <Select
          value={days}
          onChange={setDays}
          className="w-32"
          options={[
            { label: 'Last 7 Days', value: 7 },
            { label: 'Last 30 Days', value: 30 },
            { label: 'Last 90 Days', value: 90 },
          ]}
        />
      </div>

      {/* 1. Overview Cards */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Total Suggestions"
            value={overview.suggestion_metrics?.suggestions_created || 0}
            icon={<Target size={20} />}
            color="text-indigo-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Auto Approved"
            value={overview.suggestion_metrics?.suggestions_approved || 0}
            icon={<CheckCircle size={20} />}
            color="text-emerald-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Auto Applied"
            value={overview.suggestion_metrics?.suggestions_applied || 0}
            icon={<Zap size={20} />}
            color="text-amber-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Failures"
            value={overview.suggestion_metrics?.suggestions_failed || 0}
            icon={<ShieldAlert size={20} />}
            color="text-rose-600"
          />
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 2. Suggestion Lifecycle Chart */}
        <Col lg={14}>
          <Card title="Suggestion Lifecycle" className="rounded-3xl border-slate-200 shadow-sm overflow-hidden">
            <div className="h-[350px] w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formatLifecycleData(overview.suggestion_metrics)}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <Tooltip
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {formatLifecycleData(overview.suggestion_metrics).map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={LIFECYCLE_COLORS[entry.name] || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        {/* 4. Execution Health Panel */}
        <Col lg={10}>
          <Card title="Execution Health" className="rounded-3xl border-slate-200 shadow-sm h-full">
            <div className="space-y-8 py-4">
              <HealthMetric
                label="Overall Success Rate"
                value={overview.execution_metrics?.success_rate || 0}
                color="#10b981"
              />
              <div className="grid grid-cols-2 gap-8">
                <Statistic
                  title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Failure Rate</Text>}
                  value={100 - (overview.execution_metrics?.success_rate || 0)}
                  precision={1}
                  suffix="%"
                  valueStyle={{ color: '#ef4444', fontWeight: 900 }}
                />
                <Statistic
                  title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Retry Count</Text>}
                  value={overview.execution_metrics?.retry_count || 0}
                  valueStyle={{ color: '#f59e0b', fontWeight: 900 }}
                />
              </div>
              <Divider className="my-0" />
              <div className="space-y-4">
                <Text className="text-xs font-bold text-slate-500 uppercase tracking-wider">By Execution Type</Text>
                <div className="flex justify-between items-center">
                  <Space><div className="w-3 h-3 rounded-full bg-indigo-500" /><Text className="text-sm">AI Executions</Text></Space>
                  <Text strong>{executionsData.ai?.success_rate || 0}% Success</Text>
                </div>
                <div className="flex justify-between items-center">
                  <Space><div className="w-3 h-3 rounded-full bg-blue-500" /><Text className="text-sm">Automation Runs</Text></Space>
                  <Text strong>{executionsData.automation?.success_rate || 0}% Success</Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 3. Policy Effectiveness Table */}
      <Card title="Policy Effectiveness" className="rounded-3xl border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <Table
          rowKey="id"
          columns={POLICY_COLUMNS}
          dataSource={policiesData.policies || []}
          pagination={false}
          locale={{ emptyText: <Empty description="No automation policies configured." /> }}
        />
      </Card>
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: number | string; icon: any; color: string }) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">{title}</Text>
          <div className={cn('text-3xl font-black', color)}>{value}</div>
        </div>
        <div className={cn('p-4 rounded-2xl bg-slate-50', color)}>{icon}</div>
      </div>
    </Card>
  )
}

function HealthMetric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-end">
        <Text className="text-sm font-bold text-slate-700">{label}</Text>
        <Text className="text-2xl font-black" style={{ color }}>{Math.round(value)}%</Text>
      </div>
      <Progress
        percent={value}
        strokeColor={color}
        trailColor="#f1f5f9"
        strokeWidth={12}
        showInfo={false}
        className="m-0"
      />
    </div>
  )
}

const POLICY_COLUMNS: ColumnsType<any> = [
  {
    title: 'Policy',
    key: 'policy',
    render: (_, record) => (
      <Space direction="vertical" size={0}>
        <Text strong className="text-slate-800">{record.suggestion_type.replace(/_/g, ' ')}</Text>
        <Text type="secondary" className="text-[10px] uppercase tracking-tighter">{record.module_scope}</Text>
      </Space>
    ),
  },
  {
    title: 'Triggered',
    dataIndex: 'policy_trigger_count',
    key: 'triggered',
    align: 'center',
    render: (v) => <Text className="font-mono font-bold">{v}</Text>,
  },
  {
    title: 'Auto Approved',
    dataIndex: 'auto_approve_count',
    key: 'approved',
    align: 'center',
    render: (v) => <Text className="font-mono font-bold text-emerald-600">{v}</Text>,
  },
  {
    title: 'Auto Applied',
    dataIndex: 'auto_apply_count',
    key: 'applied',
    align: 'center',
    render: (v) => <Text className="font-mono font-bold text-amber-600">{v}</Text>,
  },
  {
    title: 'Failures',
    dataIndex: 'policy_failure_count',
    key: 'failures',
    align: 'center',
    render: (v) => <Text className={cn('font-mono font-bold', v > 0 ? 'text-rose-600' : 'text-slate-300')}>{v}</Text>,
  },
  {
    title: 'Success Rate',
    dataIndex: 'success_rate',
    key: 'rate',
    render: (v) => (
      <Space size={12}>
        <Progress
          percent={v}
          size="small"
          showInfo={false}
          strokeColor={v > 90 ? '#10b981' : v > 70 ? '#f59e0b' : '#ef4444'}
          className="w-24"
        />
        <Text strong className="text-xs">{v}%</Text>
      </Space>
    ),
  },
]

const LIFECYCLE_COLORS: Record<string, string> = {
  'Created': '#6366f1',
  'Approved': '#10b981',
  'Applied': '#f59e0b',
  'Failed': '#ef4444',
}

function formatLifecycleData(metrics: any) {
  if (!metrics) return []
  return [
    { name: 'Created', value: metrics.suggestions_created },
    { name: 'Approved', value: metrics.suggestions_approved },
    { name: 'Applied', value: metrics.suggestions_applied },
    { name: 'Failed', value: metrics.suggestions_failed },
  ]
}
