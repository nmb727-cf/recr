import { Tag, Card, Descriptions, Spin, Empty } from 'antd'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import type { AgencyRelationship, AgencyAssignment } from '@/types'

export default function AgencyClientQVPanel({ relationship }: { relationship: AgencyRelationship }) {
  const { data: assignmentsData, isLoading } = useApiQuery(
    ['agency', 'assignments', 'client', relationship.tenant_id],
    () => agenciesApi.listAssignments()
  )
  const activeJobs = (assignmentsData as any)?.assignments?.filter((a: AgencyAssignment) => a.status === 'active') ?? []

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-20 w-20 rounded-3xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 shadow-sm border border-blue-100 font-black text-3xl">
          {relationship.id.slice(0, 1).toUpperCase()}
        </div>
        <Tag color={relationship.status === 'active' ? 'green' : 'orange'} className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {relationship.status}
        </Tag>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Client {relationship.tenant_id.slice(0, 8)}</h2>
      </div>

      <Card title={<span className="text-xs font-bold uppercase tracking-widest text-slate-400">Relationship Terms</span>} bordered={false} className="shadow-soft-sm bg-slate-50/50">
        <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 140 }}>
          <Descriptions.Item label="Tier">
            <Tag color="blue" className="m-0 border-none font-bold uppercase text-[10px]">{relationship.tier}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Commission">{relationship.commission_percentage}%</Descriptions.Item>
          <Descriptions.Item label="SLA hours">{relationship.sla_hours} Hours</Descriptions.Item>
          <Descriptions.Item label="Partner Since">{dayjs(relationship.created_at).format('MMMM D, YYYY')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Active Job Assignments</h3>
        {isLoading ? <Spin /> : activeJobs.length > 0 ? (
          <div className="space-y-3">
            {activeJobs.slice(0, 5).map((job: AgencyAssignment) => (
              <div key={job.id} className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-white shadow-soft-sm">
                <div className="min-w-0">
                  <p className="text-sm font-bold text-slate-900 truncate">{job.job_title}</p>
                  <p className="text-[10px] text-slate-400 font-medium uppercase mt-0.5">Ref: {job.requisition_id.slice(0, 8)}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-700">{job.submissions_count} / {job.max_submissions}</p>
                  <p className="text-[9px] text-slate-400 font-bold uppercase">Apps</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No active assignments" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </div>
    </div>
  )
}
