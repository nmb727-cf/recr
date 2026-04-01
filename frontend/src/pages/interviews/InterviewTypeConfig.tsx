import { useEffect } from 'react'
import { Alert, Button, Card, Checkbox, Form, Input, Select, Space, Spin, Typography, message } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text } = Typography

export default function InterviewTypeConfig() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()

  const { data, isLoading, isError } = useApiQuery(
    ['interview_type_config', id],
    () => interviewsApi.getTypeConfig(id || ''),
    { enabled: Boolean(id) },
  )

  const payload = (data as any)?.data || {}
  const interviewType = payload?.type
  const configuration = payload?.configuration || {}

  useEffect(() => {
    if (!interviewType) return
    form.setFieldsValue({
      name: interviewType.name,
      code: interviewType.code,
      description: interviewType.description,
      execution_mode: interviewType.execution_mode,
      configurable: interviewType.configurable,
      is_active: interviewType.is_active,
      template: configuration.template,
      scorecard: configuration.scorecard,
      scheduling: configuration.scheduling,
      automation: configuration.automation,
      prequalification: configuration.prequalification,
    })
  }, [interviewType, configuration, form])

  const update = useMutation({
    mutationFn: (values: any) => interviewsApi.updateTypeConfig(id || '', values),
    onSuccess: () => {
      message.success('Interview type configuration updated')
      queryClient.invalidateQueries({ queryKey: ['interview_type_config', id] })
      queryClient.invalidateQueries({ queryKey: ['interview-types-list'] })
    },
    onError: () => {
      message.error('Failed to update configuration')
    },
  })

  if (isLoading) return <div className="p-8"><Spin /></div>
  if (isError || !interviewType) return <div className="p-8"><Alert type="error" message="Type configuration failed to load" /></div>

  return (
    <div className="space-y-4">
      <Space align="center" className="w-full justify-between">
        <div>
          <Title level={4} className="!m-0">Interview Type Configuration</Title>
          <Text type="secondary">{interviewType.name}</Text>
        </div>
        <Button onClick={() => navigate('/interviews/types')}>Back to Types</Button>
      </Space>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => update.mutate(values)}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Form.Item name="name" label="Name">
              <Input disabled />
            </Form.Item>
            <Form.Item name="code" label="Code">
              <Input disabled />
            </Form.Item>
            <Form.Item name="description" label="Description">
              <Input.TextArea rows={2} disabled />
            </Form.Item>
            <Form.Item name="execution_mode" label="Execution Mode" rules={[{ required: true }]}>
              <Select options={[
                { value: 'native', label: 'Native' },
                { value: 'third_party', label: 'Third Party' },
                { value: 'external', label: 'External' },
                { value: 'manual', label: 'Manual' },
                { value: 'async', label: 'Async' },
              ]} />
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Form.Item name="is_active" valuePropName="checked">
              <Checkbox>Enabled</Checkbox>
            </Form.Item>
            <Form.Item name="configurable" valuePropName="checked">
              <Checkbox>Configurable</Checkbox>
            </Form.Item>
          </div>

          <Title level={5}>Type Configuration</Title>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <Form.Item name="template" valuePropName="checked"><Checkbox>Template</Checkbox></Form.Item>
            <Form.Item name="scorecard" valuePropName="checked"><Checkbox>Scorecard</Checkbox></Form.Item>
            <Form.Item name="scheduling" valuePropName="checked"><Checkbox>Scheduling</Checkbox></Form.Item>
            <Form.Item name="automation" valuePropName="checked"><Checkbox>Automation</Checkbox></Form.Item>
            <Form.Item name="prequalification" valuePropName="checked"><Checkbox>Prequalification</Checkbox></Form.Item>
          </div>

          <Button type="primary" htmlType="submit" loading={update.isPending}>
            Save Configuration
          </Button>
        </Form>
      </Card>
    </div>
  )
}
