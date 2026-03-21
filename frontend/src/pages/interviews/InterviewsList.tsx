import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Table, Button, Input, Select, Tag, Form,
  Typography, Row, Col, Card, Avatar, Badge, Tabs, Spin, Modal, message
} from 'antd'
import {
  Search, RefreshCw, Clock, X, ChevronRight, Video,
  MapPin, Calendar, Briefcase, CheckCircle2, MessageSquare,
  Play, CheckCheck, DollarSign, UserCheck
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { interviewsApi } from '@/api/interviews'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import type { Interview, Application, CandidateDetail } from '@/types'
import { cn } from '@/utils/cn'
import http from '@/utils/http'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

dayjs.extend(relativeTime)
const { Title, Text } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'pending_feedback', label: 'Pending Feedback' },
]

// ─── Feedback Submit Modal ────────────────────────────────────────────────────

const FeedbackModal = ({ interviewId, open, onClose }: { interviewId: string; open: boolean; onClose: () => void }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await interviewsApi.submitFeedback(interviewId, {
        score: values.score,
        recommendation: values.recommendation,
        feedback_text: values.feedback_text,
      })
      await queryClient.invalidateQueries({ queryKey: ['interview-feedback', interviewId] })
      message.success('Feedback submitted')
      form.resetFields()
      onClose()
    } catch {
      message.error('Failed to submit feedback')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold text-slate-900">Submit Feedback</span>}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText="Submit"
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4">
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="score" label="Score (0–100)" rules={[{ required: true }]}>
              <Input type="number" min={0} max={100} className="h-10 rounded-xl" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="recommendation" label="Recommendation" rules={[{ required: true }]}>
              <Select className="h-10" options={[
                { value: 'strong_hire', label: 'Strong Hire' },
                { value: 'hire', label: 'Hire' },
                { value: 'neutral', label: 'Neutral' },
                { value: 'no_hire', label: 'No Hire' },
                { value: 'strong_no_hire', label: 'Strong No Hire' },
              ]} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="feedback_text" label="Comments" rules={[{ required: true }]}>
          <Input.TextArea rows={4} placeholder="Detailed feedback..." className="rounded-xl" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

// ─── Interview Sub-components ─────────────────────────────────────────────────

const FullInterviewList = ({ interviews, onSelect, selectedInterviewId, isLoading }: any) => {
  const columns: ColumnsType<Interview> = [
    {
      title: 'Candidate Name',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      render: (name) => (
        <div className="flex items-center gap-3">
          <Avatar className="bg-blue-50 text-blue-600 font-bold border-none shrink-0">
            {name?.charAt(0).toUpperCase()}
          </Avatar>
          <div className="min-w-0">
            <Text className="block font-bold text-slate-900 leading-tight truncate">{name || 'Unknown'}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Job Title',
      dataIndex: 'job_title',
      key: 'job_title',
      render: (title: string) => <Text className="font-bold text-slate-700 text-xs">{title || 'Unknown Job'}</Text>,
    },
    {
      title: 'Interview Type',
      dataIndex: 'interview_type',
      key: 'interview_type',
      width: 160,
      render: (type: string) => (
        <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-md px-2 py-0.5 tracking-wider">
          {formatStatusLabel(type)}
        </Tag>
      ),
    },
    {
      title: 'Scheduled At',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      width: 180,
      render: (date: string) => (
        <div className="flex flex-col">
          <div className="flex items-center gap-2 text-slate-700 font-bold text-xs">
            <Calendar className="h-3 w-3" />
            {date ? dayjs(date).format('MMM D, YYYY') : 'TBD'}
          </div>
          <div className="flex items-center gap-2 text-slate-400 font-medium text-[11px] mt-0.5">
            <Clock className="h-3 w-3" />
            {date ? dayjs(date).format('h:mm A') : ''}
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (s: string) => (
        <Tag color={getStatusStyle(s, 'application').antColor} className="m-0 border-none uppercase font-bold text-[9px] tracking-widest px-2 py-0.5 rounded-full">
          {formatStatusLabel(s)}
        </Tag>
      ),
    },
    {
      title: 'Round',
      dataIndex: 'interview_round',
      key: 'interview_round',
      width: 80,
      align: 'center',
      render: (r) => <Badge count={`R${r}`} style={{ backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0', boxShadow: 'none', fontWeight: 'bold' }} />,
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />,
    },
  ]

  return (
    <Table<Interview>
      columns={columns}
      dataSource={interviews}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          'cursor-pointer transition-all duration-200',
          record.id === selectedInterviewId ? 'bg-blue-50 hover:bg-blue-50' : 'hover:bg-slate-50'
        ),
      })}
      pagination={{ pageSize: 15, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedInterviewList = ({ interviews, onSelect, selectedInterviewId }: any) => (
  <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
    <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
      <Text className="font-bold text-slate-900">Interviews</Text>
      <Badge count={interviews.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
    </div>
    {interviews.map((item: any) => (
      <div
        key={item.id}
        onClick={() => onSelect(item)}
        className={cn(
          'p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4',
          item.id === selectedInterviewId
            ? 'bg-blue-50/50 border-l-blue-600'
            : 'bg-white border-l-transparent hover:bg-slate-50'
        )}
      >
        <div className="flex items-center gap-3">
          <Avatar size={32} className="bg-slate-100 text-slate-600 font-bold border-none shrink-0">
            {item.candidate_name?.charAt(0)}
          </Avatar>
          <div className="min-w-0">
            <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">{item.candidate_name}</p>
            <Text className="text-[10px] text-slate-400 font-bold uppercase truncate">
              R{item.interview_round} • {formatStatusLabel(item.interview_type)}
            </Text>
          </div>
        </div>
      </div>
    ))}
  </div>
)

const InterviewDetailPanel = ({ interview, onClose, onRefetch }: { interview: Interview; onClose: () => void; onRefetch: () => void }) => {
  const interviewId = interview?.id
  const [feedbackModal, setFeedbackModal] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const { data: feedbackData, isLoading: feedbackLoading, refetch: refetchFeedback } = useApiQuery(
    ['interview-feedback', interviewId],
    () => http.get(`/interviews/${interviewId}/feedback/`),
    { enabled: !!interviewId }
  )
  const feedbackList = Array.isArray((feedbackData as any)?.data?.feedback) ? (feedbackData as any).data.feedback : []

  const { data: applicationData } = useApiQuery(
    ['application', interview.application_id],
    () => pipelineApi.getApplication(interview.application_id),
    { enabled: !!interview.application_id }
  )
  const application = (applicationData as any)?.application as Application | undefined

  const { data: candidateData } = useApiQuery(
    ['candidate', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id || ''),
    { enabled: !!application?.candidate_id }
  )
  const candidate = (candidateData as any)?.candidate as CandidateDetail | undefined

  const handleAction = async (action: 'start' | 'complete') => {
    setActionLoading(action)
    try {
      if (action === 'start') await interviewsApi.start(interviewId)
      else await interviewsApi.complete(interviewId)
      message.success(`Interview ${action === 'start' ? 'started' : 'completed'}`)
      onRefetch()
      refetchFeedback()
    } catch {
      message.error('Action failed')
    } finally {
      setActionLoading(null)
    }
  }

  const canStart = ['scheduled', 'confirmed', 'rescheduled'].includes(interview.status)
  const canComplete = interview.status === 'in_progress'
  const panelists = Array.isArray(interview.interviewers) ? interview.interviewers : []

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div className="p-6">
          <div className="mb-6 bg-slate-50/50 rounded-2xl p-5 border border-slate-100">
            <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Candidate Summary</Text>
            <Text className="block font-bold text-slate-800">{interview.candidate_name || 'Unknown Candidate'}</Text>
            <Text className="block text-sm text-slate-500 mt-1">
              {candidate?.current_title || 'No title'} {candidate?.current_company ? `· ${candidate.current_company}` : ''}
            </Text>
            <Text className="block text-xs text-slate-500 mt-2 leading-relaxed">
              {candidate?.profile?.summary || 'No candidate summary available.'}
            </Text>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100">
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Time & Date</Text>
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-blue-600" />
                <Text className="font-bold text-slate-700">
                  {interview?.scheduled_at ? dayjs(interview.scheduled_at).format('dddd, MMMM D, YYYY') : 'TBD'}
                </Text>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <Clock className="h-4 w-4 text-blue-600" />
                <Text className="font-bold text-slate-700">
                  {interview?.scheduled_at ? dayjs(interview.scheduled_at).format('h:mm A') : 'TBD'}
                  {interview?.duration_minutes ? ` · ${interview.duration_minutes} min` : ''}
                </Text>
              </div>
            </div>
            <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100">
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Schedule Details</Text>
              <div className="flex items-center gap-3">
                <Video className="h-4 w-4 text-blue-600" />
                <Text className="font-bold text-blue-600 cursor-pointer underline underline-offset-4 truncate">
                  {interview?.meeting_link || 'No link'}
                </Text>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <MapPin className="h-4 w-4 text-slate-400" />
                <Text className="text-slate-500 font-medium">{interview?.location_detail || 'Virtual'}</Text>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <Tag color={getStatusStyle(interview.status, 'application').antColor} className="m-0 border-none uppercase font-bold text-[9px] tracking-widest px-2 py-0.5 rounded-full">
                  {formatStatusLabel(interview.status)}
                </Tag>
              </div>
            </div>
          </div>

          <div>
            <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Job Context</Title>
            <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100">
              <div className="flex items-center gap-3">
                <Briefcase className="h-5 w-5 text-slate-400" />
                <div>
                  <Text className="block font-bold text-slate-800">{interview?.job_title || 'N/A'}</Text>
                  <Text className="block text-xs text-slate-500">Round {interview?.interview_round} · {formatStatusLabel(interview?.interview_type)}</Text>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100">
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Panelists</Text>
                <div className="flex flex-wrap gap-2">
                  {panelists.length > 0 ? panelists.map((id) => (
                    <Tag key={id} className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase px-2 py-0.5 rounded-md">
                      {id}
                    </Tag>
                  )) : (
                    <Text className="text-xs text-slate-400 font-medium">No panelists assigned</Text>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'feedback',
      label: `Feedback${feedbackList.length ? ` (${feedbackList.length})` : ''}`,
      children: (
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <Title level={5} className="!m-0 !text-sm">Interviewer Feedback</Title>
            <Button
              type="primary"
              size="small"
              className="bg-blue-600 border-none font-bold text-[11px] h-8 rounded-lg px-4 uppercase"
              onClick={() => setFeedbackModal(true)}
            >
              Add Feedback
            </Button>
          </div>

          {feedbackList.length > 0 && (
            <div className="mb-6 p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
              <Text className="block text-[10px] font-bold text-emerald-600 uppercase tracking-widest mb-1">Average Score</Text>
              <Text className="block text-2xl font-black text-emerald-700">
                {interview.feedback_average_score?.toFixed(0) ?? '—'}<span className="text-sm font-bold text-emerald-500">/100</span>
              </Text>
              <Text className="text-[10px] text-emerald-500 font-bold uppercase">{feedbackList.length} response{feedbackList.length !== 1 ? 's' : ''}</Text>
            </div>
          )}

          <div className="space-y-4">
            {feedbackLoading ? <Spin /> : feedbackList.length > 0 ? feedbackList.map((fb: any) => (
              <div key={fb.id} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-soft-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Avatar size={32} className="bg-slate-100" />
                    <div>
                      <Text className="block font-bold text-slate-800 text-sm">{fb.interviewer_name || 'Interviewer'}</Text>
                      <Text className="block text-[10px] text-slate-400 font-bold uppercase">{fb.created_at ? dayjs(fb.created_at).fromNow() : ''}</Text>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-blue-50 text-blue-600 font-black px-3 py-1 rounded-full text-xs">{fb.score ?? '—'}/100</span>
                    <Tag className="m-0 border-none uppercase font-bold text-[9px] px-2 rounded-full" color={fb.recommendation?.startsWith('strong_hire') ? 'success' : fb.recommendation?.startsWith('strong_no') ? 'error' : 'default'}>
                      {fb.recommendation?.replace(/_/g, ' ') || '—'}
                    </Tag>
                  </div>
                </div>
                <Text className="text-slate-600 text-sm leading-relaxed block">{fb.feedback_text || 'No comments.'}</Text>
              </div>
            )) : (
              <div className="py-16 text-center bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
                <MessageSquare className="h-10 w-10 text-slate-200 mx-auto mb-3" />
                <Text className="text-slate-300 font-bold uppercase text-[10px] tracking-widest">No feedback submitted yet</Text>
              </div>
            )}
          </div>

          <FeedbackModal interviewId={interviewId} open={feedbackModal} onClose={() => setFeedbackModal(false)} />
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Avatar size={48} className="bg-blue-600 text-white font-bold border-none shadow-soft-md">
            {interview.candidate_name?.charAt(0)}
          </Avatar>
          <div>
            <div className="flex items-center gap-3 mb-0.5">
              <Title level={4} className="!m-0 text-slate-900">{interview.candidate_name}</Title>
              <Tag color={getStatusStyle(interview.status, 'application').antColor} className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                {formatStatusLabel(interview.status)}
              </Tag>
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              R{interview.interview_round} {formatStatusLabel(interview.interview_type)} · {interview.job_title}
            </Text>
          </div>
        </div>
        <Button icon={<X className="h-4 w-4" />} onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg border-slate-200" />
      </div>

      {/* Quick Actions */}
      <div className="px-6 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
        <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Quick Actions</Text>
        <div className="flex gap-2">
          {canStart && (
            <Button
              size="small"
              icon={<Play className="h-3 w-3" />}
              loading={actionLoading === 'start'}
              onClick={() => handleAction('start')}
              className="text-[10px] font-bold uppercase h-7 rounded-lg bg-emerald-500 border-none text-white hover:bg-emerald-600"
            >
              Start Interview
            </Button>
          )}
          {canComplete && (
            <Button
              size="small"
              type="primary"
              icon={<CheckCheck className="h-3 w-3" />}
              loading={actionLoading === 'complete'}
              onClick={() => handleAction('complete')}
              className="text-[10px] font-bold uppercase h-7 rounded-lg bg-blue-600 border-none"
            >
              Mark Complete
            </Button>
          )}
          <Button
            size="small"
            icon={<MessageSquare className="h-3 w-3" />}
            className="text-[10px] font-bold uppercase h-7 rounded-lg"
            onClick={() => setFeedbackModal(true)}
          >
            Add / View Feedback
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Tabs
          defaultActiveKey="overview"
          items={tabItems}
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>
    </div>
  )
}

// ─── Offers Sub-components ────────────────────────────────────────────────────

const FullOfferList = ({ offers, onSelect, selectedOfferId, isLoading }: any) => {
  const columns: ColumnsType<Application> = [
    {
      title: 'Candidate Name',
      dataIndex: 'candidate_name',
      key: 'candidate_name',
      render: (_: string, record) => (
        <div className="flex items-center gap-3">
          <Avatar className="bg-orange-50 text-orange-600 font-bold border-none shrink-0">
            {(record as any).candidate_name?.charAt(0) || record.candidate_id?.substring(0, 1).toUpperCase()}
          </Avatar>
          <div className="min-w-0">
            <Text className="block font-bold text-slate-900 leading-tight truncate">
              {(record as any).candidate_name || `Candidate ···${record.candidate_id?.slice(-6)}`}
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Job Title',
      dataIndex: 'job_title',
      key: 'job_title',
      render: (_: string, record) => (
        <Text className="font-bold text-slate-700 text-xs">
          {(record as any).job_title || `Job ···${record.requisition_id?.slice(-6)}`}
        </Text>
      ),
    },
    {
      title: 'Offer Amount',
      key: 'offer_amount',
      width: 140,
      render: (_, record) => record.offer_amount
        ? <Text className="font-black text-slate-800">{record.offer_currency || 'USD'} {Number(record.offer_amount).toLocaleString()}</Text>
        : <Text className="text-slate-300 font-bold text-xs">—</Text>,
    },
    {
      title: 'Joining Date',
      dataIndex: 'joining_date',
      key: 'joining_date',
      width: 130,
      render: (d) => d
        ? <div className="flex items-center gap-2 text-slate-700 font-bold text-xs"><Calendar className="h-3 w-3" />{dayjs(d).format('MMM D, YYYY')}</div>
        : <Text className="text-slate-300 font-bold text-xs">—</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (s: string) => (
        <Tag color={getStatusStyle(s, 'application').antColor} className="m-0 border-none uppercase font-bold text-[9px] tracking-widest px-2 py-0.5 rounded-full">
          {formatStatusLabel(s)}
        </Tag>
      ),
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 110,
      render: (d) => <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">{dayjs(d).fromNow()}</span>,
    },
    {
      title: '',
      key: 'arrow',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />,
    },
  ]

  return (
    <Table<Application>
      columns={columns}
      dataSource={offers}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          'cursor-pointer transition-all duration-200',
          record.id === selectedOfferId ? 'bg-orange-50 hover:bg-orange-50' : 'hover:bg-slate-50'
        ),
      })}
      pagination={{ pageSize: 15, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedOfferList = ({ offers, onSelect, selectedOfferId }: any) => (
  <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
    <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
      <Text className="font-bold text-slate-900">Offers</Text>
      <Badge count={offers.length} showZero style={{ backgroundColor: '#fff7ed', color: '#ea580c', boxShadow: 'none' }} />
    </div>
    {offers.map((item: any) => (
      <div
        key={item.id}
        onClick={() => onSelect(item)}
        className={cn(
          'p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4',
          item.id === selectedOfferId
            ? 'bg-orange-50/50 border-l-orange-500'
            : 'bg-white border-l-transparent hover:bg-slate-50'
        )}
      >
        <div className="flex items-center gap-3">
          <Avatar size={32} className="bg-orange-100 text-orange-600 font-bold border-none shrink-0">
            {item.candidate_name?.charAt(0) || '?'}
          </Avatar>
          <div className="min-w-0">
            <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
              {item.candidate_name || `···${item.candidate_id?.slice(-6)}`}
            </p>
            <Text className="text-[10px] text-slate-400 font-bold uppercase truncate">
              {item.offer_amount ? `${item.offer_currency || 'USD'} ${Number(item.offer_amount).toLocaleString()}` : 'No amount'}
            </Text>
          </div>
        </div>
      </div>
    ))}
  </div>
)

const OfferDetailPanel = ({ offer, onClose, onRefetch }: { offer: Application; onClose: () => void; onRefetch: () => void }) => {
  const navigate = useNavigate()
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const o = offer as any

  const statusFlow = [
    { key: 'offer_extended', label: 'Offer Extended', date: offer.offer_date },
    { key: 'offer_accepted', label: 'Accepted', date: offer.offer_accepted_at },
  ]

  const canWithdraw = ['offer_extended'].includes(offer.status)
  const canReject = ['offer_extended'].includes(offer.status)

  const handleStatusUpdate = async (action: 'withdraw' | 'reject') => {
    setActionLoading(action)
    try {
      if (action === 'withdraw') {
        await pipelineApi.withdraw(offer.id)
      } else {
        await pipelineApi.reject(offer.id, 'Offer not proceeding')
      }
      message.success(`Offer ${action === 'withdraw' ? 'withdrawn' : 'rejected'}`)
      onRefetch()
    } catch {
      message.error('Failed to update status')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-orange-100 flex items-center justify-center shrink-0">
            <DollarSign className="h-6 w-6 text-orange-500" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-0.5">
              <Title level={4} className="!m-0 text-slate-900">
                {o.candidate_name || `Candidate ···${offer.candidate_id?.slice(-6)}`}
              </Title>
              <Tag color={getStatusStyle(offer.status, 'application').antColor} className="m-0 border-none font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                {formatStatusLabel(offer.status)}
              </Tag>
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              {o.job_title || `Job ···${offer.requisition_id?.slice(-6)}`}
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="small"
            icon={<Briefcase className="h-3.5 w-3.5" />}
            className="h-8 rounded-lg font-bold text-[10px] uppercase"
            onClick={() => navigate(`/pipeline?job=${offer.requisition_id}`)}
          >
            View Linked Application
          </Button>
          <Button icon={<X className="h-4 w-4" />} onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg border-slate-200" />
        </div>
      </div>

      {(canWithdraw || canReject) && (
        <div className="px-6 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
          <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Quick Actions</Text>
          <div className="flex gap-2">
            {canWithdraw && (
              <Button
                size="small"
                loading={actionLoading === 'withdraw'}
                className="text-[10px] font-bold uppercase h-7 rounded-lg"
                onClick={() => handleStatusUpdate('withdraw')}
              >
                Withdraw Offer
              </Button>
            )}
            {canReject && (
              <Button
                size="small"
                danger
                loading={actionLoading === 'reject'}
                className="text-[10px] font-bold uppercase h-7 rounded-lg"
                onClick={() => handleStatusUpdate('reject')}
              >
                Reject Offer
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Offer Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-orange-50 rounded-2xl p-5 border border-orange-100">
            <Text className="block text-[10px] font-bold text-orange-500 uppercase tracking-widest mb-1">Offer Amount</Text>
            <Text className="block text-2xl font-black text-orange-700">
              {offer.offer_amount ? `${offer.offer_currency || 'USD'} ${Number(offer.offer_amount).toLocaleString()}` : '—'}
            </Text>
          </div>
          <div className="bg-slate-50 rounded-2xl p-5 border border-slate-100">
            <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Joining Date</Text>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-slate-400" />
              <Text className="font-bold text-slate-700">
                {offer.joining_date ? dayjs(offer.joining_date).format('MMMM D, YYYY') : 'Not set'}
              </Text>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div>
          <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Offer Timeline</Title>
          <div className="space-y-3">
            {statusFlow.filter(s => s.date).map((step) => (
              <div key={step.key} className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-100">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
                <div>
                  <Text className="block font-bold text-slate-700 text-sm">{step.label}</Text>
                  <Text className="text-[11px] text-slate-400 font-bold uppercase">
                    {step.date ? dayjs(step.date).format('MMM D, YYYY') : ''}
                  </Text>
                </div>
              </div>
            ))}
            {offer.offer_rejected_at && (
              <div className="flex items-center gap-4 bg-red-50 p-4 rounded-xl border border-red-100">
                <X className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <Text className="block font-bold text-red-700 text-sm">Rejected</Text>
                  <Text className="text-[11px] text-red-400 font-bold uppercase">{dayjs(offer.offer_rejected_at).format('MMM D, YYYY')}</Text>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Candidate & Job */}
        <div>
          <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Details</Title>
          <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100 space-y-4">
            <div className="flex items-center gap-3">
              <UserCheck className="h-4 w-4 text-slate-400" />
              <div>
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Candidate</Text>
                <Text className="font-bold text-slate-700">{o.candidate_name || `···${offer.candidate_id?.slice(-6)}`}</Text>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Briefcase className="h-4 w-4 text-slate-400" />
              <div>
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Job</Text>
                <Text className="font-bold text-slate-700">{o.job_title || `···${offer.requisition_id?.slice(-6)}`}</Text>
              </div>
            </div>
            {offer.is_agency_submission && (
              <div className="flex items-center gap-3">
                <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Source</Text>
                <Tag className="m-0 border-none bg-purple-50 text-purple-600 font-bold text-[10px] uppercase rounded-md px-2">Agency Submission</Tag>
              </div>
            )}
          </div>
        </div>

        <Text className="block text-[10px] text-slate-300 font-bold uppercase tracking-wider">
          Last updated {dayjs(offer.updated_at).fromNow()}
        </Text>
      </div>
    </div>
  )
}

// ─── Interviews Tab ───────────────────────────────────────────────────────────

function InterviewsTab() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null)

  const { data, isLoading, refetch } = useApiQuery(
    ['interviews', statusFilter, search],
    () => interviewsApi.list({ status: statusFilter || undefined, search: search || undefined })
  )

  const interviews: Interview[] = (data as { interviews: Interview[] } | undefined)?.interviews ?? []

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {!selectedInterview && (
        <div className="p-6 pb-4">
          <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '12px' } }}>
            <Row gutter={[12, 12]} align="middle">
              <Col xs={24} md={14}>
                <Input
                  prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                  placeholder="Search by candidate or job…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  allowClear
                  className="h-10 text-sm border-slate-200"
                />
              </Col>
              <Col xs={12} md={6}>
                <Select
                  className="w-full h-10"
                  value={statusFilter}
                  onChange={setStatusFilter}
                  options={STATUS_OPTIONS}
                />
              </Col>
              <Col xs={12} md={4}>
                <Button
                  icon={<RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />}
                  onClick={() => refetch()}
                  className="w-full h-10 flex items-center justify-center rounded-xl border-slate-200 font-bold"
                >
                  Refresh
                </Button>
              </Col>
            </Row>
          </Card>
        </div>
      )}

      <StandardSplitView
        isDetailOpen={!!selectedInterview}
        compactListContent={
          <CompressedInterviewList interviews={interviews} selectedInterviewId={selectedInterview?.id} onSelect={setSelectedInterview} />
        }
        fullListContent={
          <div className="p-6 pt-0 h-full overflow-y-auto">
            <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
              <FullInterviewList interviews={interviews} onSelect={setSelectedInterview} isLoading={isLoading} selectedInterviewId={null} />
            </Card>
          </div>
        }
        detailContent={
          selectedInterview ? (
            <InterviewDetailPanel
              interview={selectedInterview}
              onClose={() => setSelectedInterview(null)}
              onRefetch={refetch}
            />
          ) : null
        }
      />
    </div>
  )
}

// ─── Offers Tab ───────────────────────────────────────────────────────────────

function OffersTab() {
  const [selectedOffer, setSelectedOffer] = useState<Application | null>(null)

  // Fetch applications with offer statuses
  const { data: extendedData, isLoading: loadingExtended, refetch: refetchExtended } = useApiQuery(
    ['offers', 'offer_extended'],
    () => pipelineApi.listApplications({ status: 'offer_extended' })
  )
  const { data: acceptedData, isLoading: loadingAccepted, refetch: refetchAccepted } = useApiQuery(
    ['offers', 'offer_accepted'],
    () => pipelineApi.listApplications({ status: 'offer_accepted' })
  )

  const isLoading = loadingExtended || loadingAccepted
  const extended = (extendedData as { applications: Application[] } | undefined)?.applications ?? []
  const accepted = (acceptedData as { applications: Application[] } | undefined)?.applications ?? []
  const offers = [...extended, ...accepted].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())

  return (
    <StandardSplitView
      isDetailOpen={!!selectedOffer}
      compactListContent={
        <CompressedOfferList offers={offers} selectedOfferId={selectedOffer?.id} onSelect={setSelectedOffer} />
      }
      fullListContent={
        <div className="p-6 pt-0 h-full overflow-y-auto">
          <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
            <FullOfferList offers={offers} onSelect={setSelectedOffer} isLoading={isLoading} selectedOfferId={null} />
          </Card>
        </div>
      }
      detailContent={
        selectedOffer ? (
          <OfferDetailPanel
            offer={selectedOffer}
            onClose={() => setSelectedOffer(null)}
            onRefetch={() => {
              refetchExtended()
              refetchAccepted()
            }}
          />
        ) : null
      }
    />
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function InterviewsList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'interviews')

  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab && tab !== activeTab) {
      setActiveTab(tab)
    }
  }, [searchParams])

  const handleTabChange = (key: string) => {
    setActiveTab(key)
    setSearchParams({ tab: key })
  }

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6">
      {/* Header */}
      <div className="px-6 pt-6 pb-0 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-none">Interviews & Offers</h1>
          <p className="text-slate-500 mt-2 font-medium">Manage scheduled interviews and active offer letters.</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        className="flex-1 flex flex-col overflow-hidden px-6"
        tabBarStyle={{ marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        items={[
          { key: 'interviews', label: 'Interviews', children: <InterviewsTab /> },
          { key: 'offers', label: 'Offers', children: <OffersTab /> },
        ]}
      />
    </div>
  )
}
