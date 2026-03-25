import React, { useState } from 'react'
import { 
  Typography, Button, Card, Tag, Space, Table, 
  Avatar, Breadcrumb, Tabs, message, Empty, Tooltip 
} from 'antd'
import { 
  ArrowLeftOutlined, 
  UsergroupAddOutlined, 
  SettingOutlined,
  FilterOutlined,
  DownloadOutlined,
  DeleteOutlined,
  MailOutlined,
  MoreOutlined,
  UserOutlined
} from '@ant-design/icons'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { talentPoolsApi } from '@/api/talentPools'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { Users, LayoutGrid, List as ListIcon, Activity, Settings, ShieldAlert, History } from 'lucide-react'

const { Title, Text, Paragraph } = Typography

export default function TalentPoolDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('members')

  const { data: poolData, isLoading: isPoolLoading } = useApiQuery(
    ['talent-pool', id],
    () => talentPoolsApi.get(id!)
  )

  const { data: membersData, isLoading: isMembersLoading } = useApiQuery(
    ['talent-pool-members', id],
    () => talentPoolsApi.listMembers(id!)
  )

  const pool = poolData?.data?.talent_pool
  const members = membersData?.data?.memberships || []

  if (isPoolLoading) return <div className="p-8">Loading pool details...</div>
  if (!pool) return <div className="p-8">Pool not found.</div>

  const columns = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_: any, record: any) => (
        <div className="flex items-center gap-3">
          <Avatar size={40} icon={<UserOutlined />} className="bg-slate-100 text-slate-400" />
          <div>
            <div className="font-bold text-slate-900 leading-tight">
              {record.candidate_details.first_name} {record.candidate_details.last_name}
            </div>
            <div className="text-xs text-slate-500">{record.candidate_details.email}</div>
          </div>
        </div>
      )
    },
    {
      title: 'Current Role',
      dataIndex: ['candidate_details', 'current_title'],
      key: 'title',
      render: (text: string) => <Text className="font-medium">{text || '—'}</Text>
    },
    {
      title: 'Location',
      dataIndex: ['candidate_details', 'current_location_city'],
      key: 'location',
      render: (text: string) => <span className="text-slate-500">{text || '—'}</span>
    },
    {
      title: 'Exp.',
      dataIndex: ['candidate_details', 'experience_years'],
      key: 'experience',
      render: (val: number) => <Tag className="rounded-md border-slate-200">{val || 0} Years</Tag>
    },
    {
      title: 'Added',
      dataIndex: 'added_at',
      key: 'added_at',
      render: (date: string) => (
        <div>
          <div className="text-slate-700 text-sm">{dayjs(date).format('MMM D, YYYY')}</div>
          <div className="text-[10px] text-slate-400 uppercase font-bold tracking-tighter">
            {dayjs(date).fromNow()}
          </div>
        </div>
      )
    },
    {
      title: '',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="View Candidate">
            <Button 
              type="text" 
              icon={<ArrowLeftOutlined rotate={135} className="text-slate-400" />} 
              onClick={() => navigate(`/candidates?id=${record.candidate}`)}
            />
          </Tooltip>
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => handleRemoveMember(record.candidate)}
          />
        </Space>
      )
    }
  ]

  const handleRemoveMember = async (candidateId: string) => {
    try {
      await talentPoolsApi.bulkRemove(id!, { candidate_ids: [candidateId] })
      message.success('Candidate removed from pool')
      queryClient.invalidateQueries({ queryKey: ['talent-pool-members', id] })
      queryClient.invalidateQueries({ queryKey: ['talent-pool', id] })
    } catch (err) {
      message.error('Failed to remove candidate')
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white px-8 pt-8 border-b border-slate-100">
        <Breadcrumb className="mb-4">
          <Breadcrumb.Item><Link to="/candidates/pools">Talent Pools</Link></Breadcrumb.Item>
          <Breadcrumb.Item>{pool.name}</Breadcrumb.Item>
        </Breadcrumb>
        
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-4">
            <div 
              className="w-4 h-12 rounded-full" 
              style={{ backgroundColor: pool.color || '#E2E8F0' }} 
            />
            <div>
              <Title level={2} className="!mb-1 font-['Outfit'] font-bold">{pool.name}</Title>
              <div className="flex items-center gap-3">
                <Tag color={pool.pool_type === 'smart' ? 'purple' : 'default'} className="rounded-md border-none font-medium px-2 py-0.5 uppercase text-[10px] tracking-wider">
                  {pool.pool_type === 'smart' ? 'Smart Pool' : 'Manual'}
                </Tag>
                <Text type="secondary" className="flex items-center gap-1.5 text-sm">
                  <Users className="w-4 h-4" /> <b>{pool.member_count}</b> Members
                </Text>
              </div>
            </div>
          </div>
          
          <Space size="middle">
            <Button icon={<UsergroupAddOutlined />} size="large" className="rounded-xl font-semibold h-11">Add Candidates</Button>
            <Button icon={<SettingOutlined />} size="large" className="rounded-xl font-semibold h-11">Pool Settings</Button>
          </Space>
        </div>

        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          className="talent-pool-tabs"
          items={[
            { key: 'members', label: <span className="flex items-center gap-2"><TeamOutlined /> Members</span> },
            { key: 'activity', label: <span className="flex items-center gap-2"><History className="w-4 h-4" /> Activity</span> },
            { key: 'rules', label: <span className="flex items-center gap-2"><Zap className="w-4 h-4" /> Smart Rules</span>, disabled: pool.pool_type !== 'smart' },
            { key: 'settings', label: <span className="flex items-center gap-2"><Settings className="w-4 h-4" /> Settings</span> },
          ]}
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8 bg-[#f8fafc]">
        {activeTab === 'members' && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="p-4 border-b border-slate-50 flex justify-between items-center">
              <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-xl border border-slate-100">
                <Input 
                  prefix={<SearchOutlined className="text-slate-400" />} 
                  placeholder="Search members..." 
                  bordered={false}
                  className="w-64"
                />
              </div>
              <Space>
                <Button icon={<FilterOutlined />} className="rounded-lg">Filter</Button>
                <Button icon={<DownloadOutlined />} className="rounded-lg">Export</Button>
              </Space>
            </div>
            
            <Table 
              columns={columns} 
              dataSource={members} 
              rowKey="id"
              loading={isMembersLoading}
              pagination={{ pageSize: 20 }}
              locale={{
                emptyText: <Empty description="No members in this pool yet." className="py-20" />
              }}
            />
          </div>
        )}

        {activeTab === 'activity' && (
          <Card className="rounded-3xl border-slate-100">
            <Empty description="Activity history placeholder." />
          </Card>
        )}

        {activeTab === 'rules' && (
          <Card className="rounded-3xl border-slate-100">
            <div className="text-center py-12">
              <Zap className="w-12 h-12 text-purple-200 mx-auto mb-4" />
              <Title level={4}>Smart Pool Rules</Title>
              <Text type="secondary" className="block mb-6">Automation rules are coming soon for enterprise tier.</Text>
              <Button type="primary" disabled>Configure Rules</Button>
            </div>
          </Card>
        )}

        {activeTab === 'settings' && (
          <Card className="rounded-3xl border-slate-100">
            <Empty description="Pool settings placeholder." />
          </Card>
        )}
      </div>
    </div>
  )
}
