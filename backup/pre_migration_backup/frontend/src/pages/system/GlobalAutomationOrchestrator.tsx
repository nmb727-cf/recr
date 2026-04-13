import React, { useState } from 'react'
import { Typography, Card, Statistic, Tag, Table, Spin, Alert, Empty, Progress, Tabs } from 'antd'
import { BrainCircuit, Activity, AlertTriangle, Zap, CheckCircle2, XCircle, Clock, FileText, Settings2, Users } from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { automationApi } from '@/api/automation'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function GlobalAutomationOrchestrator() {
  const [activeTab, setActiveTab] = useState('inventory')

  const { data, isLoading, error } = useApiQuery(
    ['automation-orchestrator'],
    () => automationApi.getOrchestratorDashboard(),
    { refetchOnWindowFocus: false, staleTime: 30000 }
  )

  const dashboard = (data as any)?.orchestrator || (data as any)?.data?.orchestrator

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Loading Global Automation Orchestrator..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert type="error" showIcon message="Failed to load Orchestrator Data" description={(error as any)?.message} />
      </div>
    )
  }

  if (!dashboard) {
    return <Empty className="my-16" description="No Orchestrator Data Available" />
  }

  const { overview, inventory, execution_activity, failed_blocked, coverage, manual_review_queue } = dashboard

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'success': return <Tag className="border-emerald-200 bg-emerald-50 text-emerald-700 m-0"><CheckCircle2 size={12} className="inline mr-1" />Success</Tag>
      case 'failed': return <Tag className="border-rose-200 bg-rose-50 text-rose-700 m-0"><XCircle size={12} className="inline mr-1" />Failed</Tag>
      case 'skipped': return <Tag className="border-amber-200 bg-amber-50 text-amber-700 m-0"><AlertTriangle size={12} className="inline mr-1" />Skipped</Tag>
      default: return <Tag>{status}</Tag>
    }
  }

  return (
    <div className="mx-auto max-w-[1560px] p-6 lg:p-8 flex flex-col gap-6">
      
      {/* ─── Header ─── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <Text className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Intelligence / Automation</Text>
          <div className="flex items-center gap-3 mt-1">
             <div className="bg-indigo-600 text-white p-2 rounded-xl shadow-soft-sm">
               <BrainCircuit size={24} />
             </div>
             <Title level={2} className="!m-0 tracking-tight text-slate-900">Global Automation Orchestrator</Title>
          </div>
          <Text className="text-sm text-slate-500 mt-2 block">Cross-module execution layer for Jobs, Pipeline, Agencies, and AI recommendations.</Text>
        </div>
        <Tag className="rounded-full bg-indigo-50 border-indigo-100 text-indigo-700 px-4 py-1 flex items-center gap-1.5 text-[11px] font-black uppercase tracking-widest shadow-sm">
          <Activity size={14} className="animate-pulse" /> Live Monitoring
        </Tag>
      </div>

      {/* ─── Overview Metrics ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card className="rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-2 text-indigo-600">
             <Settings2 size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-indigo-400">Active Rules</Text>
          </div>
          <Statistic value={overview.active_rules} suffix={`/ ${overview.total_rules}`} valueStyle={{ fontWeight: 900, color: '#1e293b' }} />
        </Card>
        
        <Card className="rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-2 text-emerald-600">
             <Activity size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-emerald-400">Execution Success</Text>
          </div>
          <Statistic value={overview.success_rate} suffix="%" valueStyle={{ fontWeight: 900, color: '#1e293b' }} />
        </Card>

        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-rose-50/50 to-white">
          <div className="flex items-center gap-3 mb-2 text-rose-600">
             <AlertTriangle size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-rose-400">Failed Executions</Text>
          </div>
          <Statistic value={overview.failed_executions} valueStyle={{ fontWeight: 900, color: '#be123c' }} />
        </Card>

        <Card className="rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-2 text-blue-600">
             <Users size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-blue-400">Manual Reviews</Text>
          </div>
          <Statistic value={manual_review_queue.length} valueStyle={{ fontWeight: 900, color: '#1e293b' }} />
        </Card>
      </div>

      {/* ─── Coverage & Health ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-3xl shadow-sm border border-slate-200" title={<Text className="text-[11px] font-black uppercase tracking-[0.15em] text-slate-500">Job Automation Coverage</Text>}>
           <div className="flex flex-col gap-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Text className="font-bold text-slate-700">Jobs with Active Automation</Text>
                  <Text className="font-black text-indigo-600">{coverage.automation_coverage_pct}%</Text>
                </div>
                <Progress percent={coverage.automation_coverage_pct} showInfo={false} strokeColor="#4f46e5" trailColor="#f1f5f9" />
                <Text className="text-xs text-slate-400">{coverage.jobs_with_automation} of {coverage.total_active_jobs} active requisitions</Text>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Text className="font-bold text-slate-700">Jobs with SLA Reminders</Text>
                  <Text className="font-black text-emerald-600">{coverage.sla_coverage_pct}%</Text>
                </div>
                <Progress percent={coverage.sla_coverage_pct} showInfo={false} strokeColor="#059669" trailColor="#f1f5f9" />
                <Text className="text-xs text-slate-400">{coverage.jobs_with_sla} of {coverage.total_active_jobs} active requisitions</Text>
              </div>
           </div>
        </Card>
        
        <Card className="rounded-3xl shadow-sm border border-rose-200 bg-rose-50/20" title={<Text className="text-[11px] font-black uppercase tracking-[0.15em] text-rose-500">Blocked / Failed Automations</Text>}>
           {failed_blocked.length > 0 ? (
             <div className="space-y-3 max-h-[180px] overflow-y-auto custom-scrollbar pr-2">
                {failed_blocked.map((fail: any, idx: number) => (
                  <div key={idx} className="p-3 bg-white border border-rose-100 rounded-2xl flex items-start gap-3">
                     <XCircle className="text-rose-500 mt-0.5 shrink-0" size={16} />
                     <div className="min-w-0 flex-1">
                        <div className="flex justify-between items-center mb-1">
                           <Text className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{fail.trigger_event}</Text>
                           <Text className="text-[10px] text-slate-400 font-medium">{dayjs(fail.executed_at).fromNow()}</Text>
                        </div>
                        <Text className="text-sm font-medium text-slate-800 truncate block">{fail.error_message || 'Unknown execution error'}</Text>
                        <Text className="text-[10px] text-rose-500 font-bold uppercase mt-1 block tracking-wider">Entity: {fail.entity_type}</Text>
                     </div>
                  </div>
                ))}
             </div>
           ) : (
             <div className="h-[150px] flex flex-col items-center justify-center text-center">
                <CheckCircle2 size={32} className="text-emerald-400 mb-2" />
                <Text className="text-emerald-700 font-bold block">No Failed Automations</Text>
                <Text className="text-emerald-500 text-xs">All systems operational</Text>
             </div>
           )}
        </Card>
      </div>

      {/* ─── Detailed Tabs ─── */}
      <Card className="rounded-3xl shadow-sm border border-slate-200" bodyStyle={{ padding: '0 24px 24px 24px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} size="large" tabBarGutter={24}>
           
           <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Automation Registry</span>} key="inventory">
              <Table 
                dataSource={inventory} 
                rowKey="id"
                pagination={{ pageSize: 10 }}
                columns={[
                  { 
                    title: 'Name', 
                    dataIndex: 'name', 
                    render: (text, record: any) => (
                      <div>
                        <Text className="font-bold text-slate-800 text-sm block">{text}</Text>
                        <Text className="text-[10px] uppercase font-black tracking-widest text-indigo-500">{record.trigger_event}</Text>
                      </div>
                    )
                  },
                  { 
                    title: 'Status', 
                    dataIndex: 'is_active', 
                    render: (isActive) => <Tag color={isActive ? 'green' : 'default'} className="uppercase font-bold tracking-widest text-[9px]">{isActive ? 'Active' : 'Inactive'}</Tag>
                  },
                  { title: 'Actions Set', dataIndex: 'actions_count', render: (c) => <Text className="font-bold text-slate-600">{c} Actions</Text> },
                  { title: 'Executions', dataIndex: 'execution_count', render: (c) => <Text className="font-black text-slate-700">{c}</Text> },
                  { title: 'Last Run', dataIndex: 'last_executed_at', render: (date) => date ? <Text className="text-xs text-slate-500"><Clock size={12} className="inline mr-1 -mt-0.5" />{dayjs(date).format('MMM D, YYYY HH:mm')}</Text> : 'Never' },
                ]}
              />
           </Tabs.TabPane>

           <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Execution Logs</span>} key="activity">
              <Table 
                dataSource={execution_activity} 
                rowKey="id"
                pagination={{ pageSize: 10 }}
                columns={[
                  { title: 'Status', dataIndex: 'status', render: getStatusTag },
                  { 
                    title: 'Trigger Event', 
                    dataIndex: 'trigger_event',
                    render: (t) => <Text className="text-xs font-bold text-slate-700">{t}</Text>
                  },
                  { 
                    title: 'Target Entity', 
                    render: (_, record: any) => (
                      <Text className="text-[11px] text-slate-500 font-medium">
                         <span className="uppercase font-bold text-slate-400 mr-1 tracking-wider">{record.entity_type}</span>
                         {record.entity_id ? record.entity_id.slice(0, 8) + '...' : '-'}
                      </Text>
                    )
                  },
                  { title: 'Details', dataIndex: 'error_message', render: (e) => e ? <Text className="text-xs text-rose-500">{e}</Text> : <Text className="text-xs text-emerald-600 font-medium">Executed cleanly</Text> },
                  { title: 'Timestamp', dataIndex: 'executed_at', render: (d) => <Text className="text-xs text-slate-500">{dayjs(d).format('MMM D, HH:mm:ss')}</Text> }
                ]}
              />
           </Tabs.TabPane>

           <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Manual Review Queue <Tag className="ml-2 bg-slate-100">{manual_review_queue.length}</Tag></span>} key="reviews">
              {manual_review_queue.length > 0 ? (
                <Table 
                  dataSource={manual_review_queue} 
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                  columns={[
                    { 
                      title: 'Action Required', 
                      dataIndex: 'action_required',
                      render: (text) => <Text className="font-bold text-slate-800 block text-sm">{text}</Text>
                    },
                    { 
                      title: 'Entity', 
                      dataIndex: 'entity_type',
                      render: (type) => <Tag className="uppercase font-bold tracking-widest text-[9px]">{type}</Tag>
                    },
                    { 
                      title: 'SLA Overdue', 
                      dataIndex: 'deadline_at',
                      render: (date) => <Text className="text-xs font-bold text-amber-600"><AlertTriangle size={12} className="inline mr-1" />{dayjs(date).fromNow()}</Text>
                    }
                  ]}
                />
              ) : (
                <div className="py-16 text-center">
                  <div className="h-16 w-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 size={32} className="text-emerald-500" />
                  </div>
                  <Title level={4} className="!m-0 text-slate-700">Inbox Zero</Title>
                  <Text className="text-slate-500 block mt-1">No automations require manual review or intervention right now.</Text>
                </div>
              )}
           </Tabs.TabPane>
        </Tabs>
      </Card>
      
    </div>
  )
}
