import { useState, useEffect } from 'react'
import {
  Button, Typography,
  Spin, Empty, message, Tag
} from 'antd'
import {
  Briefcase, Users, ArrowRight,
  Edit, Calendar,
  TrendingUp, AlertCircle
} from 'lucide-react'
import dayjs from 'dayjs'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import type { JobRequisition, RequisitionStatus, Application, PipelineData } from '@/types'
import { cn } from '@/utils/cn'

const { Title } = Typography

interface JobQuickViewProps {
  jobId: string
  onClose: () => void
  onOpenFullView: (tab?: string) => void
  onRefresh?: () => void
}

const STATUS_BANNER: Record<RequisitionStatus, { label: string, color: string }> = {
  draft: { label: 'Draft — Not visible to candidates', color: 'border-slate-400 bg-slate-50 text-slate-600' },
  pending_approval: { label: '⏳ Waiting for approval', color: 'border-amber-400 bg-amber-50 text-amber-700' },
  approved: { label: '✓ Approved — Ready to publish', color: 'border-blue-400 bg-blue-50 text-blue-700' },
  active: { label: '🟢 Live — Accepting applications', color: 'border-emerald-400 bg-emerald-50 text-emerald-700' },
  closed: { label: 'Closed', color: 'border-rose-400 bg-rose-50 text-rose-700' },
  cancelled: { label: 'Cancelled', color: 'border-slate-300 bg-slate-50 text-slate-500' },
}

