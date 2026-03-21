import { useState } from 'react'
import {
  Table, Button, Input, Tag, Avatar, Typography,
  Card, Modal, Tabs, Spin, Form, DatePicker, InputNumber,
  Segmented, Badge, message, Row, Col, Divider, Select
} from 'antd'
import {
  Plus, Clock,
  Import, LayoutGrid, List as ListIcon, BarChart3,
  Phone, Mail, MessageSquare, UserPlus,
  ExternalLink, TrendingUp, Search, RefreshCw, X, ChevronRight,
  MapPin, Globe, Linkedin, Github,
  Briefcase, Calendar, ArrowUpRight
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { candidatesApi } from '@/api/candidates'
import { interviewsApi } from '@/api/interviews'
import { pipelineApi } from '@/api/pipeline'
import type { Candidate } from '@/types'
import { cn } from '@/utils/cn'
import http from '@/utils/http'
import { useNavigate } from 'react-router-dom'
import AllApplications from './AllApplications'
import CandidateInteractionDrawer from '@/components/CandidateInteractionDrawer'
import { StandardSplitView } from '@/components/layout/StandardSplitView'
import { formatStatusLabel, getStatusStyle } from '@/utils/status'

dayjs.extend(relativeTime)
const { Text, Title } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const SOURCE_COLORS: Record<string, string> = {
  linkedin: 'blue',
  referral: 'purple',
  direct: 'default',
  agency: 'orange',
  passport: 'green',
  self: 'cyan',
}

const CRM_STAGES = [
  { key: 'new_lead', label: 'New Lead', icon: '🆕' },
  { key: 'nurturing', label: 'Nurturing', icon: '💬' },
  { key: 'in_process', label: 'In Process', icon: '⚡' },
  { key: 'offer_stage', label: 'Offer Stage', icon: '🔥' },
  { key: 'placed', label: 'Placed', icon: '✅' },
  { key: 'lost', label: 'Lost', icon: '❌' },
]

// ─── Sub-components ─────────────────────────────────────────────────────────

const FullCandidateList = ({ candidates, onSelect, selectedCandidateId, isLoading }: any) => {
  const columns: ColumnsType<Candidate> = [
    {
      title: 'Candidate Name',
      key: 'name',
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <Avatar size={36} className="bg-blue-50 text-blue-600 font-bold border-none">
            {record.first_name?.charAt(0).toUpperCase()}{record.last_name?.charAt(0).toUpperCase()}
          </Avatar>
          <div className="min-w-0">
            <Text className="block font-bold text-slate-900 leading-tight truncate">{record.first_name} {record.last_name}</Text>
            <Text className="text-[11px] text-slate-400 font-medium truncate">{record.email}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'Current Role',
      key: 'role',
      render: (_, record) => (
        <div className="min-w-0">
          <Text className="block font-bold text-slate-700 text-xs truncate">{record.current_title || '—'}</Text>
          <Text className="text-[11px] text-slate-400 font-medium truncate uppercase tracking-wider">{record.current_company || '—'}</Text>
        </div>
      ),
    },
    {
      title: 'Experience',
      dataIndex: 'experience_years',
      key: 'exp',
      width: 100,
      render: (exp) => <Text className="font-bold text-slate-600">{exp || 0} Yrs</Text>
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source: string) => (
        <Tag color={SOURCE_COLORS[source?.toLowerCase()] || 'default'} className="m-0 border-none font-bold text-[10px] uppercase rounded-full px-2">
          {source || 'Other'}
        </Tag>
      )
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Tag
          color={getStatusStyle(record.is_actively_looking ? 'active' : 'passive', 'candidate_activity').antColor}
          className="m-0 border-none font-bold text-[10px] uppercase px-2 rounded-full"
        >
          {record.is_actively_looking ? 'Active' : 'Passive'}
        </Tag>
      )
    },
    {
      title: 'Updated At',
      dataIndex: 'updated_at',
      key: 'updated',
      width: 120,
      render: (d) => <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">{dayjs(d).format('MMM D, YYYY')}</span>
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      align: 'right',
      render: () => <Button type="text" icon={<ChevronRight className="h-4 w-4 text-slate-300" />} />
    }
  ]

  return (
    <Table<Candidate>
      columns={columns}
      dataSource={candidates}
      rowKey="id"
      loading={isLoading}
      onRow={(record) => ({
        onClick: () => onSelect(record),
        className: cn(
          "cursor-pointer transition-all duration-200",
          record.id === selectedCandidateId ? "bg-blue-50 hover:bg-blue-50" : "hover:bg-slate-50"
        ),
      })}
      pagination={{ pageSize: 15, hideOnSinglePage: true }}
      className="modern-table"
    />
  )
}

