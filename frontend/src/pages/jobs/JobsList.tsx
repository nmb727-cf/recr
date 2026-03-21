import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Button, Input, Select, Typography, Row, Col, Card,
  Drawer, Tag, Tabs, Spin, Badge, message, Space
} from 'antd'
import {
  Plus,
  Search,
  Briefcase,
  Download,
  RefreshCw,
  X,
  ChevronRight,
  ArrowRight,
  Send,
  CheckCircle,
  Globe,
  LayoutGrid
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { requisitionsApi } from '@/api/jobs'
import { agenciesApi } from '@/api/agencies'
import { pipelineApi } from '@/api/pipeline'
import { interviewsApi } from '@/api/interviews'
import type { JobRequisition } from '@/types'
import { cn } from '@/utils/cn'
import JobCreateForm from '@/components/forms/JobCreateForm'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Title, Text } = Typography

// ─── Status Config ──────────────────────────────────────────────────────────

// ─── Sub-components ─────────────────────────────────────────────────────────

const FullJobList = ({ jobs, onSelect, selectedJobId, isLoading }: any) => {
  const jobList = Array.isArray(jobs) ? jobs : []

  const columns: ColumnsType<JobRequisition> = [
    {
      title: 'Job Role',
      dataIndex: 'title',
      key: 'title',
      render: (title, record) => (
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Briefcase className="h-4.5 w-4.5" />
          </div>
          <div>
            <Text className="block font-bold text-slate-900 leading-tight">{title || 'Untitled'}</Text>
            <Text className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">
              {record?.location_id || 'Remote'} • {record?.job_type?.replace('_', ' ') || 'Full Time'}
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const config = getStatusStyle(status, 'job')
        return (
          <div className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider", config.softClass)}>
            <span className={cn("h-1 w-1 rounded-full", config.dotClass)} />
            {formatStatusLabel(status)}
          </div>
        )
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => (
        <Tag color={priority === 'high' || priority === 'urgent' ? 'red' : priority === 'medium' ? 'orange' : 'blue'} 
             className="m-0 border-none font-bold text-[10px] uppercase rounded px-2">
          {priority || 'Medium'}
        </Tag>
      )
    },
    {
      title: 'Applications',
      key: 'applications',
      width: 150,
      render: (_, record) => {
        const metadata = record?.metadata || {}
        return (
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <Badge count={Number(metadata?.applications_count) || 0} showZero overflowCount={999} 
                     style={{ backgroundColor: '#3b82f6', fontSize: '10px' }} />
              <Text className="text-[11px] font-bold text-slate-400 uppercase">Total</Text>
            </div>
            {/* Pipeline Mini-stats */}
            <div className="flex gap-1 mt-1">
               <div className="bg-slate-100 rounded px-1.5 py-0.5 text-[9px] font-bold text-slate-500">APP {Number(metadata?.applied) || 0}</div>
               <div className="bg-blue-50 rounded px-1.5 py-0.5 text-[9px] font-bold text-blue-600">INT {Number(metadata?.interview) || 0}</div>
               <div className="bg-emerald-50 rounded px-1.5 py-0.5 text-[9px] font-bold text-emerald-600">OFF {Number(metadata?.offer) || 0}</div>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Days Open',
      dataIndex: 'created_at',
      key: 'days_open',
      width: 120,
      render: (date) => {
        const days = date ? dayjs().diff(dayjs(date), 'day') : 0
        return (
          <div className="flex flex-col">
            <Text className="text-sm font-bold text-slate-700">{days} Days</Text>
            <Text className="text-[10px] text-slate-400 font-medium uppercase">Since Posted</Text>
          </div>
        )
      }
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />
    }
  ]

  return (
    <Table<JobRequisition>
      columns={columns}
      dataSource={jobList}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          "cursor-pointer transition-all duration-200",
          record.id === selectedJobId ? "bg-blue-50 hover:bg-blue-50" : "hover:bg-slate-50"
        ),
      })}
      pagination={{ pageSize: 10, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedJobList = ({ jobs, onSelect, selectedJobId }: any) => {
  const jobList = Array.isArray(jobs) ? jobs : []
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
        <Text className="font-bold text-slate-900">All Jobs</Text>
        <Badge count={jobList.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
      </div>
      {jobList.map((item: any) => (
        <div 
          key={item.id}
          onClick={() => onSelect(item)}
          className={cn(
            "p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
            item.id === selectedJobId 
              ? "bg-blue-50/50 border-l-blue-600" 
              : "bg-white border-l-transparent hover:bg-slate-50"
          )}
        >
          <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
            {item.title || 'Untitled'}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <div className={cn(
              "text-[9px] font-bold uppercase px-1.5 py-0.5 rounded",
              getStatusStyle(item.status, 'job').softClass
            )}>
              {formatStatusLabel(item.status || 'draft')}
            </div>
            <Text className="text-[10px] text-slate-400 font-medium truncate uppercase">
              {item.location_id || 'Remote'}
            </Text>
          </div>
        </div>
      ))}
    </div>
  )
}

const JobDetailPanel = ({ job, onClose }: { job: JobRequisition, onClose: () => void }) => {
  const jobId = job?.id
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch applications for this job
  const { data: appsData, isLoading: appsLoading } = useApiQuery(
    ['job-applications', jobId],
    () => pipelineApi.listApplications({ requisition_id: jobId }),
    { enabled: !!jobId }
  )

  // Fetch pipeline for this job
  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['job-pipeline', jobId],
    () => pipelineApi.getPipeline(jobId),
    { enabled: !!jobId }
  )

  // Fetch interviews for this job
  const { data: interviewsData } = useApiQuery(
    ['job-interviews', jobId],
    () => interviewsApi.list({ requisition_id: jobId }),
    { enabled: !!jobId }
  )

  // Fetch assigned agencies
  const { data: agenciesData } = useApiQuery(
    ['job-agencies', jobId],
    () => agenciesApi.listAssignments(),
    { enabled: !!jobId }
  )

  // Actions
  const submitMutation = useMutation({
    mutationFn: () => requisitionsApi.submitForApproval(jobId!),
    onSuccess: () => {
      message.success('Requisition submitted for approval')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const approveMutation = useMutation({
    mutationFn: () => requisitionsApi.approve(jobId!),
    onSuccess: () => {
      message.success('Requisition approved')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const publishMutation = useMutation({
    mutationFn: () => requisitionsApi.publish(jobId!),
    onSuccess: () => {
      message.success('Requisition published and is now ACTIVE')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    }
  })

  const applications = Array.isArray((appsData as any)?.applications) ? (appsData as any).applications : []
  const interviews = Array.isArray((interviewsData as any)?.interviews) ? (interviewsData as any).interviews : []
  const pipeline = (pipelineData as any)?.pipeline || {}
  const allAssignments = Array.isArray((agenciesData as any)?.assignments) ? (agenciesData as any).assignments : []
  const assignedAgenciesCount = allAssignments.filter((a: any) => a.requisition_id === jobId).length

  const formatSalary = (amount: any) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: job?.salary_currency || 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div className="p-6">
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Experience', value: `${job?.experience_min || 0}-${job?.experience_max || 0} years` },
              { label: 'Salary Range', value: `${formatSalary(job?.salary_min)} - ${formatSalary(job?.salary_max)}` },
              { label: 'Headcount', value: job?.headcount || 0 },
              { label: 'Job Type', value: job?.job_type?.replace('_', ' ') || 'N/A' },
              { label: 'Work Mode', value: job?.work_mode || 'N/A' },
              { label: 'Priority', value: job?.priority || 'Medium', type: 'tag' },
              { label: 'Assigned Agencies', value: assignedAgenciesCount }
            ].map((stat, i) => (
              <div key={i} className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</Text>
                {stat.type === 'tag' ? (
                  <Tag color={stat.value === 'high' ? 'red' : 'blue'} className="m-0 font-bold uppercase text-[11px]">{stat.value as string}</Tag>
                ) : (
                  <Text className="block font-bold text-slate-700">{stat.value}</Text>
                )}
              </div>
            ))}
          </div>

          <div className="space-y-6">
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Description</Title>
              <Text className="text-slate-600 leading-relaxed block whitespace-pre-wrap">{job?.description || 'No description provided.'}</Text>
            </div>
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Requirements</Title>
              <Text className="text-slate-600 leading-relaxed block whitespace-pre-wrap">{job?.requirements || 'No requirements specified.'}</Text>
            </div>
            <div>
              <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-3">Skills Required</Title>
              <div className="flex flex-wrap gap-2">
                {(job?.skills_required || []).map((s: string) => (
                  <Tag key={s} className="bg-blue-50 text-blue-600 border-none font-bold rounded-lg px-3 py-1 m-0">{s}</Tag>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      key: 'pipeline',
      label: `Pipeline`,
      children: (
        <div className="p-6 overflow-x-auto">
          {pipelineLoading ? <Spin /> : (
            <div className="flex gap-4 min-w-max pb-4">
              {Object.entries(pipeline).map(([stageId, stageData]: [string, any]) => (
                <div key={stageId} className="w-64 shrink-0 bg-slate-50/50 rounded-2xl p-4 border border-slate-200 shadow-soft-sm">
                  <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                    <Text className="font-bold text-slate-900 text-xs uppercase tracking-widest">{stageData?.stage?.name || 'Stage'}</Text>
                    <Badge count={stageData?.count || 0} showZero size="small" style={{ backgroundColor: '#fff', color: '#64748b', border: '1px solid #e2e8f0', boxShadow: 'none' }} />
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(stageData?.applications) && stageData.applications.map((app: any) => (
                      <div key={app.id} className="bg-white rounded-xl p-3 border border-slate-100 shadow-soft-sm">
                        <Text className="block font-bold text-slate-700 text-xs mb-1">
                          {app.candidate_name || `Candidate #${app.id?.substring(0, 5)}`}
                        </Text>
                        <div className="flex items-center justify-between">
                          <Tag className="m-0 text-[9px] uppercase font-bold border-none bg-slate-100 text-slate-500">{app.status || 'applied'}</Tag>
                          <ArrowRight className="h-3 w-3 text-slate-300" />
                        </div>
                      </div>
                    ))}
                    {(stageData?.count === 0 || !stageData?.applications?.length) && <div className="py-8 text-center text-slate-300 text-[10px] font-bold uppercase tracking-widest">No candidates</div>}
                  </div>
                </div>
              ))}
              {Object.keys(pipeline).length === 0 && <div className="py-20 text-center w-full text-slate-400">No pipeline stages defined.</div>}
            </div>
          )}
        </div>
      )
    },
    {
      key: 'applications',
      label: `Applications`,
      children: (
        <div className="p-0">
          {appsLoading ? <div className="p-10 text-center"><Spin /></div> : (
            <Table
              dataSource={applications}
              rowKey="id"
              size="small"
              pagination={false}
              className="modern-table"
              columns={[
                {
                  title: 'Candidate',
                  dataIndex: 'candidate_name',
                  render: (name, _record) => (
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-500 text-xs uppercase">
                        {name?.charAt(0) || 'C'}
                      </div>
                      <Text className="font-bold text-slate-700">{name || 'Candidate'}</Text>
                    </div>
                  )
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  render: (status) => <Tag className="m-0 uppercase font-bold text-[10px] rounded-full px-2" color="blue">{status || 'Applied'}</Tag>
                },
                {
                  title: 'Applied',
                  dataIndex: 'created_at',
                  render: (date) => <Text className="text-slate-500 text-xs">{date ? dayjs(date).format('MMM D, YYYY') : 'N/A'}</Text>
                },
                {
                  title: '',
                  key: 'actions',
                  render: (_, _record) => (
                    <div className="flex gap-2 justify-end">
                      <Button size="small" type="primary" className="text-[10px] font-bold uppercase h-7 px-3 rounded-lg bg-blue-600 border-none">Shortlist</Button>
                      <Button size="small" danger className="text-[10px] font-bold uppercase h-7 px-3 rounded-lg">Reject</Button>
                    </div>
                  )
                }
              ]}
            />
          )}
        </div>
      )
    },
    {
      key: 'interviews',
      label: `Interviews`,
      children: (
        <div className="p-0">
          <Table
            dataSource={interviews}
            rowKey="id"
            size="small"
            pagination={false}
            className="modern-table"
            columns={[
              { 
                title: 'Type', 
                dataIndex: 'interview_type',
                render: (t) => <Text className="font-bold text-slate-700 capitalize text-xs">{t?.replace('_', ' ') || 'Interview'}</Text>
              },
              { title: 'Round', dataIndex: 'interview_round', align: 'center', render: (r) => <Badge count={`R${r || 1}`} style={{ backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0', boxShadow: 'none', fontWeight: 'bold', fontSize: '10px' }} /> },
              {
                title: 'Scheduled',
                dataIndex: 'scheduled_at',
                render: (date) => <Text className="text-slate-500 text-xs">{date ? dayjs(date).format('MMM D, h:mm A') : 'TBD'}</Text>
              },
              {
                title: 'Status',
                dataIndex: 'status',
                render: (status) => <Tag color={status === 'completed' ? 'green' : 'blue'} className="m-0 uppercase font-bold text-[10px] rounded-full px-2">{status || 'scheduled'}</Tag>
              }
            ]}
          />
        </div>
      )
    }
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Detail Header */}
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div>
          <div className="flex items-center gap-3 mb-1">
             <Title level={4} className="!m-0 text-slate-900">{job?.title || 'Untitled'}</Title>
             <Tag className={cn("m-0 border-none font-bold text-[10px] uppercase rounded-full px-2", getStatusStyle(job?.status || 'draft', 'job').softClass)}>
                {formatStatusLabel(job?.status || 'draft')}
             </Tag>
          </div>
          <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
            {job?.department_id || 'Engineering'} • {job?.location_id || 'Remote'}
          </Text>
        </div>
        <div className="flex items-center gap-2">
          <Button icon={<X className="h-4 w-4" />} onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg border-slate-200" />
          <Button 
            type="primary" 
            className="h-9 font-bold px-4 rounded-lg bg-blue-600 border-none shadow-soft-sm"
            onClick={() => navigate(`/pipeline?job=${jobId}`)}
            icon={<LayoutGrid className="h-4 w-4" />}
          >
            Open Pipeline
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Quick Actions Bar */}
        <div className="px-6 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
           <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Quick Actions</Text>
           <Space>
              {job?.status === 'draft' && (
                <Button 
                  size="small" 
                  icon={<Send className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg"
                  loading={submitMutation.isPending}
                  onClick={() => submitMutation.mutate()}
                >
                  Submit for Approval
                </Button>
              )}
              {job?.status === 'pending_approval' && (
                <Button 
                  size="small" 
                  type="primary" 
                  icon={<CheckCircle className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg bg-blue-600 border-none"
                  loading={approveMutation.isPending}
                  onClick={() => approveMutation.mutate()}
                >
                  Approve Requisition
                </Button>
              )}
              {job?.status === 'approved' && (
                <Button 
                  size="small" 
                  type="primary" 
                  icon={<Globe className="h-3 w-3" />} 
                  className="text-[10px] font-bold uppercase h-7 rounded-lg bg-emerald-600 border-none"
                  loading={publishMutation.isPending}
                  onClick={() => publishMutation.mutate()}
                >
                  Publish to Active
                </Button>
              )}
              <Button size="small" icon={<Plus className="h-3 w-3" />} className="text-[10px] font-bold uppercase h-7 rounded-lg">Assign Agency</Button>
           </Space>
        </div>

        <Tabs 
          defaultActiveKey="overview" 
          items={tabItems} 
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function JobsList() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedJob, setSelectedJob] = useState<JobRequisition | null>(null)
  const [createDrawerOpen, setCreateDrawerOpen] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['jobs', statusFilter, search],
    () => requisitionsApi.list({
      status: statusFilter || undefined,
      search: search || undefined,
    })
  )

  const requisitions = (data as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6">
      {/* Top Header / Actions - Only show if no job selected or in header above list */}
      {!selectedJob && (
        <div className="p-6 pb-0 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Job Requisitions</h1>
            <p className="text-slate-500 mt-1">Manage and track all open roles across your organization.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button icon={<Download className="h-4 w-4" />} className="flex items-center gap-2 font-bold h-10 rounded-xl">Export</Button>
            <Button 
              type="primary" 
              icon={<Plus className="h-4 w-4" />} 
              className="flex items-center gap-2 font-bold h-10 rounded-xl bg-blue-600 border-none shadow-soft-md"
              onClick={() => setCreateDrawerOpen(true)}
            >
              Create Job
            </Button>
          </div>
        </div>
      )}

      {/* Filter Toolbar - Sticky below header */}
      {!selectedJob && (
        <div className="p-6 pb-4">
          <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '12px' } }}>
            <Row gutter={[12, 12]} align="middle">
              <Col xs={24} md={14}>
                <Input
                  prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                  placeholder="Search by role, location, or department..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-10 text-sm border-slate-200"
                  allowClear
                />
              </Col>
              <Col xs={12} md={6}>
                <Select
                  className="w-full h-10"
                  placeholder="Status"
                  value={statusFilter}
                  onChange={setStatusFilter}
                  allowClear
                  options={[
                    { value: 'active', label: 'Active Roles' },
                    { value: 'pending_approval', label: 'Pending Approval' },
                    { value: 'draft', label: 'Drafts' },
                    { value: 'closed', label: 'Closed' },
                  ]}
                />
              </Col>
              <Col xs={12} md={4}>
                <Button
                  icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />}
                  onClick={() => refetch()}
                  className="w-full h-10 flex items-center justify-center rounded-xl border-slate-200 font-bold"
                >
                  Refresh
                </Button>
              </Col>
            </Row>
          </Card>
        </div>
      )}

      <StandardSplitView
        isDetailOpen={!!selectedJob}
        compactListContent={
          <CompressedJobList
            jobs={requisitions}
            selectedJobId={selectedJob?.id}
            onSelect={setSelectedJob}
          />
        }
        fullListContent={
          <div className="p-6 pt-0 h-full overflow-y-auto">
            <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
              <FullJobList
                jobs={requisitions}
                onSelect={setSelectedJob}
                isLoading={isLoading}
              />
            </Card>
          </div>
        }
        detailContent={
          selectedJob ? (
            <JobDetailPanel
              job={selectedJob}
              onClose={() => setSelectedJob(null)}
            />
          ) : null
        }
      />

      {/* Create Job Drawer */}
      <Drawer
        open={createDrawerOpen}
        onClose={() => setCreateDrawerOpen(false)}
        width={640}
        title={<span className="text-lg font-bold">Create New Job Requisition</span>}
        destroyOnClose
      >
        <JobCreateForm onSuccess={() => {
          setCreateDrawerOpen(false)
          refetch()
        }} />
      </Drawer>
    </div>
  )
}
