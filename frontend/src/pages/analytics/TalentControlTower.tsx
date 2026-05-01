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
  Select, 
  DatePicker, 
  Space,
  Badge,
  List,
  Avatar,
  Modal,
  Form,
  Input,
  message
} from 'antd'
import { 
  Activity, 
  AlertTriangle, 
  ShieldAlert, 
  Users, 
  Zap, 
  CheckCircle2, 
  TrendingUp, 
  Briefcase,
  Layers,
  Target,
  Settings2,
  Clock,
  ArrowUpRight,
  UserCheck,
  AlertCircle,
  Filter,
  Calendar,
  Search,
  MoreVertical,
  Bell,
  RefreshCw,
  UserPlus,
  Link,
  ChevronRight,
  ArrowUpCircle as EscalateIcon,
  Plus,
  Send
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { cn } from '@/utils/cn'
import { useNavigate } from 'react-router-dom'

dayjs.extend(relativeTime)

const { Title, Text } = Typography
const { RangePicker } = DatePicker

export default function TalentControlTower() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<any>({
    time_range: 'this_month',
    department_id: undefined,
    recruiter_id: undefined,
    job_priority: undefined
  })
  const [quickActionModal, setQuickActionModal] = useState<string | null>(null)

  const { data, isLoading, error, refetch } = useApiQuery(
    ['talent-control-tower', filters],
    () => analyticsApi.getControlTower(filters),
    { refetchOnWindowFocus: false, staleTime: 30000 }
  )

  const towerData = (data as any)?.control_tower || (data as any)?.data?.control_tower

  if (isLoading && !towerData) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <Spin size="large" tip="Initiating Talent Control Tower..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert 
          type="error" 
          showIcon 
          message="Control Tower Offline" 
          description={(error as any)?.message || 'Global aggregation service failure.'} 
        />
      </div>
    )
  }

  if (!towerData) return <Empty className="my-16" />

  const { 
    system_health, 
    pipeline_health, 
    team_capacity, 
    source_health, 
    automation_health, 
    ai_recommendations, 
    activity_feed,
    alerts,
    last_updated 
  } = towerData

  const handleQuickAction = (action: string) => {
    setQuickActionModal(action)
  }

  return (
    <div className="mx-auto max-w-[1800px] p-6 lg:p-10 flex flex-col gap-8 min-h-screen bg-[#F8FAFC]">
      
      {/* ─── Global Filters & Header ─── */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 bg-white p-6 rounded-[2.5rem] border border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-indigo-200 shadow-lg">
            <Activity size={28} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <Badge status="processing" color="indigo" />
              <Text className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">Hiring Operating System</Text>
            </div>
            <Title level={3} className="!m-0 tracking-tight text-slate-900 font-black">
              Talent Control Tower
            </Title>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Select 
            placeholder="Department" 
            className="w-40" 
            allowClear
            onChange={(v) => setFilters({...filters, department_id: v})}
          >
            <Select.Option value="eng">Engineering</Select.Option>
            <Select.Option value="product">Product</Select.Option>
            <Select.Option value="design">Design</Select.Option>
          </Select>
          <Select 
            placeholder="Recruiter" 
            className="w-40" 
            allowClear
            onChange={(v) => setFilters({...filters, recruiter_id: v})}
          >
            <Select.Option value="r1">Sarah Connor</Select.Option>
            <Select.Option value="r2">John Smith</Select.Option>
          </Select>
          <Select 
            placeholder="Priority" 
            className="w-32" 
            allowClear
            onChange={(v) => setFilters({...filters, job_priority: v})}
          >
            <Select.Option value="critical">Critical</Select.Option>
            <Select.Option value="high">High</Select.Option>
            <Select.Option value="normal">Normal</Select.Option>
          </Select>
          <Select 
            value={filters.time_range}
            className="w-32" 
            onChange={(v) => setFilters({...filters, time_range: v})}
          >
            <Select.Option value="today">Today</Select.Option>
            <Select.Option value="this_week">This Week</Select.Option>
            <Select.Option value="this_month">This Month</Select.Option>
            <Select.Option value="custom">Custom</Select.Option>
          </Select>
          {filters.time_range === 'custom' && <RangePicker className="w-64" />}
          
          <Divider type="vertical" className="h-8 mx-2" />
          
          <Button 
            icon={<RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />} 
            onClick={() => refetch()}
            className="rounded-xl font-bold uppercase text-[10px] tracking-widest border-slate-200"
          >
            Sync
          </Button>
        </div>
      </div>

      {/* ─── Section 1: Executive Overview ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-6">
        <HealthCard label="Active Jobs" value={system_health.active_jobs} sub="Requisitions" icon={<Briefcase size={20}/>} color="indigo" onClick={() => navigate('/jobs')} />
        <HealthCard label="Open Positions" value={system_health.open_headcount} sub="Headcount" icon={<Target size={20}/>} color="blue" onClick={() => navigate('/jobs')} />
        <HealthCard label="Pipeline Load" value={system_health.candidates_in_pipeline} sub="Active Candidates" icon={<Layers size={20}/>} color="emerald" onClick={() => navigate('/pipeline')} />
        <HealthCard label="Interviews" value={system_health.interviews_scheduled} sub="This Week" icon={<Clock size={20}/>} color="amber" onClick={() => navigate('/interviews')} />
        <HealthCard label="Offers" value={system_health.offers_pending} sub="Pending Approval" icon={<Zap size={20}/>} color="purple" onClick={() => navigate('/pipeline?status=offer')} />
        <HealthCard label="Hires" value={system_health.hires_this_month} sub={filters.time_range.replace('_', ' ')} icon={<UserCheck size={20}/>} color="rose" onClick={() => navigate('/pipeline?status=joined')} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* ─── Left Column (8 cols) ─── */}
        <div className="lg:col-span-8 flex flex-col gap-8">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* ─── Section 2: Real-Time Activity ─── */}
            <Card 
              className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" 
              title={<SectionTitle label="Real-Time Activity" icon={<Activity size={16}/>} />}
              bodyStyle={{ padding: 0 }}
            >
              <div className="max-h-[400px] overflow-y-auto">
                <List
                  dataSource={activity_feed}
                  renderItem={(item: any) => (
                    <div key={item.id} className="p-4 border-b border-slate-50 hover:bg-slate-50 transition-colors flex items-start gap-4">
                      <div className={cn("p-2 rounded-xl mt-1", 
                        item.action_type.includes('joined') ? "bg-emerald-50 text-emerald-600" :
                        item.action_type.includes('offer') ? "bg-purple-50 text-purple-600" :
                        item.action_type.includes('interview') ? "bg-amber-50 text-amber-600" :
                        "bg-blue-50 text-blue-600"
                      )}>
                        {item.action_type.includes('interview') ? <Clock size={16}/> : <Zap size={16}/>}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <Text className="text-sm font-black text-slate-800 truncate">
                            {item.action_type.replace(/_/g, ' ')}
                          </Text>
                          <Text className="text-[10px] text-slate-400 font-bold whitespace-nowrap">{dayjs(item.created_at).fromNow()}</Text>
                        </div>
                        <Text className="text-xs text-slate-500 block truncate">Target: {item.target_type} ({item.target_id.slice(0,8)})</Text>
                      </div>
                    </div>
                  )}
                />
              </div>
              <div className="p-4 bg-slate-50 text-center border-t border-slate-100">
                <Button type="link" className="text-xs font-black uppercase tracking-widest text-indigo-600">View Full Audit Log</Button>
              </div>
            </Card>

            {/* ─── Section 8: Alerts & Risks ─── */}
            <Card 
              className="rounded-[2.5rem] border-slate-200 shadow-sm" 
              title={<SectionTitle label="Alerts & Risks" icon={<Bell size={16}/>} />}
            >
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                {alerts.map((alert: any, i: number) => (
                  <div 
                    key={i} 
                    className={cn(
                      "p-4 rounded-3xl border flex items-start gap-4 cursor-pointer hover:shadow-md transition-all",
                      alert.severity === 'critical' ? "bg-rose-50 border-rose-100" :
                      alert.severity === 'high' ? "bg-orange-50 border-orange-100" :
                      alert.severity === 'medium' ? "bg-amber-50 border-amber-100" :
                      "bg-blue-50 border-blue-100"
                    )}
                    onClick={() => alert.job_id && navigate(`/jobs/${alert.job_id}`)}
                  >
                    <div className={cn("p-2 rounded-xl mt-0.5", 
                      alert.severity === 'critical' ? "bg-rose-600 text-white" :
                      alert.severity === 'high' ? "bg-orange-500 text-white" :
                      alert.severity === 'medium' ? "bg-amber-500 text-white" :
                      "bg-blue-500 text-white"
                    )}>
                      <AlertCircle size={18} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Tag className="m-0 border-none bg-black/10 text-black/60 text-[8px] font-black uppercase px-2 rounded-full">
                          {alert.severity}
                        </Tag>
                        <Text className="text-xs font-black text-slate-800 uppercase tracking-tight">{alert.title}</Text>
                      </div>
                      <Text className="text-xs text-slate-600 leading-snug">{alert.description}</Text>
                    </div>
                  </div>
                ))}
                {alerts.length === 0 && (
                  <div className="text-center py-12">
                    <CheckCircle2 size={40} className="text-emerald-400 mx-auto mb-3 opacity-40" />
                    <Text className="text-sm font-bold text-slate-400">System Healthy. No Active Alerts.</Text>
                  </div>
                )}
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
             {/* ─── Section 4: Pipeline Health ─── */}
             <Card 
               className="rounded-[2.5rem] border-slate-200 shadow-sm" 
               title={<SectionTitle label="Pipeline Health" icon={<Layers size={16}/>} />}
               extra={<Button type="link" className="p-0 text-xs font-bold" onClick={() => navigate('/pipeline')}>Analytics</Button>}
             >
                <div className="space-y-8">
                   <div className="grid grid-cols-2 gap-6">
                      <div className="p-4 bg-slate-50 rounded-3xl border border-slate-100">
                         <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Avg Velocity</Text>
                         <Text className="text-2xl font-black text-slate-800">4.2d</Text>
                         <Text className="text-[10px] font-bold text-emerald-600 flex items-center gap-1 mt-1"><TrendingUp size={10}/> -12% faster</Text>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-3xl border border-slate-100">
                         <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Pass Rate</Text>
                         <Text className="text-2xl font-black text-slate-800">28%</Text>
                         <Text className="text-[10px] font-bold text-slate-400 block mt-1">Screening to Offer</Text>
                      </div>
                   </div>
                   
                   <div className="space-y-4">
                      <Text className="text-xs font-black text-slate-800 uppercase tracking-widest block mb-4">Stage Distribution</Text>
                      {pipeline_health.stages.slice(0, 5).map((stage: any) => (
                        <div key={stage.status} className="space-y-1.5 cursor-pointer hover:bg-slate-50 p-2 rounded-xl transition-colors" onClick={() => navigate(`/pipeline?status=${stage.status}`)}>
                           <div className="flex justify-between items-center px-1">
                              <Text className="text-[10px] font-bold text-slate-600 uppercase">{stage.status}</Text>
                              <Text className="text-[10px] font-black text-slate-900">{stage.count}</Text>
                           </div>
                           <Progress 
                             percent={(stage.count / system_health.candidates_in_pipeline) * 100} 
                             showInfo={false} 
                             strokeColor={stage.status === 'offer' ? '#8b5cf6' : stage.status === 'interview' ? '#f59e0b' : '#3b82f6'} 
                             strokeWidth={6} 
                             trailColor="#f1f5f9"
                           />
                        </div>
                      ))}
                   </div>
                </div>
             </Card>

             {/* ─── Section 5: Team Capacity ─── */}
             <Card className="rounded-[2.5rem] border-slate-200 shadow-sm" title={<SectionTitle label="Team Capacity" icon={<Users size={16}/>} />}>
                <div className="space-y-8">
                   <div className="flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                         <Text className="text-xs font-black text-slate-800">Recruiter Workload</Text>
                         <Tag color={team_capacity.load_summary.overloaded > 0 ? 'orange' : 'green'} className="m-0 rounded-full font-black text-[9px]">
                           {team_capacity.load_summary.overloaded > 0 ? 'Action Needed' : 'Optimized'}
                         </Tag>
                      </div>
                      <Progress 
                        percent={(team_capacity.load_summary.overloaded / team_capacity.load_summary.total_recruiters) * 100} 
                        success={{ percent: 0 }} 
                        strokeColor="#f97316" 
                        trailColor="#ecfdf5"
                        showInfo={false}
                        strokeWidth={12}
                        className="my-1"
                      />
                      <Text className="text-[10px] text-slate-500 font-bold">
                        {team_capacity.load_summary.overloaded} of {team_capacity.load_summary.total_recruiters} recruiters currently overloaded.
                      </Text>
                   </div>

                   <Divider className="!my-0 border-slate-100" />

                   <div className="grid grid-cols-2 gap-6">
                      <div className="p-5 bg-indigo-50/50 rounded-[2rem] border border-indigo-100/50 text-center">
                         <Text className="text-[10px] font-black text-indigo-400 uppercase block mb-1">Avg Load</Text>
                         <Text className="text-2xl font-black text-indigo-900">{team_capacity.load_summary.avg_candidates_per_recruiter}</Text>
                         <Text className="text-[9px] font-bold text-indigo-500 block mt-1">Candidates / User</Text>
                      </div>
                      <div className="p-5 bg-amber-50/50 rounded-[2rem] border border-amber-100/50 text-center cursor-pointer hover:bg-amber-100/50 transition-colors" onClick={() => navigate('/pipeline?status=screening')}>
                         <Text className="text-[10px] font-black text-amber-500 uppercase block mb-1">HM Reviews</Text>
                         <Badge count={team_capacity.hm_bottlenecks} offset={[5, 0]}>
                            <Text className="text-2xl font-black text-amber-900">{team_capacity.hm_bottlenecks}</Text>
                         </Badge>
                         <Text className="text-[9px] font-bold text-amber-600 block mt-1">Bottlenecks</Text>
                      </div>
                   </div>
                   
                   <Button block className="h-12 rounded-2xl font-black uppercase text-[10px] tracking-widest bg-slate-900 text-white border-none hover:!bg-indigo-600" onClick={() => navigate('/talent-pools')}>
                      View Resource Planner
                   </Button>
                </div>
             </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
             {/* ─── Section 6: Source Health ─── */}
             <Card 
               className="rounded-[2.5rem] border-slate-200 shadow-sm" 
               title={<SectionTitle label="Source Health" icon={<Target size={16}/>} />}
             >
                <div className="space-y-6">
                   <div className="flex items-center justify-between">
                      <div>
                         <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Active Partners</Text>
                         <Text className="text-2xl font-black text-slate-800">{source_health.active_partners}</Text>
                      </div>
                      <div className="text-right">
                         <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1">Sourcing Gaps</Text>
                         <Text className="text-2xl font-black text-rose-600">{source_health.sourcing_gap_jobs} Jobs</Text>
                      </div>
                   </div>
                   
                   <List
                     dataSource={source_health.top_agencies}
                     renderItem={(agency: any, i: number) => (
                       <div key={i} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-2xl mb-2 hover:bg-white hover:border-indigo-200 transition-all group cursor-pointer" onClick={() => navigate('/agencies')}>
                          <div className="flex items-center gap-3">
                             <Avatar shape="square" className="bg-white border border-slate-200 text-slate-400 font-black text-xs">AG</Avatar>
                             <div>
                                <Text className="text-xs font-black text-slate-800 block">Agency {agency.agency_id.slice(0,5)}</Text>
                                <Text className="text-[10px] text-slate-400 font-bold">{agency.hires} hires total</Text>
                             </div>
                          </div>
                          <Tag className="m-0 border-none bg-emerald-100 text-emerald-700 font-black text-[10px] px-3 py-1 rounded-full group-hover:bg-emerald-600 group-hover:text-white transition-colors">{agency.score}%</Tag>
                       </div>
                     )}
                   />
                </div>
             </Card>

             {/* ─── Section 7: Automation Health ─── */}
             <Card 
               className="rounded-[2.5rem] border-slate-200 shadow-sm" 
               title={<SectionTitle label="Automation Health" icon={<Settings2 size={16}/>} />}
             >
                <div className="flex flex-col gap-8">
                   <div className="flex items-center gap-6">
                      <div className="relative">
                        <Progress 
                          type="circle" 
                          percent={automation_health.success_rate} 
                          strokeColor="#4f46e5" 
                          strokeWidth={12} 
                          width={100}
                        />
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                           <Text className="text-xl font-black text-slate-800 leading-none">{automation_health.success_rate}%</Text>
                           <Text className="text-[8px] font-bold text-slate-400 uppercase mt-1">Success</Text>
                        </div>
                      </div>
                      <div className="flex-1 space-y-4">
                         <div>
                            <div className="flex justify-between items-center mb-1">
                               <Text className="text-[10px] font-bold text-slate-500 uppercase">Process Autonomy</Text>
                               <Text className="text-[10px] font-black text-emerald-600">HIGH</Text>
                            </div>
                            <Progress percent={85} showInfo={false} strokeColor="#10b981" strokeWidth={6} trailColor="#f1f5f9" />
                         </div>
                         <div className="grid grid-cols-2 gap-4">
                            <div>
                               <Text className="text-lg font-black text-rose-600 block leading-none">{automation_health.failed_count}</Text>
                               <Text className="text-[9px] font-bold uppercase text-slate-400">Failed Runs</Text>
                            </div>
                            <div>
                               <Text className="text-lg font-black text-amber-600 block leading-none">{automation_health.blocked_actions}</Text>
                               <Text className="text-[9px] font-bold uppercase text-slate-400">Escalated</Text>
                            </div>
                         </div>
                      </div>
                   </div>
                   
                   <div className="p-4 bg-slate-900 rounded-3xl text-white">
                      <div className="flex items-center gap-2 mb-2">
                         <Zap size={14} className="text-indigo-400" />
                         <Text className="text-[10px] font-black uppercase tracking-widest text-indigo-200">System Optimization</Text>
                      </div>
                      <Text className="text-xs text-slate-400 block mb-3 leading-relaxed">AI suggests automating 12 repetitive screening tasks based on current system patterns.</Text>
                      <Button block className="bg-indigo-600 border-none text-white font-black uppercase text-[10px] tracking-widest h-10 rounded-xl" onClick={() => navigate('/jobs')}>Deploy Suggested Rules</Button>
                   </div>
                </div>
             </Card>
          </div>

        </div>

        {/* ─── Right Column (4 cols) ─── */}
        <div className="lg:col-span-4 flex flex-col gap-8">
          
           {/* ─── Section 10: Quick Actions ─── */}
           <Card className="rounded-[2.5rem] border-slate-200 shadow-indigo-100 shadow-2xl" bodyStyle={{ padding: '24px' }}>
              <Text className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-400 block mb-6">Command Controls</Text>
              <div className="grid grid-cols-1 gap-3">
                 <CommandButton label="Assign Recruiter" icon={<UserPlus size={18}/>} color="indigo" onClick={() => handleQuickAction('assign')} />
                 <CommandButton label="Add Partner Agency" icon={<Link size={18}/>} color="blue" onClick={() => handleQuickAction('agency')} />
                 <CommandButton label="Escalate Stuck Job" icon={<EscalateIcon size={18}/>} color="rose" onClick={() => handleQuickAction('escalate')} />
                 <CommandButton label="Global Priority Change" icon={<ShieldAlert size={18}/>} color="amber" onClick={() => handleQuickAction('priority')} />
                 <CommandButton label="Broadcast Hiring Drive" icon={<Send size={18}/>} color="emerald" onClick={() => handleQuickAction('broadcast')} />
              </div>
           </Card>

           {/* ─── Section 9: AI Recommendations ─── */}
           <Card className="rounded-[2.5rem] border-indigo-200 bg-indigo-50/20 shadow-sm" title={<SectionTitle label="AI Recommendations" icon={<Zap size={16} className="text-indigo-600"/>} />}>
              <div className="flex flex-col gap-4">
                 {ai_recommendations.smart_actions.slice(0, 3).map((action: any, i: number) => (
                   <div key={i} className="p-5 bg-white border border-indigo-100 rounded-[2rem] shadow-soft-sm group cursor-pointer hover:border-indigo-400 hover:shadow-indigo-100 transition-all">
                      <div className="flex items-center justify-between mb-2">
                         <Tag className="m-0 border-none bg-indigo-50 text-indigo-700 text-[9px] font-black uppercase px-2 py-0.5 rounded-full">{action.category}</Tag>
                         <ArrowUpRight size={14} className="text-slate-300 group-hover:text-indigo-600 transition-colors" />
                      </div>
                      <Text className="block text-sm font-black text-slate-800 leading-tight mb-1">{action.title}</Text>
                      <Text className="block text-xs text-slate-500 leading-relaxed">{action.description}</Text>
                   </div>
                 ))}
                 
                 <Divider className="!my-2 border-indigo-100" />
                 
                 <div className="space-y-4">
                    <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2"><AlertCircle size={12}/> Critical Opportunities</Text>
                    {ai_recommendations.opportunities.slice(0, 2).map((opp: any, i: number) => (
                      <div key={i} className="flex items-start gap-3 p-2 hover:bg-white rounded-xl transition-colors cursor-pointer group">
                         <div className="h-2 w-2 rounded-full bg-indigo-400 mt-1.5 shrink-0 animate-pulse" />
                         <div>
                            <Text className="text-xs font-bold text-slate-700 block group-hover:text-indigo-600 transition-colors">{opp.title}</Text>
                            <Text className="text-[10px] text-slate-500 leading-relaxed">{opp.description}</Text>
                         </div>
                      </div>
                    ))}
                 </div>
              </div>
           </Card>

           {/* ─── Hiring Health / Integrity ─── */}
           <Card className="rounded-[2.5rem] border-emerald-100 bg-emerald-50/10 shadow-sm" title={<SectionTitle label="System Integrity" icon={<CheckCircle2 size={16} className="text-emerald-600"/>} />}>
              <div className="space-y-6">
                 <div>
                    <div className="flex justify-between items-center mb-2">
                       <Text className="text-xs font-bold text-slate-600">Global Hiring Health</Text>
                       <Text className="text-xs font-black text-emerald-600">94.2%</Text>
                    </div>
                    <Progress percent={94.2} showInfo={false} strokeColor="#10b981" strokeWidth={10} trailColor="#f1f5f9" />
                 </div>

                 <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                       <Text className="text-slate-500">System Uptime</Text>
                       <Text className="font-black text-slate-800">99.99%</Text>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                       <Text className="text-slate-500">API Latency</Text>
                       <Text className="font-black text-slate-800">42ms</Text>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                       <Text className="text-slate-500">Data Integrity</Text>
                       <Text className="font-black text-emerald-600">Verified</Text>
                    </div>
                 </div>
                 
                 <div className="p-4 bg-emerald-950 rounded-[2rem] text-center">
                    <Text className="text-[10px] font-black uppercase tracking-widest text-emerald-400 block mb-1">Audit Status</Text>
                    <Text className="text-xs font-bold text-white">LATEST AUDIT PASSED</Text>
                 </div>
              </div>
           </Card>

        </div>

      </div>

      {/* ─── Quick Action Modals ─── */}
      <Modal
        title={<SectionTitle label={quickActionModal?.toUpperCase() || ''} icon={<Zap size={16}/>} />}
        open={!!quickActionModal}
        onCancel={() => setQuickActionModal(null)}
        footer={null}
        centered
        className="rounded-[2rem] overflow-hidden"
      >
        <div className="py-6">
          <Form layout="vertical" onFinish={() => {
            message.success("Command Executed Successfully")
            setQuickActionModal(null)
          }}>
            <Form.Item label="Target Entity" required>
              <Select placeholder="Search job, recruiter, or candidate..." showSearch>
                 <Select.Option value="1">Sr. Software Engineer (J-921)</Select.Option>
                 <Select.Option value="2">Product Manager (J-925)</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="Action Details">
              <Input.TextArea placeholder="Enter instructions or parameters..." rows={4} className="rounded-2xl" />
            </Form.Item>
            <Button block type="primary" htmlType="submit" className="h-12 rounded-2xl font-black uppercase text-xs tracking-widest bg-slate-900 border-none">
               Execute Command
            </Button>
          </Form>
        </div>
      </Modal>

    </div>
  )
}

