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
  List,
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
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  ArrowRight,
  Bot,
  Box,
  Check,
  Copy,
  Globe,
  Lightbulb,
  Lock,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  TrendingUp,
  XCircle,
  Zap,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell as RechartsCell,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useNavigate, useParams } from 'react-router-dom'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'
import IntelligenceAnalytics from './IntelligenceAnalytics'
import IntelligenceLearning from './IntelligenceLearning'
import IntelligenceGovernance from './IntelligenceGovernance'
import AutomationLibrary from './AutomationLibrary'
import IntelligenceOptimization from './IntelligenceOptimization'
import AutomationChangeImpact from './AutomationChangeImpact'
import AutomationObservability from './AutomationObservability'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

type IntelligenceSection =
  | 'suggestions'
  | 'automation-intelligence'
  | 'automation-insights-dashboard'
  | 'prompts'
  | 'analytics'
  | 'learning'
  | 'optimization'
  | 'governance'
  | 'library'
  | 'change-impact'
  | 'observability'
  | 'settings'
type AnyRecord = Record<string, any>

const SECTION_ITEMS: Array<{ key: IntelligenceSection; label: string }> = [
  { key: 'suggestions', label: 'Human Review' },
  { key: 'automation-intelligence', label: 'AI Suggestions' },
  { key: 'automation-insights-dashboard', label: 'AI Insights Dashboard' },
  { key: 'change-impact', label: 'Change Impact' },
  { key: 'observability', label: 'Observability' },
  { key: 'prompts', label: 'AI Prompts' },
  { key: 'analytics', label: 'Intelligence Analytics' },
  { key: 'learning', label: 'Learning Engine' },
  { key: 'optimization', label: 'Optimization' },
  { key: 'governance', label: 'AI Governance' },
  { key: 'library', label: 'Enterprise Library' },
  { key: 'settings', label: 'Settings' },
]

function normalizeSection(section?: string): IntelligenceSection {
  const valid = [
    'suggestions', 'automation-intelligence', 'automation-insights-dashboard', 
    'prompts', 'analytics', 'learning', 'optimization', 'governance', 
    'library', 'change-impact', 'observability', 'settings'
  ]
  if (valid.includes(section || '')) {
    return section as IntelligenceSection
  }
  return 'suggestions'
}

function formatDateTime(value: unknown) {
  if (!value) return 'Not available'
  const parsed = dayjs(String(value))
  return parsed.isValid() ? parsed.format('DD MMM YYYY, HH:mm') : String(value)
}

function humanize(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Not set'
  return String(value).replace(/_/g, ' ')
}

function shortId(value: unknown) {
  if (!value) return 'n/a'
  const stringValue = String(value)
  return stringValue.length > 12 ? `${stringValue.slice(0, 8)}…` : stringValue
}

