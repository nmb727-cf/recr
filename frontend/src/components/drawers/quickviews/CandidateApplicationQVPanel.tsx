import { Tag, Descriptions, Steps, Typography } from 'antd'
import { SolutionOutlined, CalendarOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ApplicationStatus } from '@/types'

const { Title, Text } = Typography

const STATUS_MAP: Record<ApplicationStatus, { label: string; color: string; step: number }> = {
  applied: { label: 'Applied', color: 'blue', step: 0 },
  screening: { label: 'Screening', color: 'cyan', step: 1 },
  shortlisted: { label: 'Shortlisted', color: 'geekblue', step: 2 },
  in_review: { label: 'In Review', color: 'orange', step: 2 },
  interview_scheduled: { label: 'Interview', color: 'purple', step: 3 },
  offer_extended: { label: 'Offer', color: 'gold', step: 4 },
  offer_accepted: { label: 'Accepted', color: 'green', step: 5 },
  rejected: { label: 'Rejected', color: 'red', step: -1 },
  withdrawn: { label: 'Withdrawn', color: 'default', step: -1 },
}

const STEPS = [
  { title: 'Applied' },
  { title: 'Screening' },
  { title: 'Shortlisted' },
  { title: 'Interview' },
  { title: 'Offer' },
  { title: 'Joined' },
]

export default function CandidateApplicationQVPanel({ data }: { data: any }) {
  const statusInfo = STATUS_MAP[data.status as ApplicationStatus] || { label: data.status, color: 'default', step: 0 }

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 shadow-sm border border-blue-100">
          <SolutionOutlined style={{ fontSize: 28 }} />
        </div>
        <Tag color={statusInfo.color} className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {statusInfo.label}
        </Tag>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{data.jobTitle || 'Application'}</h2>
      </div>

      <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
        <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 120 }}>
          <Descriptions.Item label="Status">
            <Tag className="m-0 uppercase font-bold text-[10px]">{data.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Applied">
            <Text className="text-xs flex items-center gap-1">
              <CalendarOutlined /> {dayjs(data.created_at).format('MMMM D, YYYY')}
            </Text>
          </Descriptions.Item>
          {data.jobType && <Descriptions.Item label="Type"><Text className="text-xs capitalize">{data.jobType.replace(/_/g, ' ')}</Text></Descriptions.Item>}
          {data.workMode && <Descriptions.Item label="Mode"><Text className="text-xs capitalize">{data.workMode}</Text></Descriptions.Item>}
        </Descriptions>
      </div>

      <div>
        <Title level={5} className="!mb-4">Hiring Timeline</Title>
        <Steps
          size="small"
          current={statusInfo.step}
          status={data.status === 'rejected' ? 'error' : 'process'}
          items={STEPS}
          className="application-steps"
        />
      </div>
    </div>
  )
}
