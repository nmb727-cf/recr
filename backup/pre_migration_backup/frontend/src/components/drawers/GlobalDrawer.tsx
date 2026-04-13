import { Drawer, Button, Tag, Spin, Tabs, Table, Modal, Input, message } from 'antd'
import { useDrawerStore } from '../../store/drawerStore'
import { useQuery } from '@tanstack/react-query'
import api from '../../utils/http'

// Import original quick view components
import JobQuickView from '../../pages/jobs/JobQuickView'
import CandidateQuickView from '../../pages/candidates/CandidateQuickView'
import ApplicationQuickView from '../../pages/pipeline/ApplicationQuickView'
import AgencySubmissionQuickView from '../../pages/agency/AgencySubmissionQuickView'
import AgencyJobQuickView from '../../pages/agency/AgencyJobQuickView'
import CandidateJobQVPanel from './quickviews/CandidateJobQVPanel'
import CandidateApplicationQVPanel from './quickviews/CandidateApplicationQVPanel'

const JobFullView = ({ data }: { data: any }) => {
  if (!data) return <Spin />

  const jobId = data.id

  // Fetch applications for this job
  const { data: appsData, isLoading: appsLoading } = useQuery({
    queryKey: ['job-applications', jobId],
    queryFn: async () => {
      const res = await api.get(`/pipeline/applications/?requisition_id=${jobId}`)
      return res.data.data?.applications || []
    },
    enabled: !!jobId
  })

  // Fetch pipeline for this job
  const { data: pipelineData, isLoading: pipelineLoading } = useQuery({
    queryKey: ['job-pipeline', jobId],
    queryFn: async () => {
      const res = await api.get(`/pipeline/pipeline/${jobId}/`)
      return res.data.data?.pipeline || {}
    },
    enabled: !!jobId
  })

  // Fetch interviews for this job's applications
  const { data: interviewsData, isLoading: interviewsLoading } = useQuery({
    queryKey: ['job-interviews', jobId],
    queryFn: async () => {
      const res = await api.get(`/interviews/interviews/?requisition_id=${jobId}`)
      return res.data.data?.interviews || []
    },
    enabled: !!jobId
  })

  const formatSalary = (amount: any) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: data.salary_currency || 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const promptStageNote = (title: string): Promise<string | null> =>
    new Promise((resolve) => {
      let note = ''
      Modal.confirm({
        title,
        content: (
          <div style={{ marginTop: 8 }}>
            <p style={{ margin: '0 0 6px 0', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#94a3b8' }}>
              Mandatory Note
            </p>
            <Input.TextArea rows={3} placeholder="Enter reason for stage change" onChange={(e) => { note = e.target.value }} />
          </div>
        ),
        okText: 'Confirm',
        onOk: async () => {
          if (!note.trim()) {
            message.error('A note is required')
            throw new Error('missing_note')
          }
          resolve(note.trim())
        },
        onCancel: () => resolve(null),
      })
    })

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div style={{ padding: '16px 0' }}>
          {/* Stats Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 12,
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
            padding: 16,
            marginBottom: 24
          }}>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Experience</p>
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>{data.experience_min}-{data.experience_max} years</p>
            </div>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Salary Range</p>
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>{formatSalary(data.salary_min)} - {formatSalary(data.salary_max)}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Headcount</p>
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>{data.headcount}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Job Type</p>
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>{data.job_type?.replace('_', ' ')}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Work Mode</p>
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>{data.work_mode}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: '#888', fontSize: 11, textTransform: 'uppercase' }}>Priority</p>
              <Tag color={data.priority === 'high' ? 'red' : data.priority === 'medium' ? 'orange' : 'blue'}>
                {data.priority}
              </Tag>
            </div>
          </div>

          {/* Description */}
          {data.description && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: '#888', fontSize: 12, marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Description</p>
              <p style={{ color: '#374151', lineHeight: 1.6 }}>{data.description}</p>
            </div>
          )}

          {/* Requirements */}
          {data.requirements && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: '#888', fontSize: 12, marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Requirements</p>
              <p style={{ color: '#374151', lineHeight: 1.6 }}>{data.requirements}</p>
            </div>
          )}

          {/* Responsibilities */}
          {data.responsibilities && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: '#888', fontSize: 12, marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Responsibilities</p>
              <p style={{ color: '#374151', lineHeight: 1.6 }}>{data.responsibilities}</p>
            </div>
          )}

          {/* Skills */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ color: '#888', fontSize: 12, marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Skills Required</p>
            <div>{(data.skills_required || []).map((s: string) => <Tag color="blue" key={s} style={{ marginBottom: 4 }}>{s}</Tag>)}</div>
          </div>
        </div>
      )
    },
    {
      key: 'pipeline',
      label: `Pipeline (${Object.values(pipelineData || {}).reduce((sum: number, stage: any) => sum + (stage.count || 0), 0)})`,
      children: pipelineLoading ? <Spin /> : (
        <div style={{ overflowX: 'auto', padding: '16px 0' }}>
          <div style={{ display: 'flex', gap: 16, minWidth: 'max-content' }}>
            {Object.entries(pipelineData || {}).map(([stageId, stageData]: [string, any]) => (
              <div key={stageId} style={{
                width: 200,
                background: '#f8fafc',
                borderRadius: 8,
                padding: 12,
                border: '1px solid #e2e8f0'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{stageData.stage?.name}</span>
                  <Tag>{stageData.count}</Tag>
                </div>
                {(stageData.applications || []).map((app: any) => (
                  <div key={app.id} style={{
                    background: 'white',
                    borderRadius: 6,
                    padding: 8,
                    marginBottom: 8,
                    border: '1px solid #e2e8f0',
                    fontSize: 12
                  }}>
                    <p style={{ margin: 0, fontWeight: 500 }}>
                      {app.candidate_id?.toString().substring(0, 8)}...
                    </p>
                    <p style={{ margin: 0, color: '#888' }}>{app.status}</p>
                  </div>
                ))}
                {stageData.count === 0 && (
                  <p style={{ color: '#ccc', fontSize: 12, textAlign: 'center' }}>Empty</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )
    },
    {
      key: 'applications',
      label: `Applications (${appsData?.length || 0})`,
      children: appsLoading ? <Spin /> : (
        <div style={{ padding: '16px 0' }}>
          {(!appsData || appsData.length === 0) ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
              No applications yet
            </div>
          ) : (
            <Table
              dataSource={appsData}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: 'Candidate',
                  dataIndex: 'candidate_id',
                  render: (id) => id?.toString().substring(0, 8) + '...'
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  render: (status) => (
                    <Tag color={
                      status === 'joined' ? 'green' :
                      status === 'rejected' ? 'red' :
                      status === 'interview' ? 'purple' :
                      status === 'offer' ? 'orange' : 'blue'
                    }>{status}</Tag>
                  )
                },
                {
                  title: 'Applied',
                  dataIndex: 'created_at',
                  render: (date) => new Date(date).toLocaleDateString()
                },
                {
                  title: 'Actions',
                  render: (_, record: any) => (
                    <div style={{ display: 'flex', gap: 4 }}>
                      <Button size="small" type="primary"
                        onClick={async () => {
                          const note = await promptStageNote('Confirm Stage Change')
                          if (!note) return
                          await api.post(`/pipeline/applications/${record.id}/shortlist/`, { note })
                        }}>
                        Shortlist
                      </Button>
                      <Button size="small" danger
                        onClick={async () => {
                          const note = await promptStageNote('Confirm Stage Change')
                          if (!note) return
                          await api.post(`/pipeline/applications/${record.id}/reject/`, { note })
                        }}>
                        Reject
                      </Button>
                    </div>
                  )
                }
              ]}
            />
          )}
        </div>
      )
    },
    {
      key: 'interviews',
      label: `Interviews (${interviewsData?.length || 0})`,
      children: interviewsLoading ? <Spin /> : (
        <div style={{ padding: '16px 0' }}>
          {(!interviewsData || interviewsData.length === 0) ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
              No interviews scheduled yet
            </div>
          ) : (
            <Table
              dataSource={interviewsData}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                { title: 'Type', dataIndex: 'interview_type' },
                { title: 'Round', dataIndex: 'interview_round' },
                {
                  title: 'Scheduled',
                  dataIndex: 'scheduled_at',
                  render: (date) => date ? new Date(date).toLocaleString() : 'TBD'
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  render: (status) => (
                    <Tag color={status === 'completed' ? 'green' : status === 'cancelled' ? 'red' : 'blue'}>
                      {status}
                    </Tag>
                  )
                },
                {
                  title: 'Score',
                  dataIndex: 'overall_score',
                  render: (score) => score ? `${score}%` : '-'
                }
              ]}
            />
          )}
        </div>
      )
    }
  ]

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
          <Tag color={data.status === 'active' ? 'green' : data.status === 'draft' ? 'default' : 'orange'}>
            {data.status}
          </Tag>
          <Tag>{data.job_type?.replace('_', ' ')}</Tag>
          <Tag>{data.work_mode}</Tag>
          <Tag color={data.priority === 'high' || data.priority === 'urgent' ? 'red' : 'blue'}>
            {data.priority}
          </Tag>
        </div>
      </div>

      {/* Tabs */}
      <Tabs items={tabItems} />
    </div>
  )
}

