import React, { useState, useEffect, useCallback } from 'react'
import {
  Modal, Form, Input, Select, Button, Avatar, 
  Typography, message, Divider, Space, Tag, Alert,
  Row, Col, Spin
} from 'antd'
import { Search, UserPlus, Check, X, Briefcase, Flame, User } from 'lucide-react'
import http from '@/utils/http'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/utils/cn'
import { Candidate, JobRequisition, Engagement } from '@/types'

const { Text } = Typography

// Custom debounce implementation
function debounce<T extends (...args: any[]) => any>(fn: T, delay: number) {
  let timeoutId: ReturnType<typeof setTimeout>
  return function(this: any, ...args: Parameters<T>) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn.apply(this, args), delay)
  }
}

interface AddToActiveModalProps {
  open: boolean
  onClose: () => void
  preSelectedCandidate?: {
    id: string
    full_name: string
    current_title?: string
    email?: string
  }
}

const PRIORITY_OPTIONS = [
  { value: 'hot', label: '🔥 Hot', color: '#EF4444' },
  { value: 'warm', label: '🟡 Warm', color: '#F59E0B' },
  { value: 'cold', label: '🔵 Cold', color: '#6B7280' },
]

const ENGAGEMENT_TYPES = [
  { value: 'lead', label: 'Lead' },
  { value: 'sourced', label: 'Sourced for Job' },
  { value: 'referral', label: 'Referral' },
  { value: 'direct', label: 'Direct Approach' },
]

