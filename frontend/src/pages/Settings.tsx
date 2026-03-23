import { useState, useEffect } from 'react'
import {
  Tabs, Card, Form, Input, Button, Row, Col, Table, Space, Tag, message,
  Typography, Avatar, Popconfirm, Spin, Modal, Select,
} from 'antd'
import {
  UserOutlined, BankOutlined, LockOutlined,
  SaveOutlined, PlusOutlined, DeleteOutlined, EnvironmentOutlined,
  ApartmentOutlined, GlobalOutlined, ClockCircleOutlined, DollarOutlined,
  SafetyOutlined, InfoCircleOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { organisationApi } from '@/api/organisation'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import type { Organisation, User, Department, Location } from '@/types'
import { COUNTRIES, TIMEZONES, CURRENCIES } from '@/utils/locale'
import { readCompanySignupPrefill } from '@/utils/companyOnboarding'

const { Title, Text } = Typography

// ─── Organisation Tab ────────────────────────────────────────────────────────

function OrganisationTab() {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(['org_profile'], () => organisationApi.getProfile())
  const org = (data as any)?.organisation as Organisation

  useEffect(() => {
    if (org) {
      const signupPrefill = readCompanySignupPrefill()
      const initialValues = {
        ...org,
        name: org.name === 'My Organisation' || org.name?.toLowerCase().includes('new company')
          ? (signupPrefill?.company_name || org.name)
          : org.name
      }
      form.setFieldsValue(initialValues)
    }
  }, [org, form])

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      await organisationApi.updateProfile(values)
      message.success('Organisation profile updated')
      setIsEditing(false)
      await refetch()
    } catch (err: any) {
      console.error('[OrganisationTab] updateProfile error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && form) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>

  if (!isEditing && org) {
    return (
      <Card
        bordered={false}
        style={{ borderRadius: 12 }}
        extra={<Button onClick={() => setIsEditing(true)}>Edit Profile</Button>}
      >
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Organisation Name</Text>
              <Text className="text-lg font-bold text-slate-800">{org.name}</Text>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Website</Text>
              <Text className="text-sm font-medium text-blue-600 block truncate">
                {org.website ? <a href={org.website} target="_blank" rel="noreferrer">{org.website}</a> : 'Not set'}
              </Text>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Country</Text>
              <Text className="text-sm font-semibold text-slate-700">
                {COUNTRIES.find(c => c.code === (org as any).country_code)?.name || (org as any).country_code || 'Not set'}
              </Text>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Timezone</Text>
              <Text className="text-sm font-semibold text-slate-700">{(org as any).timezone || 'Not set'}</Text>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Default Currency</Text>
              <Text className="text-sm font-semibold text-slate-700">
                {(org as any).settings?.default_currency || 'INR'}
              </Text>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Industry</Text>
              <Tag className="m-0 bg-slate-100 border-none font-bold text-[10px] uppercase text-slate-600 rounded-md">
                {org.industry || 'Not set'}
              </Tag>
            </div>
            <div>
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Company Size</Text>
              <Text className="text-sm font-semibold text-slate-700">{(org as any).size_range || 'Not set'}</Text>
            </div>
          </div>

          <div>
            <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Description</Text>
            <Text className="text-sm text-slate-600 leading-relaxed block bg-slate-50/50 p-4 rounded-xl border border-slate-100 italic">
              {org.description || 'No description provided.'}
            </Text>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card
      bordered={false}
      style={{ borderRadius: 12 }}
      extra={<Button type="text" onClick={() => setIsEditing(false)}>Cancel</Button>}
    >
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 800 }}>
        <Row gutter={24}>
          <Col span={12}>
            <Form.Item name="name" label="Organisation Name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="website" label="Website">
              <Input placeholder="https://example.com" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={24}>
          <Col span={8}>
            <Form.Item name="country_code" label="Base Country" rules={[{ required: true }]}>
              <Select 
                showSearch
                optionFilterProp="label"
                suffixIcon={<GlobalOutlined />}
                options={COUNTRIES.map(c => ({ value: c.code, label: c.name }))} 
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="timezone" label="Default Timezone" rules={[{ required: true }]}>
              <Select 
                showSearch
                optionFilterProp="label"
                suffixIcon={<ClockCircleOutlined />}
                options={TIMEZONES} 
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item 
              name={['settings', 'default_currency']} 
              label="Default Currency"
              initialValue="INR"
            >
              <Select 
                showSearch
                optionFilterProp="label"
                suffixIcon={<DollarOutlined />}
                options={CURRENCIES.map(c => ({ value: c.code, label: `${c.code} (${c.symbol})` }))} 
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={24}>
          <Col span={12}>
            <Form.Item name="industry" label="Industry">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="size_range" label="Company Size">
              <Select options={[
                { value: '1-10', label: '1-10 employees' },
                { value: '11-50', label: '11-50 employees' },
                { value: '51-200', label: '51-200 employees' },
                { value: '201-500', label: '201-500 employees' },
                { value: '500+', label: '500+ employees' },
              ]} />
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

// ─── Departments Tab ─────────────────────────────────────────────────────────

function DepartmentsTab() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<Department | null>(null)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const { data, isLoading, refetch } = useApiQuery(['org_departments'], () => organisationApi.listDepartments())
  const departments = (data as any)?.departments ?? []

  useEffect(() => {
    if (open && editingRecord) {
      form.setFieldsValue(editingRecord)
    } else if (open && !editingRecord) {
      form.resetFields()
    }
  }, [open, editingRecord, form])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      if (editingRecord) {
        await organisationApi.updateDepartment(editingRecord.id, values)
        message.success('Department updated')
      } else {
        await organisationApi.createDepartment(values)
        message.success('Department created')
      }
      setOpen(false)
      setEditingRecord(null)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['org_departments'] })
      refetch()
    } catch (err: any) {
      console.error('[DepartmentsTab] saveDepartment error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && form) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await organisationApi.deleteDepartment(id)
      queryClient.invalidateQueries({ queryKey: ['org_departments'] })
      message.success('Deleted successfully')
    } catch (err: any) {
      console.error('[DepartmentsTab] delete error:', err)
      message.error(err.response?.data?.message || 'Failed to delete')
    }
  }

  const handleEdit = (record: Department) => {
    setEditingRecord(record)
    setOpen(true)
  }

  const handleCancel = () => {
    setOpen(false)
    setEditingRecord(null)
    form.resetFields()
  }

  const columns: ColumnsType<Department> = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (t) => <Text strong>{t}</Text> },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (a) => <Tag color={a ? 'green' : 'default'}>{a ? 'ACTIVE' : 'INACTIVE'}</Tag>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<ApartmentOutlined style={{ color: '#1890ff' }} />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="Delete this item?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
            cancelText="Cancel"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingRecord(null); setOpen(true); }}>Add Department</Button>
      </div>
      <Table columns={columns} dataSource={departments} rowKey="id" loading={isLoading} size="middle" />
      <Modal
        title={editingRecord ? "Edit Department" : "Add Department"}
        open={open}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={onFinish}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              form.submit()
            }
          }}
        >
          <Form.Item name="name" label="Department Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="Department Code" rules={[{ required: true }]}>
            <Input placeholder="e.g. ENG, HR, MKT" />
          </Form.Item>
          {editingRecord && (
            <Form.Item name="is_active" valuePropName="checked" label="Status">
              <Select options={[
                { value: true, label: 'Active' },
                { value: false, label: 'Inactive' },
              ]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  )
}

// ─── Locations Tab ───────────────────────────────────────────────────────────

function LocationsTab() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<Location | null>(null)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const { data, isLoading, refetch } = useApiQuery(['org_locations'], () => organisationApi.listLocations())
  const locations = (data as any)?.locations ?? []

  useEffect(() => {
    if (open && editingRecord) {
      form.setFieldsValue(editingRecord)
    } else if (open && !editingRecord) {
      form.resetFields()
    }
  }, [open, editingRecord, form])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      if (editingRecord) {
        await organisationApi.updateLocation(editingRecord.id, values)
        message.success('Location updated')
      } else {
        await organisationApi.createLocation(values)
        message.success('Location created')
      }
      setOpen(false)
      setEditingRecord(null)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['org_locations'] })
      refetch()
    } catch (err: any) {
      console.error('[LocationsTab] saveLocation error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && form) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await organisationApi.deleteLocation(id)
      queryClient.invalidateQueries({ queryKey: ['org_locations'] })
      message.success('Deleted successfully')
    } catch (err: any) {
      console.error('[LocationsTab] delete error:', err)
      message.error(err.response?.data?.message || 'Failed to delete')
    }
  }

  const handleEdit = (record: Location) => {
    setEditingRecord(record)
    setOpen(true)
  }

  const handleCancel = () => {
    setOpen(false)
    setEditingRecord(null)
    form.resetFields()
  }

  const columns: ColumnsType<Location> = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (t) => <Text strong>{t}</Text> },
    { title: 'City', dataIndex: 'city', key: 'city' },
    { title: 'Country', dataIndex: 'country', key: 'country' },
    {
      title: 'Work Mode',
      key: 'mode',
      render: (_, r) => (
        <Space>
          {r.is_remote && <Tag color="blue">Remote Friendly</Tag>}
          {r.is_active ? <Tag color="green">Active</Tag> : <Tag>Inactive</Tag>}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<EnvironmentOutlined style={{ color: '#1890ff' }} />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="Delete this item?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
            cancelText="Cancel"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingRecord(null); setOpen(true); }}>Add Location</Button>
      </div>
      <Table columns={columns} dataSource={locations} rowKey="id" loading={isLoading} size="middle" />
      <Modal
        title={editingRecord ? "Edit Location" : "Add Location"}
        open={open}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={onFinish}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              form.submit()
            }
          }}
        >
          <Form.Item name="name" label="Location Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. HQ Office, Mumbai Branch" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="city" label="City" rules={[{ required: true }]}>
                <Input placeholder="Mumbai" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="country" label="Country" rules={[{ required: true }]}>
                <Select 
                  showSearch
                  optionFilterProp="label"
                  options={COUNTRIES.map(c => ({ value: c.name, label: c.name }))} 
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="is_remote" label="Location Type" rules={[{ required: true }]} initialValue={false}>
            <Select options={[
              { value: false, label: 'Physical Office' },
              { value: true, label: 'Remote / Virtual' },
            ]} />
          </Form.Item>
          {editingRecord && (
            <Form.Item name="is_active" valuePropName="checked" label="Status">
              <Select options={[
                { value: true, label: 'Active' },
                { value: false, label: 'Inactive' },
              ]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  )
}

// ─── Users Tab ───────────────────────────────────────────────────────────────

function UsersTab() {
  const queryClient = useQueryClient()
  const [inviteOpen, setInviteOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<User | null>(null)
  
  const [inviteForm] = Form.useForm()
  const [editForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  
  const { data, isLoading, refetch } = useApiQuery(['org_users'], () => organisationApi.listUsers())
  const users = (data as any)?.users ?? []
  const currentUser = useAuthStore(state => state.user)

  useEffect(() => {
    if (editOpen && editingRecord) {
      editForm.setFieldsValue(editingRecord)
    }
  }, [editOpen, editingRecord, editForm])

  const onInviteFinish = async (values: any) => {
    setLoading(true)
    try {
      await organisationApi.inviteUser(values)
      message.success('Invitation sent to ' + values.email)
      setInviteOpen(false)
      inviteForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['org_users'] })
      refetch()
    } catch (err: any) {
      console.error('[UsersTab] inviteUser error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && inviteForm) {
        inviteForm.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const onEditFinish = async (values: any) => {
    if (!editingRecord) return
    setLoading(true)
    try {
      await organisationApi.updateUser(editingRecord.id, values)
      message.success('User updated')
      setEditOpen(false)
      setEditingRecord(null)
      editForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['org_users'] })
      refetch()
    } catch (err: any) {
      console.error('[UsersTab] updateUser error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && editForm) {
        editForm.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteUser = async (id: string) => {
    try {
      await organisationApi.deleteUser(id)
      queryClient.invalidateQueries({ queryKey: ['org_users'] })
      message.success('Deleted successfully')
    } catch (err: any) {
      console.error('[UsersTab] delete error:', err)
      message.error(err.response?.data?.message || 'Failed to delete')
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: 'Member',
      key: 'user',
      render: (_, r) => (
        <Space>
          <Avatar icon={<UserOutlined />} src={r.avatar_url} />
          <Space direction="vertical" size={0}>
            <Text strong>{r.full_name || 'New Member'}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>{r.email}</Text>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag style={{ textTransform: 'capitalize' }}>
          {role?.replace('_', ' ') || 'Recruiter'}
        </Tag>
      ),
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
      render: (_, r) => (
        <Space>
          <Button 
            type="text" 
            icon={<UserOutlined style={{ color: '#1890ff' }} />} 
            onClick={() => { setEditingRecord(r); setEditOpen(true); }} 
          />
          <Popconfirm 
            title="Delete this item?"
            description="This action cannot be undone."
            onConfirm={() => handleDeleteUser(r.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
            cancelText="Cancel"
            disabled={r.id === currentUser?.id || r.role === 'tenant_admin'}
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />} 
              disabled={r.id === currentUser?.id || r.role === 'tenant_admin'}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setInviteOpen(true)}>Invite Member</Button>
      </div>
      <Table columns={columns} dataSource={users} rowKey="id" loading={isLoading} size="middle" />
      
      {/* Invite Modal */}
      <Modal
        title="Invite Team Member"
        open={inviteOpen}
        onCancel={() => setInviteOpen(false)}
        onOk={() => inviteForm.submit()}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form 
          form={inviteForm} 
          layout="vertical" 
          onFinish={onInviteFinish}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              inviteForm.submit()
            }
          }}
        >
          <Form.Item name="email" label="Email Address" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="colleague@company.com" />
          </Form.Item>
          <Form.Item name="role" label="System Role" initialValue="recruiter" rules={[{ required: true }]}>
            <Select options={[
              { value: 'hr_manager', label: 'HR Manager' },
              { value: 'recruiter', label: 'Recruiter' },
              { value: 'hiring_manager', label: 'Hiring Manager' },
              { value: 'interviewer', label: 'Interviewer' },
              { value: 'viewer', label: 'Viewer' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="Edit User"
        open={editOpen}
        onCancel={() => { setEditOpen(false); setEditingRecord(null); }}
        onOk={() => editForm.submit()}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form 
          form={editForm} 
          layout="vertical" 
          onFinish={onEditFinish}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              editForm.submit()
            }
          }}
        >
          <Form.Item name="role" label="System Role" rules={[{ required: true }]}>
            <Select 
              disabled={editingRecord?.role === 'tenant_admin'}
              options={[
                { value: 'tenant_admin', label: 'Tenant Admin', disabled: true },
                { value: 'hr_manager', label: 'HR Manager' },
                { value: 'recruiter', label: 'Recruiter' },
                { value: 'hiring_manager', label: 'Hiring Manager' },
                { value: 'interviewer', label: 'Interviewer' },
                { value: 'viewer', label: 'Viewer' },
              ]} 
            />
          </Form.Item>
          <Form.Item name="is_active" valuePropName="checked" label="Status">
            <Select options={[
              { value: true, label: 'Active' },
              { value: false, label: 'Inactive' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

// ─── Account Tab ──────────────────────────────────────────────────────────────

function AccountTab() {
  const [form] = Form.useForm()
  const [securityForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const user = useAuthStore(state => state.user)
  const fetchMe = useAuthStore(state => state.fetchMe)

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        timezone: user.timezone,
        language: user.language
      })
    }
  }, [user, form])

  const onPrefFinish = async (values: any) => {
    setLoading(true)
    try {
      await authApi.updateMe({
        timezone: values.timezone,
        language: values.language
      })
      await fetchMe()
      message.success('Localisation preferences updated')
    } catch (err: any) {
      console.error('[AccountTab] updatePreferences error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && form) {
        form.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const onSecurityFinish = async (values: any) => {
    setLoading(true)
    try {
      await authApi.changePassword(values.old_password, values.new_password)
      message.success('Password updated successfully')
      securityForm.resetFields()
    } catch (err: any) {
      console.error('[AccountTab] changePassword error:', err)
      const errData = err.response?.data
      const fieldErrors = errData?.errors
      if (fieldErrors && securityForm) {
        securityForm.setFields(
          Object.entries(fieldErrors).map(([field, msgs]) => ({
            name: field,
            errors: Array.isArray(msgs) ? msgs : [msgs as string],
          }))
        )
      }
      message.error(errData?.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 24, flexDirection: 'column' }}>
      <Card bordered={false} style={{ borderRadius: 12 }} title="Localisation Preferences">
        <Form form={form} layout="vertical" onFinish={onPrefFinish} style={{ maxWidth: 400 }}>
          <Form.Item name="timezone" label="My Timezone" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={TIMEZONES} />
          </Form.Item>
          <Form.Item name="language" label="Preferred Language" rules={[{ required: true }]}>
            <Select options={[
              { value: 'en', label: 'English' },
              { value: 'hi', label: 'Hindi' },
              { value: 'mr', label: 'Marathi' },
            ]} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Save Preferences
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card bordered={false} style={{ borderRadius: 12 }} title="Security">
        <Form form={securityForm} layout="vertical" onFinish={onSecurityFinish} style={{ maxWidth: 400 }}>
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
    </div>
  )
}

// ─── Roles Tab ───────────────────────────────────────────────────────────────

function RolesTab() {
  const roles = [
    { key: '1', role: 'Tenant Admin', level: 1, description: 'Full access to all settings and data', count: 0 },
    { key: '2', role: 'HR Manager', level: 2, description: 'Manage jobs, candidates, pipeline, agencies', count: 0 },
    { key: '3', role: 'Recruiter', level: 3, description: 'Manage assigned jobs and candidates', count: 0 },
    { key: '4', role: 'Hiring Manager', level: 4, description: 'View pipeline, give interview feedback', count: 0 },
    { key: '5', role: 'Interviewer', level: 5, description: 'Conduct interviews, submit scorecards', count: 0 },
    { key: '6', role: 'Viewer', level: 6, description: 'Read-only access to reports and pipeline', count: 0 },
  ]

  const columns = [
    { title: 'Role Name', dataIndex: 'role', key: 'role', render: (t: string) => <Text strong>{t}</Text> },
    { title: 'Level', dataIndex: 'level', key: 'level', render: (l: number) => <Tag color="blue">Level {l}</Tag> },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    { title: 'User Count', dataIndex: 'count', key: 'count' },
  ]

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-6 flex items-start gap-3">
        <InfoCircleOutlined className="text-blue-500 mt-1" />
        <Text type="secondary" style={{ fontSize: 13 }}>
          Role permissions configuration coming soon. 
          Contact your admin to change a user's role.
        </Text>
      </div>
      <Table columns={columns} dataSource={roles} pagination={false} size="middle" />
    </Card>
  )
}

// ─── Main Settings Component ──────────────────────────────────────────────────

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') || 'organisation'

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Title level={4} style={{ marginBottom: 24 }}>System Settings</Title>

      <Tabs
        activeKey={activeTab}
        onChange={(key) => setSearchParams({ tab: key })}
        destroyInactiveTabPane={false}
        className="modern-tabs"
        items={[
          { key: 'organisation', label: <Space><BankOutlined />Profile</Space>, children: <OrganisationTab /> },
          { key: 'departments', label: <Space><ApartmentOutlined />Departments</Space>, children: <DepartmentsTab /> },
          { key: 'locations', label: <Space><EnvironmentOutlined />Locations</Space>, children: <LocationsTab /> },
          { key: 'users', label: <Space><UserOutlined />Users</Space>, children: <UsersTab /> },
          { key: 'roles', label: <Space><SafetyOutlined />Roles</Space>, children: <RolesTab /> },
          { key: 'account', label: <Space><LockOutlined />Account & Security</Space>, children: <AccountTab /> },
        ]}
      />
    </div>
  )
}
