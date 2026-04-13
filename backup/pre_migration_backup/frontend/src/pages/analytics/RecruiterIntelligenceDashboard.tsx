import React from 'react'
import {
  Card, Row, Col, Typography, Statistic, Spin, Empty, Badge, Avatar, Progress, Table, Tag
} from 'antd'
import {
  Activity, Briefcase, Users, Calendar, Clock, AlertTriangle, TrendingUp, Layers,
  Target, Zap, ShieldCheck, UserCheck, Building2, BarChart3, ChevronRight, CheckCircle
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

export default function RecruiterIntelligenceDashboard() {
  const { data: res, isLoading } = useApiQuery(
    ['recruiter-intelligence'],
    () => analyticsApi.recruiterIntelligence()
  )

  const intelligence = (res as any)?.data ?? res

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Spin size="large" tip="Loading Recruiter Intelligence..." />
      </div>
    )
  }

  if (!intelligence || !intelligence.team_performance) {
    return (
      <div className="p-12">
        <Empty description="No recruiter intelligence data available yet" />
      </div>
    )
  }

  const { team_performance, workload_overview, job_recommendations } = intelligence

  return (
    <div className="max-w-[1600px] mx-auto p-8 space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between mb-2">
        <div>
          <Title level={2} className="!m-0 uppercase tracking-tighter font-black text-slate-900">
            Recruiter Intelligence & Automation
          </Title>
          <Text className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">
            Performance, Workload, and Smart Assignments
          </Text>
        </div>
      </div>

      {/* ── Overview ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Active Handled Candidates', value: workload_overview.total_active_candidates, icon: <Users size={20} className="text-indigo-600" /> },
          { label: 'Overloaded Recruiters', value: workload_overview.overloaded_count, icon: <AlertTriangle size={20} className="text-rose-600" /> },
          { label: 'Balanced Recruiters', value: workload_overview.balanced_count, icon: <CheckCircle size={20} className="text-emerald-600" /> },
          { label: 'Underutilized Recruiters', value: workload_overview.underutilized_count, icon: <Clock size={20} className="text-amber-600" /> },
        ].map((stat, i) => (
          <Card key={i} className="rounded-2xl border-none shadow-soft-sm hover:shadow-md transition-all">
            <div className="p-2 w-fit rounded-xl mb-2 bg-slate-50">
              {stat.icon}
            </div>
            <Statistic 
              title={<span className="text-[10px] font-black text-slate-400 uppercase tracking-tight">{stat.label}</span>} 
              value={stat.value} 
              valueStyle={{ fontWeight: 900, color: '#1e293b' }}
            />
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ── Recruiter Performance ───────────────────────────────────────────── */}
        <Card 
          className="lg:col-span-8 rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-500" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Recruiter Performance & Workload</span>
            </div>
          }
        >
          <Table 
            dataSource={team_performance}
            pagination={false}
            size="small"
            rowKey="user_id"
            columns={[
              {
                title: 'Recruiter',
                dataIndex: 'full_name',
                render: (text) => (
                  <div className="flex items-center gap-2">
                    <Avatar size="small" className="bg-indigo-100 text-indigo-600 font-bold">{text[0]}</Avatar>
                    <div>
                      <Text className="text-[11px] font-black text-slate-700 block">{text}</Text>
                    </div>
                  </div>
                )
              },
              {
                title: 'Workload',
                dataIndex: 'workload',
                render: (wl) => (
                  <div>
                    <Tag className={cn(
                      "rounded-full font-black text-[9px] uppercase border-none mb-1",
                      wl.workload_status === 'overloaded' ? "bg-rose-100 text-rose-600" :
                      wl.workload_status === 'underutilized' ? "bg-amber-100 text-amber-600" :
                      "bg-emerald-100 text-emerald-600"
                    )}>
                      {wl.workload_status}
                    </Tag>
                    <Text className="text-[10px] block text-slate-500">{wl.active_candidates} Active / {wl.overdue_actions} Overdue</Text>
                  </div>
                )
              },
              {
                title: 'Jobs',
                dataIndex: ['metrics', 'jobs_assigned'],
                render: (val) => <Text className="text-[11px] font-black text-slate-600">{val}</Text>
              },
              {
                title: 'Submissions',
                dataIndex: ['metrics', 'submissions'],
                render: (val) => <Text className="text-[11px] font-black text-slate-600">{val}</Text>
              },
              {
                title: 'Speed',
                dataIndex: ['metrics', 'avg_response_hours'],
                render: (val) => <Text className="text-[11px] font-black text-slate-600">{val} hrs</Text>
              },
              {
                title: 'Hire Rate',
                dataIndex: ['metrics', 'hire_rate'],
                render: (val) => <Text className="text-[11px] font-black text-indigo-600">{val.toFixed(1)}%</Text>
              },
              {
                title: 'Score',
                dataIndex: 'score',
                render: (val) => <Progress percent={val} steps={5} size="small" strokeColor="#4f46e5" showInfo={false} />
              }
            ]}
          />
        </Card>

        {/* ── Risks & Recommendations ────────────────────────────────── */}
        <Card 
          className="lg:col-span-4 rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Activity size={16} className="text-rose-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Actionable Intelligence</span>
            </div>
          }
        >
          <div className="space-y-6">
            <div>
              <Text className="text-[10px] font-black text-slate-400 uppercase block mb-3 border-b pb-2 border-slate-50">Smart Assignment Recommendations</Text>
              <div className="space-y-3">
                {job_recommendations.length > 0 ? job_recommendations.map((jobRec: any, i: number) => (
                  <div key={i} className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100/50">
                    <Text className="text-[11px] font-black text-slate-700 block mb-1">{jobRec.job_title}</Text>
                    <Text className="text-[9px] font-bold text-amber-500 uppercase block mb-2">{jobRec.reason}</Text>
                    {jobRec.recommendations.recommended ? (
                      <div className="flex justify-between items-center bg-white p-2 rounded-lg border border-slate-100">
                        <div className="flex items-center gap-2">
                           <Avatar size="small" className="bg-emerald-100 text-emerald-600 font-bold text-[10px]">
                            {jobRec.recommendations.recommended.full_name[0]}
                           </Avatar>
                           <div>
                             <Text className="text-[10px] font-bold block leading-tight">{jobRec.recommendations.recommended.full_name}</Text>
                             <Text className="text-[8px] text-emerald-600 uppercase font-black">Recommended</Text>
                           </div>
                        </div>
                        <Tag className="text-[8px] font-black m-0 border-none bg-slate-100">{jobRec.recommendations.recommended.score}% Score</Tag>
                      </div>
                    ) : (
                      <Text className="text-[10px] text-slate-500 italic">No available recruiters.</Text>
                    )}
                  </div>
                )) : (
                  <Empty description="No assignment recommendations right now" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </div>
            </div>

            <div>
              <Text className="text-[10px] font-black text-slate-400 uppercase block mb-3 border-b pb-2 border-slate-50">Pipeline Risks</Text>
              <div className="space-y-2">
                {team_performance.flatMap((r: any) => r.workload.risks.map((risk: any) => ({ ...risk, recruiter: r.full_name }))).length > 0 ? 
                  team_performance.flatMap((r: any) => r.workload.risks.map((risk: any) => ({ ...risk, recruiter: r.full_name }))).map((risk: any, i: number) => (
                    <div key={i} className="flex gap-2 items-start p-2 bg-rose-50/30 rounded-lg">
                      <AlertTriangle size={12} className="text-rose-500 mt-0.5 shrink-0" />
                      <div>
                        <Text className="text-[10px] font-black text-slate-700">{risk.recruiter}</Text>
                        <Text className="text-[10px] text-slate-600 block">{risk.message}</Text>
                      </div>
                    </div>
                  ))
                : (
                  <Empty description="No active pipeline risks" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
