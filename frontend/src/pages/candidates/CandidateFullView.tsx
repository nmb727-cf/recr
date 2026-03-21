import { useState } from 'react'
import {
  Button, Card, Tag, Descriptions,
  Typography, Spin, Empty, Tabs, Avatar,
  Popconfirm, message, Skeleton, List
} from 'antd'
import {
  Edit, Mail, Phone,
  Linkedin, MapPin, Activity,
  Trash2, Plus, MessageSquare
} from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import type { CandidateDetail, CandidateNote, TimelineEvent } from '@/types'

dayjs.extend(relativeTime)
const { Text, Paragraph } = Typography

// ─── Tabs ───────────────────────────────────────────────────────────────────

function ProfileTab({ candidate }: { candidate: CandidateDetail }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title={<span className="text-sm font-bold text-slate-900">Quick Stats</span>} bordered={false} className="shadow-soft-sm">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Experience">{parseFloat(candidate.experience_years)} years</Descriptions.Item>
            <Descriptions.Item label="Notice Period">{candidate.notice_period_days} days</Descriptions.Item>
            <Descriptions.Item label="Source">{candidate.source || 'Direct'}</Descriptions.Item>
            <Descriptions.Item label="Added">{dayjs(candidate.created_at).format('MMM D, YYYY')}</Descriptions.Item>
          </Descriptions>
        </Card>
        
        <Card title={<span className="text-sm font-bold text-slate-900">Contact Information</span>} bordered={false} className="shadow-soft-sm md:col-span-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 text-slate-600 text-sm">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="font-medium truncate">{candidate.email}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600 text-sm">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="font-medium">{candidate.phone || 'No phone provided'}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600 text-sm">
              <MapPin className="h-4 w-4 text-slate-400" />
              <span className="font-medium">
                {[candidate.current_location_city, candidate.current_location_country].filter(Boolean).join(', ') || 'Remote'}
              </span>
            </div>
            {candidate.linkedin_url && (
              <div className="flex items-center gap-3 text-slate-600 text-sm">
                <Linkedin className="h-4 w-4 text-slate-400" />
                <a href={candidate.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-600 font-medium hover:underline">
                  LinkedIn Profile
                </a>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card title={<span className="text-base font-bold text-slate-900">Professional Summary</span>} bordered={false} className="shadow-soft-sm">
        <Paragraph className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">
          {candidate.profile?.summary || 'No summary provided.'}
        </Paragraph>
      </Card>

      <Card title={<span className="text-base font-bold text-slate-900">Skills</span>} bordered={false} className="shadow-soft-sm">
        <div className="flex flex-wrap gap-2">
          {candidate.skills?.map(skill => (
            <Tag key={skill} className="m-0 border-none bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-lg">
              {skill}
            </Tag>
          ))}
          {(!candidate.skills || candidate.skills.length === 0) && (
            <Text className="italic text-slate-400 text-sm">No skills listed.</Text>
          )}
        </div>
      </Card>
    </div>
  )
}

function NotesTab({ candidateId }: { candidateId: string }) {
  const { data, isLoading, refetch } = useApiQuery(['candidate-notes-full', candidateId], () => 
    candidatesApi.listNotes(candidateId)
  )
  const notes = (data as any)?.notes ?? []

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
        extra={<Button type="primary" size="small" icon={<Plus className="h-3 w-3" />} className="bg-blue-600 border-none rounded-md font-bold">Add Note</Button>}
        bordered={false} 
        className="shadow-soft-sm"
      >
        <List
          loading={isLoading}
          dataSource={notes}
          renderItem={(note: CandidateNote) => (
            <div key={note.id} className="group flex gap-4 py-6 border-b border-slate-100 last:border-0">
              <Avatar className="bg-slate-200 text-slate-600 shrink-0 font-bold">U</Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">Recruiter Name</span>
                    <Tag className="m-0 text-[10px] uppercase font-bold border-none bg-slate-100 text-slate-500">{note.note_type}</Tag>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">{dayjs(note.created_at).fromNow()}</span>
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
        <div className="space-y-8 py-4">
          {events.map((e: TimelineEvent, i: number) => (
            <div key={i} className="flex gap-4">
              <div className="relative flex flex-col items-center">
                <div className="h-10 w-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 z-10 border border-blue-100 shadow-sm">
                  <Activity className="h-5 w-5" />
                </div>
                {i < events.length - 1 && <div className="w-[2px] bg-slate-100 absolute top-10 bottom-[-32px]" />}
              </div>
              <div className="pt-2">
                <div className="flex items-center gap-2 mb-1">
                  <Tag className="m-0 text-[10px] font-bold uppercase border-none bg-slate-100 text-slate-500">{e.note_type || e.type}</Tag>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">{dayjs(e.created_at).format('MMM D, YYYY · HH:mm')}</span>
                </div>
                <p className="text-sm text-slate-700 font-semibold leading-relaxed">{e.text}</p>
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

export default function CandidateFullView({ candidateId }: { candidateId: string }) {
  const [activeTab, setActiveTab] = useState('profile')

  const { data, isLoading } = useApiQuery(
    ['candidate', 'full', candidateId],
    () => candidatesApi.get(candidateId)
  )

  const candidate = (data as any)?.candidate as CandidateDetail

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!candidate) return <Empty description="Candidate not found" />

  return (
    <div className="space-y-8">
      {/* Header Profile Info */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
        <div className="flex items-start gap-5">
          <Avatar 
            size={80} 
            className="bg-blue-600 text-white font-bold text-3xl shadow-soft-lg shrink-0 border-4 border-white"
          >
            {candidate.full_name?.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              {candidate.is_actively_looking && (
                <Tag color="success" className="m-0 rounded-full px-2.5 py-0.5 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase tracking-wider">
                  Actively Looking
                </Tag>
              )}
              <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded-full px-2.5 tracking-wider">
                {candidate.source || 'Direct'}
              </Tag>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-tight">
              {candidate.full_name}
            </h1>
            <p className="text-slate-500 mt-1 flex items-center gap-2 text-base font-medium">
              {candidate.current_title || 'No Title'} {candidate.current_company ? `at ${candidate.current_company}` : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl border-slate-200" icon={<MessageSquare className="h-4 w-4" />}>
            Message
          </Button>
          <Button type="primary" icon={<Edit className="h-4 w-4" />} className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl bg-blue-600 border-none shadow-soft-md">
            Edit Profile
          </Button>
        </div>
      </div>

      {/* Tabs Content */}
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
            children: <NotesTab candidateId={candidateId} />
          },
          {
            key: 'activity',
            label: 'Activity',
            children: <ActivityTab candidateId={candidateId} />
          },
          {
            key: 'applications',
            label: 'Applications',
            children: (
              <Card bordered={false} className="shadow-soft-sm">
                <Empty description="Applications history view coming soon" />
              </Card>
            )
          }
        ]}
      />
    </div>
  )
}
