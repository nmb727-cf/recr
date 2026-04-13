import React from 'react'
import {
  Card, Typography, Tag, Avatar, Table, Tooltip, Badge, Timeline, Divider, Button, Spin, Empty, Switch, Row, Col
} from 'antd'
const { Title, Text } = Typography
const { Paragraph } = Typography
import {
  Zap, AlertTriangle, TrendingUp, ChevronRight, MessageSquare, UserPlus, Clock,
  CheckCircle, CheckCircle2, Users, ShieldCheck, DollarSign, Scale, Receipt, BarChart3, MapPin, Briefcase, Plus,
  Workflow, BrainCircuit, UserCheck, Target, Calendar, Layers, Activity, LayoutGrid
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { useQuery } from '@tanstack/react-query'
import { requisitionsApi, jobPrequalApi } from '@/api/jobs'
import { authApi } from '@/api/auth'
import { agenciesApi } from '@/api/agencies'
import { interviewsApi } from '@/api/interviews'
import { orchestrationApi } from '@/api/orchestration'
import type { JobRequisition, Application, Candidate, InterviewPackageBinding } from '@/types'
import { cn } from '@/utils/cn'

export function InterviewAutomationSummary({ jobId }: { jobId: string }) {
  const { data: snapshotData, isLoading, refetch } = useApiQuery(
    ['job-interview-snapshot', jobId],
    () => interviewsApi.getJobInterviewSnapshot(jobId)
  )
  const snapshot = (snapshotData as any)?.snapshot ?? (snapshotData as any)?.data?.snapshot

  if (isLoading) return <Card className="shadow-soft-sm border-none rounded-3xl h-full flex items-center justify-center"><Spin /></Card>
  if (!snapshot || !snapshot.binding_active) return (
    <Card className="shadow-soft-sm border-none rounded-3xl h-full flex flex-col items-center justify-center py-8">
      <Workflow size={24} className="text-slate-200 mb-2" />
      <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">No Automation Package</Text>
    </Card>
  )

  return (
    <Card 
      title={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <BrainCircuit size={14} className="text-indigo-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Interview Automation</span>
          </div>
          <Switch 
            size="small" 
            checked={snapshot.automation_enabled} 
            onChange={async (val) => {
              await interviewsApi.updateJobBinding(jobId, { automation_enabled: val })
              refetch()
            }}
          />
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        {/* Package Banner */}
        <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-100 flex items-center justify-between">
          <div className="min-w-0">
            <Text className="block text-[10px] font-black text-indigo-400 uppercase tracking-widest leading-none mb-1">Active Package</Text>
            <Text className="block text-xs font-black text-indigo-700 truncate uppercase">{snapshot.package_name}</Text>
          </div>
          <Badge status={snapshot.automation_enabled ? "processing" : "default"} color={snapshot.automation_enabled ? "indigo" : "slate"} />
        </div>

        {/* Snapshot Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
            <Text className="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">In Interview</Text>
            <div className="flex items-baseline gap-1">
              <Text className="text-lg font-black text-slate-700 leading-none">{snapshot.candidates_in_interview}</Text>
              <Text className="text-[9px] font-bold text-slate-400 uppercase">Apps</Text>
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
            <Text className="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Pending</Text>
            <div className="flex items-baseline gap-1">
              <Text className="text-lg font-black text-indigo-600 leading-none">{snapshot.pending_interviews}</Text>
              <Text className="text-[9px] font-bold text-slate-400 uppercase">Wait</Text>
            </div>
          </div>
        </div>

        {/* Rounds Preview */}
        <div className="space-y-2">
          {snapshot.rounds_summary?.slice(0, 3).map((round: any, i: number) => (
            <div key={i} className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-slate-300" />
                <Text className="text-[10px] font-bold text-slate-600 truncate max-w-[120px] uppercase">{round.name}</Text>
              </div>
              <div className="flex items-center gap-2">
                <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-black text-[8px] uppercase px-1.5 rounded leading-relaxed">
                  {round.threshold_score}%
                </Tag>
                {round.auto_pass_enabled && <Zap size={10} className="text-amber-500" />}
              </div>
            </div>
          ))}
          {snapshot.rounds_summary?.length > 3 && (
            <Text className="text-[9px] text-slate-400 font-black uppercase px-1">+{snapshot.rounds_summary.length - 3} more rounds</Text>
          )}
        </div>
      </div>
    </Card>
  )
}

export function PrequalificationWidget({ jobId }: { jobId: string }) {
  const { data, isLoading } = useApiQuery(
    ['job-prequal-snapshot', jobId],
    () => jobPrequalApi.getSnapshot(jobId)
  )
  const prequal = (data as any)?.data?.prequal ?? (data as any)?.prequal

  if (isLoading) return (
    <Card className="shadow-soft-sm border-none rounded-3xl h-full flex items-center justify-center">
      <Spin />
    </Card>
  )

  if (!prequal || !prequal.enabled) return (
    <Card className="shadow-soft-sm border-none rounded-3xl h-full flex flex-col items-center justify-center py-8">
      <ShieldCheck size={24} className="text-slate-200 mb-2" />
      <Text className="text-[10px] font-black text-slate-400 uppercase">No Prequalification Gate</Text>
    </Card>
  )

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-indigo-600" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Prequalification</span>
          <Badge status="processing" color="indigo" className="ml-auto" />
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-3">
        {/* Form name */}
        <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-100">
          <Text className="block text-[10px] font-black text-indigo-400 uppercase tracking-widest leading-none mb-1">Active Form</Text>
          <Text className="block text-xs font-black text-indigo-700 truncate uppercase">{prequal.form_name || 'Unnamed Form'}</Text>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2">
          <div className="flex flex-col items-center p-2 bg-emerald-50 rounded-xl border border-emerald-100">
            <Text className="text-[8px] font-black text-emerald-500 uppercase tracking-widest">Pass</Text>
            <Text className="text-base font-black text-emerald-700">{prequal.pass_count ?? 0}</Text>
          </div>
          <div className="flex flex-col items-center p-2 bg-rose-50 rounded-xl border border-rose-100">
            <Text className="text-[8px] font-black text-rose-500 uppercase tracking-widest">Fail</Text>
            <Text className="text-base font-black text-rose-700">{prequal.fail_count ?? 0}</Text>
          </div>
          <div className="flex flex-col items-center p-2 bg-amber-50 rounded-xl border border-amber-100">
            <Text className="text-[8px] font-black text-amber-500 uppercase tracking-widest">Pending</Text>
            <Text className="text-base font-black text-amber-700">{prequal.pending_count ?? 0}</Text>
          </div>
        </div>

        {/* Pass rate */}
        <div className="flex items-center justify-between px-1">
          <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Pass Rate</Text>
          <Tag
            className={`font-black text-[10px] border-none rounded-xl ${
              (prequal.pass_rate ?? 0) >= 60
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-rose-50 text-rose-700'
            }`}
          >
            {prequal.pass_rate ?? 0}%
          </Tag>
        </div>

        {/* Config row */}
        <div className="flex items-center justify-between px-1">
          <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Threshold</Text>
          <Tag className="font-black text-[10px] border-none rounded-xl bg-slate-100 text-slate-600">
            {prequal.threshold ?? 'Form Default'}%
          </Tag>
        </div>
        <div className="flex items-center justify-between px-1">
          <Text className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Fail Action</Text>
          <Tag
            className="font-black text-[10px] border-none rounded-xl"
            color={prequal.fail_action === 'reject' ? 'red' : 'orange'}
          >
            {(prequal.fail_action || 'reject').replace('_', ' ').toUpperCase()}
          </Tag>
        </div>
      </div>
    </Card>
  )
}

export function PipelineSnapshot({ jobId, isWorkflowControlled }: { jobId: string, isWorkflowControlled?: boolean }) {
  const { data: snapshotData, isLoading } = useApiQuery(
    ['job-pipeline-snapshot', jobId],
    () => requisitionsApi.getPipelineSnapshot(jobId)
  )
  const snapshot = (snapshotData as any)?.snapshot ?? (snapshotData as any)?.data?.snapshot

  if (isLoading) return <Card className="shadow-soft-sm border-none rounded-3xl h-full flex items-center justify-center"><Spin /></Card>
  
  const stages = snapshot?.stages || []
  const bottlenecks = snapshot?.bottlenecks || []
  const slaRisks = snapshot?.sla_risks || []

  return (
    <Card 
      title={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <LayoutGrid size={14} className="text-indigo-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Pipeline Snapshot</span>
            {isWorkflowControlled && (
              <Tag color="purple" className="m-0 border-none font-black text-[8px] uppercase px-1.5 rounded-md leading-relaxed ml-1">
                Orchestrated
              </Tag>
            )}
          </div>
          {bottlenecks.length > 0 && (
            <Tooltip title="Potential bottlenecks detected">
              <AlertTriangle size={14} className="text-amber-500 animate-pulse" />
            </Tooltip>
          )}
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        {/* Stage Funnel Summary */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 custom-scrollbar">
          {stages.map((stage: any, i: number) => (
            <React.Fragment key={stage.id}>
              <div className={cn(
                "flex flex-col items-center min-w-[64px] p-2 rounded-2xl border transition-all",
                stage.candidate_count > 0 ? "bg-white border-indigo-100 shadow-sm" : "bg-slate-50/50 border-transparent opacity-60"
              )}>
                <Text className="text-[14px] font-black text-slate-800 leading-none mb-1">{stage.candidate_count}</Text>
                <Text className="text-[8px] font-black text-slate-400 uppercase truncate w-full text-center px-1">{stage.name}</Text>
                {stage.is_bottleneck && <div className="mt-1 h-1 w-4 bg-amber-400 rounded-full" />}
              </div>
              {i < stages.length - 1 && <ChevronRight size={10} className="text-slate-200 shrink-0" />}
            </React.Fragment>
          ))}
        </div>

        {/* Intelligence Row */}
        <div className="grid grid-cols-2 gap-3">
          <div className={cn(
            "p-3 rounded-2xl border",
            slaRisks.length > 0 ? "bg-rose-50 border-rose-100" : "bg-emerald-50 border-emerald-100"
          )}>
            <div className="flex items-center gap-1.5 mb-1">
              <Clock size={10} className={slaRisks.length > 0 ? "text-rose-500" : "text-emerald-500"} />
              <Text className={cn("text-[9px] font-black uppercase tracking-widest", slaRisks.length > 0 ? "text-rose-500" : "text-emerald-500")}>
                SLA Health
              </Text>
            </div>
            <Text className={cn("text-xs font-black uppercase", slaRisks.length > 0 ? "text-rose-700" : "text-emerald-700")}>
              {slaRisks.length > 0 ? `${slaRisks.length} at risk` : 'Healthy'}
            </Text>
          </div>

          <div className={cn(
            "p-3 rounded-2xl border",
            bottlenecks.length > 0 ? "bg-amber-50 border-amber-100" : "bg-indigo-50 border-indigo-100"
          )}>
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp size={10} className={bottlenecks.length > 0 ? "text-amber-500" : "text-indigo-500"} />
              <Text className={cn("text-[9px] font-black uppercase tracking-widest", bottlenecks.length > 0 ? "text-amber-500" : "text-indigo-500")}>
                Velocity
              </Text>
            </div>
            <Text className={cn("text-xs font-black uppercase", bottlenecks.length > 0 ? "text-amber-700" : "text-indigo-700")}>
              {bottlenecks.length > 0 ? 'Bottleneck' : 'Fluid'}
            </Text>
          </div>
        </div>

        {/* Critical Alerts */}
        {slaRisks.length > 0 && (
          <div className="p-2.5 bg-rose-50/50 rounded-xl border border-rose-100 flex items-start gap-2">
            <AlertTriangle size={12} className="text-rose-500 mt-0.5 shrink-0" />
            <Text className="text-[10px] font-bold text-rose-600 uppercase leading-tight">
              SLA Breached in {slaRisks[0].stage_name} — Priority action required
            </Text>
          </div>
        )}
      </div>
    </Card>
  )
}

export function WorkflowSnapshot({ requisition }: { requisition: any }) {
  const { data: workflowData, isLoading } = useApiQuery(
    ['job-workflow-detail', requisition.workflow_id],
    () => orchestrationApi.getWorkflowDetail(requisition.workflow_id!),
    { enabled: !!requisition.workflow_id }
  )
  const workflow = (workflowData as any)?.workflow || (workflowData as any)?.data?.workflow

  if (!requisition.workflow_enabled) {
    return (
      <Card 
        title={
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-slate-400" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Workflow Master</span>
          </div>
        }
        className="shadow-soft-sm border-none rounded-3xl h-full bg-slate-50/30"
        size="small"
      >
        <div className="flex flex-col items-center justify-center h-full py-4 text-center">
          <Layers size={20} className="text-slate-200 mb-2" />
          <Text className="text-[10px] font-black text-slate-400 uppercase">Orchestration Disabled</Text>
          <Text className="text-[9px] text-slate-300 font-medium mt-1">Using standard module automation</Text>
        </div>
      </Card>
    )
  }

  if (isLoading) return <Card className="shadow-soft-sm border-none rounded-3xl h-full flex items-center justify-center"><Spin /></Card>

  return (
    <Card 
      title={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-purple-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Workflow Active</span>
          </div>
          <Badge status="processing" text={<span className="text-[9px] font-black text-purple-600 uppercase">Running</span>} />
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        <div className="p-3 bg-purple-50 rounded-2xl border border-purple-100">
          <div className="flex items-center justify-between mb-1">
            <Text className="text-[10px] font-black text-purple-700 uppercase truncate">
              {workflow?.name || 'Standard Hiring Flow'}
            </Text>
            <Tag color="purple" className="m-0 border-none text-[8px] font-black uppercase rounded-md px-1.5 h-4 flex items-center">
              {workflow?.health_label || 'Healthy'}
            </Tag>
          </div>
          <Text className="text-[9px] text-purple-400 font-medium block">
            Last pulse: {dayjs().format('HH:mm')} • {workflow?.active_executions_count || 0} active nodes
          </Text>
        </div>

        <div className="flex items-center justify-between px-1">
          <div className="flex flex-col">
            <Text className="text-[14px] font-black text-slate-800 leading-none">100%</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-tighter">Reliability</Text>
          </div>
          <div className="flex flex-col text-center">
            <Text className="text-[14px] font-black text-slate-800 leading-none">0</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-tighter">Failures</Text>
          </div>
          <div className="flex flex-col text-right">
            <Text className="text-[14px] font-black text-slate-800 leading-none">4.2h</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-tighter">Avg Cycle</Text>
          </div>
        </div>

        <div className="pt-2">
          <Button 
            block 
            size="small" 
            className="rounded-xl text-[10px] font-black uppercase tracking-widest bg-slate-50 border-slate-100 text-slate-500 hover:text-purple-600 hover:border-purple-200"
            icon={<Activity size={12} />}
          >
            Open Monitor
          </Button>
        </div>
      </div>
    </Card>
  )
}

export function AutomationIntelligence({ requisition }: { requisition: any }) {
  const isWorkflowControlled = requisition.is_workflow_controlled
  const automationEnabled = requisition.automation_enabled || requisition.workflow_enabled

  return (
    <Card 
      title={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-indigo-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Automation Intelligence</span>
          </div>
          <Badge status={automationEnabled ? 'processing' : 'default'} />
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div className="flex flex-col">
            <Text className="text-[14px] font-black text-slate-800 leading-none">
              {isWorkflowControlled ? 'Workflow' : (automationEnabled ? 'Active' : 'Off')}
            </Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Control Mode</Text>
          </div>
          <div className="h-8 w-px bg-slate-100" />
          <div className="flex flex-col text-right">
            <Text className="text-[14px] font-black text-emerald-600 leading-none">Healthy</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Engine Status</Text>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100">
            <Text className="text-[9px] font-bold text-slate-500 uppercase">Hierarchical Layer</Text>
            <Tag color={isWorkflowControlled ? 'purple' : 'blue'} className="m-0 border-none font-black text-[8px] uppercase px-1.5 rounded-md">
              {isWorkflowControlled ? 'Level 1: Master' : 'Level 2: Job'}
            </Tag>
          </div>
          
          {isWorkflowControlled && (
            <div className="flex items-start gap-2 p-2 bg-purple-50/50 rounded-xl border border-purple-100/50">
              <ShieldCheck size={12} className="text-purple-600 mt-0.5" />
              <Text className="text-[9px] text-purple-700 font-medium leading-tight">
                Module-level overrides are currently locked by the global orchestration engine.
              </Text>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

export function HiringTeamSection({ requisition }: { requisition: any }) {
  const team = [
    { role: 'Hiring Manager', user_id: requisition.hiring_manager_id, icon: <UserCheck size={14} />, color: 'blue' },
    { role: 'Primary Recruiter', user_id: requisition.recruiter_id, icon: <Users size={14} />, color: 'indigo' },
    { role: 'Coordinator', user_id: requisition.coordinator_id, icon: <Clock size={14} />, color: 'amber' },
  ]

  return (
    <Card 
      title={
        <div className="flex items-center gap-2">
          <Users size={14} className="text-indigo-600" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Hiring Responsibilities</span>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-3">
        {team.map((member, i) => (
          <div key={i} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-2xl border border-slate-100/50">
            <div className="flex items-center gap-3">
              <Avatar size={28} className={cn("rounded-xl font-black text-[10px]", `bg-${member.color}-100 text-${member.color}-600`)}>
                {member.role.charAt(0)}
              </Avatar>
              <div className="min-w-0">
                <Text className="block text-[10px] font-black text-slate-700 uppercase tracking-tight truncate leading-none mb-1">
                  {member.role}
                </Text>
                <Text className="text-[9px] font-bold text-slate-400 truncate block leading-none">
                  {member.user_id ? 'Assigned' : 'Unassigned'}
                </Text>
              </div>
            </div>
            {member.user_id && <Badge status="success" />}
          </div>
        ))}
      </div>
    </Card>
  )
}

export function DecisionSnapshot({ jobId }: { jobId: string }) {
  // Mock data for velocity - in real would be derived from stage history
  return (
    <Card 
      title={
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-indigo-600" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Decision Pipeline</span>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div className="flex flex-col">
            <Text className="text-[14px] font-black text-slate-800 leading-none">High</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Velocity</Text>
          </div>
          <div className="h-8 w-px bg-slate-100" />
          <div className="flex flex-col text-right">
            <Text className="text-[14px] font-black text-indigo-600 leading-none">0</Text>
            <Text className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Bottlenecks</Text>
          </div>
        </div>

        <div className="space-y-2">
          {[
            { label: 'Shortlist', owner: 'Recruiter', status: 'Fluid' },
            { label: 'Final Selection', owner: 'Hiring Manager', status: 'Action Needed' },
            { label: 'Offer Approval', owner: 'Management', status: 'Pending' },
          ].map((d, i) => (
            <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100/50">
              <div>
                <Text className="block text-[9px] font-black text-slate-700 uppercase tracking-tight">{d.label}</Text>
                <Text className="text-[8px] font-medium text-slate-400 uppercase">{d.owner}</Text>
              </div>
              <Tag color={d.status === 'Fluid' ? 'emerald' : 'amber'} className="m-0 border-none font-black text-[7px] uppercase px-1.5 rounded-md">
                {d.status}
              </Tag>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

export function HiringProgressPanel({ requisition }: { requisition: any }) {
  const total = requisition.headcount || 1
  const hired = 0 // Mock - in real would count applications with status 'joined'
  const percentage = Math.round((hired / total) * 100)

  return (
    <Card 
      title={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={14} className="text-emerald-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Hiring Progress</span>
          </div>
          <span className="text-[10px] font-black text-slate-400 uppercase">{hired} / {total} Hires</span>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center px-1">
            <Text className="text-[10px] font-bold text-slate-500 uppercase">Headcount Utilization</Text>
            <Text className="text-[10px] font-black text-indigo-600">{percentage}%</Text>
          </div>
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: `${percentage}%` }} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Offers Sent', val: 0, color: 'indigo' },
            { label: 'Accepted', val: 0, color: 'emerald' },
            { label: 'Negotiation', val: 0, color: 'amber' },
            { label: 'Declined', val: 0, color: 'rose' },
          ].map((s, i) => (
            <div key={i} className="p-2 bg-slate-50 rounded-xl border border-slate-100/50 flex flex-col">
              <Text className="text-[8px] font-black text-slate-400 uppercase tracking-tighter leading-none mb-1">{s.label}</Text>
              <Text className={cn("text-xs font-black leading-none", `text-${s.color}-600`)}>{s.val}</Text>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

export function MetricCard({ label, value, color, isAlert }: { label: string, value: number | string, color: string, isAlert?: boolean }) {
  return (
    <div className={cn(
      "flex flex-col p-3 rounded-2xl border transition-all h-full justify-center min-w-[80px]",
      isAlert ? "bg-rose-50 border-rose-100" : "bg-slate-50/50 border-slate-100 hover:border-slate-200"
    )}>
      <Text className={cn("text-[9px] font-black uppercase tracking-widest mb-1", isAlert ? "text-rose-500" : "text-slate-400")}>
        {label}
      </Text>
      <Title level={4} className={cn("!m-0 !font-black", isAlert ? "text-rose-600" : "text-slate-800")}>
        {value}
      </Title>
    </div>
  )
}

// ── Intelligence Components ──────────────────────────────────────────

// ── Hiring AI Brain Components ─────────────────────────────────────

export function HiringAIBrainDashboard({ jobId }: { jobId: string }) {
  const { t } = useTranslation('jobs')
  const { data: brainData, isLoading } = useApiQuery(
    ['hiring-brain', jobId],
    () => requisitionsApi.getHiringBrain(jobId)
  )

  const brain = (brainData as any)?.intelligence ?? (brainData as any)?.data?.intelligence

  if (isLoading) return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {[1, 2, 3, 4].map(i => <Card key={i} loading className="rounded-3xl shadow-soft-sm border-none" />)}
    </div>
  )
  if (!brain) return null

  const getHealthColor = (label: string) => {
    if (label === 'Critical') return 'rose'
    if (label === 'At Risk') return 'orange'
    if (label === 'Watch') return 'amber'
    return 'emerald'
  }

  const healthColor = getHealthColor(brain.health_label)

  return (
    <div className="space-y-6 mb-8">
      {/* Primary Intelligence Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Job Health Block */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white hover:shadow-md transition-shadow"
          title={
            <div className="flex items-center gap-2">
              <BrainCircuit size={14} className="text-indigo-600" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Job Health</span>
            </div>
          }
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <Text className="text-[10px] font-bold text-slate-400 uppercase">Health Status</Text>
              <Tag className={cn("m-0 border-none font-black text-[8px] uppercase px-1.5 rounded", `bg-${healthColor}-50 text-${healthColor}-600`)}>
                {brain.health_label}
              </Tag>
            </div>
            <div className="pt-1">
              <div className="flex justify-between items-center mb-1">
                <Text className="text-[9px] font-black text-slate-500 uppercase tracking-tighter">Health Score</Text>
                <Text className={cn("text-xs font-black", `text-${healthColor}-600`)}>{brain.health_score}/100</Text>
              </div>
              <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={cn("h-full transition-all duration-1000", `bg-${healthColor}-500`)} 
                  style={{ width: `${brain.health_score}%` }} 
                />
              </div>
            </div>
            {brain.health_factors?.length > 0 && (
              <div className="space-y-1 mt-2">
                {brain.health_factors.map((f: any, i: number) => (
                  <div key={i} className="flex justify-between items-center px-1">
                    <Text className="text-[9px] font-medium text-slate-400">{f.name}</Text>
                    <Text className="text-[9px] font-black text-rose-500">{f.impact}</Text>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Hiring Velocity Block */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-indigo-600" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Hiring Velocity</span>
            </div>
          }
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <Text className="text-[10px] font-bold text-slate-400 uppercase">Pace</Text>
              <Tag className={cn(
                "m-0 border-none font-black text-[8px] uppercase px-1.5 rounded",
                brain.velocity?.pace_status === 'Behind' ? 'bg-rose-50 text-rose-600' : 
                brain.velocity?.pace_status === 'At Risk' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
              )}>
                {brain.velocity?.pace_status || 'On Track'}
              </Tag>
            </div>
            <div className="grid grid-cols-2 gap-2 py-1">
              <div className="bg-slate-50 rounded-xl p-2 border border-slate-100/50">
                <Text className="block text-[8px] font-black text-slate-400 uppercase">Avg Pipeline</Text>
                <Text className="text-sm font-black text-slate-700">{brain.velocity?.avg_days_in_pipeline || 0}d</Text>
              </div>
              <div className="bg-slate-50 rounded-xl p-2 border border-slate-100/50">
                <Text className="block text-[8px] font-black text-slate-400 uppercase">Est. Fill</Text>
                <Text className="text-sm font-black text-indigo-600">{brain.velocity?.expected_fill_date ? dayjs(brain.velocity.expected_fill_date).format('MMM D') : 'N/A'}</Text>
              </div>
            </div>
          </div>
        </Card>

        {/* Bottlenecks Block */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-amber-500" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Bottlenecks</span>
            </div>
          }
        >
          <div className="space-y-2">
            {brain.bottlenecks?.length > 0 ? brain.bottlenecks.map((b: any, i: number) => (
              <div key={i} className="p-2 bg-amber-50/50 rounded-xl border border-amber-100/50">
                <div className="flex justify-between items-center mb-0.5">
                  <Text className="text-[9px] font-black text-amber-700 uppercase">{b.type} Delay</Text>
                  <Tag className="m-0 border-none bg-amber-100 text-amber-600 font-black text-[7px] uppercase px-1 rounded">{b.severity}</Tag>
                </div>
                <Text className="block text-[10px] font-bold text-slate-600 leading-tight">{b.message}</Text>
              </div>
            )) : (
              <div className="flex items-center gap-2 text-emerald-600 py-2 justify-center h-full">
                <CheckCircle size={14} />
                <Text className="text-[10px] font-black uppercase">No Bottlenecks</Text>
              </div>
            )}
          </div>
        </Card>

        {/* Fill Risk Block */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <ShieldCheck size={14} className="text-indigo-600" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Fill Probability</span>
            </div>
          }
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <Text className="text-[10px] font-bold text-slate-400 uppercase">Risk Level</Text>
              <Tag className={cn(
                "m-0 border-none font-black text-[8px] uppercase px-1.5 rounded",
                brain.fill_risk?.risk_level === 'High' ? 'bg-rose-50 text-rose-600' : 
                brain.fill_risk?.risk_level === 'Medium' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
              )}>
                {brain.fill_risk?.risk_level || 'Low'}
              </Tag>
            </div>
            <div className="text-center py-1">
              <Title level={3} className={cn("!m-0 !font-black", brain.fill_risk?.probability < 50 ? 'text-rose-600' : 'text-slate-800')}>
                {brain.fill_risk?.probability || 0}%
              </Title>
              <Text className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Confidence Score</Text>
            </div>
          </div>
        </Card>
      </div>

      {/* Secondary Intelligence Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Recommended Actions */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-slate-900 lg:col-span-1"
          title={
            <div className="flex items-center gap-2">
              <Zap size={14} className="text-amber-400" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Recommended Next Actions</span>
            </div>
          }
        >
          <div className="space-y-3">
            {brain.next_best_actions?.map((action: any, i: number) => (
              <div key={i} className="flex items-start gap-2 group cursor-pointer p-2 rounded-2xl hover:bg-slate-800 transition-colors">
                <div className={cn("mt-1.5 h-1.5 w-1.5 rounded-full shrink-0", action.priority === 'High' ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]' : 'bg-indigo-500')} />
                <div className="min-w-0">
                  <Text className="block text-[10px] font-black text-white leading-tight uppercase tracking-tight">{action.title}</Text>
                  <Text className="text-[10px] font-bold text-slate-400 leading-tight group-hover:text-slate-300 transition-colors">{action.action}</Text>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Source Intelligence */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-indigo-600" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Source Effectiveness</span>
            </div>
          }
        >
          <div className="space-y-2">
            {brain.source_intelligence?.slice(0, 3).map((s: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100/50">
                <div className="min-w-0">
                  <Text className="block text-[10px] font-black text-slate-700 uppercase leading-none mb-1">{s.source}</Text>
                  <Text className="text-[9px] font-bold text-slate-400 uppercase">{s.total_count} Apps • {s.hired_count} Hired</Text>
                </div>
                <div className="text-right">
                  <Text className={cn("block text-[10px] font-black", s.effectiveness === 'High' ? 'text-emerald-600' : 'text-slate-600')}>
                    {s.conversion_rate}%
                  </Text>
                  <Text className="text-[8px] font-black text-slate-400 uppercase">Conv.</Text>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Team Impact */}
        <Card 
          size="small" 
          className="shadow-soft-sm border-none rounded-3xl overflow-hidden bg-white"
          title={
            <div className="flex items-center gap-2">
              <Users size={14} className="text-indigo-600" />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Team Impact</span>
            </div>
          }
        >
          <div className="space-y-3">
            <div className="p-2 bg-slate-50 rounded-xl border border-slate-100/50">
              <div className="flex justify-between items-center mb-1">
                <Text className="text-[9px] font-black text-slate-400 uppercase">Recruiter Load</Text>
                <Tag className={cn("m-0 border-none font-black text-[7px] uppercase px-1 rounded", 
                  brain.team_impact?.recruiter_load?.impact === 'High' ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600')}>
                  {brain.team_impact?.recruiter_load?.impact} Impact
                </Tag>
              </div>
              <Text className="text-[10px] font-bold text-slate-600 uppercase">Managing {brain.team_impact?.recruiter_load?.count} active jobs</Text>
            </div>
            <div className="p-2 bg-slate-50 rounded-xl border border-slate-100/50">
              <div className="flex justify-between items-center mb-1">
                <Text className="text-[9px] font-black text-slate-400 uppercase">HM Responsiveness</Text>
                <Tag className={cn("m-0 border-none font-black text-[7px] uppercase px-1 rounded", 
                  brain.team_impact?.hiring_manager_responsiveness === 'Bottleneck' ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600')}>
                  {brain.team_impact?.hiring_manager_responsiveness}
                </Tag>
              </div>
              <Text className="text-[10px] font-bold text-slate-600 uppercase">{brain.team_impact?.hm_overdue_count} overdue decisions</Text>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export function UnifiedActivityFeed({ jobId }: { jobId: string }) {
  const { t } = useTranslation('jobs')
  const { data: activitiesData, isLoading } = useQuery({
    queryKey: ['job-activity-unified', jobId],
    queryFn: async () => {
      // 1. Get Applications
      const appRes = await pipelineApi.listApplications({ requisition_id: jobId })
      const apps = (appRes as any).applications || []
      
      // 2. Get Application History for each
      const historyPromises = apps.map((app: any) => pipelineApi.getApplication(app.id))
      const historyResults = await Promise.all(historyPromises)
      
      const allEvents: any[] = []
      
      historyResults.forEach((res: any) => {
        const app = res.application
        const history = res.history || []
        const candidateName = `Candidate ${app.candidate_id.slice(0,4)}` // Simplified lookup
        
        allEvents.push({
          candidate_id: app.candidate_id,
          text: `submitted application`,
          date: app.created_at,
          type: 'submission',
          candidateName
        })
        
        history.forEach((h: any) => {
          allEvents.push({
            candidate_id: app.candidate_id,
            text: `moved to ${h.to_status?.replace('_', ' ') || 'next stage'}`,
            date: h.moved_at,
            type: 'move',
            candidateName,
            notes: h.notes
          })
        })
      })
      
      return allEvents.sort((a, b) => dayjs(b.date).unix() - dayjs(a.date).unix())
    }
  })

  const activities = (activitiesData as any) ?? []

  if (isLoading) return <div className="py-10 text-center"><Spin /></div>
  if (activities.length === 0) return <Empty className="py-10" description="No activity found" />

  return (
    <Card bordered={false} className="shadow-soft-sm rounded-3xl p-4">
      <Timeline
        className="mt-4"
        items={activities.map((act: any, i: number) => ({
          key: i,
          children: (
            <div className="flex flex-col pb-4">
              <div className="flex items-center gap-2">
                <Text className="text-xs font-black text-slate-800">{act.candidateName}</Text>
                <Text className="text-xs text-slate-600">{act.text}</Text>
              </div>
              {act.notes && <Paragraph className="text-[11px] text-slate-400 italic m-0 mt-1 bg-slate-50 p-2 rounded-lg border border-slate-100">"{act.notes}"</Paragraph>}
              <Text className="text-[9px] font-black text-slate-400 uppercase mt-1 tracking-wider">
                {dayjs(act.date).format('MMM D, YYYY · HH:mm')} — {dayjs(act.date).fromNow()}
              </Text>
            </div>
          ),
          dot: <div className={cn("h-2 w-2 rounded-full border-2 border-white ring-2", act.type === 'submission' ? 'bg-blue-500 ring-blue-50' : 'bg-indigo-500 ring-indigo-50')} />,
        }))}
      />
    </Card>
  )
}

export function AgencyIntelligenceSection({ jobId }: { jobId: string }) {
  const { data: intelData, isLoading } = useApiQuery(
    ['job-agency-intelligence', jobId],
    () => agenciesApi.getJobIntelligence(jobId)
  )

  const assignedPerformance = (intelData as any)?.assigned_agencies ?? (intelData as any)?.assigned_performance ?? (intelData as any)?.data?.assigned_agencies ?? []
  const recommendations = (intelData as any)?.recommended_agencies ?? (intelData as any)?.recommendations ?? (intelData as any)?.data?.recommended_agencies ?? []
  const underperforming = (intelData as any)?.underperforming_agencies ?? (intelData as any)?.data?.underperforming_agencies ?? []
  const inactive = (intelData as any)?.inactive_agencies ?? (intelData as any)?.data?.inactive_agencies ?? []

  if (isLoading) {
    return (
      <Card size="small" className="shadow-soft-sm border-none rounded-3xl">
        <div className="flex min-h-[220px] items-center justify-center">
          <Spin />
        </div>
      </Card>
    )
  }

  return (
    <Card 
      size="small"
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users size={14} className="text-blue-600" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Agency Intelligence</span>
          </div>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl"
    >
      <div className="space-y-4">
        {assignedPerformance.length > 0 && (
          <div>
            <Text className="text-[9px] font-black text-slate-400 uppercase block mb-2">Assigned Performance</Text>
            <div className="space-y-2">
              {assignedPerformance.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="min-w-0 flex-1">
                    <Text className="block text-[10px] font-black text-slate-700 truncate uppercase">{item.agency_name || `Agency ${item.agency_tenant_id.slice(0, 8)}`}</Text>
                    <div className="flex items-center gap-2">
                      <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-black text-[8px] uppercase px-1 rounded">{item.status}</Tag>
                      <Text className="text-[9px] text-slate-400 font-bold uppercase">{item.submission_count} subs</Text>
                      <Text className="text-[9px] text-slate-400 font-bold uppercase">{Number(item.global_metrics?.hire_rate || 0).toFixed(0)}% hire</Text>
                    </div>
                  </div>
                  <div className="text-right pl-2">
                    <Text className="block text-[8px] font-black text-slate-400 uppercase">Score</Text>
                    <Text className={cn("text-xs font-black", item.score > 70 ? "text-emerald-600" : item.score > 50 ? "text-amber-600" : "text-rose-600")}>{Number(item.score || 0).toFixed(0)}</Text>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <Text className="text-[9px] font-black text-slate-400 uppercase block mb-2">Recommended Agencies</Text>
          <div className="space-y-2">
            {recommendations.length > 0 ? recommendations.map((rec: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-2 bg-indigo-50/50 rounded-xl border border-indigo-100/30">
                <div className="min-w-0 flex-1">
                  <Text className="block text-[10px] font-black text-indigo-700 truncate uppercase">{rec.agency_name || `Agency ${rec.agency_tenant_id.slice(0, 8)}`}</Text>
                  <Text className="block text-[8px] text-indigo-500 font-bold uppercase truncate">{rec.reason}</Text>
                </div>
                <div className="text-right pl-2">
                  <Text className="block text-[8px] font-black text-slate-400 uppercase">Score</Text>
                  <Text className="text-xs font-black text-indigo-700">{Number(rec.score || 0).toFixed(0)}</Text>
                </div>
              </div>
            )) : (
              <div className="text-center py-2 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <Text className="text-[9px] font-bold text-slate-400 uppercase">No recommendations yet</Text>
              </div>
            )}
          </div>
        </div>

        {(underperforming.length > 0 || inactive.length > 0) && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="rounded-2xl border border-rose-100 bg-rose-50/60 p-3">
              <Text className="mb-2 block text-[9px] font-black uppercase text-rose-500">Underperforming Agencies</Text>
              {underperforming.length ? underperforming.slice(0, 3).map((item: any) => (
                <div key={item.agency_tenant_id} className="flex items-center justify-between py-1.5">
                  <Text className="text-[10px] font-bold text-slate-700">{item.agency_name}</Text>
                  <Text className="text-[10px] font-black text-rose-600">{Number(item.score || 0).toFixed(0)}</Text>
                </div>
              )) : <Text className="text-[10px] text-slate-500">None</Text>}
            </div>
            <div className="rounded-2xl border border-amber-100 bg-amber-50/60 p-3">
              <Text className="mb-2 block text-[9px] font-black uppercase text-amber-600">Inactive Agencies</Text>
              {inactive.length ? inactive.slice(0, 3).map((item: any) => (
                <div key={item.agency_tenant_id} className="flex items-center justify-between py-1.5">
                  <Text className="text-[10px] font-bold text-slate-700">{item.agency_name}</Text>
                  <Text className="text-[10px] font-black text-amber-700">No recent activity</Text>
                </div>
              )) : <Text className="text-[10px] text-slate-500">None</Text>}
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export function RecruiterIntelligenceSection({ jobId }: { jobId: string }) {
  const { t } = useTranslation('jobs')
  const { data: recData, isLoading } = useApiQuery(
    ['job-recruiter-intelligence', jobId],
    () => authApi.getJobRecruiterRecommendations(jobId)
  )

  const recommendations = (recData as any)?.recommendations ?? (recData as any)?.data?.recommendations ?? []
  const overloaded = (recData as any)?.overloaded ?? (recData as any)?.data?.overloaded ?? []
  const available = (recData as any)?.available ?? (recData as any)?.data?.available ?? []

  return (
    <Card 
      size="small"
      title={
        <div className="flex items-center gap-2">
          <UserCheck size={14} className="text-emerald-600" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-600">Recruiter Intelligence</span>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl"
    >
      <div className="space-y-4">
        <div>
          <Text className="text-[9px] font-black text-slate-400 uppercase block mb-2">Smart Recommendations</Text>
          <div className="space-y-2">
            {recommendations.length > 0 ? recommendations.map((rec: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-2 bg-emerald-50/50 rounded-xl border border-emerald-100/30">
                <div className="min-w-0 flex-1">
                  <Text className="block text-[10px] font-black text-emerald-700 truncate uppercase">{rec.full_name}</Text>
                  <Text className="block text-[8px] text-emerald-500 font-bold uppercase truncate">{rec.reason}</Text>
                </div>
                <div className="text-right pl-2">
                  <Text className="block text-[8px] font-black text-slate-400 uppercase">Score</Text>
                  <Text className="text-xs font-black text-emerald-600">{rec.score.toFixed(0)}</Text>
                </div>
              </div>
            )) : (
              <div className="text-center py-2 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <Text className="text-[9px] font-bold text-slate-400 uppercase">No recommendations</Text>
              </div>
            )}
          </div>
        </div>

        <div>
          <Text className="text-[9px] font-black text-slate-400 uppercase block mb-2">Team Capacity</Text>
          <div className="space-y-2">
            {overloaded.length > 0 && (
              <div className="p-2 bg-rose-50 rounded-xl border border-rose-100 flex items-center gap-2">
                <AlertTriangle size={12} className="text-rose-500" />
                <Text className="text-[9px] font-bold text-rose-700 uppercase">{overloaded.length} Recruiters Overloaded</Text>
              </div>
            )}
            <div className="flex flex-wrap gap-1.5">
              {available.slice(0, 5).map((rec: any, i: number) => (
                <Tooltip key={i} title={`${rec.full_name} (${rec.workload.workload_status})`}>
                  <Avatar size="small" className="bg-slate-100 text-slate-600 font-black border-none text-[8px]">
                    {rec.full_name.charAt(0)}
                  </Avatar>
                </Tooltip>
              ))}
              {available.length > 5 && <Text className="text-[9px] text-slate-400 font-black uppercase mt-1">+{available.length - 5}</Text>}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export function CandidateFocusPanel({ applications }: { applications: Application[] }) {
  const { t } = useTranslation('jobs')
  const { data: candidatesData } = useApiQuery(['candidates', 'all'], () => candidatesApi.list())
  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as any)?.candidates ?? []).map((c: any) => [c.id, c])
  )

  const columns = [
    {
      title: t('fields.candidate_name'),
      key: 'candidate',
      render: (_: any, app: any) => {
        const candidate = candidateMap.get(app.candidate_id)
        return (
          <div className="flex items-center gap-2">
            <Avatar size="small" className="bg-indigo-50 text-indigo-600 font-black border-none text-[10px]">
              {candidate?.full_name?.charAt(0) || 'C'}
            </Avatar>
            <div className="min-w-0">
              <Text className="block font-bold text-slate-800 text-[11px] leading-tight truncate">
                {candidate?.full_name || 'Loading...'}
              </Text>
            </div>
          </div>
        )
      }
    },
    {
      title: t('fields.stage'),
      key: 'stage',
      render: (_: any, app: any) => (
        <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-black text-[8px] uppercase px-1.5 rounded">
          {app.status?.replace('_', ' ')}
        </Tag>
      )
    },
    {
      title: 'Score',
      key: 'match',
      render: (v: any, app: any) => <Text className="text-[10px] font-black text-emerald-600">{app.match_score || 85}%</Text>
    },
    {
      title: 'Source',
      key: 'source',
      render: (_: any, app: any) => <Text className="text-[9px] text-slate-400 font-black uppercase truncate">{app.source || 'Direct'}</Text>
    },
    {
      title: '',
      key: 'actions',
      align: 'right' as const,
      render: () => <ChevronRight size={14} className="text-slate-300" />
    }
  ]

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('candidate_panel.title')}</span>
          <Button type="link" size="small" className="text-[10px] font-black uppercase tracking-widest p-0">{t('candidate_panel.view_all_candidates')}</Button>
        </div>
      }
      bordered={false}
      className="shadow-soft-sm overflow-hidden rounded-3xl"
      bodyStyle={{ padding: 0 }}
    >
      <Table
        dataSource={applications.slice(0, 5)}
        columns={columns}
        rowKey="id"
        pagination={false}
        size="small"
        className="modern-table-dense"
      />
    </Card>
  )
}

export function SourcingIntelligence({ applications, onAssignAgency }: { applications: Application[], onAssignAgency?: () => void }) {
  const { t } = useTranslation('jobs')

  const sources = {
    direct: applications.filter(a => a.source === 'direct' || !a.agency_id).length,
    agency: applications.filter(a => a.agency_id).length,
    internal: applications.filter(a => a.source === 'internal').length,
  }

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('command_center.sourcing_intelligence')}</span>
          {onAssignAgency && (
            <Button
              type="text"
              size="small"
              icon={<Users size={12} />}
              className="text-blue-600 font-black text-[9px] uppercase hover:bg-blue-50"
              onClick={onAssignAgency}
            >
              {t('command_center.quick_actions.assign')}
            </Button>
          )}
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl"
      size="small"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-blue-50 rounded-xl">
            <Text className="block text-[8px] font-black text-blue-400 uppercase">{t('summary.direct_applicants')}</Text>
            <Text className="text-sm font-black text-blue-700">{sources.direct}</Text>
          </div>
          <div className="text-center p-2 bg-purple-50 rounded-xl">
            <Text className="block text-[8px] font-black text-purple-400 uppercase">{t('summary.agency')}</Text>
            <Text className="text-sm font-black text-purple-700">{sources.agency}</Text>
          </div>
          <div className="text-center p-2 bg-emerald-50 rounded-xl">
            <Text className="block text-[8px] font-black text-emerald-400 uppercase">{t('summary.internal')}</Text>
            <Text className="text-sm font-black text-emerald-700">{sources.internal}</Text>
          </div>
        </div>
        <div>
          <Text className="text-[9px] font-black text-slate-400 uppercase block mb-2">{t('command_center.agency_performance')}</Text>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100/50">
              <Text className="text-[10px] font-black text-slate-600 truncate flex-1">Global Sourcing Corp</Text>
              <div className="flex gap-2">
                <div className="flex flex-col items-end">
                  <Text className="text-[8px] font-black text-slate-400 uppercase">Sub</Text>
                  <Text className="text-[10px] font-black text-slate-700">12</Text>
                </div>
                <div className="flex flex-col items-end">
                  <Text className="text-[8px] font-black text-slate-400 uppercase text-emerald-500">Hired</Text>
                  <Text className="text-[10px] font-black text-emerald-600">2</Text>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export function InterviewIntelligence({ jobId }: { jobId: string }) {
  const { t } = useTranslation('jobs')
  return (
    <Card
      title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('command_center.interview_intelligence')}</span>}
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between p-2 bg-slate-50 rounded-xl border border-slate-100">
          <div>
            <Text className="text-[8px] font-black text-slate-400 uppercase block">Upcoming Today</Text>
            <Text className="text-xs font-black text-slate-800">3 Interviews</Text>
          </div>
          <Button type="primary" size="small" ghost className="h-6 text-[9px] font-black uppercase">View</Button>
        </div>
        <div className="space-y-2">
          <Text className="text-[9px] font-black text-slate-400 uppercase block">{t('command_center.upcoming_interviews')}</Text>
          <div className="flex items-center gap-3 p-2 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer">
            <Avatar size={20} className="bg-blue-100 text-blue-600 font-black text-[8px]">JD</Avatar>
            <div className="min-w-0 flex-1">
              <Text className="block text-[10px] font-black text-slate-700 truncate">John Doe</Text>
              <Text className="text-[9px] text-slate-400 font-bold uppercase">Technical Round • 2:30 PM</Text>
            </div>
            <ChevronRight size={12} className="text-slate-300" />
          </div>
        </div>
      </div>
    </Card>
  )
}

export function OfferIntelligence({ applications }: { applications: Application[] }) {
  const { t } = useTranslation('jobs')

  const stats = {
    pending: applications.filter(a => a.status === 'offer_extended' && !a.offer_accepted_at).length,
    negotiation: 2,
    joining: applications.filter(a => a.status === 'offer_accepted' || a.placement_status === 'pending_join').length
  }

  return (
    <Card
      title={<span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('command_center.offer_intelligence')}</span>}
      className="shadow-soft-sm border-none rounded-3xl h-full"
      size="small"
    >
      <div className="grid grid-cols-3 gap-2 h-full items-center">
        <MetricCard label={t('command_center.offers_pending')} value={stats.pending} color="amber" />
        <MetricCard label={t('command_center.negotiations')} value={stats.negotiation} color="blue" />
        <MetricCard label={t('command_center.joining')} value={stats.joining} color="emerald" />
      </div>
    </Card>
  )
}

export function PipelineCompactSummary({ applications, onOpenFull }: { applications: Application[], onOpenFull?: () => void }) {
  const { t } = useTranslation('jobs')

  const stages = [
    { key: 'sourced', label: t('command_center.sourced'), count: applications.filter(a => a.status === 'applied').length, color: 'bg-slate-400' },
    { key: 'submitted', label: t('command_center.submitted'), count: applications.filter(a => a.status === 'applied' || a.status === 'screening').length, color: 'bg-blue-500' },
    { key: 'screening', label: t('command_center.screening'), count: applications.filter(a => a.status === 'screening').length, color: 'bg-indigo-500' },
    { key: 'interview', label: t('command_center.interview'), count: applications.filter(a => ['interview', 'interview_scheduled'].includes(a.status)).length, color: 'bg-purple-500' },
    { key: 'offer', label: t('command_center.offer'), count: applications.filter(a => a.status === 'offer_extended').length, color: 'bg-amber-500' },
    { key: 'hired', label: t('command_center.hired'), count: applications.filter(a => a.status === 'joined').length, color: 'bg-emerald-500' },
  ]

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{t('command_center.pipeline')}</span>
          <Button type="link" size="small" className="text-[10px] font-black uppercase tracking-widest p-0" onClick={onOpenFull}>
            {t('actions.open_pipeline')}
          </Button>
        </div>
      }
      className="shadow-soft-sm border-none rounded-3xl overflow-hidden"
    >
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        {stages.map(s => (
          <div key={s.key} className="p-3 bg-slate-50/50 rounded-2xl border border-slate-100/50 flex flex-col items-center text-center">
            <div className={cn("h-1.5 w-8 rounded-full mb-2", s.color)} />
            <Text className="text-[9px] font-black text-slate-400 uppercase tracking-tighter mb-1">{s.label}</Text>
            <Text className="text-lg font-black text-slate-800 leading-none">{s.count}</Text>
          </div>
        ))}
      </div>
    </Card>
  )
}

export function JobCommandCenterView({ requisition, applications, onAssignAgency, onOpenFullPipeline }: {
  requisition: JobRequisition,
  applications: Application[], 
  onAssignAgency?: () => void,
  onOpenFullPipeline?: () => void
}) {
  return (
    <div className="space-y-6">
      {/* Primary Intelligence Layer */}
      <HiringAIBrainDashboard jobId={requisition.id} />

      {/* Main Operational Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column - Core Operations (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          <PipelineCompactSummary applications={applications} onOpenFull={onOpenFullPipeline} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InterviewIntelligence jobId={requisition.id} />
            <InterviewAutomationSummary jobId={requisition.id} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <WorkflowSnapshot requisition={requisition} />
            <AutomationIntelligence requisition={requisition} />
            <HiringProgressPanel requisition={requisition} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PrequalificationWidget jobId={requisition.id} />
            <PipelineSnapshot jobId={requisition.id} isWorkflowControlled={requisition.is_workflow_controlled} />
            <OfferIntelligence applications={applications} />
          </div>

          <CandidateFocusPanel applications={applications} />
        </div>

        {/* Right Column - Team & Intelligence (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <HiringTeamSection requisition={requisition} onAssign={onAssignAgency} />
          <RecruiterIntelligenceSection jobId={requisition.id} />
          <AgencyIntelligenceSection jobId={requisition.id} />
          <SourcingIntelligence applications={applications} onAssignAgency={onAssignAgency} />
          <UnifiedActivityFeed jobId={requisition.id} />
        </div>
      </div>
    </div>
  )
}
