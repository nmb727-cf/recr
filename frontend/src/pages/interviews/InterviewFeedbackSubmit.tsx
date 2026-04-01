import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card, Form, Input, InputNumber, Select, Spin, Typography, message } from 'antd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { interviewsApi } from '@/api/interviews'

const { Title, Text } = Typography

const RECOMMENDATION_OPTIONS = [
  { value: 'hire', label: 'Hire' },
  { value: 'reject', label: 'Reject' },
  { value: 'hold', label: 'Hold' },
  { value: 'next_round', label: 'Next Round' },
  { value: 'manual_review', label: 'Manual Review' },
  { value: 'assignment', label: 'Assignment' },
  { value: 'panel_required', label: 'Panel Required' },
  { value: 'escalate', label: 'Escalate' },
]

export default function InterviewFeedbackSubmit() {
  const { id } = useParams<{ id: string }>()
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, isError, refetch } = useApiQuery(['interview-kit', id], () => interviewsApi.getKit(id!), { enabled: !!id })
  const kit = (data as any) || {}

  const scorecardAttrs = useMemo(() => kit.scorecard?.attributes || [], [kit.scorecard])

  const onSubmit = async (values: any) => {
    if (!id) return
    setSaving(true)
    try {
      const scorecard_ratings: Record<string, any> = {}
      for (const attr of scorecardAttrs) {
        const key = `attr_${attr.id}`
        scorecard_ratings[attr.attribute_name] = values[key]
      }

      await interviewsApi.submitStructuredFeedback(id, {
        score: values.score,
        notes: values.notes || '',
        recommendation: values.recommendation,
        scorecard_ratings,
      })
      message.success('Feedback submitted')
      form.resetFields()
      refetch()
    } catch (e: any) {
      message.error(e?.response?.data?.message || 'Failed to submit feedback')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div className="p-10 text-center"><Spin /></div>
  if (isError || !kit?.interview) return <div className="p-6"><Alert type="error" message="Unable to load interview feedback form" /></div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Feedback</Title>
        <div className="flex items-center gap-2">
          <Link to="/interviews" className="text-indigo-600">Back</Link>
          <Link to={`/interviews/${id}/kit`} className="text-indigo-600 font-semibold">Open Kit</Link>
          <Link to={`/interviews/${id}/decision`} className="text-indigo-600 font-semibold">Decision Panel</Link>
        </div>
      </div>

      <Card size="small" title="Interview Context">
        <div className="text-sm">Candidate: <Text strong>{kit.candidate?.full_name || '-'}</Text></div>
        <div className="text-sm">Job: <Text strong>{kit.job?.title || '-'}</Text></div>
        <div className="text-sm">Type: <Text strong>{kit.interview?.interview_type || '-'}</Text></div>
      </Card>

      <Card size="small" title="Submit Feedback">
        <Form form={form} layout="vertical" onFinish={onSubmit}>
          {scorecardAttrs.map((attr: any) => {
            const key = `attr_${attr.id}`
            if (attr.rating_type === 'yes_no') {
              return (
                <Form.Item key={key} name={key} label={`${attr.attribute_name} (Yes/No)`} rules={attr.required ? [{ required: true }] : []}>
                  <Select options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} />
                </Form.Item>
              )
            }
            if (attr.rating_type === 'pass_fail') {
              return (
                <Form.Item key={key} name={key} label={`${attr.attribute_name} (Pass/Fail)`} rules={attr.required ? [{ required: true }] : []}>
                  <Select options={[{ value: 'pass', label: 'Pass' }, { value: 'fail', label: 'Fail' }]} />
                </Form.Item>
              )
            }
            if (attr.rating_type === 'custom_scale') {
              const opts = (attr.custom_scale || []).map((v: string) => ({ value: v, label: v }))
              return (
                <Form.Item key={key} name={key} label={`${attr.attribute_name} (Custom)`} rules={attr.required ? [{ required: true }] : []}>
                  <Select options={opts} />
                </Form.Item>
              )
            }
            return (
              <Form.Item key={key} name={key} label={`${attr.attribute_name} (1-5)`} rules={attr.required ? [{ required: true }] : []}>
                <InputNumber min={1} max={5} className="w-full" />
              </Form.Item>
            )
          })}

          <Form.Item name="score" label="Overall Numeric Score (optional)">
            <InputNumber min={0} max={100} className="w-full" />
          </Form.Item>

          <Form.Item name="recommendation" label="Recommendation" rules={[{ required: true }]}> 
            <Select options={RECOMMENDATION_OPTIONS} />
          </Form.Item>

          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={4} placeholder="Interview notes" />
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={saving}>Submit Feedback</Button>
        </Form>
      </Card>

      <Card size="small" title="Panel Decision">
        <div className="text-sm">Combined Recommendation: <Text strong>{kit.panel_decision?.combined_recommendation || 'pending'}</Text></div>
        <div className="text-sm">Average Score: <Text strong>{kit.panel_decision?.average_score ?? '-'}</Text></div>
      </Card>
    </div>
  )
}
