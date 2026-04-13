import { useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  DatePicker,
  Empty,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  Bell,
  CalendarDays,
  CheckCircle2,
  Clock3,
  ListChecks,
  RefreshCw,
  Users,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { pipelineApi } from '@/api/pipeline'
import { candidatesApi } from '@/api/candidates'
import { requisitionsApi } from '@/api/jobs'
import { useApiQuery } from '@/hooks/useApiQuery'
import type { Application, Candidate, Interview, JobRequisition } from '@/types'
import { getInterviewTypeLabel } from '@/utils/interviewTypeUx'

const { Title, Text } = Typography

type WizardStep = 'selection' | 'setup' | 'slots' | 'notifications' | 'review' | 'summary'
type SlotPattern = 'same_slot' | 'sequential_slots' | 'interviewer_specific'

type SchedulingDraft = {
  applicationIds: string[]
  interviewType: string
  templateId: string
  interviewers: string[]
  dateRange: [string | null, string | null]
  slotPattern: SlotPattern
  durationMinutes: number
  timezone: string
  sendInviteNow: boolean
  sendReminder: boolean
  notifyRecruiter: boolean
  notifyInterviewer: boolean
  notifyCandidate: boolean
  stageFilter: string
  interviewTypeFilter: string
  jobFilter: string
  recruiterFilter: string
}

type BulkResult = {
  scheduled: Array<{ applicationId: string; interviewId: string }>
  failed: Array<{ applicationId: string; reason: string }>
  skipped: Array<{ applicationId: string; reason: string }>
  warnings: string[]
}

const STEPS: Array<{ key: WizardStep; label: string; icon: React.ElementType }> = [
  { key: 'selection', label: '1. Candidate Selection', icon: Users },
  { key: 'setup', label: '2. Bulk Schedule Setup', icon: CalendarDays },
  { key: 'slots', label: '3. Slot Assignment', icon: Clock3 },
  { key: 'notifications', label: '4. Notifications', icon: Bell },
  { key: 'review', label: '5. Review & Confirm', icon: ListChecks },
  { key: 'summary', label: '6. Result Summary', icon: CheckCircle2 },
]

function combineDateTime(dateIso: string, hour: number, minute: number) {
  return dayjs(dateIso).hour(hour).minute(minute).second(0).millisecond(0).toISOString()
}

export default function RecruiterBulkScheduling() {
  const queryClient = useQueryClient()
  const [activeStep, setActiveStep] = useState<WizardStep>('selection')
  const [search, setSearch] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<BulkResult | null>(null)
  const [draft, setDraft] = useState<SchedulingDraft>({
    applicationIds: [],
    interviewType: '',
    templateId: '',
    interviewers: [],
    dateRange: [dayjs().add(1, 'day').startOf('day').toISOString(), dayjs().add(5, 'day').startOf('day').toISOString()],
    slotPattern: 'sequential_slots',
    durationMinutes: 45,
    timezone: 'UTC',
    sendInviteNow: true,
    sendReminder: true,
    notifyRecruiter: true,
    notifyInterviewer: true,
    notifyCandidate: true,
    stageFilter: '',
    interviewTypeFilter: '',
    jobFilter: '',
    recruiterFilter: '',
  })

  const { data: applicationsRes, isLoading } = useApiQuery(['bulk-scheduling-applications'], () => pipelineApi.listApplications())
  const { data: candidatesRes } = useApiQuery(['bulk-scheduling-candidates'], () => candidatesApi.list({ search: '' }))
  const { data: jobsRes } = useApiQuery(['bulk-scheduling-jobs'], () => requisitionsApi.list({ status: 'active' }))
  const { data: interviewsRes } = useApiQuery(['bulk-scheduling-interviews'], () => interviewsApi.list())
  const { data: typesRes } = useApiQuery(['bulk-scheduling-types'], () => interviewsApi.listTypes())
  const { data: templatesRes } = useApiQuery(['bulk-scheduling-templates'], () => interviewsApi.listTemplates())

  const applications: Application[] = (applicationsRes as any)?.applications || []
  const candidates = (candidatesRes as any)?.candidates || []
  const requisitions = (jobsRes as any)?.requisitions || []
  const interviews: Interview[] = (interviewsRes as any)?.interviews || []
  const interviewTypes = (typesRes as any)?.types || []
  const templates = (templatesRes as any)?.templates || []

  const candidateMap = useMemo(
    () => new Map<string, Candidate>(candidates.map((candidate: Candidate) => [candidate.id, candidate])),
    [candidates],
  )
  const requisitionMap = useMemo(
    () => new Map<string, JobRequisition>(requisitions.map((job: JobRequisition) => [job.id, job])),
    [requisitions],
  )

  const existingInterviewTypesByApplication = useMemo(() => {
    const map = new Map<string, string[]>()
    interviews.forEach((item) => {
      if (!item.application_id) return
      const current = map.get(item.application_id) || []
      current.push(item.interview_type)
      map.set(item.application_id, current)
    })
    return map
  }, [interviews])

  const stageOptions = useMemo(
    () => Array.from(new Set(applications.map((item) => item.current_stage_id).filter(Boolean))).map((value) => ({ value, label: String(value) })),
    [applications],
  )

  const recruiterOptions = useMemo(
    () => Array.from(new Set(applications.map((item) => item.submitted_by).filter(Boolean))).map((value) => ({ value, label: String(value) })),
    [applications],
  )

  const jobOptions = useMemo(
    () => requisitions.map((job: any) => ({ value: job.id, label: job.title })),
    [requisitions],
  )

  const interviewTypeOptions = useMemo(
    () => interviewTypes.map((type: any) => ({ value: type.code, label: type.name || getInterviewTypeLabel(type.code) })),
    [interviewTypes],
  )

  const filteredTemplates = useMemo(
    () => templates.filter((template: any) => !draft.interviewType || template.interview_type === draft.interviewType),
    [templates, draft.interviewType],
  )

  const interviewerOptions = useMemo(() => {
    const ids = new Set<string>()
    interviews.forEach((item) => (item.interviewers || []).forEach((id) => ids.add(id)))
    return Array.from(ids).map((value) => ({ value, label: value }))
  }, [interviews])

  const candidateRows = useMemo(() => {
    return applications.filter((application) => {
      const candidate = candidateMap.get(application.candidate_id)
      const requisition = requisitionMap.get(application.requisition_id)
      const haystack = `${candidate?.full_name || ''} ${candidate?.email || ''} ${requisition?.title || ''}`.toLowerCase()
      if (search && !haystack.includes(search.toLowerCase())) return false
      if (draft.stageFilter && application.current_stage_id !== draft.stageFilter) return false
      if (draft.jobFilter && application.requisition_id !== draft.jobFilter) return false
      if (draft.recruiterFilter && application.submitted_by !== draft.recruiterFilter) return false
      if (draft.interviewTypeFilter) {
        const types = existingInterviewTypesByApplication.get(application.id) || []
        if (!types.includes(draft.interviewTypeFilter)) return false
      }
      return true
    })
  }, [applications, candidateMap, requisitionMap, search, draft.stageFilter, draft.jobFilter, draft.recruiterFilter, draft.interviewTypeFilter, existingInterviewTypesByApplication])

  const selectedApplications = useMemo(
    () => applications.filter((application) => draft.applicationIds.includes(application.id)),
    [applications, draft.applicationIds],
  )

  const generatedAssignments = useMemo(() => {
    const warnings: string[] = []
    const assignments = selectedApplications.map((application, index) => {
      const candidate = candidateMap.get(application.candidate_id)
      const job = requisitionMap.get(application.requisition_id)
      const startDate = draft.dateRange[0] || dayjs().add(1, 'day').startOf('day').toISOString()
      let scheduledAt = combineDateTime(startDate, 10, 0)

      if (draft.slotPattern === 'same_slot') {
        scheduledAt = combineDateTime(startDate, 10, 0)
      } else if (draft.slotPattern === 'sequential_slots') {
        scheduledAt = dayjs(combineDateTime(startDate, 10, 0)).add(index * draft.durationMinutes, 'minute').toISOString()
      } else {
        scheduledAt = dayjs(combineDateTime(startDate, 10, 0)).add(index * 30, 'minute').toISOString()
      }

      const interviewer =
        draft.slotPattern === 'interviewer_specific' && draft.interviewers.length
          ? [draft.interviewers[index % draft.interviewers.length]]
          : draft.interviewers

      const conflict = interviews.find(
        (item) =>
          item.scheduled_at &&
          interviewer.some((assigned) => (item.interviewers || []).includes(assigned)) &&
          Math.abs(dayjs(item.scheduled_at).diff(dayjs(scheduledAt), 'minute')) < draft.durationMinutes,
      )
      if (conflict) {
        warnings.push(`Possible interviewer conflict for ${candidate?.full_name || application.candidate_id} at ${dayjs(scheduledAt).format('DD MMM HH:mm')}`)
      }

      return {
        application,
        candidateName: candidate?.full_name || candidate?.email || application.candidate_id,
        jobTitle: job?.title || application.requisition_id,
        scheduledAt,
        interviewers: interviewer,
      }
    })

    return { assignments, warnings }
  }, [selectedApplications, candidateMap, requisitionMap, draft.dateRange, draft.slotPattern, draft.durationMinutes, draft.interviewers, interviews])

  const selectionColumns: ColumnsType<Application> = [
    {
      title: 'Candidate',
      key: 'candidate',
      render: (_, record) => {
        const candidate = candidateMap.get(record.candidate_id)
        return (
          <div className="min-w-0">
            <div className="font-semibold text-slate-900">{candidate?.full_name || candidate?.email || record.candidate_id}</div>
            <div className="text-xs text-slate-500">{candidate?.email || 'No email'}</div>
          </div>
        )
      },
    },
    {
      title: 'Job',
      key: 'job',
      render: (_, record) => <Text>{requisitionMap.get(record.requisition_id)?.title || record.requisition_id}</Text>,
    },
    {
      title: 'Stage',
      dataIndex: 'current_stage_id',
      key: 'stage',
      render: (value) => <Tag>{value || 'No stage'}</Tag>,
    },
    {
      title: 'Recruiter',
      dataIndex: 'submitted_by',
      key: 'submitted_by',
      render: (value) => <Text>{value || 'Unknown'}</Text>,
    },
    {
      title: 'Existing Types',
      key: 'types',
      render: (_, record) => {
        const types = existingInterviewTypesByApplication.get(record.id) || []
        return (
          <div className="flex flex-wrap gap-1">
            {types.length ? types.slice(0, 3).map((type) => <Tag key={type}>{getInterviewTypeLabel(type)}</Tag>) : <Text className="text-xs text-slate-400">None</Text>}
          </div>
        )
      },
    },
  ]

  const summary = result || {
    scheduled: [],
    failed: [],
    skipped: [],
    warnings: generatedAssignments.warnings,
  }

  const runBulkSchedule = async () => {
    if (!draft.applicationIds.length) {
      message.error('Select at least one candidate')
      setActiveStep('selection')
      return
    }
    if (!draft.interviewType) {
      message.error('Interview type is required')
      setActiveStep('setup')
      return
    }
    setRunning(true)
    const nextResult: BulkResult = { scheduled: [], failed: [], skipped: [], warnings: [...generatedAssignments.warnings] }

    for (const assignment of generatedAssignments.assignments) {
      if (!assignment.application.id || !assignment.application.requisition_id) {
        nextResult.skipped.push({ applicationId: assignment.application.id, reason: 'Missing application/job data' })
        continue
      }
      try {
        const response = await interviewsApi.create({
          application_id: assignment.application.id,
          interview_type: draft.interviewType,
          title: `${getInterviewTypeLabel(draft.interviewType)} · ${assignment.jobTitle}`,
          scheduled_at: assignment.scheduledAt,
          duration_minutes: draft.durationMinutes,
          interview_round: 1,
          interviewers: assignment.interviewers,
        })
        const created = (response as any)?.data?.data?.interview || (response as any)?.data?.interview
        nextResult.scheduled.push({ applicationId: assignment.application.id, interviewId: created?.id || 'created' })
      } catch (error: any) {
        nextResult.failed.push({ applicationId: assignment.application.id, reason: error?.response?.data?.message || 'Create failed' })
      }
    }

    setResult(nextResult)
    setRunning(false)
    await queryClient.invalidateQueries({ queryKey: ['bulk-scheduling-interviews'] })
    message.success(`Bulk scheduling finished: ${nextResult.scheduled.length} scheduled`)
    setActiveStep('summary')
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <Title level={3} className="!mb-1 !mt-0">Recruiter Bulk Scheduling</Title>
          <Text className="text-sm text-slate-500">
            High-volume recruiter scheduling workflow for bulk candidate selection, slot assignment, notifications, and confirmation.
          </Text>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Selected Candidates</div>
            <div className="mt-1 text-xl font-black text-slate-900">{draft.applicationIds.length}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Warnings</div>
            <div className="mt-1 text-xl font-black text-slate-900">{generatedAssignments.warnings.length}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <Card className="h-fit rounded-3xl border-slate-200 shadow-sm">
          <div className="space-y-2">
            {STEPS.map((step) => {
              const Icon = step.icon
              return (
                <button
                  key={step.key}
                  type="button"
                  onClick={() => setActiveStep(step.key)}
                  className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left transition ${
                    activeStep === step.key ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white">
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-black uppercase tracking-wider">{step.label}</span>
                </button>
              )
            })}
          </div>
        </Card>

        <div className="space-y-6">
          {activeStep === 'selection' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <Users className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Candidate Selection</div>
                  <div className="text-sm text-slate-500">Multi-select candidates and filter by stage, interview type, job, and recruiter.</div>
                </div>
              </div>

              <div className="mb-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <Input placeholder="Search candidate or job" value={search} onChange={(e) => setSearch(e.target.value)} />
                <Select value={draft.stageFilter} onChange={(value) => setDraft((current) => ({ ...current, stageFilter: value }))} options={[{ value: '', label: 'All Stages' }, ...stageOptions]} />
                <Select value={draft.interviewTypeFilter} onChange={(value) => setDraft((current) => ({ ...current, interviewTypeFilter: value }))} options={[{ value: '', label: 'All Interview Types' }, ...interviewTypeOptions]} />
                <Select value={draft.jobFilter} onChange={(value) => setDraft((current) => ({ ...current, jobFilter: value }))} options={[{ value: '', label: 'All Jobs' }, ...jobOptions]} />
                <Select value={draft.recruiterFilter} onChange={(value) => setDraft((current) => ({ ...current, recruiterFilter: value }))} options={[{ value: '', label: 'All Recruiters' }, ...recruiterOptions]} />
              </div>

              <Table
                rowKey="id"
                loading={isLoading}
                dataSource={candidateRows}
                columns={selectionColumns}
                rowSelection={{
                  selectedRowKeys: draft.applicationIds,
                  onChange: (keys) => setDraft((current) => ({ ...current, applicationIds: keys as string[] })),
                }}
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No candidates available for bulk scheduling" /> }}
              />
            </Card>
          ) : null}

          {activeStep === 'setup' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <CalendarDays className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Bulk Schedule Setup</div>
                  <div className="text-sm text-slate-500">Choose interview type, template, interviewer pool, date range, slot pattern, duration, and timezone.</div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interview Type</Text>
                  <Select value={draft.interviewType} onChange={(value) => setDraft((current) => ({ ...current, interviewType: value }))} options={interviewTypeOptions} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Template</Text>
                  <Select value={draft.templateId} onChange={(value) => setDraft((current) => ({ ...current, templateId: value }))} options={filteredTemplates.map((template: any) => ({ value: template.id, label: template.name }))} allowClear />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Interviewer(s)</Text>
                  <Select mode="multiple" value={draft.interviewers} onChange={(value) => setDraft((current) => ({ ...current, interviewers: value }))} options={interviewerOptions} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Start Date</Text>
                  <DatePicker className="w-full" value={draft.dateRange[0] ? dayjs(draft.dateRange[0]) : null} onChange={(value) => setDraft((current) => ({ ...current, dateRange: [value ? value.startOf('day').toISOString() : null, current.dateRange[1]] }))} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">End Date</Text>
                  <DatePicker className="w-full" value={draft.dateRange[1] ? dayjs(draft.dateRange[1]) : null} onChange={(value) => setDraft((current) => ({ ...current, dateRange: [current.dateRange[0], value ? value.startOf('day').toISOString() : null] }))} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Slot Pattern</Text>
                  <Select value={draft.slotPattern} onChange={(value) => setDraft((current) => ({ ...current, slotPattern: value }))} options={[
                    { value: 'same_slot', label: 'Same Slot For Many' },
                    { value: 'sequential_slots', label: 'Sequential Slots' },
                    { value: 'interviewer_specific', label: 'Interviewer-Specific Slots' },
                  ]} />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Duration</Text>
                  <InputNumber className="w-full" min={15} max={240} value={draft.durationMinutes} onChange={(value) => setDraft((current) => ({ ...current, durationMinutes: Number(value || 0) }))} addonAfter="min" />
                </div>
                <div>
                  <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Timezone</Text>
                  <Input value={draft.timezone} onChange={(e) => setDraft((current) => ({ ...current, timezone: e.target.value }))} placeholder="UTC" />
                </div>
              </div>
            </Card>
          ) : null}

          {activeStep === 'slots' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <Clock3 className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Slot Assignment</div>
                  <div className="text-sm text-slate-500">Review assigned slots, interviewer distribution, and obvious conflict warnings.</div>
                </div>
              </div>

              {generatedAssignments.warnings.length ? (
                <Alert
                  className="mb-4"
                  type="warning"
                  showIcon
                  message="Conflict warnings detected"
                  description={
                    <div className="space-y-1">
                      {generatedAssignments.warnings.map((warning) => <div key={warning}>{warning}</div>)}
                    </div>
                  }
                />
              ) : null}

              <Table
                rowKey={(row) => row.application.id}
                dataSource={generatedAssignments.assignments}
                pagination={false}
                columns={[
                  { title: 'Candidate', key: 'candidate', render: (_, row: any) => row.candidateName },
                  { title: 'Job', key: 'job', render: (_, row: any) => row.jobTitle },
                  { title: 'Assigned Slot', key: 'slot', render: (_, row: any) => dayjs(row.scheduledAt).format('DD MMM YYYY · hh:mm A') },
                  { title: 'Interviewer(s)', key: 'interviewers', render: (_, row: any) => row.interviewers.length ? row.interviewers.join(', ') : 'Unassigned' },
                ]}
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No slot assignments generated yet" /> }}
              />
            </Card>
          ) : null}

          {activeStep === 'notifications' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <Bell className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Notifications</div>
                  <div className="text-sm text-slate-500">Choose which scheduling notifications should be triggered on bulk confirmation.</div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Checkbox checked={draft.sendInviteNow} onChange={(e) => setDraft((current) => ({ ...current, sendInviteNow: e.target.checked }))}>Send invite now</Checkbox>
                <Checkbox checked={draft.sendReminder} onChange={(e) => setDraft((current) => ({ ...current, sendReminder: e.target.checked }))}>Send reminder</Checkbox>
                <Checkbox checked={draft.notifyRecruiter} onChange={(e) => setDraft((current) => ({ ...current, notifyRecruiter: e.target.checked }))}>Notify recruiter</Checkbox>
                <Checkbox checked={draft.notifyInterviewer} onChange={(e) => setDraft((current) => ({ ...current, notifyInterviewer: e.target.checked }))}>Notify interviewer</Checkbox>
                <Checkbox checked={draft.notifyCandidate} onChange={(e) => setDraft((current) => ({ ...current, notifyCandidate: e.target.checked }))}>Notify candidate</Checkbox>
              </div>
            </Card>
          ) : null}

          {activeStep === 'review' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <ListChecks className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Review & Confirm</div>
                  <div className="text-sm text-slate-500">Final review of candidates, slots, interviewers, warnings, and notification rules.</div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Candidates</div>
                  <div className="mt-2 text-lg font-black text-slate-900">{draft.applicationIds.length}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interview Type</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{draft.interviewType ? getInterviewTypeLabel(draft.interviewType) : 'Not selected'}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Slot Pattern</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{draft.slotPattern.replace(/_/g, ' ')}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Warnings</div>
                  <div className="mt-2 text-lg font-black text-slate-900">{generatedAssignments.warnings.length}</div>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button type="primary" loading={running} onClick={runBulkSchedule}>Confirm Bulk Schedule</Button>
                <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => setActiveStep('selection')}>Rework Selection</Button>
              </div>
            </Card>
          ) : null}

          {activeStep === 'summary' ? (
            <Card className="rounded-3xl border-slate-200 shadow-sm">
              <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-black uppercase tracking-wider text-slate-900">Result Summary</div>
                  <div className="text-sm text-slate-500">Scheduled count, failed count, skipped count, and warnings from the bulk run.</div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Scheduled</div>
                  <div className="mt-2 text-xl font-black text-slate-900">{summary.scheduled.length}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Failed</div>
                  <div className="mt-2 text-xl font-black text-slate-900">{summary.failed.length}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Skipped</div>
                  <div className="mt-2 text-xl font-black text-slate-900">{summary.skipped.length}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Warnings</div>
                  <div className="mt-2 text-xl font-black text-slate-900">{summary.warnings.length}</div>
                </div>
              </div>

              <div className="mt-6 grid gap-6 xl:grid-cols-2">
                <Card size="small" title="Failures">
                  {summary.failed.length ? summary.failed.map((item) => (
                    <div key={`${item.applicationId}-${item.reason}`} className="mb-2 text-sm text-slate-600">{item.applicationId}: {item.reason}</div>
                  )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No failures" />}
                </Card>
                <Card size="small" title="Warnings">
                  {summary.warnings.length ? summary.warnings.map((warning) => (
                    <div key={warning} className="mb-2 text-sm text-slate-600">{warning}</div>
                  )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No warnings" />}
                </Card>
              </div>
            </Card>
          ) : null}

          <div className="flex items-center justify-between">
            <Button
              onClick={() => setActiveStep(STEPS[Math.max(STEPS.findIndex((step) => step.key === activeStep) - 1, 0)].key)}
              disabled={activeStep === 'selection'}
            >
              Back
            </Button>
            <Button
              type="primary"
              onClick={() => setActiveStep(STEPS[Math.min(STEPS.findIndex((step) => step.key === activeStep) + 1, STEPS.length - 1)].key)}
              disabled={activeStep === 'summary'}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
