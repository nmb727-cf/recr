import React, { useState } from 'react'
import {
  Typography, Button, Card, Row, Col, Avatar, Space, Tag,
  Badge, Spin, Progress, Tooltip, Empty, List, Divider, message
} from 'antd'
import {
  Zap, Clock, CheckCircle2, AlertTriangle, Sparkles, Plus,
  Calendar, MessageSquare, UserPlus, Target, Briefcase,
  TrendingUp, ArrowUpRight, Search, Activity, Layers, Bell,
  ShieldCheck, History, MoreHorizontal, Bot
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { workspaceApi } from '@/api/workspace'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/utils/cn'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
const { Title, Text, Paragraph } = Typography

export default function RecruiterWorkspace() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const queryClient = useQueryClient()

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: summaryData, isLoading: loadingSummary } = useApiQuery(['workspace-summary'], workspaceApi.getSummary)
  const { data: tasksData, isLoading: loadingTasks } = useApiQuery(['workspace-tasks'], workspaceApi.getTasks)
  const { data: activityData, isLoading: loadingActivity } = useApiQuery(['workspace-activity'], workspaceApi.getActivity)
  const { data: alertsData, isLoading: loadingAlerts } = useApiQuery(['workspace-alerts'], workspaceApi.getAlerts)
  const { data: aiData, isLoading: loadingAI } = useApiQuery(['workspace-ai'], workspaceApi.getAI)

  // ── Mutations ─────────────────────────────────────────────────────────────
  const taskActionMutation = useMutation({
    mutationFn: ({ taskId, action, days }: { taskId: string, action: 'complete' | 'snooze', days?: number }) => 
      workspaceApi.performTaskAction(taskId, action, days),
    onSuccess: () => {
      message.success('Task updated')
      queryClient.invalidateQueries({ queryKey: ['workspace-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['workspace-summary'] })
    }
  })

  const summary = summaryData?.data || {}
  const tasks = tasksData?.data?.tasks || []
  const activities = activityData?.data?.activities || []
  const alerts = alertsData?.data?.alerts || []
  const suggestions = aiData?.data?.suggestions || []

  const handleAction = (taskId: string, action: 'complete' | 'snooze', days?: number) => {
    taskActionMutation.mutate({ taskId, action, days })
  }

  return (
    <div className="max-w-[1600px] mx-auto p-8 space-y-8 animate-in fade-in duration-700">
      
      {/* ── Header & Productivity ────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Avatar size={64} className="bg-indigo-600 border-4 border-indigo-100 shadow-xl font-black text-xl">
            {user?.first_name?.charAt(0)}
          </Avatar>
          <div>
            <h1 className="text-2xl font-black tracking-tighter text-slate-900 leading-none mb-1 uppercase">
              Recruiter Command Center
            </h1>
            <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Agent {user?.first_name} {user?.last_name} • Operational
            </Text>
          </div>
        </div>

        <div className="flex items-center gap-6 bg-white p-4 rounded-[2rem] border border-slate-100 shadow-soft-sm">
           <div className="flex flex-col items-center px-6 border-r border-slate-100">
              <Text className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">Productivity Score</Text>
              <div className="flex items-center gap-3">
                 <Progress type="circle" percent={summary.productivity_score || 85} size={40} strokeColor="#4f46e5" strokeWidth={12} />
                 <Text className="text-xl font-black text-slate-800 tracking-tighter">{summary.productivity_score || 85}%</Text>
              </div>
           </div>
           <div className="flex items-center gap-3">
              <Button onClick={() => navigate('/jobs')} type="primary" className="h-12 bg-slate-900 border-none rounded-2xl font-black text-[10px] uppercase tracking-widest px-8 shadow-xl shadow-slate-200">
                Create Job
              </Button>
              <Button onClick={() => navigate('/candidates')} className="h-12 rounded-2xl border-slate-200 font-black text-[10px] uppercase tracking-widest px-8 shadow-soft-sm">
                Add Candidate
              </Button>
           </div>
        </div>
      </div>

      {/* ── KPI Row: Today's Focus ───────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-6">
        <KPICard label="Interviews Today" value={summary.interviews_today} icon={<Calendar className="text-indigo-600" />} color="indigo" />
        <KPICard label="Pending Actions" value={summary.tasks_pending} icon={<Clock className="text-amber-600" />} color="amber" />
        <KPICard label="Active Pipeline" value={summary.active_candidates} icon={<TrendingUp className="text-emerald-600" />} color="emerald" />
        <KPICard label="Jobs Assigned" value={summary.jobs_assigned} icon={<Briefcase className="text-blue-600" />} color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* ── Left Column: Functional Tasks ──────────────────────────────── */}
        <div className="lg:col-span-4 space-y-6">
          <Card 
            className="rounded-[2.5rem] border-none shadow-soft-sm overflow-hidden"
            title={<SectionHeader icon={<Zap size={16} />} title="My Tasks" count={tasks.length} />}
          >
            {loadingTasks ? <Spin className="p-8 w-full" /> : tasks.length === 0 ? <Empty description="Zero tasks — you're fast!" /> : (
              <List
                dataSource={tasks}
                renderItem={(item: any) => (
                  <div className="group p-4 mb-3 rounded-2xl bg-slate-50/50 border border-slate-100 hover:bg-white hover:shadow-md transition-all cursor-pointer">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <Text strong className="text-[12px] uppercase block leading-tight mb-1">{item.title}</Text>
                        <Paragraph className="text-[11px] text-slate-500 m-0 line-clamp-2">{item.description}</Paragraph>
                      </div>
                      <Tag color={item.priority === 'urgent' ? 'red' : item.priority === 'high' ? 'orange' : 'blue'} className="m-0 text-[8px] font-black uppercase">
                        {item.priority}
                      </Tag>
                    </div>
                    <div className="mt-3 flex items-center justify-between border-t border-slate-100/50 pt-3">
                      <Text className="text-[9px] font-bold text-slate-400 uppercase flex items-center gap-1">
                        <Clock size={10} /> {dayjs(item.due_at).fromNow()}
                      </Text>
                      <Space size={4}>
                        <Button 
                          size="small" 
                          type="text" 
                          className="text-[9px] font-black uppercase text-emerald-600"
                          onClick={() => handleAction(item.id, 'complete')}
                        >
                          Done
                        </Button>
                        <Button 
                          size="small" 
                          type="text" 
                          className="text-[9px] font-black uppercase text-indigo-600"
                          onClick={() => item.candidate_id ? navigate(`/candidates/${item.candidate_id}`) : message.info('Opening details...')}
                        >
                          Open
                        </Button>
                        <Button 
                          size="small" 
                          type="text" 
                          className="text-[9px] font-black uppercase text-slate-400"
                          onClick={() => handleAction(item.id, 'snooze', 1)}
                        >
                          Snooze
                        </Button>
                      </Space>
                    </div>
                  </div>
                )}
              />
            )}
          </Card>

          {/* SLA & Alerts */}
          <Card 
            className="rounded-[2.5rem] border-none shadow-soft-sm overflow-hidden bg-rose-50/30"
            title={<SectionHeader icon={<AlertTriangle size={16} />} title="SLA & Risks" color="text-rose-600" />}
          >
            {alerts.length === 0 ? <Empty description="No risks detected" /> : alerts.map((alert: any, idx: number) => (
              <div key={idx} className="p-4 rounded-2xl bg-white border border-rose-100 shadow-sm mb-3">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-1.5 rounded-lg bg-rose-100 text-rose-600"><AlertTriangle size={14} /></div>
                  <Text strong className="text-[11px] uppercase text-rose-900">{alert.title}</Text>
                </div>
                <Text className="text-[10px] text-rose-600 font-medium block">{alert.description}</Text>
              </div>
            ))}
          </Card>
        </div>

        {/* ── Center Column: Activity & Intelligence ─────────────────────── */}
        <div className="lg:col-span-5 space-y-6">
          {/* AI Suggestions */}
          <div className="p-6 rounded-[2.5rem] bg-indigo-600 text-white shadow-2xl relative overflow-hidden">
            <Sparkles size={120} className="absolute -right-8 -top-8 text-white/10 rotate-12" />
            <div className="relative z-10 space-y-6">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-white/20 rounded-xl"><Bot size={18} /></div>
                <Text className="text-[10px] font-black uppercase tracking-[0.2em] text-white/80">AI Recruitment Brain</Text>
              </div>
              <div className="space-y-4">
                {suggestions.map((s: any) => (
                  <div key={s.id} className="flex items-start gap-3 p-3 rounded-2xl bg-white/10 hover:bg-white/20 transition-all cursor-pointer group">
                    <div className="mt-1"><ArrowUpRight size={14} className="text-white/60 group-hover:text-white" /></div>
                    <Text className="text-xs font-medium leading-relaxed">{s.text}</Text>
                  </div>
                ))}
              </div>
              <Button block className="h-11 rounded-xl bg-white text-indigo-600 border-none font-black uppercase text-[10px] tracking-widest shadow-xl">
                Execute AI Recommendations
              </Button>
            </div>
          </div>

          {/* Activity Feed */}
          <Card 
            className="rounded-[2.5rem] border-none shadow-soft-sm overflow-hidden"
            title={<SectionHeader icon={<Activity size={16} />} title="Recent Activity" />}
          >
            <div className="space-y-6">
              {activities.map((act: any) => (
                <div key={act.id} className="flex gap-4 group">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:text-indigo-500 group-hover:bg-indigo-50 transition-all">
                      <Layers size={14} />
                    </div>
                    <div className="w-px flex-1 bg-slate-100 my-2" />
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="flex items-center justify-between mb-1">
                      <Text strong className="text-[11px] uppercase tracking-tight">{act.event}</Text>
                      <Text className="text-[9px] font-bold text-slate-400 uppercase">{act.time}</Text>
                    </div>
                    <Text className="text-xs text-slate-600 block leading-relaxed">{act.summary}</Text>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* ── Right Column: Metrics & Actions ────────────────────────────── */}
        <div className="lg:col-span-3 space-y-6">
          <Card 
            className="rounded-[2.5rem] border-none shadow-soft-sm overflow-hidden bg-slate-900 text-white"
            title={<SectionHeader icon={<Target size={16} />} title="My Performance" color="text-white" />}
          >
            <div className="space-y-6 p-2">
              <MetricItem label="Pipeline Velocity" value="2.4 days" trend="+12%" icon={<TrendingUp size={14}/>} />
              <MetricItem label="Interview Conversion" value="68%" trend="+5%" icon={<ShieldCheck size={14}/>} />
              <MetricItem label="SLA Compliance" value="94%" trend="Stable" icon={<Activity size={14}/>} />
              <Divider className="border-white/10 my-0" />
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                <Text className="text-[9px] font-black uppercase text-white/40 block mb-3">Top Jobs Assigned</Text>
                <div className="space-y-3">
                  <JobMini label="Senior Backend Engineer" count={14} />
                  <JobMini label="VP of Product" count={8} />
                  <JobMini label="Lead Instructor" count={22} />
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Search Widget */}
          <div className="p-6 rounded-[2.5rem] bg-white border border-slate-100 shadow-soft-sm space-y-4">
            <Text className="text-[10px] font-black uppercase text-slate-400 tracking-widest block">Omni Search</Text>
            <div className="relative group">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                placeholder="Find candidates, jobs..." 
                className="w-full h-11 rounded-xl bg-slate-50 border-none pl-10 pr-4 text-xs font-bold focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all"
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

function KPICard({ label, value, icon, color }: any) {
  const colors: any = {
    indigo: 'bg-indigo-50 text-indigo-600',
    amber: 'bg-amber-50 text-amber-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    blue: 'bg-blue-50 text-blue-600'
  }
  return (
    <div className="p-6 rounded-[2.5rem] bg-white border border-slate-100 shadow-soft-sm hover:shadow-md transition-all group cursor-pointer">
      <div className={cn("p-3 w-fit rounded-2xl mb-4 group-hover:scale-110 transition-transform", colors[color])}>
        {React.cloneElement(icon as React.ReactElement, { size: 24 })}
      </div>
      <Text className="text-[10px] font-black text-slate-400 uppercase block mb-1 tracking-widest">{label}</Text>
      <div className="flex items-end justify-between">
        <Text className="text-3xl font-black text-slate-800 tracking-tighter leading-none">{value || 0}</Text>
        <ArrowUpRight size={16} className="text-slate-200 group-hover:text-indigo-500" />
      </div>
    </div>
  )
}

function SectionHeader({ icon, title, count, color = 'text-slate-600' }: any) {
  return (
    <div className="flex items-center justify-between w-full py-2">
      <div className="flex items-center gap-2">
        <span className={color}>{icon}</span>
        <span className={cn("text-[11px] font-black uppercase tracking-widest", color)}>{title}</span>
      </div>
      {count !== undefined && (
        <Badge count={count} style={{ backgroundColor: '#f1f5f9', color: '#64748b', fontWeight: 900, boxShadow: 'none', fontSize: 10 }} />
      )}
    </div>
  )
}

function MetricItem({ label, value, trend, icon }: any) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-white/10 text-white/40">{icon}</div>
        <div>
          <Text className="text-[10px] font-bold text-white/60 uppercase block">{label}</Text>
          <Text className="text-sm font-black text-white">{value}</Text>
        </div>
      </div>
      <Tag color="success" className="m-0 border-none text-[9px] font-black uppercase bg-emerald-500/20 text-emerald-400">{trend}</Tag>
    </div>
  )
}

function JobMini({ label, count }: any) {
  return (
    <div className="flex items-center justify-between group cursor-pointer">
      <Text className="text-[11px] font-medium text-white/80 group-hover:text-white transition-colors truncate max-w-[120px]">{label}</Text>
      <div className="flex items-center gap-2">
        <div className="h-1 w-12 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-indigo-500" style={{ width: '60%' }} />
        </div>
        <Text className="text-[10px] font-black text-white/40">{count}</Text>
      </div>
    </div>
  )
}
