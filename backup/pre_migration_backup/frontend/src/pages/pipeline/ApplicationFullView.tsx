import { useState } from 'react'
import {
  Button, Card, Tag,
  Typography, Spin, Empty, Tabs, Table, Avatar, Timeline
} from 'antd'
import {
  Mail, Phone,
  FileText, CheckCircle,
  Star, X, DollarSign,
  Plus
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
        <Card title={<span className="text-sm font-bold text-slate-900">Candidate Info</span>} bordered={false} className="shadow-soft-sm">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 text-slate-600 text-sm">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="font-medium truncate">{candidate?.email}</span>
            </div>
            <div className="flex items-center gap-3 text-slate-600 text-sm">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="font-medium">{candidate?.phone || 'N/A'}</span>
            </div>
            <Button block className="mt-2 font-bold rounded-lg h-10 border-slate-200" onClick={() => window.open(candidate?.linkedin_url, '_blank')}>
              View Resume
            </Button>
          </div>
        </Card>
        
        <Card title={<span className="text-sm font-bold text-slate-900">Match Analysis</span>} bordered={false} className="shadow-soft-sm md:col-span-2">
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="text-4xl font-black text-emerald-600 tracking-tight">{application.match_score || 0}%</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase mt-1 tracking-widest">AI Match</div>
            </div>
            <div className="h-14 w-[1px] bg-slate-100" />
            <div className="flex-1">
              <p className="text-sm text-slate-600 leading-relaxed font-medium">
                The candidate's technical profile strongly aligns with the requisition requirements, particularly in React and Python ecosystems.
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card title={<span className="text-base font-bold text-slate-900">Hiring Journey</span>} bordered={false} className="shadow-soft-sm">
        <div className="py-2">
          <Timeline 
            items={[
              {
                dot: <div className="h-10 w-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100"><CheckCircle className="h-5 w-5" /></div>,
                children: (
                  <div className="pb-8 ml-2">
                    <Text strong className="text-base text-slate-900">Moved to Screening</Text>
                    <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">Yesterday at 14:20 · BY NIRAV</p>
                    <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-sm text-slate-600 italic">"Initial screening looks promising. Good communication skills and cultural fit."</p>
                    </div>
                  </div>
                )
              },
              {
                dot: <div className="h-10 w-10 rounded-full bg-slate-50 text-slate-400 flex items-center justify-center border border-slate-100"><FileText className="h-5 w-5" /></div>,
                children: (
                  <div className="ml-2">
                    <Text strong className="text-base text-slate-900">Application Submitted</Text>
                    <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">{dayjs(application.created_at).format('MMM D, YYYY · HH:mm')}</p>
                  </div>
                )
              }
            ]}
          />
        </div>
      </Card>
    </div>
  )
}

function ApplicationInterviews({ applicationId }: { applicationId: string }) {
  const { data, isLoading } = useApiQuery(['app-interviews-full', applicationId], () => 
    interviewsApi.list({ application_id: applicationId })
  )
  const interviews = (data as any)?.interviews ?? []

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Button type="primary" icon={<Plus className="h-4 w-4" />} className="bg-blue-600 border-none rounded-xl font-bold h-10 px-6">Schedule Interview</Button>
      </div>
      <Card bordered={false} className="shadow-soft-sm p-0 overflow-hidden">
        <Table 
          dataSource={interviews} 
          rowKey="id" 
          loading={isLoading}
          pagination={false}
          columns={[
            { title: 'Title', dataIndex: 'title', key: 'title', render: (t) => <Text className="font-bold text-slate-900">{t}</Text> },
            { title: 'Round', dataIndex: 'interview_round', key: 'round', align: 'center' as const },
            { title: 'Date', dataIndex: 'scheduled_at', key: 'date', render: (d) => <span className="text-slate-500 font-medium">{dayjs(d).format('MMM D, HH:mm')}</span> },
            { title: 'Status', dataIndex: 'status', key: 'status', render: (s) => <Tag color="blue" className="rounded-full font-bold text-[10px] uppercase border-none px-2.5">{s}</Tag> }
          ]}
          className="modern-table"
        />
      </Card>
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ApplicationFullView({ applicationId }: { applicationId: string }) {
  const [activeTab, setActiveTab] = useState('overview')

  const { data, isLoading } = useApiQuery(
    ['application', 'full', applicationId],
    () => pipelineApi.getApplication(applicationId)
  )

  const application = (data as any)?.application as Application
  
  const { data: candidateData } = useApiQuery(
    ['candidate', 'full', application?.candidate_id],
    () => candidatesApi.get(application?.candidate_id),
    { enabled: !!application?.candidate_id }
  )

  const candidate = (candidateData as any)?.candidate as Candidate

  if (isLoading) return <div className="flex items-center justify-center min-h-[400px]"><Spin size="large" /></div>
  if (!application) return <Empty description="Application not found" />

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
        <div className="flex items-start gap-5">
          <Avatar 
            size={80} 
            className="bg-blue-600 text-white font-bold text-3xl shadow-soft-lg shrink-0 border-4 border-white"
          >
            {candidate?.full_name?.charAt(0).toUpperCase() || 'C'}
          </Avatar>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Tag className="m-0 border-none bg-emerald-50 text-emerald-700 font-bold text-[10px] uppercase rounded-full px-3 tracking-wider">
                {application.match_score || 0}% Match
              </Tag>
              <Tag className="m-0 border-none bg-blue-50 text-blue-700 font-bold text-[10px] uppercase rounded-full px-3 tracking-wider">
                {application.status.replace(/_/g, ' ')}
              </Tag>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight leading-tight">
              {candidate?.full_name || 'Unnamed Candidate'}
            </h1>
            <p className="text-slate-500 mt-1 flex items-center gap-2 text-base font-medium">
              Applied for <Text strong className="text-slate-700 underline decoration-blue-200 decoration-2 underline-offset-4">Senior Backend Engineer</Text> · {dayjs(application.created_at).fromNow().toUpperCase()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl border-slate-200 text-emerald-700" icon={<Star className="h-4 w-4" />}>
            Shortlist
          </Button>
          <Button type="primary" danger className="h-11 px-6 flex items-center gap-2 font-bold rounded-xl bg-rose-600 border-none shadow-soft-md" icon={<X className="h-4 w-4" />}>
            Reject Application
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
            label: 'Journey Overview',
            children: <ApplicationOverview application={application} candidate={candidate!} />
          },
          {
            key: 'interviews',
            label: 'Interviews',
            children: <ApplicationInterviews applicationId={applicationId} />
          },
          {
            key: 'offers',
            label: 'Offer Management',
            children: (
              <Card bordered={false} className="shadow-soft-sm py-12">
                <Empty description={<span className="font-medium text-slate-400">No offers extended yet</span>} image={<DollarSign className="h-12 w-12 text-slate-200 mx-auto mb-4" />} />
              </Card>
            )
          }
        ]}
      />
    </div>
  )
}
