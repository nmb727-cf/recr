import React, { useEffect, useMemo, useState } from 'react'
import { 
  Typography, Button, Card, Tag, Space, Table, 
  Avatar, Breadcrumb, Tabs, message, Empty, Tooltip, Input, Modal,
  Spin, Select, Switch, Popconfirm, Alert
} from 'antd'
import { 
  ArrowLeftOutlined, 
  UsergroupAddOutlined, 
  SettingOutlined,
  TeamOutlined,
  FilterOutlined,
  DownloadOutlined,
  DeleteOutlined,
  MailOutlined,
  MoreOutlined,
  SearchOutlined,
  UserOutlined
} from '@ant-design/icons'
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useApiQuery } from '@/hooks/useApiQuery'
import { talentPoolsApi } from '@/api/talentPools'
import { candidatesApi } from '@/api/candidates'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { Users, LayoutGrid, List as ListIcon, Activity, Settings, ShieldAlert, History, Zap } from 'lucide-react'
import type { Candidate } from '@/types'
import type { TableColumnsType } from 'antd'

const { Title, Text, Paragraph } = Typography

function formatCandidateName(candidate: Candidate) {
  return candidate.full_name || `${candidate.first_name || ''} ${candidate.last_name || ''}`.trim() || 'Candidate'
}

function formatCandidateExperience(candidate: Candidate) {
  const value = candidate.experience_years
  if (value === null || value === undefined || value === '') return 'Experience not set'
  return `${value} years`
}

const ACTIVITY_TONE: Record<string, { badge: string; icon: string; label: string; text: string }> = {
  created: {
    badge: 'bg-emerald-50 text-emerald-700',
    icon: '●',
    label: 'Created',
    text: 'text-emerald-700',
  },
  updated: {
    badge: 'bg-blue-50 text-blue-700',
    icon: '●',
    label: 'Updated',
    text: 'text-blue-700',
  },
  added: {
    badge: 'bg-indigo-50 text-indigo-700',
    icon: '●',
    label: 'Added',
    text: 'text-indigo-700',
  },
  removed: {
    badge: 'bg-amber-50 text-amber-700',
    icon: '●',
    label: 'Removed',
    text: 'text-amber-700',
  },
  archived: {
    badge: 'bg-rose-50 text-rose-700',
    icon: '●',
    label: 'Archived',
    text: 'text-rose-700',
  },
}

function toneForEvent(eventType: string) {
  if (eventType === 'talent_pool.created') return ACTIVITY_TONE.created
  if (eventType === 'talent_pool.updated') return ACTIVITY_TONE.updated
  if (eventType === 'candidate.added_to_pool') return ACTIVITY_TONE.added
  if (eventType === 'candidate.removed_from_pool') return ACTIVITY_TONE.removed
  if (eventType === 'talent_pool.archived') return ACTIVITY_TONE.archived
  return ACTIVITY_TONE.updated
}

function describeActivity(event: any) {
  const poolName = event.payload?.pool_name || event.payload?.context_label || 'Talent Pool'
  const candidateName = event.payload?.candidate_name
  if (event.event_type === 'talent_pool.created') return `Created ${poolName}`
  if (event.event_type === 'talent_pool.updated') return `Updated ${poolName}`
  if (event.event_type === 'talent_pool.archived') return `Archived ${poolName}`
  if (event.event_type === 'candidate.added_to_pool') return `Added ${candidateName || 'candidate'} to ${poolName}`
  if (event.event_type === 'candidate.removed_from_pool') return `Removed ${candidateName || 'candidate'} from ${poolName}`
  return poolName
}

