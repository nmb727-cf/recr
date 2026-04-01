import React, { useMemo, useState } from 'react'
import { 
  Typography, Button, Card, Tag, Space, Input, 
  Empty, Modal, Form, Select, message, Row, Col, Tooltip, Dropdown
} from 'antd'
import { 
  PlusOutlined, 
  SearchOutlined, 
  UsergroupAddOutlined,
  TeamOutlined,
  FilterOutlined,
  CalendarOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowRightOutlined,
  MoreOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { talentPoolsApi, TalentPool } from '@/api/talentPools'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { Users, Info, Settings, Trash2, LayoutGrid, List as ListIcon, Search } from 'lucide-react'

const { Title, Text, Paragraph } = Typography

export default function TalentPoolsList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['talent-pools', searchQuery],
    async () => {
      const response = await talentPoolsApi.list({ search: searchQuery })
      return response
    }
  )

  const pools = useMemo(() => {
    const rawPools = data?.talent_pools || []
    return [...rawPools].sort(
      (a: TalentPool, b: TalentPool) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [data])

  const handleCreate = async (values: any) => {
    try {
      setSubmitting(true)
      await talentPoolsApi.create({
        ...values,
        pool_type: 'manual',
        is_active: true
      })
      message.success('Talent pool created successfully')
      setIsCreateModalOpen(false)
      form.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
      await refetch()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to create pool')
    } finally {
      setSubmitting(false)
    }
  }

  const handleArchivePool = async (pool: TalentPool) => {
    try {
      await talentPoolsApi.update(pool.id, {
        name: pool.name,
        description: pool.description,
        color: pool.color,
        pool_type: pool.pool_type,
        is_active: false,
        filters_json: pool.filters_json,
        metadata: pool.metadata,
      })
      message.success('Pool archived')
      await queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to archive pool')
    }
  }

  const getMenuItems = (pool: TalentPool): MenuProps['items'] => [
    { key: 'open', label: 'Open Pool' },
    { key: 'edit', label: 'Edit Pool' },
    { key: 'add-candidates', label: 'Add Candidates' },
    ...(pool.is_active ? [{ key: 'archive', label: 'Archive Pool', danger: true }] : []),
  ]

  const handleMenuAction = async (pool: TalentPool, key: string) => {
    if (key === 'open') { navigate(`/candidates/pools/${pool.id}`); return }
    if (key === 'edit') { navigate(`/candidates/pools/${pool.id}?tab=settings`); return }
    if (key === 'add-candidates') { navigate(`/candidates/pools/${pool.id}?action=add-candidates`); return }
    if (key === 'archive') { await handleArchivePool(pool) }
  }

  return (
    <div className="flex flex-col h-full bg-[#F8FAFC]">
      <div className="flex-none p-6 pb-0">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-black uppercase tracking-widest text-slate-800">Available Pools</h2>
            <Text type="secondary" className="text-xs uppercase tracking-wider font-bold text-slate-400">Reusable candidate grouping system</Text>
          </div>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-[#1E40AF] h-9 px-6 rounded-xl font-bold text-xs uppercase tracking-widest border-none flex items-center shadow-soft-lg"
          >
            Create New Pool
          </Button>
        </div>

        <div className="bg-white p-3 rounded-2xl shadow-soft-sm border border-slate-100 mb-6 flex items-center gap-4">
          <Input
            placeholder="Search talent pools..."
            prefix={<Search className="w-4 h-4 text-slate-400" />}
            className="h-10 rounded-xl border-slate-200 text-sm flex-1"
            onChange={(e) => setSearchQuery(e.target.value)}
            allowClear
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6 custom-scrollbar">
        {isLoading ? (
          <Row gutter={[24, 24]}>
            {[1, 2, 3].map(i => (
              <Col xs={24} md={12} lg={8} key={i}>
                <Card loading className="rounded-2xl border-slate-100" />
              </Col>
            ))}
          </Row>
        ) : pools.length > 0 ? (
          <Row gutter={[24, 24]}>
            {pools.map((pool: TalentPool) => (
              <Col xs={24} md={12} lg={8} key={pool.id}>
                <Card 
                  hoverable
                  className="rounded-2xl border-slate-100 overflow-hidden group transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
                  bodyStyle={{ padding: 0 }}
                  onClick={() => navigate(`/candidates/pools/${pool.id}`)}
                >
                  <div className="h-3 w-full" style={{ backgroundColor: pool.color || '#E2E8F0' }} />
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <Title level={4} className="!mb-1 group-hover:text-[#1E40AF] transition-colors">{pool.name}</Title>
                        <Tag color={pool.pool_type === 'smart' ? 'purple' : 'default'} className="rounded-md font-medium border-none px-2 py-0.5">
                          {pool.pool_type === 'smart' ? 'Smart Pool' : 'Manual'}
                        </Tag>
                      </div>
                      <Dropdown
                        trigger={['click']}
                        menu={{
                          items: getMenuItems(pool),
                          onClick: async ({ key, domEvent }) => {
                            domEvent.stopPropagation()
                            await handleMenuAction(pool, String(key))
                          },
                        }}
                      >
                        <Button type="text" icon={<MoreOutlined className="text-xl text-slate-400" />} onClick={(e) => e.stopPropagation()} />
                      </Dropdown>
                    </div>
                    <Paragraph className="text-slate-500 line-clamp-2 h-10 mb-6">{pool.description || 'No description provided.'}</Paragraph>
                    <div className="flex items-center justify-between pt-6 border-t border-slate-50">
                      <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-[#1E40AF]"><Users className="w-5 h-5" /></div>
                        <div><div className="text-lg font-bold text-slate-900 leading-tight">{pool.member_count}</div><div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Members</div></div>
                      </div>
                      <div className="text-right"><div className="text-xs text-slate-400 mb-1">Last activity</div><div className="text-xs font-bold text-slate-700">{dayjs(pool.updated_at).fromNow()}</div></div>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<div className="text-slate-400"><p className="text-lg font-medium mb-1">No talent pools found</p><p>Create your first pool to start organizing candidates.</p></div>} className="py-20 bg-white rounded-3xl border border-dashed border-slate-200">
            <Button type="primary" onClick={() => setIsCreateModalOpen(true)} className="bg-[#1E40AF]">Create Pool</Button>
          </Empty>
        )}
      </div>

      <Modal title={<span className="text-xl font-bold font-['Outfit']">Create Talent Pool</span>} open={isCreateModalOpen} onCancel={() => setIsCreateModalOpen(false)} footer={null} className="rounded-2xl overflow-hidden" centered>
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-4">
          <Form.Item name="name" label={<span className="font-semibold text-slate-700">Pool Name</span>} rules={[{ required: true }]}><Input placeholder="e.g. Python Developers" className="h-11 rounded-lg" /></Form.Item>
          <Form.Item name="description" label={<span className="font-semibold text-slate-700">Description</span>}><Input.TextArea rows={3} placeholder="Brief description of this talent pool..." className="rounded-lg" /></Form.Item>
          <Form.Item name="color" label={<span className="font-semibold text-slate-700">Color Indicator</span>}>
            <Select placeholder="Select a color" className="h-11 rounded-lg">
              <Select.Option value="#3B82F6">Blue</Select.Option>
              <Select.Option value="#10B981">Green</Select.Option>
              <Select.Option value="#F59E0B">Amber</Select.Option>
              <Select.Option value="#EF4444">Red</Select.Option>
              <Select.Option value="#8B5CF6">Purple</Select.Option>
            </Select>
          </Form.Item>
          <div className="flex justify-end gap-3 mt-8">
            <Button onClick={() => setIsCreateModalOpen(false)} className="h-11 px-6 rounded-lg font-medium">Cancel</Button>
            <Button type="primary" htmlType="submit" loading={submitting} className="h-11 px-8 rounded-lg font-bold bg-[#1E40AF]">Create Pool</Button>
          </div>
        </Form>
      </Modal>
    </div>
  )
}
