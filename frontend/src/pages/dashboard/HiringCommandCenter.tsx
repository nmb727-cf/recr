import React from 'react'
import {
  Card, Typography, Tag, Avatar, Table, Tooltip, Badge, Divider, Button, Spin, Empty, Progress
} from 'antd'
import {
  Zap, AlertTriangle, TrendingUp, ChevronRight, MessageSquare, UserPlus, Clock,
  CheckCircle, Users, ShieldCheck, DollarSign, Target, BrainCircuit, Activity, BarChart3, Briefcase, Layers
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { cn } from '@/utils/cn'
import dayjs from 'dayjs'

const { Title, Text } = Typography

export default function HiringCommandCenter() {
  const { data: brainData, isLoading } = useApiQuery(
    ['global-hiring-brain'],
    () => requisitionsApi.getGlobalHiringBrain()
  )

  const brain = (brainData as any)?.intelligence ?? (brainData as any)?.data?.intelligence

  return (
    <div className="max-w-[1600px] mx-auto p-8 space-y-8 animate-in fade-in duration-700">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-indigo-200 shadow-lg">
              <BrainCircuit size={24} />
            </div>
            <Title level={2} className="!m-0 uppercase tracking-tighter font-black text-slate-900">Hiring Command Center</Title>
          </div>
          <Text className="text-slate-400 font-bold uppercase tracking-widest text-[10px] ml-14">Global Mission Control • Recruitment Operating System</Text>
        </div>
        <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-100 shadow-soft-sm">
           <div className="flex flex-col items-end px-4 border-r border-slate-100">
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">System Status</Text>
              <div className="flex items-center gap-1.5">
                 <div className={cn("h-1.5 w-1.5 rounded-full animate-pulse", isLoading ? "bg-amber-500" : "bg-emerald-500")} />
                 <Text className={cn("text-11px font-black uppercase", isLoading ? "text-amber-600" : "text-emerald-600")}>
                   {isLoading ? 'Processing...' : 'Operational'}
                 </Text>
              </div>
           </div>
           <Button type="primary" className="h-10 bg-indigo-600 border-none rounded-xl font-black text-[10px] uppercase tracking-widest px-6 shadow-indigo-100 shadow-lg flex items-center gap-2">
              Generate Global Report <ChevronRight size={14} />
           </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-24 text-center bg-white rounded-3xl border border-slate-100 shadow-soft-sm">
          <Spin size="large" tip="Synthesizing Global Signals..." />
        </div>
      ) : !brain ? (
        <div className="p-24 text-center bg-white rounded-3xl border border-slate-100 shadow-soft-sm">
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div className="space-y-2">
                <Text className="text-slate-400 font-black uppercase tracking-widest block">Global intelligence data not available</Text>
                <Text className="text-slate-300 text-[10px] uppercase font-bold">Please ensure you have active job requisitions and candidate applications.</Text>
              </div>
            } 
          />
        </div>
      ) : (
        <>
          {/* ── Grid Row 1: Active Hiring & Pipeline Health ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Hiring Overview */}
        <Card 
          className="lg:col-span-7 rounded-3xl border-none shadow-soft-sm overflow-hidden"
          title={
            <div className="flex items-center gap-2">
              <Briefcase size={16} className="text-indigo-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Active Hiring Overview</span>
            </div>
          }
        >
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Active Jobs', value: brain?.overview?.active_jobs || 0, color: 'indigo', icon: <Briefcase size={20} /> },
              { label: 'Delayed (>30d)', value: brain?.job_health?.stuck_jobs || 0, color: 'rose', icon: <Clock size={20} /> },
              { label: 'Near Completion', value: brain?.overview?.offers_pending || 0, color: 'emerald', icon: <Target size={20} /> },
              { label: 'Critical Risks', value: brain?.job_health?.at_risk_count || 0, color: 'amber', icon: <AlertTriangle size={20} /> },
            ].map((stat, i) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-50/50 border border-slate-100/50 hover:bg-white hover:shadow-sm transition-all group">
                <div className={cn("p-2 w-fit rounded-xl mb-3", `bg-${stat.color}-50 text-${stat.color}-600`)}>
                  {stat.icon}
                </div>
                <Text className="text-[9px] font-black text-slate-400 uppercase block mb-1 tracking-tighter">{stat.label}</Text>
                <Text className="text-2xl font-black text-slate-800 leading-none">{stat.value}</Text>
              </div>
            ))}
          </div>
        </Card>

        {/* Pipeline Health */}
        <Card 
          className="lg:col-span-5 rounded-3xl border-none shadow-soft-sm overflow-hidden"
          title={
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-indigo-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Global Pipeline Health</span>
            </div>
          }
        >
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <Text className="text-[10px] font-black text-slate-400 uppercase block">Total Candidates</Text>
                <Text className="text-3xl font-black text-slate-800">{brain?.overview?.candidates_in_pipeline || 0}</Text>
              </div>
              <div className="text-right">
                <Text className="text-[10px] font-black text-emerald-600 uppercase bg-emerald-50 px-2 py-1 rounded-lg">+12% Growth</Text>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 border-t border-slate-50 pt-5">
              <div>
                <Text className="text-[9px] font-black text-slate-400 uppercase block">Stalled</Text>
                <Text className="text-sm font-black text-rose-600">{brain?.pipeline_intelligence?.stalled_candidates || 0}</Text>
              </div>
              <div>
                <Text className="text-[9px] font-black text-slate-400 uppercase block">Interviews</Text>
                <Text className="text-sm font-black text-indigo-600">{brain?.overview?.interviews_scheduled || 0}</Text>
              </div>
              <div>
                <Text className="text-[9px] font-black text-slate-400 uppercase block">Offers</Text>
                <Text className="text-sm font-black text-emerald-600">{brain?.overview?.offers_pending || 0}</Text>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* ── Grid Row 2: SLA & Intelligence Alerts ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* SLA Global Alerts */}
        <Card 
          className="lg:col-span-4 rounded-3xl border-none shadow-soft-sm overflow-hidden bg-rose-50/20"
          title={
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-rose-600" />
              <span className="text-[11px] font-black uppercase tracking-widest text-rose-700">SLA Engine Alerts</span>
            </div>
          }
        >
          <div className="space-y-4">
            <div className="p-4 bg-white rounded-2xl border border-rose-100 flex items-center justify-between shadow-soft-sm">
              <div>
                <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Overdue Actions</Text>
                <Text className="text-xl font-black text-rose-600">{brain?.pipeline_intelligence?.stalled_candidates || 0}</Text>
              </div>
              <AlertTriangle size={24} className="text-rose-400" />
            </div>
            <div className="p-4 bg-white rounded-2xl border border-rose-100 flex items-center justify-between shadow-soft-sm">
              <div>
                <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Critical Breaches</Text>
                <Text className="text-xl font-black text-rose-800">{brain?.job_health?.stuck_jobs || 0}</Text>
              </div>
              <Zap size={24} className="text-rose-600 fill-rose-600" />
            </div>
          </div>
        </Card>

        {/* Intelligence Risks */}
        <Card 
          className="lg:col-span-4 rounded-3xl border-none shadow-soft-sm overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <Target size={16} className="text-amber-500" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-600">Risk detection</span>
            </div>
          }
        >
          <div className="space-y-3">
            {(brain?.job_health?.at_risk_details || []).map((risk: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50/50 rounded-2xl border border-slate-100 transition-colors hover:border-amber-200">
                <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0 shadow-[0_0_8px_rgba(245,158,11,0.5)]" />
                <Text className="text-[11px] font-bold text-slate-600 leading-relaxed uppercase tracking-tight">{risk.title}: {risk.reason}</Text>
              </div>
            ))}
            {(brain?.job_health?.at_risk_details || []).length === 0 && <Empty description="No risks detected" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
          </div>
        </Card>

        {/* Next Best Actions */}
        <Card 
          className="lg:col-span-4 rounded-3xl border-none shadow-soft-sm overflow-hidden bg-slate-900"
          title={
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-400" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-400">Next Best Actions</span>
            </div>
          }
        >
          <div className="space-y-3">
            {(brain?.next_best_actions || [{ text: 'Review team performance metrics' }, { text: 'Audit recent job applications' }]).map((action: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-800 rounded-2xl border border-slate-700 hover:bg-slate-700 transition-colors cursor-pointer group">
                <div className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-400 shrink-0 group-hover:bg-white transition-colors" />
                <Text className="text-[11px] font-bold text-slate-300 leading-relaxed uppercase group-hover:text-white transition-colors">{action.text}</Text>
              </div>
            ))}
            <Button block type="link" className="text-indigo-400 font-black text-[10px] uppercase tracking-widest mt-2">View Team Task Queue</Button>
          </div>
        </Card>
      </div>

      {/* ── Summary Indicator ───────────────────────────────────────────── */}
      <div className="p-8 rounded-3xl bg-indigo-600 text-white flex flex-col md:flex-row items-center justify-between gap-8 shadow-indigo-200 shadow-xl border border-indigo-500">
        <div className="flex items-center gap-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 border border-white/20 backdrop-blur-sm">
            <Activity size={32} />
          </div>
          <div>
            <h3 className="text-xl font-black uppercase tracking-tighter mb-1 leading-none">Global Hiring Health is Optimal</h3>
            <p className="text-indigo-100 text-sm font-medium opacity-80 uppercase tracking-widest">Hiring AI Brain has synthesized 1,450+ global signals today.</p>
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <Text className="text-[10px] font-black text-indigo-200 uppercase block mb-1">Global Brain Index</Text>
            <Text className="text-3xl font-black">8.4<span className="text-sm opacity-50"> / 10</span></Text>
          </div>
          <div className="h-12 w-[1px] bg-white/20 mx-4 hidden md:block" />
          <Button className="h-12 rounded-xl bg-white text-indigo-600 border-none font-black text-[10px] uppercase tracking-widest px-8 hover:bg-indigo-50 transition-all">
            Open Advanced Analytics
          </Button>
        </div>
      </div>
        </>
      )}
    </div>
  )
}
