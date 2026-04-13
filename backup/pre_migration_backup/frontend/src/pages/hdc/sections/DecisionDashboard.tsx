import React from 'react'
import { Card, Table, Tag, Typography, Button, Statistic, Row, Col, Spin, Alert, Divider } from 'antd'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { hdcApi } from '@/api/hdc'
import { useAuthStore } from '@/store/authStore'
import { Activity, Users, Zap, Briefcase, ListChecks, ArrowRight, History, ShieldCheck, CheckCircle2 } from 'lucide-react'
import { cn } from '@/utils/cn'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const { Text } = Typography

export default function DecisionDashboard() {
  const navigate = useNavigate()
  const user = useAuthStore(state => state.user)
  const [searchParams] = useSearchParams()
  const applicationIdFromUrl = searchParams.get('applicationId')

  const { data: statsData, isLoading: loadingStats, isError: errorStats } = useApiQuery(
    ['hdc-global-stats'],
    hdcApi.getStats
  )

  const stats = (statsData as any)?.data?.stats || {}
  const recentTasks = (statsData as any)?.data?.recent_tasks || []

  if (loadingStats) {
    return <div className="py-20 text-center"><Spin size="large" tip="Synchronizing Decision Data..." /></div>
  }

  if (errorStats) {
    return <Alert type="error" message="Failed to load HDC pulse. Please refresh." showIcon className="my-8" />
  }

  return (
    <div className="space-y-10">
      {/* ─── Decision Lifecycle Diagram ─── */}
      <Card className="rounded-[2.5rem] border-none bg-slate-50 shadow-inner overflow-hidden relative">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-8 relative z-10">
          {[
            { label: 'Committee', icon: <Users size={16} />, color: 'blue' },
            { label: 'Approval', icon: <ShieldCheck size={16} />, color: 'indigo' },
            { label: 'Comp Planning', icon: <Activity size={16} />, color: 'purple' },
            { label: 'Negotiation', icon: <Zap size={16} />, color: 'amber' },
            { label: 'Offer Release', icon: <Briefcase size={16} />, color: 'emerald' },
            { label: 'Acceptance', icon: <CheckCircle2 size={16} />, color: 'green' },
          ].map((step, idx, arr) => (
            <React.Fragment key={step.label}>
              <div className="flex flex-col items-center gap-3">
                <div className={cn(
                  "h-12 w-12 rounded-2xl flex items-center justify-center border-2 shadow-sm transition-transform hover:scale-110",
                  `bg-${step.color}-50 border-${step.color}-200 text-${step.color}-600`
                )}>
                  {step.icon}
                </div>
                <Text className={cn("text-[9px] font-black uppercase tracking-widest", `text-${step.color}-600`)}>{step.label}</Text>
              </div>
              {idx < arr.length - 1 && (
                <div className="hidden md:block opacity-20">
                  <ArrowRight size={20} className="text-slate-400" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </Card>

      {/* ─── Executive Metrics ─── */}
      <Row gutter={24}>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm border-b-4 border-b-blue-500 overflow-hidden relative">
            <div className="absolute -right-2 -bottom-2 opacity-5"><Users size={80} /></div>
            <Statistic
              title={<Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">Active Committees</Text>}
              value={stats.pending_committee || 0}
              valueStyle={{ fontWeight: 900, color: '#1e293b' }}
              prefix={<Users className="mr-2 h-4 w-4 text-blue-500" />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm border-b-4 border-b-purple-500 overflow-hidden relative">
            <div className="absolute -right-2 -bottom-2 opacity-5"><Activity size={80} /></div>
            <Statistic
              title={<Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">Offer Modeling</Text>}
              value={stats.scenario_modeling || 0}
              valueStyle={{ fontWeight: 900, color: '#1e293b' }}
              prefix={<Activity className="mr-2 h-4 w-4 text-purple-500" />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm border-b-4 border-b-amber-500 overflow-hidden relative">
            <div className="absolute -right-2 -bottom-2 opacity-5"><Zap size={80} /></div>
            <Statistic
              title={<Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">Ready for Release</Text>}
              value={stats.ready_for_release || 0}
              valueStyle={{ fontWeight: 900, color: '#1e293b' }}
              prefix={<Zap className="mr-2 h-4 w-4 text-amber-500" />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-3xl border-slate-200 shadow-sm border-b-4 border-b-green-500 overflow-hidden relative">
            <div className="absolute -right-2 -bottom-2 opacity-5"><Briefcase size={80} /></div>
            <Statistic
              title={<Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">Awaiting Joining</Text>}
              value={stats.awaiting_joining || 0}
              valueStyle={{ fontWeight: 900, color: '#1e293b' }}
              prefix={<Briefcase className="mr-2 h-4 w-4 text-green-500" />}
            />
          </Card>
        </Col>
      </Row>

      {/* ─── Operational Feed ─── */}
      <Card
        className="rounded-[2.5rem] border-slate-200 shadow-sm"
        title={
          <div className="flex items-center gap-2 py-2">
            <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600"><History size={18} /></div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 leading-none mb-1">Decision Pipeline</div>
              <div className="text-base font-black text-slate-800 leading-none">Recent Action Items</div>
            </div>
          </div>
        }
      >
        {recentTasks.length === 0 ? (
          <EmptyPanel icon={<ListChecks size={48} />} message="Everything caught up. No pending decision tasks." />
        ) : (
          <Table
            pagination={false}
            dataSource={recentTasks}
            rowKey="id"
            columns={[
              {
                title: 'Task Type',
                dataIndex: 'type',
                width: 150,
                render: (t: string) => (
                  <Tag className="rounded-full border-none bg-slate-100 text-slate-600 font-black text-[9px] uppercase px-3 py-0.5">
                    {t}
                  </Tag>
                )
              },
              {
                title: 'Title',
                dataIndex: 'title',
                render: (title: string) => <Text strong className="text-sm text-slate-700">{title}</Text>
              },
              {
                title: 'Status',
                dataIndex: 'status',
                render: (s: string) => <Tag color="blue" className="rounded-md font-bold text-[10px] uppercase border-none px-2">{s}</Tag>
              },
              {
                title: 'Timeline',
                dataIndex: 'created_at',
                render: (d: string) => <Text className="text-xs text-slate-400">{dayjs(d).fromNow()}</Text>
              },
              {
                title: '',
                key: 'action',
                align: 'right',
                render: (_: any, record: any) => {
                  let route = '/hiring-decisions'
                  if (record.type === 'committee') route = '/hiring-decisions/committee'
                  else if (record.type === 'approval') route = '/hiring-decisions/approvals'
                  else if (record.type === 'release') route = '/hiring-decisions/offer-release'
                  
                  return (
                    <Button 
                      icon={<ArrowRight size={14} />} 
                      type="text" 
                      className="text-indigo-600 hover:bg-indigo-50 font-bold"
                      onClick={() => navigate(`${route}?applicationId=${record.application_id}`)}
                    >
                      Process
                    </Button>
                  )
                }
              }
            ]}
          />
        )}
      </Card>
    </div>
  )
}

function EmptyPanel({ icon, message }: { icon: React.ReactNode; message: string }) {
  return (
    <div className="py-16 text-center flex flex-col items-center gap-4">
      <div className="text-slate-100">{icon}</div>
      <Text className="block font-bold text-slate-400 max-w-xs">{message}</Text>
    </div>
  )
}
