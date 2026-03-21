import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Tag,
  Typography, Spin, Empty, Tabs, Table, Avatar,
  Timeline
} from 'antd'
import {
  ArrowLeft, Mail, Phone,
  CheckCircle, Star, X, DollarSign, Plus
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { interviewsApi } from '@/api/interviews'
import type { Application, Candidate } from '@/types'

const { Text } = Typography

// ─── Tabs ───────────────────────────────────────────────────────────────────

function ApplicationOverview({ application, candidate }: { application: Application, candidate: Candidate }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Candidate Details" bordered={false} className="shadow-soft-sm">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 text-slate-600">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium truncate">{candidate?.email}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium">{candidate?.phone || 'N/A'}</span>
            </div>
            <Button block className="mt-2 font-semibold" onClick={() => window.open(candidate?.linkedin_url, '_blank')}>
              View Resume
            </Button>
          </div>
        </Card>
        
        <Card title="Match Analysis" bordered={false} className="shadow-soft-sm md:col-span-2">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600">{application.match_score}%</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase mt-1">AI Score</div>
            </div>
            <div className="h-12 w-[1px] bg-slate-100" />
            <div className="flex-1">
              <p className="text-sm text-slate-600 leading-relaxed">
                Candidate's profile matches 85% of the core technical requirements and 90% of the preferred skills for this role.
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Stage History" bordered={false} className="shadow-soft-sm">
        <Timeline 
          items={[
            {
              dot: <CheckCircle className="h-4 w-4 text-blue-600" />,
              children: (
                <div className="pb-4">
                  <Text strong className="text-slate-900">Moved to Screening</Text>
                  <p className="text-xs text-slate-400 mb-1">Yesterday at 14:20 by Nirav</p>
                  <p className="text-sm text-slate-600 italic">"Initial screening looks promising. Good communication skills."</p>
                </div>
              )
            },
            {
              dot: <div className="h-4 w-4 rounded-full bg-slate-200" />,
              children: (
                <div>
                  <Text strong className="text-slate-900">Applied</Text>
                  <p className="text-xs text-slate-400">3 days ago at 09:12</p>
                </div>
              )
            }
          ]}
        />
      </Card>
    </div>
  )
}

function ApplicationInterviews({ applicationId }: { applicationId: string }) {
  const { data, isLoading } = useApiQuery(['app-interviews', applicationId], () => 
    interviewsApi.list({ application_id: applicationId })
  )
  const interviews = (data as any)?.interviews ?? []

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Button type="primary" icon={<Plus className="h-4 w-4" />}>Schedule Interview</Button>
      </div>
      <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
        <Table 
          dataSource={interviews} 
          rowKey="id" 
          loading={isLoading}
          columns={[
            { title: 'Title', dataIndex: 'title', key: 'title', render: (t) => <Text strong>{t}</Text> },
            { title: 'Round', dataIndex: 'interview_round', key: 'round' },
            { title: 'Date', dataIndex: 'scheduled_at', key: 'date', render: (d) => dayjs(d).format('MMM D, HH:mm') },
            { title: 'Status', dataIndex: 'status', key: 'status', render: (s) => <Tag color="blue">{s}</Tag> }
          ]}
        />
      </Card>
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')

  const { data, isLoading } = useApiQuery(
    ['application', id],
    () => pipelineApi.getApplication(id!)
  )

  const application = (data as any)?.application as Application
  
  const { data: candidateData } = useApiQuery(
    ['candidate', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id),
    { enabled: !!application?.candidate_id }
  )

  const candidate = (candidateData as any)?.candidate as Candidate

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!application) return <Empty description="Application not found" />

  return (
    <div className="space-y-6">
      <Button 
        type="text" 
        icon={<ArrowLeft className="h-4 w-4" />} 
        className="flex items-center gap-2 text-slate-500 font-medium hover:text-slate-900 w-fit p-0"
        onClick={() => navigate(-1)}
      >
        Go Back
      </Button>

      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="flex items-start gap-4">
          <Avatar 
            size={64} 
            className="bg-blue-100 text-blue-600 font-bold text-2xl shadow-soft-sm shrink-0"
          >
            {candidate?.full_name?.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <Tag className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase rounded-full px-2.5">
                {application.match_score}% Match
              </Tag>
              <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase rounded-full px-2.5">
                {application.status.replace(/_/g, ' ')}
              </Tag>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-tight">
              {candidate?.full_name}
            </h1>
            <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm font-medium">
              Applied for <Text strong>Senior Backend Engineer</Text> · {dayjs(application.created_at).fromNow()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button className="h-10 flex items-center gap-2 font-semibold" icon={<Star className="h-4 w-4" />}>
            Shortlist
          </Button>
          <Button type="primary" danger className="h-10 flex items-center gap-2 font-semibold" icon={<X className="h-4 w-4" />}>
            Reject
          </Button>
        </div>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="modern-tabs"
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: <ApplicationOverview application={application} candidate={candidate!} />
          },
          {
            key: 'interviews',
            label: 'Interviews',
            children: <ApplicationInterviews applicationId={id!} />
          },
          {
            key: 'offers',
            label: 'Offers',
            children: (
              <Card bordered={false} className="shadow-soft-sm">
                <Empty description="No offers extended yet" image={<DollarSign className="h-12 w-12 text-slate-200 mx-auto mb-4" />} />
              </Card>
            )
          }
        ]}
      />
    </div>
  )
}
