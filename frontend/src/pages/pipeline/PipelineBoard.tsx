import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Select, Card, Tag, Typography, Spin, Empty, Button,
  Avatar, message, Modal,
  Tabs, Table, Timeline, Badge, Row, Col, Divider, Form, Input as AntInput, DatePicker, InputNumber
} from 'antd'
import {
  Clock,
  Star,
  X,
  ArrowRight,
  Search,
  ChevronRight,
  Mail,
  Phone,
  FileText,
  CheckCircle,
  User,
  ExternalLink,
  Plus,
  Calendar,
  DollarSign
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from 'react-beautiful-dnd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { pipelineApi } from '@/api/pipeline'
import { requisitionsApi } from '@/api/jobs'
import { candidatesApi } from '@/api/candidates'
import { interviewsApi } from '@/api/interviews'
import type {
  PipelineData, PipelineStageData, Application,
  JobRequisition, Candidate, CandidateDetail
} from '@/types'
import { cn } from '@/utils/cn'
import http from '@/utils/http'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

const { Text, Title } = Typography
const { TextArea } = AntInput

// ─── Sub-components ─────────────────────────────────────────────────────────

const InterviewScheduleModal = ({ 
  visible, 
  onCancel, 
  applicationId, 
  onSuccess 
}: { 
  visible: boolean, 
  onCancel: () => void, 
  applicationId: string,
  onSuccess: () => void
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (values: any) => interviewsApi.create({
      application_id: applicationId,
      title: values.title,
      interview_type: values.interview_type,
      scheduled_at: values.scheduled_at.toISOString(),
      duration_minutes: values.duration_minutes,
      interview_round: values.interview_round,
    }),
    onSuccess: () => {
      message.success('Interview scheduled')
      queryClient.invalidateQueries({ queryKey: ['app-interviews', applicationId] })
      onSuccess()
      onCancel()
      form.resetFields()
    },
    onError: (err: any) => {
      message.error(err.response?.data?.message || 'Failed to schedule interview')
    }
  })

  return (
    <Modal
      title="Schedule Interview"
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={mutation.isPending}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={{ duration_minutes: 45, interview_round: 1 }}>
        <Form.Item name="title" label="Interview Title" rules={[{ required: true }]}>
          <AntInput placeholder="e.g. Technical Round 1" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="interview_type" label="Type" rules={[{ required: true }]}>
              <Select options={[
                { value: 'technical', label: 'Technical' },
                { value: 'culture', label: 'Culture' },
                { value: 'management', label: 'Management' },
                { value: 'screening', label: 'Screening' }
              ]} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="interview_round" label="Round" rules={[{ required: true }]}>
              <InputNumber className="w-full" min={1} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="scheduled_at" label="Date & Time" rules={[{ required: true }]}>
              <DatePicker showTime className="w-full" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="duration_minutes" label="Duration (mins)" rules={[{ required: true }]}>
              <InputNumber className="w-full" min={15} step={15} />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  )
}

