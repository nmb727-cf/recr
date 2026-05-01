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
  BookOpen,
  CheckCircle,
  Copy,
  Download,
  Info,
  Layout,
  Play,
  RotateCcw,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { automationPlaybooksApi } from '@/api/automationPlaybooks'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationPlaybooks() {
  const [activeTab, setActiveTab] = useState('library')
  const [selectedPlaybookId, setSelectedPlaybookId] = useState<string | null>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [isInstallWizardOpen, setIsInstallWizardOpen] = useState(false)
  const [form] = Form.useForm()

  const libraryQuery = useApiQuery(['automation-playbooks', 'library'], automationPlaybooksApi.getLibrary)
  const installedQuery = useApiQuery(['automation-playbooks', 'installed'], automationPlaybooksApi.listInstalled)
  const recommendationsQuery = useApiQuery(['automation-playbooks', 'recommendations'], automationPlaybooksApi.listRecommendations)
  const analyticsQuery = useApiQuery(['automation-playbooks', 'analytics'], automationPlaybooksApi.getAnalytics)

  const previewQuery = useApiQuery(
    ['automation-playbooks', 'preview', selectedPlaybookId],
    () => automationPlaybooksApi.getPreview(selectedPlaybookId!),
    { enabled: !!selectedPlaybookId && isPreviewOpen }
  )

  const installMutation = useApiMutation(
    (config: any) => automationPlaybooksApi.installPlaybook(selectedPlaybookId!, config),
    {
      successMessage: 'Playbook installation initiated.',
      invalidateKeys: [['automation-playbooks', 'installed']],
      onSuccess: () => {
        setIsInstallWizardOpen(false)
        form.resetFields()
      }
    }
  )

  const duplicateMutation = useApiMutation(
    (id: string) => automationPlaybooksApi.duplicatePlaybook(id),
    {
      successMessage: 'Playbook duplicated to your collection.',
      invalidateKeys: [['automation-playbooks', 'library']]
    }
  )

  const isLoading = libraryQuery.isLoading || installedQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Accessing playbook vault...</Text>
        </Space>
      </div>
    )
  }

  const library = (libraryQuery.data as any)?.data || []
  const installed = (installedQuery.data as any)?.data || []
  const recommendations = (recommendationsQuery.data as any)?.data || []
  const analytics = (analyticsQuery.data as any)?.data || { top_installed: [] }

  const handlePreview = (id: string) => {
    setSelectedPlaybookId(id)
    setIsPreviewOpen(true)
  }

  const handleInstall = (id: string) => {
    setSelectedPlaybookId(id)
    setIsInstallWizardOpen(true)
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0">Automation Playbooks</Title>
        <Paragraph className="text-slate-500 max-w-3xl">
          Deploy expert-crafted automation bundles. Turn complex multi-step workflows, SLAs, and notifications into ready-made business solutions with a single click.
        </Paragraph>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'library',
            label: <Space><BookOpen size={16}/><span>Playbook Library</span></Space>,
            children: <PlaybookGrid 
              playbooks={library} 
              onPreview={handlePreview} 
              onInstall={handleInstall} 
              onDuplicate={(id) => duplicateMutation.mutate(id)}
            />
          },
          {
            key: 'installed',
            label: <Space><CheckCircle size={16}/><span>Installed</span></Space>,
            children: <InstalledTable installed={installed} />
          },
          {
            key: 'recommendations',
            label: <Space><Sparkles size={16}/><span>Recommendations</span></Space>,
            children: <RecommendationsList recommendations={recommendations} onInstall={handleInstall} />
          },
          {
            key: 'analytics',
            label: <Space><TrendingUp size={16}/><span>Analytics</span></Space>,
            children: <PlaybookAnalytics analytics={analytics} />
          }
        ]}
      />

      {/* Preview Drawer */}
      <Drawer
        title="Playbook Preview"
        placement="right"
        width={600}
        onClose={() => setIsPreviewOpen(false)}
        open={isPreviewOpen}
        extra={
          <Button type="primary" onClick={() => { setIsPreviewOpen(false); setIsInstallWizardOpen(true); }} className="rounded-xl bg-indigo-600">
            Install Playbook
          </Button>
        }
      >
        {previewQuery.isLoading ? <Spin /> : (
          <div className="space-y-8">
            <div>
              <Title level={4}>{(previewQuery.data as any)?.data.name}</Title>
              <Paragraph className="text-slate-500">{(previewQuery.data as any)?.data.description}</Paragraph>
            </div>

            <Card className="rounded-3xl border-slate-100 bg-slate-50/50 shadow-none">
              <Descriptions title="Expected Impact" column={1}>
                <Descriptions.Item label="Time Saved">{(previewQuery.data as any)?.data.expected_impact.time_saved_weekly}</Descriptions.Item>
                <Descriptions.Item label="Accuracy Improvement">{(previewQuery.data as any)?.data.expected_impact.accuracy_improvement}</Descriptions.Item>
                <Descriptions.Item label="SLA Compliance">{(previewQuery.data as any)?.data.expected_impact.sla_breach_reduction}</Descriptions.Item>
              </Descriptions>
            </Card>

            <div className="space-y-4">
              <Title level={5}>Included Components</Title>
              <List
                dataSource={(previewQuery.data as any)?.data.items || []}
                renderItem={(item: any) => (
                  <List.Item className="px-0">
                    <List.Item.Meta
                      avatar={<div className="p-2 rounded-xl bg-indigo-50 text-indigo-600"><Zap size={16}/></div>}
                      title={<Text strong className="text-xs">{item.item_name}</Text>}
                      description={<Tag className="text-[10px] uppercase font-bold">{item.item_type}</Tag>}
                    />
                  </List.Item>
                )}
              />
            </div>
          </div>
        )}
      </Drawer>

      {/* Install Wizard */}
      <Modal
        title="Install Playbook Wizard"
        open={isInstallWizardOpen}
        onCancel={() => setIsInstallWizardOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={installMutation.isPending}
        className="rounded-3xl"
        width={640}
      >
        <div className="py-4">
          <Paragraph>This wizard will guide you through the configuration of the <strong>{library.find((p:any) => p.id === selectedPlaybookId)?.name}</strong>.</Paragraph>
          <Divider />
          <Form form={form} layout="vertical" onFinish={(v) => installMutation.mutate(v)}>
             <Form.Item label="Primary Owner" name={['config', 'owner_role']} initialValue="recruiter">
                <Select options={[
                  { label: 'Recruiter', value: 'recruiter' },
                  { label: 'Hiring Manager', value: 'hiring_manager' },
                  { label: 'Admin', value: 'admin' },
                ]} className="rounded-xl" />
             </Form.Item>
             <Form.Item label="Reminder Window (Hours)" name={['config', 'reminder_hours']} initialValue={24}>
                <Input type="number" className="rounded-xl" />
             </Form.Item>
             <Form.Item label="Notification Channel" name={['config', 'channel']} initialValue="email">
                <Select options={[
                  { label: 'Email Only', value: 'email' },
                  { label: 'Slack Only', value: 'slack' },
                  { label: 'Multi-Channel', value: 'mixed' },
                ]} className="rounded-xl" />
             </Form.Item>
          </Form>
        </div>
      </Modal>
    </div>
  )
}