function prettyJson(value: unknown) {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

function statusColor(value: unknown) {
  const normalized = String(value ?? '').toLowerCase()
  if (/completed|approved|applied|healthy|active|resolved|converted|valid/.test(normalized)) return 'green'
  if (/queued|pending|review|warning|retrying|scheduled|testing|partial/.test(normalized)) return 'gold'
  if (/failed|rejected|disabled|cancelled|expired|invalid/.test(normalized)) return 'red'
  return 'default'
}

function SectionLoadingState({ label }: { label: string }) {
  return (
    <div className="flex min-h-[400px] items-center justify-center rounded-[2.5rem] border border-slate-200 bg-white shadow-sm">
      <Space direction="vertical" align="center" size={24}>
        <div className="relative flex items-center justify-center">
          <div className="absolute h-16 w-16 animate-ping rounded-full bg-indigo-100 opacity-75"></div>
          <div className="relative h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
            <Spin size="large" />
          </div>
        </div>
        <Text className="text-slate-500 font-medium tracking-wide">{label}</Text>
      </Space>
    </div>
  )
}

function SectionErrorState({ title, error, onRetry }: { title: string; error: unknown; onRetry?: () => void }) {
  return (
    <div className="rounded-[2.5rem] border border-rose-100 bg-rose-50/30 p-12 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-100 text-rose-600">
        <XCircle size={32} />
      </div>
      <Title level={4} className="!mb-2">{title}</Title>
      <Paragraph className="mx-auto max-w-md text-slate-500">
        {(error as { message?: string })?.message || 'The intelligence data could not be retrieved from the cluster.'}
      </Paragraph>
      {onRetry && (
        <Button onClick={onRetry} className="mt-4 rounded-xl px-8 font-bold" icon={<Activity size={16}/>}>
          Retry Connection
        </Button>
      )}
    </div>
  )
}

function SectionHeader({
  section,
  navigate,
}: {
  section: IntelligenceSection
  navigate: ReturnType<typeof useNavigate>
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-slate-400">Intelligence Hub</Text>
          <Title level={2} className="!mb-0 !mt-0">
            Intelligence Hub
          </Title>
          <Paragraph className="!mb-0 max-w-4xl text-slate-500">
            Operational intelligence platform. Govern AI suggestions, manage automation rules and executions, review failures, configure prompts, and adjust tenant intelligence settings.
          </Paragraph>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {SECTION_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => {
              navigate(item.key === 'suggestions' ? '/intelligence' : `/intelligence/${item.key}`)
            }}
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

function DetailJson({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="space-y-2">
      <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">{title}</Text>
      <pre className="max-h-[280px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{prettyJson(value)}</pre>
    </div>
  )
}

function SuggestionsSection() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [processingSuggestionId, setProcessingSuggestionId] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  
  const suggestionsQuery = useApiQuery(['intelligence-hub', 'suggestions'], () => intelligenceHubApi.listSuggestions({
    category: categoryFilter || undefined,
    status: statusFilter || undefined,
  }), {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })

  const approveMutation = useApiMutation(
    ({ id, payload }: { id: string; payload?: AnyRecord }) => intelligenceHubApi.approveSuggestion(id, payload),
    {
      successMessage: 'Suggestion approved and applied.',
      errorMessage: 'Approval failed.',
      invalidateKeys: [['intelligence-hub', 'suggestions']],
      onSuccess: () => setSelectedId(null),
    },
  )
  const rejectMutation = useApiMutation(
    ({ id, payload }: { id: string; payload?: AnyRecord }) => intelligenceHubApi.rejectSuggestion(id, payload),
    {
      successMessage: 'Suggestion rejected.',
      invalidateKeys: [['intelligence-hub', 'suggestions']],
      onSuccess: () => setSelectedId(null),
    },
  )

  const suggestions = (suggestionsQuery.data as AnyRecord[] | undefined) ?? []
  
  const columns: ColumnsType<AnyRecord> = [
    { title: 'Suggestion', key: 'title', render: (_, record) => (
      <Space direction="vertical" size={0}>
        <Text strong>{record.title || humanize(record.suggestion_type)}</Text>
        <Text type="secondary" className="text-[10px]">{shortId(record.id)}</Text>
      </Space>
    )},
    { title: 'Category', dataIndex: 'category', key: 'cat', render: (v) => <Tag color="blue">{humanize(v)}</Tag> },
    { title: 'Confidence', dataIndex: 'confidence_score', key: 'conf', render: (v) => (
      <Space size={8}>
        <Progress percent={Math.round((v || 0) * 100)} size="small" showInfo={false} strokeColor={v > 0.8 ? '#52c41a' : v > 0.5 ? '#faad14' : '#ff4d4f'} className="w-12" />
        <Text className="text-[10px] font-bold">{Math.round((v || 0) * 100)}%</Text>
      </Space>
    )},
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{humanize(v)}</Tag> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: formatDateTime },
    { title: 'Action', key: 'action', render: (_, record) => (
      <Button size="small" onClick={(e) => { e.stopPropagation(); setSelectedId(record.id) }}>Review</Button>
    )},
  ]

  if (suggestionsQuery.isLoading) return <SectionLoadingState label="Analyzing suggestions…" />
  if (suggestionsQuery.error) return <SectionErrorState title="Connection Failed" error={suggestionsQuery.error} onRetry={() => suggestionsQuery.refetch()} />

  const selectedSuggestion = suggestions.find(s => s.id === selectedId)

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Pending Review" value={suggestions.filter(s => s.status === 'pending_review').length} icon={<Activity size={20}/>} color="text-amber-600" />
        <StatCard title="Avg Confidence" value={`${Math.round((suggestions.reduce((a,b) => a + (b.confidence_score || 0), 0) / (suggestions.length || 1)) * 100)}%`} icon={<TrendingUp size={20}/>} color="text-indigo-600" />
        <StatCard title="Applied Today" value={suggestions.filter(s => s.status === 'applied' && dayjs(s.updated_at).isAfter(dayjs().startOf('day'))).length} icon={<ShieldCheck size={20}/>} color="text-emerald-600" />
        <StatCard title="Rejected" value={suggestions.filter(s => s.status === 'rejected').length} icon={<ShieldAlert size={20}/>} color="text-rose-600" />
      </div>

      <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <div className="flex flex-wrap gap-4 px-8 py-6 bg-slate-50/50 border-b border-slate-100">
           <Select placeholder="Filter Category" className="w-48 rounded-xl" allowClear onChange={setCategoryFilter} value={categoryFilter} options={[{label: 'Pipeline', value: 'pipeline'}, {label: 'Communication', value: 'communication'}]} />
           <Select placeholder="Filter Status" className="w-48 rounded-xl" allowClear onChange={setStatusFilter} value={statusFilter} options={[{label: 'Pending Review', value: 'pending_review'}, {label: 'Applied', value: 'applied'}, {label: 'Rejected', value: 'rejected'}]} />
        </div>
        <Table rowKey="id" columns={columns} dataSource={suggestions} onRow={(record) => ({ onClick: () => setSelectedId(record.id), className: 'cursor-pointer' })} />
      </Card>

      <Drawer title="Suggestion Review" width={640} open={!!selectedId} onClose={() => setSelectedId(null)}>
        {selectedSuggestion ? (
          <Space direction="vertical" size={24} className="w-full">
            <div className="p-6 rounded-3xl bg-slate-50 border border-slate-100">
               <div className="flex justify-between items-start mb-4">
                  <Tag color="blue">{humanize(selectedSuggestion.category)}</Tag>
                  <Text className="text-xs font-black text-slate-400 uppercase tracking-widest">{formatDateTime(selectedSuggestion.created_at)}</Text>
               </div>
               <Title level={4} className="!m-0">{selectedSuggestion.title || humanize(selectedSuggestion.suggestion_type)}</Title>
               <Paragraph className="mt-2 text-slate-600">{selectedSuggestion.description}</Paragraph>
               
               <div className="mt-6 flex items-center gap-6">
                  <div>
                     <Text className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Confidence</Text>
                     <div className="flex items-center gap-2">
                        <Progress type="circle" percent={Math.round(selectedSuggestion.confidence_score * 100)} width={32} strokeWidth={12} strokeColor="#6366f1" />
                        <Text strong className="text-indigo-600">{Math.round(selectedSuggestion.confidence_score * 100)}%</Text>
                     </div>
                  </div>
                  <Divider type="vertical" className="h-10 border-slate-200" />
                  <div>
                     <Text className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Source Model</Text>
                     <Text strong className="text-slate-700">{selectedSuggestion.ai_model || 'GPT-4-Turbo'}</Text>
                  </div>
               </div>
            </div>

            <DetailJson title="Proposed Action" value={selectedSuggestion.proposed_action_payload} />
            <DetailJson title="Reasoning Context" value={selectedSuggestion.reasoning_json} />

            {selectedSuggestion.status === 'pending_review' && (
              <div className="flex gap-3 pt-4">
                <Button type="primary" size="large" className="flex-1 rounded-2xl h-12 font-bold" onClick={() => approveMutation.mutate({ id: selectedSuggestion.id })} loading={approveMutation.isPending}>Approve & Apply</Button>
                <Button danger size="large" className="flex-1 rounded-2xl h-12 font-bold" onClick={() => rejectMutation.mutate({ id: selectedSuggestion.id })} loading={rejectMutation.isPending}>Reject</Button>
              </div>
            )}
          </Space>
        ) : <Empty />}
      </Drawer>
    </>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: React.ReactNode; icon: React.ReactNode; color: string }) {
  return (
    <Card className="rounded-3xl border-slate-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</Text>
          <div className={`text-2xl font-black mt-1 ${color}`}>{value}</div>
        </div>
        <div className={`p-3 rounded-2xl bg-slate-50 ${color}`}>{icon}</div>
      </div>
    </Card>
  )
}

