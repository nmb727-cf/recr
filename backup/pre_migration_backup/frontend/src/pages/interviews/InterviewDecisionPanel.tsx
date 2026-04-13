import { useState } from 'react'
import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Switch, Table, Tag, Typography, message } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text } = Typography

const DECISION_OPTIONS = [
  'hire', 'reject', 'hold', 'next_round', 'manual_review', 'assignment', 'panel_required', 'escalate',
].map((v) => ({ value: v, label: v }))

export default function InterviewDecisionPanel() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const [persistAuto, setPersistAuto] = useState(true)

  const { data: kitRes } = useApiQuery(['decision_panel_kit', id], () => interviewsApi.getKit(id || ''), { enabled: Boolean(id) })
  const { data: decisionRes } = useApiQuery(['decision_panel_current', id], () => interviewsApi.getDecision(id || ''), { enabled: Boolean(id) })
  const { data: historyRes } = useApiQuery(['decision_panel_history', id], () => interviewsApi.getDecisionHistory(id || ''), { enabled: Boolean(id) })

  const kit = (kitRes as any)?.data || {}
  const currentDecision = (decisionRes as any)?.data?.decision
  const history = (historyRes as any)?.data?.history || []

  const recordDecision = useMutation({
    mutationFn: (payload: any) => interviewsApi.recordDecision(id || '', payload),
    onSuccess: () => {
      message.success('Decision recorded')
      queryClient.invalidateQueries({ queryKey: ['decision_panel_current', id] })
      queryClient.invalidateQueries({ queryKey: ['decision_panel_history', id] })
      queryClient.invalidateQueries({ queryKey: ['decision_panel_kit', id] })
    },
    onError: (err: any) => message.error(err?.response?.data?.message || 'Decision save failed'),
  })

  const evaluateDecision = useMutation({
    mutationFn: (payload: any) => interviewsApi.evaluateDecision(id || '', payload),
    onSuccess: () => {
      message.success('Decision evaluated')
      queryClient.invalidateQueries({ queryKey: ['decision_panel_current', id] })
      queryClient.invalidateQueries({ queryKey: ['decision_panel_history', id] })
      queryClient.invalidateQueries({ queryKey: ['decision_panel_kit', id] })
    },
    onError: (err: any) => message.error(err?.response?.data?.message || 'Decision evaluation failed'),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Title level={4} className="!m-0">Interview Decision Panel</Title>
        <Tag color="purple">ICC-DECISION-ENGINE-01</Tag>
      </div>

      <Card size="small" title="Interview Context">
        <div className="text-sm">Candidate: <Text strong>{kit.candidate?.full_name || kit.interview?.candidate_id || '-'}</Text></div>
        <div className="text-sm">Job: <Text strong>{kit.job?.title || kit.interview?.requisition_id || '-'}</Text></div>
        <div className="text-sm">Interview Type: <Text strong>{kit.interview?.interview_type || '-'}</Text></div>
        <div className="text-sm">Panel Majority: <Text strong>{kit.panel_decision?.majority_vote || kit.panel_decision?.combined_recommendation || 'pending'}</Text></div>
        <div className="text-sm">Weighted Decision: <Text strong>{kit.panel_decision?.weighted_decision || '-'}</Text></div>
        <div className="text-sm">Average Score: <Text strong>{kit.panel_decision?.average_score ?? '-'}</Text></div>
      </Card>

      {currentDecision && (
        <Alert
          type="info"
          showIcon
          message={`Current Decision: ${currentDecision.decision}`}
          description={`Source: ${currentDecision.decision_source} | Mode: ${currentDecision.decision_mode}`}
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card size="small" title="Manual Decision / Override">
          <Form
            layout="vertical"
            onFinish={(values) =>
              recordDecision.mutate({
                decision: values.decision,
                decision_source: values.decision_source || 'manual',
                decision_mode: 'manual',
                notes: values.notes || '',
                is_override: Boolean(values.is_override),
                override_reason: values.override_reason || '',
              })
            }
          >
            <Form.Item name="decision" label="Decision" rules={[{ required: true }]}>
              <Select options={DECISION_OPTIONS} />
            </Form.Item>
            <Form.Item name="decision_source" label="Decision Source" initialValue="manual">
              <Select options={[
                { value: 'manual', label: 'manual' },
                { value: 'scorecard', label: 'scorecard' },
                { value: 'interviewer_feedback', label: 'interviewer_feedback' },
                { value: 'prequalification', label: 'prequalification' },
                { value: 'skill_matching', label: 'skill_matching' },
                { value: 'automation_rules', label: 'automation_rules' },
              ]} />
            </Form.Item>
            <Form.Item name="is_override" valuePropName="checked">
              <Switch checkedChildren="Override" unCheckedChildren="Normal" />
            </Form.Item>
            <Form.Item name="override_reason" label="Override Reason">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Form.Item name="notes" label="Notes">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={recordDecision.isPending}>Save Decision</Button>
          </Form>
        </Card>

        <Card size="small" title="Auto / Conditional Decision">
          <Form
            layout="vertical"
            onFinish={(values) =>
              evaluateDecision.mutate({
                persist: persistAuto,
                notes: values.notes || '',
                thresholds: {
                  next_round_min: values.next_round_min ?? 80,
                  reject_max: values.reject_max ?? 50,
                },
                source_inputs: {
                  score: values.score,
                  hiring_manager_override: values.hiring_manager_override || undefined,
                  prequalification: values.prequalification_score,
                  skill_matching: values.skill_match_score,
                },
              })
            }
          >
            <Form.Item name="score" label="Composite Score">
              <InputNumber min={0} max={100} className="w-full" />
            </Form.Item>
            <Form.Item name="next_round_min" label="Next Round Threshold" initialValue={80}>
              <InputNumber min={0} max={100} className="w-full" />
            </Form.Item>
            <Form.Item name="reject_max" label="Reject Threshold" initialValue={50}>
              <InputNumber min={0} max={100} className="w-full" />
            </Form.Item>
            <Form.Item name="prequalification_score" label="Prequalification Score">
              <InputNumber min={0} max={100} className="w-full" />
            </Form.Item>
            <Form.Item name="skill_match_score" label="Skill Match Score">
              <InputNumber min={0} max={100} className="w-full" />
            </Form.Item>
            <Form.Item name="hiring_manager_override" label="Hiring Manager Override">
              <Select allowClear options={DECISION_OPTIONS} />
            </Form.Item>
            <Form.Item name="notes" label="Notes">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Space className="mb-3">
              <Text>Persist Result</Text>
              <Switch checked={persistAuto} onChange={setPersistAuto} />
            </Space>
            <div>
              <Button htmlType="submit" loading={evaluateDecision.isPending}>Evaluate Decision</Button>
            </div>
          </Form>
        </Card>
      </div>

      <Card size="small" title="Decision History">
        <Table
          rowKey="id"
          size="small"
          dataSource={history}
          pagination={{ pageSize: 8 }}
          columns={[
            { title: 'When', dataIndex: 'changed_at' },
            { title: 'From', dataIndex: 'previous_decision', render: (v) => v || '-' },
            { title: 'To', dataIndex: 'new_decision', render: (v) => <Tag>{v}</Tag> },
            { title: 'Source', dataIndex: 'change_source' },
            { title: 'Override', dataIndex: 'is_override', render: (v) => (v ? 'Yes' : 'No') },
            { title: 'Reason', dataIndex: 'override_reason', render: (v) => v || '-' },
          ]}
        />
      </Card>
    </div>
  )
}
