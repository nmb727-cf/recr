import { useState, useEffect } from 'react'
import {
  Tabs, Card, Form, Input, Button, Row, Col, Table, Space, Tag, message,
  Typography, Avatar, Popconfirm, Spin, Modal, Select, Alert, Badge, Collapse, Descriptions, Checkbox, Drawer, Switch,
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
import { useMutation, useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { organisationApi } from '@/api/organisation'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import type { Organisation, User, Department, Location } from '@/types'
import { COUNTRIES, TIMEZONES, CURRENCIES } from '@/utils/locale'
import { readCompanySignupPrefill } from '@/utils/companyOnboarding'
import { useTranslation } from 'react-i18next'
import { rbacApi, type PermissionMeta as CatalogPermissionMeta, type RoleMeta as CatalogRoleMeta } from '@/api/rbac'

const { Title, Text } = Typography

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'red',
  tenant_admin: 'volcano',
  hr_manager: 'orange',
  hiring_manager: 'gold',
  recruiter: 'blue',
  interviewer: 'geekblue',
  viewer: 'default',
  agency_owner: 'purple',
  agency_admin: 'magenta',
  agency_recruiter: 'cyan',
  candidate: 'green',
}

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
  const { t } = useTranslation('settings')
  const queryClient = useQueryClient()
  const [roleOpen, setRoleOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<CatalogRoleMeta | null>(null)
  const [basedOnTemplateId, setBasedOnTemplateId] = useState<string | null>(null)
  const [showAllRoles, setShowAllRoles] = useState(false)
  const [selectedCodes, setSelectedCodes] = useState<string[]>([])
  const [form] = Form.useForm()

  const { data, isLoading, error } = useQuery({
    queryKey: ['rbac-role-catalog'],
    queryFn: async () => (await rbacApi.getCatalog()).data.data,
  })

  const createRoleMutation = useMutation({
    mutationFn: async (payload: { name: string; display_name: string; description?: string; permission_codes: string[] }) =>
      rbacApi.createRole(payload),
    onSuccess: () => {
      message.success(t('rbac.role_created', 'Role created'))
      queryClient.invalidateQueries({ queryKey: ['rbac-role-catalog'] })
      closeEditor()
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || t('rbac.role_create_failed', 'Failed to create role'))
    },
  })

  const updateRoleMutation = useMutation({
    mutationFn: async (payload: { roleId: string; name: string; display_name: string; description?: string; permission_codes: string[] }) =>
      rbacApi.updateRole(payload.roleId, payload),
    onSuccess: () => {
      message.success(t('rbac.role_updated', 'Role updated'))
      queryClient.invalidateQueries({ queryKey: ['rbac-role-catalog'] })
      closeEditor()
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || t('rbac.role_update_failed', 'Failed to update role'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (roleId: string) => rbacApi.deleteRole(roleId),
    onSuccess: () => {
      message.success(t('rbac.role_deleted', 'Role deleted'))
      queryClient.invalidateQueries({ queryKey: ['rbac-role-catalog'] })
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || t('rbac.role_delete_failed', 'Failed to delete role'))
    },
  })

  const humanLabel = (p: CatalogPermissionMeta) => p.label || `${(p.action || '').replace(/_/g, ' ')} ${p.resource || ''}`
  const humanModule = (p: CatalogPermissionMeta) =>
    p.module_label || p.module.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  if (isLoading) {
    return (
      <Card bordered={false} style={{ borderRadius: 12 }}>
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      </Card>
    )
  }

  if (error || !data) {
    return (
      <Card bordered={false} style={{ borderRadius: 12 }}>
        <Alert type="error" message={t('rbac.load_error', 'Failed to load RBAC metadata')} />
      </Card>
    )
  }

  const tenantType = data.current_user.tenant_type || (data.current_user.role?.startsWith('agency_') ? 'agency' : 'company')
  const isDebugAdmin = data.current_user.role === 'super_admin'
  const allowedApplicability = showAllRoles
    ? ['shared', 'company', 'agency', 'candidate']
    : [tenantType, 'shared']

  const visiblePermissions = data.all_permissions.filter((p: CatalogPermissionMeta) =>
    allowedApplicability.includes(p.tenant_type_applicability || 'shared')
  )

  const groupedPermissions = visiblePermissions.reduce<Record<string, CatalogPermissionMeta[]>>((acc, p) => {
    const key = humanModule(p)
    if (!acc[key]) acc[key] = []
    acc[key].push(p)
    return acc
  }, {})

  const permissionGroups = {
    shared: visiblePermissions.filter((p) => (p.tenant_type_applicability || 'shared') === 'shared'),
    company: visiblePermissions.filter((p) => p.tenant_type_applicability === 'company'),
    agency: visiblePermissions.filter((p) => p.tenant_type_applicability === 'agency'),
  }

  const closeEditor = () => {
    setRoleOpen(false)
    setEditingRole(null)
    setBasedOnTemplateId(null)
    setSelectedCodes([])
    form.resetFields()
  }

  const openCreateRole = () => {
    setEditingRole(null)
    setBasedOnTemplateId(null)
    setRoleOpen(true)
    form.setFieldsValue({
      name: '',
      display_name: '',
      description: '',
    })
    setSelectedCodes([])
  }

  const openEditRole = (role: CatalogRoleMeta) => {
    setEditingRole(role)
    setBasedOnTemplateId(null)
    setRoleOpen(true)
    form.setFieldsValue({
      name: role.name,
      display_name: role.display_name,
      description: role.description || '',
    })
    setSelectedCodes(role.permissions.map((p) => p.code))
  }

  const openFromTemplate = (role: CatalogRoleMeta, duplicate = false) => {
    setEditingRole(null)
    setBasedOnTemplateId(role.id)
    setRoleOpen(true)
    form.setFieldsValue({
      name: duplicate ? `${role.name}_copy` : `${role.name}_custom`,
      display_name: duplicate ? `${role.display_name} Copy` : role.display_name,
      description: role.description || '',
    })
    setSelectedCodes(role.permissions.map((p) => p.code))
  }

  const openDuplicateCustom = (role: CatalogRoleMeta) => {
    setEditingRole(null)
    setBasedOnTemplateId(role.based_on_role_id || null)
    setRoleOpen(true)
    form.setFieldsValue({
      name: `${role.name}_copy`,
      display_name: `${role.display_name} Copy`,
      description: role.description || '',
    })
    setSelectedCodes(role.permissions.map((p) => p.code))
  }

  const onSaveRole = async () => {
    const values = await form.validateFields()
    const payload = {
      name: values.name,
      display_name: values.display_name,
      description: values.description || '',
      permission_codes: selectedCodes,
      based_on_role_id: basedOnTemplateId || undefined,
    }
    if (editingRole) {
      updateRoleMutation.mutate({ roleId: editingRole.id, ...payload })
    } else {
      createRoleMutation.mutate(payload)
    }
  }

  const roleVisible = (r: CatalogRoleMeta) =>
    showAllRoles || ['shared', tenantType].includes(r.tenant_type_applicability || 'shared')

  const systemTemplateRoles = data.system_templates.filter((r: CatalogRoleMeta) =>
    roleVisible(r) && (
    r.name === 'super_admin' || r.name === 'candidate'
    )
  )
  const agencyRoles = data.system_templates.filter((r: CatalogRoleMeta) => roleVisible(r) && r.name.startsWith('agency_'))
  const companyRoles = data.system_templates.filter((r: CatalogRoleMeta) =>
    roleVisible(r) && !r.name.startsWith('agency_') && r.name !== 'super_admin' && r.name !== 'candidate'
  )
  const customRoles = data.tenant_roles.filter(roleVisible)

  const RoleSection = ({
    title,
    roles,
    systemOwned,
  }: {
    title: string
    roles: CatalogRoleMeta[]
    systemOwned?: boolean
  }) => (
    <div className="mb-6">
      <div className="mb-3 flex items-center justify-between">
        <Text strong>{title}</Text>
        <Badge count={roles.length} color={roles.length ? 'blue' : 'default'} />
      </div>
      <div className="space-y-2">
        {roles.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
            {t('rbac.no_roles_in_section', 'No roles in this section')}
          </div>
        )}
        {roles.map((role) => (
          <div
            key={role.id}
            className="rounded-xl border border-slate-200 bg-white p-4 transition-colors hover:border-blue-200"
          >
            <div className="flex items-start justify-between gap-3">
              <div
                className="min-w-0 cursor-pointer"
                onClick={() => {
                  if (!data.can_manage_roles) return
                  if (systemOwned) openFromTemplate(role)
                  else openEditRole(role)
                }}
              >
                <div className="mb-1 flex items-center gap-2">
                  <Text strong>{role.display_name || role.name}</Text>
                  <Tag className="m-0">{role.permission_count}</Tag>
                  {role.name === data.current_user.role && <Tag color="green">{t('rbac.current', 'Current')}</Tag>}
                </div>
                <Text type="secondary" className="text-xs">{role.description || '—'}</Text>
              </div>
              <Space>
                {systemOwned ? (
                  <>
                    <Button size="small" onClick={() => openFromTemplate(role)}>
                      {t('rbac.use_template', 'Use Template')}
                    </Button>
                    <Button size="small" onClick={() => openFromTemplate(role, true)}>
                      {t('rbac.duplicate', 'Duplicate')}
                    </Button>
                  </>
                ) : (
                  <>
                    <Button size="small" onClick={() => openEditRole(role)}>
                      {t('rbac.edit_role', 'Edit')}
                    </Button>
                    <Button size="small" onClick={() => openDuplicateCustom(role)}>
                      {t('rbac.duplicate', 'Duplicate')}
                    </Button>
                    <Popconfirm
                      title={t('rbac.delete_role_confirm', 'Delete this tenant role?')}
                      onConfirm={() => deleteMutation.mutate(role.id)}
                      okText={t('common:actions.delete', 'Delete')}
                      cancelText={t('common:actions.cancel', 'Cancel')}
                    >
                      <Button size="small" danger>{t('common:actions.delete', 'Delete')}</Button>
                    </Popconfirm>
                  </>
                )}
              </Space>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <Card bordered={false} style={{ borderRadius: 12 }}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <Text strong>{t('rbac.title', 'Roles & Permissions')}</Text>
          <div><Text type="secondary">{t('rbac.subtitle', 'Configure role visibility with human-friendly permission labels.')}</Text></div>
          <div className="mt-1">
            <Tag color={tenantType === 'agency' ? 'purple' : 'blue'}>
              {t('rbac.tenant_type_label', 'Tenant Type')}: {tenantType === 'agency' ? t('rbac.tenant_type_agency', 'Agency') : t('rbac.tenant_type_company', 'Company')}
            </Tag>
          </div>
        </div>
        <Space>
          {isDebugAdmin && (
            <Space>
              <Text type="secondary">{t('rbac.show_all_roles', 'Show all roles')}</Text>
              <Switch checked={showAllRoles} onChange={setShowAllRoles} />
            </Space>
          )}
          <Button type="primary" onClick={openCreateRole}>
            {t('rbac.create_custom_role', 'Create Custom Role')}
          </Button>
        </Space>
      </div>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label={t('rbac.current_user_role', 'Current User Role')}>
            <Tag color={ROLE_COLORS[data.current_user.role] ?? 'default'}>{data.current_user.role}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('rbac.current_user_email', 'Current User Email')}>
            {data.current_user.email}
          </Descriptions.Item>
          <Descriptions.Item label={t('rbac.permission_count_api', 'Permissions from API')}>
            <Badge count={data.current_user.permission_count} color="blue" />
          </Descriptions.Item>
          <Descriptions.Item label={t('rbac.permission_count_store', 'Tenant Custom Roles')}>
            <Badge count={data.tenant_roles.length} color="green" />
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <RoleSection title={t('rbac.system_templates', 'System Templates')} roles={systemTemplateRoles} systemOwned />
      <RoleSection title={t('rbac.agency_roles', 'Agency Roles')} roles={agencyRoles} systemOwned />
      <RoleSection title={t('rbac.company_roles', 'Company Roles')} roles={companyRoles} systemOwned />
      <RoleSection title={t('rbac.custom_roles', 'Custom Roles')} roles={customRoles} />

      <Drawer
        title={editingRole ? t('rbac.edit_role_modal', 'Edit Tenant Role') : t('rbac.create_role_modal', 'Create Tenant Role')}
        open={roleOpen}
        onClose={closeEditor}
        width={560}
        extra={
          <Space>
            <Button onClick={closeEditor}>{t('common:actions.cancel', 'Cancel')}</Button>
            <Button
              type="primary"
              onClick={onSaveRole}
              loading={createRoleMutation.isPending || updateRoleMutation.isPending}
            >
              {t('common:actions.save', 'Save')}
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label={t('rbac.role_key', 'Role Key')}
            rules={[{ required: true, message: t('rbac.role_key_required', 'Role key is required') }]}
          >
            <Input placeholder="e.g. recruiter_plus" />
          </Form.Item>
          <Form.Item
            name="display_name"
            label={t('rbac.role', 'Role')}
            rules={[{ required: true, message: t('rbac.role_name_required', 'Role name is required') }]}
          >
            <Input placeholder="e.g. Recruiter Plus" />
          </Form.Item>
          <Form.Item name="description" label={t('rbac.description', 'Description')}>
            <Input />
          </Form.Item>
        </Form>

        <div className="mb-2 mt-4">
          <Text strong>{t('rbac.permissions_by_module', 'Permissions by Module')}</Text>
        </div>
        <div className="mb-3 flex flex-wrap gap-2">
          <Tag>{t('rbac.permissions_shared', 'Shared')}: {permissionGroups.shared.length}</Tag>
          <Tag color="blue">{t('rbac.permissions_company_only', 'Company-only')}: {permissionGroups.company.length}</Tag>
          <Tag color="purple">{t('rbac.permissions_agency_only', 'Agency-only')}: {permissionGroups.agency.length}</Tag>
        </div>
        <Collapse
          items={Object.entries(groupedPermissions).map(([moduleName, perms]) => ({
            key: moduleName,
            label: (
              <Space>
                <Text strong>{moduleName}</Text>
                <Badge count={perms.length} />
              </Space>
            ),
            children: (
              <Checkbox.Group
                value={selectedCodes}
                onChange={(vals) => setSelectedCodes(vals as string[])}
                className="grid grid-cols-1 md:grid-cols-2 gap-2"
              >
                {perms.map((p) => (
                  <div key={p.code} className="rounded-lg border border-slate-100 p-2">
                    <Checkbox value={p.code}>
                      <span className="font-medium">{humanLabel(p)}</span>
                    </Checkbox>
                    <div className="text-xs text-slate-500">{p.description || '—'}</div>
                  </div>
                ))}
              </Checkbox.Group>
            ),
          }))}
        />
      </Drawer>

      <div className="mt-4 bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-start gap-3">
        <InfoCircleOutlined className="text-blue-500 mt-1" />
        <Text type="secondary" style={{ fontSize: 13 }}>
          {t('rbac.enforcement_note', 'Permission enforcement still uses technical codes internally. This screen only improves admin readability.')}
        </Text>
      </div>
    </Card>
  )
}

// ─── Main Settings Component ──────────────────────────────────────────────────

export default function Settings() {
  const { t } = useTranslation('settings')
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') || 'organisation'

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Title level={4} style={{ marginBottom: 24 }}>{t('page.title', 'System Settings')}</Title>

      <Tabs
        activeKey={activeTab}
        onChange={(key) => setSearchParams({ tab: key })}
        destroyInactiveTabPane={false}
        className="modern-tabs"
        items={[
          { key: 'organisation', label: <Space><BankOutlined />{t('tabs.profile', 'Profile')}</Space>, children: <OrganisationTab /> },
          { key: 'departments', label: <Space><ApartmentOutlined />{t('tabs.departments', 'Departments')}</Space>, children: <DepartmentsTab /> },
          { key: 'locations', label: <Space><EnvironmentOutlined />{t('tabs.locations', 'Locations')}</Space>, children: <LocationsTab /> },
          { key: 'users', label: <Space><UserOutlined />{t('tabs.users', 'Users')}</Space>, children: <UsersTab /> },
          { key: 'roles', label: <Space><SafetyOutlined />{t('tabs.roles', 'Roles & Permissions')}</Space>, children: <RolesTab /> },
          { key: 'account', label: <Space><LockOutlined />{t('tabs.account', 'Account & Security')}</Space>, children: <AccountTab /> },
        ]}
      />
    </div>
  )
}