function PlaybookGrid({ playbooks, onPreview, onInstall, onDuplicate }: { playbooks: any[], onPreview: (id: string) => void, onInstall: (id: string) => void, onDuplicate: (id: string) => void }) {
  return (
    <Row gutter={[24, 24]}>
      {playbooks.map((pb) => (
        <Col xs={24} md={12} lg={8} key={pb.id}>
          <Card 
            className="rounded-[2rem] border-slate-200 shadow-sm hover:shadow-md transition-all h-full flex flex-col"
            bodyStyle={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column' }}
          >
            <div className="flex justify-between items-start mb-4">
              <Tag color="indigo" className="rounded-full px-3 text-[10px] font-black uppercase tracking-widest">
                {pb.category}
              </Tag>
              <Text className="text-[10px] text-slate-400 font-bold uppercase">v{pb.version}</Text>
            </div>
            
            <Title level={5} className="!m-0 mb-2">{pb.name}</Title>
            <Paragraph className="text-slate-500 text-xs line-clamp-2 mb-6">
              {pb.description}
            </Paragraph>

            <div className="mt-auto space-y-2">
              <div className="flex gap-2">
                <Button 
                  className="flex-1 rounded-xl font-bold text-xs h-10" 
                  icon={<Info size={14}/>}
                  onClick={() => onPreview(pb.id)}
                >
                  Preview
                </Button>
                <Button 
                  type="primary" 
                  className="flex-1 rounded-xl font-bold text-xs h-10 bg-indigo-600" 
                  icon={<Download size={14}/>}
                  onClick={() => onInstall(pb.id)}
                >
                  Install
                </Button>
              </div>
              <Button 
                type="text" 
                className="w-full rounded-xl font-bold text-[10px] uppercase text-slate-400" 
                icon={<Copy size={12}/>}
                onClick={() => onDuplicate(pb.id)}
              >
                Duplicate to Custom
              </Button>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function InstalledTable({ installed }: { installed: any[] }) {
  const columns: ColumnsType<any> = [
    { title: 'Playbook', dataIndex: 'playbook_name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Installed At', dataIndex: 'installed_at', key: 'at', render: (v) => v ? dayjs(v).format('MMM DD, YYYY') : '—' },
    { title: 'Workflows', dataIndex: 'created_workflow_count', key: 'wf', align: 'center' },
    { title: 'Status', dataIndex: 'install_status', key: 'status', render: (v) => <Tag color={v === 'installed' ? 'green' : 'orange'}>{v.toUpperCase()}</Tag> },
    { title: 'Actions', key: 'actions', render: (_, record) => (
      <Space>
        <Button size="small" type="link" icon={<Play size={12}/>}>View</Button>
        <Button size="small" type="link" danger icon={<RotateCcw size={12}/>}>Rollback</Button>
      </Space>
    )}
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table columns={columns} dataSource={installed} rowKey="id" pagination={false} locale={{ emptyText: <Empty description="No playbooks installed yet." /> }} />
    </Card>
  )
}

function RecommendationsList({ recommendations, onInstall }: { recommendations: any[], onInstall: (id: string) => void }) {
  if (recommendations.length === 0) return <Card className="rounded-[2rem] border-slate-200 shadow-sm"><Empty description="No AI recommendations available yet." /></Card>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {recommendations.map((rec) => (
        <Card key={rec.id} className="rounded-[2rem] border-amber-100 bg-amber-50/20 shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <Space>
              <Sparkles size={18} className="text-amber-500" />
              <Text strong className="text-amber-900">{rec.playbook_name}</Text>
            </Space>
            <Badge count={`${Math.round(rec.confidence_score * 100)}% Match`} style={{ backgroundColor: '#f59e0b' }} />
          </div>
          <Paragraph className="text-xs text-amber-800">{rec.recommendation_reason}</Paragraph>
          <Button 
            type="primary" 
            size="small" 
            className="rounded-lg bg-amber-600 border-none font-bold"
            onClick={() => onInstall(rec.playbook_id)}
          >
            Review & Install
          </Button>
        </Card>
      ))}
    </div>
  )
}

function PlaybookAnalytics({ analytics }: { analytics: any }) {
  return (
    <Row gutter={[24, 24]}>
      <Col lg={16}>
        <Card title="Playbook Installation Trends" className="rounded-[2rem] border-slate-200 shadow-sm h-full">
          <Empty description="Collecting trend data..." className="py-12" />
        </Card>
      </Col>
      <Col lg={8}>
        <Card title="Impact Summary" className="rounded-[2rem] border-slate-200 shadow-sm h-full">
          <div className="space-y-6">
            <Statistic title="Total Automated Workflows" value={14} prefix={<Zap size={16}/>} />
            <Statistic title="Manual Tasks Prevented" value={128} prefix={<TrendingUp size={16}/>} />
            <div className="space-y-2">
              <Text className="text-xs text-slate-400 font-bold uppercase">Efficiency Gain</Text>
              <Progress percent={22} strokeColor="#6366f1" />
            </div>
          </div>
        </Card>
      </Col>
    </Row>
  )
}
