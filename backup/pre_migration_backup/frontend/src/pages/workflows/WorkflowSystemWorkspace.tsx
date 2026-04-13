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
import {
  Activity,
  ArrowRight,
  Building2,
  CheckCircle2,
  Clock,
  Settings2,
  Database,
  Network,
  FileDone,
  History,
  Layers,
  LayoutGrid,
  Play,
  Rocket,
  Safety,
  Send,
  Settings,
  Thunderbolt,
  TrendingUp,
  XCircle,
  Zap,
  Users,
  Plus,
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect, useMemo } from 'react'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery } from '@/hooks/useApiQuery'
import dayjs from 'dayjs'
import GuidedWorkflowBuilder from './GuidedWorkflowBuilder'
import AdvancedWorkflowBuilder from './AdvancedWorkflowBuilder'
import AgencyEventTriggers from './AgencyEventTriggers'
import AgencyOrchestrationEngine from './AgencyOrchestrationEngine'
import OrchestrationEngine from './OrchestrationEngine'
import WorkflowEventWorkspace from './WorkflowEventWorkspace'
import { useAuthStore } from '@/store/authStore'

const { Title, Text, Paragraph } = Typography

type WorkflowSection =
  | 'hub'
  | 'dashboard'
  | 'active'
  | 'guided-builder'
  | 'advanced-builder'
  | 'templates'
  | 'playbooks'
  | 'e2e-company'
  | 'e2e-agency'
  | 'e2e-cross'
  | 'event-triggers'
  | 'rules'
  | 'instances'
  | 'history'
  | 'failures'
  | 'governance'
  | 'analytics'

const SECTION_ITEMS: Array<{ key: WorkflowSection; label: string; group: string }> = [
  { key: 'hub', label: 'Workflow Hub', group: 'Overview' },
  { key: 'dashboard', label: 'Dashboard', group: 'Overview' },
  { key: 'active', label: 'Active Workflows', group: 'Overview' },
  { key: 'guided-builder', label: 'Guided Builder', group: 'Builder' },
  { key: 'advanced-builder', label: 'Advanced Visual Builder', group: 'Builder' },
  { key: 'templates', label: 'Templates', group: 'Builder' },
  { key: 'playbooks', label: 'Playbooks', group: 'Builder' },
  { key: 'e2e-company', label: 'Company Hiring Flows', group: 'End-to-End' },
  { key: 'e2e-agency', label: 'Agency Recruitment Flows', group: 'End-to-End' },
  { key: 'e2e-cross', label: 'Cross-Entity Flows', group: 'End-to-End' },
  { key: 'event-triggers', label: 'Event Triggers', group: 'Automation' },
  { key: 'instances', label: 'Running Instances', group: 'Execution' },
  { key: 'history', label: 'Execution History', group: 'Execution' },
  { key: 'failures', label: 'Failure Logs', group: 'Execution' },
  { key: 'governance', label: 'Governance', group: 'Governance' },
  { key: 'analytics', label: 'Workflow Analytics', group: 'Analytics' },
]