const CompressedCandidateList = ({ candidates, onSelect, selectedCandidateId }: any) => {
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white border-r border-slate-200">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
        <Text className="font-bold text-slate-900">Candidates</Text>
        <Badge count={candidates.length} showZero style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none' }} />
      </div>
      {candidates.map((item: any) => (
        <div 
          key={item.id}
          onClick={() => onSelect(item)}
          className={cn(
            "p-4 border-b border-slate-50 cursor-pointer transition-all border-l-4",
            item.id === selectedCandidateId 
              ? "bg-blue-50/50 border-l-blue-600" 
              : "bg-white border-l-transparent hover:bg-slate-50"
          )}
        >
          <div className="flex items-center gap-3">
             <Avatar size={32} className="bg-slate-100 text-slate-600 font-bold border-none shrink-0">
                {item.first_name?.charAt(0)}{item.last_name?.charAt(0)}
             </Avatar>
             <div className="min-w-0">
                <p className="m-0 font-bold text-slate-900 text-sm leading-tight truncate">
                  {item.first_name} {item.last_name}
                </p>
                <Text className="text-[10px] text-slate-400 font-medium truncate uppercase tracking-tight">
                  {item.current_title || 'No Title'}
                </Text>
             </div>
          </div>
        </div>
      ))}
    </div>
  )
}

const AddNoteModal = ({ candidateId, open, onClose }: { candidateId: string; open: boolean; onClose: () => void }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await candidatesApi.addNote(candidateId, { note_text: values.note_text, note_type: values.note_type })
      await queryClient.invalidateQueries({ queryKey: ['candidate-notes', candidateId] })
      message.success('Note added')
      form.resetFields()
      onClose()
    } catch {
      message.error('Failed to add note')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold text-slate-900">Add Note</span>}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText="Save Note"
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4">
        <Form.Item name="note_type" label="Type" initialValue="general">
          <Select className="h-10" options={[
            { value: 'general', label: 'General' },
            { value: 'call', label: 'Call' },
            { value: 'email', label: 'Email' },
            { value: 'interview', label: 'Interview' },
            { value: 'internal', label: 'Internal' },
          ]} />
        </Form.Item>
        <Form.Item name="note_text" label="Note" rules={[{ required: true, message: 'Please enter a note' }]}>
          <Input.TextArea rows={4} placeholder="Write your note here..." className="rounded-xl" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

const ScheduleInterviewModal = ({ candidateId, open, onClose }: { candidateId: string; open: boolean; onClose: () => void }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const { data: appsData } = useApiQuery(
    ['candidate-applications', candidateId],
    () => pipelineApi.listApplications({ candidate_id: candidateId }),
    { enabled: !!candidateId && open }
  )
  const applications = Array.isArray((appsData as any)?.applications) ? (appsData as any).applications : []

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await interviewsApi.create({
        application_id: values.application_id,
        interview_type: values.interview_type,
        title: values.title,
        scheduled_at: values.scheduled_at.toISOString(),
        duration_minutes: values.duration_minutes,
        interview_round: values.interview_round,
      })
      message.success('Interview scheduled')
      form.resetFields()
      onClose()
    } catch {
      message.error('Failed to schedule interview')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="font-bold text-slate-900">Schedule Interview</span>}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      okText="Schedule"
      confirmLoading={loading}
      width={520}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4" initialValues={{ duration_minutes: 60, interview_round: 1 }}>
        <Form.Item name="application_id" label="Application" rules={[{ required: true, message: 'Select an application' }]}>
          <Select className="h-10" placeholder="Select application" options={applications.map((a: any) => ({
            value: a.id,
            label: a.job_title || `Application #${a.id?.substring(0, 8)}`
          }))} />
        </Form.Item>
        <Form.Item name="title" label="Interview Title" rules={[{ required: true }]}>
          <Input placeholder="e.g. Technical Screen" className="h-10 rounded-xl" />
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="interview_type" label="Type" rules={[{ required: true }]}>
              <Select className="h-10" options={[
                { value: 'screening', label: 'Screening' },
                { value: 'technical', label: 'Technical' },
                { value: 'behavioral', label: 'Behavioral' },
                { value: 'panel', label: 'Panel' },
                { value: 'final', label: 'Final' },
              ]} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="interview_round" label="Round">
              <InputNumber min={1} max={10} className="w-full h-10" />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={14}>
            <Form.Item name="scheduled_at" label="Date & Time" rules={[{ required: true }]}>
              <DatePicker showTime className="w-full h-10 rounded-xl" format="MMM D, YYYY HH:mm" disabledDate={(d) => d < dayjs().startOf('day')} />
            </Form.Item>
          </Col>
          <Col span={10}>
            <Form.Item name="duration_minutes" label="Duration (min)">
              <InputNumber min={15} max={480} step={15} className="w-full h-10" />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  )
}

