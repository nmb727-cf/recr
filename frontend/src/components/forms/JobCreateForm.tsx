import { Form, Input, Button, Row, Col, Select, InputNumber, message } from 'antd'
import { requisitionsApi } from '@/api/jobs'
import { useState } from 'react'

export default function JobCreateForm({ onSuccess }: { onSuccess: () => void }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await requisitionsApi.create(values)
      message.success('Job created successfully')
      onSuccess()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        job_type: 'full_time',
        work_mode: 'hybrid',
        priority: 'medium',
        headcount: 1,
        salary_currency: 'USD'
      }}
    >
      <Form.Item name="title" label="Job Title" rules={[{ required: true }]}>
        <Input placeholder="e.g. Senior Software Engineer" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="job_type" label="Job Type" rules={[{ required: true }]}>
            <Select options={[
              { value: 'full_time', label: 'Full Time' },
              { value: 'part_time', label: 'Part Time' },
              { value: 'contract', label: 'Contract' },
              { value: 'internship', label: 'Internship' },
            ]} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="work_mode" label="Work Mode" rules={[{ required: true }]}>
            <Select options={[
              { value: 'remote', label: 'Remote' },
              { value: 'onsite', label: 'On-site' },
              { value: 'hybrid', label: 'Hybrid' },
            ]} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="priority" label="Priority">
            <Select options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="headcount" label="Headcount">
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="salary_currency" label="Currency">
            <Input placeholder="USD" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="salary_min" label="Min Salary">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="salary_max" label="Max Salary">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="description" label="Description">
        <Input.TextArea rows={4} placeholder="Describe the role..." />
      </Form.Item>

      <Form.Item name="requirements" label="Requirements">
        <Input.TextArea rows={4} placeholder="List requirements..." />
      </Form.Item>

      <Form.Item name="skills_required" label="Skills (comma separated)">
        <Select mode="tags" placeholder="e.g. React, Python" />
      </Form.Item>

      <div className="flex justify-end gap-3 mt-6">
        <Button onClick={() => form.resetFields()}>Reset</Button>
        <Button type="primary" htmlType="submit" loading={loading}>
          Create Job Requisition
        </Button>
      </div>
    </Form>
  )
}