export default function AddToActiveModal({ open, onClose, preSelectedCandidate }: AddToActiveModalProps) {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState(false)
  
  // Section 1 State
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Candidate[]>([])
  const [searching, setSearching] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<any>(preSelectedCandidate || null)
  const [showNewForm, setShowNewForm] = useState(false)
  const [pendingNewCandidatePayload, setPendingNewCandidatePayload] = useState<any | null>(null)
  const [duplicateCandidate, setDuplicateCandidate] = useState<any | null>(null)
  const [emailDuplicateHint, setEmailDuplicateHint] = useState<any | null>(null)
  const [phoneDuplicateHint, setPhoneDuplicateHint] = useState<any | null>(null)
  
  // Section 2 State
  const [jobs, setJobs] = useState<JobRequisition[]>([])
  const [existingEngagements, setExistingEngagements] = useState<Engagement[]>([])
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null)
  const [priority, setPriority] = useState<'hot' | 'warm' | 'cold'>('warm')
  const [engagementType, setEngagementType] = useState('lead')

  // Sync state if preSelectedCandidate changes
  useEffect(() => {
    if (preSelectedCandidate) {
      setSelectedCandidate(preSelectedCandidate)
      checkExistingEngagements(preSelectedCandidate.id)
    } else {
      setSelectedCandidate(null)
    }
  }, [preSelectedCandidate, open])

  // Fetch active jobs
  useEffect(() => {
    if (open) {
      http.get('/jobs/requisitions/?status=active').then(r => {
        setJobs(r.data.data.requisitions || [])
      })
    }
  }, [open])

  // Search candidates
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      if (query.length < 2) {
        setSearchResults([])
        return
      }
      setSearching(true)
      try {
        const res = await http.get(`/candidates/?search=${query}`)
        setSearchResults(res.data.data.candidates || [])
      } catch (err) {
        console.error('Candidate search failed', err)
      } finally {
        setSearching(false)
      }
    }, 300),
    []
  )

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setSearchQuery(val)
    debouncedSearch(val)
  }

  const handleSelectCandidate = (candidate: Candidate) => {
    const fullName = candidate.full_name || `${candidate.first_name || ''} ${candidate.last_name || ''}`.trim() || 'Candidate'
    setSelectedCandidate({
      id: candidate.id,
      full_name: fullName,
      current_title: candidate.current_title,
      email: candidate.email,
      phone: (candidate as any).phone,
    })
    setSearchResults([])
    setSearchQuery('')
    setShowNewForm(false)
    setDuplicateCandidate(null)
    setPendingNewCandidatePayload(null)
    setEmailDuplicateHint(null)
    setPhoneDuplicateHint(null)
    checkExistingEngagements(candidate.id)
  }

  const completeAddToActive = async (candidateId: string, values: any) => {
    await http.post(`/candidates/${candidateId}/engagements/`, {
      engagement_type: engagementType,
      stage: 'new',
      priority: priority,
      job: values.job_id || null,
      owner_user: 'me',
    })

    if (values.initial_note?.trim()) {
      await http.post(`/candidates/${candidateId}/notes/`, {
        note_text: values.initial_note.trim(),
        note_type: 'general',
      })
    }

    message.success('Added to active work')
    queryClient.invalidateQueries({ queryKey: ['active-engagements'] })
    onClose()
    form.resetFields()
    setSelectedCandidate(null)
    setShowNewForm(false)
    setPendingNewCandidatePayload(null)
    setDuplicateCandidate(null)
    setEmailDuplicateHint(null)
    setPhoneDuplicateHint(null)
    setPriority('warm')
    setEngagementType('lead')
  }

  const checkInlineDuplicate = async (field: 'email' | 'phone', rawValue: string) => {
    const value = (rawValue || '').trim()
    if (!value) {
      if (field === 'email') setEmailDuplicateHint(null)
      if (field === 'phone') setPhoneDuplicateHint(null)
      return
    }

    try {
      const res = await http.get(`/candidates/?search=${encodeURIComponent(value)}`)
      const candidates = res.data?.data?.candidates || []
      let match = null
      if (field === 'email') {
        const normalized = value.toLowerCase()
        match = candidates.find((c: any) => (c.email || '').toLowerCase() === normalized) || null
      } else {
        match = candidates.find((c: any) => (c.phone || '').trim() === value) || null
      }

      if (field === 'email') setEmailDuplicateHint(match)
      if (field === 'phone') setPhoneDuplicateHint(match)
    } catch {
      if (field === 'email') setEmailDuplicateHint(null)
      if (field === 'phone') setPhoneDuplicateHint(null)
    }
  }

  const useDuplicateCandidate = async (candidate: any) => {
    const values = form.getFieldsValue(true)
    const candidateId = candidate.id
    const fullName = candidate.name || `${candidate.first_name || ''} ${candidate.last_name || ''}`.trim() || candidate.full_name || 'Candidate'
    setSelectedCandidate({
      id: candidateId,
      full_name: fullName,
      current_title: candidate.current_title,
      email: candidate.email,
      phone: candidate.phone,
    })
    setShowNewForm(false)
    setDuplicateCandidate(null)
    await checkExistingEngagements(candidateId)
    await completeAddToActive(candidateId, values)
  }

  const handleCreateAnyway = async () => {
    if (!pendingNewCandidatePayload) {
      message.error('Please fill candidate details again')
      setDuplicateCandidate(null)
      return
    }
    setLoading(true)
    try {
      const cRes = await http.post('/candidates/?force=true', pendingNewCandidatePayload)
      if (cRes.data?.duplicate === true) {
        setDuplicateCandidate(cRes.data.existing_candidate || null)
        message.error('Duplicate check is still blocking this candidate creation.')
        return
      }
      const created = cRes.data?.data?.candidate
      if (!created?.id) {
        throw new Error('Candidate creation failed')
      }
      const values = form.getFieldsValue(true)
      await completeAddToActive(created.id, values)
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to create candidate')
    } finally {
      setLoading(false)
    }
  }

  const checkExistingEngagements = async (candidateId: string) => {
    try {
      const res = await http.get(`/candidates/${candidateId}/engagements/`)
      setExistingEngagements(res.data.data || [])
    } catch {}
  }

  const handleJobChange = (jobId: string) => {
    const exists = existingEngagements.find(e => e.job === jobId && e.is_active)
    if (exists) {
      setDuplicateWarning(`This candidate already has an active engagement for this job. Are you sure you want to create another?`)
    } else {
      setDuplicateWarning(null)
    }
  }

  const onFinish = async (values: any) => {
    if (!selectedCandidate && !showNewForm) {
      message.error('Please select or create a candidate')
      return
    }

    setLoading(true)
    try {
      let candidateId = selectedCandidate?.id

      // 1. Create candidate if new
      if (showNewForm) {
        const candidatePayload = {
          first_name: values.first_name,
          last_name: values.last_name,
          email: values.email,
          phone: values.phone,
          current_title: values.current_title,
          source: 'direct'
        }
        setPendingNewCandidatePayload(candidatePayload)
        const cRes = await http.post('/candidates/', candidatePayload)

        if (cRes.data?.duplicate === true) {
          setDuplicateCandidate(cRes.data.existing_candidate || null)
          setLoading(false)
          return
        }

        candidateId = cRes.data?.data?.candidate?.id
      }

      if (!candidateId) {
        throw new Error('Candidate is required')
      }

      await completeAddToActive(candidateId, values)
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Failed to add to active work')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={<span className="text-xl font-bold text-slate-900">Add to Active Work</span>}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      okText={preSelectedCandidate ? "Start Working This Candidate" : "Add to Active"}
      okButtonProps={{ className: "bg-indigo-600 font-bold h-10 rounded-xl" }}
      cancelButtonProps={{ className: "h-10 rounded-xl" }}
      width={550}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        
        {/* SECTION 1: Find or Create Candidate */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-6 w-6 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs font-bold">1</div>
            <Text className="font-bold text-slate-800">Find or Create Candidate</Text>
          </div>

          {!selectedCandidate ? (
            <div className="space-y-4">
              <div className="relative">
                <Input
                  prefix={<Search size={16} className="text-slate-400 mr-2" />}
                  placeholder="Search by name or email"
                  className="h-11 rounded-xl border-slate-200"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  autoComplete="off"
                />
                
                {searching && <div className="absolute right-3 top-3"><Spin size="small" /></div>}
                
                {searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-slate-100 z-50 max-h-60 overflow-y-auto p-2 space-y-1">
                    {searchResults.map(c => (
                      <div 
                        key={c.id} 
                        onClick={() => handleSelectCandidate(c)}
                        className="flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg cursor-pointer transition-colors border border-transparent hover:border-slate-100"
                      >
                        <Avatar className="bg-indigo-50 text-indigo-600 font-bold shrink-0">
                          {c.first_name[0]}{c.last_name[0]}
                        </Avatar>
                        <div className="min-w-0">
                          <Text className="block font-bold text-slate-900 text-sm leading-tight">{c.full_name}</Text>
                          <Text className="block text-[11px] text-slate-400 truncate">{c.current_title || 'No Title'} • {c.email}</Text>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                  <div className="mt-2 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                    <Text className="text-slate-500 text-sm">No candidate found — <Button type="link" className="p-0 font-bold h-auto" onClick={() => setShowNewForm(true)}>create new</Button></Text>
                  </div>
                )}
              </div>

              {showNewForm && (
                duplicateCandidate ? (
                  <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 space-y-4 animate-in fade-in slide-in-from-top-2">
                    <div className="text-sm font-bold text-amber-900">
                      ⚠️ A candidate already exists with this email or phone.
                    </div>
                    <button
                      type="button"
                      className="w-full text-left p-3 rounded-xl border border-amber-300 bg-white hover:bg-amber-50 transition-colors"
                      onClick={() => useDuplicateCandidate(duplicateCandidate)}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="bg-amber-100 text-amber-700 font-bold shrink-0">
                          {(duplicateCandidate.name || 'C').charAt(0)}
                        </Avatar>
                        <div className="min-w-0">
                          <Text className="block font-bold text-slate-900 text-sm leading-tight truncate">
                            {duplicateCandidate.name || 'Candidate'} — {duplicateCandidate.current_title || 'No Title'}
                          </Text>
                          <Text className="block text-[11px] text-slate-500 truncate">
                            {duplicateCandidate.email || 'No Email'} · {duplicateCandidate.phone || 'No Phone'}
                          </Text>
                        </div>
                      </div>
                    </button>
                    <div className="flex gap-2">
                      <Button
                        type="primary"
                        className="bg-amber-600 border-none font-bold"
                        onClick={() => useDuplicateCandidate(duplicateCandidate)}
                      >
                        Use This Candidate
                      </Button>
                      <Button
                        className="font-bold"
                        onClick={handleCreateAnyway}
                        loading={loading}
                      >
                        Create Anyway - different person
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-0 animate-in fade-in slide-in-from-top-2">
                    <Row gutter={12}>
                      <Col span={12}>
                        <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
                          <Input className="h-9 rounded-lg" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
                          <Input className="h-9 rounded-lg" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item 
                      name="email" 
                      label="Email" 
                      rules={[{ required: true, type: 'email' }]}
                      extra={emailDuplicateHint ? (
                        <button
                          type="button"
                          className="mt-1 text-left text-xs text-amber-700 font-medium hover:underline"
                          onClick={() => handleSelectCandidate(emailDuplicateHint)}
                        >
                          ⚠️ {emailDuplicateHint.full_name || `${emailDuplicateHint.first_name || ''} ${emailDuplicateHint.last_name || ''}`.trim() || 'Candidate'} already exists with this email. Select them instead?
                        </button>
                      ) : null}
                    >
                      <Input 
                        className="h-9 rounded-lg" 
                        onBlur={(e) => checkInlineDuplicate('email', e.target.value)}
                      />
                    </Form.Item>
                    <Row gutter={12}>
                      <Col span={12}>
                        <Form.Item 
                          name="phone" 
                          label="Phone (Optional)"
                          extra={phoneDuplicateHint ? (
                            <button
                              type="button"
                              className="mt-1 text-left text-xs text-amber-700 font-medium hover:underline"
                              onClick={() => handleSelectCandidate(phoneDuplicateHint)}
                            >
                              ⚠️ {phoneDuplicateHint.full_name || `${phoneDuplicateHint.first_name || ''} ${phoneDuplicateHint.last_name || ''}`.trim() || 'Candidate'} already exists with this phone. Select them instead?
                            </button>
                          ) : null}
                        >
                          <Input 
                            className="h-9 rounded-lg" 
                            onBlur={(e) => checkInlineDuplicate('phone', e.target.value)}
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="current_title" label="Current Title (Optional)">
                          <Input className="h-9 rounded-lg" />
                        </Form.Item>
                      </Col>
                    </Row>
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                  <Check size={18} />
                </div>
                <div>
                  <Text className="block font-bold text-emerald-900 text-sm">{selectedCandidate.full_name}</Text>
                  <Text className="block text-[11px] text-emerald-600 font-medium uppercase tracking-wider">{selectedCandidate.current_title || 'Candidate'}</Text>
                </div>
              </div>
              {!preSelectedCandidate && (
                <Button type="link" size="small" className="text-emerald-700 font-bold" onClick={() => setSelectedCandidate(null)}>
                  Change
                </Button>
              )}
            </div>
          )}
        </div>

        <Divider className="my-0 mb-8" />

        {/* SECTION 2: Engagement Details */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-6">
            <div className="h-6 w-6 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs font-bold">2</div>
            <Text className="font-bold text-slate-800">Engagement Details</Text>
          </div>

          <Form.Item 
            name="job_id" 
            label={<span>Which job are you working them for? <Text type="secondary" className="font-normal text-[11px]">(Optional)</Text></span>}
          >
            <Select 
              placeholder="General Nurture"
              className="h-11 modern-select"
              onChange={handleJobChange}
              allowClear
              options={jobs.map(j => ({
                value: j.id,
                label: (
                  <div className="flex flex-col py-1">
                    <span className="font-bold text-slate-800">{j.title}</span>
                    <span className="text-[10px] text-slate-400 uppercase font-black">{j.department_id || 'Global'}</span>
                  </div>
                )
              }))}
            />
          </Form.Item>

          {duplicateWarning && (
            <Alert 
              message={duplicateWarning} 
              type="warning" 
              showIcon 
              className="mb-6 rounded-xl font-medium text-xs"
              action={
                <Space>
                  <Button size="small" type="primary" className="bg-amber-600 border-none text-[10px] font-bold" onClick={() => setDuplicateWarning(null)}>Confirm</Button>
                  <Button size="small" type="text" className="text-[10px] font-bold" onClick={() => { form.setFieldValue('job_id', undefined); setDuplicateWarning(null); }}>Cancel</Button>
                </Space>
              }
            />
          )}

          <Form.Item label="Priority">
            <div className="flex gap-3">
              {PRIORITY_OPTIONS.map(opt => {
                const isActive = priority === opt.value
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setPriority(opt.value as any)}
                    className={cn(
                      "flex-1 h-10 rounded-xl font-bold text-xs transition-all border flex items-center justify-center gap-2",
                      isActive 
                        ? "bg-[#4F46E5] text-white border-[#4F46E5] shadow-md" 
                        : "bg-white border-slate-200 text-slate-400 hover:border-slate-200"
                    )}
                  >
                    {opt.label}
                  </button>
                )
              })}
            </div>
          </Form.Item>

          <Form.Item label="Engagement Type">
            <div className="flex flex-wrap gap-2">
              {ENGAGEMENT_TYPES.map(opt => {
                const isActive = engagementType === opt.value
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setEngagementType(opt.value)}
                    className={cn(
                      "px-4 h-9 rounded-full font-bold text-[11px] transition-all border flex items-center justify-center",
                      isActive 
                        ? "bg-[#4F46E5] border-[#4F46E5] text-white shadow-md" 
                        : "bg-white border-slate-200 text-slate-500 hover:border-indigo-200"
                    )}
                  >
                    {opt.label}
                  </button>
                )
              })}
            </div>
          </Form.Item>

          <Form.Item name="initial_note" label="Any initial notes?">
            <Input.TextArea rows={3} placeholder="Initial reach out details..." className="rounded-xl" />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  )
}