const CandidateDetailPanel = ({
  candidate,
  onClose,
  onAddNote,
  onScheduleInterview,
}: {
  candidate: Candidate,
  onClose: () => void,
  onAddNote: () => void,
  onScheduleInterview: () => void,
}) => {
  const candidateId = candidate?.id
  const [activeTab, setActiveTab] = useState('profile')
  const navigate = useNavigate()

  const { data: profileData, isLoading: _profileLoading } = useApiQuery(
    ['candidate-profile', candidateId],
    () => candidatesApi.profile(candidateId),
    { enabled: !!candidateId }
  )

  const { data: appsData, isLoading: appsLoading } = useApiQuery(
    ['candidate-applications', candidateId],
    () => pipelineApi.listApplications({ candidate_id: candidateId }),
    { enabled: !!candidateId }
  )

  const { data: notesData, isLoading: notesLoading } = useApiQuery(
    ['candidate-notes', candidateId],
    () => candidatesApi.listNotes(candidateId),
    { enabled: !!candidateId }
  )

  const profile = (profileData as any)?.profile || {}
  const workExperience = Array.isArray(profile.work_experience) ? profile.work_experience : []
  const applications = Array.isArray((appsData as any)?.applications) ? (appsData as any).applications : []
  const notes = Array.isArray((notesData as any)?.notes) ? (notesData as any).notes : []

  const tabItems = [
    {
      key: 'profile',
      label: 'Profile',
      children: (
        <div className="p-6">
          <Row gutter={24}>
            <Col span={16}>
              <div className="mb-8">
                <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Summary</Title>
                <Text className="text-slate-600 leading-relaxed block bg-slate-50/50 p-4 rounded-2xl border border-slate-100">
                  {profile.summary || 'No professional summary provided.'}
                </Text>
              </div>

              <div className="mb-8">
                <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Experience</Title>
                <div className="space-y-4">
                  {workExperience.length > 0 ? workExperience.map((exp: any, i: number) => (
                    <div key={i} className="flex gap-4">
                      <div className="h-10 w-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                        <Briefcase className="h-5 w-5 text-slate-400" />
                      </div>
                      <div>
                        <Text className="block font-bold text-slate-800">{exp.title}</Text>
                        <Text className="block text-sm text-slate-500 font-medium">{exp.company} {exp.duration ? `• ${exp.duration}` : ''}</Text>
                        <Text className="block text-xs text-slate-400 mt-1 leading-relaxed">{exp.description}</Text>
                      </div>
                    </div>
                  )) : <Text className="text-slate-400 italic text-sm">No work experience details provided.</Text>}
                </div>
              </div>

              <div>
                <Title level={5} className="!text-xs !font-bold !uppercase !tracking-widest !text-slate-400 !mb-4">Skills</Title>
                <div className="flex flex-wrap gap-2">
                  {(candidate?.skills || []).map((s: string) => (
                    <Tag key={s} className="bg-blue-50 text-blue-600 border-none font-bold rounded-lg px-3 py-1 m-0">{s}</Tag>
                  ))}
                </div>
              </div>
            </Col>
            
            <Col span={8}>
              <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-100 space-y-4 sticky top-4">
                <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !m-0">Contact Info</Title>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-slate-600">
                    <Mail className="h-4 w-4 text-slate-400" />
                    <Text className="text-xs font-bold truncate">{candidate?.email || 'N/A'}</Text>
                  </div>
                  {candidate?.phone && (
                    <div className="flex items-center gap-3 text-slate-600">
                      <Phone className="h-4 w-4 text-slate-400" />
                      <Text className="text-xs font-bold">{candidate.phone}</Text>
                    </div>
                  )}
                  <div className="flex items-center gap-3 text-slate-600">
                    <MapPin className="h-4 w-4 text-slate-400" />
                    <Text className="text-xs font-bold">
                      {[candidate?.current_location_city, candidate?.current_location_country].filter(Boolean).join(', ') || 'N/A'}
                    </Text>
                  </div>
                </div>
                
                <Divider className="my-2" />
                
                <Title level={5} className="!text-[10px] !font-bold !uppercase !tracking-widest !text-slate-400 !m-0">Professional Links</Title>
                <div className="flex flex-wrap gap-2">
                   <Button size="small" icon={<Linkedin className="h-3.5 w-3.5" />} className="bg-white border-slate-200 text-blue-600" />
                   <Button size="small" icon={<Github className="h-3.5 w-3.5" />} className="bg-white border-slate-200 text-slate-800" />
                   <Button size="small" icon={<Globe className="h-3.5 w-3.5" />} className="bg-white border-slate-200 text-slate-500" />
                </div>
              </div>
            </Col>
          </Row>
        </div>
      )
    },
    {
      key: 'applications',
      label: 'Applications',
      children: (
        <div className="p-0">
          {appsLoading ? <div className="p-10 text-center"><Spin /></div> : (
            <Table
              dataSource={applications}
              rowKey="id"
              size="small"
              pagination={false}
              className="modern-table"
              columns={[
                {
                  title: 'Job Position',
                  dataIndex: 'job_title',
                  render: (title: string, record: any) => (
                    <div className="flex flex-col">
                      <Text className="font-bold text-slate-700">{title || `Job #${record?.requisition_id?.substring(0,8) || 'Unknown'}`}</Text>
                      <Text className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">
                        Applied {record?.created_at ? dayjs(record.created_at).fromNow() : 'N/A'}
                      </Text>
                    </div>
                  )
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  render: (status) => (
                    <Tag
                      className="m-0 uppercase font-bold text-[10px] rounded-full px-2"
                      color={getStatusStyle(status, 'application').antColor}
                    >
                      {formatStatusLabel(status || 'applied')}
                    </Tag>
                  )
                },
                {
                  title: '',
                  key: 'actions',
                  render: () => <Button size="small" icon={<ChevronRight className="h-4 w-4" />} type="text" />
                }
              ]}
            />
          )}
        </div>
      )
    },
    {
      key: 'notes',
      label: 'Notes',
      children: (
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
             <Title level={5} className="!m-0 !text-sm">Activity & Notes</Title>
             <Button 
                size="small" 
                type="primary" 
                icon={<Plus className="h-3 w-3" />} 
                className="bg-slate-900 border-none font-bold text-[11px] h-8 rounded-lg px-4 uppercase"
                onClick={onAddNote}
             >
                Add Note
             </Button>
          </div>
          <div className="space-y-4">
             {notesLoading ? <Spin /> : notes.map((note: any) => (
               <div key={note.id} className="bg-white rounded-2xl p-4 border border-slate-100 shadow-soft-sm">
                  <div className="flex items-center justify-between mb-2">
                     <Tag className="m-0 border-none bg-slate-100 text-slate-500 font-bold text-[10px] uppercase rounded-md px-2 py-0.5">{note.note_type || 'General'}</Tag>
                     <Text className="text-[10px] text-slate-400 font-bold uppercase">{note.created_at ? dayjs(note.created_at).format('MMM D, YYYY') : 'N/A'}</Text>
                  </div>
                  <Text className="text-sm text-slate-600 block">{note.note_text}</Text>
               </div>
             ))}
             {(!notesLoading && notes.length === 0) && (
               <div className="py-12 text-center">
                  <MessageSquare className="h-12 w-12 text-slate-100 mx-auto mb-4" />
                  <Text className="text-slate-300 font-bold uppercase text-[10px] tracking-widest">No notes yet</Text>
               </div>
             )}
          </div>
        </div>
      )
    }
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Detail Header */}
      <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-20">
        <div className="flex items-center gap-4">
          <Avatar size={48} className="bg-blue-600 text-white font-bold border-none shadow-soft-md">
            {candidate?.first_name?.charAt(0) || ''}{candidate?.last_name?.charAt(0) || ''}
          </Avatar>
          <div>
            <div className="flex items-center gap-3 mb-0.5">
               <Title level={4} className="!m-0 text-slate-900">{candidate?.first_name || ''} {candidate?.last_name || ''}</Title>
               {candidate?.is_actively_looking && (
                 <Tag className="m-0 border-none bg-emerald-50 text-emerald-600 font-bold text-[9px] uppercase rounded-full px-2 py-0.5">Active</Tag>
               )}
            </div>
            <Text className="text-slate-400 font-medium text-xs uppercase tracking-wider">
              {candidate?.current_title || 'No Title'} • {candidate?.current_company || 'Independent'}
            </Text>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button icon={<X className="h-4 w-4" />} onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg border-slate-200" />
          <Button type="primary" className="h-9 font-bold px-4 rounded-lg bg-blue-600 border-none shadow-soft-sm">Edit Candidate</Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Quick Actions */}
        <div className="px-6 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
           <Text className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Quick Actions</Text>
           <div className="flex gap-2">
              <Button
                size="small"
                icon={<ArrowUpRight className="h-3 w-3" />}
                className="text-[10px] font-bold uppercase h-7 rounded-lg"
                onClick={() => navigate(`/candidates/pipeline?candidate_id=${candidateId}`)}
              >
                View in Pipeline
              </Button>
              <Button
                size="small"
                icon={<Plus className="h-3 w-3" />}
                className="text-[10px] font-bold uppercase h-7 rounded-lg"
                onClick={onAddNote}
              >
                Add Note
              </Button>
              <Button
                size="small"
                type="primary"
                icon={<Calendar className="h-3 w-3" />}
                className="text-[10px] font-bold uppercase h-7 rounded-lg bg-blue-600 border-none"
                onClick={onScheduleInterview}
              >
                Schedule Interview
              </Button>
           </div>
        </div>

        <Tabs 
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems} 
          className="detail-tabs"
          tabBarStyle={{ padding: '0 24px', marginBottom: 0, borderBottom: '1px solid #f1f5f9' }}
        />
      </div>
    </div>
  )
}

