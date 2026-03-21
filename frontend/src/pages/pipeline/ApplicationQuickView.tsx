import {
  Button, Tag, Typography, Avatar,
  Spin, Empty, Divider, Descriptions
} from 'antd'
import {
  Mail, Phone, ArrowRight, Star, X, CheckCircle, FileText
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import type { Application, Candidate } from '@/types'
import { cn } from '@/utils/cn'

const { Title } = Typography

interface ApplicationQuickViewProps {
  applicationId: string
  onClose: () => void
  onOpenFullView: () => void
  onShortlist?: (app: Application) => void
  onReject?: (app: Application) => void
}

export default function ApplicationQuickView({ applicationId, onOpenFullView, onShortlist, onReject }: ApplicationQuickViewProps) {
  const { data, isLoading } = useApiQuery(
    ['application', 'quick', applicationId],
    () => pipelineApi.getApplication(applicationId)
  )

  const application = (data as any)?.application as Application
  
  const { data: candidateData } = useApiQuery(
    ['candidate', 'quick', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id),
    { enabled: !!application?.candidate_id }
  )

  const candidate = (candidateData as any)?.candidate as Candidate

  if (isLoading) return <div className="p-12 text-center"><Spin /></div>
  if (!application) return <Empty description="Application not found" />

  const displayName = candidate?.full_name || 'Candidate'
  const daysInStage = dayjs().diff(dayjs(application.updated_at), 'day')

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {/* Profile Header */}
        <div className="flex items-start gap-4 mb-8">
          <Avatar 
            size={64} 
            className="bg-blue-100 text-blue-600 font-bold text-2xl shadow-soft-sm shrink-0"
          >
            {displayName.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight leading-tight">
              {displayName}
            </h2>
            <p className="text-slate-500 font-medium text-sm mt-0.5">
              {candidate?.current_title || 'No Title'}
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              <Tag className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase rounded-full px-2.5">
                {application.match_score || 0}% Match
              </Tag>
              <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase rounded-full px-2.5">
                {application.status.replace(/_/g, ' ')}
              </Tag>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100 mb-8 text-sm">
          <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 120 }}>
            <Descriptions.Item label="Current Stage">
              <span className="font-semibold text-slate-700">{application.current_stage_id}</span>
            </Descriptions.Item>
            <Descriptions.Item label="Days in Stage">
              <span className={cn("font-bold", daysInStage > 7 ? "text-rose-500" : "text-slate-700")}>
                {daysInStage} days
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="Applied Date">
              {dayjs(application.created_at).format('MMM D, YYYY')}
            </Descriptions.Item>
          </Descriptions>
        </div>

        {/* Contact Info (if available) */}
        {candidate && (
          <div className="space-y-3 mb-8 px-1">
            <div className="flex items-center gap-3 text-slate-600">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">{candidate.email}</span>
            </div>
            {candidate.phone && (
              <div className="flex items-center gap-3 text-slate-600">
                <Phone className="h-4 w-4 text-slate-400" />
                <span className="text-sm font-medium">{candidate.phone}</span>
              </div>
            )}
          </div>
        )}

        <Divider />

        {/* Latest Activity (Placeholder) */}
        <div className="mb-8">
          <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Application Journey</Title>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                <CheckCircle className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-700 font-medium leading-tight">Moved to Screening</p>
                <p className="text-slate-400 text-[10px] mt-0.5">YESTERDAY · 14:20</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-slate-50 flex items-center justify-center shrink-0 text-slate-400">
                <FileText className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm text-slate-700 font-medium leading-tight">Applied for position</p>
                <p className="text-slate-400 text-[10px] mt-0.5">3 DAYS AGO · 09:12</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Footer */}
      <div className="pt-6 border-t border-slate-100 mt-auto">
        <div className="grid grid-cols-3 gap-3 mb-4">
          <Button 
            className="h-11 rounded-xl font-bold flex flex-col items-center justify-center gap-0 bg-emerald-50 text-emerald-700 border-none hover:bg-emerald-100"
            onClick={() => onShortlist?.(application)}
          >
            <Star className="h-4 w-4" />
            <span className="text-[9px] uppercase tracking-wider">Shortlist</span>
          </Button>
          <Button 
            className="h-11 rounded-xl font-bold flex flex-col items-center justify-center gap-0 bg-blue-50 text-blue-700 border-none hover:bg-blue-100"
          >
            <ArrowRight className="h-4 w-4" />
            <span className="text-[9px] uppercase tracking-wider">Move</span>
          </Button>
          <Button 
            danger
            className="h-11 rounded-xl font-bold flex flex-col items-center justify-center gap-0 bg-rose-50 text-rose-700 border-none hover:bg-rose-100"
            onClick={() => onReject?.(application)}
          >
            <X className="h-4 w-4" />
            <span className="text-[9px] uppercase tracking-wider">Reject</span>
          </Button>
        </div>

        <Button 
          type="primary" 
          block 
          className="h-12 rounded-xl font-bold flex items-center justify-center gap-2 bg-slate-900 hover:!bg-slate-800 border-none shadow-soft-md"
          onClick={onOpenFullView}
        >
          View Full Application <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