function SectionHeader({
  section,
  navigate,
}: {
  section: WorkflowSection
  navigate: ReturnType<typeof useNavigate>
}) {
  const currentItem = SECTION_ITEMS.find(i => i.key === section)
  
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">Workflow System</Text>
          <Title level={2} className="!mb-0 !mt-0">
            {currentItem?.label || 'Workflow Hub'}
          </Title>
          <Paragraph className="!mb-0 max-w-4xl text-slate-500">
            Enterprise process orchestration. Design business-friendly hiring flows, manage automation triggers, and monitor execution health across company and agency lifecycles.
          </Paragraph>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {['Overview', 'Builder', 'End-to-End', 'Automation', 'Execution', 'Governance', 'Analytics'].map(group => (
          <div key={group} className="flex items-center gap-2 mr-4 last:mr-0">
            <Text className="text-[9px] font-black uppercase text-slate-400 mr-1">{group}:</Text>
            <div className="flex gap-1">
              {SECTION_ITEMS.filter(i => i.group === group).map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => navigate(`/workflows/${item.key}`)}
                  className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition ${
                    item.key === section
                      ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                      : 'border-slate-100 bg-white text-slate-400 hover:border-slate-300 hover:text-slate-600'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Placeholder Components for Workflow System ──────────────────────────────

function WorkflowDashboard() {
  const navigate = useNavigate()
  const { data: workflowsData } = useApiQuery(['workflow-system', 'dashboard-workflows'], intelligenceHubApi.listWorkflows)
  const workflows = (workflowsData as any[]) || []

  const companyFlows = workflows.filter(w => w.scope === 'company' || w.category === 'company')
  const agencyFlows = workflows.filter(w => w.scope === 'agency' || w.category === 'agency')
  const crossEntityFlows = workflows.filter(w => w.scope === 'cross_entity' || w.category === 'e2e')
  const draftWorkflows = workflows.filter(w => w.status === 'draft')

  return (
    <div className="space-y-8">
      {/* ─── Overview Cards ─── */}
      <Row gutter={[24, 24]}>
        <Col xs={24} md={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <Statistic title="Active Processes" value={ workflows.filter(w => w.status === 'active').length } prefix={<Play size={18} className="text-emerald-500 mr-2" />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <Statistic title="Total Automations" value={workflows.length} prefix={<Zap size={18} className="text-amber-500 mr-2" />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <Statistic title="Avg. Completion" value={94.5} suffix="%" prefix={<Activity size={18} className="text-indigo-500 mr-2" />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <Statistic title="Efficiency Gain" value={12.4} suffix="h/mo" prefix={<TrendingUp size={18} className="text-blue-500 mr-2" />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* ─── Flow Categories ─── */}
        <Col xs={24} lg={16}>
          <div className="space-y-6">
            <FlowCategorySection title="Company Hiring Flows" icon={<Building2 size={20} className="text-blue-500" />} data={companyFlows} onAdd={() => navigate('/workflows/guided-builder?type=company')} />
            <FlowCategorySection title="Agency Recruitment Flows" icon={<Users size={20} className="text-emerald-500" />} data={agencyFlows} onAdd={() => navigate('/workflows/guided-builder?type=agency')} />
            <FlowCategorySection title="Cross-Entity Flows" icon={<Layers size={20} className="text-indigo-500" />} data={crossEntityFlows} onAdd={() => navigate('/workflows/guided-builder?type=e2e')} />
          </div>
        </Col>

        {/* ─── Sidebar Status ─── */}
        <Col xs={24} lg={8}>
          <div className="space-y-6">
            <StatusListSection title="Draft Workflows" data={draftWorkflows} emptyText="No pending drafts" />
            <StatusListSection title="Running Instances" data={[]} emptyText="No active instances" isRunning />
            
            <Card title="Quick Actions" className="rounded-3xl border-slate-200 shadow-sm">
              <Space direction="vertical" className="w-full">
                <Button block className="rounded-xl h-12 text-left flex items-center gap-3 px-4 font-bold" onClick={() => navigate('/workflows/guided-builder')}>
                  <Rocket size={18} className="text-indigo-500" /> Start Guided Builder
                </Button>
                <Button block className="rounded-xl h-12 text-left flex items-center gap-3 px-4 font-bold" onClick={() => navigate('/workflows/advanced-builder')}>
                  <Settings2 size={18} className="text-slate-500" /> Advanced Flow Editor
                </Button>
              </Space>
            </Card>
          </div>
        </Col>
      </Row>
    </div>
  )
}

function FlowCategorySection({ title, icon, data, onAdd }: { title: string; icon: React.ReactNode; data: any[]; onAdd: () => void }) {
  const navigate = useNavigate()
  return (
    <Card className="rounded-[2rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="flex justify-between items-center px-6 py-4 bg-slate-50/50 border-b border-slate-100">
        <div className="flex items-center gap-3">
          {icon}
          <Title level={5} className="!m-0">{title}</Title>
          <Badge count={data.length} className="site-badge-count-4" style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
        </div>
        <Button type="text" size="small" icon={<Plus size={14}/>} onClick={onAdd}>Create New</Button>
      </div>
      <div className="p-4">
        {data.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.slice(0, 4).map(flow => (
              <div key={flow.id} className="p-3 rounded-2xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/20 transition-all cursor-pointer group" onClick={() => navigate(`/workflows/guided-builder?id=${flow.id}`)}>
                <div className="flex justify-between items-start">
                  <Text strong className="text-sm truncate pr-4">{flow.name}</Text>
                  <ArrowRight size={14} className="text-slate-300 group-hover:text-indigo-500 transition-colors" />
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <Tag color={flow.status === 'active' ? 'green' : 'gold'} className="text-[9px] uppercase font-black tracking-widest">{flow.status}</Tag>
                  <Text className="text-[10px] text-slate-400">v{flow.version || 1.0}</Text>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center bg-white">
            <Text type="secondary" className="text-xs italic">No {title.toLowerCase()} configured yet.</Text>
          </div>
        )}
      </div>
    </Card>
  )
}

function StatusListSection({ title, data, emptyText, isRunning }: { title: string; data: any[]; emptyText: string; isRunning?: boolean }) {
  return (
    <Card title={<div className="flex items-center gap-2"><Text strong>{title}</Text></div>} size="small" className="rounded-3xl border-slate-200 shadow-sm overflow-hidden">
      {data.length > 0 ? (
        <div className="divide-y divide-slate-100">
          {data.map(item => (
            <div key={item.id} className="py-3 flex items-center justify-between group">
              <div>
                <Text className="text-xs font-bold block truncate">{item.name || item.id.slice(0,8)}</Text>
                <Text className="text-[9px] text-slate-400 font-mono uppercase">{isRunning ? item.current_stage : formatDateTime(item.updated_at)}</Text>
              </div>
              <Button type="text" size="small" icon={<ArrowRight size={14} className="text-slate-200 group-hover:text-indigo-500" />} />
            </div>
          ))}
        </div>
      ) : (
        <div className="py-6 text-center">
          <Text type="secondary" className="text-[11px] italic">{emptyText}</Text>
        </div>
      )}
    </Card>
  )
}

function WorkflowHub() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('all')
  const { data: workflowsData, isLoading } = useApiQuery(['workflow-system', 'hub'], intelligenceHubApi.listWorkflows)
  const workflows = (workflowsData as any[]) || []

  const filteredWorkflows = useMemo(() => {
    if (activeTab === 'all') return workflows
    return workflows.filter(w => w.category === activeTab || w.scope === activeTab)
  }, [workflows, activeTab])

  const columns: ColumnsType<any> = [
    { title: 'Workflow Name', dataIndex: 'name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Scope', dataIndex: 'scope', key: 'scope', render: (v) => <Tag color="blue">{v?.toUpperCase() || 'GENERAL'}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={v === 'active' ? 'green' : 'gold'}>{v?.toUpperCase()}</Tag> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: (v) => dayjs(v).format('DD MMM YYYY') },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => navigate(`/workflows/guided-builder?id=${record.id}`)}>Edit</Button>
          <Button size="small" type="link" onClick={() => navigate(`/workflows/advanced-builder/${record.id}`)} icon={<Settings size={14}/>} />
        </Space>
      ),
    },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <div className="flex flex-col">
        <div className="flex justify-between items-center px-8 py-6 bg-slate-50/50 border-b border-slate-100">
          <Title level={4} className="!m-0">Process Repository</Title>
          <Button type="primary" className="rounded-xl h-10 font-bold bg-indigo-600" onClick={() => navigate('/workflows/guided-builder')}>
            Create New Process
          </Button>
        </div>
        <div className="px-8 py-2 border-b border-slate-100">
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            items={[
              { key: 'all', label: 'All Flows' },
              { key: 'company', label: 'Company Flows' },
              { key: 'agency', label: 'Agency Flows' },
              { key: 'e2e', label: 'End-to-End' },
              { key: 'template', label: 'Templates' },
              { key: 'draft', label: 'Drafts' },
            ]}
          />
        </div>
        <Table rowKey="id" columns={columns} dataSource={filteredWorkflows} loading={isLoading} />
      </div>
    </Card>
  )
}

export default function WorkflowSystemWorkspace() {
  const { section } = useParams<{ section: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const normalizedSection = (section || 'hub') as WorkflowSection
  const isAgency = user?.role?.includes('agency')

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <SectionHeader section={normalizedSection} navigate={navigate} />
      
      {normalizedSection === 'dashboard' && <WorkflowDashboard />}
      {normalizedSection === 'hub' && <WorkflowHub />}
      
      {/* Sections that redirect to specific builders */}
      {normalizedSection === 'guided-builder' && <GuidedWorkflowBuilder />}
      {normalizedSection === 'advanced-builder' && <AdvancedWorkflowBuilder />}

      {/* Orchestration & Events */}
      {normalizedSection === 'e2e-company' && <OrchestrationEngine />}
      {normalizedSection === 'e2e-agency' && <AgencyOrchestrationEngine />}
      
      {normalizedSection === 'event-triggers' && (
        isAgency ? <AgencyEventTriggers /> : <WorkflowEventWorkspace />
      )}
      
      {normalizedSection === 'instances' && (
        isAgency ? <AgencyOrchestrationEngine /> : <OrchestrationEngine />
      )}

      {/* Sections that use the Hub but filtered or ComingSoon */}
      {normalizedSection === 'active' && <WorkflowHub />}
      {normalizedSection === 'templates' && <WorkflowHub />}
      
      {/* Grouped logic for other sections */}
      {['playbooks', 'e2e-cross', 'rules', 'history', 'failures', 'governance', 'analytics'].includes(normalizedSection) && (
        <ComingSoon label={SECTION_ITEMS.find(i => i.key === normalizedSection)?.label || normalizedSection} />
      )}
    </div>
  )
}

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center rounded-[2.5rem] border border-slate-200 bg-white p-12 shadow-sm text-center">
      <div className="mb-6 rounded-full bg-slate-50 p-8">
        <Layers size={48} className="text-slate-200" />
      </div>
      <Title level={3} className="!mb-2">{label}</Title>
      <Paragraph className="max-w-md text-slate-500">
        This module is currently being refactored into the new Workflow System architecture.
      </Paragraph>
      <Button type="primary" className="rounded-xl px-8 font-bold mt-4" ghost>
        View Documentation
      </Button>
    </div>
  )
}