// ─── CRM Components ───────────────────────────────────────────────────────────

const CandidateCRMCards = ({ candidate, index, onLogInteraction }: any) => {
  const daysInStage = candidate?.updated_at ? dayjs().diff(dayjs(candidate.updated_at), 'day') : 0
  const isOverdue = candidate?.next_action_due && dayjs(candidate.next_action_due).isBefore(dayjs())

  return (
    <Draggable draggableId={candidate.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className="mb-3"
        >
          <Card
            bordered={false}
            className={cn(
              "shadow-soft-sm rounded-2xl border border-transparent hover:border-blue-200 transition-all",
              snapshot.isDragging ? "rotate-2 scale-105 shadow-soft-lg border-blue-300" : ""
            )}
            styles={{ body: { padding: '12px' } }}
          >
            <div className="flex items-center gap-3 mb-3">
              <Avatar className="bg-blue-100 text-blue-600 font-bold">
                {candidate?.full_name?.charAt(0).toUpperCase() || '?'}
              </Avatar>
              <div className="min-w-0">
                <Text className="block font-bold text-slate-900 text-sm leading-tight truncate">{candidate?.full_name || 'Unnamed'}</Text>
                <Text className="text-[10px] text-slate-400 font-medium truncate">{candidate?.current_title || 'No Title'}</Text>
              </div>
            </div>

            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase">
                <Clock className="h-3 w-3" /> {daysInStage} Days
              </div>
              {candidate?.next_action_due && (
                <div className={cn("text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tighter", isOverdue ? "bg-rose-50 text-rose-600" : "bg-slate-50 text-slate-500")}>
                  Next: {dayjs(candidate.next_action_due).format('MMM D')}
                </div>
              )}
            </div>

            <div className="flex gap-1 pt-2 border-t border-slate-50">
              <Button type="text" size="small" icon={<Phone className="h-3.5 w-3.5" />} className="flex-1 text-slate-400 hover:text-blue-600" onClick={(e) => { e.stopPropagation(); onLogInteraction(candidate, 'call') }} />
              <Button type="text" size="small" icon={<Mail className="h-3.5 w-3.5" />} className="flex-1 text-slate-400 hover:text-blue-600" onClick={(e) => { e.stopPropagation(); onLogInteraction(candidate, 'email') }} />
              <Button type="text" size="small" icon={<MessageSquare className="h-3.5 w-3.5" />} className="flex-1 text-slate-400 hover:text-blue-600" onClick={(e) => { e.stopPropagation(); onLogInteraction(candidate, 'note') }} />
            </div>
          </Card>
        </div>
      )}
    </Draggable>
  )
}

