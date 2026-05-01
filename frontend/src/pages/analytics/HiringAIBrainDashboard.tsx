import { Alert, Avatar, Card, Empty, Progress, Spin, Statistic, Table, Tag, Typography, Button } from 'antd'
import { Activity, AlertTriangle, BrainCircuit, Users, Zap, TrendingUp, Info, ShieldAlert } from 'lucide-react'
import { cn } from '@/utils/cn'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'

const { Title, Text } = Typography

function severityColor(severity: string) {
  if (severity === 'high') return 'text-rose-600 bg-rose-50 border-rose-100'
  if (severity === 'medium') return 'text-amber-600 bg-amber-50 border-amber-100'
  return 'text-emerald-600 bg-emerald-50 border-emerald-100'
}

export default function HiringAIBrainDashboard() {
  const { data, isLoading, error } = useApiQuery(
    ['hiring-ai-brain-dashboard'],
    () => analyticsApi.getAIBrainIntelligence(),
    { retry: false, refetchOnWindowFocus: false, staleTime: 60_000 },
  )

  const brain = (data as any)?.brain ?? (data as any)?.data?.brain

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Booting Hiring AI Brain..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-[1440px] p-8">
        <Alert
          type="error"
          showIcon
          message="AI Brain could not be loaded."
          description={(error as { message?: string })?.message || 'The dashboard endpoint failed.'}
        />
      </div>
    )
  }

  if (!brain) {
    return (
      <div className="mx-auto max-w-[1440px] p-8">
        <Empty description="No AI brain intelligence data available yet" />
      </div>
    )
  }

  const { overview, smart_actions, risks, opportunities, job_recommendations } = brain

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <Text className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Intelligence / Hiring / AI</Text>
          <div className="flex items-center gap-3">
             <Title level={2} className="!mb-1 !mt-2 flex items-center gap-2">
                Hiring AI Brain
             </Title>
          </div>
          <Text className="text-slate-500">Autonomous intelligence layer orchestrating jobs, recruiters, agencies, and candidates.</Text>
        </div>
        <Tag className="rounded-full border-blue-200 bg-blue-50 px-4 py-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-blue-700">
          <BrainCircuit size={12} className="animate-pulse text-blue-600" />
          Neural Engine Active
        </Tag>
      </div>

      {/* OVERVIEW STATS */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-indigo-50/50 to-white">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600"><Zap size={18} /></div>
          <Statistic title={<span className="text-[10px] font-black uppercase tracking-[0.12em] text-indigo-400">Actionable Insights</span>} value={overview.actionable_insights} valueStyle={{ fontWeight: 900, color: '#3730a3' }} />
        </Card>
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-rose-50/50 to-white">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-100 text-rose-600"><AlertTriangle size={18} /></div>
          <Statistic title={<span className="text-[10px] font-black uppercase tracking-[0.12em] text-rose-400">Critical Risks</span>} value={overview.critical_risks} valueStyle={{ fontWeight: 900, color: '#9f1239' }} />
        </Card>
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-emerald-50/50 to-white">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600"><TrendingUp size={18} /></div>
          <Statistic title={<span className="text-[10px] font-black uppercase tracking-[0.12em] text-emerald-400">Opportunities</span>} value={overview.opportunities} valueStyle={{ fontWeight: 900, color: '#065f46' }} />
        </Card>
        <Card className="rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-br from-amber-50/50 to-white">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-100 text-amber-600"><Activity size={18} /></div>
          <Statistic title={<span className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-400">System Health Score</span>} value={overview.health_score} suffix="/100" valueStyle={{ fontWeight: 900, color: '#92400e' }} />
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1fr]">
        {/* SMART ACTIONS */}
        <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Smart Action Center</span>}>
          {smart_actions?.length ? (
            <div className="space-y-3">
              {smart_actions.map((action: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-4 rounded-2xl border border-slate-100 bg-slate-50/80 hover:bg-white hover:shadow-sm transition-all group">
                   <div>
                     <div className="flex items-center gap-2 mb-1">
                       <Tag className={cn("m-0 border-none px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded-lg", severityColor(action.priority))}>
                         {action.priority} Priority
                       </Tag>
                       <Text className="text-[10px] font-bold text-slate-400 uppercase">{action.category}</Text>
                     </div>
                     <Text className="text-sm font-bold text-slate-800">{action.title}</Text>
                     <Text className="block text-xs text-slate-500 mt-1">{action.description}</Text>
                   </div>
                   <Button type="primary" size="small" className="bg-indigo-600 shadow-soft-sm font-bold text-[10px] uppercase tracking-wider h-8 px-4 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity">
                     Execute
                   </Button>
                </div>
              ))}
            </div>
          ) : (
            <Empty description="No immediate actions required" />
          )}
        </Card>

        {/* RISKS */}
        <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Active Risks</span>}>
          {risks?.length ? (
            <div className="space-y-3">
              {risks.map((risk: any, i: number) => (
                <div key={i} className="p-4 rounded-2xl border border-rose-100 bg-rose-50/60 flex items-start gap-3">
                   <ShieldAlert size={18} className="text-rose-500 shrink-0 mt-0.5" />
                   <div>
                     <Text className="text-sm font-bold text-slate-800 leading-tight">{risk.title}</Text>
                     <Text className="block text-xs text-slate-600 mt-1">{risk.impact}</Text>
                     <div className="mt-2 text-[10px] font-bold text-rose-600 uppercase flex items-center gap-1 cursor-pointer hover:text-rose-700">
                        View Details
                     </div>
                   </div>
                </div>
              ))}
            </div>
          ) : (
             <div className="flex flex-col items-center justify-center p-8 bg-emerald-50 rounded-2xl border border-emerald-100 text-center">
                <ShieldAlert size={32} className="text-emerald-400 mb-3" />
                <Text className="text-sm font-bold text-emerald-800">No Critical Risks</Text>
                <Text className="text-xs text-emerald-600">The hiring ecosystem is running smoothly.</Text>
             </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* OPPORTUNITIES */}
        <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Opportunities</span>}>
           {opportunities?.length ? (
             <div className="space-y-3">
                {opportunities.map((opp: any, i: number) => (
                  <div key={i} className="p-4 rounded-2xl border border-emerald-100 bg-emerald-50/50 flex items-start gap-3">
                     <Zap size={18} className="text-emerald-500 shrink-0 mt-0.5" />
                     <div>
                       <Text className="text-sm font-bold text-slate-800 leading-tight">{opp.title}</Text>
                       <Text className="block text-xs text-slate-600 mt-1">{opp.description}</Text>
                       {opp.metric && (
                         <div className="mt-2 inline-block px-2 py-1 bg-white rounded-lg border border-emerald-100 text-[10px] font-black text-emerald-700 uppercase">
                           Impact: {opp.metric}
                         </div>
                       )}
                     </div>
                  </div>
                ))}
             </div>
           ) : (
             <Empty description="No detected opportunities" />
           )}
        </Card>

        {/* JOB RECOMMENDATIONS */}
        <Card className="rounded-3xl border border-slate-200 shadow-sm" title={<span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600">Job Orchestration</span>}>
           {job_recommendations?.length ? (
             <div className="space-y-3">
                {job_recommendations.map((jobRec: any, i: number) => (
                  <div key={i} className="p-4 rounded-2xl border border-slate-200 bg-white shadow-sm flex items-start justify-between gap-4">
                     <div className="min-w-0">
                       <Text className="block text-[10px] font-black text-indigo-500 uppercase mb-1 truncate">{jobRec.job_title}</Text>
                       <div className="space-y-1 mt-2">
                         {jobRec.suggestions.map((sug: any, j: number) => (
                            <div key={j} className="flex items-center gap-2 text-xs text-slate-600">
                               <div className="h-1 w-1 bg-slate-300 rounded-full" />
                               <span className="truncate">{sug}</span>
                            </div>
                         ))}
                       </div>
                     </div>
                     <Button size="small" className="text-[9px] font-black uppercase shrink-0">Review</Button>
                  </div>
                ))}
             </div>
           ) : (
             <Empty description="No job recommendations at this time" />
           )}
        </Card>
      </div>

    </div>
  )
}