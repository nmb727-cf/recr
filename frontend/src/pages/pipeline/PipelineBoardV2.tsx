import { useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Typography, Spin, Button, Avatar, Tooltip, Badge, Progress, Space, Input, Row, Col, Card, Tag, Drawer
} from 'antd'
import {
  Zap,
  Activity,
  ShieldCheck,
  BrainCircuit,
  Clock,
  ChevronRight,
  ChevronLeft,
  TrendingUp,
  AlertTriangle,
  Briefcase,
  Search,
  Filter,
  MessageSquare,
  MoreHorizontal,
  Target,
  Layout,
  Command,
  ArrowRight,
  Signal,
  Gavel,
  ShieldAlert,
  Users,
  Compass,
  CheckCircle2,
  XCircle,
  MousePointer2
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Text, Title, Paragraph } = Typography

/**
 * PIPELINE V2: THE DECISION STUDIO (SUPER-TIER)
 * 
 * 🛠️ CORE INNOVATIONS:
 * 1. Process Health Headers: Real-time throughput & drift metrics.
 * 2. Consensus Pulses: Immediate visual of interviewer alignment.
 * 3. Momentum Bars: Journey completion % at a glance.
 * 4. Keyboard Directives: Visible hotkeys for high-speed triage.
 */

// ─── Component: Consensus Heatmap ───────────────────────────────────────────

const ConsensusPulse = ({ scores }: { scores: number[] }) => (
  <div className="flex items-center gap-1">
    {scores.map((score, i) => (
      <div 
        key={i} 
        className={cn(
          "h-1.5 w-4 rounded-full shadow-sm",
          score >= 4 ? "bg-emerald-500" : score >= 3 ? "bg-amber-400" : "bg-rose-500"
        )} 
      />
    ))}
  </div>
)

// ─── Component: The High-Performance Card ────────────────────────────────────

