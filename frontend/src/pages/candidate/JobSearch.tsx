import { useState } from 'react'
import {
  Input, Select, Row, Col, Card, Tag, Button, Typography, Space, Drawer,
  Divider, message, Spin, Empty, Tooltip,
} from 'antd'
import {
  SearchOutlined, EnvironmentOutlined, BankOutlined, ClockCircleOutlined,
  DollarOutlined, RocketOutlined, SendOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidateApi } from '@/api/candidate'
import { jobsPublicApi } from '@/api/jobs'
import type { JobPosting, JobRequisition, Application } from '@/types'

const { Title, Text, Paragraph } = Typography

// ─── Job Detail Drawer Content ────────────────────────────────────────────────

function JobDetailContent({
  postingId,
  isApplied,
  onApply,
}: {
  postingId: string
  isApplied: boolean
  onApply: () => void
}) {
  const { data, isLoading } = useApiQuery(
    ['job_posting', postingId],
    () => jobsPublicApi.getPosting(postingId)
  )

  const jobData = (data as { posting: JobPosting; requisition: JobRequisition } | undefined)
  const posting = jobData?.posting
  const requisition = jobData?.requisition

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
  if (!posting || !requisition) return <Empty />

  return (
    <div>
      <Title level={4} style={{ marginBottom: 4 }}>{posting.title}</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Tag icon={<EnvironmentOutlined />}>{requisition.work_mode}</Tag>
        <Tag icon={<ClockCircleOutlined />}>{requisition.job_type.replace('_', ' ')}</Tag>
        {requisition.salary_visible && (
          <Tag icon={<DollarOutlined />} color="green">
            {requisition.salary_currency} {Number(requisition.salary_min).toLocaleString()} - {Number(requisition.salary_max).toLocaleString()}
          </Tag>
        )}
      </Space>

      {isApplied ? (
        <Button
          block
          size="large"
          disabled
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          style={{ backgroundColor: '#f6ffed', borderColor: '#b7eb8f', color: '#52c41a', fontWeight: 700 }}
        >
          Already Applied
        </Button>
      ) : (
        <Button type="primary" size="large" block icon={<SendOutlined />} onClick={onApply}>
          Apply for this Position
        </Button>
      )}

      <Divider />

      <Title level={5}>Job Description</Title>
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: posting.description_html || requisition.description }}
        style={{ color: '#595959' }}
      />

      <Divider />

      <Title level={5}>Requirements</Title>
      <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{requisition.requirements}</Paragraph>

      <Title level={5}>Key Responsibilities</Title>
      <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{requisition.responsibilities}</Paragraph>

      {requisition.skills_required?.length > 0 && (
        <>
          <Title level={5}>Skills</Title>
          <Space wrap>
            {requisition.skills_required.map(s => <Tag key={s} color="blue">{s}</Tag>)}
          </Space>
        </>
      )}
    </div>
  )
}

// ─── Main JobSearch Component ─────────────────────────────────────────────────

