import React from 'react'
import { Typography, Card, Statistic, Tag, Table, Spin, Alert, Empty, Progress, Divider, Button } from 'antd'
import { 
  Activity, 
  AlertTriangle, 
  ShieldAlert, 
  Users, 
  Zap, 
  CheckCircle2, 
  TrendingUp, 
  ArrowRight,
  Target,
  Briefcase,
  Layers,
  Search,
  MessageSquare,
  Clock,
  Settings2
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function UnifiedOperationsDashboard() {
  const { data, isLoading, error } = useApiQuery(
    ['unified-operations'],
    () => analyticsApi.getUnifiedOperations(),
    { refetchOnWindowFocus: false, staleTime: 60000 }
  )

  const ops = (data as any)?.operations || (data as any)?.data?.operations

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Aggregating Unified Operations Data..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert 
          type="error" 
          showIcon 
          message="Operations Data Unavailable" 
          description={(error as any)?.message || 'The unified operations engine encountered an error.'} 
        />
      </div>
    )
  }

  if (!ops) return <Empty className="my-16" />

  const { summary, health, risks, workload, interviews, automation, interventions, last_updated } = ops

  const getHealthTag = (status: string) => {
    if (status === 'healthy') return <Tag className="bg-emerald-50 text-emerald-700 border-emerald-100 uppercase font-black text-[9px] tracking-widest m-0">Healthy</Tag>
    if (status === 'warning') return <Tag className="bg-amber-50 text-amber-700 border-amber-100 uppercase font-black text-[9px] tracking-widest m-0">Warning</Tag>
    return <Tag className="bg-rose-50 text-rose-700 border-rose-100 uppercase font-black text-[9px] tracking-widest m-0">Critical</Tag>
  }

  return (
    <div className="mx-auto max-w-[1600px] p-6 lg:p-8 flex flex-col gap-6">
      
      {/* ─── Level 1: Operations Header ─── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-1.5 w-1.5 rounded-full bg-indigo-600 animate-pulse" />
            <Text className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Operations Control Center</Text>
          </div>
          <div className="flex items-center gap-3">
             <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">Unified Operations View</Title>
          </div>
          <Text className="text-sm text-slate-500 mt-2 block">Global cross-module monitoring of Jobs, Pipeline, Teams, and Automation.</Text>
        </div>
        <div className="flex flex-col items-end gap-2">
           <div className="flex items-center gap-2">
              <Text className="text-[10px] font-bold text-slate-400 uppercase">System Status:</Text>
              <Tag className="rounded-full bg-emerald-50 border-emerald-100 text-emerald-700 px-3 py-0.5 text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Operational
              </Tag>
           </div>
           <Text className="text-[10px] text-slate-400 font-medium">Last synced: {dayjs(last_updated).format('HH:mm:ss')}</Text>
        </div>
      </div>

      {/* ─── Level 2: Executive Summary ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard 
          label="Active Hiring Load" 
          value={summary.total_active_load} 
          subValue={`${summary.total_in_pipeline} Candidates`}
          icon={<Briefcase size={20} className="text-indigo-600" />}
          color="indigo"
        />
        <SummaryCard 
          label="Urgent Decisions" 
          value={summary.urgent_actions} 
          subValue="Action required now"
          icon={<Zap size={20} className="text-amber-600" />}
          color="amber"
        />
        <SummaryCard 
          label="Pending Feedback" 
          value={interviews.pending_feedback} 
          subValue={`${interviews.scheduled_today} Scheduled today`}
          icon={<MessageSquare size={20} className="text-blue-600" />}
          color="blue"
        />
        <SummaryCard 
          label="Operations Score" 
          value={summary.system_health_score} 
          suffix="%"
          subValue="Aggregate Health"
          icon={<Activity size={20} className="text-emerald-600" />}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-6">
        
        {/* Left Column: Health & Risks */}
        <div className="flex flex-col gap-6">
          
          {/* Module Health Traffic Lights */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
             <div className="bg-slate-50/50 border-b border-slate-100 px-6 py-3 flex items-center justify-between">
                <Text className="text-[11px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                  <ShieldAlert size={14} /> Operational Module Health
                </Text>
             </div>
             <div className="grid grid-cols-2 md:grid-cols-5 divide-x divide-slate-100">
                <HealthBlock label="Jobs" status={health.jobs} icon={<Briefcase size={16} />} />
                <HealthBlock label="Pipeline" status={health.pipeline} icon={<Layers size={16} />} />
                <HealthBlock label="Team" status={health.team} icon={<Users size={16} />} />
                <HealthBlock label="Agencies" status={health.agencies} icon={<Target size={16} />} />
                <HealthBlock label="Automation" status={health.automation} icon={<Settings2 size={16} />} />
             </div>
          </Card>

          {/* Cross-Module Risks Section */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Cross-Module Risk Alerts</span>}>
             {risks.length > 0 ? (
               <div className="space-y-4">
                  {risks.map((risk: any, i: number) => (
                    <div key={i} className={cn(
                      "p-5 rounded-2xl border flex items-start gap-4 transition-all hover:shadow-md",
                      risk.severity === 'high' ? "bg-rose-50/30 border-rose-100" : "bg-amber-50/30 border-amber-100"
                    )}>
                       <div className={cn(
                         "p-2.5 rounded-xl shrink-0",
                         risk.severity === 'high' ? "bg-rose-100 text-rose-600" : "bg-amber-100 text-amber-600"
                       )}>
                         <AlertTriangle size={20} />
                       </div>
                       <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between mb-1">
                             <div className="flex items-center gap-2">
                                <Tag className="m-0 border-none px-2 py-0 text-[9px] font-black uppercase bg-white rounded-lg">{risk.module}</Tag>
                                <Text className="text-sm font-black text-slate-800">{risk.title}</Text>
                             </div>
                             <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Owner: {risk.owner}</Text>
                          </div>
                          <Text className="block text-xs text-slate-600 leading-relaxed mb-3">{risk.impact}</Text>
                          <div className="flex items-center gap-2 p-2 bg-white/60 rounded-xl border border-slate-100/50">
                             <TrendingUp size={12} className="text-indigo-500" />
                             <Text className="text-[11px] font-bold text-indigo-700">Recommendation: {risk.suggested_action}</Text>
                          </div>
                       </div>
                    </div>
                  ))}
               </div>
             ) : (
               <div className="py-12 text-center bg-emerald-50/30 rounded-3xl border border-emerald-100 border-dashed">
                  <CheckCircle2 size={40} className="text-emerald-400 mx-auto mb-3" />
                  <Text className="text-lg font-black text-emerald-800 block">System Integrity Clear</Text>
                  <Text className="text-emerald-600 font-medium">No cross-module operational risks detected at this time.</Text>
               </div>
             )}
          </Card>

          {/* Intervention Roadmap */}
          <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Recommended Interventions</span>}>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {interventions.map((item: any, i: number) => (
                  <div key={i} className="p-4 rounded-2xl border border-slate-100 bg-white hover:border-indigo-200 transition-all group">
                     <div className="flex items-center justify-between mb-2">
                        <Tag className="m-0 border-none px-2 py-0 text-[9px] font-black uppercase bg-indigo-50 text-indigo-600 rounded-lg">{item.type}</Tag>
                        <ArrowRight size={14} className="text-slate-300 group-hover:text-indigo-500 transform group-hover:translate-x-1 transition-all" />
                     </div>
                     <Text className="block font-black text-slate-800 text-sm mb-1">{item.title}</Text>
                     <Text className="block text-xs text-slate-500 leading-normal">{item.description}</Text>
                  </div>
                ))}
             </div>
          </Card>
        </div>

        {/* Right Column: Mini Dashboards */}
        <div className="flex flex-col gap-6">
           
           {/* Team / Recruiter Load */}
           <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Team Workload</span>}>
              <div className="flex flex-col gap-4">
                 <div className="flex justify-between items-end mb-2">
                    <div>
                       <Text className="text-[10px] font-black text-slate-400 uppercase block">Total Recruiters</Text>
                       <Text className="text-2xl font-black text-slate-800 leading-none">{workload.total_recruiters}</Text>
                    </div>
                    <div className="text-right">
                       <Text className="text-[10px] font-black text-rose-500 uppercase block">Overloaded</Text>
                       <Text className="text-2xl font-black text-rose-600 leading-none">{workload.overloaded}</Text>
                    </div>
                 </div>
                 <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="h-full bg-rose-500" style={{ width: `${(workload.overloaded / workload.total_recruiters) * 100}%` }} />
                    <div className="h-full bg-emerald-500" style={{ width: `${(workload.balanced / workload.total_recruiters) * 100}%` }} />
                    <div className="h-full bg-slate-300" style={{ width: `${(workload.underutilized / workload.total_recruiters) * 100}%` }} />
                 </div>
                 <div className="flex flex-col gap-2 mt-2">
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-tight">
                       <span className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-rose-500" /> Overloaded</span>
                       <span className="text-slate-600">{workload.overloaded}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-tight">
                       <span className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-emerald-500" /> Balanced</span>
                       <span className="text-slate-600">{workload.balanced}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-tight">
                       <span className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-slate-300" /> Underutilized</span>
                       <span className="text-slate-600">{workload.underutilized}</span>
                    </div>
                 </div>
              </div>
           </Card>

           {/* Automation / SLA Health */}
           <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Execution Health</span>}>
              <div className="flex flex-col gap-5">
                 <div>
                    <div className="flex justify-between items-center mb-2">
                       <Text className="text-xs font-bold text-slate-600">Automation Success Rate</Text>
                       <Text className="text-xs font-black text-indigo-600">{automation.success_rate}%</Text>
                    </div>
                    <Progress percent={automation.success_rate} showInfo={false} strokeColor="#4f46e5" trailColor="#f1f5f9" strokeWidth={10} />
                 </div>
                 <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Failed Automations (24h)</Text>
                    <Text className={cn(
                      "text-xl font-black",
                      automation.failed_last_24h > 0 ? "text-rose-600" : "text-slate-800"
                    )}>{automation.failed_last_24h}</Text>
                 </div>
                 <Button ghost type="primary" block className="rounded-xl border-indigo-200 text-indigo-600 font-bold text-[10px] uppercase tracking-widest h-10">
                    View Orchestrator
                 </Button>
              </div>
           </Card>

           {/* Interview Flow Health */}
           <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Interview Flow</span>}>
              <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                       <div className="bg-blue-50 text-blue-600 p-2 rounded-xl"><Clock size={16} /></div>
                       <Text className="text-xs font-bold text-slate-700">Scheduled Today</Text>
                    </div>
                    <Text className="text-sm font-black text-slate-800">{interviews.scheduled_today}</Text>
                 </div>
                 <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                       <div className="bg-amber-50 text-amber-600 p-2 rounded-xl"><MessageSquare size={16} /></div>
                       <Text className="text-xs font-bold text-slate-700">Pending Feedback</Text>
                    </div>
                    <Text className="text-sm font-black text-amber-600">{interviews.pending_feedback}</Text>
                 </div>
              </div>
           </Card>

        </div>
      </div>

    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SummaryCard({ label, value, subValue, icon, color, suffix = '' }: any) {
  const colorMap: any = {
    indigo: 'from-indigo-50/50 to-white border-indigo-100 text-indigo-900',
    amber: 'from-amber-50/50 to-white border-amber-100 text-amber-900',
    blue: 'from-blue-50/50 to-white border-blue-100 text-blue-900',
    emerald: 'from-emerald-50/50 to-white border-emerald-100 text-emerald-900',
  }

  return (
    <Card className={cn("rounded-3xl border shadow-sm bg-gradient-to-br transition-all hover:scale-[1.02]", colorMap[color] || colorMap.indigo)}>
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-white shadow-soft-sm">
        {icon}
      </div>
      <Statistic 
        title={<span className="text-[10px] font-black uppercase tracking-[0.12em] opacity-60">{label}</span>} 
        value={value} 
        suffix={suffix}
        valueStyle={{ fontWeight: 900, color: 'inherit' }} 
      />
      <Text className="text-[10px] font-bold opacity-50 block mt-1">{subValue}</Text>
    </Card>
  )
}

function HealthBlock({ label, status, icon }: any) {
  const getStatusColor = (s: string) => {
    if (s === 'healthy') return 'bg-emerald-500'
    if (s === 'warning') return 'bg-amber-500'
    return 'bg-rose-500'
  }

  return (
    <div className="px-6 py-5 flex flex-col items-center gap-3 transition-colors hover:bg-slate-50/80 group">
       <div className={cn(
         "p-2.5 rounded-xl transition-all group-hover:shadow-soft-sm",
         status === 'healthy' ? "bg-emerald-50 text-emerald-600" : status === 'warning' ? "bg-amber-50 text-amber-600" : "bg-rose-50 text-rose-600"
       )}>
         {icon}
       </div>
       <div className="text-center">
          <Text className="text-[10px] font-black text-slate-400 uppercase block tracking-wider mb-1">{label}</Text>
          <div className="flex items-center gap-1.5 justify-center">
             <div className={cn("h-1.5 w-1.5 rounded-full", getStatusColor(status))} />
             <Text className="text-[10px] font-black uppercase tracking-widest text-slate-700">{status}</Text>
          </div>
       </div>
    </div>
  )
}
