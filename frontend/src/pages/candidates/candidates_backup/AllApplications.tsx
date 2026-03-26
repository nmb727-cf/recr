import {
  Table, Tag, Typography, Card, Avatar, Skeleton
} from 'antd'
import {
  Briefcase, Clock
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import type { Application, JobRequisition, Candidate } from '@/types'

const { Text } = Typography

export default function AllApplications() {
  const { data, isLoading } = useApiQuery(
    ['all-applications'],
    () => pipelineApi.listApplications()
  )

  const { data: jobsData } = useApiQuery(
    ['all-jobs'],
    () => requisitionsApi.list()
  )

  const { data: candidatesData } = useApiQuery(
    ['all-candidates'],
    () => candidatesApi.list()
  )

  const applications = (data as { applications: Application[] } | undefined)?.applications ?? []
  const jobs = (jobsData as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []
  const candidates = (candidatesData as { candidates: Candidate[] } | undefined)?.candidates ?? []

  const jobMap = new Map(jobs.map(j => [j.id, j]))
  const candidateMap = new Map(candidates.map(c => [c.id, c]))

  const columns: ColumnsType<Application> = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_, r) => {
        const c = candidateMap.get(r.candidate_id)
        return (
          <div className="flex items-center gap-3">
            <Avatar size="small" className="bg-slate-100 text-slate-600 font-bold">
              {c?.full_name?.charAt(0).toUpperCase() || 'C'}
            </Avatar>
            <Text className="font-bold text-slate-900">{c?.full_name || 'Unknown'}</Text>
          </div>
        )
      }
    },
    {
      title: 'Job Position',
      key: 'job',
      render: (_, r) => {
        const j = jobMap.get(r.requisition_id)
        return (
          <div className="flex items-center gap-2">
            <Briefcase className="h-3.5 w-3.5 text-slate-400" />
            <Text className="font-medium text-slate-700">{j?.title || 'Unknown'}</Text>
          </div>
        )
      }
    },
    {
      title: 'Stage',
      dataIndex: 'current_stage_id',
      key: 'stage',
      render: (stage) => <Tag className="border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-md">{stage || 'Initial'}</Tag>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s) => <Tag color="blue" className="m-0 border-none font-bold text-[10px] uppercase rounded-full">{s.replace('_', ' ')}</Tag>
    },
    {
      title: 'Applied On',
      dataIndex: 'created_at',
      key: 'date',
      render: (d) => (
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <Clock className="h-3.5 w-3.5" />
          {dayjs(d).format('MMM D, YYYY')}
        </div>
      )
    }
  ]

  return (
    <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0">
      {isLoading ? (
        <div className="p-6 space-y-4">
          {[...Array(5)].map((_, i) => <Skeleton key={i} active paragraph={{ rows: 1 }} />)}
        </div>
      ) : (
        <Table<Application>
          columns={columns}
          dataSource={applications}
          rowKey="id"
          pagination={{ pageSize: 15 }}
          className="modern-table"
        />
      )}
    </Card>
  )
}
