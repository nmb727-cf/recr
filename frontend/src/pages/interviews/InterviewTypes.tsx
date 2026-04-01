import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Table, Button, Input, Tag,
  Typography, Row, Col, Card, Avatar, Spin, Modal, message, Form
} from 'antd'
import {
  Search,
  Plus, LayoutGrid, List, Target, Calendar, Settings2, Cpu, ClipboardList, UserCheck, Video, Pencil, GitBranch, Users, BarChart2, Wand2, Monitor, Layers, Building2
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useTranslation } from 'react-i18next'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { interviewsApi } from '@/api/interviews'
import { cn } from '@/utils/cn'
import { formatStatusLabel } from '@/utils/status'
import InterviewAIEngine from '@/pages/interviews/InterviewAIEngine'
import InterviewTechnicalEngine from '@/pages/interviews/InterviewTechnicalEngine'
import InterviewHumanEngine from '@/pages/interviews/InterviewHumanEngine'
import InterviewAssessmentEngine from '@/pages/interviews/InterviewAssessmentEngine'
import InterviewAssessmentCenterEngine from '@/pages/interviews/InterviewAssessmentCenterEngine'
import InterviewBarRaiserEngine from '@/pages/interviews/InterviewBarRaiserEngine'
import InterviewCampusHiringEngine from '@/pages/interviews/InterviewCampusHiringEngine'
import InterviewGroupDiscussionEngine from '@/pages/interviews/InterviewGroupDiscussionEngine'
import InterviewMockEngine from '@/pages/interviews/InterviewMockEngine'
import InterviewPortfolioReviewEngine from '@/pages/interviews/InterviewPortfolioReviewEngine'
import InterviewPresentationEngine from '@/pages/interviews/InterviewPresentationEngine'
import InterviewPrequalificationEngine from '@/pages/interviews/InterviewPrequalificationEngine'
import InterviewRolePlayEngine from '@/pages/interviews/InterviewRolePlayEngine'
import InterviewScreeningEngine from '@/pages/interviews/InterviewScreeningEngine'
import InterviewSequentialRoundEngine from '@/pages/interviews/InterviewSequentialRoundEngine'
import InterviewVideoEngine from '@/pages/interviews/InterviewVideoEngine'
import InterviewWalkinDriveEngine from '@/pages/interviews/InterviewWalkinDriveEngine'
import InterviewWhiteboardEngine from '@/pages/interviews/InterviewWhiteboardEngine'

const { Title, Text } = Typography

