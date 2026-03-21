import { Button, Tag, Space, Divider, Typography, Spin, Empty, message } from 'antd'
import {
  EnvironmentOutlined, ClockCircleOutlined, DollarOutlined,
  SendOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidateApi } from '@/api/candidate'
import { jobsPublicApi } from '@/api/jobs'
import type { JobPosting, JobRequisition, Application } from '@/types'

const { Title, Paragraph } = Typography

export default function CandidateJobQVPanel({ job }: { job: JobPosting }) {
  const queryClient = useQueryClient()

  const { data, isLoading } = useApiQuery(
    ['job_posting', job.id],
    () => jobsPublicApi.getPosting(job.id)
  )

  const { data: appsData } = useApiQuery(
    ['candidate_applications'],
    () => candidateApi.listApplications()
  )

  const jobData = (data as { posting: JobPosting; requisition: JobRequisition } | undefined)
  const posting = jobData?.posting
  const requisition = jobData?.requisition
  const applications = ((appsData as any)?.applications ?? []) as Application[]
  const isApplied = applications.some(a => a.requisition_id === job.requisition_id)

  const handleApply = async () => {
    try {
      await candidateApi.applyJob(job.id)
      message.success('Application submitted!')
      queryClient.invalidateQueries({ queryKey: ['candidate_applications'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to apply')
    }
  }

  if (isLoading) return <div className="py-20 text-center"><Spin /></div>
  if (!posting || !requisition) return <Empty />

  return (
    <div className="space-y-6">
      <div>
        <Title level={4} className="!mb-2">{posting.title}</Title>
        <Space wrap>
          <Tag icon={<EnvironmentOutlined />}>{requisition.work_mode}</Tag>
          <Tag icon={<ClockCircleOutlined />}>{requisition.job_type.replace('_', ' ')}</Tag>
          {requisition.salary_visible && (
            <Tag icon={<DollarOutlined />} color="green">
              {requisition.salary_currency} {Number(requisition.salary_min).toLocaleString()} – {Number(requisition.salary_max).toLocaleString()}
            </Tag>
          )}
        </Space>
      </div>

      {isApplied ? (
        <Button block size="large" disabled icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          style={{ backgroundColor: '#f6ffed', borderColor: '#b7eb8f', color: '#52c41a', fontWeight: 700 }}>
          Already Applied
        </Button>
      ) : (
        <Button type="primary" size="large" block icon={<SendOutlined />} onClick={handleApply}
          className="h-12 rounded-xl font-bold bg-blue-600 border-none">
          Apply for this Position
        </Button>
      )}

      <Divider />

      <div>
        <Title level={5}>Job Description</Title>
        <div className="prose prose-sm max-w-none text-slate-600"
          dangerouslySetInnerHTML={{ __html: posting.description_html || requisition.description || '' }} />
      </div>

      {requisition.requirements && (
        <>
          <Divider />
          <Title level={5}>Requirements</Title>
          <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{requisition.requirements}</Paragraph>
        </>
      )}

      {requisition.skills_required?.length > 0 && (
        <>
          <Divider />
          <Title level={5}>Skills Required</Title>
          <Space wrap>
            {requisition.skills_required.map(s => <Tag key={s} color="blue">{s}</Tag>)}
          </Space>
        </>
      )}
    </div>
  )
}
