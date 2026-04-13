import React, { useState } from 'react'
import { 
  Typography, 
  Card, 
  Statistic, 
  Tag, 
  Table, 
  Spin, 
  Alert, 
  Empty, 
  Progress, 
  Divider, 
  Button, 
  Tooltip, 
  Space,
  Badge,
  List,
  Avatar,
  Tabs
} from 'antd'
import { 
  BrainCircuit, 
  Zap, 
  TrendingUp, 
  Clock, 
  CheckCircle2, 
  Users, 
  Target, 
  Layers, 
  Activity,
  History,
  ShieldCheck,
  Search,
  RefreshCw,
  Lightbulb,
  ArrowRight
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'

dayjs.extend(relativeTime)

const { Title, Text } = Typography

export default function SystemIntelligenceMemory() {
  const [activeTab, setActiveTab] = useState('all')
  const { data, isLoading, error, refetch } = useApiQuery(
    ['system-intelligence-memory'],
    () => analyticsApi.getIntelligenceMemory(),
    { refetchOnWindowFocus: false, staleTime: 60000 }
  )

  const memories = (data as any)?.memories || (data as any)?.data?.memories || []

  const handleTriggerLearning = async () => {
    await analyticsApi.getIntelligenceMemory({ trigger_learning: 'true' })
    refetch()
  }

  if (isLoading && !memories.length) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Accessing System Intelligence Memory Layer..." />
      </div>
    )
  }

  const filteredMemories = activeTab === 'all' 
    ? memories 
    : memories.filter((m: any) => m.category === activeTab)

  return (
    <div className="mx-auto max-w-[1600px] p-6 lg:p-10 flex flex-col gap-8 min-h-screen bg-[#F8FAFC]">
      
      {/* ─── Header ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="h-12 w-12 rounded-2xl bg-slate-900 flex items-center justify-center text-indigo-400 shadow-xl border border-slate-800">
              <BrainCircuit size={28} />
            </div>
            <div>
              <Text className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400 block mb-0.5">Neural Storage / Global Learning</Text>
              <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">System Intelligence Memory</Title>
            </div>
          </div>
          <Text className="text-sm text-slate-500 max-w-2xl block">
            The persistence layer for the Hiring Operating System. This layer records successful patterns, speed benchmarks, and quality correlations to optimize future autonomous decisions.
          </Text>
        </div>
        <div className="flex items-center gap-3">
           <Button 
             icon={<RefreshCw size={14} />} 
             onClick={handleTriggerLearning}
             className="h-11 rounded-xl font-black uppercase text-[10px] tracking-widest bg-white border-slate-200 shadow-sm"
           >
             Trigger Learning Cycle
           </Button>
           <Tag className="m-0 rounded-full bg-indigo-600 text-white px-4 py-1.5 border-none font-black text-[10px] uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-indigo-100">
             <div className="h-2 w-2 rounded-full bg-white animate-pulse" /> Memory Active
           </Tag>
        </div>
      </div>

      {/* ─── Highlights ─── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
         <MemoryMetricCard label="Learned Patterns" value={memories.length} sub="Active Correlations" icon={<Zap size={20}/>} color="indigo" />
         <MemoryMetricCard label="Avg Confidence" value="84%" sub="Statistical Reliability" icon={<ShieldCheck size={20}/>} color="emerald" />
         <MemoryMetricCard label="Last Learn Cycle" value="Just Now" sub="Real-time Adaptation" icon={<History size={20}/>} color="blue" />
         <MemoryMetricCard label="Optimization Rate" value="+18.2%" sub="System efficiency lift" icon={<TrendingUp size={20}/>} color="amber" />
      </div>

      <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
         <div className="px-8 pt-8 pb-4 border-b border-slate-100 bg-white">
            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab}
              className="custom-intelligence-tabs"
              items={[
                { key: 'all', label: <TabLabel label="All Memories" count={memories.length} /> },
                { key: 'recruiter', label: <TabLabel label="Recruiter Patterns" count={memories.filter((m:any) => m.category === 'recruiter').length} /> },
                { key: 'agency', label: <TabLabel label="Agency Intelligence" count={memories.filter((m:any) => m.category === 'agency').length} /> },
                { key: 'pipeline', label: <TabLabel label="Pipeline Success" count={memories.filter((m:any) => m.category === 'pipeline').length} /> },
                { key: 'interview', label: <TabLabel label="Interview Benchmarks" count={memories.filter((m:any) => m.category === 'interview').length} /> },
              ]}
            />
         </div>
         
         <div className="p-8">
            {filteredMemories.length > 0 ? (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                 {filteredMemories.map((memory: any) => (
                   <MemoryCard key={memory.id} memory={memory} />
                 ))}
              </div>
            ) : (
              <Empty className="my-20" description="No learned patterns in this category yet." />
            )}
         </div>
      </Card>

    </div>
  )
}

function MemoryMetricCard({ label, value, sub, icon, color }: any) {
  return (
    <Card className="rounded-[2rem] border-none bg-white shadow-soft-sm">
       <div className="flex items-center gap-3 mb-3">
          <div className={cn("p-2 rounded-xl bg-slate-50", `text-${color}-600`)}>{icon}</div>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{label}</Text>
       </div>
       <Text className="text-2xl font-black text-slate-900 block leading-none">{value}</Text>
       <Text className="text-[10px] font-bold text-slate-400 uppercase mt-1.5 block tracking-tighter">{sub}</Text>
    </Card>
  )
}

function TabLabel({ label, count }: any) {
  return (
    <div className="flex items-center gap-2 px-1">
       <span className="text-[11px] font-black uppercase tracking-widest">{label}</span>
       <Badge count={count} className="intel-badge" />
    </div>
  )
}

function MemoryCard({ memory }: any) {
  const { category, attribute_key, entity_name, attribute_value, confidence_score, learned_at } = memory
  
  return (
    <div className="p-6 rounded-[2rem] border border-slate-100 bg-slate-50/30 hover:bg-white hover:border-indigo-200 transition-all group flex flex-col gap-4">
       <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
             <div className={cn("p-3 rounded-2xl bg-white shadow-sm border border-slate-100", 
               category === 'recruiter' ? "text-blue-600" :
               category === 'agency' ? "text-amber-600" :
               category === 'pipeline' ? "text-emerald-600" :
               "text-purple-600"
             )}>
                {category === 'recruiter' ? <Users size={20}/> : 
                 category === 'agency' ? <Target size={20}/> : 
                 category === 'pipeline' ? <Layers size={20}/> : 
                 <Lightbulb size={20}/>}
             </div>
             <div>
                <div className="flex items-center gap-2 mb-0.5">
                   <Tag className="m-0 border-none bg-slate-900 text-white text-[8px] font-black uppercase px-2 rounded-full">{category}</Tag>
                   <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{attribute_key.replace(/_/g, ' ')}</Text>
                </div>
                <Text className="text-sm font-black text-slate-800 block truncate max-w-[200px]">{entity_name || 'Global Pattern'}</Text>
             </div>
          </div>
          <div className="text-right">
             <div className="flex items-center gap-1 justify-end mb-1">
                <ShieldCheck size={12} className="text-emerald-500" />
                <Text className="text-[10px] font-black text-emerald-600">{(confidence_score * 100).toFixed(0)}% CONFIDENCE</Text>
             </div>
             <Text className="text-[9px] text-slate-400 font-bold uppercase">{dayjs(learned_at).fromNow()}</Text>
          </div>
       </div>

       <div className="p-4 bg-white rounded-2xl border border-slate-50 flex flex-wrap gap-4 items-center">
          {Object.entries(attribute_value).map(([key, val]: [string, any]) => (
            <div key={key} className="flex flex-col">
               <Text className="text-[9px] font-black text-slate-400 uppercase tracking-tighter">{key.replace(/_/g, ' ')}</Text>
               <Text className="text-sm font-black text-slate-700">{typeof val === 'number' ? val.toLocaleString() : String(val)}</Text>
            </div>
          ))}
       </div>

       <div className="flex items-center justify-between mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Text className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
             <Info size={10} /> Influencing autonomous scheduling and routing.
          </Text>
          <Button type="link" className="p-0 h-auto text-[10px] font-black uppercase tracking-widest flex items-center gap-1">
             Correlation Details <ArrowRight size={12} />
          </Button>
       </div>
    </div>
  )
}

function Info({ size, className }: any) {
  return <Lightbulb size={size} className={className} />
}
