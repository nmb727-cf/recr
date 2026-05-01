import React, { useState } from 'react'
import { Typography, Card, Statistic, Tag, Table, Spin, Alert, Empty, Progress, Tabs, Button, message } from 'antd'
import { 
  BrainCircuit, 
  Activity, 
  AlertTriangle, 
  Zap, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert, 
  Settings2, 
  Users,
  ThumbsUp,
  ThumbsDown,
  ArrowRight
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { automationApi } from '@/api/automation'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function AutonomousHiringEngine() {
  const [activeTab, setActiveTab] = useState('suggestions')
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useApiQuery(
    ['autonomous-hiring-engine'],
    () => automationApi.getAutonomousEngine(),
    { refetchOnWindowFocus: false, staleTime: 30000 }
  )

  const actionMutation = useMutation({
    mutationFn: ({ id, action, item_type }: { id: string, action: 'approve' | 'reject', item_type: 'suggestion' | 'approval' }) => 
      automationApi.updateAutonomousAction(id, { action, item_type }),
    onSuccess: (data, variables) => {
      message.success(`Action successfully ${variables.action}d`)
      queryClient.invalidateQueries({ queryKey: ['autonomous-hiring-engine'] })
    },
    onError: (err: any) => {
      message.error(err?.message || 'Failed to process action')
    }
  })

  const dashboard = (data as any)?.autonomous || (data as any)?.data?.autonomous

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Loading Autonomous Hiring Engine..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert type="error" showIcon message="Failed to load Autonomous Engine" description={(error as any)?.message} />
      </div>
    )
  }

  if (!dashboard) {
    return <Empty className="my-16" description="No Autonomous Data Available" />
  }

  const { overview, suggested_actions, pending_approvals, executed_actions, settings } = dashboard

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
          <Text className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Intelligence / AI / Automation</Text>
          <div className="flex items-center gap-3 mt-1">
             <div className="bg-indigo-600 text-white p-2 rounded-xl shadow-soft-sm">
               <BrainCircuit size={24} />
             </div>
             <Title level={2} className="!m-0 tracking-tight text-slate-900">Autonomous Hiring Engine</Title>
          </div>
          <Text className="text-sm text-slate-500 mt-2 block">Human-in-the-Loop control layer for safe AI-driven autonomous actions.</Text>
        </div>
        <Tag className="rounded-full bg-emerald-50 border-emerald-100 text-emerald-700 px-4 py-1 flex items-center gap-1.5 text-[11px] font-black uppercase tracking-widest shadow-sm">
          <Activity size={14} className="animate-pulse" /> Active Guardrails
        </Tag>
      </div>

      {/* ─── Overview Metrics ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-indigo-50/50 to-white">
          <div className="flex items-center gap-3 mb-2 text-indigo-600">
             <Zap size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-indigo-400">Suggested Actions</Text>
          </div>
          <Statistic value={overview.pending_suggestions} valueStyle={{ fontWeight: 900, color: '#3730a3' }} />
        </Card>
        
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-amber-50/50 to-white">
          <div className="flex items-center gap-3 mb-2 text-amber-600">
             <ShieldAlert size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-amber-400">Pending Approvals</Text>
          </div>
          <Statistic value={overview.pending_approvals} valueStyle={{ fontWeight: 900, color: '#92400e' }} />
        </Card>

        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-emerald-50/50 to-white">
          <div className="flex items-center gap-3 mb-2 text-emerald-600">
             <CheckCircle2 size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-emerald-400">Executed Today</Text>
          </div>
          <Statistic value={overview.executed_today} valueStyle={{ fontWeight: 900, color: '#065f46' }} />
        </Card>

        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-blue-50/50 to-white">
          <div className="flex items-center gap-3 mb-2 text-blue-600">
             <Settings2 size={18} />
             <Text className="text-[10px] font-black uppercase tracking-[0.1em] text-blue-400">Jobs Auto-Enabled</Text>
          </div>
          <Statistic value={overview.jobs_auto_enabled} suffix={`/ ${overview.total_active_jobs}`} valueStyle={{ fontWeight: 900, color: '#1e3a8a' }} />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
        
        {/* ─── Detailed Tabs ─── */}
        <Card className="rounded-3xl shadow-sm border border-slate-200" bodyStyle={{ padding: '0 24px 24px 24px' }}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} size="large" tabBarGutter={24}>
            
            <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Suggested Actions <Tag className="ml-2 bg-indigo-50 text-indigo-600">{suggested_actions.length}</Tag></span>} key="suggestions">
                {suggested_actions.length > 0 ? (
                  <div className="space-y-4">
                    {suggested_actions.map((action: any) => (
                      <div key={action.id} className="p-4 border border-slate-200 rounded-2xl flex items-start gap-4 bg-white hover:border-indigo-200 transition-all shadow-soft-sm">
                        <div className="bg-indigo-50 text-indigo-600 p-2 rounded-xl mt-0.5">
                          <BrainCircuit size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <Text className="text-sm font-black text-slate-800">{action.title}</Text>
                            <Tag className="m-0 uppercase font-black tracking-widest text-[9px] bg-slate-100 border-none">{action.category}</Tag>
                          </div>
                          <Text className="block text-xs text-slate-500 mb-3">{action.summary}</Text>
                          <div className="flex items-center justify-between">
                            <Text className="text-[10px] font-bold text-slate-400"><Clock size={12} className="inline mr-1" />{dayjs(action.created_at).fromNow()}</Text>
                            <div className="flex gap-2">
                              <Button 
                                size="small" 
                                type="text" 
                                danger 
                                className="text-[10px] font-black uppercase tracking-widest bg-rose-50"
                                onClick={() => actionMutation.mutate({ id: action.id, action: 'reject', item_type: 'suggestion' })}
                                loading={actionMutation.isPending}
                              >
                                Reject
                              </Button>
                              <Button 
                                size="small" 
                                type="primary" 
                                className="text-[10px] font-black uppercase tracking-widest bg-indigo-600"
                                onClick={() => actionMutation.mutate({ id: action.id, action: 'approve', item_type: 'suggestion' })}
                                loading={actionMutation.isPending}
                              >
                                Approve
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty className="my-12" description="No AI suggested actions currently." />
                )}
            </Tabs.TabPane>

            <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Pending Approvals <Tag className="ml-2 bg-amber-50 text-amber-600">{pending_approvals.length}</Tag></span>} key="approvals">
                {pending_approvals.length > 0 ? (
                  <div className="space-y-4">
                    {pending_approvals.map((approval: any) => (
                      <div key={approval.id} className="p-4 border border-amber-200 rounded-2xl flex items-start gap-4 bg-amber-50/30 hover:bg-amber-50/60 transition-all shadow-soft-sm">
                        <div className="bg-amber-100 text-amber-600 p-2 rounded-xl mt-0.5">
                          <ShieldAlert size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <Text className="text-sm font-black text-slate-800">{approval.requested_action}</Text>
                            <Tag className="m-0 uppercase font-black tracking-widest text-[9px] bg-white border-amber-200 text-amber-700">Approval Required</Tag>
                          </div>
                          <Text className="block text-xs text-slate-500 mb-2">
                            <span className="font-bold text-slate-600">Item Type:</span> {approval.item_type} <br/>
                            <span className="font-bold text-slate-600">Recommended Decision:</span> {approval.recommended_decision}
                          </Text>
                          <div className="flex items-center justify-between mt-3">
                            <Text className="text-[10px] font-bold text-slate-400"><Clock size={12} className="inline mr-1" />{dayjs(approval.created_at).fromNow()}</Text>
                            <div className="flex gap-2">
                              <Button 
                                size="small" 
                                type="text" 
                                danger 
                                className="text-[10px] font-black uppercase tracking-widest bg-rose-50"
                                onClick={() => actionMutation.mutate({ id: approval.id, action: 'reject', item_type: 'approval' })}
                                loading={actionMutation.isPending}
                              >
                                <ThumbsDown size={14} className="mr-1" /> Reject
                              </Button>
                              <Button 
                                size="small" 
                                type="primary" 
                                className="text-[10px] font-black uppercase tracking-widest bg-emerald-600 border-none"
                                onClick={() => actionMutation.mutate({ id: approval.id, action: 'approve', item_type: 'approval' })}
                                loading={actionMutation.isPending}
                              >
                                <ThumbsUp size={14} className="mr-1" /> Approve
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty className="my-12" description="No actions waiting for approval." />
                )}
            </Tabs.TabPane>

            <Tabs.TabPane tab={<span className="font-bold tracking-tight uppercase text-[11px]">Executed Actions</span>} key="executed">
                <Table 
                  dataSource={executed_actions} 
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                  columns={[
                    { title: 'Status', dataIndex: 'status', render: getStatusTag },
                    { title: 'Action Name', dataIndex: 'action_name', render: (t) => <Text className="text-xs font-bold text-slate-700">{t}</Text> },
                    { title: 'Entity Type', dataIndex: 'entity_type', render: (t) => <Tag className="uppercase font-bold tracking-widest text-[9px]">{t}</Tag> },
                    { title: 'Details', dataIndex: 'error_message', render: (e) => e ? <Text className="text-xs text-rose-500">{e}</Text> : <Text className="text-xs text-emerald-600 font-medium">Auto-executed</Text> },
                    { title: 'Timestamp', dataIndex: 'executed_at', render: (d) => <Text className="text-xs text-slate-500">{dayjs(d).format('MMM D, HH:mm:ss')}</Text> }
                  ]}
                />
            </Tabs.TabPane>

          </Tabs>
        </Card>

        {/* ─── Right Column: Settings & Guardrails ─── */}
        <div className="flex flex-col gap-6">
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Automation Guardrails</span>}>
            
            <div className="mb-6">
              <Text className="text-[10px] font-black text-emerald-600 uppercase tracking-widest flex items-center gap-1 mb-2"><CheckCircle2 size={12}/> Safe Automation</Text>
              <div className="space-y-1.5 border-l-2 border-emerald-200 pl-3">
                {settings.safe_automation.map((item: string, i: number) => (
                  <Text key={i} className="block text-xs font-bold text-slate-600">{item}</Text>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <Text className="text-[10px] font-black text-amber-600 uppercase tracking-widest flex items-center gap-1 mb-2"><ShieldAlert size={12}/> Approval Required</Text>
              <div className="space-y-1.5 border-l-2 border-amber-200 pl-3">
                {settings.approval_required.map((item: string, i: number) => (
                  <Text key={i} className="block text-xs font-bold text-slate-600">{item}</Text>
                ))}
              </div>
            </div>

            <div>
              <Text className="text-[10px] font-black text-rose-600 uppercase tracking-widest flex items-center gap-1 mb-2"><XCircle size={12}/> Manual Only</Text>
              <div className="space-y-1.5 border-l-2 border-rose-200 pl-3">
                {settings.manual_only.map((item: string, i: number) => (
                  <Text key={i} className="block text-xs font-bold text-slate-600">{item}</Text>
                ))}
              </div>
            </div>

          </Card>
        </div>

      </div>

    </div>
  )
}
