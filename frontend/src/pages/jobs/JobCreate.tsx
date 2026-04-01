import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form, Input, Select, InputNumber, Button, Card,
  Row, Col, Typography, Space, Divider, message,
} from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { requisitionsApi } from '@/api/jobs'
import type { JobRequisition } from '@/types'

const { Title, Text } = Typography
const { TextArea } = Input

const JOB_TYPE_OPTIONS = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'freelance', label: 'Freelance' },
]

const WORK_MODE_OPTIONS = [
  { value: 'onsite', label: 'On-site' },
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
]

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
]

const CURRENCY_OPTIONS = [
  { value: 'INR', label: 'INR ₹' },
  { value: 'USD', label: 'USD $' },
  { value: 'GBP', label: 'GBP £' },
  { value: 'EUR', label: 'EUR €' },
  { value: 'SGD', label: 'SGD S$' },
  { value: 'AED', label: 'AED د.إ' },
]

type FormValues = Partial<JobRequisition>

export default function JobCreate() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isLoading, setIsLoading] = useState(false)
  const [form] = Form.useForm<FormValues>()

  const handleSubmit = async (values: FormValues) => {
    setIsLoading(true)
    try {
      await requisitionsApi.create(values)
      message.success('Job created successfully')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      navigate('/jobs')
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: { message?: string } } })?.response?.data
      message.error(errData?.message ?? 'Failed to create job')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <Row align="middle" gutter={12} style={{ marginBottom: 24 }}>
        <Col>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/jobs')}
          />
        </Col>
        <Col>
          <Title level={4} style={{ margin: 0 }}>Create Job Requisition</Title>
          <Text type="secondary">Fill in the details to open a new position</Text>
        </Col>
      </Row>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        requiredMark={false}
        initialValues={{
          job_type: 'full_time',
          work_mode: 'hybrid',
          priority: 'medium',
          salary_currency: 'INR',
          headcount: 1,
          experience_min: 0,
          experience_max: 3,
        }}
      >
        {/* ── Basic Info ─────────────────────────────────────────────────── */}
        <Card
          title="Basic Information"
          bordered={false}
          style={{ borderRadius: 12, marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={24} md={16}>
              <Form.Item
                name="title"
                label="Job Title"
                rules={[{ required: true, message: 'Job title is required' }]}
              >
                <Input placeholder="e.g. Senior Backend Engineer" size="large" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="headcount"
                label="Headcount"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} size="large" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={8}>
              <Form.Item name="job_type" label="Job Type" rules={[{ required: true }]}>
                <Select options={JOB_TYPE_OPTIONS} size="large" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="work_mode" label="Work Mode" rules={[{ required: true }]}>
                <Select options={WORK_MODE_OPTIONS} size="large" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
                <Select options={PRIORITY_OPTIONS} size="large" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ── Experience & Salary ────────────────────────────────────────── */}
        <Card
          title="Experience & Compensation"
          bordered={false}
          style={{ borderRadius: 12, marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={12} md={6}>
              <Form.Item name="experience_min" label="Min Experience (yrs)">
                <InputNumber min={0} max={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="experience_max" label="Max Experience (yrs)">
                <InputNumber min={0} max={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item name="salary_currency" label="Currency">
                <Select options={CURRENCY_OPTIONS} />
              </Form.Item>
            </Col>
            <Col xs={12} md={4}>
              <Form.Item
                name="salary_min"
                label="Min Salary"
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(v) => (v?.replace(/,/g, '') ?? '') as unknown as 0}
                  min={0}
                />
              </Form.Item>
            </Col>
            <Col xs={12} md={4}>
              <Form.Item
                name="salary_max"
                label="Max Salary"
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(v) => (v?.replace(/,/g, '') ?? '') as unknown as 0}
                  min={0}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ── Skills & Description ───────────────────────────────────────── */}
        <Card
          title="Role Details"
          bordered={false}
          style={{ borderRadius: 12, marginBottom: 16 }}
        >
          <Form.Item name="skills_required" label="Skills Required">
            <Select
              mode="tags"
              size="large"
              placeholder="Type a skill and press Enter…"
              tokenSeparators={[',']}
              options={[
                { value: 'Python' },
                { value: 'JavaScript' },
                { value: 'TypeScript' },
                { value: 'React' },
                { value: 'Node.js' },
                { value: 'Django' },
                { value: 'PostgreSQL' },
                { value: 'Docker' },
                { value: 'Kubernetes' },
                { value: 'AWS' },
                { value: 'Go' },
                { value: 'Java' },
                { value: 'Rust' },
              ]}
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="Job Description"
          >
            <TextArea
              rows={6}
              placeholder="Describe the role, team and company…"
              showCount
              maxLength={5000}
            />
          </Form.Item>

          <Form.Item name="requirements" label="Requirements">
            <TextArea
              rows={4}
              placeholder="List the qualifications and requirements…"
              showCount
              maxLength={3000}
            />
          </Form.Item>

          <Form.Item name="responsibilities" label="Responsibilities">
            <TextArea
              rows={4}
              placeholder="List the key responsibilities…"
              showCount
              maxLength={3000}
            />
          </Form.Item>
        </Card>

        {/* ── Footer ────────────────────────────────────────────────────── */}
        <Divider />
        <Row justify="end">
          <Space>
            <Button size="large" onClick={() => navigate('/jobs')}>
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={isLoading}
            >
              Create Job
            </Button>
          </Space>
        </Row>
      </Form>
    </div>
  )
}