export default function InterviewTypes() {
  const { t } = useTranslation(['interviews', 'common'])
  const navigate = useNavigate()
  const location = useLocation()
  const [search, setSearch] = useState('')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const queryClient = useQueryClient()
  const isAiInterviewsRoute = ['/interviews/types/ai-interviews', '/interviews/ai'].includes(location.pathname)
  const isTechnicalInterviewsRoute = ['/interviews/types/technical-interviews', '/interviews/technical'].includes(location.pathname)
  const isHumanInterviewsRoute = ['/interviews/types/human-interviews', '/interviews/human'].includes(location.pathname)
  const isScreeningInterviewsRoute = ['/interviews/types/screening-interviews', '/interviews/screening'].includes(location.pathname)
  const isSequentialRoundRoute = ['/interviews/types/sequential-round', '/interviews/sequential-round'].includes(location.pathname)
  const isGroupDiscussionRoute = ['/interviews/types/group-discussion', '/interviews/group-discussion'].includes(location.pathname)
  const isBarRaiserRoute = ['/interviews/types/bar-raiser', '/interviews/bar-raiser'].includes(location.pathname)
  const isRolePlayRoute = ['/interviews/types/role-play', '/interviews/role-play'].includes(location.pathname)
  const isPresentationRoute = ['/interviews/types/presentation-interview', '/interviews/presentation-interview'].includes(location.pathname)
  const isPortfolioReviewRoute = ['/interviews/types/portfolio-review', '/interviews/portfolio-review'].includes(location.pathname)
  const isAssessmentCenterRoute = ['/interviews/types/assessment-center', '/interviews/assessment-center'].includes(location.pathname)
  const isCampusHiringRoute = ['/interviews/types/campus-hiring', '/interviews/campus-hiring'].includes(location.pathname)
  const isMockInterviewRoute = ['/interviews/types/mock-interview', '/interviews/mock-interview'].includes(location.pathname)
  const isWalkinDriveRoute = ['/interviews/types/walkin-drive', '/interviews/walkin-drive'].includes(location.pathname)
  const isVideoInterviewsRoute = ['/interviews/types/video-interviews', '/interviews/video'].includes(location.pathname)
  const isWhiteboardInterviewsRoute = ['/interviews/types/whiteboard-interview', '/interviews/whiteboard'].includes(location.pathname)
  const isAssessmentsRoute = ['/interviews/types/assessments', '/interviews/assessments'].includes(location.pathname)
  const isPrequalificationRoute = ['/interviews/types/prequalification', '/interviews/prequalification'].includes(location.pathname)
  const isRegistryHome = !isAiInterviewsRoute && !isTechnicalInterviewsRoute && !isHumanInterviewsRoute && !isScreeningInterviewsRoute && !isSequentialRoundRoute && !isGroupDiscussionRoute && !isBarRaiserRoute && !isRolePlayRoute && !isPresentationRoute && !isPortfolioReviewRoute && !isAssessmentCenterRoute && !isCampusHiringRoute && !isMockInterviewRoute && !isWalkinDriveRoute && !isVideoInterviewsRoute && !isWhiteboardInterviewsRoute && !isAssessmentsRoute && !isPrequalificationRoute

  const { data, isLoading, refetch } = useApiQuery(
    ['interview-types-list'],
    () => interviewsApi.listTypes()
  )
  const types = (data as any)?.types ?? []

  const filteredTypes = types.filter((t: any) => 
    t.name.toLowerCase().includes(search.toLowerCase()) || 
    t.code.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async (values: any) => {
    setSubmitting(true)
    try {
      await interviewsApi.createType(values)
      message.success('Interview type created')
      queryClient.invalidateQueries({ queryKey: ['interview-types-list'] })
      setCreateModalOpen(false)
      form.resetFields()
    } catch {
      message.error('Failed to create interview type')
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggle = async (record: any, isActive: boolean) => {
    try {
      await interviewsApi.updateType(record.id, { is_active: isActive })
      message.success(`Interview type ${isActive ? 'enabled' : 'disabled'}`)
      queryClient.invalidateQueries({ queryKey: ['interview-types-list'] })
    } catch {
      message.error('Failed to update type status')
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Type Name',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
            <Target size={16} />
          </div>
          <Text className="font-bold text-slate-900">{name}</Text>
        </div>
      ),
    },
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      render: (code) => <Tag className="font-mono text-[10px] uppercase border-slate-200 bg-slate-50 text-slate-500">{code}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (active, record) => (
        <div className="flex items-center gap-2">
          <Tag color={active ? 'success' : 'default'} className="m-0 border-none uppercase font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full">
            {active ? 'Active' : 'Inactive'}
          </Tag>
          <Button size="small" onClick={() => handleToggle(record, !active)}>
            {active ? 'Disable' : 'Enable'}
          </Button>
        </div>
      ),
    },
    {
      title: 'Execution',
      dataIndex: 'execution_mode',
      key: 'execution_mode',
      render: (mode) => <Tag className="uppercase">{mode || 'native'}</Tag>,
    },
    {
      title: 'Config',
      key: 'config',
      render: (_, record) => (
        <Button
          size="small"
          icon={<Settings2 size={13} />}
          onClick={() => navigate(`/interviews/types/${record.id}/config`)}
        >
          Configure
        </Button>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created',
      render: (date) => <Text className="text-slate-400 text-xs font-medium">{new Date(date).toLocaleDateString()}</Text>,
    },
  ]

  return (
    <div
      className={cn(
        'flex flex-col bg-[#F8FAFC] -m-4',
        isAiInterviewsRoute || isTechnicalInterviewsRoute || isHumanInterviewsRoute || isScreeningInterviewsRoute || isSequentialRoundRoute || isGroupDiscussionRoute || isBarRaiserRoute || isRolePlayRoute || isPresentationRoute || isPortfolioReviewRoute || isAssessmentCenterRoute || isCampusHiringRoute || isMockInterviewRoute || isWalkinDriveRoute || isVideoInterviewsRoute || isWhiteboardInterviewsRoute || isAssessmentsRoute || isPrequalificationRoute
          ? 'min-h-[calc(100vh-96px)]'
          : 'h-[calc(100vh-96px)] overflow-hidden',
      )}
    >
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-soft-sm shadow-indigo-100">
              <Calendar size={18} />
            </div>
            <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">Type Registry</h1>
          </div>
          
          <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-0.5 ml-2">
            <button
              onClick={() => navigate('/interviews')}
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700"
            >
              <List size={12} /> Command Center
            </button>
            <button
              onClick={() => navigate('/interviews/types')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isRegistryHome
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Target size={12} /> Registry
            </button>
            <button
              onClick={() => navigate('/interviews/ai')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isAiInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Cpu size={12} /> AI Interviews
            </button>
            <button
              onClick={() => navigate('/interviews/technical')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isTechnicalInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Settings2 size={12} /> Technical Interviews
            </button>
            <button
              onClick={() => navigate('/interviews/human')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isHumanInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Target size={12} /> Human Interviews
            </button>
            <button
              onClick={() => navigate('/interviews/screening')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isScreeningInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <UserCheck size={12} /> Screening Interviews
            </button>
            <button
              onClick={() => navigate('/interviews/sequential-round')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isSequentialRoundRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <GitBranch size={12} /> Sequential Round
            </button>
            <button
              onClick={() => navigate('/interviews/group-discussion')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isGroupDiscussionRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Users size={12} /> Group Discussion
            </button>
            <button
              onClick={() => navigate('/interviews/bar-raiser')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isBarRaiserRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <BarChart2 size={12} /> Bar Raiser
            </button>
            <button
              onClick={() => navigate('/interviews/role-play')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isRolePlayRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Wand2 size={12} /> Role Play
            </button>
            <button
              onClick={() => navigate('/interviews/presentation-interview')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isPresentationRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Monitor size={12} /> Presentation
            </button>
            <button
              onClick={() => navigate('/interviews/portfolio-review')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isPortfolioReviewRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Layers size={12} /> Portfolio Review
            </button>
            <button
              onClick={() => navigate('/interviews/assessment-center')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isAssessmentCenterRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Building2 size={12} /> Assessment Center
            </button>
            <button
              onClick={() => navigate('/interviews/campus-hiring')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isCampusHiringRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Building2 size={12} /> Campus Hiring
            </button>
            <button
              onClick={() => navigate('/interviews/mock-interview')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isMockInterviewRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Wand2 size={12} /> Mock Interview
            </button>
            <button
              onClick={() => navigate('/interviews/walkin-drive')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isWalkinDriveRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Building2 size={12} /> Walk-in Drive
            </button>
            <button
              onClick={() => navigate('/interviews/video')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isVideoInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Video size={12} /> Video Interviews
            </button>
            <button
              onClick={() => navigate('/interviews/whiteboard')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isWhiteboardInterviewsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Pencil size={12} /> Whiteboard Interview
            </button>
            <button
              onClick={() => navigate('/interviews/assessments')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isAssessmentsRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Cpu size={12} /> Assessments
            </button>
            <button
              onClick={() => navigate('/interviews/prequalification')}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest',
                isPrequalificationRoute
                  ? 'bg-white text-indigo-700 shadow-sm border border-indigo-50'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <ClipboardList size={12} /> Prequalification
            </button>
            <button
              onClick={() => navigate('/interviews/templates')}
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700"
            >
              <LayoutGrid size={12} /> Templates
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isAiInterviewsRoute ? null : (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-700 shadow-soft-lg shadow-indigo-100 active:scale-95 transition-all"
            >
              <Plus size={14} /> New Type
            </button>
          )}
        </div>
      </div>

      <div
        className={cn(
          'flex-1 p-6 space-y-6',
          isAiInterviewsRoute || isTechnicalInterviewsRoute || isHumanInterviewsRoute || isScreeningInterviewsRoute || isSequentialRoundRoute || isGroupDiscussionRoute || isBarRaiserRoute || isRolePlayRoute || isPresentationRoute || isPortfolioReviewRoute || isAssessmentCenterRoute || isCampusHiringRoute || isMockInterviewRoute || isWalkinDriveRoute || isVideoInterviewsRoute || isWhiteboardInterviewsRoute || isAssessmentsRoute || isPrequalificationRoute ? 'overflow-visible' : 'overflow-hidden',
        )}
      >
        {isAiInterviewsRoute ? (
          <InterviewAIEngine embedded />
        ) : isTechnicalInterviewsRoute ? (
          <InterviewTechnicalEngine embedded />
        ) : isHumanInterviewsRoute ? (
          <InterviewHumanEngine embedded />
        ) : isScreeningInterviewsRoute ? (
          <InterviewScreeningEngine embedded />
        ) : isSequentialRoundRoute ? (
          <InterviewSequentialRoundEngine embedded />
        ) : isGroupDiscussionRoute ? (
          <InterviewGroupDiscussionEngine embedded />
        ) : isBarRaiserRoute ? (
          <InterviewBarRaiserEngine embedded />
        ) : isRolePlayRoute ? (
          <InterviewRolePlayEngine embedded />
        ) : isPresentationRoute ? (
          <InterviewPresentationEngine embedded />
        ) : isPortfolioReviewRoute ? (
          <InterviewPortfolioReviewEngine embedded />
        ) : isAssessmentCenterRoute ? (
          <InterviewAssessmentCenterEngine embedded />
        ) : isCampusHiringRoute ? (
          <InterviewCampusHiringEngine embedded />
        ) : isMockInterviewRoute ? (
          <InterviewMockEngine embedded />
        ) : isWalkinDriveRoute ? (
          <InterviewWalkinDriveEngine embedded />
        ) : isVideoInterviewsRoute ? (
          <InterviewVideoEngine embedded />
        ) : isWhiteboardInterviewsRoute ? (
          <InterviewWhiteboardEngine embedded />
        ) : isAssessmentsRoute ? (
          <InterviewAssessmentEngine embedded />
        ) : isPrequalificationRoute ? (
          <InterviewPrequalificationEngine embedded />
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-soft-md overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-slate-100 bg-slate-50/30 flex items-center justify-between">
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 focus-within:border-indigo-300 transition-all max-w-sm flex-1">
                <Search size={14} className="text-slate-400" />
                <input
                  placeholder="Search types..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-transparent text-[11px] font-bold text-slate-700 outline-none placeholder-slate-400 uppercase tracking-widest w-full"
                />
              </div>
              <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{filteredTypes.length} Active Catalog Items</Text>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              <Table
                columns={columns}
                dataSource={filteredTypes}
                rowKey="id"
                loading={isLoading}
                pagination={false}
                className="enterprise-table"
              />
            </div>
          </div>
        )}
      </div>

      <Modal
        title={<span className="font-black text-slate-900 tracking-tight uppercase">Create Interview Type</span>}
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-6">
          <Form.Item name="name" label="Type Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Technical Assessment" className="h-10 rounded-xl" />
          </Form.Item>
          <Form.Item name="code" label="Type Code" rules={[{ required: true }]}>
            <Input placeholder="e.g. technical_eval" className="h-10 rounded-xl font-mono uppercase" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="What is this interview format for?" className="rounded-xl" />
          </Form.Item>
          <Form.Item name="execution_mode" label="Execution Mode" initialValue="native">
            <Input placeholder="native / third_party / external / manual / async" className="h-10 rounded-xl" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
