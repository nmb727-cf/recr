import { Card, Descriptions, Tag, Empty, Tabs, Typography } from 'antd'
import { Calendar, User, Briefcase, Clock, Video } from 'lucide-react'
import dayjs from 'dayjs'
import type { Interview, InterviewStatus } from '@/types'

const { Text } = Typography

const STATUS_COLOR: Record<InterviewStatus, string> = {
  scheduled: 'processing', confirmed: 'cyan', rescheduled: 'warning',
  in_progress: 'green', paused: 'warning', completed: 'success', cancelled: 'error',
  no_show: 'default', pending_feedback: 'magenta', awaiting_feedback: 'magenta',
  awaiting_decision: 'gold', rejected: 'error',
}

export default function InterviewFVPanel({ interview }: { interview: Interview }) {
  return (
    <div className="space-y-6">
      <div className="flex items-start gap-5">
        <div className="flex h-16 w-14 shrink-0 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 shadow-soft-lg">
          <Calendar className="h-8 w-8" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{interview.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <Tag color={STATUS_COLOR[interview.status]} className="m-0 border-none uppercase font-bold text-[10px] rounded-full px-3">{interview.status.replace(/_/g, ' ')}</Tag>
            <Tag className="m-0 border-none bg-slate-100 text-slate-600 uppercase font-bold text-[10px] rounded-full">{interview.interview_type?.replace(/_/g, ' ')}</Tag>
          </div>
        </div>
      </div>

      <Tabs className="modern-tabs" items={[
        {
          key: 'details',
          label: 'Details',
          children: (
            <div className="space-y-4">
              <Card bordered={false} className="shadow-soft-sm">
                <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 140 }}>
                  <Descriptions.Item label={<span className="flex items-center gap-1"><User className="h-3.5 w-3.5" /> Candidate</span>}>
                    <Text strong>{interview.candidate_name || 'N/A'}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label={<span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> Job Role</span>}>
                    {interview.job_title || 'N/A'}
                  </Descriptions.Item>
                  <Descriptions.Item label={<span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Scheduled</span>}>
                    {dayjs(interview.scheduled_at).format('MMMM D, YYYY · h:mm A')}
                  </Descriptions.Item>
                  <Descriptions.Item label="Round">
                    Round {interview.interview_round}
                  </Descriptions.Item>
                  {interview.meeting_link && (
                    <Descriptions.Item label={<span className="flex items-center gap-1"><Video className="h-3.5 w-3.5" /> Meeting Link</span>}>
                      <a href={interview.meeting_link} target="_blank" rel="noreferrer" className="text-blue-600 font-medium">Join Meeting</a>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </div>
          )
        },
        {
          key: 'questions',
          label: 'Questions',
          children: (
            <Card bordered={false} className="shadow-soft-sm">
              <Empty description="No questions added yet" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '40px 0' }} />
            </Card>
          )
        },
        {
          key: 'feedback',
          label: 'Feedback',
          children: (
            <Card bordered={false} className="shadow-soft-sm">
              {interview.status === 'completed' || interview.status === 'pending_feedback' ? (
                <Empty description="Feedback pending submission" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '40px 0' }} />
              ) : (
                <Empty description="Interview not yet completed" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '40px 0' }} />
              )}
            </Card>
          )
        },
      ]} />
    </div>
  )
}
