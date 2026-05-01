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
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  Beaker,
  CheckCircle,
  Eye,
  FileText,
  FlaskConical,
  Play,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { automationSandboxApi } from '@/api/automationSandbox'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationSandbox() {
  const [activeTab, setActiveTab] = useState('runs')
  const [selectedRunId, setSelectedId] = useState<string | null>(null)
  const [isSimulationModalOpen, setIsSimulationModalOpen] = useState(false)
  const [form] = Form.useForm()

  const runsQuery = useApiQuery(['workflow-sandbox', 'runs'], automationSandboxApi.listRuns)
  const scenariosQuery = useApiQuery(['workflow-sandbox', 'scenarios'], automationSandboxApi.listScenarios)
  const workflowsQuery = useApiQuery(['intelligence-hub', 'workflows'], intelligenceHubApi.listWorkflows)

  const simulateMutation = useApiMutation(
    (data: any) => automationSandboxApi.simulate(data),
    {
      successMessage: 'Simulation completed successfully.',
      invalidateKeys: [['workflow-sandbox', 'runs']],
      onSuccess: (res) => {
        setIsSimulationModalOpen(false)
        form.resetFields()
        setSelectedId(res.data.id)
      }
    }
  )

  const isLoading = runsQuery.isLoading || scenariosQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Initializing sandbox environment...</Text>
        </Space>
      </div>
    )
  }

  const runs = (runsQuery.data as any)?.data || []
  const scenarios = (scenariosQuery.data as any)?.data || []
  const workflows = (workflowsQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-2">
          <Title level={3} className="!m-0">Automation Sandbox & Test Lab</Title>
          <Paragraph className="text-slate-500 max-w-3xl">
            Safely simulate, validate, and inspect your hiring workflows. Test edge cases, verify actions, and ensure production readiness without affecting live data.
          </Paragraph>
        </div>
        <Button 
          type="primary" 
          icon={<FlaskConical size={16}/>} 
          className="rounded-xl h-10 font-bold bg-indigo-600"
          onClick={() => setIsSimulationModalOpen(true)}
        >
          New Simulation
        </Button>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'runs',
            label: <Space><Activity size={16}/><span>Sandbox Runs</span></Space>,
            children: <RunTable runs={runs} onInspect={setSelectedId} />
          },
          {
            key: 'scenarios',
            label: <Space><Beaker size={16}/><span>Scenario Library</span></Space>,
            children: <ScenarioGrid scenarios={scenarios} />
          },
          {
            key: 'approvals',
            label: <Space><ShieldCheck size={16}/><span>Approvals</span></Space>,
            children: <Empty description="No sandbox approvals pending." className="py-12" />
          }
        ]}
      />

      <RunInspector runId={selectedRunId} onClose={() => setSelectedId(null)} />

      <Modal
        title="Simulate Workflow"
        open={isSimulationModalOpen}
        onCancel={() => setIsSimulationModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={simulateMutation.isPending}
        className="rounded-3xl"
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={(v) => simulateMutation.mutate(v)} className="py-4">
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="run_name" label="Simulation Name" rules={[{ required: true }]}>
                <Input placeholder="e.g. Test Offer Escalation" className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="workflow_id" label="Target Workflow" rules={[{ required: true }]}>
                <Select options={workflows.map((w:any) => ({ label: w.name, value: w.id }))} className="rounded-xl" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="scenario_id" label="Use Scenario (Optional)">
                <Select options={scenarios.map((s:any) => ({ label: s.name, value: s.id }))} className="rounded-xl" allowClear />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

function RunTable({ runs, onInspect }: { runs: any[], onInspect: (id: string) => void }) {
  const columns: ColumnsType<any> = [
    { title: 'Run Name', dataIndex: 'run_name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Trigger', dataIndex: 'trigger_event', key: 'trig', render: (v) => <Tag className="text-[10px] uppercase font-bold">{v}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={v === 'completed' ? 'green' : v === 'failed' ? 'red' : 'blue'}>{v.toUpperCase()}</Tag> },
    { title: 'Started At', dataIndex: 'created_at', key: 'at', render: (v) => dayjs(v).format('MMM DD, HH:mm') },
    { title: 'Actions', key: 'actions', render: (_, record) => (
      <Button size="small" type="link" icon={<Eye size={14}/>} onClick={() => onInspect(record.id)}>Inspect</Button>
    )}
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={runs} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  )
}

function ScenarioGrid({ scenarios }: { scenarios: any[] }) {
  return (
    <Row gutter={[24, 24]}>
      {scenarios.map((s) => (
        <Col xs={24} md={12} lg={8} key={s.id}>
          <Card className="rounded-3xl border-slate-200 shadow-sm h-full">
            <div className="flex justify-between items-start mb-2">
              <Title level={5} className="!m-0">{s.name}</Title>
              {s.is_system_scenario && <Tag color="blue" className="text-[9px] uppercase font-black tracking-tighter">System</Tag>}
            </div>
            <Paragraph className="text-slate-500 text-xs line-clamp-2">{s.description}</Paragraph>
            <div className="mt-4 flex items-center gap-2">
              <Tag className="rounded-full px-3 text-[10px] font-bold uppercase">{s.module_scope}</Tag>
              <Text className="text-[10px] text-slate-400 font-bold uppercase">{s.trigger_event}</Text>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function RunInspector({ runId, onClose }: { runId: string | null, onClose: () => void }) {
  const { data: runData, isLoading } = useApiQuery(
    ['workflow-sandbox', 'run', runId],
    () => automationSandboxApi.getRun(runId!),
    { enabled: !!runId }
  )

  const run = (runData as any)?.data

  return (
    <Drawer
      title="Simulation Inspector"
      width={800}
      onClose={onClose}
      open={!!runId}
      extra={<Button icon={<FileText size={14}/>}>Download Report</Button>}
    >
      {isLoading ? <Spin /> : run ? (
        <div className="space-y-8">
          <Row gutter={24}>
            <Col span={12}><Statistic title="Status" value={run.status.toUpperCase()} valueStyle={{ color: run.status === 'completed' ? '#10b981' : '#f43f5e', fontSize: 14, fontWeight: 900 }} /></Col>
            <Col span={12}><Statistic title="Execution Time" value={`${dayjs(run.completed_at).diff(run.started_at, 'ms')}ms`} valueStyle={{ fontSize: 14, fontWeight: 900 }} /></Col>
          </Row>

          <Divider />

          <div className="space-y-4">
            <Title level={5} className="flex items-center gap-2"><Zap size={18} className="text-indigo-500" /> Trace Log</Title>
            <Table
              size="small"
              pagination={false}
              dataSource={run.steps}
              rowKey="id"
              columns={[
                { title: 'Step', dataIndex: 'step_order', key: 'ord', width: 60 },
                { title: 'Node', dataIndex: 'action_type', key: 'type', render: (v) => <Tag className="text-[10px] uppercase font-black">{v}</Tag> },
                { title: 'Status', dataIndex: 'status', key: 'st', render: (v) => <Badge status={v === 'simulated' ? 'processing' : 'success'} text={v} /> },
                { title: 'Duration', dataIndex: 'duration_ms', key: 'dur', render: (v) => `${v}ms` },
              ]}
            />
          </div>

          <div className="space-y-4">
            <Title level={5} className="flex items-center gap-2"><Beaker size={18} className="text-emerald-500" /> Simulated Artifacts</Title>
            <List
              dataSource={run.artifacts}
              renderItem={(item: any) => (
                <List.Item className="rounded-2xl border border-slate-100 p-4 mb-3 bg-slate-50/50">
                  <List.Item.Meta
                    title={<Space><Text strong>{item.artifact_name}</Text><Tag color="cyan" className="text-[9px] font-black">{item.artifact_type.replace('simulated_', '').toUpperCase()}</Tag></Space>}
                    description={<pre className="text-[10px] mt-2 bg-white p-2 rounded-lg">{JSON.stringify(item.artifact_payload, null, 2)}</pre>}
                  />
                </List.Item>
              )}
            />
          </div>
        </div>
      ) : <Empty />}
    </Drawer>
  )
}
