import {
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle,
  Lightbulb,
  ShieldAlert,
  Zap,
} from 'lucide-react'
import dayjs from 'dayjs'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function IntelligenceLearning() {
  const overviewQuery = useApiQuery(['intelligence-learning', 'overview'], intelligenceHubApi.getLearningOverview)
  const recommendationsQuery = useApiQuery(['intelligence-learning', 'recommendations'], intelligenceHubApi.getLearningRecommendations)
  const signalsQuery = useApiQuery(['intelligence-learning', 'signals'], () => intelligenceHubApi.listLearningSignals())
  const policyTableQuery = useApiQuery(['intelligence-learning', 'policy-table'], intelligenceHubApi.getPolicyLearningTable)

  const isLoading = overviewQuery.isLoading || recommendationsQuery.isLoading || signalsQuery.isLoading || policyTableQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Initializing automation learning engine...</Text>
        </Space>
      </div>
    )
  }

  const overview = (overviewQuery.data as any)?.data || {}
  const recommendations = (recommendationsQuery.data as any)?.data || []
  const signals = (signalsQuery.data as any)?.data || []
  const policyTableData = (policyTableQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0">Automation Learning Engine</Title>
        <Paragraph className="text-slate-500 max-w-3xl">
          The system continuously monitors automation outcomes and provides proactive recommendations to optimize your intelligence policies based on real-world performance.
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col lg={16}>
          {/* 1. Learning Recommendations */}
          <Card 
            title={<Space><Lightbulb className="text-amber-500" size={18}/><span>Learning Recommendations</span></Space>}
            className="rounded-3xl border-slate-200 shadow-sm"
          >
            {recommendations.length > 0 ? (
              <div className="space-y-4">
                {recommendations.map((rec: any) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            ) : (
              <Empty description="No optimization recommendations yet. Collecting signals..." />
            )}
          </Card>
        </Col>
        <Col lg={8}>
          <div className="space-y-6">
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <Statistic 
                title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Total Signals (30d)</Text>}
                value={overview.total_signals}
                prefix={<Activity size={16} className="text-indigo-500" />}
              />
            </Card>
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="space-y-4">
                <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block">System Health</Text>
                <div className="space-y-2">
                   <div className="flex justify-between items-center">
                      <Text className="text-xs">Avg Success Rate</Text>
                      <Text strong className="text-emerald-600">{Math.round(overview.avg_success_rate)}%</Text>
                   </div>
                   <Progress percent={overview.avg_success_rate} size="small" strokeColor="#10b981" showInfo={false} />
                </div>
                <div className="space-y-2">
                   <div className="flex justify-between items-center">
                      <Text className="text-xs">Avg Failure Rate</Text>
                      <Text strong className="text-rose-600">{Math.round(overview.avg_failure_rate)}%</Text>
                   </div>
                   <Progress percent={overview.avg_failure_rate} size="small" strokeColor="#ef4444" showInfo={false} />
                </div>
              </div>
            </Card>
          </div>
        </Col>
      </Row>

      {/* 2. Policy Learning Table */}
      <Card 
        title={<Space><Brain className="text-indigo-600" size={18}/><span>Policy Learning Performance</span></Space>}
        className="rounded-3xl border-slate-200 shadow-sm overflow-hidden"
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          rowKey="policy_id"
          columns={POLICY_COLUMNS}
          dataSource={policyTableData}
          pagination={false}
        />
      </Card>

      {/* 3. Learning Signals */}
      <Card 
        title={<Space><Activity className="text-slate-400" size={18}/><span>Recent Learning Signals</span></Space>}
        className="rounded-3xl border-slate-200 shadow-sm overflow-hidden"
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          rowKey="id"
          columns={SIGNAL_COLUMNS}
          dataSource={signals}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

function RecommendationCard({ recommendation }: { recommendation: any }) {
  const isRisk = recommendation.recommendation.includes('disabling')
  
  return (
    <div className={cn(
      "p-5 rounded-2xl border flex flex-col gap-3",
      isRisk ? "bg-rose-50 border-rose-100" : "bg-indigo-50 border-indigo-100"
    )}>
      <div className="flex justify-between items-start">
        <Space>
          {isRisk ? <ShieldAlert size={20} className="text-rose-600" /> : <Zap size={20} className="text-indigo-600" />}
          <Text strong className={isRisk ? "text-rose-900" : "text-indigo-900"}>
            {recommendation.suggestion_type.replace(/_/g, ' ')}
          </Text>
        </Space>
        <Tag color={isRisk ? "red" : "blue"} className="rounded-full uppercase text-[10px] font-black tracking-widest">
          {isRisk ? "Critical Action" : "Optimization"}
        </Tag>
      </div>
      
      <Paragraph className={cn("m-0", isRisk ? "text-rose-700" : "text-indigo-700")}>
        {recommendation.recommendation}
      </Paragraph>
      
      <div className="flex items-center gap-6 mt-1">
        <div>
          <Text className="block text-[10px] uppercase font-black text-slate-400 tracking-tighter">Success Rate</Text>
          <Text strong className={recommendation.success_rate > 90 ? "text-emerald-600" : "text-rose-600"}>
            {recommendation.success_rate}%
          </Text>
        </div>
        <div className="h-8 w-px bg-slate-200" />
        <div>
          <Text className="block text-[10px] uppercase font-black text-slate-400 tracking-tighter">Override Rate</Text>
          <Text strong>{recommendation.override_rate}%</Text>
        </div>
        <div className="flex-1" />
        <Button 
          type="primary" 
          size="small" 
          className={cn("rounded-lg text-[10px] font-black uppercase", isRisk ? "bg-rose-600" : "bg-indigo-600")}
          icon={<CheckCircle size={14}/>}
        >
          Review & Apply
        </Button>
      </div>
    </div>
  )
}

const POLICY_COLUMNS: ColumnsType<any> = [
  {
    title: 'Policy / Suggestion Type',
    key: 'policy',
    render: (_, record) => (
      <Text strong className="text-slate-800">{record.suggestion_type.replace(/_/g, ' ')}</Text>
    )
  },
  {
    title: 'Success Rate',
    dataIndex: 'success_rate',
    key: 'success',
    render: (v) => <Progress percent={v} size="small" strokeColor={v > 90 ? '#10b981' : v > 70 ? '#f59e0b' : '#ef4444'} />
  },
  {
    title: 'Failure Rate',
    dataIndex: 'failure_rate',
    key: 'failure',
    render: (v) => <Text className={cn("font-bold", v > 10 ? "text-rose-600" : "text-slate-400")}>{v}%</Text>
  },
  {
    title: 'System Recommendation',
    dataIndex: 'recommendation',
    key: 'rec',
    render: (v) => (
      <Space>
        <div className={cn("w-2 h-2 rounded-full", v.includes('No recommendation') ? "bg-slate-300" : "bg-indigo-500")} />
        <Text italic={v.includes('No recommendation')} className={v.includes('No recommendation') ? "text-slate-400" : "text-slate-700"}>
          {v}
        </Text>
      </Space>
    )
  }
]

const SIGNAL_COLUMNS: ColumnsType<any> = [
  {
    title: 'Timestamp',
    dataIndex: 'created_at',
    key: 'time',
    render: (v) => dayjs(v).format('MMM DD, HH:mm')
  },
  {
    title: 'Outcome',
    dataIndex: 'outcome_type',
    key: 'type',
    render: (v) => (
      <Tag color={v === 'success' || v === 'applied' || v === 'approved' ? 'green' : v === 'failure' || v === 'rejected' ? 'red' : 'blue'}>
        {v.toUpperCase()}
      </Tag>
    )
  },
  {
    title: 'Suggestion Type',
    dataIndex: 'suggestion_type',
    key: 'stype',
    render: (v) => <Text className="text-xs font-medium">{v.replace(/_/g, ' ')}</Text>
  },
  {
    title: 'Confidence',
    dataIndex: 'confidence_score',
    key: 'conf',
    render: (v) => <Text className="font-mono text-xs">{Math.round(v * 100)}%</Text>
  },
  {
    title: 'User Action',
    dataIndex: 'user_action',
    key: 'user',
    render: (v) => v || <Text className="text-slate-300">System</Text>
  }
]
