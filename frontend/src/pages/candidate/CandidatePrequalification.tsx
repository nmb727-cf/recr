import { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  Radio,
  Space,
  Spin,
  Typography,
  message,
} from 'antd'
import { CheckCircle2, ChevronLeft, ClipboardList } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { prequalificationApi } from '@/api/prequalification'

const { Title, Text, Paragraph } = Typography

export default function CandidatePrequalification() {
  const { requisitionId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const formId = searchParams.get('form') || ''
  const navigate = useNavigate()
  const [submitting, setSaving] = useState(false)
  const [completed, setCompleted] = useState(false)

  const prequalQuery = useQuery({
    queryKey: ['candidate_prequal_form', formId],
    enabled: Boolean(formId),
    queryFn: async () => (await prequalificationApi.candidateGetForm(formId)).data?.data || {},
  })

  const form = prequalQuery.data?.form || null

  if (prequalQuery.isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Spin size="large" tip="Loading prequalification..." />
      </div>
    )
  }

  if (prequalQuery.error || (!prequalQuery.isLoading && !form)) {
    return (
      <div className="p-8">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Prequalification form not found or no longer active."
        >
          <Button onClick={() => navigate('/candidate/interviews')}>Back to Dashboard</Button>
        </Empty>
      </div>
    )
  }

  const handleSubmit = async (values: any) => {
    setSaving(true)
    try {
      const responses = Object.entries(values).map(([questionId, value]) => ({
        question_id: questionId,
        answer_text: typeof value === 'string' ? value : JSON.stringify(value),
        answer_json: typeof value === 'object' ? value : {},
      }))

      await prequalificationApi.candidateSubmitForm(form.id, responses)
      setCompleted(true)
      message.success('Prequalification submitted successfully')
    } catch (err: any) {
      message.error(err?.message || 'Failed to submit prequalification')
    } finally {
      setSaving(false)
    }
  }

  if (completed) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <CheckCircle2 size={40} />
        </div>
        <Title level={2}>Submission Received</Title>
        <Paragraph className="max-w-md text-slate-500">
          Thank you for completing the prequalification for this role. Our hiring team will review your responses and update you on the next steps soon.
        </Paragraph>
        <Button size="large" type="primary" onClick={() => navigate('/candidate/interviews')}>
          Back to Interviews
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 py-8">
      <div className="flex items-center gap-4">
        <Button icon={<ChevronLeft size={16} />} onClick={() => navigate(-1)} type="text" />
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
            <ClipboardList size={12} />
            Prequalification
          </div>
          <Title level={3} className="!m-0">
            {form.name}
          </Title>
        </div>
      </div>

      <Alert
        message="Help us understand your fit"
        description="Your responses will help our team route you to the appropriate next stage in our hiring process."
        type="info"
        showIcon
      />

      <Form layout="vertical" onFinish={handleSubmit} size="large" className="space-y-8">
        {form.sections?.map((section: any) => (
          <Card key={section.id} className="overflow-hidden rounded-3xl border-slate-200 shadow-soft-sm">
            <div className="mb-6">
              <Title level={4} className="!mb-1">
                {section.title}
              </Title>
              {section.description && <Text className="text-slate-500">{section.description}</Text>}
            </div>

            <div className="space-y-6">
              {section.questions?.map((q: any) => (
                <Form.Item
                  key={q.id}
                  name={q.id}
                  label={<span className="font-bold text-slate-700">{q.question_text}</span>}
                  rules={[{ required: q.required, message: 'This field is required' }]}
                  extra={q.help_text && <span className="text-xs text-slate-400">{q.help_text}</span>}
                >
                  {renderQuestionInput(q)}
                </Form.Item>
              ))}
            </div>
          </Card>
        ))}

        <div className="flex justify-end pt-4">
          <Button type="primary" htmlType="submit" size="large" loading={submitting} className="min-w-[160px] rounded-2xl font-bold uppercase tracking-widest">
            Submit Responses
          </Button>
        </div>
      </Form>
    </div>
  )
}

function renderQuestionInput(q: any) {
  switch (q.question_type) {
    case 'yes_no':
      return (
        <Radio.Group>
          <Space direction="vertical">
            <Radio value="yes">Yes</Radio>
            <Radio value="no">No</Radio>
          </Space>
        </Radio.Group>
      )
    case 'single_select':
    case 'dropdown':
      return (
        <Radio.Group className="w-full">
          <Space direction="vertical" className="w-full">
            {q.options_json?.map((opt: string) => (
              <Radio key={opt} value={opt} className="rounded-xl border border-slate-100 p-3 hover:bg-slate-50 w-full">
                {opt}
              </Radio>
            ))}
          </Space>
        </Radio.Group>
      )
    case 'long_text':
      return <Input.TextArea rows={4} placeholder="Your answer..." className="rounded-2xl" />
    case 'number':
      return <Input type="number" placeholder="0" className="rounded-2xl" />
    case 'date':
      return <Input type="date" className="rounded-2xl" />
    default:
      return <Input placeholder="Your answer..." className="rounded-2xl" />
  }
}
