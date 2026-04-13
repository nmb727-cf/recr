import { useParams, Link } from 'react-router-dom'
import { Alert, Card, List, Spin, Tag, Typography } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { interviewsApi } from '@/api/interviews'

const { Title, Text, Paragraph } = Typography

export default function InterviewKit() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useApiQuery(['interview-kit', id], () => interviewsApi.getKit(id!), { enabled: !!id })
  const kit = (data as any) || {}

  if (isLoading) return <div className="p-10 text-center"><Spin /></div>
  if (isError || !kit?.interview) return <div className="p-6"><Alert type="error" message="Interview kit failed to load" /></div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Kit</Title>
        <div className="flex items-center gap-2">
          <Link to="/interviews" className="text-indigo-600">Back</Link>
          <Link to={`/interviews/${id}/feedback`} className="text-indigo-600 font-semibold">Submit Feedback</Link>
          <Link to={`/interviews/${id}/decision`} className="text-indigo-600 font-semibold">Decision Panel</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Candidate" size="small">
          <Paragraph className="!mb-1"><Text strong>{kit.candidate?.full_name || '-'}</Text></Paragraph>
          <Paragraph className="!mb-1 text-xs">{kit.candidate?.email || '-'}</Paragraph>
          <Paragraph className="!mb-1 text-xs">{kit.candidate?.current_title || '-'}</Paragraph>
          {kit.resume_url ? <a href={kit.resume_url} target="_blank" rel="noreferrer">Open Resume</a> : <Text type="secondary">Resume not available</Text>}
        </Card>

        <Card title="Job" size="small">
          <Paragraph className="!mb-1"><Text strong>{kit.job?.title || '-'}</Text></Paragraph>
          {kit.job?.job_ref_id ? <Tag>{kit.job.job_ref_id}</Tag> : null}
          <Paragraph className="!mt-2 !mb-0 text-xs whitespace-pre-wrap">{kit.job?.description || 'No description.'}</Paragraph>
        </Card>
      </div>

      <Card title="Instructions" size="small">
        <Paragraph className="!mb-0 whitespace-pre-wrap">{kit.instructions || 'No instructions set.'}</Paragraph>
      </Card>

      <Card title="Questions" size="small">
        <List
          dataSource={kit.questions || []}
          renderItem={(q: any, idx: number) => (
            <List.Item>
              <div>
                <Text strong>{idx + 1}. {q.question_text}</Text>
                <div className="text-xs text-slate-500">Type: {q.question_type}</div>
              </div>
            </List.Item>
          )}
        />
      </Card>

      <Card title="Scorecard" size="small">
        {kit.scorecard ? (
          <div className="space-y-2">
            <div>
              <Text strong>{kit.scorecard.name}</Text>
              <div className="text-xs text-slate-500">{kit.scorecard.description || 'No description'}</div>
            </div>
            <List
              dataSource={kit.scorecard.attributes || []}
              renderItem={(a: any) => (
                <List.Item>
                  <div className="flex w-full justify-between gap-2">
                    <Text>{a.attribute_name}</Text>
                    <div className="text-xs text-slate-500">{a.rating_type} · w={a.weight}{a.required ? ' · required' : ''}</div>
                  </div>
                </List.Item>
              )}
            />
          </div>
        ) : (
          <Text type="secondary">No scorecard mapped</Text>
        )}
      </Card>

      <Card title="Panel Summary" size="small">
        <div className="text-sm">Combined Recommendation: <Text strong>{kit.panel_decision?.combined_recommendation || 'pending'}</Text></div>
        <div className="text-sm">Average Score: <Text strong>{kit.panel_decision?.average_score ?? '-'}</Text></div>
      </Card>
    </div>
  )
}
