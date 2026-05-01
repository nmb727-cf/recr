import React, { useState } from 'react'
import {
  Card, Typography, Tag, Avatar, Table, Tooltip, Badge, Divider, Button, Switch, 
  Empty, Progress, List, Space, Alert, Steps, Radio, InputNumber, Select, Spin
} from 'antd'
import {
  Zap, UserPlus, Users, Briefcase, Clock, AlertTriangle, TrendingUp,
  ShieldCheck, BrainCircuit, Workflow, Settings, CheckCircle2,
  Calendar, MessageSquare, Target, ChevronRight, Play, Pause, Bell,
  UserCheck, Building2, BarChart3, Filter, Sliders, Box, Layers, Eye,
  FileText, Activity
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { useApiQuery } from '@/hooks/useApiQuery'
import { interviewsApi } from '@/api/interviews'
import type { JobRequisition, Application, InterviewPackageBinding } from '@/types'

const { Text, Title, Paragraph } = Typography

// ─── Sub-components ───────────────────────────────────────────────────────────

function AutomationHeader({ job }: { job: JobRequisition }) {
  return (
    <div className="mb-8 flex items-center justify-between">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-soft-sm">
            <BrainCircuit size={18} />
          </div>
          <Title level={4} className="!m-0 uppercase tracking-widest font-black text-slate-800 tracking-tight">Job Automation Engine</Title>
        </div>
        <Text type="secondary" className="text-[10px] font-black uppercase tracking-widest ml-10 text-slate-400">Control recruitment intelligence and automated orchestration for {job.title}</Text>
      </div>
      <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-100 shadow-soft-sm">
         <div className="flex flex-col items-end px-3 border-r border-slate-100">
            <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Global Status</Text>
            <Text className="text-[11px] font-black text-emerald-600 uppercase">Engine Active</Text>
         </div>
         <Button type="primary" size="small" className="h-9 bg-indigo-600 border-none rounded-xl font-black text-[10px] uppercase tracking-widest px-4">
            Reset Defaults
         </Button>
      </div>
    </div>
  )
}

function SectionCard({ title, icon, color, description, children, activeCount, totalCount, isLoading = false }: any) {
  const [enabled, setEnabled] = useState(true)

  return (
    <Card 
      className={cn(
        "rounded-3xl border-slate-100 shadow-soft-sm overflow-hidden transition-all h-full flex flex-col",
        !enabled && "opacity-60 grayscale-[0.5]"
      )}
      styles={{ body: { padding: 0, flex: 1, display: 'flex', flexDirection: 'column' } }}
    >
      <div className="p-6 border-b border-slate-50 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className={cn("flex h-12 w-12 items-center justify-center rounded-2xl shadow-soft-sm", `bg-${color}-50 text-${color}-600`)}>
            {React.cloneElement(icon, { size: 24 })}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
               <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest">{title}</h3>
               <Badge count={activeCount} overflowCount={99} className="automation-badge" style={{ backgroundColor: enabled ? '#4f46e5' : '#94a3b8' }} />
            </div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider leading-none">{description}</p>
          </div>
        </div>
        <Switch checked={enabled} onChange={setEnabled} size="small" className={cn(enabled ? 'bg-indigo-600' : 'bg-slate-300')} />
      </div>
      <div className="p-6 flex-1 overflow-y-auto custom-scrollbar">
        {isLoading ? <div className="py-10 text-center"><Spin /></div> : children}
      </div>
      {enabled && !isLoading && (
        <div className="px-6 py-3 bg-slate-50/50 border-t border-slate-50 flex items-center justify-between shrink-0">
           <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{activeCount} of {totalCount} Rules Active</Text>
           <Button type="link" size="small" className="text-[10px] font-black uppercase tracking-widest text-indigo-600 p-0 h-auto">View Logic Map</Button>
        </div>
      )}
    </Card>
  )
}

function RuleRow({ icon: Icon, label, status, value, description, type = 'toggle' }: any) {
  return (
    <div className="flex items-start justify-between gap-4 p-4 rounded-2xl border border-slate-100 bg-white hover:border-indigo-100 transition-colors group mb-3 last:mb-0">
      <div className="flex items-start gap-3 min-w-0">
        <div className="mt-0.5 p-2 rounded-xl bg-slate-50 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors shrink-0">
          <Icon size={16} />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Text className="text-[11px] font-black text-slate-700 uppercase tracking-tight truncate">{label}</Text>
            {status === 'active' && <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />}
          </div>
          <Text className="text-[10px] font-bold text-slate-400 uppercase leading-none block truncate">{description}</Text>
        </div>
      </div>
      <div className="flex items-center shrink-0">
        {type === 'toggle' ? (
          <Switch size="small" defaultChecked={status === 'active'} />
        ) : type === 'select' ? (
          <div className="text-[10px] font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg border border-indigo-100/50 uppercase">{value}</div>
        ) : (
          <div className="text-[10px] font-black text-slate-600 uppercase">{value}</div>
        )}
      </div>
    </div>
  )
}

function InterviewRoundRow({ round, index }: any) {
  return (
    <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100 mb-2 last:mb-0">
      <div className="flex items-center gap-3">
        <div className="h-6 w-6 rounded-full bg-white flex items-center justify-center text-[10px] font-black text-slate-400 border border-slate-100 shadow-sm">
          {index + 1}
        </div>
        <div>
          <Text className="block text-[11px] font-black text-slate-700 uppercase tracking-tight leading-none mb-1">{round.name}</Text>
          <div className="flex items-center gap-2">
            <Tag className="m-0 border-none bg-indigo-100 text-indigo-600 font-bold text-[8px] uppercase px-1.5 rounded-md leading-relaxed">
              {round.type.replace('_', ' ')}
            </Tag>
            {round.auto_pass_enabled && <Tag className="m-0 border-none bg-emerald-100 text-emerald-600 font-bold text-[8px] uppercase px-1.5 rounded-md leading-relaxed">Auto-Pass</Tag>}
          </div>
        </div>
      </div>
      <div className="text-right">
        <Text className="block text-[10px] font-black text-slate-500 uppercase">Threshold</Text>
        <Text className="text-[11px] font-black text-indigo-600">{round.threshold_score}%</Text>
      </div>
    </div>
  )
}

// ─── Main View Component ─────────────────────────────────────────────────────

export default function JobAutomationView({ job, applications = [] }: { job: JobRequisition, applications?: Application[] }) {
  const { data: bindingData, isLoading: bindingLoading } = useApiQuery(
    ['job-interview-binding', job.id],
    () => interviewsApi.getJobBinding(job.id)
  )
  const binding = (bindingData as any)?.data?.binding as InterviewPackageBinding | null

  const stats = {
    totalRules: 12 + (binding ? binding.rounds_summary.length : 0),
    activeRules: 8 + (binding?.automation_enabled ? binding.rounds_summary.length : 0),
    eventsTriggered: 145,
    savingsHours: 24,
  }

  return (
    <div className="max-w-[1400px] mx-auto p-4 animate-in fade-in duration-500">
      <AutomationHeader job={job} />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: 'Active Rules', value: stats.activeRules, icon: <Zap size={20} />, color: 'indigo' },
          { label: 'Total Triggers', value: stats.eventsTriggered, icon: <TrendingUp size={20} />, color: 'emerald' },
          { label: 'Time Optimized', value: `${stats.savingsHours}h`, icon: <Clock size={20} />, color: 'blue' },
          { label: 'Decision Logic', value: 'Smart', icon: <BrainCircuit size={20} />, color: 'amber' },
        ].map((stat, i) => (
          <Card key={i} className="rounded-3xl border-slate-100 shadow-soft-sm bg-white" styles={{ body: { padding: '20px' } }}>
            <div className="flex items-center justify-between">
              <div className={cn("p-2.5 rounded-2xl shadow-soft-sm", `bg-${stat.color}-50 text-${stat.color}-600`)}>
                {stat.icon}
              </div>
              <div className="text-right">
                <Text className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] block mb-1">{stat.label}</Text>
                <Text className="text-2xl font-black text-slate-800 leading-none">{stat.value}</Text>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* SECTION 1: Assignment Automation */}
        <SectionCard 
          title="Assignment Automation" 
          icon={<UserPlus />} 
          color="blue" 
          description="Users & Agencies assignment"
          activeCount={3}
          totalCount={4}
        >
          <div className="space-y-0">
            <RuleRow 
              icon={UserCheck} 
              label="Auto Assign Recruiter" 
              description="Based on dept & location"
              status="active"
              value="Smart Routing"
              type="select"
            />
            <RuleRow 
              icon={Building2} 
              label="Agency Distribution" 
              description="Preferred agency lists"
              status="active"
              value="Tier 1"
              type="select"
            />
            <RuleRow 
              icon={Sliders} 
              label="Sourcing Quotas" 
              description="Auto-pause on pipeline limits"
              status="inactive"
              value="50 / round"
            />
          </div>
        </SectionCard>

        {/* SECTION 2: Interview Automation */}
        <SectionCard 
          title="Interview Engine" 
          icon={<Workflow />} 
          color="indigo" 
          description="Interview rounds & thresholds"
          activeCount={binding?.automation_enabled ? binding.rounds_summary.length : 0}
          totalCount={binding ? binding.rounds_summary.length : 0}
          isLoading={bindingLoading}
        >
          {!binding ? (
            <Empty 
              image={Empty.PRESENTED_IMAGE_SIMPLE} 
              description={<Text className="text-[10px] font-bold text-slate-400 uppercase">No Interview Package Attached</Text>}
            />
          ) : (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-indigo-600 text-white shadow-soft-sm mb-4">
                <div className="flex items-center gap-2 mb-1">
                  <ShieldCheck size={14} />
                  <Text className="text-[10px] font-black uppercase tracking-widest text-indigo-100">Attached Package</Text>
                </div>
                <Text className="block text-sm font-black uppercase leading-tight truncate">{binding.package_title}</Text>
              </div>
              
              <div className="space-y-2">
                <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Rounds Automation</Text>
                {binding.rounds_summary.map((round, idx) => (
                  <InterviewRoundRow key={idx} round={round} index={idx} />
                ))}
              </div>
            </div>
          )}
        </SectionCard>

        {/* SECTION 3: Decision Automation */}
        <SectionCard 
          title="Decision Rules" 
          icon={<Zap />} 
          color="amber" 
          description="AI movement & screening logic"
          activeCount={2}
          totalCount={4}
        >
          <div className="space-y-0">
            <RuleRow 
              icon={Filter} 
              label="Auto-Reject" 
              description="Reject below 60% match"
              status="active"
              value="< 60%"
              type="select"
            />
            <RuleRow 
              icon={Layers} 
              label="Auto-Shortlist" 
              description="Direct pass if score > 90%"
              status="active"
              value="> 90%"
              type="select"
            />
             <RuleRow 
              icon={MessageSquare} 
              label="Nurture Loop" 
              description="Engage high-quality past leads"
              status="inactive"
            />
          </div>
        </SectionCard>

        {/* SECTION 4: SLA & Escalation */}
        <SectionCard 
          title="SLA & Escalation" 
          icon={<Clock />} 
          color="rose" 
          description="Response times & bottlenecks"
          activeCount={1}
          totalCount={3}
        >
          <div className="space-y-0">
            <RuleRow 
              icon={Bell} 
              label="Review Deadline" 
              description="Escalate after 48 hours"
              status="active"
              value="48h"
              type="select"
            />
            <RuleRow 
              icon={Calendar} 
              label="Scheduling SLA" 
              description="Recruiter reminder if unset"
              status="inactive"
              value="24h"
            />
            <RuleRow 
              icon={AlertTriangle} 
              label="Bottleneck Alert" 
              description="Notify HM if wait > 7 days"
              status="inactive"
              value="7d"
            />
          </div>
        </SectionCard>

        {/* SECTION 5: Pipeline Visibility */}
        <SectionCard 
          title="Pipeline Hooks" 
          icon={<Activity />} 
          color="emerald" 
          description="Automatic stage transitions"
          activeCount={2}
          totalCount={3}
        >
          <div className="space-y-0">
            <RuleRow 
              icon={ChevronRight} 
              label="Auto-Advance" 
              description="Move to next stage on pass"
              status="active"
            />
            <RuleRow 
              icon={Target} 
              label="Hiring Signal" 
              description="Notify team on final round pass"
              status="active"
            />
          </div>
        </SectionCard>

      </div>

      {/* Logic Summary Footer */}
      <Card className="mt-8 rounded-3xl border-slate-100 shadow-soft-sm bg-slate-900 overflow-hidden shrink-0">
         <div className="px-8 py-10 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-6">
               <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Play size={32} />
               </div>
               <div>
                  <h3 className="text-lg font-black text-white uppercase tracking-tight mb-1">Automation Engine Execution</h3>
                  <Text className="text-slate-400 text-sm font-medium">Rules are evaluated on every candidate movement, submission, and update.</Text>
               </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
               <Button className="h-11 rounded-xl bg-slate-800 border-slate-700 text-white font-black text-[10px] uppercase tracking-widest px-6 hover:bg-slate-700 transition-colors">
                  View Logs
               </Button>
               <Button type="primary" className="h-11 rounded-xl bg-indigo-600 border-none text-white font-black text-[10px] uppercase tracking-widest px-8 shadow-soft-lg">
                  Test Scenarios
               </Button>
            </div>
         </div>
      </Card>
    </div>
  )
}
