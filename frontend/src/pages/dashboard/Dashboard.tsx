import { useNavigate } from 'react-router-dom'
import { Row, Col, Card, Skeleton, Empty, Tag, Button, Typography } from 'antd'
import {
  Users, Briefcase, ClipboardCheck, Calendar,
  ArrowRight, Plus, Rocket,
  AlertCircle, MessageSquare, Send, Search, IdCard
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { analyticsApi } from '@/api/analytics'
import { candidateApi } from '@/api/candidate'
import { interviewsApi } from '@/api/interviews'
import { requisitionsApi } from '@/api/jobs'
import { useAuthStore } from '@/store/authStore'
import http from '@/utils/http'
import type { ApiResponse, JobRequisition, CandidateApplication } from '@/types'
import { cn } from '@/utils/cn'
import AgencyDashboard from '../agency/AgencyDashboard'
import RemindersWidget from '@/components/RemindersWidget'

dayjs.extend(relativeTime)
const { Text, Title } = Typography

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

const STATUS_COLOR: Record<string, string> = {
  applied: 'blue',
  screening: 'cyan',
  interview_scheduled: 'gold',
  shortlisted: 'green',
  offer_extended: 'purple',
  offer_accepted: 'success',
  rejected: 'error',
  withdrawn: 'default',
}

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

// ─── Company Dashboard ────────────────────────────────────────────────────────

interface DashboardData {
  jobs: { total: number; active: number; this_month: number }
  candidates: { total: number; new_this_month: number }
  applications: { total: number; by_status: { status: string; count: number }[] }
  interviews: { scheduled: number; completed: number }
}

function CompanyDashboard() {
  const navigate = useNavigate()

  const { data: analytics, isLoading } = useApiQuery<DashboardData>(
    ['analytics', 'dashboard'],
    analyticsApi.dashboard
  )

  const { data: pipelineData } = useApiQuery<any>(
    ['analytics', 'pipeline-overview'],
    analyticsApi.pipeline
  )

  const { data: pendingInterviews } = useApiQuery<any>(
    ['interviews', 'pending-feedback'],
    () => interviewsApi.list({ status: 'pending_feedback' })
  )

  const { data: reqData, isLoading: reqLoading } = useApiQuery<{ requisitions: JobRequisition[] }>(
    ['jobs', 'recent-active'],
    () => requisitionsApi.list({ status: 'active' })
  )

  const stats = [
    {
      title: 'Active Jobs',
      value: analytics?.jobs?.active ?? 0,
      icon: Briefcase,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Total Candidates',
      value: analytics?.candidates?.total ?? 0,
      icon: Users,
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Active Pipeline',
      value: analytics?.applications?.total ?? 0,
      icon: ClipboardCheck,
      color: 'bg-orange-50 text-orange-600',
    },
    {
      title: 'Interviews Scheduled',
      value: analytics?.interviews?.scheduled ?? 0,
      icon: Calendar,
      color: 'bg-purple-50 text-purple-600',
    },
  ]

  const chartData = (analytics?.applications?.by_status ?? []).map((item) => ({
    name: item.status.replace(/_/g, ' '),
    value: item.count,
  }))

  const recentJobs = reqData?.requisitions?.slice(0, 5) ?? []
  const staleCount = pipelineData?.stale_applications || 0
  const pendingFeedbackCount = (pendingInterviews as any)?.interviews?.length || 0
  const offersPendingCount = analytics?.applications?.by_status?.find(s => s.status === 'offer')?.count || 0

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
        {/* Needs Attention & Chart */}
        <Col xs={24} lg={16}>
          <div className="space-y-6 h-full flex flex-col">
            <Card 
              title={<span className="text-lg font-bold text-slate-900">Needs Attention</span>}
              bordered={false}
              className="shadow-soft-sm"
            >
              <Row gutter={16}>
                <Col span={8}>
                  <div 
                    className="p-4 rounded-2xl bg-rose-50 border border-rose-100 cursor-pointer hover:shadow-soft-md transition-all"
                    onClick={() => navigate('/pipeline')}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <AlertCircle className="h-5 w-5 text-rose-600" />
                      <Text className="font-bold text-rose-900">Stale Apps</Text>
                    </div>
                    <Title level={2} className="!m-0 text-rose-600">{staleCount}</Title>
                    <Text className="text-[10px] uppercase font-bold text-rose-400">Stuck &gt; 7 days</Text>
                  </div>
                </Col>
                <Col span={8}>
                  <div 
                    className="p-4 rounded-2xl bg-amber-50 border border-amber-100 cursor-pointer hover:shadow-soft-md transition-all"
                    onClick={() => navigate('/interviews')}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <MessageSquare className="h-5 w-5 text-amber-600" />
                      <Text className="font-bold text-amber-900">Feedback</Text>
                    </div>
                    <Title level={2} className="!m-0 text-amber-600">{pendingFeedbackCount}</Title>
                    <Text className="text-[10px] uppercase font-bold text-amber-400">Pending Input</Text>
                  </div>
                </Col>
                <Col span={8}>
                  <div 
                    className="p-4 rounded-2xl bg-blue-50 border border-blue-100 cursor-pointer hover:shadow-soft-md transition-all"
                    onClick={() => navigate('/pipeline')}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <Send className="h-5 w-5 text-blue-600" />
                      <Text className="font-bold text-blue-900">Offers</Text>
                    </div>
                    <Title level={2} className="!m-0 text-blue-600">{offersPendingCount}</Title>
                    <Text className="text-[10px] uppercase font-bold text-blue-400">Awaiting Response</Text>
                  </div>
                </Col>
              </Row>
            </Card>

            <Card
              title={<span className="text-lg font-bold text-slate-900">Pipeline Distribution</span>}
              bordered={false}
              className="flex-1 shadow-soft-sm"
            >
              {isLoading ? (
                <Skeleton active paragraph={{ rows: 5 }} />
              ) : chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorValue)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No pipeline data" />
              )}
            </Card>
          </div>
        </Col>

        {/* Sidebar widgets */}
        <Col xs={24} lg={8}>
          <div className="space-y-6">
            <RemindersWidget />
            <Card
              title={<span className="text-lg font-bold text-slate-900">Recent Active Jobs</span>}
              bordered={false}
              className="shadow-soft-sm"
              extra={
                <Button type="text" size="small" onClick={() => navigate('/jobs')}>
                  View all
                </Button>
              }
            >
              {reqLoading ? (
                <Skeleton active paragraph={{ rows: 4 }} />
              ) : recentJobs.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {recentJobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50 rounded-lg px-2 transition-colors"
                      onClick={() => navigate(`/jobs?id=${job.id}`)}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-slate-900 truncate">{job.title}</p>
                        <p className="text-xs text-slate-500 capitalize">{job.location_id || 'Remote'} · {job.job_type.replace(/_/g, ' ')}</p>
                      </div>
                      <Tag color="green" className="ml-2 shrink-0 border-none font-bold text-[10px] uppercase rounded-full px-2">Active</Tag>
                    </div>
                  ))}
                </div>
              ) : (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="No active jobs"
                  style={{ padding: '40px 0' }}
                >
                  <Button type="primary" size="small" icon={<Plus className="h-3.5 w-3.5" />} onClick={() => navigate('/jobs')}>
                    Post a Job
                  </Button>
                </Empty>
              )}
            </Card>
          </div>
        </Col>
      </Row>
    </div>
  )
}

