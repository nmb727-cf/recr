import { Tag, Steps, Card, Descriptions, Typography, Empty, Tabs } from 'antd'
import { CalendarOutlined, SolutionOutlined, SyncOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ApplicationStatus } from '@/types'

const { Text } = Typography

const STATUS_MAP: Record<ApplicationStatus, { label: string; color: string; step: number }> = {
  applied: { label: 'Applied', color: 'blue', step: 0 },
  screening: { label: 'Screening', color: 'cyan', step: 1 },
  shortlisted: { label: 'Shortlisted', color: 'geekblue', step: 2 },
  in_review: { label: 'In Review', color: 'orange', step: 2 },
  interview: { label: 'Interview', color: 'purple', step: 3 },
  interview_scheduled: { label: 'Interview', color: 'purple', step: 3 },
  on_hold: { label: 'On Hold', color: 'default', step: 2 },
  offer_extended: { label: 'Offer', color: 'gold', step: 4 },
  offer_accepted: { label: 'Accepted', color: 'green', step: 4 },
  joined: { label: 'Joined', color: 'success', step: 5 },
  placement_confirmed: { label: 'Confirmed', color: 'success', step: 5 },
  placement_cancelled: { label: 'Cancelled', color: 'red', step: -1 },
  rejected: { label: 'Rejected', color: 'red', step: -1 },
  withdrawn: { label: 'Withdrawn', color: 'default', step: -1 },
}

const STEPS = [
  { title: 'Applied', icon: <SolutionOutlined /> },
  { title: 'Screening' },
  { title: 'Shortlisted' },
  { title: 'Interview', icon: <CalendarOutlined /> },
  { title: 'Offer' },
  { title: 'Joined' },
]

export default function CandidateApplicationFVPanel({ data }: { data: any }) {
  const statusInfo = STATUS_MAP[data.status as ApplicationStatus] || { label: data.status, color: 'default', step: 0 }

  return (
    <div className="space-y-8">
      <div className="flex items-start gap-5">
        <div className="flex h-16 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 shadow-soft-lg">
          <SolutionOutlined style={{ fontSize: 28 }} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{data.jobTitle || 'Application'}</h1>
          <div className="flex items-center gap-2 mt-2">
            <Tag color={statusInfo.color} className="m-0 border-none uppercase font-bold text-[10px] rounded-full px-3">{statusInfo.label}</Tag>
            {data.jobType && <Tag className="m-0 border-none bg-slate-100 text-slate-600 uppercase font-bold text-[10px] rounded-full">{data.jobType.replace(/_/g, ' ')}</Tag>}
          </div>
        </div>
      </div>

      <Tabs className="modern-tabs" items={[
        {
          key: 'status',
          label: 'Status',
          children: (
            <div className="space-y-8">
              <Card bordered={false} className="shadow-soft-sm">
                <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 120 }}>
                  <Descriptions.Item label="Current Status">
                    <Tag color={statusInfo.color} className="border-none font-bold uppercase text-[10px]">{statusInfo.label}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Applied On">
                    {dayjs(data.created_at).format('MMMM D, YYYY')}
                  </Descriptions.Item>
                  {data.jobType && <Descriptions.Item label="Job Type"><Text className="capitalize">{data.jobType.replace(/_/g, ' ')}</Text></Descriptions.Item>}
                  {data.workMode && <Descriptions.Item label="Work Mode"><Text className="capitalize">{data.workMode}</Text></Descriptions.Item>}
                </Descriptions>
              </Card>
              <Card title={<span className="text-sm font-bold">Pipeline Progress</span>} bordered={false} className="shadow-soft-sm">
                <Steps
                  size="small"
                  current={statusInfo.step}
                  status={data.status === 'rejected' ? 'error' : 'process'}
                  items={STEPS}
                  className="application-steps"
                />
              </Card>
            </div>
          )
        },
        {
          key: 'history',
          label: 'Stage History',
          children: (
            <Card bordered={false} className="shadow-soft-sm">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                      <SyncOutlined />
                    </div>
                    <div className="w-[2px] bg-slate-100 flex-1 mt-2" />
                  </div>
                  <div className="pt-1 pb-4">
                    <Text strong className="block">Application Received</Text>
                    <Text className="text-xs text-slate-400">{dayjs(data.created_at).format('MMM D, YYYY · HH:mm')}</Text>
                  </div>
                </div>
              </div>
            </Card>
          )
        },
        {
          key: 'interviews',
          label: 'Interviews',
          children: (
            <Card bordered={false} className="shadow-soft-sm">
              {data.status === 'interview_scheduled' ? (
                <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
                  <p className="text-sm font-bold text-purple-900">Interview Scheduled</p>
                  <p className="text-xs text-purple-600 mt-1">Check your calendar for details.</p>
                </div>
              ) : (
                <Empty description="No interviews scheduled yet" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '40px 0' }} />
              )}
            </Card>
          )
        },
      ]} />
    </div>
  )
}
