import { Tag, Space, Timeline, Typography } from 'antd'
import { CheckCircle } from 'lucide-react'
import dayjs from 'dayjs'
import type { Application, ApplicationStatus } from '@/types'

const { Text } = Typography

function prettyLabel(value?: string | null) {
  if (!value) return '—'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDisplayDate(value?: string | null) {
  if (!value) return '—'
  return dayjs(value).isValid() ? dayjs(value).format('MMMM D, YYYY') : value
}

const STATUS_MAP: Record<ApplicationStatus, { label: string; color: string }> = {
  applied: { label: 'Applied', color: 'blue' },
  screening: { label: 'Screening', color: 'cyan' },
  shortlisted: { label: 'Shortlisted', color: 'green' },
  in_review: { label: 'In Review', color: 'orange' },
  interview: { label: 'Interview', color: 'purple' },
  interview_scheduled: { label: 'Interview', color: 'purple' },
  on_hold: { label: 'On Hold', color: 'default' },
  offer_extended: { label: 'Offer', color: 'gold' },
  offer_accepted: { label: 'Accepted', color: 'green' },
  joined: { label: 'Joined', color: 'success' },
  placement_confirmed: { label: 'Confirmed', color: 'success' },
  placement_cancelled: { label: 'Cancelled', color: 'red' },
  rejected: { label: 'Rejected', color: 'red' },
  withdrawn: { label: 'Withdrawn', color: 'default' },
}

export default function AgencySubmissionQVPanel({ data }: { data: { submission: Application; jobTitle?: string } }) {
  const { submission, jobTitle } = data
  const statusInfo = STATUS_MAP[submission.status] || { label: submission.status, color: 'default' }

  return (
    <div className="space-y-8">
      <div className="bg-slate-50 rounded-2xl p-5 border border-slate-100">
        <Space direction="vertical" className="w-full" size={12}>
          <div className="flex justify-between">
            <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Job Role</Text>
            <Text className="text-sm font-bold text-slate-900">{jobTitle || 'Unknown Position'}</Text>
          </div>
          <div className="flex justify-between">
            <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Candidate ID</Text>
            <Text className="text-sm font-bold text-slate-900">{submission.candidate_id}</Text>
          </div>
          <div className="flex justify-between">
            <Text className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Submitted On</Text>
            <Text className="text-sm font-bold text-slate-900">{dayjs(submission.created_at).format('MMMM D, YYYY')}</Text>
          </div>
        </Space>
      </div>

      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Status</h3>
        <div className="flex flex-wrap gap-2">
          <Tag color={statusInfo.color} className="border-none font-bold rounded-lg px-3 py-1 text-xs">{submission.status.toUpperCase()}</Tag>
          {submission.is_agency_protected && (
            <Tag color="purple" className="border-none font-bold rounded-lg px-3 py-1 text-xs">PROTECTED</Tag>
          )}
          {submission.is_under_guarantee && (
            <Tag color="gold" className="border-none font-bold rounded-lg px-3 py-1 text-xs">UNDER GUARANTEE</Tag>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-violet-100 bg-violet-50/60 p-4">
          <h3 className="text-xs font-bold text-violet-700 uppercase tracking-widest mb-3">Candidate Protection</h3>
          {submission.is_agency_protected ? (
            <Space direction="vertical" size={6}>
              <Text className="text-sm"><span className="font-semibold">Protected Until:</span> {formatDisplayDate(submission.protected_until)}</Text>
              <Text className="text-sm"><span className="font-semibold">Scope:</span> {prettyLabel(submission.protection_scope)}</Text>
            </Space>
          ) : (
            <Text className="text-sm text-slate-500">No active protection visible for this submission.</Text>
          )}
        </div>

        <div className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4">
          <h3 className="text-xs font-bold text-amber-700 uppercase tracking-widest mb-3">Guarantee Watch</h3>
          {submission.guarantee_status ? (
            <Space direction="vertical" size={6}>
              <Text className="text-sm"><span className="font-semibold">Status:</span> {prettyLabel(submission.guarantee_status)}</Text>
              <Text className="text-sm"><span className="font-semibold">Guarantee End:</span> {formatDisplayDate(submission.guarantee_end_date)}</Text>
              <Text className="text-sm"><span className="font-semibold">Resolution:</span> {prettyLabel(submission.guarantee_resolution_type)}</Text>
            </Space>
          ) : (
            <Text className="text-sm text-slate-500">No active guarantee data available.</Text>
          )}
        </div>
      </div>

      {!!submission.application_form_data?.cover_note && (
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Cover Note</h3>
          <div className="bg-white p-4 rounded-xl border border-slate-100 italic text-sm text-slate-600 leading-relaxed">
            "{String(submission.application_form_data.cover_note)}"
          </div>
        </div>
      )}

      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Hiring Progress</h3>
        <Timeline items={[{
          dot: <CheckCircle className="h-4 w-4 text-blue-600" />,
          children: (
            <div>
              <Text strong className="text-sm text-slate-900">Application Submitted</Text>
              <p className="text-xs text-slate-400 mt-0.5">{dayjs(submission.created_at).format('MMM D, YYYY · HH:mm')}</p>
            </div>
          )
        }]} />
      </div>
    </div>
  )
}
