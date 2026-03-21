import { Button, Tag } from 'antd'
import { Calendar, User, Briefcase, Clock } from 'lucide-react'
import dayjs from 'dayjs'
import type { Interview, InterviewStatus } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const STATUS_COLOR: Record<InterviewStatus, string> = {
  scheduled: 'processing',
  confirmed: 'cyan',
  rescheduled: 'warning',
  in_progress: 'green',
  completed: 'success',
  cancelled: 'error',
  no_show: 'default',
  pending_feedback: 'magenta',
}

export default function InterviewQVPanel({ interview }: { interview: Interview }) {
  const openFullView = useDrawerStore(s => s.openFullView)
  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 shadow-sm border border-purple-100">
          <Calendar className="h-8 w-8" />
        </div>
        <Tag color={STATUS_COLOR[interview.status]} className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {interview.status.replace(/_/g, ' ')}
        </Tag>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{interview.title}</h2>
      </div>
      <div className="space-y-4 bg-slate-50/50 rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Candidate</span>
            <span className="text-sm font-bold text-slate-700">{interview.candidate_name || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Briefcase className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Job Role</span>
            <span className="text-sm font-bold text-slate-700">{interview.job_title || 'N/A'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Clock className="h-4 w-4 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Scheduled At</span>
            <span className="text-sm font-bold text-slate-700">{dayjs(interview.scheduled_at).format('MMM D, YYYY · h:mm A')}</span>
          </div>
        </div>
      </div>
      <Button type="primary" block className="h-12 rounded-xl font-bold bg-slate-900 border-none shadow-soft-md" onClick={() => openFullView()}>
        Open Full Details
      </Button>
    </div>
  )
}
