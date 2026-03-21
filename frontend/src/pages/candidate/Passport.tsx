import { useState, useEffect } from 'react'
import {
  Tabs, Card, Form, Input, Button, Row, Col, Space, message,
  Typography, Avatar, Divider, Spin, Progress, DatePicker, Select,
  Switch, InputNumber, List, Modal, Empty,
} from 'antd'
import {
  UserOutlined, LinkedinOutlined, GithubOutlined,
  GlobalOutlined, PlusOutlined, EditOutlined, DeleteOutlined,
  ShareAltOutlined, CopyOutlined, ReloadOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { passportApi } from '@/api/passport'
import type { Passport, PassportWorkExperience, PassportEducation } from '@/types'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// ─── Shared Components ────────────────────────────────────────────────────────

const ShareSection = () => {
  const [shareUrl, setShareUrl] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchLink = async () => {
    try {
      const res = await passportApi.getShareLink()
      setShareUrl(res.data.data.share_url)
    } catch (err) {
      message.error('Failed to fetch share link')
    }
  }

  const regenerate = async () => {
    setLoading(true)
    try {
      const res = await passportApi.regenerateShareLink()
      setShareUrl(res.data.data.share_url)
      message.success('Link regenerated')
    } catch (err) {
      message.error('Failed to regenerate link')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLink()
  }, [])

  return (
    <Card bordered={false} style={{ marginTop: 24, background: '#f0f5ff', borderRadius: 12 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <ShareAltOutlined />
          <Text strong>Share My Passport</Text>
        </Space>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Anyone with this link can view your professional profile.
        </Text>
        <Space.Compact style={{ width: '100%' }}>
          <Input value={shareUrl} readOnly />
          <Button
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(shareUrl)
              message.success('Link copied to clipboard')
            }}
          >
            Copy
          </Button>
          <Button icon={<ReloadOutlined />} onClick={regenerate} loading={loading}>
            Regenerate
          </Button>
        </Space.Compact>
      </Space>
    </Card>
  )
}

// ─── Tabs ───────────────────────────────────────────────────────────────────

function ProfileTab({ passport, onUpdate }: { passport: Passport; onUpdate: () => void }) {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      await passportApi.update(values)
      message.success('Profile updated')
      onUpdate()
    } catch (err) {
      message.error('Update failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Form form={form} layout="vertical" initialValues={passport} onFinish={onFinish}>
      <Row gutter={24} align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Avatar size={100} icon={<UserOutlined />} style={{ background: '#1890ff' }} />
        </Col>
        <Col flex="auto">
          <Text type="secondary">Profile Completeness</Text>
          <Progress percent={passport.completeness_score} status="active" />
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="headline" label="Headline">
            <Input placeholder="e.g. Senior Full Stack Engineer" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="current_title" label="Current Title">
            <Input />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="summary" label="Professional Summary">
        <TextArea rows={4} />
      </Form.Item>

      <Form.Item name="video_intro_url" label="Video Introduction URL (Loom, YouTube)">
        <Input prefix={<GlobalOutlined />} />
      </Form.Item>

      <Divider>Social Links</Divider>
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="linkedin_url" label="LinkedIn">
            <Input prefix={<LinkedinOutlined />} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="github_url" label="GitHub">
            <Input prefix={<GithubOutlined />} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="portfolio_url" label="Portfolio">
            <Input prefix={<GlobalOutlined />} />
          </Form.Item>
        </Col>
      </Row>

      <Button type="primary" htmlType="submit" loading={saving}>Save Profile</Button>
    </Form>
  )
}

function ExperienceTab({ passport, onUpdate }: { passport: Passport; onUpdate: () => void }) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<PassportWorkExperience | null>(null)
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const handleSave = async (values: any) => {
    setSaving(true)
    const newHistory = editingItem
      ? passport.work_history.map(h => h.id === editingItem.id ? { ...h, ...values, id: h.id } : h)
      : [...passport.work_history, { ...values, id: crypto.randomUUID() }]

    try {
      await passportApi.update({ work_history: newHistory })
      message.success('Experience updated')
      setIsModalOpen(false)
      onUpdate()
    } catch (err) {
      message.error('Update failed')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    const newHistory = passport.work_history.filter(h => h.id !== id)
    try {
      await passportApi.update({ work_history: newHistory })
      message.success('Experience deleted')
      onUpdate()
    } catch (err) {
      message.error('Delete failed')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingItem(null)
            form.resetFields()
            setIsModalOpen(true)
          }}
        >
          Add Experience
        </Button>
      </div>

      <List
        dataSource={passport.work_history}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => {
                  setEditingItem(item)
                  form.setFieldsValue({
                    ...item,
                    from_date: dayjs(item.from_date),
                    to_date: item.to_date ? dayjs(item.to_date) : null,
                  })
                  setIsModalOpen(true)
                }}
              />,
              <Popconfirm title="Delete?" onConfirm={() => handleDelete(item.id)}>
                <Button type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              title={<Text strong>{item.title} at {item.company}</Text>}
              description={
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {dayjs(item.from_date).format('MMM YYYY')} - {item.is_current ? 'Present' : dayjs(item.to_date).format('MMM YYYY')}
                  </Text>
                  <Paragraph style={{ marginTop: 8 }}>{item.description}</Paragraph>
                </div>
              }
            />
          </List.Item>
        )}
      />

      <Modal
        title={editingItem ? 'Edit Experience' : 'Add Experience'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="company" label="Company" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="title" label="Job Title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="from_date" label="From" rules={[{ required: true }]}>
                <DatePicker picker="month" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="to_date" label="To">
                <DatePicker picker="month" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="is_current" valuePropName="checked">
            <Switch checkedChildren="Current Position" unCheckedChildren="Previous" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function EducationTab({ passport, onUpdate }: { passport: Passport; onUpdate: () => void }) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<PassportEducation | null>(null)
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const handleSave = async (values: any) => {
    setSaving(true)
    const newEdu = editingItem
      ? passport.education.map(h => h.id === editingItem.id ? { ...h, ...values, id: h.id } : h)
      : [...passport.education, { ...values, id: crypto.randomUUID() }]

    try {
      await passportApi.update({ education: newEdu })
      message.success('Education updated')
      setIsModalOpen(false)
      onUpdate()
    } catch (err) {
      message.error('Update failed')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    const newEdu = passport.education.filter(h => h.id !== id)
    try {
      await passportApi.update({ education: newEdu })
      message.success('Education deleted')
      onUpdate()
    } catch (err) {
      message.error('Delete failed')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingItem(null)
            form.resetFields()
            setIsModalOpen(true)
          }}
        >
          Add Education
        </Button>
      </div>

      <List
        dataSource={passport.education}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => {
                  setEditingItem(item)
                  form.setFieldsValue(item)
                  setIsModalOpen(true)
                }}
              />,
              <Popconfirm title="Delete?" onConfirm={() => handleDelete(item.id)}>
                <Button type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              title={<Text strong>{item.degree} in {item.field}</Text>}
              description={<Text type="secondary">{item.institution}, {item.year}</Text>}
            />
          </List.Item>
        )}
      />

      <Modal
        title={editingItem ? 'Edit Education' : 'Add Education'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="institution" label="Institution" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="degree" label="Degree" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="field" label="Field of Study" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="year" label="Graduation Year" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function SkillsTab({ passport, onUpdate }: { passport: Passport; onUpdate: () => void }) {
  const [skills, setSkills] = useState(passport.skills || [])
  const [languages, setLanguages] = useState(passport.languages || [])
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await passportApi.update({ skills, languages })
      message.success('Skills & Languages updated')
      onUpdate()
    } catch (err) {
      message.error('Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <Title level={5}>Professional Skills</Title>
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Add skills (type and press Enter)"
        value={skills}
        onChange={setSkills}
      />

      <Divider />

      <Title level={5}>Languages</Title>
      <Select
        mode="tags"
        style={{ width: '100%' }}
        placeholder="Add languages"
        value={languages}
        onChange={setLanguages}
      />

      <div style={{ marginTop: 24 }}>
        <Button type="primary" onClick={save} loading={saving}>Save Changes</Button>
      </div>
    </div>
  )
}

function PreferencesTab({ passport, onUpdate }: { passport: Passport; onUpdate: () => void }) {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      await passportApi.update({
        ...values,
        availability_date: values.availability_date?.toISOString(),
      })
      message.success('Preferences updated')
      onUpdate()
    } catch (err) {
      message.error('Update failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        ...passport,
        availability_date: passport.availability_date ? dayjs(passport.availability_date) : null,
      }}
      onFinish={onFinish}
    >
      <Row gutter={24}>
        <Col span={12}>
          <Form.Item name="is_actively_looking" label="Actively Looking for Jobs" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="open_to_work" label="Open to Work" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="preferred_work_mode" label="Preferred Work Mode">
            <Select options={[
              { value: 'onsite', label: 'On-site' },
              { value: 'remote', label: 'Remote' },
              { value: 'hybrid', label: 'Hybrid' },
              { value: 'any', label: 'Any' },
            ]} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="notice_period_days" label="Notice Period (Days)">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="expected_salary_min" label="Min Expected Salary">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="expected_salary_max" label="Max Expected Salary">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="availability_date" label="Available From">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Button type="primary" htmlType="submit" loading={saving}>Save Preferences</Button>
    </Form>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

import { Popconfirm } from 'antd'

export default function PassportPage() {
  const { data, isLoading, refetch } = useApiQuery(['passport'], () => passportApi.get())
  const passport = (data as { passport: Passport } | undefined)?.passport

  if (isLoading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  if (!passport) return <Empty description="Passport not found" />

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Title level={4} style={{ marginBottom: 24 }}>Candidate Passport</Title>

      <Card bordered={false} style={{ borderRadius: 12 }}>
        <Tabs
          defaultActiveKey="profile"
          items={[
            {
              key: 'profile',
              label: 'Profile',
              children: <ProfileTab passport={passport} onUpdate={refetch} />,
            },
            {
              key: 'experience',
              label: 'Experience',
              children: <ExperienceTab passport={passport} onUpdate={refetch} />,
            },
            {
              key: 'education',
              label: 'Education',
              children: <EducationTab passport={passport} onUpdate={refetch} />,
            },
            {
              key: 'skills',
              label: 'Skills',
              children: <SkillsTab passport={passport} onUpdate={refetch} />,
            },
            {
              key: 'preferences',
              label: 'Preferences',
              children: <PreferencesTab passport={passport} onUpdate={refetch} />,
            },
          ]}
        />
        <ShareSection />
      </Card>
    </div>
  )
}