export default function JobQuickView({ jobId, onOpenFullView, onClose: _onClose, onRefresh }: JobQuickViewProps) {
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({})

  const { data, isLoading } = useApiQuery(
    ['requisition', 'quick', jobId],
    () => requisitionsApi.get(jobId)
  )

  const { data: pipelineData } = useApiQuery(
    ['pipeline', 'stats', jobId],
    () => pipelineApi.getPipeline(jobId),
    { enabled: !!jobId }
  )

  const { data: appsData } = useApiQuery(
    ['applications', 'latest', jobId],
    () => pipelineApi.listApplications({ requisition_id: jobId, limit: 3 } as any),
    { enabled: !!jobId }
  )

  const requisition = (data as any)?.requisition as JobRequisition
  const pipeline = (pipelineData as any) as PipelineData
  const latestApps = (appsData as any)?.applications as Application[]

  useEffect(() => {
    if (latestApps?.length > 0) {
      const fetchNames = async () => {
        const names: Record<string, string> = {}
        await Promise.all(latestApps.map(async (app) => {
          try {
            const res = await candidatesApi.get(app.candidate_id)
            names[app.candidate_id] = res.data.data.candidate.full_name || 'Unknown Candidate'
          } catch {
            names[app.candidate_id] = 'Unknown Candidate'
          }
        }))
        setCandidateNames(prev => ({ ...prev, ...names }))
      }
      fetchNames()
    }
  }, [latestApps])

  const doAction = async (label: string, fn: () => Promise<unknown>) => {
    setActionLoading(label)
    try {
      await fn()
      message.success(`${label} successful`)
      queryClient.invalidateQueries({ queryKey: ['requisitions'] })
      queryClient.invalidateQueries({ queryKey: ['requisition', 'quick', jobId] })
      if (onRefresh) onRefresh()
    } catch (err: any) {
      message.error(err.response?.data?.message || `${label} failed`)
    } finally {
      setActionLoading(null)
    }
  }

  if (isLoading) return <div className="p-12 text-center"><Spin /></div>
  if (!requisition) return <Empty description="Job not found" />

  const banner = STATUS_BANNER[requisition.status] || STATUS_BANNER.draft
  const daysOpen = dayjs().diff(dayjs(requisition.created_at), 'day')

  const pipelineStages = pipeline?.pipeline ? Object.values(pipeline.pipeline).sort((a, b) => a.stage.stage_order - b.stage.stage_order) : []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', paddingTop: 24 }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px' }}>
        {/* SECTION 1: Status Banner */}
        <div className={cn("border-l-4 p-3 rounded-r-xl mb-6 font-semibold text-sm shadow-sm", banner.color)}>
          {banner.label}
        </div>

        {/* Header Title */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight leading-tight">
            {requisition.title}
          </h2>
          <p className="text-slate-500 mt-1 flex items-center gap-1.5 text-sm font-medium">
            <Briefcase className="h-3.5 w-3.5" /> {requisition.job_type.replace('_', ' ')} · {requisition.work_mode}
          </p>
        </div>

        {/* SECTION 2: Primary Action */}
        <div className="mb-8">
          {requisition.status === 'draft' && (
            <Button 
              type="primary" 
              block 
              className="h-12 rounded-xl font-bold text-base bg-blue-600 border-none shadow-soft-md"
              loading={actionLoading === 'Submit'}
              onClick={() => doAction('Submit', () => requisitionsApi.submitForApproval(requisition.id))}
            >
              Submit for Approval
            </Button>
          )}
          {requisition.status === 'pending_approval' && (
            <Button 
              type="primary" 
              block 
              className="h-12 rounded-xl font-bold text-base bg-emerald-600 border-none shadow-soft-md"
              loading={actionLoading === 'Approve'}
              onClick={() => doAction('Approve', () => requisitionsApi.approve(requisition.id))}
            >
              Approve & Publish
            </Button>
          )}
          {requisition.status === 'approved' && (
            <Button 
              type="primary" 
              block 
              className="h-12 rounded-xl font-bold text-base bg-emerald-600 border-none shadow-soft-md"
              loading={actionLoading === 'Publish'}
              onClick={() => doAction('Publish', () => requisitionsApi.publish(requisition.id))}
            >
              Publish Now
            </Button>
          )}
          {requisition.status === 'active' && (
            <Button 
              type="primary" 
              block 
              className="h-12 rounded-xl font-bold text-base bg-blue-600 border-none shadow-soft-md flex items-center justify-center gap-2"
              onClick={() => onOpenFullView('pipeline')}
            >
              View Pipeline <ArrowRight className="h-5 w-5" />
            </Button>
          )}
        </div>

        {/* SECTION 3: Pipeline Numbers */}
        <div className="mb-8">
          <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Pipeline Status</Title>
          <div className="flex items-center justify-between bg-white rounded-2xl border border-slate-100 p-1 shadow-soft-sm overflow-hidden">
            {pipelineStages.length > 0 ? pipelineStages.map((stageData) => (
              <div 
                key={stageData.stage.id}
                className="flex-1 flex flex-col items-center py-2 cursor-pointer hover:bg-slate-50 transition-colors border-r last:border-0 border-slate-50"
                onClick={() => onOpenFullView('pipeline')}
              >
                <span className={cn("text-lg font-black leading-none", stageData.count === 0 ? "text-amber-500" : "text-slate-900")}>
                  {stageData.count}
                </span>
                <span className="text-[9px] font-bold text-slate-400 uppercase mt-1 tracking-tighter truncate w-full text-center px-1">
                  {stageData.stage.name}
                </span>
              </div>
            )) : <div className="p-4 text-center text-xs text-slate-400 w-full italic">No stages configured</div>}
          </div>
        </div>

        {/* SECTION 4: 3 Key Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-slate-50/50 rounded-2xl p-3 border border-slate-100 flex flex-col items-center justify-center shadow-sm">
            <Calendar className="h-4 w-4 text-slate-400 mb-1" />
            <span className="text-xs font-bold text-slate-900">{daysOpen} Days</span>
            <span className="text-[9px] font-bold text-slate-400 uppercase">Open</span>
          </div>
          <div className="bg-slate-50/50 rounded-2xl p-3 border border-slate-100 flex flex-col items-center justify-center shadow-sm">
            <Users className="h-4 w-4 text-slate-400 mb-1" />
            <span className="text-xs font-bold text-slate-900">{requisition.headcount} Headcount</span>
            <span className="text-[9px] font-bold text-slate-400 uppercase">Target</span>
          </div>
          <div className="bg-slate-50/50 rounded-2xl p-3 border border-slate-100 flex flex-col items-center justify-center shadow-sm">
            <TrendingUp className="h-4 w-4 text-slate-400 mb-1" />
            <div className="flex items-center gap-1">
              <span className={cn("text-xs font-bold capitalize", 
                requisition.priority === 'urgent' ? "text-rose-600" : 
                requisition.priority === 'high' ? "text-amber-600" : "text-blue-600"
              )}>
                {requisition.priority}
              </span>
            </div>
            <span className="text-[9px] font-bold text-slate-400 uppercase">Priority</span>
          </div>
        </div>

        {/* SECTION SKILLS */}
        <div className="mb-8">
          <p style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>SKILLS REQUIRED</p>
          <div className="flex flex-wrap gap-1.5">
            {(requisition.skills_required || []).map(s => 
              <Tag color="blue" key={s} style={{ marginBottom: 4 }}>{s}</Tag>
            )}
          </div>
        </div>

        {/* SECTION 5: Latest 3 Applications */}
        <div className="mb-8">
          <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Latest Applications</Title>
          <div className="space-y-2">
            {latestApps?.length > 0 ? latestApps.map(app => (
              <div key={app.id} className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-50 bg-white shadow-soft-sm hover:border-blue-100 transition-colors cursor-pointer" onClick={() => onOpenFullView('applications')}>
                <div className="h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-slate-900 truncate">
                    {candidateNames[app.candidate_id] || `Candidate ${app.candidate_id.slice(0, 4)}`}
                  </p>
                  <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mt-0.5">
                    {app.status.replace('_', ' ')} · {dayjs(app.created_at).fromNow()}
                  </p>
                </div>
                <ArrowRight className="h-3 w-3 text-slate-300" />
              </div>
            )) : (
              <div className="py-6 text-center rounded-2xl border border-dashed border-slate-200">
                <AlertCircle className="h-5 w-5 text-slate-300 mx-auto mb-2" />
                <p className="text-xs text-slate-400 font-medium">No applications yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SECTION 6: Footer */}
      <div style={{
        position: 'sticky',
        bottom: 0,
        background: 'white',
        borderTop: '1px solid #f0f0f0',
        padding: '12px 16px',
        display: 'flex',
        gap: 8,
        marginTop: 'auto'
      }}>
        <Button 
          style={{ flex: 1 }}
          icon={<Edit className="h-4 w-4" />} 
          className="h-12 rounded-xl font-bold flex items-center justify-center gap-2 border-slate-200 text-slate-600"
        >
          Edit Job
        </Button>
        <Button 
          type="primary" 
          style={{ flex: 2 }}
          className="h-12 rounded-xl font-bold flex items-center justify-center gap-2 bg-slate-900 hover:!bg-slate-800 border-none shadow-soft-md"
          onClick={() => onOpenFullView()}
        >
          Open Full View <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
