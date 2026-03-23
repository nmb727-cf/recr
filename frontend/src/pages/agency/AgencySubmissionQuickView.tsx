import {
  Button, Tag, Typography, Avatar,
  Spin, Empty, Divider, Timeline
} from 'antd'
import {
  ExternalLink, Briefcase, Clock
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { requisitionsApi } from '@/api/jobs'
import type { Application, Candidate, JobRequisition, TimelineEvent } from '@/types'

dayjs.extend(relativeTime)
const { Title, Text } = Typography

interface AgencySubmissionQuickViewProps {
  submission: Application
  jobTitle?: string
  onClose: () => void
}

interface ApplicationResponse {
  application: Application
}

interface CandidateResponse {
  candidate: Candidate
}

interface RequisitionResponse {
  requisition: JobRequisition
}

interface TimelineResponse {
  events: TimelineEvent[]
}

export default function AgencySubmissionQuickView({ submission: initialSubmission, jobTitle: initialJobTitle, onClose }: AgencySubmissionQuickViewProps) {
  const applicationId = initialSubmission.id

  const { data: appData, isLoading: appLoading } = useApiQuery(
    ['application', applicationId],
    () => pipelineApi.getApplication(applicationId)
  )

  const application = (appData as unknown as { data: ApplicationResponse } | undefined)?.data?.application || initialSubmission

  const { data: candidateData, isLoading: candidateLoading } = useApiQuery(
    ['candidate', application.candidate_id],
    () => candidatesApi.get(application.candidate_id),
    { enabled: !!application.candidate_id }
  )

  const candidate = (candidateData as unknown as { data: CandidateResponse } | undefined)?.data?.candidate

  const { data: jobData, isLoading: jobLoading } = useApiQuery(
    ['requisition', application.requisition_id],
    () => requisitionsApi.get(application.requisition_id),
    { enabled: !!application.requisition_id }
  )

  const requisition = (jobData as unknown as unknown as { data: RequisitionResponse } | undefined)?.data?.requisition
  const jobTitle = initialJobTitle || requisition?.title || 'Unknown Position'

  const { data: timelineData } = useApiQuery(
    ['candidate-timeline', application.candidate_id],
    () => candidatesApi.timeline(application.candidate_id),
    { enabled: !!application.candidate_id }
  )
  const timeline = (timelineData as unknown as unknown as { data: TimelineResponse } | undefined)?.data?.events || []

  if ((appLoading && !initialSubmission) || candidateLoading || jobLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-12">
        <Spin size="large" />
        <Text className="mt-4 text-slate-400 font-medium">Loading submission details...</Text>
      </div>
    )
  }

  if (!application) return <Empty description="Submission not found" className="mt-20" />

  const displayName = candidate?.full_name || 'Candidate'
  const statusInfo = {
    applied: { label: 'Applied', color: 'blue' },
    screening: { label: 'Screening', color: 'cyan' },
    shortlisted: { label: 'Shortlisted', color: 'green' },
    in_review: { label: 'In Review', color: 'orange' },
    interview_scheduled: { label: 'Interview', color: 'purple' },
    offer_extended: { label: 'Offer', color: 'gold' },
    offer_accepted: { label: 'Accepted', color: 'green' },
    rejected: { label: 'Rejected', color: 'red' },
    withdrawn: { label: 'Withdrawn', color: 'default' },
  }[application.status] || { label: application.status, color: 'default' }

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-start gap-4 mb-8">
          <Avatar 
            size={64} 
            className="bg-blue-100 text-blue-600 font-bold text-2xl shadow-soft-sm shrink-0 border-none"
          >
            {displayName.charAt(0).toUpperCase()}
          </Avatar>
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight leading-tight truncate">
              {displayName}
            </h2>
            <div className="flex items-center gap-1.5 mt-1 text-slate-500 font-medium text-sm">
              <Briefcase className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{jobTitle}</span>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              <Tag color={statusInfo.color} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
                {statusInfo.label}
              </Tag>
              {application.match_score && (
                <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-full px-2.5 py-0.5">
                  {application.match_score}% Match
                </Tag>
              )}
            </div>
          </div>
        </div>

        {/* Info Grid */}
        <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100 mb-8 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Submitted On</Text>
              <Text className="text-sm font-semibold text-slate-700">{dayjs(application.created_at).format('MMM D, YYYY')}</Text>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Last Updated</Text>
              <Text className="text-sm font-semibold text-slate-700">{dayjs(application.updated_at).fromNow()}</Text>
            </div>
          </div>
          <Divider className="my-0 border-slate-200/60" />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Experience</Text>
              <Text className="text-sm font-semibold text-slate-700">{candidate?.experience_years || 0} Years</Text>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Current Company</Text>
              <Text className="text-sm font-semibold text-slate-700 truncate" title={candidate?.current_company}>{candidate?.current_company || 'N/A'}</Text>
            </div>
          </div>
        </div>

        {/* Submission Note */}
        {application.source_detail && (
          <div className="mb-8">
            <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Submission Note</Title>
            <div className="bg-blue-50/30 p-4 rounded-2xl border border-blue-100/50 italic text-slate-600 text-sm leading-relaxed">
              "{application.source_detail}"
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="mb-8">
          <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Application History</Title>
          {timeline.length > 0 ? (
            <Timeline
              items={timeline.map((event: TimelineEvent, i: number) => ({
                color: i === 0 ? 'blue' : 'gray',
                children: (
                  <div className="pb-4">
                    <p className="m-0 text-sm font-bold text-slate-700 leading-tight">{event.text}</p>
                    <p className="m-0 mt-1 text-[11px] text-slate-400 font-medium uppercase tracking-tight">
                      {dayjs(event.created_at).format('MMM D, YYYY • HH:mm')}
                    </p>
                  </div>
                )
              }))}
            />
          ) : (
             <div className="py-6 text-center border-2 border-dashed border-slate-100 rounded-2xl">
                <Clock className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                <Text className="text-slate-300 font-bold uppercase text-[10px] tracking-widest">No history recorded</Text>
             </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-slate-100 bg-white sticky bottom-0">
        <div className="grid grid-cols-2 gap-3 mb-3">
          <Button 
            block 
            className="h-11 rounded-xl font-bold flex items-center justify-center gap-2 border-slate-200 text-slate-600"
            icon={<Briefcase className="h-4 w-4" />}
          >
            View Job
          </Button>
          <Button 
            block 
            className="h-11 rounded-xl font-bold flex items-center justify-center gap-2 border-slate-200 text-slate-600"
            icon={<ExternalLink className="h-4 w-4" />}
          >
            View Candidate
          </Button>
        </div>
        <Button 
          type="primary" 
          block 
          className="h-12 rounded-xl font-bold flex items-center justify-center gap-2 bg-slate-900 hover:!bg-slate-800 border-none shadow-soft-md"
          onClick={onClose}
        >
          Close Preview
        </Button>
      </div>
    </div>
  )
}
