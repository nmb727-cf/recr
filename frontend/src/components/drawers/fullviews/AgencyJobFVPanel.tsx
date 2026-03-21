import { Card, Descriptions, Tag, Progress, Table, Typography, Tabs } from 'antd'
import { MapPin } from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyAssignment, JobRequisition, Application } from '@/types'

const { Text } = Typography
type JobWithAssignment = { assignment: AgencyAssignment; requisition: JobRequisition }

export default function AgencyJobFVPanel({ data }: { data: JobWithAssignment }) {
  const { requisition, assignment } = data

  const { data: submissionsData, isLoading } = useApiQuery(
    ['agency', 'submissions', requisition.id],
    () => agenciesApi.mySubmissions()
  )
  const submissions = ((submissionsData as any)?.submissions ?? []) as Application[]
  const jobSubmissions = submissions.filter(s => s.requisition_id === requisition.id)

  const submissionColumns = [
    { title: 'Candidate ID', key: 'candidate', render: (_: any, r: Application) => <Text className="font-bold">{r.candidate_id.slice(0, 8)}</Text> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="blue" className="border-none font-bold text-[10px] uppercase">{s}</Tag> },
    { title: 'Submitted', dataIndex: 'created_at', key: 'date', render: (d: string) => <span className="text-slate-500 text-sm">{dayjs(d).format('MMM D, YYYY')}</span> },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-5">
        <div className="flex h-16 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-soft-lg">
          <MapPin className="h-7 w-7" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{requisition.title}</h1>
          <p className="text-slate-500 text-sm mt-1">{requisition.job_type.replace('_', ' ')} · {requisition.work_mode} · {requisition.location_id || 'Remote'}</p>
        </div>
      </div>

      <Tabs className="modern-tabs" items={[
        {
          key: 'details',
          label: 'Job Details',
          children: (
            <div className="space-y-6">
              <Card bordered={false} className="shadow-soft-sm">
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="Experience">{requisition.experience_min}–{requisition.experience_max}y</Descriptions.Item>
                  <Descriptions.Item label="Headcount">{requisition.headcount}</Descriptions.Item>
                  <Descriptions.Item label="Status"><Tag color="green" className="border-none font-bold uppercase text-[10px]">{requisition.status}</Tag></Descriptions.Item>
                  <Descriptions.Item label="Priority"><Tag className="border-none font-bold uppercase text-[10px]">{requisition.priority}</Tag></Descriptions.Item>
                </Descriptions>
              </Card>
              <Card bordered={false} className="shadow-soft-sm">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Submission Quota</span>
                  <span className="font-bold text-slate-700">{assignment.submissions_count} / {assignment.max_submissions}</span>
                </div>
                <Progress percent={(assignment.submissions_count / assignment.max_submissions) * 100} strokeColor="#3b82f6" />
                <p className="text-xs text-amber-600 font-bold mt-3">Deadline: {dayjs(assignment.deadline).format('MMMM D, YYYY')}</p>
              </Card>
            </div>
          )
        },
        {
          key: 'submissions',
          label: `Submissions (${jobSubmissions.length})`,
          children: (
            <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
              <Table
                dataSource={jobSubmissions}
                columns={submissionColumns}
                rowKey="id"
                loading={isLoading}
                size="middle"
                className="modern-table"
              />
            </Card>
          )
        },
      ]} />
    </div>
  )
}
