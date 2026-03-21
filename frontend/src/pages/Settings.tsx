import { useState, useEffect } from 'react'
import {
  Tabs, Card, Form, Input, Button, Row, Col, Table, Space, Tag, message,
  Typography, Avatar, Popconfirm, Spin,
} from 'antd'
import {
  UserOutlined, TeamOutlined, BankOutlined, LockOutlined,
  SaveOutlined, PlusOutlined, DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useApiQuery } from '@/hooks/useApiQuery'
import { organisationApi } from '@/api/organisation'
import { authApi } from '@/api/auth'
import type { Organisation, User } from '@/types'

const { Title, Text } = Typography

// ─── Organisation Tab ────────────────────────────────────────────────────────

function OrganisationTab() {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const { data, isLoading } = useApiQuery(['org_profile'], () => organisationApi.getProfile())
  const org = (data as { organisation: Organisation } | undefined)?.organisation

  useEffect(() => {
    if (org) form.setFieldsValue(org)
  }, [org, form])

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      await organisationApi.updateProfile(values)
      message.success('Organisation profile updated')
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 600 }}>
        <Form.Item name="name" label="Organisation Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="website" label="Website">
          <Input placeholder="https://example.com" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="industry" label="Industry">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="size" label="Company Size">
              <Input placeholder="e.g. 50-100" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="description" label="Company Description">
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
            Save Changes
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

// ─── Users Tab ───────────────────────────────────────────────────────────────

function UsersTab() {
  const { data, isLoading } = useApiQuery(['org_users'], () => organisationApi.listUsers())
  const users = (data as { users: User[] } | undefined)?.users ?? []

  const columns: ColumnsType<User> = [
    {
      title: 'Member',
      key: 'user',
      render: (_, r) => (
        <Space>
          <Avatar icon={<UserOutlined />} src={r.avatar_url} />
          <Space direction="vertical" size={0}>
            <Text strong>{r.full_name}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>{r.email}</Text>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role) => <Tag style={{ textTransform: 'capitalize' }}>{role.replace('_', ' ')}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (active) => <Tag color={active ? 'green' : 'red'}>{active ? 'ACTIVE' : 'INACTIVE'}</Tag>,
    },
    {
      title: '',
      key: 'actions',
      render: () => (
        <Popconfirm title="Remove user from team?" okText="Remove" okButtonProps={{ danger: true }}>
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />}>Invite Member</Button>
      </div>
      <Table columns={columns} dataSource={users} rowKey="id" loading={isLoading} size="middle" />
    </Card>
  )
}

// ─── Account Tab ──────────────────────────────────────────────────────────────

function AccountTab() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await authApi.changePassword(values.old_password, values.new_password)
      message.success('Password changed successfully')
      form.resetFields()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card bordered={false} style={{ borderRadius: 12 }} title="Change Password">
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 400 }}>
        <Form.Item name="old_password" label="Current Password" rules={[{ required: true }]}>
          <Input.Password />
        </Form.Item>
        <Form.Item name="new_password" label="New Password" rules={[{ required: true, min: 8 }]}>
          <Input.Password />
        </Form.Item>
        <Form.Item
          name="confirm_password"
          label="Confirm New Password"
          dependencies={['new_password']}
          rules={[
            { required: true },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) return Promise.resolve()
                return Promise.reject(new Error('Passwords do not match'))
              },
            }),
          ]}
        >
          <Input.Password />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<LockOutlined />} loading={loading}>
            Update Password
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

// ─── Main Settings Component ──────────────────────────────────────────────────

export default function Settings() {
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>System Settings</Title>

      <Tabs
        defaultActiveKey="organisation"
        items={[
          { key: 'organisation', label: <Space><BankOutlined />Organisation</Space>, children: <OrganisationTab /> },
          { key: 'users', label: <Space><TeamOutlined />Team Members</Space>, children: <UsersTab /> },
          { key: 'account', label: <Space><LockOutlined />Account & Security</Space>, children: <AccountTab /> },
        ]}
      />
    </div>
  )
}