export default function JobSearch() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [workMode, setWorkMode] = useState<string | undefined>()
  const [jobType, setJobType] = useState<string | undefined>()
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['jobs_search', search, workMode, jobType],
    () => jobsPublicApi.search({ q: search, work_mode: workMode })
  )

  const { data: appsData } = useApiQuery(
    ['candidate_applications'],
    () => candidateApi.listApplications()
  )

  const jobs = (jobsData as { jobs: JobPosting[] } | undefined)?.jobs ?? []
  const applications = ((appsData as any)?.applications ?? []) as Application[]

  // Build a set of requisition IDs the candidate has already applied to
  const appliedIds = new Set(applications.map((a: Application) => a.requisition_id).filter(Boolean))

  // Debug: verify the matching
  if (jobs.length > 0 || appliedIds.size > 0) {
    console.log('Jobs:', jobs.map(j => ({ id: j.id, req_id: j.requisition_id, title: j.title })))
    console.log('Applied req IDs:', [...appliedIds])
  }

  const handleApply = async (jobId: string) => {
    try {
      await candidateApi.applyJob(jobId)
      message.success('Application submitted successfully!')
      setSelectedJobId(null)
      // Invalidate both queries so the "Applied" badge appears immediately
      queryClient.invalidateQueries({ queryKey: ['candidate_applications'] })
      queryClient.invalidateQueries({ queryKey: ['jobs_search', search, workMode, jobType] })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      message.error(msg || 'Failed to apply')
    }
  }

  const selectedJob = jobs.find(j => j.id === selectedJobId)
  const isSelectedJobApplied = selectedJob ? appliedIds.has(selectedJob.requisition_id) : false

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <Title level={2}>Find Your Next Career Move</Title>
        <Text type="secondary">Explore opportunities across top companies and industries</Text>
      </div>

      {/* Filters */}
      <Card bordered={false} style={{ borderRadius: 16, marginBottom: 24, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={12}>
            <Input
              size="large"
              placeholder="Search jobs, skills, or companies..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={search}
              onChange={e => setSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={12} md={6}>
            <Select
              size="large"
              placeholder="Work Mode"
              style={{ width: '100%' }}
              allowClear
              onChange={setWorkMode}
              options={[
                { value: 'remote', label: 'Remote' },
                { value: 'onsite', label: 'On-site' },
                { value: 'hybrid', label: 'Hybrid' },
              ]}
            />
          </Col>
          <Col xs={12} md={6}>
            <Select
              size="large"
              placeholder="Job Type"
              style={{ width: '100%' }}
              allowClear
              onChange={setJobType}
              options={[
                { value: 'full_time', label: 'Full Time' },
                { value: 'part_time', label: 'Part Time' },
                { value: 'contract', label: 'Contract' },
                { value: 'internship', label: 'Internship' },
              ]}
            />
          </Col>
        </Row>
      </Card>

      {/* Grid */}
      <Row gutter={[24, 24]}>
        {jobsLoading ? (
          <Col span={24} style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></Col>
        ) : jobs.length > 0 ? (
          jobs.map(job => {
            const isApplied = appliedIds.has(job.requisition_id)
            return (
              <Col xs={24} sm={12} lg={8} key={job.id}>
                <div style={{ position: 'relative' }}>
                  {/* Applied badge — top right corner */}
                  {isApplied && (
                    <div style={{
                      position: 'absolute',
                      top: 12,
                      right: 12,
                      zIndex: 10,
                      background: '#52c41a',
                      color: '#fff',
                      fontSize: 11,
                      fontWeight: 700,
                      borderRadius: 20,
                      padding: '3px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      boxShadow: '0 2px 8px rgba(82,196,26,0.3)',
                    }}>
                      <CheckCircleOutlined style={{ fontSize: 11 }} /> Applied
                    </div>
                  )}
                  <Tooltip title={isApplied ? 'You applied for this position' : undefined}>
                    <Card
                      hoverable
                      style={{
                        borderRadius: 12,
                        height: '100%',
                        border: isApplied ? '1.5px solid #b7eb8f' : '1px solid #f0f0f0',
                        background: isApplied ? '#f6ffed' : '#fff',
                      }}
                      bodyStyle={{ padding: 20, display: 'flex', flexDirection: 'column', height: '100%' }}
                      onClick={() => setSelectedJobId(job.id)}
                    >
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ width: 48, height: 48, borderRadius: 8, background: isApplied ? '#d9f7be' : '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                          <RocketOutlined style={{ fontSize: 24, color: isApplied ? '#52c41a' : '#1890ff' }} />
                        </div>
                        <Title level={5} style={{ margin: 0, lineHeight: 1.4 }}>{job.title}</Title>
                        <Text type="secondary" style={{ fontSize: 13 }}><BankOutlined /> Recruitment Corp</Text>
                      </div>

                      <div style={{ marginTop: 'auto' }}>
                        <Space wrap style={{ marginBottom: 12 }}>
                          <Tag icon={<EnvironmentOutlined />} style={{ borderRadius: 4 }}>Remote</Tag>
                          <Tag color={isApplied ? 'success' : 'blue'} style={{ borderRadius: 4 }}>
                            {isApplied ? '✓ Applied' : 'Full Time'}
                          </Tag>
                        </Space>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text strong style={{ color: '#52c41a' }}>$80k - $120k</Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {job.posted_at ? dayjs(job.posted_at).fromNow() : 'Recently'}
                          </Text>
                        </div>
                      </div>
                    </Card>
                  </Tooltip>
                </div>
              </Col>
            )
          })
        ) : (
          <Col span={24}><Empty description="No jobs found matching your criteria" /></Col>
        )}
      </Row>

      {/* Detail Drawer */}
      <Drawer
        title="Job Details"
        width={640}
        onClose={() => setSelectedJobId(null)}
        open={!!selectedJobId}
        destroyOnClose
      >
        {selectedJobId && (
          <JobDetailContent
            postingId={selectedJobId}
            isApplied={isSelectedJobApplied}
            onApply={() => handleApply(selectedJobId)}
          />
        )}
      </Drawer>
    </div>
  )
}