function AutomationIntelligenceSection() {
  const { data: insightsData, isLoading: loadingInsights } = useApiQuery(
    ['intelligence-hub', 'automation-insights'],
    () => intelligenceHubApi.listAutomationInsights({ status: 'new' }),
    { refetchOnWindowFocus: false }
  )

  const { data: recsData, isLoading: loadingRecs } = useApiQuery(
    ['intelligence-hub', 'automation-recommendations'],
    intelligenceHubApi.listAutomationRecommendations,
    { refetchOnWindowFocus: false }
  )

  const acceptMutation = useApiMutation(
    (id: string) => intelligenceHubApi.acceptAutomationInsight(id),
    {
      successMessage: 'Insight accepted and workflow created!',
      invalidateKeys: [['intelligence-hub', 'automation-insights']],
    }
  )

  const dismissMutation = useApiMutation(
    (id: string) => intelligenceHubApi.dismissAutomationInsight(id),
    {
      successMessage: 'Insight dismissed.',
      invalidateKeys: [['intelligence-hub', 'automation-insights']],
    }
  )

  const insights = (insightsData as any)?.data || []
  const recommendations = (recsData as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0 text-slate-900">AI Automation Intelligence</Title>
        <Text className="text-slate-500">
          Proactive AI analysis of your hiring pipelines, predicting bottlenecks, and suggesting high-impact workflows.
        </Text>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title={<div className="flex items-center gap-2"><Lightbulb size={18} className="text-amber-500" /> Actionable Insights</div>} className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '24px' }}>
          {loadingInsights ? (
            <SectionLoadingState label="Analyzing pipeline..." />
          ) : insights.length === 0 ? (
            <Empty description="No new insights. Your pipelines are optimized!" />
          ) : (
            <div className="space-y-4">
              {insights.map((insight: any) => (
                <div key={insight.id} className="p-5 rounded-2xl border border-slate-100 bg-slate-50 shadow-sm flex flex-col gap-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <Tag color="purple" className="mb-2 uppercase text-[10px] font-black tracking-widest">{humanize(insight.insight_type)}</Tag>
                      <Title level={5} className="!m-0">{insight.title}</Title>
                    </div>
                    <div className="text-right">
                      <Text className="block text-[10px] uppercase font-black text-slate-400">Confidence</Text>
                      <Text className="text-emerald-600 font-black">{Math.round(insight.confidence_score * 100)}%</Text>
                    </div>
                  </div>
                  <Text className="text-sm text-slate-600">{insight.description}</Text>
                  
                  {insight.suggested_action && (
                    <div className="mt-2 p-3 bg-white rounded-xl border border-indigo-100 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Bot size={16} className="text-indigo-500" />
                        <Text className="text-xs font-bold text-indigo-700">AI Suggests: {humanize(insight.suggested_action.action)}</Text>
                      </div>
                      <Space>
                        <Button 
                          size="small" 
                          className="rounded-lg text-[10px] uppercase font-black"
                          onClick={() => dismissMutation.mutate(insight.id)}
                          loading={dismissMutation.isPending}
                        >
                          Dismiss
                        </Button>
                        <Button 
                          type="primary" 
                          size="small" 
                          className="rounded-lg text-[10px] uppercase font-black bg-indigo-600"
                          icon={<Check size={12}/>}
                          onClick={() => acceptMutation.mutate(insight.id)}
                          loading={acceptMutation.isPending}
                        >
                          Accept & Automate
                        </Button>
                      </Space>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title={<div className="flex items-center gap-2"><TrendingUp size={18} className="text-blue-500" /> Strategic Recommendations</div>} className="rounded-3xl border-slate-200 shadow-sm" bodyStyle={{ padding: '24px' }}>
          {loadingRecs ? (
            <SectionLoadingState label="Generating recommendations..." />
          ) : recommendations.length === 0 ? (
            <Empty description="No strategic recommendations at this time." />
          ) : (
            <div className="space-y-4">
              {recommendations.map((rec: any) => (
                <div key={rec.id} className="p-5 rounded-2xl border border-slate-100 bg-white flex flex-col gap-2">
                  <div className="flex justify-between">
                    <Text className="text-[11px] font-black uppercase tracking-widest text-slate-400">{rec.recommendation_type}</Text>
                    <Tag color="blue">{Math.round(rec.confidence_score * 100)}% match</Tag>
                  </div>
                  <Text className="text-sm font-medium text-slate-800">{rec.reason}</Text>
                  {rec.workflow_template_name && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                      <ArrowRight size={14} /> 
                      Suggested Template: <Text strong>{rec.workflow_template_name}</Text>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

function PromptsSection() {
  const promptsQuery = useApiQuery(['intelligence-hub', 'prompts'], intelligenceHubApi.listPrompts, {
    retry: false,
    refetchOnWindowFocus: false,
  })

  const prompts = (promptsQuery.data as AnyRecord[] | undefined) ?? []

  const columns: ColumnsType<AnyRecord> = [
    { title: 'Prompt Key', dataIndex: 'prompt_key', key: 'key', render: (v) => <Text strong>{v}</Text> },
    { title: 'Version', dataIndex: 'current_version_number', key: 'ver', render: (v) => `v${v}` },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{humanize(v)}</Tag> },
    { title: 'Updated', dataIndex: 'updated_at', key: 'updated', render: formatDateTime },
  ]

  if (promptsQuery.isLoading) return <SectionLoadingState label="Loading prompt versions…" />
  if (promptsQuery.error) return <SectionErrorState title="Registry Unreachable" error={promptsQuery.error} onRetry={() => promptsQuery.refetch()} />

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="px-8 py-6 border-b border-slate-100 bg-white">
        <Title level={4} className="!m-0">Prompt Engineering</Title>
        <Text className="text-slate-500">Manage AI system prompts, versioning, and approval workflows.</Text>
      </div>
      <Table rowKey="id" columns={columns} dataSource={prompts} pagination={false} />
    </Card>
  )
}

function SettingsSection() { return <Empty description="Intelligence Hub Settings" /> }

function AutomationInsightsDashboard() {
  const { data: recsData } = useApiQuery(['intelligence-hub', 'automation-recommendations'], intelligenceHubApi.listAutomationRecommendations)
  const recommendations = (recsData as any)?.data || []

  return (
    <div className="grid gap-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0 text-slate-900">Automation Intelligence Dashboard</Title>
        <Text className="text-slate-500">Holistic view of AI-driven optimizations, automation coverage, and system performance.</Text>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="rounded-3xl border-slate-200 shadow-sm">
          <Statistic title={<Text className="text-[10px] font-black uppercase text-slate-400">Recommended Workflows</Text>} value={recommendations.length} prefix={<Zap size={16} className="text-amber-500" />} />
        </Card>
        <Card className="rounded-3xl border-slate-200 shadow-sm">
          <Statistic title={<Text className="text-[10px] font-black uppercase text-slate-400">Automation Coverage</Text>} value={68} suffix="%" prefix={<Activity size={16} className="text-indigo-500" />} />
        </Card>
        <Card className="rounded-3xl border-slate-200 shadow-sm">
          <Statistic title={<Text className="text-[10px] font-black uppercase text-slate-400">Optimization Impact</Text>} value={12.4} suffix="h saved/mo" prefix={<TrendingUp size={16} className="text-emerald-500" />} />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title="Missed Opportunities" className="rounded-3xl border-slate-200 shadow-sm">
          <List
            itemLayout="horizontal"
            dataSource={[
              { title: 'Incomplete Interview Loops', desc: '4 workflows missed because of missing calendar integrations.' },
              { title: 'Slow Offer Approvals', desc: 'Average delay of 18h detected in Finance stage.' }
            ]}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta title={<Text strong>{item.title}</Text>} description={item.desc} />
              </List.Item>
            )}
          />
        </Card>
        <Card title="Performance Insights" className="rounded-3xl border-slate-200 shadow-sm">
           <div className="space-y-4">
              <div className="flex justify-between items-center">
                 <Text className="text-xs font-bold text-slate-600">Workflow Execution Success</Text>
                 <Tag color="green">94.2%</Tag>
              </div>
              <Progress percent={94.2} strokeColor="#10b981" />
              <div className="flex justify-between items-center">
                 <Text className="text-xs font-bold text-slate-600">AI Suggestion Acceptance</Text>
                 <Tag color="blue">82.0%</Tag>
              </div>
              <Progress percent={82} strokeColor="#6366f1" />
           </div>
        </Card>
      </div>
    </div>
  )
}

function truncateText(value: unknown, maxLength = 88) {
  const text = String(value ?? '').trim()
  if (!text) return 'Not available'
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text
}

export default function IntelligenceHubWorkspace() {
  const params = useParams<{ section?: string }>()
  const navigate = useNavigate()
  const section = normalizeSection(params.section)

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <SectionHeader section={section} navigate={navigate} />
      {section === 'suggestions' ? <SuggestionsSection /> : null}
      {section === 'automation-intelligence' ? <AutomationIntelligenceSection /> : null}
      {section === 'automation-insights-dashboard' ? <AutomationInsightsDashboard /> : null}
      {section === 'prompts' ? <PromptsSection /> : null}
      {section === 'analytics' ? <IntelligenceAnalytics /> : null}
      {section === 'learning' ? <IntelligenceLearning /> : null}
      {section === 'optimization' ? <IntelligenceOptimization /> : null}
      {section === 'governance' ? <IntelligenceGovernance /> : null}
      {section === 'library' ? <AutomationLibrary /> : null}
      {section === 'change-impact' ? <AutomationChangeImpact /> : null}
      {section === 'observability' ? <AutomationObservability /> : null}
      {section === 'settings' ? <SettingsSection /> : null}
    </div>
  )
}
