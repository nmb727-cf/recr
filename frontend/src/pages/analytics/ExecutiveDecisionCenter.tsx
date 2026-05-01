import React from 'react'
import { Typography, Card, Statistic, Tag, Spin, Alert, Empty, Button, Divider, Avatar } from 'antd'
import { 
  AlertTriangle, 
  Briefcase, 
  CheckCircle2, 
  Clock, 
  Target, 
  Users, 
  Zap, 
  ArrowRight,
  ShieldAlert,
  Building2,
  TrendingUp,
  Activity,
  UserCheck
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function ExecutiveDecisionCenter() {
  const { data, isLoading, error } = useApiQuery(
    ['executive-decision'],
    () => analyticsApi.getExecutiveDecisionCenter(),
    { refetchOnWindowFocus: false, staleTime: 60000 }
  )

  const executiveData = (data as any)?.executive_decision || (data as any)?.data?.executive_decision

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Loading Executive Decision Center..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert 
          type="error" 
          showIcon 
          message="Executive Data Unavailable" 
          description={(error as any)?.message || 'Failed to load executive decision data.'} 
        />
      </div>
    )
  }

  if (!executiveData) return <Empty className="my-16" />

  const { summary, critical_hiring, bottlenecks, team_capacity, agency_effectiveness, interventions, last_updated } = executiveData

  const getRiskColor = (state: string) => {
    if (state === 'Critical') return 'bg-rose-50 text-rose-700 border-rose-200'
    if (state === 'At Risk') return 'bg-amber-50 text-amber-700 border-amber-200'
    return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  }

  return (
    <div className="mx-auto max-w-[1600px] p-6 lg:p-8 flex flex-col gap-6 bg-slate-50/50 min-h-screen">
      
      {/* ─── Level 1: Executive Header ─── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-1.5 w-1.5 rounded-full bg-slate-800" />
            <Text className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Leadership Layer</Text>
          </div>
          <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">Executive Decision Center</Title>
          <Text className="text-sm text-slate-500 mt-2 block">High-level strategic view of critical roles, bottlenecks, and team performance.</Text>
        </div>
        <div className="flex flex-col items-end gap-2">
           <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Decision Board Status</Text>
           <Tag className="rounded-full bg-slate-900 border-none text-white px-4 py-1 text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5">
             <Activity size={12} className="text-emerald-400" /> Live
           </Tag>
           <Text className="text-[9px] text-slate-400 font-medium">As of {dayjs(last_updated).format('MMM D, HH:mm')}</Text>
        </div>
      </div>
      
      <div className="flex flex-wrap items-center gap-2 mb-2 pb-4 border-b border-slate-200">
        <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mr-2">Quick Navigation:</Text>
        <Button size="small" type="dashed" className="rounded-full text-[10px] font-bold uppercase tracking-widest" href="/unified-operations">Unified Operations</Button>
        <Button size="small" type="dashed" className="rounded-full text-[10px] font-bold uppercase tracking-widest" href="/hiring-ai">Hiring AI Brain</Button>
        <Button size="small" type="dashed" className="rounded-full text-[10px] font-bold uppercase tracking-widest" href="/automation-orchestrator">Global Orchestrator</Button>
        <Button size="small" type="dashed" className="rounded-full text-[10px] font-bold uppercase tracking-widest" href="/hiring-intelligence">Hiring Intelligence</Button>
      </div>

      {/* ─── Level 2: Executive Summary Cards ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard 
          label="Critical Roles Open" 
          value={summary.critical_roles_open} 
          icon={<Target size={20} className="text-indigo-600" />}
          color="indigo"
          trend="High Priority"
        />
        <SummaryCard 
          label="Total Open Headcount" 
          value={summary.total_open_headcount} 
          icon={<Users size={20} className="text-blue-600" />}
          color="blue"
          trend="Enterprise Wide"
        />
        <SummaryCard 
          label="Bottlenecked Decisions" 
          value={summary.bottlenecked_decisions} 
          icon={<AlertTriangle size={20} className={summary.bottlenecked_decisions > 0 ? "text-rose-600" : "text-slate-400"} />}
          color={summary.bottlenecked_decisions > 0 ? "rose" : "slate"}
          trend="Requires Action"
        />
        <SummaryCard 
          label="Avg Hiring Velocity" 
          value={summary.hiring_velocity} 
          suffix=" Days"
          icon={<Zap size={20} className="text-emerald-600" />}
          color="emerald"
          trend="Time to Hire"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.5fr_1fr] gap-6">
        
        {/* ─── Left Column: Critical Path ─── */}
        <div className="flex flex-col gap-6">
          
          {/* Critical Hiring View */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-800">Business-Critical Hiring</span>} extra={<Button type="link" size="small" className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">View All</Button>}>
             {critical_hiring.length > 0 ? (
               <div className="space-y-3">
                  {critical_hiring.map((job: any, i: number) => (
                    <div key={i} className="p-4 rounded-2xl border border-slate-100 bg-white hover:border-slate-300 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                       <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1.5">
                             <Tag className={cn("m-0 px-2 py-0 border text-[9px] font-black uppercase tracking-wider rounded-md", getRiskColor(job.risk_state))}>
                               {job.risk_state}
                             </Tag>
                             <Tag className="m-0 border-none bg-slate-100 text-slate-600 px-2 py-0 text-[9px] font-black uppercase tracking-wider rounded-md">
                               {job.priority} Priority
                             </Tag>
                          </div>
                          <Text className="text-sm font-black text-slate-900 truncate block">{job.title}</Text>
                          <div className="flex items-center gap-3 mt-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                             <span className="flex items-center gap-1"><Clock size={12} /> {job.days_open} Days Open</span>
                             <span>•</span>
                             <span className="flex items-center gap-1"><Users size={12} /> {job.filled} / {job.headcount} Filled</span>
                          </div>
                       </div>
                       <Button size="small" className="shrink-0 text-[10px] font-bold uppercase tracking-widest rounded-lg h-8 px-4 border-slate-200">
                          Review Job
                       </Button>
                    </div>
                  ))}
               </div>
             ) : (
               <Empty description="No critical roles open currently." />
             )}
          </Card>

          {/* Decision Bottlenecks */}
          <Card className="rounded-3xl border border-rose-200 shadow-sm bg-rose-50/30" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-rose-800">Decision Bottlenecks</span>}>
             {bottlenecks.length > 0 ? (
               <div className="space-y-4">
                  {bottlenecks.map((btn: any, i: number) => (
                    <div key={i} className="flex items-start gap-4">
                       <div className="bg-rose-100 text-rose-600 p-2 rounded-xl shrink-0 mt-0.5">
                         <ShieldAlert size={18} />
                       </div>
                       <div>
                          <Text className="text-sm font-black text-slate-900 block mb-0.5">{btn.item}</Text>
                          <Text className="text-[11px] font-bold text-rose-600 uppercase tracking-widest block mb-2">{btn.blocker}</Text>
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[10px] text-slate-500 font-medium">
                             <span className="bg-white border border-slate-200 px-2 py-0.5 rounded-md text-slate-700 font-bold">Owner: {btn.owner}</span>
                             <span className="flex items-center gap-1"><Clock size={10} /> Age: {btn.age_days} Days</span>
                             <span className="flex items-center gap-1 text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-md"><ArrowRight size={10} /> {btn.suggested_step}</span>
                          </div>
                       </div>
                    </div>
                  ))}
               </div>
             ) : (
               <div className="py-8 flex flex-col items-center justify-center text-center">
                 <CheckCircle2 size={32} className="text-emerald-400 mb-3" />
                 <Text className="text-sm font-black text-slate-700">No Blockers Detected</Text>
                 <Text className="text-xs text-slate-500">Pipeline decisions are moving smoothly.</Text>
               </div>
             )}
          </Card>

        </div>

        {/* ─── Right Column: Capacity & Strategy ─── */}
        <div className="flex flex-col gap-6">
          
          {/* Intervention Recommendations */}
          <Card className="rounded-3xl border border-indigo-200 shadow-sm bg-indigo-50/20" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-indigo-800 flex items-center gap-2"><Zap size={14} /> Executive Interventions</span>}>
             {interventions.length > 0 ? (
               <div className="flex flex-col gap-3">
                 {interventions.map((inv: any, i: number) => (
                   <div key={i} className="p-3 bg-white border border-indigo-100 rounded-2xl flex items-start gap-3 shadow-soft-sm group cursor-pointer hover:border-indigo-300 transition-all">
                      <div className="bg-indigo-50 text-indigo-500 p-1.5 rounded-lg shrink-0">
                         {inv.action_type === 'rebalance' ? <Users size={14} /> : 
                          inv.action_type === 'sourcing' ? <Target size={14} /> : 
                          inv.action_type === 'partnership' ? <Building2 size={14} /> : <TrendingUp size={14} />}
                      </div>
                      <div>
                         <Text className="text-xs font-black text-slate-800 block leading-tight mb-1 group-hover:text-indigo-700 transition-colors">{inv.title}</Text>
                         <Text className="text-[10px] text-slate-500 leading-normal block">{inv.description}</Text>
                      </div>
                   </div>
                 ))}
               </div>
             ) : (
               <Empty description="No strategic interventions recommended." />
             )}
          </Card>

          {/* Team Capacity & Performance */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-800">Team Capacity</span>}>
             <div className="flex items-center justify-between mb-6 pb-6 border-b border-slate-100">
                <div className="text-center">
                   <Text className="text-3xl font-black text-rose-600 block leading-none">{team_capacity.overloaded_recruiters}</Text>
                   <Text className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mt-1 block">Overloaded</Text>
                </div>
                <Divider type="vertical" className="h-10 border-slate-200" />
                <div className="text-center">
                   <Text className="text-3xl font-black text-slate-300 block leading-none">{team_capacity.underutilized_recruiters}</Text>
                   <Text className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mt-1 block">Underutilized</Text>
                </div>
             </div>
             <div>
                <Text className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3 block">Top Contributors (Active Load)</Text>
                <div className="space-y-3">
                   {team_capacity.top_performers.map((perf: any, i: number) => (
                     <div key={i} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                           <Avatar size="small" className="bg-slate-200 text-slate-600 text-[10px] font-bold">{perf.full_name?.charAt(0) || 'U'}</Avatar>
                           <Text className="text-xs font-bold text-slate-700">{perf.full_name}</Text>
                        </div>
                        <Tag className="m-0 border-none bg-slate-100 text-slate-600 text-[10px] font-black">{perf.workload?.active_candidates || 0} Cand.</Tag>
                     </div>
                   ))}
                </div>
             </div>
          </Card>

          {/* Agency Effectiveness */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-800">Agency Strategy</span>}>
             <div className="mb-4">
                <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">Source Mix Health</Text>
                <Tag className={cn(
                  "m-0 border px-3 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg",
                  agency_effectiveness.source_mix === 'Healthy' ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"
                )}>
                  {agency_effectiveness.source_mix}
                </Tag>
             </div>
             
             <div className="space-y-4">
               <div>
                  <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2 block flex items-center gap-1"><UserCheck size={12} /> Top Partners</Text>
                  {agency_effectiveness.top_agencies.length > 0 ? (
                    <div className="space-y-2">
                       {agency_effectiveness.top_agencies.map((ag: any, i: number) => (
                         <div key={i} className="flex justify-between items-center bg-slate-50 px-3 py-1.5 rounded-lg">
                           <Text className="text-[11px] font-bold text-slate-700 truncate pr-2">{ag.agency_name}</Text>
                           <Text className="text-[10px] font-black text-emerald-600">{ag.score} Score</Text>
                         </div>
                       ))}
                    </div>
                  ) : <Text className="text-xs text-slate-400">No data</Text>}
               </div>
               
               {agency_effectiveness.weak_agencies.length > 0 && (
                 <div>
                    <Text className="text-[10px] font-bold uppercase tracking-widest text-rose-500 mb-2 block flex items-center gap-1"><AlertTriangle size={12} /> Underperforming</Text>
                    <div className="space-y-2">
                       {agency_effectiveness.weak_agencies.slice(0, 3).map((ag: any, i: number) => (
                         <div key={i} className="flex justify-between items-center bg-rose-50 px-3 py-1.5 rounded-lg">
                           <Text className="text-[11px] font-bold text-rose-700 truncate pr-2">{ag.agency_name}</Text>
                           <Text className="text-[10px] font-black text-rose-600">{ag.score} Score</Text>
                         </div>
                       ))}
                    </div>
                 </div>
               )}
             </div>
          </Card>

        </div>
      </div>

    </div>
  )
}

function SummaryCard({ label, value, icon, color, suffix = '', trend = '' }: any) {
  const colorMap: any = {
    indigo: 'bg-white border-indigo-100 text-indigo-900',
    blue: 'bg-white border-blue-100 text-blue-900',
    rose: 'bg-white border-rose-100 text-rose-900',
    emerald: 'bg-white border-emerald-100 text-emerald-900',
    slate: 'bg-white border-slate-200 text-slate-800',
  }
  
  const iconBgMap: any = {
    indigo: 'bg-indigo-50',
    blue: 'bg-blue-50',
    rose: 'bg-rose-50',
    emerald: 'bg-emerald-50',
    slate: 'bg-slate-50',
  }

  return (
    <Card className={cn("rounded-3xl border shadow-sm transition-all hover:shadow-md", colorMap[color] || colorMap.slate)}>
      <div className="flex items-start justify-between">
        <div>
           <Statistic 
             title={<span className="text-[10px] font-black uppercase tracking-widest opacity-60 block mb-1">{label}</span>} 
             value={value} 
             suffix={suffix}
             valueStyle={{ fontWeight: 900, color: 'inherit', fontSize: '28px', lineHeight: 1 }} 
           />
           {trend && <Text className="text-[9px] font-bold uppercase tracking-widest opacity-50 block mt-2">{trend}</Text>}
        </div>
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-2xl", iconBgMap[color] || iconBgMap.slate)}>
          {icon}
        </div>
      </div>
    </Card>
  )
}