export default function TalentPoolDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('members')
  const [memberSearch, setMemberSearch] = useState('')
  const [isPickerOpen, setIsPickerOpen] = useState(false)
  const [candidateSearch, setCandidateSearch] = useState('')
  const [candidateResults, setCandidateResults] = useState<Candidate[]>([])
  const [isSearchingCandidates, setIsSearchingCandidates] = useState(false)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([])
  const [isAddingCandidates, setIsAddingCandidates] = useState(false)
  const [pickerPage, setPickerPage] = useState(1)
  const [settingsDraft, setSettingsDraft] = useState({
    name: '',
    description: '',
    color: '',
    pool_type: 'manual' as 'manual' | 'smart',
    is_active: true,
  })
  const [isSavingSettings, setIsSavingSettings] = useState(false)
  const [isDeletingPool, setIsDeletingPool] = useState(false)

  const { data: poolData, isLoading: isPoolLoading } = useApiQuery(
    ['talent-pool', id],
    () => talentPoolsApi.get(id!)
  )

  const { data: membersData, isLoading: isMembersLoading } = useApiQuery(
    ['talent-pool-members', id],
    () => talentPoolsApi.listMembers(id!)
  )

  const { data: activityData, isLoading: isActivityLoading } = useApiQuery(
    ['talent-pool-activity', id],
    () => talentPoolsApi.listActivity(id!)
  )

  const pool = poolData?.talent_pool
  const members = membersData?.memberships || []
  const activity = activityData?.activity || []
  const existingMemberIds = useMemo(
    () => new Set(members.map((member) => member.candidate)),
    [members]
  )
  const filteredMembers = useMemo(() => {
    const search = memberSearch.trim().toLowerCase()
    if (!search) return members
    return members.filter((member) => {
      const fullName = `${member.candidate_details.first_name} ${member.candidate_details.last_name}`.trim().toLowerCase()
      return (
        fullName.includes(search) ||
        (member.candidate_details.email || '').toLowerCase().includes(search) ||
        (member.candidate_details.current_title || '').toLowerCase().includes(search) ||
        (member.candidate_details.current_location_city || '').toLowerCase().includes(search)
      )
    })
  }, [memberSearch, members])
  const selectableCandidates = useMemo(
    () => candidateResults.map((candidate) => ({
      ...candidate,
      isAlreadyMember: existingMemberIds.has(candidate.id),
    })),
    [candidateResults, existingMemberIds]
  )

  useEffect(() => {
    if (!isPickerOpen) {
      setCandidateSearch('')
      setCandidateResults([])
      setSelectedCandidateIds([])
      setIsSearchingCandidates(false)
      setPickerPage(1)
      return
    }

    const timeoutId = window.setTimeout(async () => {
      setIsSearchingCandidates(true)
      try {
        const response = await candidatesApi.list({ search: candidateSearch || undefined })
        setCandidateResults(response.data.data.candidates || [])
      } catch (err) {
        console.error('[TalentPool] candidate search failed', err)
        message.error('Failed to search candidates')
      } finally {
        setIsSearchingCandidates(false)
      }
    }, 250)

    return () => window.clearTimeout(timeoutId)
  }, [candidateSearch, isPickerOpen])

  useEffect(() => {
    setPickerPage(1)
  }, [candidateSearch])

  useEffect(() => {
    if (!pool) return
    setSettingsDraft({
      name: pool.name || '',
      description: pool.description || '',
      color: pool.color || '',
      pool_type: pool.pool_type || 'manual',
      is_active: pool.is_active,
    })
  }, [pool])

  useEffect(() => {
    const tab = searchParams.get('tab')
    const action = searchParams.get('action')

    if (tab === 'settings') {
      setActiveTab('settings')
    } else if (tab === 'members') {
      setActiveTab('members')
    }

    if (action === 'add-candidates') {
      setActiveTab('members')
      setIsPickerOpen(true)
    }
  }, [searchParams])

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
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-members', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-activity', id] })
    } catch (err) {
      message.error('Failed to remove candidate')
    }
  }

  const handleToggleCandidate = (candidateId: string, checked: boolean) => {
    setSelectedCandidateIds((current) => {
      if (checked) {
        return current.includes(candidateId) ? current : [...current, candidateId]
      }
      return current.filter((id) => id !== candidateId)
    })
  }

  const candidatePickerColumns: TableColumnsType<(Candidate & { isAlreadyMember: boolean })> = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_, candidate) => (
        <div className="flex items-center gap-3">
          <Avatar size={40} icon={<UserOutlined />} className="bg-slate-100 text-slate-500" />
          <div>
            <div className="font-semibold text-slate-900">{formatCandidateName(candidate)}</div>
            <div className="text-xs text-slate-500">{candidate.email || 'No email'}</div>
          </div>
        </div>
      ),
    },
    {
      title: 'Title',
      key: 'current_title',
      render: (_, candidate) => (
        <span className="text-sm text-slate-700">{candidate.current_title || 'Title not set'}</span>
      ),
    },
    {
      title: 'Location',
      key: 'location',
      render: (_, candidate) => (
        <span className="text-sm text-slate-500">
          {[candidate.current_location_city, candidate.current_location_country].filter(Boolean).join(', ') || 'Location not set'}
        </span>
      ),
    },
    {
      title: 'Experience',
      key: 'experience_years',
      render: (_, candidate) => (
        <span className="text-sm text-slate-500">{formatCandidateExperience(candidate)}</span>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 160,
      render: (_, candidate) =>
        candidate.isAlreadyMember ? <Tag>Already in pool</Tag> : <Tag color="blue">Available</Tag>,
    },
  ]

  const handleAddCandidates = async () => {
    if (selectedCandidateIds.length === 0) {
      message.error('Select at least one candidate to add')
      return
    }

    const duplicateSelections = selectedCandidateIds.filter((candidateId) => existingMemberIds.has(candidateId))
    if (duplicateSelections.length > 0) {
      message.error('One or more selected candidates are already in this pool')
      return
    }

    setIsAddingCandidates(true)
    try {
      const response = await talentPoolsApi.bulkAdd(id!, {
        candidate_ids: selectedCandidateIds,
        source: 'manual',
      })
      message.success(response.data.message || 'Candidates added to pool')
      setIsPickerOpen(false)
      setSelectedCandidateIds([])
      setCandidateSearch('')
      setPickerPage(1)
      if (searchParams.get('action') === 'add-candidates') {
        setSearchParams((current) => {
          const next = new URLSearchParams(current)
          next.delete('action')
          return next
        }, { replace: true })
      }
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-members', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-activity', id] })
    } catch (err: any) {
      const apiMessage =
        err.response?.data?.errors?.candidate_ids?.[0] ||
        err.response?.data?.message ||
        'Failed to add candidates to pool'
      message.error(apiMessage)
    } finally {
      setIsAddingCandidates(false)
    }
  }

  const handleSaveSettings = async () => {
    if (!pool) return
    if (!settingsDraft.name.trim()) {
      message.error('Pool name is required')
      return
    }

    setIsSavingSettings(true)
    try {
      await talentPoolsApi.update(pool.id, {
        name: settingsDraft.name.trim(),
        description: settingsDraft.description.trim(),
        color: settingsDraft.color,
        pool_type: settingsDraft.pool_type,
        is_active: settingsDraft.is_active,
        filters_json: pool.filters_json,
        metadata: pool.metadata,
      })
      message.success('Pool settings updated')
      await queryClient.invalidateQueries({ queryKey: ['talent-pool', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-activity', id] })
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to update pool settings')
    } finally {
      setIsSavingSettings(false)
    }
  }

  const handleArchivePool = async () => {
    if (!pool) return
    setIsSavingSettings(true)
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
      await queryClient.invalidateQueries({ queryKey: ['talent-pool', id] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
      await queryClient.invalidateQueries({ queryKey: ['talent-pool-activity', id] })
      setSettingsDraft((current) => ({ ...current, is_active: false }))
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to archive pool')
    } finally {
      setIsSavingSettings(false)
    }
  }

  const handleDeletePool = async () => {
    if (!pool) return
    setIsDeletingPool(true)
    try {
      await talentPoolsApi.delete(pool.id)
      message.success('Pool deleted')
      await queryClient.invalidateQueries({ queryKey: ['talent-pools'] })
      navigate('/candidates/pools')
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to delete pool')
    } finally {
      setIsDeletingPool(false)
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
            <Button
              icon={<UsergroupAddOutlined />}
              size="large"
              className="rounded-xl font-semibold h-11"
              onClick={() => {
                setActiveTab('members')
                setIsPickerOpen(true)
              }}
            >
              Add Candidates
            </Button>
            <Button
              icon={<SettingOutlined />}
              size="large"
              className="rounded-xl font-semibold h-11"
              onClick={() => setActiveTab('settings')}
            >
              Pool Settings
            </Button>
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
                  value={memberSearch}
                  onChange={(e) => setMemberSearch(e.target.value)}
                />
              </div>
              <Space>
                <Button icon={<FilterOutlined />} className="rounded-lg">Filter</Button>
                <Button icon={<DownloadOutlined />} className="rounded-lg">Export</Button>
              </Space>
            </div>
            
            <Table 
              columns={columns} 
              dataSource={filteredMembers} 
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
            {isActivityLoading ? (
              <div className="flex min-h-[220px] items-center justify-center">
                <Spin />
              </div>
            ) : activity.length > 0 ? (
              <div className="space-y-3">
                {activity.map((item) => {
                  const tone = toneForEvent(item.event_type)
                  return (
                    <div key={item.id} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                      <div className="mb-1 flex items-center gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${tone.badge}`}>
                          {tone.icon} {tone.label}
                        </span>
                        <span className="text-[10px] text-slate-400">{dayjs(item.created_at).format('MMM D, h:mm A')}</span>
                      </div>
                      <p className="text-sm font-semibold text-slate-800">{item.actor_name || 'System'}</p>
                      <p className={`mt-0.5 text-sm font-medium ${tone.text}`}>{describeActivity(item)}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {(item.payload?.context_label || pool.name)} • {(item.payload?.method || item.source || 'manual').toString().replace(/_/g, ' ')} • {dayjs(item.created_at).fromNow()}
                      </p>
                    </div>
                  )
                })}
              </div>
            ) : (
              <Empty description="No activity recorded for this pool yet." className="py-16" />
            )}
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
          <div className="space-y-6">
            <Card className="rounded-3xl border-slate-100">
              <div className="mb-6">
                <Title level={4} className="!mb-1">Basic Settings</Title>
                <Text type="secondary">Keep the pool metadata accurate and minimal.</Text>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="md:col-span-2">
                  <Text className="mb-2 block font-medium text-slate-700">Pool Name</Text>
                  <Input
                    value={settingsDraft.name}
                    onChange={(e) => setSettingsDraft((current) => ({ ...current, name: e.target.value }))}
                    placeholder="Talent pool name"
                    className="h-11 rounded-xl"
                  />
                </div>

                <div className="md:col-span-2">
                  <Text className="mb-2 block font-medium text-slate-700">Description</Text>
                  <Input.TextArea
                    value={settingsDraft.description}
                    onChange={(e) => setSettingsDraft((current) => ({ ...current, description: e.target.value }))}
                    placeholder="Brief description for recruiters using this pool"
                    rows={4}
                    className="rounded-xl"
                  />
                </div>

                <div>
                  <Text className="mb-2 block font-medium text-slate-700">Color</Text>
                  <Select
                    value={settingsDraft.color || undefined}
                    onChange={(value) => setSettingsDraft((current) => ({ ...current, color: value }))}
                    placeholder="Select a color"
                    className="w-full"
                    options={[
                      { value: '#3B82F6', label: 'Blue' },
                      { value: '#10B981', label: 'Green' },
                      { value: '#F59E0B', label: 'Amber' },
                      { value: '#EF4444', label: 'Red' },
                      { value: '#8B5CF6', label: 'Purple' },
                    ]}
                  />
                </div>

                <div>
                  <Text className="mb-2 block font-medium text-slate-700">Pool Type</Text>
                  <Select
                    value={settingsDraft.pool_type}
                    onChange={(value) => setSettingsDraft((current) => ({ ...current, pool_type: value }))}
                    className="w-full"
                    options={[
                      { value: 'manual', label: 'Manual' },
                      { value: 'smart', label: 'Smart (Placeholder)' },
                    ]}
                  />
                </div>

                <div className="md:col-span-2 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <Text className="block font-medium text-slate-800">Pool Status</Text>
                    <Text type="secondary">Inactive pools are hidden from the list but remain accessible by direct link.</Text>
                  </div>
                  <Switch
                    checked={settingsDraft.is_active}
                    onChange={(checked) => setSettingsDraft((current) => ({ ...current, is_active: checked }))}
                    checkedChildren="Active"
                    unCheckedChildren="Inactive"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <Button
                  type="primary"
                  className="bg-[#1E40AF]"
                  loading={isSavingSettings}
                  onClick={handleSaveSettings}
                >
                  Save Settings
                </Button>
              </div>
            </Card>

            <Card className="rounded-3xl border-slate-100">
              <div className="mb-6">
                <Title level={4} className="!mb-1">Access & Ownership</Title>
                <Text type="secondary">Workspace ownership context for this pool.</Text>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <Text type="secondary" className="block text-xs uppercase tracking-wider">Created By</Text>
                  <Text className="mt-1 block font-medium text-slate-800">{pool.created_by || 'System'}</Text>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <Text type="secondary" className="block text-xs uppercase tracking-wider">Tenant Type</Text>
                  <Text className="mt-1 block font-medium capitalize text-slate-800">{pool.tenant_type}</Text>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <Text type="secondary" className="block text-xs uppercase tracking-wider">Tenant Ownership Context</Text>
                  <Text className="mt-1 block font-medium text-slate-800">{pool.tenant_id}</Text>
                </div>
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4">
                  <Text type="secondary" className="block text-xs uppercase tracking-wider">Visibility Scope</Text>
                  <Text className="mt-1 block font-medium text-slate-700">Tenant-wide for now</Text>
                  <Text type="secondary" className="block text-xs">Granular visibility controls can be added later.</Text>
                </div>
              </div>
            </Card>

            <Card className="rounded-3xl border-slate-100">
              <div className="mb-6">
                <Title level={4} className="!mb-1">Smart Pool Rules</Title>
                <Text type="secondary">Reserved for future rule-based automation.</Text>
              </div>
              <Alert
                type="info"
                showIcon
                message="Smart rules coming later"
                description="Manual pools work today. Rule-driven pool automation is not implemented yet."
              />
            </Card>

            <Card className="rounded-3xl border border-red-200 bg-red-50/40">
              <div className="mb-6">
                <Title level={4} className="!mb-1 text-red-700">Danger Zone</Title>
                <Text type="secondary">Use destructive actions sparingly.</Text>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-white px-4 py-4">
                  <div>
                    <Text className="block font-medium text-slate-900">Archive Pool</Text>
                    <Text type="secondary">Sets the pool inactive so it disappears from the main list without deleting data.</Text>
                  </div>
                  <Popconfirm
                    title="Archive this pool?"
                    description="You can reactivate it later from this page."
                    okText="Archive"
                    onConfirm={handleArchivePool}
                  >
                    <Button danger ghost loading={isSavingSettings} disabled={!pool.is_active}>
                      Archive Pool
                    </Button>
                  </Popconfirm>
                </div>

                <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-white px-4 py-4">
                  <div>
                    <Text className="block font-medium text-slate-900">Delete Pool</Text>
                    <Text type="secondary">
                      Permanent delete is only allowed for empty pools. Pools with members should be archived instead.
                    </Text>
                  </div>
                  <Popconfirm
                    title="Delete this pool permanently?"
                    description="This action cannot be undone."
                    okText="Delete"
                    okButtonProps={{ danger: true }}
                    onConfirm={handleDeletePool}
                    disabled={pool.member_count > 0}
                  >
                    <Button danger loading={isDeletingPool} disabled={pool.member_count > 0}>
                      Delete Pool
                    </Button>
                  </Popconfirm>
                </div>

                {pool.member_count > 0 ? (
                  <Text type="secondary" className="block text-sm">
                    Delete is disabled because this pool currently has {pool.member_count} member{pool.member_count === 1 ? '' : 's'}.
                  </Text>
                ) : null}
              </div>
            </Card>
          </div>
        )}
      </div>

      <Modal
        title={<span className="text-xl font-bold">Add Candidates to {pool.name}</span>}
        open={isPickerOpen}
        onCancel={() => setIsPickerOpen(false)}
        onOk={handleAddCandidates}
        okText={selectedCandidateIds.length > 1 ? `Add ${selectedCandidateIds.length} Candidates` : 'Add Candidate'}
        confirmLoading={isAddingCandidates}
        okButtonProps={{ disabled: selectedCandidateIds.length === 0, className: 'bg-[#1E40AF]' }}
        width={860}
        destroyOnClose
      >
        <div className="space-y-4 py-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-2 flex items-center justify-between">
              <Text className="font-semibold text-slate-800">Candidate Picker</Text>
              <Text type="secondary">
                {selectedCandidateIds.length} candidate{selectedCandidateIds.length === 1 ? '' : 's'} selected
              </Text>
            </div>
            <Input
              value={candidateSearch}
              onChange={(e) => setCandidateSearch(e.target.value)}
              prefix={<SearchOutlined className="text-slate-400" />}
              placeholder="Search candidates by name, email, or current title"
              className="h-11 rounded-xl"
            />
            <Text type="secondary" className="mt-2 block text-xs">
              Existing members are shown but disabled to prevent duplicate pool membership.
            </Text>
          </div>

          <div className="max-h-[420px] overflow-auto rounded-2xl border border-slate-200 bg-white">
            {isSearchingCandidates ? (
              <div className="flex min-h-[220px] items-center justify-center">
                <Spin />
              </div>
            ) : selectableCandidates.length > 0 ? (
              <Table
                rowKey="id"
                columns={candidatePickerColumns}
                dataSource={selectableCandidates}
                pagination={{
                  current: pickerPage,
                  pageSize: 8,
                  showSizeChanger: false,
                  onChange: (page) => setPickerPage(page),
                }}
                rowSelection={{
                  selectedRowKeys: selectedCandidateIds,
                  preserveSelectedRowKeys: true,
                  onChange: (selectedRowKeys) => setSelectedCandidateIds(selectedRowKeys.map(String)),
                  getCheckboxProps: (record) => ({
                    disabled: record.isAlreadyMember,
                  }),
                }}
                onRow={(record) => ({
                  onClick: () => {
                    if (record.isAlreadyMember) return
                    handleToggleCandidate(record.id, !selectedCandidateIds.includes(record.id))
                  },
                })}
                rowClassName={(record) => {
                  if (record.isAlreadyMember) return 'cursor-not-allowed bg-slate-50'
                  if (selectedCandidateIds.includes(record.id)) return 'bg-blue-50/70'
                  return 'cursor-pointer'
                }}
                locale={{
                  emptyText: candidateSearch ? 'No candidates match this search.' : 'No candidates available in this workspace.',
                }}
              />
            ) : (
              <Empty
                className="py-16"
                description={candidateSearch ? 'No candidates match this search.' : 'No candidates available in this workspace.'}
              />
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
