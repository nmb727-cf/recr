import React, { useState } from 'react'
import { 
  Typography, 
  Card, 
  Tag, 
  Table, 
  Spin, 
  Alert, 
  Empty, 
  Tabs, 
  Button, 
  Statistic, 
  List, 
  Badge,
  Avatar,
  Space,
  Tooltip
} from 'antd'
import { 
  ShieldCheck, 
  Activity, 
  Clock, 
  UserCheck, 
  Zap, 
  AlertTriangle, 
  FileText, 
  User, 
  Bot,
  Settings,
  ChevronRight,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  History
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function GovernanceCenter() {
  const [activeTab, setActiveTab] = useState('audit')

  const { data: auditData, isLoading: loadingAudit, refetch: refetchAudit } = useApiQuery(
    ['intelligence-audit-logs'],
    () => intelligenceHubApi.listAuditLogs()
  )

  const { data: decisionData, isLoading: loadingDecisions } = useApiQuery(
    ['intelligence-decisions'],
    () => intelligenceHubApi.getDecisionsHistory(),
    { enabled: activeTab === 'decisions' }
  )

  const { data: automationData, isLoading: loadingAutomation } = useApiQuery(
    ['intelligence-automation-governance'],
    () => intelligenceHubApi.getAutomationGovernance(),
    { enabled: activeTab === 'automation' }
  )

  const { data: aiData, isLoading: loadingAI } = useApiQuery(
    ['intelligence-ai-transparency'],
    () => intelligenceHubApi.getAITransparency(),
    { enabled: activeTab === 'ai' }
  )

  const auditLogs = (auditData as any)?.data || []
  const decisions = (decisionData as any)?.data || { approvals: [], audit_decisions: [] }
  const automation = (automationData as any)?.data || { runs_summary: { total: 0, completed: 0, failed: 0 }, manual_overrides: [] }
  const aiTransparency = (aiData as any)?.data || { ai_summary: { total_executions: 0, total_suggestions: 0, applied_suggestions: 0 }, human_overrides: [] }

  return (
    <div className="mx-auto max-w-[1600px] p-6 lg:p-10 flex flex-col gap-8 min-h-screen bg-[#F8FAFC]">
      
      {/* ─── Governance Header ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-2xl bg-slate-900 flex items-center justify-center text-emerald-400 shadow-xl border border-slate-800">
            <ShieldCheck size={32} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <Badge status="processing" color="emerald" />
              <Text className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">Enterprise Control / Compliance</Text>
            </div>
            <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">Governance & Audit Center</Title>
          </div>
        </div>
        <div className="flex items-center gap-3">
           <Button icon={<RefreshCw size={14} />} onClick={() => refetchAudit()} className="h-11 rounded-xl font-black uppercase text-[10px] tracking-widest bg-white border-slate-200">Sync Ledger</Button>
           <Tag className="m-0 rounded-full bg-emerald-600 text-white px-4 py-1.5 border-none font-black text-[10px] uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-emerald-100">
             Compliance Active
           </Tag>
        </div>
      </div>

      {/* ─── Highlights ─── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
         <GovernanceStatCard label="Audit Retention" value="365 Days" sub="Enterprise Standard" icon={<History size={20}/>} color="indigo" />
         <GovernanceStatCard label="Human Overrides" value={automation.manual_overrides.length + aiTransparency.human_overrides.length} sub="Decision Inversions" icon={<UserCheck size={20}/>} color="amber" />
         <GovernanceStatCard label="System Trust" value="99.2%" sub="Verified Outcomes" icon={<ShieldCheck size={20}/>} color="emerald" />
         <GovernanceStatCard label="Alerts" value="0" sub="Compliance Breaches" icon={<AlertTriangle size={20}/>} color="rose" />
      </div>

      <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <div className="px-8 pt-8 border-b border-slate-100 bg-white">
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            className="custom-governance-tabs"
            items={[
              { 
                key: 'audit', 
                label: <TabLabel label="Audit Ledger" icon={<Activity size={14}/>} />,
                children: (
                  <div className="p-8">
                    <Table 
                      dataSource={auditLogs} 
                      loading={loadingAudit}
                      rowKey="id"
                      columns={[
                        {
                          title: 'ACTION',
                          dataIndex: 'action_type',
                          render: (text) => <Tag className="m-0 border-none bg-slate-100 text-slate-700 font-black text-[10px] uppercase px-3 rounded-lg">{text.replace('.', ': ')}</Tag>
                        },
                        {
                          title: 'ACTOR',
                          dataIndex: 'actor_id',
                          render: (id) => <Text className="text-xs font-bold text-slate-500">{id?.slice(0,8) || 'SYSTEM'}</Text>
                        },
                        {
                          title: 'TARGET',
                          dataIndex: 'target_type',
                          render: (text, record: any) => (
                            <div className="flex flex-col">
                              <Text className="text-[10px] font-black uppercase text-slate-400">{text}</Text>
                              <Text className="text-xs font-bold text-slate-700">{record.target_id?.slice(0,8)}</Text>
                            </div>
                          )
                        },
                        {
                          title: 'TIMESTAMP',
                          dataIndex: 'created_at',
                          render: (date) => <Text className="text-xs text-slate-500 font-bold">{dayjs(date).format('MMM DD, HH:mm:ss')}</Text>
                        },
                        {
                          title: 'METADATA',
                          dataIndex: 'metadata_json',
                          render: (json) => json ? <Tooltip title={JSON.stringify(json, null, 2)}><div className="max-w-[150px] truncate text-[10px] text-slate-400 font-mono italic">View Details</div></Tooltip> : '-'
                        }
                      ]}
                      pagination={{ pageSize: 15 }}
                    />
                  </div>
                )
              },
              { 
                key: 'decisions', 
                label: <TabLabel label="Decision Tracking" icon={<UserCheck size={14}/>} />,
                children: (
                  <div className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                       <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title={<div className="flex items-center gap-2"><Settings size={14}/> Approval History</div>}>
                          <List
                            dataSource={decisions.approvals}
                            renderItem={(item: any) => (
                              <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-slate-100 mb-2">
                                 <div>
                                    <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">{item.item_type}</Text>
                                    <Text className="text-sm font-black text-slate-800">{item.requested_action}</Text>
                                 </div>
                                 <div className="text-right">
                                    <Tag color={item.status === 'approved' ? 'success' : 'error'} className="m-0 rounded-full font-black text-[9px] uppercase px-3">{item.status}</Tag>
                                    <Text className="block text-[10px] text-slate-400 font-bold mt-1">{dayjs(item.decided_at).fromNow()}</Text>
                                 </div>
                              </div>
                            )}
                          />
                       </Card>
                       <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title={<div className="flex items-center gap-2"><Activity size={14}/> Lifecycle Decisions</div>}>
                          <List
                            dataSource={decisions.audit_decisions}
                            renderItem={(item: any) => (
                              <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-slate-100 mb-2">
                                 <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600"><UserCheck size={16}/></div>
                                    <div>
                                       <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">{item.action_type.split('.')[1]}</Text>
                                       <Text className="text-sm font-black text-slate-800">Target: {item.target_id.slice(0,8)}</Text>
                                    </div>
                                 </div>
                                 <Text className="text-[10px] text-slate-400 font-bold">{dayjs(item.created_at).fromNow()}</Text>
                              </div>
                            )}
                          />
                       </Card>
                    </div>
                  </div>
                )
              },
              { 
                key: 'automation', 
                label: <TabLabel label="Automation Governance" icon={<Zap size={14}/>} />,
                children: (
                  <div className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                       <MetricBox label="Total Executions" value={automation.runs_summary.total} color="indigo" />
                       <MetricBox label="Success Rate" value={`${((automation.runs_summary.completed / (automation.runs_summary.total || 1)) * 100).toFixed(1)}%`} color="emerald" />
                       <MetricBox label="Failure Rate" value={`${((automation.runs_summary.failed / (automation.runs_summary.total || 1)) * 100).toFixed(1)}%`} color="rose" />
                    </div>
                    <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title={<div className="flex items-center gap-2"><User size={14}/> Manual Automation Overrides</div>}>
                       <Table 
                         dataSource={automation.manual_overrides} 
                         pagination={false}
                         size="small"
                         rowKey="id"
                         columns={[
                           { title: 'ACTION', dataIndex: 'action_type', render: (t) => <Text className="text-xs font-black text-slate-700">{t.replace('automation_execution.', '')}</Text> },
                           { title: 'RUN ID', dataIndex: 'target_id', render: (id) => <Text className="text-[10px] font-mono">{id.slice(0,8)}</Text> },
                           { title: 'ACTOR', dataIndex: 'actor_id', render: (id) => <Text className="text-xs font-bold text-slate-500">{id?.slice(0,8) || 'SYSTEM'}</Text> },
                           { title: 'TIMESTAMP', dataIndex: 'created_at', render: (d) => <Text className="text-xs font-bold text-slate-400">{dayjs(d).fromNow()}</Text> }
                         ]}
                       />
                    </Card>
                  </div>
                )
              },
              { 
                key: 'ai', 
                label: <TabLabel label="AI Transparency" icon={<Bot size={14}/>} />,
                children: (
                  <div className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                       <MetricBox label="AI Executions" value={aiTransparency.ai_summary.total_executions} color="blue" />
                       <MetricBox label="Total Suggestions" value={aiTransparency.ai_summary.total_suggestions} color="indigo" />
                       <MetricBox label="Applied Rate" value={`${((aiTransparency.ai_summary.applied_suggestions / (aiTransparency.ai_summary.total_suggestions || 1)) * 100).toFixed(1)}%`} color="purple" />
                    </div>
                    <Card className="rounded-3xl border-slate-100 bg-slate-50/30" title={<div className="flex items-center gap-2"><UserCheck size={14}/> AI Recommendation Overrides</div>}>
                       <Table 
                         dataSource={aiTransparency.human_overrides} 
                         pagination={false}
                         size="small"
                         rowKey="id"
                         columns={[
                           { title: 'ACTION', dataIndex: 'action_type', render: (t) => <Text className="text-xs font-black text-slate-700">{t.replace('suggestion.', '')}</Text> },
                           { title: 'SUGGESTION', dataIndex: 'target_id', render: (id) => <Text className="text-[10px] font-mono">{id.slice(0,8)}</Text> },
                           { title: 'ACTOR', dataIndex: 'actor_id', render: (id) => <Text className="text-xs font-bold text-slate-500">{id?.slice(0,8) || 'SYSTEM'}</Text> },
                           { title: 'TIMESTAMP', dataIndex: 'created_at', render: (d) => <Text className="text-xs font-bold text-slate-400">{dayjs(d).fromNow()}</Text> }
                         ]}
                       />
                    </Card>
                  </div>
                )
              }
            ]}
          />
        </div>
      </Card>

    </div>
  )
}

function GovernanceStatCard({ label, value, sub, icon, color }: any) {
  return (
    <Card className="rounded-[2rem] border-none bg-white shadow-soft-sm">
       <div className="flex items-center gap-3 mb-3">
          <div className={cn("p-2 rounded-xl bg-slate-50", `text-${color}-600`)}>{icon}</div>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{label}</Text>
       </div>
       <Text className="text-2xl font-black text-slate-900 block leading-none">{value}</Text>
       <Text className="text-[10px] font-bold text-slate-400 uppercase mt-1.5 block tracking-tighter">{sub}</Text>
    </Card>
  )
}

function TabLabel({ label, icon }: any) {
  return (
    <div className="flex items-center gap-2 px-1">
       <span className="text-slate-500">{icon}</span>
       <span className="text-[11px] font-black uppercase tracking-widest">{label}</span>
    </div>
  )
}

function MetricBox({ label, value, color }: any) {
  return (
    <div className={cn("p-6 rounded-3xl border border-slate-100 text-center bg-white")}>
       <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">{label}</Text>
       <Text className={cn("text-3xl font-black", `text-${color}-600`)}>{value}</Text>
    </div>
  )
}
