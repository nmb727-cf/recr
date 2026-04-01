import React from 'react'
import {
  Card, Row, Col, Typography, Statistic, Spin, Empty, Badge, Avatar, Progress, Table, Tag
} from 'antd'
import {
  Activity, Briefcase, Users, Calendar, Clock, AlertTriangle, TrendingUp, Layers,
  Target, Zap, ShieldCheck, UserCheck, Building2, BarChart3, ChevronRight
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

export default function HiringIntelligenceDashboard() {
  const { data: res, isLoading } = useApiQuery(
    ['hiring-intelligence'],
    () => analyticsApi.hiringIntelligence()
  )

  const intelligence = (res as any)?.intelligence ?? (res as any)?.data?.intelligence

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Spin size="large" tip="Synthesizing Hiring Intelligence..." />
      </div>
    )
  }

  if (!intelligence) {
    return (
      <div className="p-12">
        <Empty description="No intelligence data available yet" />
      </div>
    )
  }

  const { overview, job_health, pipeline_intelligence, performance, candidate_intelligence } = intelligence

  return (
    <div className="max-w-[1600px] mx-auto p-8 space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between mb-2">
        <div>
          <Title level={2} className="!m-0 uppercase tracking-tighter font-black text-slate-900">
            Hiring Intelligence Dashboard
          </Title>
          <Text className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">
            Real-time Talent Acquisition Mission Control
          </Text>
        </div>
        <div className="flex items-center gap-2">
          <Badge status="processing" text="Live Feed" className="text-xs font-bold uppercase" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: 'Active Jobs', value: overview.active_jobs, icon: <Briefcase size={20} className="text-indigo-600" /> },
          { label: 'Open Positions', value: overview.open_positions, icon: <Target size={20} className="text-blue-600" /> },
          { label: 'Pipeline', value: overview.candidates_in_pipeline, icon: <Users size={20} className="text-emerald-600" /> },
          { label: 'Interviews', value: overview.interviews_scheduled, icon: <Calendar size={20} className="text-amber-600" /> },
          { label: 'Offers Pending', value: overview.offers_pending, icon: <Clock size={20} className="text-purple-600" /> },
          { label: 'Hires (MoM)', value: overview.hires_this_month, icon: <UserCheck size={20} className="text-rose-600" /> },
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
        <Card 
          className="lg:col-span-4 rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Activity size={16} className="text-rose-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Job Health Intelligence</span>
            </div>
          }
        >
          <div className="space-y-6">
            <div className="flex justify-between items-end">
              <div>
                <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Jobs at Risk</Text>
                <Text className="text-4xl font-black text-rose-600">{job_health.at_risk_count}</Text>
              </div>
              <div className="text-right">
                <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Stuck Jobs</Text>
                <Text className="text-2xl font-black text-slate-800">{job_health.stuck_jobs}</Text>
              </div>
            </div>
            
            <div className="space-y-3">
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest block border-b pb-2 border-slate-50">At Risk Details</Text>
              {job_health.at_risk_details.length > 0 ? job_health.at_risk_details.map((job: any, i: number) => (
                <div key={i} className="flex justify-between items-center p-3 bg-rose-50/30 rounded-xl border border-rose-100/50">
                  <div>
                    <Text className="text-[11px] font-black text-slate-700 block">{job.title}</Text>
                    <Text className="text-[10px] font-bold text-rose-500 uppercase">{job.reason}</Text>
                  </div>
                  <ChevronRight size={14} className="text-rose-300" />
                </div>
              )) : <Empty description="All jobs are healthy" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
            </div>
          </div>
        </Card>

        <Card 
          className="lg:col-span-8 rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-indigo-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Pipeline Intelligence</span>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Stalled Candidates</Text>
                <div className="flex items-center gap-4">
                  <Text className="text-4xl font-black text-amber-500">{pipeline_intelligence.stalled_candidates}</Text>
                  <Progress percent={45} status="warning" showInfo={false} className="flex-1" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                  <Text className="text-[9px] font-black text-slate-400 uppercase block mb-1">Avg Time to Hire</Text>
                  <Text className="text-xl font-black text-slate-800">{pipeline_intelligence.avg_time_to_hire_days} Days</Text>
                </div>
                <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                  <Text className="text-[9px] font-black text-indigo-400 uppercase block mb-1">Global Velocity</Text>
                  <Text className="text-xl font-black text-indigo-700">High</Text>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">Stage Conversions</Text>
              {Object.entries(pipeline_intelligence.stage_conversion_rates).map(([key, value]: [string, any], i) => (
                <div key={i}>
                  <div className="flex justify-between mb-1">
                    <Text className="text-[10px] font-black text-slate-500 uppercase">{key.replace(/_/g, ' ')}</Text>
                    <Text className="text-[10px] font-black text-indigo-600">{value}%</Text>
                  </div>
                  <Progress percent={value} strokeColor="#4f46e5" showInfo={false} size="small" />
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card 
          className="rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-500" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Recruiter Performance</span>
            </div>
          }
        >
          <Table 
            dataSource={performance.recruiters}
            pagination={false}
            size="small"
            rowKey="user_id"
            columns={[
              {
                title: 'Recruiter',
                dataIndex: 'full_name',
                render: (text: string) => (
                  <div className="flex items-center gap-2">
                    <Avatar size="small" className="bg-indigo-100 text-indigo-600 font-bold">{text[0]}</Avatar>
                    <Text className="text-[11px] font-black text-slate-700">{text}</Text>
                  </div>
                )
              },
              {
                title: 'Workload',
                dataIndex: ['workload', 'active_candidates'],
                render: (val) => <Tag className="rounded-full font-black text-[9px] uppercase border-none bg-slate-100 text-slate-600">{val} Active</Tag>
              },
              {
                title: 'Hire Rate',
                dataIndex: ['metrics', 'hire_rate'],
                render: (val) => <Text className="text-[11px] font-black text-emerald-600">{val.toFixed(1)}%</Text>
              },
              {
                title: 'Score',
                dataIndex: 'score',
                render: (val) => <Progress percent={val} steps={5} size="small" strokeColor="#4f46e5" showInfo={false} />
              }
            ]}
          />
        </Card>

        <Card 
          className="rounded-3xl border-none shadow-soft-sm"
          title={
            <div className="flex items-center gap-2">
              <Building2 size={16} className="text-blue-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Agency Performance</span>
            </div>
          }
        >
          <Table 
            dataSource={performance.agencies}
            pagination={false}
            size="small"
            rowKey="agency_tenant_id"
            columns={[
              {
                title: 'Agency',
                dataIndex: 'agency_name',
                render: (text) => <Text className="text-[11px] font-black text-slate-700 uppercase tracking-tight">{text}</Text>
              },
              {
                title: 'Shortlist Rate',
                dataIndex: ['metrics', 'shortlist_rate'],
                render: (val) => <Text className="text-[11px] font-black text-indigo-600">{val.toFixed(1)}%</Text>
              },
              {
                title: 'Join Rate',
                dataIndex: ['metrics', 'join_rate'],
                render: (val) => <Text className="text-[11px] font-black text-emerald-600">{val.toFixed(1)}%</Text>
              },
              {
                title: 'Score',
                dataIndex: 'score',
                render: (val) => <Progress type="circle" percent={val} size={24} strokeWidth={12} strokeColor="#4f46e5" />
              }
            ]}
          />
        </Card>
      </div>

      <Card 
        className="rounded-3xl border-none shadow-soft-sm overflow-hidden"
        title={
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-emerald-600" />
            <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Candidate Intelligence Summary</span>
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 py-4">
          <div className="text-center space-y-2">
            <Text className="text-[10px] font-black text-slate-400 uppercase block tracking-widest">Strong Candidates</Text>
            <Text className="text-4xl font-black text-slate-800">{candidate_intelligence.strong_candidates}</Text>
            <div className="text-[10px] font-bold text-emerald-600 uppercase">Top 10% Fitment</div>
          </div>
          <div className="text-center space-y-2 border-l border-slate-50">
            <Text className="text-[10px] font-black text-slate-400 uppercase block tracking-widest">Fast Hire Potential</Text>
            <Text className="text-4xl font-black text-indigo-600">{candidate_intelligence.fast_hire_potential}</Text>
            <div className="text-[10px] font-bold text-indigo-400 uppercase">High Momentum</div>
          </div>
          <div className="text-center space-y-2 border-l border-slate-50">
            <Text className="text-[10px] font-black text-slate-400 uppercase block tracking-widest">Stalled Talents</Text>
            <Text className="text-4xl font-black text-rose-500">{candidate_intelligence.stalled_candidates}</Text>
            <div className="text-[10px] font-bold text-rose-300 uppercase">Needs Nurture</div>
          </div>
          <div className="text-center space-y-2 border-l border-slate-50">
            <Text className="text-[10px] font-black text-slate-400 uppercase block tracking-widest">High Potential</Text>
            <Text className="text-4xl font-black text-amber-500">{candidate_intelligence.high_potential}</Text>
            <div className="text-[10px] font-bold text-amber-400 uppercase">Future Ready</div>
          </div>
        </div>
      </Card>
    </div>
  )
}
