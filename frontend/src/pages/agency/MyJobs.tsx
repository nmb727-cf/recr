import {
  Table, Tag, Button, Typography, Card,
  Progress,
} from 'antd'
import {
  MapPin, Clock, Plus
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyAssignment, JobRequisition } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const { Text } = Typography

type JobWithAssignment = {
  assignment: AgencyAssignment
  requisition: JobRequisition
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function MyJobs() {
  const navigate = useNavigate()
  const openQuickView = useDrawerStore(s => s.openQuickView)

  const { data, isLoading } = useApiQuery(['agency', 'my-jobs'], () => agenciesApi.myJobs())
  const jobs = (data as any)?.jobs ?? []

  const columns: ColumnsType<JobWithAssignment> = [
    {
      title: 'Job Title',
      key: 'title',
      render: (_, r) => (
        <div className="flex flex-col">
          <Text className="font-bold text-slate-900">{r.requisition.title}</Text>
          <Text className="text-[10px] text-slate-400 font-bold uppercase">{r.requisition.id.slice(0, 8)}</Text>
        </div>
      )
    },
    {
      title: 'Type',
      key: 'type',
      render: (_, r) => <Tag className="border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-md px-2 py-0.5">{r.requisition.job_type.replace('_', ' ')}</Tag>
    },
    {
      title: 'Work Mode',
      key: 'mode',
      render: (_, r) => <span className="text-sm font-medium text-slate-600 capitalize">{r.requisition.work_mode}</span>
    },
    {
      title: 'Location',
      key: 'location',
      render: (_, r) => (
        <span className="text-sm text-slate-500 flex items-center gap-1">
          <MapPin className="h-3.5 w-3.5" /> {r.requisition.location_id || 'Remote'}
        </span>
      )
    },
    {
      title: 'Submissions',
      key: 'submissions',
      render: (_, r) => (
        <div className="flex flex-col">
          <span className="text-sm font-bold text-slate-700">{r.assignment.submissions_count} / {r.assignment.max_submissions}</span>
          <Progress percent={(r.assignment.submissions_count / r.assignment.max_submissions) * 100} showInfo={false} size="small" strokeColor="#3b82f6" />
        </div>
      )
    },
    {
      title: 'Deadline',
      key: 'deadline',
      render: (_, r) => (
        <span className="text-sm font-medium text-slate-500 flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" /> {dayjs(r.assignment.deadline).format('MMM D, YYYY')}
        </span>
      )
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, r) => <Tag color={r.assignment.status === 'active' ? 'green' : 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{r.assignment.status}</Tag>
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">My Assigned Jobs</h1>
          <p className="text-slate-500 mt-1">Roles assigned to your agency by our enterprise clients.</p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} type="primary" className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md" onClick={() => navigate('/agencies/submit-candidate')}>
          New Submission
        </Button>
      </div>

      <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
        <Table<JobWithAssignment>
          columns={columns}
          dataSource={jobs}
          rowKey={(r) => r.assignment.id}
          loading={isLoading}
          onRow={(r) => ({
            onClick: () => openQuickView('agency_job', r),
            className: "cursor-pointer transition-colors hover:bg-slate-50"
          })}
          className="modern-table"
        />
      </Card>
    </div>
  )
}
