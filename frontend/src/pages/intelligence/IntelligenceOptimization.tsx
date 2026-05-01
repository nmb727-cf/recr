import {
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
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ArrowUpRight,
  CheckCircle,
  Lightbulb,
  ShieldCheck,
  TrendingUp,
  Zap,
} from 'lucide-react'
import { useState } from 'react'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function IntelligenceOptimization() {
  const overviewQuery = useApiQuery(['intelligence-optimization', 'overview'], intelligenceHubApi.getOptimizationOverview)
  const recommendationsQuery = useApiQuery(['intelligence-optimization', 'recommendations'], intelligenceHubApi.listOptimizationRecommendations)
  const policyTableQuery = useApiQuery(['intelligence-learning', 'policy-table'], intelligenceHubApi.getPolicyLearningTable)

  const applyMutation = useApiMutation(
    (id: string) => intelligenceHubApi.applyOptimizationRecommendation(id),
    {
      successMessage: 'Optimization recommendation applied successfully.',
      invalidateKeys: [['intelligence-optimization', 'overview'], ['intelligence-optimization', 'recommendations'], ['intelligence-hub', 'automation-policies']],
    }
  )

  const isLoading = overviewQuery.isLoading || recommendationsQuery.isLoading || policyTableQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Running optimization analysis...</Text>
        </Space>
      </div>
    )
  }

  const overview = (overviewQuery.data as any)?.data || {}
  const recommendations = (recommendationsQuery.data as any)?.data || []
  const policyTableData = (policyTableQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0">Optimization Engine</Title>
        <Paragraph className="text-slate-500 max-w-3xl">
          AI-driven tuning of your automation policies. The system analyzes success rates, failure patterns, and human overrides to suggest optimal configurations.
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col lg={16}>
          {/* 1. Optimization Recommendations */}
          <Card 
            title={<Space><Lightbulb className="text-amber-500" size={18}/><span>Optimization Recommendations</span></Space>}
            className="rounded-3xl border-slate-200 shadow-sm"
          >
            {recommendations.length > 0 ? (
              <div className="space-y-4">
                {recommendations.map((rec: any) => (
                  <RecommendationItem 
                    key={rec.id} 
                    recommendation={rec} 
                    onApply={() => applyMutation.mutate(rec.id)}
                    loading={applyMutation.isPending}
                  />
                ))}
              </div>
            ) : (
              <Empty description="All policies are currently optimized. No new recommendations." />
            )}
          </Card>
        </Col>
        <Col lg={8}>
          <div className="space-y-6">
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <Statistic 
                title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Pending Optimizations</Text>}
                value={overview.pending_count}
                prefix={<TrendingUp size={16} className="text-indigo-500" />}
              />
            </Card>
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <Statistic 
                title={<Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Total Improvements Applied</Text>}
                value={overview.applied_total}
                prefix={<CheckCircle size={16} className="text-emerald-500" />}
              />
            </Card>
          </div>
        </Col>
      </Row>

      {/* 2. Policy Performance Table */}
      <Card 
        title={<Space><ShieldCheck className="text-indigo-600" size={18}/><span>Policy Performance & Health</span></Space>}
        className="rounded-3xl border-slate-200 shadow-sm overflow-hidden"
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          rowKey="policy_id"
          columns={PERFORMANCE_COLUMNS}
          dataSource={policyTableData}
          pagination={false}
        />
      </Card>
    </div>
  )
}

function RecommendationItem({ recommendation, onApply, loading }: { recommendation: any, onApply: () => void, loading: boolean }) {
  return (
    <div className="p-5 rounded-2xl border border-indigo-100 bg-indigo-50/50 flex flex-col gap-3">
      <div className="flex justify-between items-start">
        <Space>
          <Zap size={18} className="text-indigo-600" />
          <Text strong className="text-indigo-900">
            {recommendation.suggestion_type.replace(/_/g, ' ')}
          </Text>
          <Tag color="blue" className="rounded-full text-[10px] font-black">{recommendation.recommendation_type.replace(/_/g, ' ').toUpperCase()}</Tag>
        </Space>
        <div className="text-right">
           <Text className="block text-[10px] uppercase font-black text-slate-400">Confidence</Text>
           <Text strong className="text-emerald-600">{Math.round(recommendation.confidence * 100)}%</Text>
        </div>
      </div>
      
      <Paragraph className="m-0 text-slate-700 text-sm">
        {recommendation.reason}
      </Paragraph>
      
      <div className="flex items-center justify-between mt-2 pt-3 border-t border-indigo-100">
        <Space size={24}>
           <div>
              <Text className="block text-[10px] uppercase font-black text-slate-400">Current</Text>
              <Text strong className="text-xs">{String(recommendation.current_value)}</Text>
           </div>
           <ArrowUpRight size={16} className="text-slate-300" />
           <div>
              <Text className="block text-[10px] uppercase font-black text-indigo-400">Recommended</Text>
              <Text strong className="text-xs text-indigo-700">{String(recommendation.recommended_value)}</Text>
           </div>
        </Space>
        <Button 
          type="primary" 
          size="small" 
          className="rounded-lg text-[10px] font-black uppercase bg-indigo-600"
          onClick={onApply}
          loading={loading}
        >
          Apply Optimization
        </Button>
      </div>
    </div>
  )
}

const PERFORMANCE_COLUMNS: ColumnsType<any> = [
  {
    title: 'Policy',
    key: 'policy',
    render: (_, record) => (
      <Text strong className="text-slate-800">{record.suggestion_type.replace(/_/g, ' ')}</Text>
    )
  },
  {
    title: 'Success Rate',
    dataIndex: 'success_rate',
    key: 'success',
    render: (v) => (
      <Space size={12}>
        <Progress percent={v} size="small" strokeColor={v > 90 ? '#10b981' : v > 70 ? '#f59e0b' : '#ef4444'} className="w-24" />
        <Text strong className="text-xs">{v}%</Text>
      </Space>
    )
  },
  {
    title: 'Failure Rate',
    dataIndex: 'failure_rate',
    key: 'failure',
    render: (v) => <Text className={cn("font-bold", v > 10 ? "text-rose-600" : "text-slate-400")}>{v}%</Text>
  },
  {
    title: 'Optimization Status',
    dataIndex: 'recommendation',
    key: 'rec',
    render: (v) => (
      <Tag color={v.includes('No recommendation') ? 'default' : 'orange'}>
        {v.includes('No recommendation') ? 'OPTIMIZED' : 'Tuning Required'}
      </Tag>
    )
  }
]
