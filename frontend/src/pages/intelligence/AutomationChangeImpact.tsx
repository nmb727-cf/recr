import {
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
  GitMerge,
  Info,
  Network,
  Play,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { automationChangeImpactApi } from '@/api/automationChangeImpact'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationChangeImpact() {
  const [activeTab, setActiveTab] = useState('analysis')
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null)
  const [isAnalyzeModalOpen, setIsAnalyzeModalOpen] = useState(false)
  const [form] = Form.useForm()

  const analysisQuery = useApiQuery(['workflow-change', 'analysis'], automationChangeImpactApi.listAnalysis)
  const plansQuery = useApiQuery(['workflow-change', 'plans'], automationChangeImpactApi.listDeploymentPlans)
  const rollbackQuery = useApiQuery(['workflow-change', 'rollback'], () => automationChangeImpactApi.listRollbackPreviews())
  const workflowsQuery = useApiQuery(['intelligence-hub', 'workflows'], intelligenceHubApi.listWorkflows)

  const analyzeMutation = useApiMutation(
    (data: any) => automationChangeImpactApi.analyzeChange(data),
    {
      successMessage: 'Impact analysis complete.',
      invalidateKeys: [['workflow-change', 'analysis']],
      onSuccess: () => {
        setIsAnalyzeModalOpen(false)
        form.resetFields()
      }
    }
  )

  const deployMutation = useApiMutation(
    (id: string) => automationChangeImpactApi.deployChange({ change_set_id: id }),
    {
      successMessage: 'Deployment strategy initiated.',
      invalidateKeys: [['workflow-change', 'plans']]
    }
  )

  const isLoading = analysisQuery.isLoading || plansQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Mapping workflow dependencies...</Text>
        </Space>
      </div>
    )
  }

  const analysisData = (analysisQuery.data as any)?.data || []
  const plans = (plansQuery.data as any)?.data || []
  const workflows = (workflowsQuery.data as any)?.data || []
  const rollbackData = (rollbackQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-2">
          <Title level={3} className="!m-0">Automation Change Impact Center</Title>
          <Paragraph className="text-slate-500 max-w-3xl">
            Ensure safe automation changes. Map dependencies, detect affected modules, and simulate rollout risks before activating new workflows or versions.
          </Paragraph>
        </div>
        <Button 
          type="primary" 
          icon={<Activity size={16}/>} 
          className="rounded-xl h-10 font-bold bg-indigo-600"
          onClick={() => setIsAnalyzeModalOpen(true)}
        >
          New Impact Analysis
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Active Changes" value={analysisData.length} icon={<GitMerge size={20}/>} color="text-indigo-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="High Risk Deployments" value={analysisData.filter((a:any) => a.impact_level === 'critical' || a.impact_level === 'high').length} icon={<ShieldAlert size={20}/>} color="text-rose-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Pending Deployments" value={plans.filter((p:any) => p.status === 'pending').length} icon={<Play size={20}/>} color="text-amber-600" />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard title="Safe Rollbacks" value={rollbackData.filter((r:any) => r.rollback_possible).length} icon={<RotateCcw size={20}/>} color="text-emerald-600" />
        </Col>
      </Row>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'analysis',
            label: <Space><Activity size={16}/><span>Impact Analysis</span></Space>,
            children: <AnalysisTable data={analysisData} onSelect={setSelectedChangeId} />
          },
          {
            key: 'deployment',
            label: <Space><Play size={16}/><span>Deployment Plans</span></Space>,
            children: <DeploymentTable data={plans} onDeploy={(id) => deployMutation.mutate(id)} loading={deployMutation.isPending} />
          },
          {
            key: 'rollback',
            label: <Space><RotateCcw size={16}/><span>Rollback Preview</span></Space>,
            children: <RollbackTable data={rollbackData} />
          }
        ]}
      />

      <AnalysisDrawer 
        changeId={selectedChangeId} 
        data={analysisData.find((a:any) => a.id === selectedChangeId)} 
        onClose={() => setSelectedChangeId(null)} 
      />

      <Modal
        title="Analyze Workflow Change"
        open={isAnalyzeModalOpen}
        onCancel={() => setIsAnalyzeModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={analyzeMutation.isPending}
        className="rounded-3xl"
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={(v) => analyzeMutation.mutate(v)} className="py-4">
          <Form.Item name="workflow_id" label="Target Workflow" rules={[{ required: true }]}>
            <Select options={workflows.map((w:any) => ({ label: w.name, value: w.id }))} className="rounded-xl" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="from_version" label="From Version" initialValue={1}>
                <Input type="number" className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="to_version" label="To Version" initialValue={2}>
                <Input type="number" className="rounded-xl" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name={['change_summary', 'description']} label="Change Summary (Mock)">
            <Input.TextArea placeholder="Describe the changes for simulation..." className="rounded-xl" />
          </Form.Item>
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

function AnalysisTable({ data, onSelect }: { data: any[], onSelect: (id: string) => void }) {
  const columns: ColumnsType<any> = [
    { title: 'Workflow ID', dataIndex: 'workflow_id', render: (v) => <Text className="font-mono text-xs">{v.slice(0,8)}</Text> },
    { title: 'Version Change', render: (_, record) => <Text>v{record.from_version} → v{record.to_version}</Text> },
    { title: 'Risk Score', dataIndex: 'risk_score', render: (v) => <Progress percent={v} size="small" showInfo={false} strokeColor={v > 75 ? '#e11d48' : v > 50 ? '#f59e0b' : '#10b981'} className="w-24" /> },
    { title: 'Impact Level', dataIndex: 'impact_level', render: (v) => (
      <Tag color={v === 'critical' ? 'red' : v === 'high' ? 'orange' : v === 'medium' ? 'blue' : 'green'}>{v.toUpperCase()}</Tag>
    )},
    { title: 'Actions', render: (_, record) => (
      <Button size="small" type="link" onClick={() => onSelect(record.id)}>View Details</Button>
    )}
  ]

  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No impact analysis records found." /> }} />
    </Card>
  )
}

