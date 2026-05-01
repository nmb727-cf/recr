import {
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
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
  AlertTriangle,
  BarChart2,
  Clock,
  Plus,
  ShieldCheck,
  Target,
  Timer,
  TrendingUp,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useState } from 'react'

import { automationSlaApi } from '@/api/automationSla'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text, Paragraph } = Typography

export default function AutomationSla() {
  const [activeTab, setActiveTab] = useState('policies')
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false)
  const [form] = Form.useForm()

  const policiesQuery = useApiQuery(['workflow-sla', 'policies'], automationSlaApi.listPolicies)
  const executionsQuery = useApiQuery(['workflow-sla', 'executions'], automationSlaApi.listExecutions)
  const analyticsQuery = useApiQuery(['workflow-sla', 'analytics'], automationSlaApi.getAnalytics)
  const insightsQuery = useApiQuery(['workflow-sla', 'insights'], automationSlaApi.listBreachInsights)

  const createPolicyMutation = useApiMutation(
    (data: any) => automationSlaApi.createPolicy(data),
    {
      successMessage: 'SLA Policy created successfully.',
      invalidateKeys: [['workflow-sla', 'policies']],
      onSuccess: () => {
        setIsPolicyModalOpen(false)
        form.resetFields()
      }
    }
  )

  const completeSlaMutation = useApiMutation(
    (id: string) => automationSlaApi.completeSla(id),
    {
      successMessage: 'SLA marked as completed.',
      invalidateKeys: [['workflow-sla', 'executions'], ['workflow-sla', 'analytics']]
    }
  )

  const isLoading = policiesQuery.isLoading || executionsQuery.isLoading || analyticsQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Initializing SLA engine...</Text>
        </Space>
      </div>
    )
  }

  const policies = (policiesQuery.data as any)?.data || []
  const executions = (executionsQuery.data as any)?.data || []
  const analytics = (analyticsQuery.data as any)?.data || { summary: {}, module_comparison: [] }
  const insights = (insightsQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-2">
          <Title level={3} className="!m-0">Automation SLA Engine</Title>
          <Paragraph className="text-slate-500 max-w-3xl">
            Monitor and enforce time-bound recruitment actions. Automatically track deadlines, trigger warnings, and manage escalations across all modules.
          </Paragraph>
        </div>
        <Button 
          type="primary" 
          icon={<Plus size={16}/>} 
          className="rounded-xl h-10 font-bold bg-indigo-600"
          onClick={() => setIsPolicyModalOpen(true)}
        >
          New SLA Policy
        </Button>
      </div>

      {/* 1. Analytics Summary */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard 
            title="SLA Completion" 
            value={`${analytics.summary.completion_rate}%`} 
            icon={<ShieldCheck size={20}/>} 
            color="text-emerald-600" 
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard 
            title="Breach Rate" 
            value={`${analytics.summary.breach_rate}%`} 
            icon={<AlertTriangle size={20}/>} 
            color="text-rose-600" 
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard 
            title="Active Trackers" 
            value={executions.filter((e:any) => e.current_status === 'active' || e.current_status === 'warning_due').length} 
            icon={<Timer size={20}/>} 
            color="text-indigo-600" 
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard 
            title="Avg Resolve Time" 
            value={`${analytics.summary.avg_completion_time_minutes}m`} 
            icon={<Clock size={20}/>} 
            color="text-amber-600" 
          />
        </Col>
      </Row>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'policies',
            label: <Space><ShieldCheck size={16}/><span>SLA Policies</span></Space>,
            children: <PolicyTable policies={policies} />
          },
          {
            key: 'executions',
            label: <Space><Timer size={16}/><span>Live Trackers</span></Space>,
            children: <ExecutionTable executions={executions} onComplete={(id) => completeSlaMutation.mutate(id)} />
          },
          {
            key: 'dashboard',
            label: <Space><BarChart2 size={16}/><span>Breach Dashboard</span></Space>,
            children: <BreachDashboard analytics={analytics} insights={insights} />
          }
        ]}
      />

      <Modal
        title="Create SLA Policy"
        open={isPolicyModalOpen}
        onCancel={() => setIsPolicyModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createPolicyMutation.isPending}
        className="rounded-3xl"
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createPolicyMutation.mutate(v)} className="py-4">
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="name" label="Policy Name" rules={[{ required: true }]}>
                <Input placeholder="e.g. Candidate Application Review" className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="module_scope" label="Module Scope" rules={[{ required: true }]}>
                <Select options={[
                  { label: 'Candidates', value: 'candidates' },
                  { label: 'Interviews', value: 'interviews' },
                  { label: 'Offers', value: 'offers' },
                  { label: 'Pipeline', value: 'pipeline' },
                ]} className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="trigger_event" label="Trigger Event" rules={[{ required: true }]}>
                <Input placeholder="e.g. candidate_applied" className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="deadline_minutes" label="Deadline (Min)" rules={[{ required: true }]}>
                <InputNumber className="w-full rounded-xl" min={1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="warning_before_minutes" label="Warning (Min)" initialValue={60}>
                <InputNumber className="w-full rounded-xl" min={1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="priority" label="Priority" initialValue="medium">
                <Select options={[
                  { label: 'Low', value: 'low' },
                  { label: 'Medium', value: 'medium' },
                  { label: 'High', value: 'high' },
                  { label: 'Critical', value: 'critical' },
                ]} className="rounded-xl" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
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

function PolicyTable({ policies }: { policies: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Policy Name', dataIndex: 'name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Module', dataIndex: 'module_scope', key: 'mod', render: (v) => <Tag color="blue" className="uppercase text-[10px] font-bold">{v}</Tag> },
    { title: 'Trigger', dataIndex: 'trigger_event', key: 'trigger', render: (v) => <code className="text-xs">{v}</code> },
    { title: 'Deadline', key: 'deadline', render: (_, record) => <span>{Math.round(record.deadline_minutes / 60)}h</span> },
    { title: 'Priority', dataIndex: 'priority', key: 'prio', render: (v) => <Tag color={v === 'critical' ? 'red' : 'orange'}>{v.toUpperCase()}</Tag> },
    { title: 'Status', dataIndex: 'is_active', key: 'active', render: (v) => <Badge status={v ? 'success' : 'default'} text={v ? 'Active' : 'Inactive'} /> },
  ]

  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={policies} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No SLA policies defined yet." /> }} />
    </Card>
  )
}

function ExecutionTable({ executions, onComplete }: { executions: any[], onComplete: (id: string) => void }) {
  const columns: ColumnsType<any> = [
    { title: 'Entity', key: 'entity', render: (_, record) => <Text strong className="text-xs">{record.entity_type}:{record.entity_id.slice(0,8)}</Text> },
    { title: 'SLA Policy', dataIndex: 'policy_name', key: 'policy' },
    { title: 'Due At', dataIndex: 'due_at', key: 'due', render: (v) => dayjs(v).format('MMM DD, HH:mm') },
    { title: 'Status', dataIndex: 'current_status', key: 'status', render: (v) => <Tag color={v === 'breached' ? 'red' : v === 'completed' ? 'green' : 'blue'}>{v.toUpperCase()}</Tag> },
    { title: 'Remaining', key: 'remaining', render: (_, record) => {
      if (record.current_status === 'completed') return <Text type="secondary">—</Text>
      const remaining = dayjs(record.due_at).diff(dayjs(), 'minute')
      return remaining > 0 ? <Text className="text-emerald-600 font-bold">{remaining}m</Text> : <Text className="text-rose-600 font-bold">Overdue</Text>
    }},
    { title: 'Action', key: 'action', render: (_, record) => (
      record.current_status !== 'completed' && record.current_status !== 'cancelled' && (
        <Button size="small" type="link" onClick={() => onComplete(record.id)}>Complete</Button>
      )
    )}
  ]

  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={executions} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  )
}

