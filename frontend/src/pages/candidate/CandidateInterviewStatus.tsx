import { Card, Descriptions, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { interviewsApi } from '@/api/interviews'

const { Title } = Typography

export default function CandidateInterviewStatus() {
  const { id = '' } = useParams()
  const q = useQuery({
    queryKey: ['candidate_interview_status', id],
    enabled: !!id,
    queryFn: async () => (await interviewsApi.candidateStatus(id)).data?.data || {},
  })
  const d = q.data || {}
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Status</Title>
        <Tag color={d.status === 'completed' ? 'green' : d.status === 'missed' ? 'red' : 'blue'}>{d.status || 'pending'}</Tag>
      </div>
      <Card>
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Interview ID">{d.interview_id || '-'}</Descriptions.Item>
          <Descriptions.Item label="Status">{d.status || '-'}</Descriptions.Item>
          <Descriptions.Item label="Decision">{d.decision?.decision || '-'}</Descriptions.Item>
          <Descriptions.Item label="Overall Score">{d.scores?.overall_score ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Human Score">{d.scores?.human_score ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="AI Score">{d.scores?.ai_score ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

