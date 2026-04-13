import { useNavigate } from 'react-router-dom'
import { Row, Col, Card, Skeleton, Empty, Tag, Button, Space } from 'antd'
import {
  Users, Briefcase, Calendar,
  ArrowRight, UserPlus, Building2
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { agenciesApi } from '@/api/agencies'
import { interviewsApi } from '@/api/interviews'
import type { AgencyAssignment, Application } from '@/types'
import { cn } from '@/utils/cn'


// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  title, value, icon: Icon, color, loading,
}: {
  title: string
  value: number | string
  icon: any
  color: string
  loading?: boolean
}) {
  return (
    <Card bordered={false} className="group overflow-hidden transition-all duration-300 hover:shadow-soft-lg">
      {loading ? (
        <Skeleton active paragraph={{ rows: 2 }} />
      ) : (
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className={cn('flex h-12 w-12 items-center justify-center rounded-2xl transition-transform duration-300 group-hover:scale-110', color)}>
              <Icon className="h-6 w-6" />
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight mt-1">{value}</h3>
          </div>
          <div className="absolute -right-4 -bottom-4 h-24 w-24 rounded-full bg-slate-50/50 group-hover:bg-slate-100/50 transition-colors duration-300" />
        </div>
      )}
    </Card>
  )
}

// ─── Main Agency Dashboard Component ───────────────────────────────────────────

export default function AgencyDashboard() {
  const navigate = useNavigate()

  // Assignments
  const { data: assignmentsData, isLoading: assignmentsLoading } = useApiQuery<{ assignments: AgencyAssignment[] }>(
    ['agency', 'assignments', 'active'],
    () => agenciesApi.listAssignments()
  )

  // My Submissions
  const { data: submissionsData, isLoading: submissionsLoading } = useApiQuery<{ submissions: Application[] }>(
    ['agency', 'submissions'],
    () => agenciesApi.mySubmissions()
  )

  // Clients
  const { data: clientsData, isLoading: clientsLoading } = useApiQuery<{ relationships: any[] }>(
    ['agency', 'clients'],
    () => agenciesApi.listRelationships()
  )

  // Interviews
  const { data: interviewsData, isLoading: interviewsLoading } = useApiQuery(
    ['agency', 'interviews'],
    () => interviewsApi.list()
  )

  const activeAssignments = assignmentsData?.assignments?.filter(a => a.status === 'active') ?? []
  const submissions = submissionsData?.submissions ?? []
  const activeClients = clientsData?.relationships?.filter(r => r.status === 'active') ?? []
  const interviews = (interviewsData as any)?.interviews ?? []

  const stats = [
    {
      title: 'Active Assignments',
      value: activeAssignments.length,
      icon: Briefcase,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Total Submissions',
      value: submissions.length,
      icon: UserPlus,
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Active Clients',
      value: activeClients.length,
      icon: Building2,
      color: 'bg-orange-50 text-orange-600',
    },
    {
      title: 'Interviews This Month',
      value: interviews.length,
      icon: Calendar,
      color: 'bg-purple-50 text-purple-600',
    },
  ]

  const isLoading = assignmentsLoading || submissionsLoading || clientsLoading || interviewsLoading

  return (
    <div className="space-y-6">
      <Row gutter={[24, 24]}>
        {stats.map((stat, i) => (
          <Col xs={24} sm={12} xl={6} key={i}>
            <StatCard {...stat} loading={isLoading} />
          </Col>
        ))}
      </Row>

      <Row gutter={[24, 24]}>
        {/* Recent Submissions */}
        <Col xs={24} lg={12}>
          <Card
            title={<span className="text-lg font-bold text-slate-900">Recent Submissions</span>}
            bordered={false}
            className="h-full shadow-soft-sm"
            extra={
              <Button type="text" size="small" onClick={() => navigate('/agencies/my-submissions')}>
                View all
              </Button>
            }
          >
            {submissionsLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : submissions.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {submissions.slice(0, 5).map((app: any) => (
                  <div
                    key={app.id}
                    className="flex items-center justify-between py-3 px-2 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-900 truncate">Candidate {app.candidate_id.slice(0, 8)}</p>
                      <p className="text-xs text-slate-500">Submitted {dayjs(app.created_at).fromNow()}</p>
                    </div>
                    <Tag color="blue" style={{ textTransform: 'capitalize' }}>{app.status}</Tag>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No submissions yet. Start by browsing assigned jobs."
                style={{ padding: '40px 0' }}
              >
                <Button
                  type="primary"
                  icon={<Briefcase className="h-4 w-4" />}
                  onClick={() => navigate('/agencies/my-jobs')}
                >
                  Browse My Jobs
                </Button>
              </Empty>
            )}
          </Card>
        </Col>

        {/* Active Assignments */}
        <Col xs={24} lg={12}>
          <Card
            title={<span className="text-lg font-bold text-slate-900">Active Assignments</span>}
            bordered={false}
            className="h-full shadow-soft-sm"
            extra={
              <Button type="text" size="small" onClick={() => navigate('/agencies/my-jobs')}>
                View all
              </Button>
            }
          >
            {assignmentsLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : activeAssignments.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {activeAssignments.slice(0, 3).map((job) => (
                  <div
                    key={job.id}
                    className="flex flex-col py-4 px-2 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer"
                    onClick={() => navigate('/agencies/my-jobs')}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-bold text-slate-900 truncate">{job.job_title}</p>
                      <Tag color="orange" className="m-0 border-none font-bold text-[10px] uppercase">
                        Deadline: {dayjs(job.deadline).format('MMM D')}
                      </Tag>
                    </div>
                    <div className="flex items-center justify-between">
                      <Space size={16} className="text-slate-400">
                        <span className="text-xs flex items-center gap-1.5 font-medium">
                          <Users className="h-3.5 w-3.5" /> {job.submissions_count} / {job.max_submissions} Submissions
                        </span>
                      </Space>
                      <Button type="link" size="small" className="p-0 text-xs font-bold uppercase tracking-wider">
                        Submit <ArrowRight className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No active assignments"
                style={{ padding: '40px 0' }}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