const MakeOfferModal = ({ 
  visible, 
  onCancel, 
  applicationId, 
  onSuccess 
}: { 
  visible: boolean, 
  onCancel: () => void, 
  applicationId: string,
  onSuccess: () => void
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (values: any) => http.post(`/pipeline/applications/${applicationId}/make-offer/`, values),
    onSuccess: () => {
      message.success('Offer created and sent')
      queryClient.invalidateQueries({ queryKey: ['application', 'full', applicationId] })
      onSuccess()
      onCancel()
      form.resetFields()
    },
    onError: (err: any) => {
      message.error(err.response?.data?.message || 'Failed to make offer')
    }
  })

  return (
    <Modal
      title="Create Offer"
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={mutation.isPending}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={{ currency: 'INR' }}>
        <Row gutter={16}>
          <Col span={16}>
            <Form.Item name="offer_amount" label="Annual CTC" rules={[{ required: true }]}>
              <InputNumber className="w-full" formatter={value => `₹ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="currency" label="Currency">
              <Select options={[{ value: 'INR', label: 'INR' }, { value: 'USD', label: 'USD' }]} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="joining_date" label="Expected Joining Date" rules={[{ required: true }]}>
          <DatePicker className="w-full" />
        </Form.Item>
        <Form.Item name="notes" label="Offer Notes">
          <TextArea rows={3} placeholder="Add any special conditions..." />
        </Form.Item>
      </Form>
    </Modal>
  )
}

const MiniPipelineBoard = ({ orderedStages, candidateMap, onCardClick, selectedAppId }: any) => {
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-slate-50 border-r border-slate-200 p-4 gap-4">
      {orderedStages.map((stageData: any) => (
        <div key={stageData.stage.id} className="flex flex-col gap-2">
          <div className="flex items-center justify-between px-2">
            <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stageData.stage.name}</Text>
            <Badge count={stageData.count} showZero size="small" style={{ backgroundColor: '#e2e8f0', color: '#64748b', boxShadow: 'none' }} />
          </div>
          <div className="space-y-2">
            {stageData.applications.map((app: any) => {
              const candidate = candidateMap.get(app.candidate_id)
              const isSelected = app.id === selectedAppId
              return (
                <div 
                  key={app.id}
                  onClick={() => onCardClick(app)}
                  className={cn(
                    "p-3 rounded-xl border cursor-pointer transition-all border-l-4",
                    isSelected 
                      ? "bg-white border-blue-200 border-l-blue-600 shadow-soft-md" 
                      : "bg-white/60 border-transparent border-l-transparent hover:bg-white hover:border-slate-200"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Avatar size={24} className="bg-slate-100 text-slate-600 font-bold text-[10px]">
                      {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
                    </Avatar>
                    <Text className="font-bold text-slate-800 text-xs truncate">
                      {candidate?.first_name} {candidate?.last_name}
                    </Text>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                     <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-bold text-[8px] uppercase px-1 rounded">
                        {formatStatusLabel(app.status || 'applied')}
                     </Tag>
                     <Text className="text-[9px] font-bold text-slate-400 uppercase">
                        {app.updated_at ? `${dayjs().diff(dayjs(app.updated_at), 'day')}d ago` : 'N/A'}
                     </Text>
                  </div>
                </div>
              )
            })}
            {stageData.applications.length === 0 && (
              <div className="py-4 text-center border border-dashed border-slate-200 rounded-xl opacity-40">
                <Text className="text-[8px] font-bold uppercase tracking-tighter text-slate-400">Empty</Text>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

const ApplicationDetailPanel = ({ applicationId, onClose, onRefresh, requisitionStages }: { applicationId: string, onClose: () => void, onRefresh: () => void, requisitionStages: any[] }) => {
  const [interviewModalVisible, setInterviewModalVisible] = useState(false)
  const [offerModalVisible, setOfferModalVisible] = useState(false)

  const { data, isLoading } = useApiQuery(
    ['application', 'full', applicationId],
    () => pipelineApi.getApplication(applicationId),
    { enabled: !!applicationId }
  )

  const application = (data as any)?.application as Application
  const stageHistory = (data as any)?.stage_history || []
  
  const { data: candidateData } = useApiQuery(
    ['candidate', 'full', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id),
    { enabled: !!application?.candidate_id }
  )

  const candidate = (candidateData as any)?.candidate as CandidateDetail

  const { data: interviewsData, isLoading: interviewsLoading } = useApiQuery(
    ['app-interviews', applicationId],
    () => interviewsApi.list({ application_id: applicationId }),
    { enabled: !!applicationId }
  )

  const handleMoveStage = async (stageId: string) => {
    try {
      await pipelineApi.moveStage(applicationId, stageId)
      message.success('Application moved')
      onRefresh()
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to move application')
    }
  }

  const handleShortlist = async () => {
    try {
      await http.post(`/pipeline/applications/${applicationId}/shortlist/`)
      message.success('Candidate shortlisted')
      onRefresh()
    } catch (err: any) {
      message.error('Failed to shortlist')
    }
  }

  const handleReject = async () => {
    Modal.confirm({
      title: 'Reject Candidate',
      content: 'Are you sure you want to reject this candidate?',
      onOk: async () => {
        try {
          await http.post(`/pipeline/applications/${applicationId}/reject/`, { reason: 'Not suitable' })
          message.success('Candidate rejected')
          onRefresh()
        } catch {
          message.error('Failed to reject')
        }
      }
    })
  }

  if (isLoading) return <div className="p-20 text-center"><Spin size="large" /></div>
  if (!application) return <Empty description="Application not found" />

  const timeInStage = application.updated_at ? dayjs(application.updated_at).fromNow(true) : 'N/A'
  const interviewList = Array.isArray((interviewsData as any)?.interviews) ? (interviewsData as any).interviews : []

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div className="p-6">
          <Row gutter={24}>
            <Col span={16}>
              <div className="mb-8">
                <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Candidate Summary</Title>
                <Text className="text-slate-600 leading-relaxed block bg-slate-50/50 p-4 rounded-2xl border border-slate-100">
                  {candidate?.profile?.summary || 'No professional summary available for this candidate.'}
                </Text>
              </div>

              <Card title={<span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Match Analysis</span>} bordered={false} className="shadow-soft-sm mb-8">
                <div className="flex items-center gap-8">
                  <div className="text-center">
                    <div className="text-4xl font-black text-emerald-600 tracking-tight">{application.match_score || 0}%</div>
                    <div className="text-[9px] font-bold text-slate-400 uppercase mt-1 tracking-widest">AI Score</div>
                  </div>
                  <div className="h-14 w-[1px] bg-slate-100" />
                  <div className="flex-1">
                    <p className="text-sm text-slate-600 leading-relaxed font-medium">
                      High proficiency in React and distributed systems architecture noted. Strong alignment with core technical requirements.
                    </p>
                  </div>
                </div>
              </Card>

              <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-6">Hiring Journey</Title>
              <Timeline 
                className="ml-2"
                items={[
                  ...stageHistory.map((h: any) => ({
                    dot: <div className="h-6 w-6 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100"><CheckCircle className="h-3 w-3" /></div>,
                    children: (
                      <div className="pb-6">
                        <Text className="block font-bold text-slate-900 text-sm">Moved to {h.to_status?.replace('_', ' ')}</Text>
                        {h.notes && <p className="text-xs text-slate-500 mt-1">"{h.notes}"</p>}
                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-1">{dayjs(h.moved_at).format('MMM D, YYYY · HH:mm')}</p>
                      </div>
                    )
                  })).reverse(),
                  {
                    dot: <div className="h-6 w-6 rounded-full bg-slate-50 text-slate-400 flex items-center justify-center border border-blue-100"><FileText className="h-3 w-3" /></div>,
                    children: (
                      <div>
                        <Text className="block font-bold text-slate-900 text-sm">Application Submitted</Text>
                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-1">{dayjs(application.created_at).format('MMM D, YYYY · HH:mm')}</p>
                      </div>
                    )
                  }
                ]}
              />
            </Col>
            
            <Col span={8}>
              <div className="space-y-6 sticky top-4">
                <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100 space-y-4">
                  <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !m-0">Details</Title>
                  <div className="space-y-3">
                    <div className="flex flex-col gap-1">
                       <Text className="text-[9px] font-bold text-slate-400 uppercase">Source</Text>
                       <Tag className="m-0 w-fit border-none bg-blue-50 text-blue-600 font-bold text-[10px] uppercase rounded-md px-2">
                          {application.source || 'Direct'}
                       </Tag>
                    </div>
                    <div className="flex flex-col gap-1">
                       <Text className="text-[9px] font-bold text-slate-400 uppercase">Time in stage</Text>
                       <Text className="text-xs font-bold text-slate-700">{timeInStage}</Text>
                    </div>
                    <div className="flex flex-col gap-1 pt-2">
                       <Text className="text-[9px] font-bold text-slate-400 uppercase mb-1">Contact</Text>
                       <div className="flex items-center gap-2 text-slate-600">
                          <Mail className="h-3.5 w-3.5 text-slate-400" />
                          <Text className="text-xs font-bold truncate">{candidate?.email || 'N/A'}</Text>
                       </div>
                       {candidate?.phone && (
                         <div className="flex items-center gap-2 text-slate-600 mt-1">
                            <Phone className="h-3.5 w-3.5 text-slate-400" />
                            <Text className="text-xs font-bold">{candidate.phone}</Text>
                         </div>
                       )}
                    </div>
                  </div>
                  <Divider className="my-2" />
                  <Button block className="h-10 rounded-xl font-bold flex items-center justify-center gap-2 border-slate-200" icon={<ExternalLink className="h-3.5 w-3.5" />}>
                     View Resume
                  </Button>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100">
                   <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Skills</Title>
                   <div className="flex flex-wrap gap-1.5">
                      {(candidate?.skills || []).map(s => (
                        <Tag key={s} className="m-0 border-none bg-slate-50 text-slate-600 font-bold text-[9px] uppercase px-2 rounded-md">{s}</Tag>
                      ))}
                   </div>
                </div>
              </div>
            </Col>
          </Row>
        </div>
      )
    },
    {
      key: 'interviews',
      label: 'Interviews',
      children: (
        <div className="p-0">
          <Table 
            dataSource={interviewList}
            rowKey="id" 
            loading={interviewsLoading}
            pagination={false}
            className="modern-table"
            columns={[
              { title: 'Type', dataIndex: 'interview_type', key: 'type', render: (t) => <Text className="font-bold text-slate-800 text-xs capitalize">{t?.replace(/_/g, ' ')}</Text> },
              { title: 'Round', dataIndex: 'interview_round', key: 'round', align: 'center', render: (r) => <Badge count={`R${r}`} style={{ backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0', boxShadow: 'none' }} /> },
              {
                title: 'Status',
                dataIndex: 'status',
                key: 'status',
                render: (s) => (
                  <Tag
                    color={getStatusStyle(s, 'application').antColor}
                    className="rounded-full font-bold text-[9px] uppercase border-none px-2"
                  >
                    {formatStatusLabel(s)}
                  </Tag>
                ),
              },
              { title: '', key: 'actions', align: 'right', render: () => <Button size="small" type="text" icon={<ChevronRight className="h-4 w-4" />} /> }
            ]}
          />
          <div className="p-6 border-t border-slate-50">
             <Button 
                onClick={() => setInterviewModalVisible(true)}
                icon={<Plus className="h-4 w-4" />} 
                className="h-10 rounded-xl font-bold border-slate-200"
             >
                Schedule New Interview
             </Button>
          </div>
        </div>
      )
    }
  ]

  const hasCompletedInterview = interviewList.some((i: any) => i.status === 'completed')

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Avatar size={56} className="bg-blue-600 text-white font-bold border-4 border-white shadow-soft-lg">
            {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
          </Avatar>
          <div>
            <div className="flex items-center gap-3 mb-0.5">
               <Title level={4} className="!m-0 text-slate-900">{candidate?.first_name} {candidate?.last_name}</Title>
               <Tag className="m-0 border-none bg-emerald-50 text-emerald-600 font-bold text-[9px] uppercase rounded-full px-2 py-0.5">
                  {application.match_score || 0}% Match
               </Tag>
            </div>
            <div className="flex items-center gap-2">
               <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
                  {candidate?.current_title || 'No Title'} • {formatStatusLabel(application?.status || 'applied')}
               </Text>
               <div className="h-1 w-1 rounded-full bg-slate-200" />
               <Select 
                  size="small"
                  className="w-32"
                  placeholder="Move to stage..."
                  value={application.current_stage_id}
                  onChange={handleMoveStage}
                  options={requisitionStages.map(s => ({ value: s.stage.id, label: s.stage.name }))}
               />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {application.status !== 'shortlisted' && (
            <Button 
              onClick={handleShortlist}
              className="h-10 rounded-xl font-bold border-slate-200 text-emerald-600 flex items-center gap-2" 
              icon={<Star className="h-4 w-4" />}
            >
              Shortlist
            </Button>
          )}
          <Button 
            danger 
            onClick={handleReject}
            className="h-10 rounded-xl font-bold bg-rose-50 border-none text-rose-600 flex items-center gap-2" 
            icon={<X className="h-4 w-4" />}
          >
            Reject
          </Button>
          <Button icon={<X className="h-4 w-4" />} onClick={onClose} className="h-10 w-10 flex items-center justify-center rounded-xl border-slate-200" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Quick Actions Bar */}
        <div className="px-6 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
           <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Execution</Text>
           <div className="flex gap-2">
              <Button 
                size="small" 
                icon={<Calendar className="h-3 w-3" />} 
                className="text-[10px] font-bold uppercase h-7 rounded-lg"
                onClick={() => setInterviewModalVisible(true)}
              >
                Schedule
              </Button>
              {(application.status === 'offer_extended' || application.status === 'interview_scheduled') && (
                <Button 
                  size="small" 
                  type="primary"
                  icon={<DollarSign className="h-3 w-3" />} 
                  className={cn(
                    "text-[10px] font-bold uppercase h-7 rounded-lg bg-emerald-600 border-none",
                    !hasCompletedInterview && "opacity-50 grayscale cursor-not-allowed"
                  )}
                  onClick={() => hasCompletedInterview ? setOfferModalVisible(true) : message.warning('Interview must be completed before offer')}
                >
                  Make Offer
                </Button>
              )}
           </div>
        </div>

        <Tabs 
          defaultActiveKey="overview" 
          items={tabItems} 
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>

      <InterviewScheduleModal 
        visible={interviewModalVisible} 
        onCancel={() => setInterviewModalVisible(false)} 
        applicationId={applicationId}
        onSuccess={onRefresh}
      />

      <MakeOfferModal 
        visible={offerModalVisible} 
        onCancel={() => setOfferModalVisible(false)} 
        applicationId={applicationId}
        onSuccess={onRefresh}
      />
    </div>
  )
}

// ─── Main PipelineBoard ──────────────────────────────────────────────────────

export default function PipelineBoard({ jobId }: { jobId?: string }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedJobId, setSelectedJobId] = useState<string>(jobId ?? searchParams.get('job') ?? '')
  const [boardState, setBoardState] = useState<Record<string, PipelineStageData>>({})
  
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null)

  // Fetch all requisitions for the selector
  const { data: jobsData } = useApiQuery(
    ['jobs'],
    () => requisitionsApi.list()
  )
  const jobs: JobRequisition[] =
    (jobsData as { requisitions: JobRequisition[] } | undefined)?.requisitions ?? []

  // Fetch pipeline for selected job
  const { data: pipelineData, isLoading: pipelineLoading, refetch } = useApiQuery(
    ['pipeline', selectedJobId],
    () => pipelineApi.getPipeline(selectedJobId),
    { enabled: !!selectedJobId }
  )

  // Fetch all candidates for name lookup
  const { data: candidatesData } = useApiQuery(
    ['candidates', 'all'],
    () => candidatesApi.list()
  )
  const candidateMap = new Map<string, Candidate>(
    ((candidatesData as { candidates: Candidate[] } | undefined)?.candidates ?? []).map((c) => [c.id, c])
  )

  useEffect(() => {
    const pd = pipelineData as PipelineData | undefined
    if (pd?.pipeline) {
      setBoardState(pd.pipeline)
    }
  }, [pipelineData])

  useEffect(() => {
    if (jobId) setSelectedJobId(jobId)
  }, [jobId])

  useEffect(() => {
    if (selectedJobId && !jobId) {
      setSearchParams({ job: selectedJobId }, { replace: true })
    }
  }, [selectedJobId, setSearchParams, jobId])

  const orderedStages = Object.values(boardState).sort(
    (a, b) => a.stage.stage_order - b.stage.stage_order
  )

  const handleDragEnd = async (result: DropResult) => {
    const { source, destination, draggableId } = result
    if (!destination || source.droppableId === destination.droppableId) return

    const fromStageId = source.droppableId
    const toStageId = destination.droppableId

    const newBoard = { ...boardState }
    const fromStage = { ...newBoard[fromStageId], applications: [...newBoard[fromStageId].applications] }
    const toStage = { ...newBoard[toStageId], applications: [...newBoard[toStageId].applications] }

    const [movedApp] = fromStage.applications.splice(source.index, 1)
    toStage.applications.splice(destination.index, 0, { ...movedApp, current_stage_id: toStageId })

    newBoard[fromStageId] = { ...fromStage, count: fromStage.count - 1 }
    newBoard[toStageId] = { ...toStage, count: toStage.count + 1 }
    setBoardState(newBoard)

    try {
      await pipelineApi.moveStage(draggableId, toStageId)
      message.success('Application moved')
      refetch()
    } catch (err: any) {
      setBoardState(boardState)
      message.error(err.response?.data?.message || 'Failed to move application')
    }
  }

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6 overflow-hidden">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="p-6 shrink-0 flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-white border-b border-slate-100">
        <div className="flex items-center gap-4">
           {!selectedAppId && <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Pipeline Board</h1>}
           {selectedAppId && (
             <Button icon={<ArrowRight className="h-4 w-4 rotate-180" />} onClick={() => setSelectedAppId(null)} className="h-10 w-10 flex items-center justify-center rounded-xl border-slate-200" />
           )}
           <Select
            className="w-72 h-10 font-bold"
            placeholder="Select Job Role..."
            value={selectedJobId || undefined}
            onChange={(val) => { setSelectedJobId(val); setSelectedAppId(null); }}
            showSearch
            optionFilterProp="label"
            options={jobs.map((j) => ({ value: j.id, label: j.title }))}
          />
        </div>
        <div className="flex items-center gap-3">
          <Badge count={orderedStages.reduce((acc, s) => acc + s.count, 0)} overflowCount={999} style={{ backgroundColor: '#eff6ff', color: '#3b82f6', border: 'none', fontWeight: 'bold' }}>
             <Button icon={<User className="h-4 w-4" />} className="h-10 rounded-xl font-bold flex items-center gap-2 border-slate-200">Candidates</Button>
          </Badge>
          <Button type="primary" className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md px-6">Settings</Button>
        </div>
      </div>

      {/* ── Content ───────────────────────────────────────────────────────── */}
      <StandardSplitView
        isDetailOpen={!!selectedAppId}
        leftOpenWidthClass="w-[30%]"
        rightOpenWidthClass="w-[70%]"
        compactListContent={
          !selectedJobId ? (
            <div className="h-full flex flex-col items-center justify-center p-20 bg-slate-50">
              <Search className="h-16 w-16 text-slate-200 mb-4" />
              <Title level={4} className="!m-0 text-slate-400">Select a job to view pipeline</Title>
              <p className="text-slate-400 mt-2 font-medium">Choose a role from the dropdown above to start managing candidates.</p>
            </div>
          ) : pipelineLoading ? (
            <div className="h-full flex items-center justify-center"><Spin size="large" /></div>
          ) : (
            <MiniPipelineBoard
              orderedStages={orderedStages}
              candidateMap={candidateMap}
              onCardClick={(app: any) => setSelectedAppId(app.id)}
              selectedAppId={selectedAppId}
            />
          )
        }
        fullListContent={
          !selectedJobId ? (
            <div className="h-full flex flex-col items-center justify-center p-20 bg-slate-50">
              <Search className="h-16 w-16 text-slate-200 mb-4" />
              <Title level={4} className="!m-0 text-slate-400">Select a job to view pipeline</Title>
              <p className="text-slate-400 mt-2 font-medium">Choose a role from the dropdown above to start managing candidates.</p>
            </div>
          ) : pipelineLoading ? (
            <div className="h-full flex items-center justify-center"><Spin size="large" /></div>
          ) : (
            <div className="p-6 h-full overflow-x-auto bg-slate-50/50">
              <DragDropContext onDragEnd={handleDragEnd}>
                <div className="flex gap-6 h-full items-start">
                  {orderedStages.map((stageData) => (
                    <div key={stageData.stage.id} className="flex flex-col w-72 shrink-0 h-full max-h-full bg-white/70 rounded-2xl border border-slate-200 shadow-soft-sm overflow-hidden">
                      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
                        <Text className="font-bold text-slate-900 text-xs uppercase tracking-widest">{stageData.stage.name}</Text>
                        <Badge count={stageData.count} showZero size="small" style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
                      </div>
                      <Droppable droppableId={stageData.stage.id}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={cn("flex-1 overflow-y-auto p-3", snapshot.isDraggingOver ? "bg-blue-50/30" : "")}
                          >
                            {stageData.applications.map((app: any, i: any) => {
                              const candidate = candidateMap.get(app.candidate_id)
                              return (
                                <Draggable key={app.id} draggableId={app.id} index={i}>
                                  {(p, s) => (
                                    <div
                                      ref={p.innerRef}
                                      {...p.draggableProps}
                                      {...p.dragHandleProps}
                                      onClick={() => !s.isDragging && setSelectedAppId(app.id)}
                                      className={cn(
                                        "p-4 bg-white rounded-2xl border border-slate-100 shadow-soft-sm mb-3 cursor-pointer transition-all",
                                        s.isDragging ? "rotate-2 scale-105 shadow-soft-lg" : "hover:border-blue-200 hover:shadow-soft-md"
                                      )}
                                    >
                                      <div className="flex items-center gap-3 mb-3">
                                        <Avatar className="bg-blue-50 text-blue-600 font-bold border-none shrink-0">
                                          {candidate?.first_name?.charAt(0)}{candidate?.last_name?.charAt(0)}
                                        </Avatar>
                                        <div className="min-w-0">
                                          <Text className="block font-bold text-slate-900 text-xs leading-tight truncate">
                                            {candidate?.first_name} {candidate?.last_name}
                                          </Text>
                                          <Text className="text-[10px] text-slate-400 font-medium truncate">
                                            {candidate?.current_title || 'No Title'}
                                          </Text>
                                        </div>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-bold text-[9px] uppercase px-1.5 rounded">
                                          {app.match_score || 0}% Match
                                        </Tag>
                                        <div className="flex items-center gap-1">
                                          <Clock className="h-3 w-3 text-slate-300" />
                                          <span className="text-[10px] font-bold text-slate-400">
                                            {app.updated_at ? `${dayjs().diff(dayjs(app.updated_at), 'day')}d` : 'N/A'}
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </Draggable>
                              )
                            })}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  ))}
                </div>
              </DragDropContext>
            </div>
          )
        }
        detailContent={
          selectedAppId ? (
            <ApplicationDetailPanel
              applicationId={selectedAppId}
              onClose={() => setSelectedAppId(null)}
              onRefresh={() => {
                refetch()
                setSelectedAppId(selectedAppId)
              }}
              requisitionStages={orderedStages}
            />
          ) : null
        }
      />
    </div>
  )
}
