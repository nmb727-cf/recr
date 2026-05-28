import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Descriptions, Tag,
  Typography, Spin, Empty, Tabs, Avatar,
  Popconfirm, message, Skeleton, Modal, Form, Input, Select
} from 'antd'
import {
  ArrowLeft, Edit, Mail, Phone,
  Linkedin, MapPin, Activity,
  Trash2, Plus, MessageSquare,
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import type { CandidateDetail, CandidateNote, TimelineEvent } from '@/types'
import WorkflowStatusPanel from '@/components/workflow/WorkflowStatusPanel'

dayjs.extend(relativeTime)
const { Text, Paragraph } = Typography

// ─── Tabs ───────────────────────────────────────────────────────────────────

function ProfileTab({ candidate }: { candidate: CandidateDetail }) {
  const experienceYears = Number(candidate.experience_years)
  const displayExperience = Number.isFinite(experienceYears) ? `${experienceYears} years` : 'Not specified'
  const displayNotice = candidate.notice_period_days != null ? `${candidate.notice_period_days} days` : 'Not specified'

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Quick Stats" bordered={false} className="shadow-soft-sm">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Experience">{displayExperience}</Descriptions.Item>
            <Descriptions.Item label="Notice Period">{displayNotice}</Descriptions.Item>
            <Descriptions.Item label="Source">{candidate.source || 'Direct'}</Descriptions.Item>
            <Descriptions.Item label="Added">{dayjs(candidate.created_at).format('MMM D, YYYY')}</Descriptions.Item>
          </Descriptions>
        </Card>
        
        <Card title="Contact Information" bordered={false} className="shadow-soft-sm md:col-span-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 text-slate-600">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">{candidate.email}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">{candidate.phone || 'No phone provided'}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600">
              <MapPin className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">
                {[candidate.current_location_city, candidate.current_location_country].filter(Boolean).join(', ') || 'Remote'}
              </span>
            </div>
            {candidate.linkedin_url && (
              <div className="flex items-center gap-3 text-slate-600">
                <Linkedin className="h-4 w-4 text-slate-400" />
                <a href={candidate.linkedin_url} target="_blank" rel="noreferrer" className="text-sm text-blue-600 font-medium hover:underline">
                  LinkedIn Profile
                </a>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card title="Professional Summary" bordered={false} className="shadow-soft-sm">
        <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap">
          {candidate.profile?.summary || 'No summary provided.'}
        </Paragraph>
      </Card>

      <Card title="Skills" bordered={false} className="shadow-soft-sm">
        <div className="flex flex-wrap gap-2">
          {candidate.skills?.map(skill => (
            <Tag key={skill} className="m-0 border-none bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-lg">
              {skill}
            </Tag>
          ))}
          {(!candidate.skills || candidate.skills.length === 0) && (
            <Text className="italic text-slate-400">No skills listed.</Text>
          )}
        </div>
      </Card>
    </div>
  )
}

function NotesTab({ candidateId }: { candidateId: string }) {
  const [createOpen, setCreateOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm()
  const { data, isLoading, refetch } = useApiQuery(['candidate-notes-full', candidateId], () =>
    candidatesApi.listNotes(candidateId)
  )
  const notes = (data as any)?.notes ?? []

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      await candidatesApi.addNote(candidateId, {
        note_text: values.note_text,
        note_type: values.note_type || 'general',
      })
      message.success('Note added')
      setCreateOpen(false)
      form.resetFields()
      refetch()
    } catch (err: any) {
      if (err?.errorFields) return
      message.error(err?.response?.data?.message || 'Failed to add note')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (noteId: string) => {
    try {
      await candidatesApi.deleteNote(candidateId, noteId)
      message.success('Note deleted')
      refetch()
    } catch {
      message.error('Failed to delete note')
    }
  }

  return (
    <div className="space-y-6">
      <Card 
        title={<span className="text-lg font-bold text-slate-900">Team Notes</span>} 
        extra={
          <Button
            type="primary"
            size="small"
            icon={<Plus className="h-3 w-3" />}
            onClick={() => setCreateOpen(true)}
          >
            Add Note
          </Button>
        }
        bordered={false} 
        className="shadow-soft-sm"
      >
        <List
          loading={isLoading}
          dataSource={notes}
          renderItem={(note: CandidateNote) => (
            <div key={note.id} className="group flex gap-4 py-6 border-b border-slate-100 last:border-0">
              <Avatar className="bg-slate-200 text-slate-600 shrink-0">U</Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">Recruiter Name</span>
                    <Tag className="m-0 text-[10px] uppercase font-bold border-none bg-slate-100">{note.note_type}</Tag>
                    <span className="text-xs text-slate-400 font-medium">{dayjs(note.created_at).fromNow()}</span>
                  </div>
                  <Popconfirm title="Delete note?" onConfirm={() => handleDelete(note.id)}>
                    <Button type="text" size="small" danger icon={<Trash2 className="h-4 w-4" />} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Popconfirm>
                </div>
                <Paragraph className="text-sm text-slate-600 leading-relaxed m-0 whitespace-pre-wrap">
                  {note.note_text}
                </Paragraph>
              </div>
            </div>
          )}
        />
      </Card>

      <Modal
        title="Add Note"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
        confirmLoading={submitting}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ note_type: 'general' }}
        >
          <Form.Item name="note_type" label="Type">
            <Select
              options={[
                { value: 'general', label: 'General' },
                { value: 'interview', label: 'Interview' },
                { value: 'screening', label: 'Screening' },
                { value: 'offer', label: 'Offer' },
                { value: 'feedback', label: 'Feedback' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="note_text"
            label="Note"
            rules={[{ required: true, message: 'Please enter a note' }]}
          >
            <Input.TextArea rows={4} placeholder="Write a note..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function ActivityTab({ candidateId }: { candidateId: string }) {
  const { data, isLoading } = useApiQuery(['candidate-timeline-full', candidateId], () => 
    candidatesApi.timeline(candidateId)
  )
  const events = (data as any)?.events ?? []

  return (
    <Card bordered={false} className="shadow-soft-sm">
      {isLoading ? <Skeleton active /> : (
        <div className="space-y-8">
          {events.map((e: TimelineEvent, i: number) => (
            <div key={i} className="flex gap-4">
              <div className="relative flex flex-col items-center">
                <div className="h-10 w-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 z-10">
                  <Activity className="h-5 w-5" />
                </div>
                {i < events.length - 1 && <div className="w-[2px] bg-slate-100 absolute top-10 bottom-[-32px]" />}
              </div>
              <div className="pt-2">
                <div className="flex items-center gap-2 mb-1">
                  <Tag className="m-0 text-[10px] font-bold uppercase border-none bg-slate-100">{e.note_type || e.type}</Tag>
                  <span className="text-xs text-slate-400 font-medium">{dayjs(e.created_at).format('MMM D, YYYY HH:mm')}</span>
                </div>
                <p className="text-sm text-slate-700 font-medium leading-relaxed">{e.text}</p>
              </div>
            </div>
          ))}
          {events.length === 0 && <Empty description="No activity found" />}
        </div>
      )}
    </Card>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

import { List } from 'antd'

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('profile')

  const { data, isLoading } = useApiQuery(
    ['candidate', id],
    () => candidatesApi.get(id!)
  )

  const candidate = (data as any)?.candidate as CandidateDetail

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!candidate) return <Empty description="Candidate not found" />

  return (
    <div className="space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col gap-6">
        <Button 
          type="text" 
          icon={<ArrowLeft className="h-4 w-4" />} 
          className="flex items-center gap-2 text-slate-500 font-medium hover:text-slate-900 w-fit p-0"
          onClick={() => navigate('/candidates')}
        >
          Back to Candidates
        </Button>

        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-start gap-4">
            <Avatar 
              size={64} 
              className="bg-blue-100 text-blue-600 font-bold text-2xl shadow-soft-sm shrink-0"
            >
              {candidate.full_name?.charAt(0).toUpperCase()}
            </Avatar>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                {candidate.is_actively_looking && (
                  <Tag color="success" className="m-0 rounded-full px-2.5 py-0.5 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase">
                    Actively Looking
                  </Tag>
                )}
                <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-full px-2.5">
                  {candidate.source || 'Direct'}
                </Tag>
              </div>
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-tight">
                {candidate.full_name}
              </h1>
              <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm font-medium">
                {candidate.current_title || 'No Title'} {candidate.current_company ? `at ${candidate.current_company}` : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button className="h-10 flex items-center gap-2 font-semibold" icon={<MessageSquare className="h-4 w-4" />}>
              Message
            </Button>
            <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-10 flex items-center gap-2 font-semibold">
              Edit Profile
            </Button>
          </div>
        </div>
      </div>

      <WorkflowStatusPanel
        entityId={candidate.id}
        title="Workflow Status"
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="modern-tabs"
        items={[
          {
            key: 'profile',
            label: 'Profile',
            children: <ProfileTab candidate={candidate} />
          },
          {
            key: 'notes',
            label: 'Notes',
            children: <NotesTab candidateId={id!} />
          },
          {
            key: 'activity',
            label: 'Activity',
            children: <ActivityTab candidateId={id!} />
          },
          {
            key: 'applications',
            label: 'Applications',
            children: (
              <Card bordered={false} className="shadow-soft-sm">
                <Empty description="Applications view coming soon" />
              </Card>
            )
          }
        ]}
      />
    </div>
  )
}