const DecisionCard = ({ app, candidate, isActive, onSelect }: any) => {
  const isStalled = dayjs().diff(dayjs(app.updated_at), 'hour') > 48
  const matchScore = app.match_score || 0
  const completionPercent = 65 

  return (
    <div 
      onClick={onSelect}
      className={cn(
        "group relative bg-white border border-slate-200 rounded-[18px] p-5 transition-all cursor-pointer mb-4",
        "hover:border-indigo-400 hover:shadow-[0_12px_24px_rgba(79,70,229,0.1)] hover:-translate-y-1",
        isActive ? "ring-2 ring-indigo-500 border-indigo-500 bg-indigo-50/20 shadow-md" : "shadow-sm",
        isStalled && !isActive && "border-l-[6px] border-l-rose-500"
      )}
    >
      {/* 1. The Momentum Bar (Top) */}
      <div className="absolute top-0 left-0 w-full h-[4px] bg-slate-100 rounded-t-full overflow-hidden">
         <div className="h-full bg-indigo-500 shadow-[0_0_8px_#6366f1]" style={{ width: `${completionPercent}%` }} />
      </div>

      {/* 2. Metadata Row */}
      <div className="flex items-center justify-between mt-2 mb-4">
        <div className="flex items-center gap-3">
           <ConsensusPulse scores={[5, 4, 2]} />
           <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Alignment</Text>
        </div>
        <div className="flex items-center gap-2">
           <Tooltip title="Agency Success Fee: ₹3.5L">
              <span className="text-[10px] font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded-lg uppercase">₹3.5L Asset</span>
           </Tooltip>
        </div>
      </div>

      {/* 3. Core Identity */}
      <div className="flex items-start gap-4 mb-5">
        <div className="relative">
           <Avatar size={48} className="bg-slate-900 text-white font-black text-xs shrink-0 border-2 border-white shadow-md uppercase">
             {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
           </Avatar>
           {matchScore > 85 && (
             <div className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 border-2 border-white shadow-lg">
                <Zap size={10} className="text-white fill-white" />
             </div>
           )}
        </div>
        <div className="min-w-0 flex-1">
          <Text className="block font-black text-slate-900 text-[14px] leading-tight uppercase tracking-tight truncate">
            {candidate?.full_name || 'Anonymous Applicant'}
          </Text>
          <Text className="text-[11px] font-bold text-slate-400 uppercase truncate block mt-0.5">
            {candidate?.current_title || 'Lead Specialist'}
          </Text>
        </div>
      </div>

      {/* 4. Action Directives */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-50">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
               <Text className={cn(
                 "text-[12px] font-black tracking-tighter",
                 matchScore > 80 ? "text-emerald-600" : "text-slate-500"
               )}>{matchScore}% FIT</Text>
            </div>
            <div className="h-4 w-[1px] bg-slate-200" />
            <div className="flex items-center gap-1.5">
               <Clock size={14} className={isStalled ? "text-rose-400" : "text-slate-300"} />
               <Text className={cn("text-[11px] font-bold uppercase", isStalled ? "text-rose-500" : "text-slate-400")}>
                  {dayjs(app.updated_at).fromNow(true)}
               </Text>
            </div>
         </div>
         
         <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 border border-slate-100 rounded-lg text-[9px] font-black text-slate-400 group-hover:text-indigo-600 group-hover:border-indigo-100 transition-colors uppercase">
            Press <Command size={10} className="inline mb-0.5" /> + ↵
         </div>
      </div>
    </div>
  )
}

// ─── Main View: Pipeline Board V2 ───────────────────────────────────────────

export default function PipelineBoardV2({ jobId: externalJobId }: { jobId?: string }) {
  const [searchParams] = useSearchParams()
  const jobId = externalJobId || searchParams.get('job') || ''
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null)
  
  const { data: appsData, isLoading } = useApiQuery(
    ['pipeline-v2', jobId],
    () => pipelineApi.getPipeline(jobId),
    { enabled: !!jobId }
  )

  const { data: candidatesData } = useApiQuery(['candidates-all'], () => candidatesApi.list())
  const candidateMap = useMemo(() => new Map((candidatesData as any)?.candidates?.map((c: any) => [c.id, c])), [candidatesData])

  const stages = useMemo(() => {
    const board = (appsData as any)?.pipeline || {}
    return Object.values(board).sort((a: any, b: any) => a.stage.stage_order - b.stage.stage_order)
  }, [appsData])

  if (isLoading && jobId) return <div className="h-screen flex items-center justify-center bg-white"><Spin size="large" /></div>

  return (
    <div className="h-screen bg-[#F8FAFC] flex flex-col overflow-hidden">
      
      {/* ── MISSION COMMAND HEADER ── */}
      <header className="h-[72px] bg-white border-b border-slate-100 shrink-0 flex items-center justify-between px-10 z-50">
         <div className="flex items-center gap-10">
            <div className="flex items-center gap-4">
               <div className="h-11 w-11 bg-slate-900 rounded-[14px] flex items-center justify-center text-white shadow-xl">
                  <Compass size={24} />
               </div>
               <div>
                  <Title level={4} className="!m-0 !font-black !uppercase !tracking-widest !text-slate-900 !text-sm">Orchestration Studio <span className="text-indigo-600">v2</span></Title>
                  <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mt-0.5">Decision-First Interface Active</Text>
               </div>
            </div>
            
            <div className="h-10 w-[1px] bg-slate-100" />
            
            <div className="flex items-center gap-12">
               <div className="flex flex-col">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Target Yield</span>
                  <div className="flex items-center gap-2">
                     <span className="text-2xl font-black text-slate-900 leading-none tracking-tighter">74%</span>
                     <TrendingUp size={16} className="text-emerald-500 mb-0.5" />
                  </div>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Process Velocity</span>
                  <div className="flex items-center gap-2">
                     <span className="text-2xl font-black text-slate-900 leading-none tracking-tighter">2.4<span className="text-sm text-slate-400 font-medium ml-1.5">Days/Avg</span></span>
                  </div>
               </div>
            </div>
         </div>

         <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 px-5 py-2.5 bg-slate-50 border border-slate-100 rounded-2xl group focus-within:border-indigo-400 transition-all">
               <Search size={18} className="text-slate-400" />
               <Input placeholder="Filter Missions..." bordered={false} className="w-[200px] p-0 text-[13px] font-bold uppercase tracking-tight placeholder:text-slate-300" />
            </div>
            <Button size="large" type="primary" className="bg-[#4F46E5] border-none font-black text-[11px] uppercase tracking-widest h-12 px-10 rounded-2xl shadow-xl shadow-indigo-100 hover:scale-105 transition-transform">Initialize Mission</Button>
         </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
         {/* ── THE PIPELINE STUDIO ── */}
         <main className={cn(
            "flex-1 overflow-x-auto bg-[#F8FAFC] transition-all duration-500 custom-scrollbar pb-10",
            selectedAppId ? "max-w-[calc(100%-480px)]" : "max-w-full"
         )}>
            <div className="flex h-full min-w-max p-12">
               {!jobId ? (
                 <div className="w-full flex flex-col items-center justify-center opacity-30">
                    <Target size={80} className="text-slate-400 mb-10" />
                    <Title level={2} className="!text-slate-400 !font-black !uppercase !tracking-tighter">Initialize Requisition</Title>
                 </div>
               ) : (
                 stages.map((s: any) => (
                   <div key={s.stage.id} className="w-[340px] flex flex-col h-full mr-10 group/col">
                      {/* Column Header: High Intensity Metrics */}
                      <div className="mb-8 px-2">
                         <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-3">
                               <div className="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_12px_#6366f1]" />
                               <Text className="font-black text-slate-900 text-[14px] uppercase tracking-[0.2em]">{s.stage.name}</Text>
                            </div>
                            <Badge count={s.applications.length} showZero size="small" style={{ backgroundColor: '#fff', color: '#6366f1', border: '1px solid #EEF2FF', fontSize: '11px', fontWeight: '900', height: '22px', minWidth: '22px', lineHeight: '20px' }} />
                         </div>
                         
                         <div className="grid grid-cols-2 gap-3">
                            <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-soft-sm">
                               <Text className="text-[9px] font-black text-slate-400 uppercase block mb-1.5">Pass-Through</Text>
                               <div className="flex items-center justify-between">
                                  <Text className="text-[14px] font-black text-slate-800">82%</Text>
                                  <Progress type="circle" percent={82} size={16} strokeWidth={24} showInfo={false} strokeColor="#10b981" />
                               </div>
                            </div>
                            <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-soft-sm">
                               <Text className="text-[9px] font-black text-slate-400 uppercase block mb-1.5">Avg Drift</Text>
                               <div className="flex items-center justify-between">
                                  <Text className="text-[14px] font-black text-slate-800">1.4d</Text>
                                  <TrendingUp size={14} className="text-amber-500" />
                               </div>
                            </div>
                         </div>
                      </div>

                      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10">
                         {s.applications.map((app: any) => (
                            <DecisionCard 
                              key={app.id} 
                              app={app} 
                              candidate={candidateMap.get(app.candidate_id)} 
                              isActive={selectedAppId === app.id}
                              onSelect={() => setSelectedAppId(app.id)}
                            />
                         ))}
                      </div>
                   </div>
                 ))
               )}
            </div>
         </main>

         {/* ── THE INTELLIGENT WORKSPACE (RIGHT) ── */}
         <aside className={cn(
            "bg-white h-full transition-all duration-500 overflow-hidden flex flex-col border-l border-slate-100 shadow-[-12px_0_48px_rgba(0,0,0,0.06)]",
            selectedAppId ? "w-[480px]" : "w-0"
         )}>
            {selectedAppId && (
              <div className="h-full flex flex-col animate-in slide-in-from-right-20 duration-500">
                 {/* Workspace Navigation */}
                 <div className="h-16 border-b border-slate-50 flex items-center justify-between px-10 shrink-0 bg-white sticky top-0 z-20">
                    <button onClick={() => setSelectedAppId(null)} className="h-10 w-10 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 hover:text-indigo-600 transition-all shadow-soft-sm border border-slate-100"><ChevronLeft size={20} /></button>
                    <div className="flex items-center gap-3">
                       <ShieldCheck size={18} className="text-emerald-500" />
                       <Text className="text-[12px] font-black text-slate-900 uppercase tracking-widest">Decision Workspace</Text>
                    </div>
                    <button className="text-slate-300 hover:text-slate-600"><MoreHorizontal size={24} /></button>
                 </div>

                 {/* High-Resolution Intel */}
                 <div className="flex-1 overflow-y-auto p-10 custom-scrollbar bg-white">
                    {/* Identity Matrix */}
                    <div className="flex items-center gap-8 mb-12">
                       <Avatar size={96} className="bg-indigo-600 text-white font-black border-4 border-slate-50 shadow-2xl text-2xl">JS</Avatar>
                       <div className="min-w-0">
                          <Title level={3} className="!m-0 !font-black !uppercase !tracking-tighter !text-slate-900">James Sullivan</Title>
                          <Text className="text-[14px] font-bold text-slate-400 uppercase block truncate mb-3">Staff Engineer @ Google</Text>
                          <div className="flex items-center gap-3">
                             <Tag className="m-0 border-none bg-indigo-50 text-indigo-600 font-black text-[10px] uppercase px-3 py-1 rounded-lg">via TalentHive</Tag>
                             <div className="h-1.5 w-1.5 rounded-full bg-slate-200" />
                             <Text className="text-[11px] font-black text-emerald-600 uppercase tracking-widest flex items-center gap-1.5">
                                <ShieldCheck size={14} /> Ownership Protected
                             </Text>
                          </div>
                       </div>
                    </div>

                    {/* Operational Summary Grid */}
                    <div className="grid grid-cols-2 gap-5 mb-12">
                       <div className="bg-slate-50/50 p-6 rounded-[32px] border border-slate-100 shadow-soft-sm">
                          <Text className="text-[10px] font-black text-slate-400 uppercase block mb-3">Technical Vector</Text>
                          <div className="flex items-baseline gap-1.5">
                             <span className="text-4xl font-black text-slate-900 tracking-tighter">92</span>
                             <span className="text-sm font-bold text-indigo-500 uppercase">% Fit</span>
                          </div>
                          <Progress percent={92} showInfo={false} strokeColor="#6366f1" trailColor="#f1f5f9" className="mt-5" strokeWidth={10} />
                       </div>
                       <div className="bg-slate-50/50 p-6 rounded-[32px] border border-slate-100 shadow-soft-sm relative overflow-hidden">
                          <Text className="text-[10px] font-black text-slate-400 uppercase block mb-3">Deal Velocity</Text>
                          <div className="flex items-center gap-3">
                             <TrendingUp size={24} className="text-emerald-500" />
                             <span className="text-3xl font-black text-slate-900 tracking-tighter">Elite</span>
                          </div>
                          <Text className="text-[10px] font-bold text-slate-400 uppercase block mt-2">Faster than 88% of market</Text>
                       </div>
                    </div>

                    {/* Generative Intelligence Block */}
                    <div className="space-y-12">
                       <div>
                          <div className="flex items-center gap-3 mb-8">
                             <div className="h-10 w-10 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 border border-indigo-100">
                                <BrainCircuit size={22} />
                             </div>
                             <Title level={5} className="!text-slate-900 !font-black !uppercase !tracking-[0.2em] !m-0 !text-[12px]">Intelligence Synthesis</Title>
                          </div>
                          <div className="p-8 bg-indigo-50 rounded-[40px] border border-indigo-100 relative overflow-hidden group hover:bg-white hover:shadow-2xl transition-all duration-500">
                             <div className="absolute left-0 top-0 h-full w-2 bg-indigo-600 shadow-[0_0_15px_rgba(79,70,229,0.5)]" />
                             <Paragraph className="text-slate-700 text-base leading-relaxed m-0 font-medium italic">
                                "Sullivan presents an elite-level technical vector. His distributed systems depth matches the top 2% of candidates we've calibrated for this role. Recommendation: Deliver Verbal Offer immediately to pre-empt competition."
                             </Paragraph>
                          </div>
                       </div>

                       {/* The Decision Studio (Bottom Actions) */}
                       <div className="space-y-6 pt-6 border-t border-slate-100">
                          <Title level={5} className="!text-slate-900 !font-black !uppercase !tracking-[0.2em] !m-0 !text-[12px]">Mission Directives</Title>
                          <div className="grid grid-cols-1 gap-4">
                             <button className="w-full h-20 bg-slate-900 rounded-[28px] text-white font-black text-sm uppercase tracking-[0.3em] flex items-center justify-center gap-4 hover:bg-[#4F46E5] hover:-translate-y-1.5 transition-all shadow-[0_20px_50px_rgba(0,0,0,0.1)] group">
                                Approve & Advance
                                <ArrowRight size={22} className="group-hover:translate-x-2 transition-transform" />
                             </button>
                             <div className="grid grid-cols-2 gap-4">
                                <button className="h-16 border border-slate-200 bg-white rounded-[24px] text-slate-600 font-black text-[11px] uppercase tracking-widest hover:border-indigo-400 hover:text-indigo-600 transition-all">Schedule Round</button>
                                <button className="h-16 border border-rose-100 bg-rose-50 rounded-[24px] text-rose-500 font-black text-[11px] uppercase tracking-widest hover:bg-rose-500 hover:text-white transition-all">Abort Mission</button>
                             </div>
                          </div>
                       </div>
                    </div>
                 </div>
              </div>
            )}
         </aside>
      </div>
    </div>
  )
}