// ─── Main CandidatesList ──────────────────────────────────────────────────────

export default function CandidatesList() {
  const [view, setView] = useState<'pool' | 'crm' | 'analytics'>('pool')
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)

  // Interactions (CRM drawer)
  const [interactionCandidate, setInteractionCandidate] = useState<any>(null)
  const [interactionType, setInteractionType] = useState<string>('note')

  // Modals
  const [importModal, setImportModal] = useState(false)
  const [importToken, setImportToken] = useState('')
  const [addNoteModal, setAddNoteModal] = useState(false)
  const [scheduleModal, setScheduleModal] = useState(false)
  
  const { data, isLoading, refetch } = useApiQuery(
    ['candidates', search, sourceFilter],
    () => candidatesApi.list({ 
      search: search || undefined,
      source: sourceFilter || undefined
    })
  )

  const { data: pipelineData, isLoading: pipelineLoading } = useApiQuery(
    ['crm-pipeline'],
    () => candidatesApi.crmPipeline()
  )

  const candidates = (data as { candidates: Candidate[] } | undefined)?.candidates ?? []
  const crmData = (pipelineData as Record<string, any[]> | undefined) || {}

  const handleDragEnd = async (result: any) => {
    const { source, destination, draggableId } = result
    if (!destination || (source.droppableId === destination.droppableId)) return
    
    try {
      await http.put(`/crm/pipeline/${draggableId}/move/`, { status: destination.droppableId })
      message.success('Candidate moved')
      refetch()
    } catch {
      message.error('Failed to move candidate')
    }
  }

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col -m-6">
      {/* Header & View Switcher */}
      {!selectedCandidate && (
        <div className="p-6 pb-0 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-none">Candidates</h1>
            <p className="text-slate-500 mt-2 font-medium">Your centralized talent database and recruitment CRM.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Segmented
              value={view}
              onChange={(v: any) => setView(v)}
              className="p-1 bg-slate-100 rounded-xl"
              options={[
                { label: 'Talent Pool', value: 'pool', icon: <ListIcon className="h-4 w-4" /> },
                { label: 'CRM Kanban', value: 'crm', icon: <LayoutGrid className="h-4 w-4" /> },
                { label: 'Analytics', value: 'analytics', icon: <BarChart3 className="h-4 w-4" /> },
              ]}
            />
            <Button icon={<Import className="h-4 w-4" />} className="h-10 rounded-xl font-bold" onClick={() => setImportModal(true)}>Import</Button>
            <Button type="primary" icon={<Plus className="h-4 w-4" />} className="h-10 rounded-xl font-bold bg-blue-600 border-none shadow-soft-md">Add Candidate</Button>
          </div>
        </div>
      )}

      {/* Toolbar / Filters (Only for Pool view) */}
      {view === 'pool' && !selectedCandidate && (
        <div className="p-6 pb-4">
          <Card bordered={false} className="shadow-soft-sm bg-white/50 backdrop-blur-sm" styles={{ body: { padding: '12px' } }}>
            <Row gutter={[12, 12]} align="middle">
              <Col xs={24} md={12}>
                <Input
                  prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                  placeholder="Search candidates by name, email, skills or company..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-10 text-sm border-slate-200"
                  allowClear
                />
              </Col>
              <Col xs={12} md={6}>
                <Select
                  className="w-full h-10"
                  placeholder="Filter by Source"
                  value={sourceFilter}
                  onChange={setSourceFilter}
                  allowClear
                  options={[
                    { value: 'linkedin', label: 'LinkedIn' },
                    { value: 'agency', label: 'Agency' },
                    { value: 'referral', label: 'Referral' },
                    { value: 'job_board', label: 'Job Board' },
                    { value: 'passport', label: 'Talent Passport' },
                    { value: 'self', label: 'Self Registered' },
                  ]}
                />
              </Col>
              <Col xs={12} md={6}>
                <Button
                  icon={<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />}
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

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {view === 'pool' ? (
          <StandardSplitView
            isDetailOpen={!!selectedCandidate}
            compactListContent={
              <CompressedCandidateList
                candidates={candidates}
                selectedCandidateId={selectedCandidate?.id}
                onSelect={setSelectedCandidate}
              />
            }
            fullListContent={
              <div className="p-6 pt-0 h-full overflow-y-auto">
                <Tabs
                  defaultActiveKey="database"
                  className="modern-tabs mb-6"
                  items={[
                    {
                      key: 'database',
                      label: 'Candidate Database',
                      children: (
                        <Card bordered={false} className="shadow-soft-sm overflow-hidden p-0 border border-slate-100">
                          <FullCandidateList
                            candidates={candidates}
                            onSelect={setSelectedCandidate}
                            isLoading={isLoading}
                          />
                        </Card>
                      ),
                    },
                    { key: 'apps', label: 'All Applications', children: <AllApplications /> },
                  ]}
                />
              </div>
            }
            detailContent={
              selectedCandidate ? (
                <CandidateDetailPanel
                  candidate={selectedCandidate}
                  onClose={() => setSelectedCandidate(null)}
                  onAddNote={() => setAddNoteModal(true)}
                  onScheduleInterview={() => setScheduleModal(true)}
                />
              ) : null
            }
          />
        ) : view === 'crm' ? (
          <div className="p-6 h-full overflow-hidden">
            {pipelineLoading ? <div className="h-full flex items-center justify-center"><Spin size="large" /></div> : (
              <DragDropContext onDragEnd={handleDragEnd}>
                <div className="flex gap-6 h-full overflow-x-auto pb-4 items-start scrollbar-hide">
                  {CRM_STAGES.map((stage) => (
                    <div key={stage.key} className="flex flex-col w-72 shrink-0 h-full bg-slate-50/50 rounded-2xl border border-slate-200 shadow-soft-sm">
                      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{stage.icon}</span>
                          <span className="font-bold text-slate-900 text-sm tracking-tight">{stage.label}</span>
                        </div>
                        <Badge count={crmData[stage.key]?.length || 0} className="site-badge-count-4" style={{ backgroundColor: '#f1f5f9', color: '#64748b', boxShadow: 'none', border: '1px solid #e2e8f0' }} />
                      </div>
                      
                      <Droppable droppableId={stage.key}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={cn("flex-1 p-3 overflow-y-auto", snapshot.isDraggingOver ? "bg-blue-50/30" : "")}
                          >
                            {crmData[stage.key]?.length > 0 ? crmData[stage.key].map((cand: any, i: number) => (
                              <CandidateCRMCards 
                                key={cand.id} 
                                candidate={cand} 
                                index={i} 
                                onLogInteraction={(c: any, type: string) => {
                                  setInteractionCandidate(c)
                                  setInteractionType(type)
                                }}
                              />
                            )) : (
                              <div className="h-24 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl">
                                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">No candidates</span>
                              </div>
                            )}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  ))}
                </div>
              </DragDropContext>
            )}
          </div>
        ) : (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2">
              <TrendingUp className="h-5 w-5 text-blue-600 mb-2" />
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pipeline Health</Text>
              <Title level={3} className="!m-0">Healthy</Title>
            </Card>
            <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2">
              <Clock className="h-5 w-5 text-amber-600 mb-2" />
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Avg. Time in Stage</Text>
              <Title level={3} className="!m-0">4.2 Days</Title>
            </Card>
            <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2">
              <UserPlus className="h-5 w-5 text-emerald-600 mb-2" />
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Lead → Hire Rate</Text>
              <Title level={3} className="!m-0">12.5%</Title>
            </Card>
            <Card bordered={false} className="shadow-soft-sm rounded-2xl p-2">
              <ExternalLink className="h-5 w-5 text-purple-600 mb-2" />
              <Text className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Top Source</Text>
              <Title level={3} className="!m-0">Referral</Title>
            </Card>
          </div>
        )}
      </div>

      {/* ── Drawers & Modals ──────────────────────────────────────────────── */}

      <CandidateInteractionDrawer
        candidate={interactionCandidate}
        initialType={interactionType}
        onClose={() => setInteractionCandidate(null)}
      />

      {selectedCandidate && (
        <AddNoteModal
          candidateId={selectedCandidate.id}
          open={addNoteModal}
          onClose={() => setAddNoteModal(false)}
        />
      )}

      {selectedCandidate && (
        <ScheduleInterviewModal
          candidateId={selectedCandidate.id}
          open={scheduleModal}
          onClose={() => setScheduleModal(false)}
        />
      )}

      <Modal
        title={<span className="text-lg font-bold text-slate-900">Import from Passport</span>}
        open={importModal}
        onCancel={() => setImportModal(false)}
        onOk={() => message.info('Passport imported')}
        okText="Import Profile"
        className="rounded-2xl"
      >
        <p className="text-slate-500 mb-4 text-sm font-medium">Enter the unique share token provided by the candidate from their RecruitOS Passport.</p>
        <Input placeholder="PAS-XXXX-XXXX" className="h-11 rounded-xl" value={importToken} onChange={e => setImportToken(e.target.value)} />
      </Modal>
    </div>
  )
}
