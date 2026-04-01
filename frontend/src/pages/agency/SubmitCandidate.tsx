import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Row, Col, Card, Input, Avatar, Button, Typography, 
  Tag, message, Result, Spin, Empty
} from 'antd'
import {
  Search, CheckCircle, User, Briefcase, FileText, 
  Send, AlertCircle, ShieldCheck
} from 'lucide-react'
import dayjs from 'dayjs'
import { useApiQuery } from '@/hooks/useApiQuery'
import { candidatesApi } from '@/api/candidates'
import { agenciesApi } from '@/api/agencies'
import type { Candidate, JobRequisition, AgencyAssignment } from '@/types'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography
const { TextArea } = Input

export default function SubmitCandidate() {
  const navigate = useNavigate()
  const [candidateSearch, setCandidateSearch] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [selectedJob, setSelectedJob] = useState<{ requisition: JobRequisition, assignment: AgencyAssignment } | null>(null)
  const [coverNote, setCoverNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Fetch candidates
  const { data: candData, isLoading: candLoading } = useApiQuery(
    ['agency', 'candidates', candidateSearch],
    () => candidatesApi.list({ search: candidateSearch || undefined })
  )
  const candidates = (candData as any)?.candidates ?? []

  // Fetch assigned jobs
  const { data: jobsData, isLoading: jobsLoading } = useApiQuery(
    ['agency', 'my-jobs'],
    () => agenciesApi.myJobs()
  )
  const jobs = (jobsData as any)?.jobs ?? []

  const handleOpenSubmit = async () => {
    if (!selectedCandidate || !selectedJob) return
    setSubmitting(true)
    try {
      const govMode = selectedJob.assignment?.governance_mode || 'direct'
      await agenciesApi.submitCandidate({
        candidate_id: selectedCandidate.id,
        requisition_id: selectedJob.requisition.id,
        cover_note: coverNote,
        // Backend should handle initial status based on govMode, 
        // but we can pass a hint if needed.
        is_draft: govMode === 'approval_required'
      })
      
      const successMsg = govMode === 'approval_required' 
        ? 'Draft submitted for internal approval!' 
        : 'Candidate submitted to client successfully!'
        
      message.success(successMsg)
      setSubmitted(true)
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to submit candidate')
    } finally {
      setSubmitting(false)
    }
  }

  const govMode = selectedJob?.assignment?.governance_mode || 'direct'

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <Card bordered={false} className="shadow-soft-lg rounded-3xl p-8">
          <Result
            status="success"
            title={<span className="text-2xl font-black text-slate-900 tracking-tight">{govMode === 'approval_required' ? 'Internal Submission Sent' : 'Submission Successful'}</span>}
            subTitle={
              <div className="mt-4 space-y-2">
                <p className="text-slate-500 font-medium">
                  {govMode === 'approval_required' 
                    ? 'Your submission has been sent to your agency administrator for review.' 
                    : 'Your candidate has been successfully submitted to the client.'}
                </p>
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 mt-6 text-left">
                  <div className="flex items-center gap-3 mb-2">
                    <Avatar className="bg-blue-100 text-blue-600 shrink-0 font-bold">
                      {selectedCandidate?.full_name?.charAt(0).toUpperCase()}
                    </Avatar>
                    <Text strong className="text-slate-900">{selectedCandidate?.full_name}</Text>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                      <Briefcase className="h-4 w-4" />
                    </div>
                    <Text className="text-sm font-semibold text-slate-700">{selectedJob?.requisition.title}</Text>
                  </div>
                </div>
              </div>
            }
            extra={[
              <Button type="primary" key="dashboard" size="large" className="rounded-xl font-bold bg-slate-900 border-none h-12 px-8" onClick={() => navigate('/dashboard')}>
                Go to Dashboard
              </Button>,
              <Button key="jobs" size="large" className="rounded-xl font-bold h-12 px-8 border-slate-200" onClick={() => {
                setSubmitted(false)
                setSelectedCandidate(null)
                setSelectedJob(null)
                setCoverNote('')
              }}>
                New Submission
              </Button>,
            ]}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <Title level={3} className="!mb-1">Submit Candidate</Title>
        <p className="text-slate-500 mt-1">Connect your top talent with the right opportunities.</p>
      </div>

      <Row gutter={24}>
        {/* Step 1: Select Candidate */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <User className="h-4 w-4" />
                </div>
                <span className="text-base font-bold text-slate-900">1. Select Candidate</span>
              </div>
            } 
            bordered={false} 
            className="shadow-soft-sm h-[600px] flex flex-col"
            styles={{ body: { padding: '0', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' } }}
          >
            <div className="p-4 border-b border-slate-50">
              <Input
                prefix={<Search className="h-4 w-4 text-slate-400 mr-2" />}
                placeholder="Search candidates…"
                value={candidateSearch}
                onChange={e => setCandidateSearch(e.target.value)}
                className="h-10 rounded-xl"
              />
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {candLoading ? <div className="p-12 text-center"><Spin /></div> : (
                <div className="space-y-2">
                  {candidates.map((c: Candidate) => (
                    <div 
                      key={c.id}
                      className={cn(
                        "group flex items-center justify-between p-3 rounded-2xl border transition-all cursor-pointer",
                        selectedCandidate?.id === c.id 
                          ? "bg-blue-50 border-blue-200 shadow-sm" 
                          : "bg-white border-slate-100 hover:border-slate-200 hover:shadow-soft-sm"
                      )}
                      onClick={() => setSelectedCandidate(c)}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <Avatar className={cn("shrink-0 font-bold", selectedCandidate?.id === c.id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-400")}>
                          {c.full_name?.charAt(0).toUpperCase()}
                        </Avatar>
                        <div className="min-w-0">
                          <p className="text-sm font-bold text-slate-900 truncate">{c.full_name}</p>
                          <p className="text-[10px] text-slate-400 font-bold uppercase truncate">{c.current_title || 'N/A'}</p>
                        </div>
                      </div>
                      {selectedCandidate?.id === c.id && <CheckCircle className="h-5 w-5 text-blue-600 shrink-0" />}
                    </div>
                  ))}
                  {candidates.length === 0 && <Empty description="No candidates found" className="mt-12" />}
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* Step 2: Select Job */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Briefcase className="h-4 w-4" />
                </div>
                <span className="text-base font-bold text-slate-900">2. Select Opportunity</span>
              </div>
            } 
            bordered={false} 
            className="shadow-soft-sm h-[600px] flex flex-col"
            styles={{ body: { padding: '0', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' } }}
          >
            <div className="flex-1 overflow-y-auto p-4">
              {jobsLoading ? <div className="p-12 text-center"><Spin /></div> : (
                <div className="space-y-2">
                  {jobs.map((j: any) => (
                    <div 
                      key={j.assignment.id}
                      className={cn(
                        "group flex flex-col p-4 rounded-2xl border transition-all cursor-pointer",
                        selectedJob?.requisition.id === j.requisition.id 
                          ? "bg-emerald-50 border-emerald-200 shadow-sm" 
                          : "bg-white border-slate-100 hover:border-slate-200 hover:shadow-soft-sm"
                      )}
                      onClick={() => setSelectedJob(j)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="min-w-0">
                          <p className="text-sm font-bold text-slate-900 truncate">{j.requisition.title}</p>
                          <div className="flex gap-2 mt-1">
                            <Tag className="m-0 border-none bg-white/50 text-[9px] font-bold uppercase rounded px-1.5 tracking-wider">{j.requisition.job_type.replace('_', ' ')}</Tag>
                            <Tag className="m-0 border-none bg-white/50 text-[9px] font-bold uppercase rounded px-1.5 tracking-wider">{j.requisition.work_mode}</Tag>
                          </div>
                        </div>
                        {selectedJob?.requisition.id === j.requisition.id && <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0" />}
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100/50">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Submissions: {j.assignment.submissions_count}/{j.assignment.max_submissions}</span>
                        <span className="text-[10px] font-bold text-amber-600 uppercase tracking-widest">Ends: {dayjs(j.assignment.deadline).format('MMM D')}</span>
                      </div>
                    </div>
                  ))}
                  {jobs.length === 0 && <Empty description="No assigned jobs found" className="mt-12" />}
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Step 3: Finalize & Submit */}
      <Card bordered={false} className="shadow-soft-lg rounded-2xl">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-slate-900 text-white flex items-center justify-center">
              <FileText className="h-4 w-4" />
            </div>
            <span className="text-base font-bold text-slate-900">3. Cover Note & Submission</span>
          </div>

          <Row gutter={24} align="middle">
            <Col xs={24} md={16}>
              <TextArea
                rows={4}
                placeholder="Include a brief summary of why this candidate is perfect for this role..."
                value={coverNote}
                onChange={e => setCoverNote(e.target.value)}
                className="rounded-xl border-slate-200 p-4 text-sm"
              />
            </Col>
            <Col xs={24} md={8}>
              <div className="space-y-4">
                  <Button 
                  type="primary" 
                  block 
                  size="large" 
                  icon={govMode === 'approval_required' ? <ShieldCheck className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                  loading={submitting}
                  disabled={!selectedCandidate || !selectedJob || !coverNote.trim()}
                  className={cn(
                    "h-14 rounded-xl font-bold border-none shadow-soft-md transition-all",
                    govMode === 'approval_required' ? "bg-indigo-600 hover:bg-indigo-700" : "bg-blue-600 hover:bg-blue-700"
                  )}
                  onClick={handleOpenSubmit}
                >
                  {govMode === 'approval_required' ? 'Send for Internal Approval' : 'Submit to Client'}
                </Button>
                {!selectedCandidate || !selectedJob ? (
                  <div className="flex items-center gap-2 text-rose-500 font-bold text-[10px] uppercase tracking-widest justify-center">
                    <AlertCircle className="h-3 w-3" />
                    Select candidate and job
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-emerald-500 font-bold text-[10px] uppercase tracking-widest justify-center">
                    <CheckCircle className="h-3 w-3" />
                    {govMode === 'approval_required' ? 'Ready for internal review' : 'Ready for submission'}
                  </div>
                )}
              </div>
            </Col>
          </Row>
        </div>
      </Card>
    </div>
  )
}