function BreachDashboard({ analytics, insights }: { analytics: any, insights: any[] }) {
  return (
    <div className="space-y-6">
      <Row gutter={[24, 24]}>
        <Col lg={16}>
          <Card title="Module Breach Comparison" className="rounded-[2rem] border-slate-200 shadow-sm h-full">
            <div className="space-y-6 py-4">
              {analytics.module_comparison.map((item: any) => (
                <div key={item.sla_policy__module_scope} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Text strong className="uppercase text-xs">{item.sla_policy__module_scope}</Text>
                    <Text className="text-xs text-slate-400">{item.breached} breaches / {item.total} total</Text>
                  </div>
                  <Progress 
                    percent={Math.round((item.breached / item.total) * 100)} 
                    strokeColor={item.breached / item.total > 0.3 ? '#ef4444' : '#6366f1'} 
                    size="small"
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>
        <Col lg={8}>
          <Card title="System Insights" className="rounded-[2rem] border-slate-200 shadow-sm h-full">
            <List
              dataSource={insights}
              renderItem={(item: any) => (
                <List.Item className="border-b-slate-50 px-0">
                  <List.Item.Meta
                    avatar={<div className="p-2 rounded-xl bg-amber-50 text-amber-600"><AlertTriangle size={16}/></div>}
                    title={<Text strong className="text-xs">{item.title}</Text>}
                    description={<Text className="text-[10px] text-slate-500">{item.description}</Text>}
                  />
                </List.Item>
              )}
              locale={{ emptyText: <Empty description="No breach insights detected." /> }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
