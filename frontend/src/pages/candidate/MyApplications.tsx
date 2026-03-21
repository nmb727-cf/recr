import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Tag, Space, Typography, Card, Steps,
  Spin, Button,
} from 'antd'
import {
  SyncOutlined, ArrowRightOutlined,
  CalendarOutlined, SolutionOutlined,
} from '@ant-design/icons'
import { candidateApi } from '@/api/candidate'
import { requisitionsApi } from '@/api/jobs'
import type { JobRequisition, ApplicationStatus } from '@/types'
import { useDrawerStore } from '@/store/drawerStore'

const { Title, Text, Paragraph } = Typography

const STATUS_MAP: Record<ApplicationStatus, { label: string; color: string; step: number }> = {
  applied: { label: 'Applied', color: 'blue', step: 0 },
  screening: { label: 'Screening', color: 'cyan', step: 1 },
  shortlisted: { label: 'Shortlisted', color: 'geekblue', step: 2 },
  in_review: { label: 'In Review', color: 'orange', step: 2 },
  interview_scheduled: { label: 'Interview', color: 'purple', step: 3 },
  offer_extended: { label: 'Offer', color: 'gold', step: 4 },
  offer_accepted: { label: 'Accepted', color: 'green', step: 5 },
  rejected: { label: 'Rejected', color: 'red', step: -1 },
  withdrawn: { label: 'Withdrawn', color: 'default', step: -1 },
}

const STEPS = [
  { title: 'Applied' },
  { title: 'Screening' },
  { title: 'Shortlisted' },
  { title: 'Interview' },
  { title: 'Offer' },
  { title: 'Joined' },
]

// ─── Main MyApplications Component ───────────────────────────────────────────

export default function MyApplications() {
  const [applicationsWithJobs, setApplicationsWithJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const openQuickView = useDrawerStore(s => s.openQuickView)

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Step 1: fetch all applications
      const appsResponse = await candidateApi.listApplications()
      console.log('Applications API response:', appsResponse.data)
      
      const applications = appsResponse.data.data.applications || []
      console.log('First application:', applications[0])
      
      if (applications.length === 0) {
        setApplicationsWithJobs([])
        setLoading(false)
        return
      }
      
      // Step 2: get unique requisition IDs
      const uniqueReqIds = [...new Set(applications.map((a: any) => a.requisition_id).filter(Boolean))]
      
      // Step 3: fetch all requisitions in parallel
      const reqResponses = await Promise.all(
        uniqueReqIds.map(id => 
          requisitionsApi.get(id as string).catch((err) => {
            console.error(`Failed to fetch job ${id}:`, err)
            return null
          })
        )
      )
      console.log('Job response example:', reqResponses[0]?.data)
      
      // Step 4: build lookup map
      const jobMap: Record<string, JobRequisition> = {}
      reqResponses.forEach(res => {
        if (res?.data?.data?.requisition) {
          const req = res.data.data.requisition
          jobMap[req.id] = req
        }
      })
      
      // Step 5: combine applications with job data
      const combined = applications.map(app => {
        const job = jobMap[app.requisition_id]
        return {
          ...app,
          jobTitle: job?.title || 'Position',
          jobType: job?.job_type || '',
          workMode: job?.work_mode || '',
        }
      })
      
      setApplicationsWithJobs(combined)
    } catch (error) {
      console.error('Error fetching applications:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spin size="large" tip="Loading your applications..." />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Title level={3} className="!mb-1">My Applications</Title>
          <Text type="secondary">Track the status of your current job applications.</Text>
        </div>
        <Button icon={<SyncOutlined />} onClick={fetchData} className="rounded-xl font-bold">Refresh</Button>
      </div>

      {applicationsWithJobs.length > 0 ? (
        <div className="space-y-4">
          {applicationsWithJobs.map((app) => {
            const statusInfo = STATUS_MAP[app.status as ApplicationStatus] || { label: app.status, color: 'default', step: 0 }
            
            return (
              <Card
                key={app.id}
                bordered={false}
                className="shadow-soft-sm rounded-2xl hover:shadow-soft-md transition-shadow cursor-pointer"
                onClick={() => openQuickView('candidate_application', app)}
              >
                <div className="flex flex-col gap-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 font-bold">
                        <SolutionOutlined style={{ fontSize: 24 }} />
                      </div>
                      <div>
                        <Title level={4} className="!mb-1 text-slate-900">
                          {app.jobTitle}
                        </Title>
                        <Space size={4}>
                          {app.jobType && (
                            <Tag className="m-0 border-none bg-slate-100 text-slate-600 font-bold text-[10px] uppercase rounded px-2 py-0.5">
                              {app.jobType.replace(/_/g, ' ')}
                            </Tag>
                          )}
                          {app.workMode && (
                            <Tag className="m-0 border-none bg-blue-50 text-blue-600 font-bold text-[10px] uppercase rounded px-2 py-0.5">
                              {app.workMode}
                            </Tag>
                          )}
                        </Space>
                      </div>
                    </div>
                    <Tag color={statusInfo.color} className="m-0 rounded-full px-3 py-0.5 border-none font-bold text-[10px] uppercase tracking-wider">
                      {statusInfo.label}
                    </Tag>
                  </div>

                  <Steps
                    size="small"
                    current={statusInfo.step}
                    status={app.status === 'rejected' ? 'error' : 'process'}
                    items={STEPS}
                    className="application-steps"
                  />

                  <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                    <Space size={16} className="text-slate-400">
                      <span className="text-xs flex items-center gap-1.5">
                        <CalendarOutlined /> Applied {new Date(app.created_at).toLocaleDateString()}
                      </span>
                    </Space>
                    <Button type="link" className="p-0 flex items-center gap-1 text-xs font-bold uppercase tracking-wider">
                      View Details <ArrowRightOutlined style={{ fontSize: 10 }} />
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card bordered={false} className="text-center py-20 rounded-3xl shadow-soft-sm">
          <div className="h-20 w-20 bg-slate-50 text-slate-200 rounded-full flex items-center justify-center mx-auto mb-6">
            <SolutionOutlined style={{ fontSize: 40 }} />
          </div>
          <Title level={4} className="text-slate-900 mb-2">You haven't applied to any jobs yet</Title>
          <Paragraph className="text-slate-500 mb-8 max-w-xs mx-auto">
            Explore our current openings and find your next dream role today.
          </Paragraph>
          <Link to="/candidate/jobs">
            <Button type="primary" size="large" className="rounded-xl font-bold h-12 px-8 bg-blue-600 border-none shadow-soft-md">
              Browse Jobs <ArrowRightOutlined />
            </Button>
          </Link>
        </Card>
      )}

    </div>
  )
}