function HealthCard({ label, value, sub, icon, color, onClick }: any) {
  const colorMap: any = {
    indigo: 'border-indigo-100 text-indigo-900 hover:border-indigo-400 hover:shadow-indigo-100',
    blue: 'border-blue-100 text-blue-900 hover:border-blue-400 hover:shadow-blue-100',
    emerald: 'border-emerald-100 text-emerald-900 hover:border-emerald-400 hover:shadow-emerald-100',
    amber: 'border-amber-100 text-amber-900 hover:border-amber-400 hover:shadow-amber-100',
    purple: 'border-purple-100 text-purple-900 hover:border-purple-400 hover:shadow-purple-100',
    rose: 'border-rose-100 text-rose-900 hover:border-rose-400 hover:shadow-rose-100',
  }

  return (
    <Card 
      className={cn("rounded-[2rem] border shadow-soft-sm cursor-pointer transition-all", colorMap[color])} 
      bodyStyle={{ padding: '24px' }}
      onClick={onClick}
    >
       <div className="flex items-center gap-2 mb-3 opacity-60">
          <div className="p-2 rounded-xl bg-slate-50">{icon}</div>
          <Text className="text-[10px] font-black uppercase tracking-widest text-inherit">{label}</Text>
       </div>
       <div className="flex items-end gap-2">
          <Text className="text-3xl font-black text-inherit block leading-none">{value}</Text>
          <Text className="text-[10px] font-bold uppercase tracking-tighter opacity-40 mb-1 leading-none">{sub}</Text>
       </div>
    </Card>
  )
}

function SectionTitle({ label, icon, className }: any) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
       <div className="p-2 bg-slate-100 rounded-xl text-slate-600">{icon}</div>
       <span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-800">{label}</span>
    </div>
  )
}

function CommandButton({ label, icon, color, onClick }: any) {
  const colorMap: any = {
    indigo: 'bg-indigo-50 text-indigo-700 hover:bg-indigo-600',
    blue: 'bg-blue-50 text-blue-700 hover:bg-blue-600',
    rose: 'bg-rose-50 text-rose-700 hover:bg-rose-600',
    amber: 'bg-amber-50 text-amber-700 hover:bg-amber-600',
    emerald: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-600',
  }

  return (
    <Button 
      onClick={onClick}
      className={cn(
        "h-14 rounded-2xl border-none flex items-center justify-between px-6 group transition-all",
        colorMap[color]
      )}
    >
      <div className="flex items-center gap-4">
        <span className="group-hover:text-white transition-colors">{icon}</span>
        <span className="text-xs font-black uppercase tracking-widest group-hover:text-white transition-colors">{label}</span>
      </div>
      <ChevronRight size={16} className="opacity-40 group-hover:opacity-100 group-hover:text-white transition-all group-hover:translate-x-1" />
    </Button>
  )
}