function DeploymentTable({ data, onDeploy, loading }: { data: any[], onDeploy: (id: string) => void, loading: boolean }) {
  const columns: ColumnsType<any> = [
    { title: 'Change Set ID', dataIndex: 'change_set', render: (v) => <Text className="font-mono text-xs">{(v||'').slice(0,8)}</Text> },
    { title: 'Strategy', dataIndex: 'deployment_strategy', render: (v) => <Tag className="uppercase font-bold text-[10px]">{v}</Tag> },
    { title: 'Status', dataIndex: 'status', render: (v) => <Tag color={v === 'pending' ? 'blue' : v === 'completed' ? 'green' : 'orange'}>{v.toUpperCase()}</Tag> },
    { title: 'Actions', render: (_, record) => (
      <Button size="small" type="primary" onClick={() => onDeploy(record.change_set)} disabled={record.status !== 'pending'} loading={loading}>
        Execute Rollout
      </Button>
    )}
  ]

  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No deployment plans found." /> }} />
    </Card>
  )
}

function RollbackTable({ data }: { data: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Change Set ID', dataIndex: 'change_set', render: (v) => <Text className="font-mono text-xs">{(v||'').slice(0,8)}</Text> },
    { title: 'Rollback Possible', dataIndex: 'rollback_possible', render: (v) => <Badge status={v ? 'success' : 'error'} text={v ? 'Yes' : 'No'} /> },
    { title: 'Impact/Risk', dataIndex: 'rollback_impact', render: (v) => <Text className="text-xs text-slate-500">{v}</Text> },
  ]

  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No rollback previews generated." /> }} />
    </Card>
  )
}

function AnalysisDrawer({ changeId, data, onClose }: { changeId: string | null, data: any, onClose: () => void }) {
  if (!data) return null;

  return (
    <Drawer title="Impact Analysis Details" width={600} onClose={onClose} open={!!changeId}>
      <div className="space-y-6">
        <Row gutter={16}>
          <Col span={12}><Statistic title="Risk Score" value={data.risk_score} suffix="/ 100" valueStyle={{ color: data.risk_score > 75 ? '#e11d48' : '#10b981' }} /></Col>
          <Col span={12}><Statistic title="Impact Level" value={data.impact_level.toUpperCase()} /></Col>
        </Row>
        
        <Divider />
        
        {data.impact_analysis && (
          <div className="space-y-4">
            <Title level={5}><Network size={16} className="inline mr-2" /> Dependency Map</Title>
            <Descriptions column={1} size="small" bordered className="bg-slate-50">
              <Descriptions.Item label="Affected Workflows">{data.impact_analysis.affected_workflows.length}</Descriptions.Item>
              <Descriptions.Item label="Affected Modules">{data.impact_analysis.affected_module.join(', ') || 'None'}</Descriptions.Item>
              <Descriptions.Item label="Affected Users (Est.)">{data.impact_analysis.affected_users_count}</Descriptions.Item>
              <Descriptions.Item label="SLA Impact">{data.impact_analysis.affected_slas.length}</Descriptions.Item>
            </Descriptions>

            <Alert type={data.risk_score > 50 ? "warning" : "info"} message="Risk Reason" description={data.impact_analysis.risk_reason} showIcon />
          </div>
        )}

        <Divider />
        
        {data.deployment_plan && (
          <div className="space-y-4">
            <Title level={5}><Play size={16} className="inline mr-2" /> Recommended Deployment</Title>
            <Card size="small" className="bg-indigo-50 border-indigo-100">
              <Text strong className="block mb-2 uppercase text-xs text-indigo-700">Strategy: {data.deployment_plan.deployment_strategy}</Text>
              {data.deployment_plan.rollout_steps.length > 0 && (
                <Text className="text-xs text-slate-600">Rollout Stages: {data.deployment_plan.rollout_steps.join('% → ')}%</Text>
              )}
            </Card>
          </div>
        )}
      </div>
    </Drawer>
  )
}
