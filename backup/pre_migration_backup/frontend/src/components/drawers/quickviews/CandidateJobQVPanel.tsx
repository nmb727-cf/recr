import { useState } from 'react'
import { Button, Tag, Space, Divider, Typography, Spin, Empty, message } from 'antd'
import {
  EnvironmentOutlined, ClockCircleOutlined, DollarOutlined,
  SendOutlined, CheckCircleOutlined, LoadingOutlined,
} from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidateApi } from '@/api/candidate'
import { jobsPublicApi } from '@/api/jobs'
import type { JobPosting, JobRequisition, Application } from '@/types'

const { Title, Paragraph } = Typography

export default function CandidateJobQVPanel({ job }: { job: JobPosting }) {
  const queryClient = useQueryClient()
  const [applying, setApplying] = useState(false)

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
    if (applying || isApplied) return
    setApplying(true)
    try {
      await candidateApi.applyJob(job.id)
      message.success('Application submitted! Good luck!')
      queryClient.invalidateQueries({ queryKey: ['candidate_applications'] })
      queryClient.invalidateQueries({ queryKey: ['candidate', 'applications'] })
    } catch (err: any) {
      const statusCode = err.response?.status
      const msg = err.response?.data?.message || ''
      if (statusCode === 409 || msg.toLowerCase().includes('already applied')) {
        // Treat as soft duplicate — refresh state so the "Already Applied" badge shows
        message.warning('You have already applied for this position.')
        queryClient.invalidateQueries({ queryKey: ['candidate_applications'] })
        queryClient.invalidateQueries({ queryKey: ['candidate', 'applications'] })
      } else {
        message.error(msg || 'Failed to submit application. Please try again.')
      }
    } finally {
      setApplying(false)
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
        <Button
          type="primary"
          size="large"
          block
          icon={applying ? <LoadingOutlined /> : <SendOutlined />}
          onClick={handleApply}
          disabled={applying}
          className="h-12 rounded-xl font-bold bg-blue-600 border-none"
        >
          {applying ? 'Submitting…' : 'Apply for this Position'}
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