const CandidateNotesTab = ({ candidateId }: { candidateId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['candidate-notes', candidateId],
    queryFn: async () => {
      if (!candidateId) return []
      const res = await api.get(`/candidates/${candidateId}/notes/`)
      return res?.data?.data?.notes || []
    },
    enabled: !!candidateId
  })

  if (isLoading) return <div style={{ padding: 20 }}><Spin /></div>
  if (!data?.length) return <p style={{ padding: 20 }}>No notes yet</p>

  return (
    <div style={{ padding: 20 }}>
      {data.map((note: any) => (
        <div key={note.id} style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
          <Tag color="orange">{note?.note_type || 'General'}</Tag>
          <p style={{ marginTop: 8 }}>{note?.note_text || ''}</p>
        </div>
      ))}
    </div>
  )
}

const FullViewContent = ({ type, data }: { type: any, data: any }) => {
  if (!data) return <Spin />

  if (type === 'job') return <JobFullView data={data} />

  if (type === 'candidate') return (
    <div style={{ padding: 24 }}>
      <h2>{data.first_name} {data.last_name}</h2>
      <Tabs items={[
        {
          key: 'profile',
          label: 'Profile',
          children: (
            <div>
              <p><b>Email:</b> {data.email}</p>
              <p><b>Phone:</b> {data.phone}</p>
              <p><b>Title:</b> {data.current_title}</p>
              <p><b>Company:</b> {data.current_company}</p>
              <p><b>Experience:</b> {data.experience_years} years</p>
              <p><b>Location:</b> {data.current_location_city}, {data.current_location_country}</p>
              <div><b>Skills:</b> {(data.skills || []).map((s: string) => <Tag key={s}>{s}</Tag>)}</div>
            </div>
          )
        },
        {
          key: 'notes',
          label: 'Notes',
          children: <CandidateNotesTab candidateId={data.id} />
        },
      ]} />
    </div>
  )

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">{data.title || data.full_name || 'Details'}</h1>
      <Tabs items={[
        { key: 'overview', label: 'Overview', children: <div className="py-4"><pre className="whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre></div> },
        { key: 'raw', label: 'Raw Data', children: <div className="py-4"><pre className="bg-slate-50 p-4 rounded-lg overflow-auto">{JSON.stringify(data, null, 2)}</pre></div> }
      ]} />
    </div>
  )
}

