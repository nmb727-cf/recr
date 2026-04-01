import { Alert, Button, Card, Descriptions, Space, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { interviewsApi } from '@/api/interviews'

const { Title, Paragraph, Text } = Typography

export default function CandidateInterviewInstructions() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('access_token') || ''
  const q = useQuery({
    queryKey: ['candidate_interview_instructions', id],
    enabled: !!id,
    queryFn: async () => (await interviewsApi.candidateInstructions(id)).data?.data || {},
  })
  const d = q.data || {}
  const interview = d.interview || {}
  const runtime = d.runtime || {}

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Instructions</Title>
        <Tag>{interview.interview_type || '-'}</Tag>
      </div>

      <Card>
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Title">{interview.title || 'Interview'}</Descriptions.Item>
          <Descriptions.Item label="Scheduled At">{interview.scheduled_at ? dayjs(interview.scheduled_at).format('MMM D, YYYY HH:mm') : 'TBD'}</Descriptions.Item>
          <Descriptions.Item label="Status">{interview.status || '-'}</Descriptions.Item>
          <Descriptions.Item label="Single Attempt">{runtime.single_attempt ? 'Enabled' : 'Disabled'}</Descriptions.Item>
          <Descriptions.Item label="Access Window">
            <Text type="secondary">
              {runtime.not_before ? dayjs(runtime.not_before).format('MMM D, HH:mm') : '-'}
              {' '}to{' '}
              {runtime.expires_at ? dayjs(runtime.expires_at).format('MMM D, HH:mm') : '-'}
            </Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Instructions">
        <Paragraph>{d.instructions || 'Please complete all required questions and submit before closing.'}</Paragraph>
        <Alert
          type="info"
          showIcon
          message="Security Shell Enabled"
          description="Token-based, time-based and single-attempt runtime safeguards are active for this interview."
        />
        <Space className="mt-4">
          <Button onClick={() => navigate('/candidate/interviews')}>Back</Button>
          <Button type="primary" onClick={() => navigate(`/candidate/interviews/${id}/runtime?access_token=${token || runtime.token || ''}`)}>Join Interview</Button>
        </Space>
      </Card>
    </div>
  )
}