// ─── Candidate Dashboard ──────────────────────────────────────────────────────

function CandidateDashboard() {
  const navigate = useNavigate()

  const { data: appsData, isLoading: appsLoading } = useApiQuery(
    ['candidate', 'applications'],
    () => candidateApi.listApplications()
  )

  const { data: interviewsData, isLoading: interviewsLoading } = useApiQuery(
    ['candidate', 'interviews'],
    () => interviewsApi.list({ status: 'scheduled' })
  )

  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['candidate', 'available-jobs'],
    () => candidateApi.searchJobs()
  )

  const { data: passportData, isLoading: passportLoading } = useApiQuery(
    ['candidate', 'passport'],
    () => http.get<ApiResponse<{ passport: { completeness_score: number } }>>('/passport/my-passport/')
  )

  const applications = (appsData as unknown as { applications: CandidateApplication[] } | undefined)?.applications ?? []
  const interviews = (interviewsData as { interviews: unknown[] } | undefined)?.interviews ?? []
  const availableJobs = (jobsData as { jobs: unknown[] } | undefined)?.jobs ?? []
  const completeness = (passportData as { passport?: { completeness_score?: number } } | undefined)?.passport?.completeness_score ?? 0

  const isLoading = appsLoading || interviewsLoading || jobsLoading || passportLoading

  const stats = [
    {
      title: 'My Applications',
      value: applications.length,
      icon: ClipboardCheck,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Interviews Scheduled',
      value: interviews.length,
      icon: Calendar,
      color: 'bg-purple-50 text-purple-600',
    },
    {
      title: 'Jobs Available',
      value: availableJobs.length,
      icon: Search,
      color: 'bg-orange-50 text-orange-600',
    },
    {
      title: 'Passport Completeness',
      value: `${completeness}%`,
      icon: IdCard,
      color: completeness === 100 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600',
    },
  ]

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
        {/* Recent Applications */}
        <Col xs={24} lg={14}>
          <Card
            title={<span className="text-lg font-bold text-slate-900">My Recent Applications</span>}
            bordered={false}
            className="h-full shadow-soft-sm"
            extra={
              <Button type="text" size="small" onClick={() => navigate('/candidate/applications')}>
                View all
              </Button>
            }
          >
            {appsLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : applications.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {applications.slice(0, 6).map((app) => (
                  <div
                    key={app.id}
                    className="flex items-center justify-between py-3 px-2 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer"
                    onClick={() => navigate('/candidate/applications')}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-900 truncate">{app.job_title}</p>
                      <p className="text-xs text-slate-500">{app.company_name} · {dayjs(app.applied_at).fromNow()}</p>
                    </div>
                    <Tag
                      color={STATUS_COLOR[app.status] ?? 'default'}
                      className="ml-2 shrink-0"
                      style={{ textTransform: 'capitalize' }}
                    >
                      {app.status.replace(/_/g, ' ')}
                    </Tag>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No activity yet. Start by searching for jobs."
                style={{ padding: '40px 0' }}
              >
                <Button
                  type="primary"
                  icon={<Search className="h-4 w-4" />}
                  onClick={() => navigate('/candidate/jobs')}
                >
                  Browse Jobs
                </Button>
              </Empty>
            )}
          </Card>
        </Col>

        {/* Browse Jobs CTA */}
        <Col xs={24} lg={10}>
          <Card
            bordered={false}
            className="h-full shadow-soft-sm overflow-hidden"
            style={{ background: 'linear-gradient(135deg, #1890ff 0%, #6366f1 100%)' }}
          >
            <div className="flex flex-col items-center justify-center text-center py-8 gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20">
                <Rocket className="h-8 w-8 text-white" />
              </div>
              <div>
                <p className="text-xl font-bold text-white">Ready for your next role?</p>
                <p className="text-blue-100 text-sm mt-1">
                  {availableJobs.length > 0
                    ? `${availableJobs.length} jobs match your profile`
                    : 'Explore opportunities waiting for you'}
                </p>
              </div>
              <Button
                size="large"
                icon={<ArrowRight className="h-4 w-4" />}
                onClick={() => navigate('/candidate/jobs')}
                className="bg-white text-blue-600 border-0 font-semibold hover:bg-blue-50"
              >
                Browse Available Jobs
              </Button>
              {completeness < 100 && (
                <p
                  className="text-blue-200 text-xs cursor-pointer hover:text-white transition-colors"
                  onClick={() => navigate('/passport')}
                >
                  Complete your passport to stand out →
                </p>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

// ─── Main Dashboard (role-branched) ──────────────────────────────────────────

export default function Dashboard() {
  const user = useAuthStore((state) => state.user)
  const isAgency = user?.role === 'agency_owner' || user?.role === 'agency_recruiter'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            {getGreeting()}, {user?.first_name ?? 'there'}
          </h1>
          <p className="text-slate-500 mt-1">
            {user?.role === 'candidate'
              ? 'Track your applications and upcoming interviews.'
              : isAgency
                ? 'Here\'s your agency activity today.'
                : 'Here\'s what\'s happening with your recruitment pipeline today.'}
          </p>
        </div>
        {user?.role !== 'candidate' && !isAgency && (
          <div className="flex items-center gap-3">
            <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => window.location.href = '/jobs'}>
              Create Job
            </Button>
          </div>
        )}
      </div>

      {user?.role === 'candidate' ? (
        <CandidateDashboard />
      ) : isAgency ? (
        <AgencyDashboard />
      ) : (
        <CompanyDashboard />
      )}
    </motion.div>
  )
}