export const GlobalDrawer = () => {
  const {
    quickViewOpen, quickViewData, quickViewType,
    fullViewOpen,
    closeQuickView, closeFullView, openFullView
  } = useDrawerStore()

  const drawerTitle: Record<string, string> = {
    job: 'Job Details',
    candidate: 'Candidate Profile',
    application: 'Application Details',
    agency_submission: 'Submission Details',
    agency_job: 'Agency Job',
    candidate_job: 'Job Details',
    candidate_application: 'Application Status',
  }

  return (
    <Drawer
      open={quickViewOpen}
      onClose={closeQuickView}
      width={quickViewType === 'candidate_job' ? 560 : 480}
      title={drawerTitle[quickViewType ?? ''] ?? 'Quick View'}
      destroyOnClose
      styles={{ body: { padding: '24px' } }}
    >
      {quickViewType === 'job' && quickViewData && (
        <JobQuickView
          jobId={quickViewData.id}
          onOpenFullView={() => openFullView('job', quickViewData)}
          onClose={closeQuickView}
        />
      )}

      {quickViewType === 'candidate' && quickViewData && (
        <CandidateQuickView
          candidateId={quickViewData.id}
          onOpenFullView={() => openFullView('candidate', quickViewData)}
          onClose={closeQuickView}
        />
      )}

      {quickViewType === 'application' && quickViewData && (
        <ApplicationQuickView
          applicationId={quickViewData.id}
          onOpenFullView={() => openFullView('application', quickViewData)}
          onClose={closeQuickView}
        />
      )}

      {quickViewType === 'agency_submission' && quickViewData && (
        <AgencySubmissionQuickView
          submission={quickViewData.submission}
          jobTitle={quickViewData.jobTitle}
          onClose={closeQuickView}
        />
      )}

      {quickViewType === 'agency_job' && quickViewData && (
        <AgencyJobQuickView
          data={quickViewData}
          onClose={closeQuickView}
        />
      )}

      {quickViewType === 'candidate_job' && quickViewData && (
        <CandidateJobQVPanel job={quickViewData} />
      )}

      {quickViewType === 'candidate_application' && quickViewData && (
        <CandidateApplicationQVPanel data={quickViewData} />
      )}

      <Drawer
        open={fullViewOpen}
        onClose={closeFullView}
        width={800}
        title="Full Details"
        destroyOnClose
        styles={{ wrapper: { width: 800 } }}
        style={{ position: 'absolute' }}
        extra={<Button onClick={closeFullView}>Back</Button>}
      >
        <FullViewContent
          type={quickViewType}
          data={quickViewData}
        />
      </Drawer>
    </Drawer>
  )
}
