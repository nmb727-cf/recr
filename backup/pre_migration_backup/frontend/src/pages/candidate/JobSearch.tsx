import { useState } from 'react'
import {
  Input, Select, Row, Col, Card, Tag, Typography, Space,
  Spin, Empty, Tooltip,
} from 'antd'
import {
  SearchOutlined, EnvironmentOutlined, BankOutlined,
  DollarOutlined, RocketOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidateApi } from '@/api/candidate'
import { jobsPublicApi } from '@/api/jobs'
import type { JobPosting, Application } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const { Title, Text } = Typography

// ─── Main JobSearch Component ─────────────────────────────────────────────────

export default function JobSearch() {
  const [search, setSearch] = useState('')
  const [workMode, setWorkMode] = useState<string | undefined>()
  const [jobType, setJobType] = useState<string | undefined>()
  const openQuickView = useDrawerStore(s => s.openQuickView)

  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['jobs_search', search, workMode, jobType],
    () => jobsPublicApi.search({ search, work_mode: workMode, job_type: jobType })
  )

  const { data: appsData } = useApiQuery(
    ['candidate_applications'],
    () => candidateApi.listApplications()
  )

  const jobs = (jobsData as { jobs: JobPosting[] } | undefined)?.jobs ?? []
  const applications = ((appsData as any)?.applications ?? []) as Application[]

  // Build a set of requisition IDs the candidate has already applied to
  const appliedIds = new Set(applications.map((a: Application) => a.requisition_id).filter(Boolean))

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
            const j = job as any
            const isApplied = appliedIds.has(job.requisition_id)
            const company   = j.company_name ?? j.tenant_name ?? j.metadata?.company ?? null
            const workMode  = j.work_mode ?? j.metadata?.work_mode ?? null
            const jobType   = j.job_type ?? j.metadata?.job_type ?? null
            const salaryMin = j.salary_min ?? j.metadata?.salary_min ?? null
            const salaryMax = j.salary_max ?? j.metadata?.salary_max ?? null
            const currency  = j.salary_currency ?? j.metadata?.salary_currency ?? ''

            return (
              <Col xs={24} sm={12} lg={8} key={job.id}>
                <div style={{ position: 'relative' }}>
                  {/* Applied badge */}
                  {isApplied && (
                    <div style={{
                      position: 'absolute', top: 12, right: 12, zIndex: 10,
                      background: '#52c41a', color: '#fff', fontSize: 11, fontWeight: 700,
                      borderRadius: 20, padding: '3px 10px',
                      display: 'flex', alignItems: 'center', gap: 4,
                      boxShadow: '0 2px 8px rgba(82,196,26,0.3)',
                    }}>
                      <CheckCircleOutlined style={{ fontSize: 11 }} /> Applied
                    </div>
                  )}
                  <Tooltip title={isApplied ? 'You have already applied for this role' : 'Click to view details and apply'}>
                    <Card
                      hoverable
                      style={{
                        borderRadius: 12, height: '100%',
                        border: isApplied ? '1.5px solid #b7eb8f' : '1px solid #f0f0f0',
                        background: isApplied ? '#f6ffed' : '#fff',
                      }}
                      bodyStyle={{ padding: 20, display: 'flex', flexDirection: 'column', height: '100%' }}
                      onClick={() => openQuickView('candidate_job', job)}
                    >
                      <div style={{ marginBottom: 12 }}>
                        <div style={{
                          width: 44, height: 44, borderRadius: 8,
                          background: isApplied ? '#d9f7be' : '#f0f5ff',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10,
                        }}>
                          <RocketOutlined style={{ fontSize: 22, color: isApplied ? '#52c41a' : '#1890ff' }} />
                        </div>
                        <Title level={5} style={{ margin: 0, lineHeight: 1.4 }}>{job.title}</Title>
                        {company && (
                          <Text type="secondary" style={{ fontSize: 13 }}>
                            <BankOutlined /> {company}
                          </Text>
                        )}
                      </div>

                      <div style={{ marginTop: 'auto' }}>
                        <Space wrap style={{ marginBottom: 10 }}>
                          {workMode && (
                            <Tag icon={<EnvironmentOutlined />} style={{ borderRadius: 4 }}>
                              {workMode.replace(/_/g, ' ')}
                            </Tag>
                          )}
                          {isApplied ? (
                            <Tag color="success" style={{ borderRadius: 4 }}>✓ Applied</Tag>
                          ) : jobType ? (
                            <Tag color="blue" style={{ borderRadius: 4 }}>
                              {jobType.replace(/_/g, ' ')}
                            </Tag>
                          ) : null}
                        </Space>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          {salaryMin ? (
                            <Text strong style={{ color: '#52c41a', fontSize: 12 }}>
                              <DollarOutlined /> {currency} {Number(salaryMin).toLocaleString()}
                              {salaryMax ? ` – ${Number(salaryMax).toLocaleString()}` : '+'}
                            </Text>
                          ) : (
                            <Text type="secondary" style={{ fontSize: 12 }}>View Details →</Text>
                          )}
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
    </div>
  )
}
