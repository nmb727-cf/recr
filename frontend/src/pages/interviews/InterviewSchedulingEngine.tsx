import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  TimePicker,
  Typography,
  message,
} from 'antd'
import {
  Calendar,
  Copy,
  Link2,
  Users,
  XCircle,
} from 'lucide-react'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { interviewsApi } from '@/api/interviews'
import { candidatesApi } from '@/api/candidates'
import { requisitionsApi } from '@/api/jobs'
import { pipelineApi } from '@/api/pipeline'
import { useApiQuery } from '@/hooks/useApiQuery'
import { getInterviewTypeLabel } from '@/utils/interviewTypeUx'

const { Title, Text } = Typography

const WEEKDAYS = [
  { key: 'mon', label: 'Mon' },
  { key: 'tue', label: 'Tue' },
  { key: 'wed', label: 'Wed' },
  { key: 'thu', label: 'Thu' },
  { key: 'fri', label: 'Fri' },
  { key: 'sat', label: 'Sat' },
  { key: 'sun', label: 'Sun' },
]

const MODE_OPTIONS = [
  { value: 'manual', label: 'Manual Scheduling' },
  { value: 'system', label: 'System Availability Scheduling' },
  { value: 'calendar', label: 'Calendar-Based Scheduling' },
  { value: 'candidate_self', label: 'Candidate Self Scheduling' },
]

function parseApiData<T = any>(response: any, key: string, fallback: T): T {
  return response?.[key] ?? response?.data?.[key] ?? fallback
}

function combineDateTime(dateValue: any, timeValue?: any) {
  if (!dateValue) return null
  if (!timeValue) return dayjs(dateValue).toISOString()
  const merged = dayjs(dateValue)
    .hour(dayjs(timeValue).hour())
    .minute(dayjs(timeValue).minute())
    .second(0)
    .millisecond(0)
  return merged.toISOString()
}

export default function InterviewSchedulingEngine() {
  const queryClient = useQueryClient()
  const [scheduleForm] = Form.useForm()
  const [availabilityForm] = Form.useForm()
  const [blockForm] = Form.useForm()
  const [selfScheduleForm] = Form.useForm()
  const [calendarForm] = Form.useForm()
  const [slotFinderForm] = Form.useForm()
  const [rescheduleForm] = Form.useForm()
  const [cancelForm] = Form.useForm()

  const [selectedInterview, setSelectedInterview] = useState<any | null>(null)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const selectedInterviewType = Form.useWatch('interview_type', scheduleForm)

  const { data: interviewsRes, isLoading } = useApiQuery(['icc-scheduling-interviews'], () => interviewsApi.list())
  const { data: typesRes } = useApiQuery(['icc-scheduling-types'], () => interviewsApi.listTypes())
  const { data: templatesRes } = useApiQuery(['icc-scheduling-templates'], () => interviewsApi.listTemplates())
  const { data: flowsRes } = useApiQuery(['icc-scheduling-flows'], () => interviewsApi.listFlows())
  const { data: profileRes } = useApiQuery(['icc-scheduling-profile'], () => interviewsApi.getAvailabilityProfile())
  const { data: blocksRes } = useApiQuery(['icc-scheduling-blocks'], () => interviewsApi.listAvailabilityBlocks())
  const { data: calendarRes } = useApiQuery(['icc-scheduling-calendar'], () => interviewsApi.listCalendarConnections())
  const { data: candidatesRes } = useApiQuery(['icc-scheduling-candidates'], () => candidatesApi.list({ search: '' }))
  const { data: jobsRes } = useApiQuery(['icc-scheduling-jobs'], () => requisitionsApi.list({ status: 'active' }))
  const { data: applicationsRes } = useApiQuery(['icc-scheduling-applications'], () => pipelineApi.listApplications())

  const interviews = parseApiData(interviewsRes, 'interviews', [])
  const interviewTypes = parseApiData(typesRes, 'types', [])
  const templates = parseApiData(templatesRes, 'templates', [])
  const flows = parseApiData(flowsRes, 'flows', [])
  const profile = parseApiData(profileRes, 'profile', null)
  const blocks = parseApiData(blocksRes, 'blocks', [])
  const connections = parseApiData(calendarRes, 'connections', [])
  const candidates = parseApiData(candidatesRes, 'candidates', [])
  const requisitions = parseApiData(jobsRes, 'requisitions', [])
  const applications = parseApiData(applicationsRes, 'applications', [])

  const candidateMap = useMemo(() => new Map(candidates.map((candidate: any) => [candidate.id, candidate])), [candidates])
  const requisitionMap = useMemo(() => new Map(requisitions.map((job: any) => [job.id, job])), [requisitions])
  const templateMap = useMemo(() => new Map(templates.map((template: any) => [template.id, template])), [templates])

  const applicationOptions = useMemo(() => {
    return applications.map((application: any) => {
      const candidate = candidateMap.get(application.candidate_id)
      const requisition = requisitionMap.get(application.requisition_id)
      return {
        value: application.id,
        label: `${candidate?.full_name || candidate?.email || application.candidate_id} • ${requisition?.title || application.requisition_id}`,
        application,
      }
    })
  }, [applications, candidateMap, requisitionMap])

  const interviewerOptions = useMemo(() => {
    const ids = new Set<string>()
    connections.forEach((connection: any) => {
      if (connection.interviewer_id) ids.add(connection.interviewer_id)
    })
    interviews.forEach((interview: any) => {
      ;(interview.interviewers || []).forEach((id: string) => ids.add(id))
      ;(interview.panelists || []).forEach((panelist: any) => {
        if (panelist?.interviewer_id) ids.add(panelist.interviewer_id)
      })
    })
    if (profile?.interviewer_id) ids.add(profile.interviewer_id)
    return Array.from(ids).map((id) => ({ value: id, label: id.slice(0, 8) }))
  }, [connections, interviews, profile])

  const flowStageOptions = useMemo(() => {
    const stageMap = new Map<string, { value: string; label: string }>()
    flows.forEach((flow: any) => {
      ;(flow.stages || []).forEach((stage: any) => {
        const key = stage.id || `${flow.id}:${stage.name}`
        stageMap.set(key, {
          value: stage.name || key,
          label: `${flow.name || 'Flow'} • ${stage.name || 'Stage'}`,
        })
      })
    })
    applications.forEach((application: any) => {
      if (application.current_stage_id) {
        stageMap.set(application.current_stage_id, {
          value: application.current_stage_id,
          label: `Current Stage • ${application.current_stage_id}`,
        })
      }
    })
    return Array.from(stageMap.values())
  }, [applications, flows])

  const availableTemplates = useMemo(() => {
    if (!selectedInterviewType) return templates
    return templates.filter((template: any) => template.interview_type === selectedInterviewType)
  }, [selectedInterviewType, templates])

  const availabilityInitial = useMemo(() => {
    const workingHours = profile?.working_hours || {}
    const initial: Record<string, any> = {
      mode: profile?.mode || 'system',
      timezone: profile?.timezone || 'UTC',
      default_duration_minutes: profile?.default_duration_minutes || 60,
      default_buffer_minutes: profile?.default_buffer_minutes || 15,
    }
    WEEKDAYS.forEach((day) => {
      initial[`${day.key}_enabled`] = workingHours?.[day.key]?.enabled ?? (day.key !== 'sat' && day.key !== 'sun')
      initial[`${day.key}_start`] = dayjs(workingHours?.[day.key]?.start || '09:00', 'HH:mm')
      initial[`${day.key}_end`] = dayjs(workingHours?.[day.key]?.end || '18:00', 'HH:mm')
    })
    return initial
  }, [profile])

  useEffect(() => {
    availabilityForm.setFieldsValue(availabilityInitial)
  }, [availabilityForm, availabilityInitial])

  const upsertProfile = useMutation({
    mutationFn: (payload: any) => interviewsApi.updateAvailabilityProfile(payload),
    onSuccess: () => {
      message.success('Availability settings saved')
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-profile'] })
    },
  })

  const addBlock = useMutation({
    mutationFn: (payload: any) => interviewsApi.createAvailabilityBlock(payload),
    onSuccess: () => {
      message.success('Blocked time added')
      blockForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-blocks'] })
    },
  })

  const scheduleMutation = useMutation({
    mutationFn: (payload: any) => interviewsApi.manualSchedule(payload),
    onSuccess: () => {
      message.success('Interview scheduled')
      scheduleForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-interviews'] })
    },
  })

  const slotMutation = useMutation({
    mutationFn: (payload: any) => interviewsApi.getPanelSlots(payload),
  })

  const linkMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => interviewsApi.createSchedulingLink(id, payload),
    onSuccess: async (_, variables) => {
      message.success('Scheduling link generated')
      await queryClient.invalidateQueries({ queryKey: ['icc-scheduling-interviews'] })
      selfScheduleForm.setFieldsValue({ interview_id: variables.id })
    },
  })

  const calendarMutation = useMutation({
    mutationFn: (payload: any) => interviewsApi.saveCalendarConnection(payload),
    onSuccess: () => {
      message.success('Calendar connection saved')
      calendarForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-calendar'] })
    },
  })

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, scheduled_at }: { id: string; scheduled_at: string }) => interviewsApi.reschedule(id, { scheduled_at }),
    onSuccess: () => {
      message.success('Interview rescheduled')
      setRescheduleOpen(false)
      rescheduleForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-interviews'] })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => interviewsApi.cancelInterviewFlex(id, { reason }),
    onSuccess: () => {
      message.success('Interview cancelled')
      setCancelOpen(false)
      cancelForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['icc-scheduling-interviews'] })
    },
  })

  const slots = parseApiData(slotMutation.data, 'slots', [])
  const fallbackSuggestions = parseApiData(slotMutation.data, 'fallback_suggestions', [])
  const generatedLink = parseApiData(linkMutation.data, 'scheduling_url', '')

  const scheduledInterviews = interviews.filter((interview: any) => ['scheduled', 'rescheduled', 'confirmed'].includes(interview.status))
  const upcomingInterviews = scheduledInterviews
    .filter((interview: any) => interview.scheduled_at)
    .sort((a: any, b: any) => dayjs(a.scheduled_at).valueOf() - dayjs(b.scheduled_at).valueOf())

  const stats = {
    upcoming: upcomingInterviews.length,
    selfScheduling: interviews.filter((interview: any) => interview.metadata?.schedule_mode === 'candidate_self').length,
    panel: interviews.filter((interview: any) => (interview.interviewers || []).length > 1).length,
    cancelled: interviews.filter((interview: any) => interview.status === 'cancelled').length,
  }

  const scheduleColumns: ColumnsType<any> = [
    {
      title: 'Interview',
      render: (_, record) => (
        <div>
          <Text className="block font-bold text-slate-900">{record.title || getInterviewTypeLabel(record.interview_type)}</Text>
          <Text className="text-xs text-slate-500">{candidateMap.get(record.candidate_id)?.full_name || record.candidate_id}</Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'interview_type',
      render: (value: string) => <Tag color="blue">{getInterviewTypeLabel(value)}</Tag>,
    },
    {
      title: 'Template',
      render: (_, record) => <Text className="text-slate-600">{templateMap.get(record.template_id)?.name || 'Not linked'}</Text>,
    },
    {
      title: 'Scheduled',
      dataIndex: 'scheduled_at',
      render: (value: string) => value ? dayjs(value).format('MMM D, YYYY HH:mm') : '-',
    },
    {
      title: 'Mode',
      render: (_, record) => <Tag>{record.metadata?.schedule_mode || 'manual'}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (value: string) => <Tag color={value === 'cancelled' ? 'red' : value === 'rescheduled' ? 'gold' : 'green'}>{value}</Tag>,
    },
    {
      title: 'Actions',
      render: (_, record) => (
        <Space size={4}>
          <Button size="small" onClick={() => {
            setSelectedInterview(record)
            rescheduleForm.setFieldsValue({ scheduled_at: dayjs(record.scheduled_at) })
            setRescheduleOpen(true)
          }}>
            Reschedule
          </Button>
          <Button size="small" onClick={() => {
            setSelectedInterview(record)
            selfScheduleForm.setFieldsValue({ interview_id: record.id, timezone: record.metadata?.schedule_timezone || 'UTC', expires_in_days: 7 })
          }}>
            Self Schedule
          </Button>
          <Button size="small" danger onClick={() => {
            setSelectedInterview(record)
            setCancelOpen(true)
          }}>
            Cancel
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} className="!m-0">Flexible Scheduling Engine</Title>
          <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">Manual, system, calendar-based, and candidate self-scheduling</Text>
        </div>
        <Tag color="blue">ICC-SCHEDULING-ENGINE-01</Tag>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card><Statistic title="Upcoming Interviews" value={stats.upcoming} prefix={<Calendar size={14} />} /></Card>
        <Card><Statistic title="Candidate Self-Scheduling" value={stats.selfScheduling} prefix={<Link2 size={14} />} /></Card>
        <Card><Statistic title="Panel Interviews" value={stats.panel} prefix={<Users size={14} />} /></Card>
        <Card><Statistic title="Cancelled / Closed" value={stats.cancelled} prefix={<XCircle size={14} />} /></Card>
      </div>

      <Tabs
        items={[
          {
            key: 'schedule',
            label: 'Schedule Interview',
            children: (
              <div className="grid grid-cols-12 gap-6">
                <div className="col-span-12 xl:col-span-8">
                  <Card title="Schedule Wizard" className="border-slate-200">
                    <Form
                      form={scheduleForm}
                      layout="vertical"
                      initialValues={{ mode: 'manual', timezone: profile?.timezone || 'UTC', duration_minutes: 60 }}
                      onFinish={(values) => {
                        const selectedApplication = applicationOptions.find((item) => item.value === values.application_id)?.application
                        const selectedTemplate = templates.find((template: any) => template.id === values.template_id)
                        scheduleMutation.mutate({
                          application_id: values.application_id,
                          candidate_id: selectedApplication?.candidate_id,
                          requisition_id: selectedApplication?.requisition_id,
                          interview_type: values.interview_type,
                          title: values.title || selectedTemplate?.name || getInterviewTypeLabel(values.interview_type),
                          scheduled_at: combineDateTime(values.date, values.time),
                          duration_minutes: values.duration_minutes,
                          panelist_ids: values.interviewer_ids || [],
                          timezone: values.timezone,
                          interview_round: 1,
                          execution_mode: values.mode === 'calendar' ? 'third_party' : values.mode === 'manual' ? 'native' : 'external_manual',
                          execution_provider_code: values.calendar_provider || undefined,
                          metadata: {
                            schedule_mode: values.mode,
                            template_id: values.template_id,
                            stage_name: values.stage_name,
                            notify_recruiter: values.notify_recruiter ?? true,
                          },
                        })
                      }}
                    >
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <Form.Item name="application_id" label="Candidate / Application" rules={[{ required: true }]}>
                          <Select
                            showSearch
                            optionFilterProp="label"
                            options={applicationOptions.map((item) => ({ value: item.value, label: item.label }))}
                            onChange={(value) => {
                              const selectedApplication = applicationOptions.find((item) => item.value === value)?.application
                              const candidate = candidateMap.get(selectedApplication?.candidate_id)
                              const job = requisitionMap.get(selectedApplication?.requisition_id)
                              scheduleForm.setFieldsValue({
                                title: `${candidate?.full_name || 'Candidate'} • ${job?.title || 'Interview'}`,
                              })
                            }}
                          />
                        </Form.Item>
                        <Form.Item name="mode" label="Scheduling Mode" rules={[{ required: true }]}>
                          <Select options={MODE_OPTIONS} />
                        </Form.Item>
                        <Form.Item name="interview_type" label="Interview Type" rules={[{ required: true }]}>
                          <Select showSearch optionFilterProp="label" options={interviewTypes.map((type: any) => ({ value: type.code, label: type.name }))} />
                        </Form.Item>
                        <Form.Item name="template_id" label="Template">
                          <Select allowClear showSearch optionFilterProp="label" options={availableTemplates.map((template: any) => ({ value: template.id, label: template.name }))} />
                        </Form.Item>
                        <Form.Item name="stage_name" label="Stage">
                          <Select allowClear showSearch optionFilterProp="label" options={flowStageOptions} />
                        </Form.Item>
                        <Form.Item name="interviewer_ids" label="Interviewer(s)">
                          <Select mode="multiple" allowClear options={interviewerOptions} placeholder="Select interviewer IDs" />
                        </Form.Item>
                        <Form.Item name="date" label="Date" rules={[{ required: true }]}>
                          <DatePicker className="w-full" />
                        </Form.Item>
                        <Form.Item name="time" label="Time" rules={[{ required: true }]}>
                          <TimePicker className="w-full" format="HH:mm" />
                        </Form.Item>
                        <Form.Item name="duration_minutes" label="Duration">
                          <InputNumber min={15} max={240} className="w-full" addonAfter="min" />
                        </Form.Item>
                        <Form.Item name="timezone" label="Timezone">
                          <Input />
                        </Form.Item>
                        <Form.Item name="calendar_provider" label="Calendar Provider (Optional)">
                          <Select allowClear options={[
                            { value: 'google_calendar', label: 'Google Calendar' },
                            { value: 'outlook_calendar', label: 'Outlook Calendar' },
                            { value: 'apple_calendar', label: 'Apple Calendar' },
                            { value: 'ics_external', label: 'ICS' },
                          ]} />
                        </Form.Item>
                        <Form.Item name="title" label="Interview Title">
                          <Input placeholder="Optional custom title" />
                        </Form.Item>
                      </div>
                      <Button type="primary" htmlType="submit" loading={scheduleMutation.isPending}>Schedule Interview</Button>
                    </Form>
                  </Card>
                </div>

                <div className="col-span-12 xl:col-span-4">
                  <Space direction="vertical" size={16} className="w-full">
                    <Card title="Panel / Common Slot Logic" className="border-slate-200">
                      <Form
                        form={slotFinderForm}
                        layout="vertical"
                        initialValues={{ timezone: profile?.timezone || 'UTC', duration_minutes: 60 }}
                        onFinish={(values) => {
                          slotMutation.mutate({
                            panelist_ids: values.panelist_ids || [],
                            from_date: values.from_date?.format('YYYY-MM-DD'),
                            to_date: values.to_date?.format('YYYY-MM-DD'),
                            timezone: values.timezone,
                            duration_minutes: values.duration_minutes,
                          })
                        }}
                      >
                        <Form.Item name="panelist_ids" label="Interviewer(s)" rules={[{ required: true }]}>
                          <Select mode="multiple" options={interviewerOptions} />
                        </Form.Item>
                        <div className="grid grid-cols-2 gap-3">
                          <Form.Item name="from_date" label="From" rules={[{ required: true }]}><DatePicker className="w-full" /></Form.Item>
                          <Form.Item name="to_date" label="To" rules={[{ required: true }]}><DatePicker className="w-full" /></Form.Item>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <Form.Item name="duration_minutes" label="Duration"><InputNumber min={15} className="w-full" /></Form.Item>
                          <Form.Item name="timezone" label="Timezone"><Input /></Form.Item>
                        </div>
                        <Button htmlType="submit" loading={slotMutation.isPending}>Find Common Slots</Button>
                      </Form>

                      <div className="mt-4 space-y-2 max-h-[360px] overflow-y-auto pr-1">
                        {slots.map((slot: any) => (
                          <Alert
                            key={`${slot.starts_at}-${slot.ends_at}`}
                            type="info"
                            showIcon
                            message={`${dayjs(slot.starts_at).format('ddd, MMM D YYYY HH:mm')} - ${dayjs(slot.ends_at).format('HH:mm')}`}
                            description={
                              <Button
                                size="small"
                                onClick={() => {
                                  const start = dayjs(slot.starts_at)
                                  scheduleForm.setFieldsValue({ date: start, time: start, timezone: slot.timezone })
                                }}
                              >
                                Use Slot
                              </Button>
                            }
                          />
                        ))}
                        {fallbackSuggestions.length > 0 ? (
                          <Alert type="warning" showIcon message={`Fallback options available: ${fallbackSuggestions.length}`} />
                        ) : null}
                      </div>
                    </Card>
                  </Space>
                </div>
              </div>
            ),
          },
          {
            key: 'availability',
            label: 'Availability Modes',
            children: (
              <div className="grid grid-cols-12 gap-6">
                <div className="col-span-12 xl:col-span-7">
                  <Card title="System Availability Profile" className="border-slate-200">
                    <Form
                      form={availabilityForm}
                      layout="vertical"
                      onFinish={(values) => {
                        const working_hours: Record<string, any> = {}
                        WEEKDAYS.forEach((day) => {
                          working_hours[day.key] = {
                            enabled: Boolean(values[`${day.key}_enabled`]),
                            start: values[`${day.key}_start`]?.format?.('HH:mm') || '09:00',
                            end: values[`${day.key}_end`]?.format?.('HH:mm') || '18:00',
                          }
                        })
                        upsertProfile.mutate({
                          mode: values.mode,
                          timezone: values.timezone,
                          default_duration_minutes: values.default_duration_minutes,
                          default_buffer_minutes: values.default_buffer_minutes,
                          working_hours,
                        })
                      }}
                    >
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <Form.Item name="mode" label="Availability Mode">
                          <Select options={MODE_OPTIONS} />
                        </Form.Item>
                        <Form.Item name="timezone" label="Timezone">
                          <Input />
                        </Form.Item>
                        <Form.Item name="default_duration_minutes" label="Default Duration">
                          <InputNumber className="w-full" min={15} addonAfter="min" />
                        </Form.Item>
                        <Form.Item name="default_buffer_minutes" label="Buffer">
                          <InputNumber className="w-full" min={0} addonAfter="min" />
                        </Form.Item>
                      </div>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        {WEEKDAYS.map((day) => (
                          <Card key={day.key} size="small">
                            <div className="mb-2 font-medium">{day.label}</div>
                            <Form.Item name={`${day.key}_enabled`} className="!mb-2">
                              <Select options={[{ value: true, label: 'Working' }, { value: false, label: 'Blocked' }]} />
                            </Form.Item>
                            <Space>
                              <Form.Item name={`${day.key}_start`} className="!mb-0"><TimePicker format="HH:mm" /></Form.Item>
                              <Form.Item name={`${day.key}_end`} className="!mb-0"><TimePicker format="HH:mm" /></Form.Item>
                            </Space>
                          </Card>
                        ))}
                      </div>
                      <Button type="primary" htmlType="submit" loading={upsertProfile.isPending} className="mt-4">Save Availability</Button>
                    </Form>
                  </Card>
                </div>

                <div className="col-span-12 xl:col-span-5">
                  <Space direction="vertical" size={16} className="w-full">
                    <Card title="Blocked Time / Manual Holds" className="border-slate-200">
                      <Form
                        form={blockForm}
                        layout="vertical"
                        onFinish={(values) => {
                          addBlock.mutate({
                            starts_at: values.range?.[0]?.toISOString(),
                            ends_at: values.range?.[1]?.toISOString(),
                            reason: values.reason,
                          })
                        }}
                      >
                        <Form.Item name="range" label="Blocked Range" rules={[{ required: true }]}>
                          <DatePicker.RangePicker showTime className="w-full" />
                        </Form.Item>
                        <Form.Item name="reason" label="Reason">
                          <Input placeholder="Leave, hiring sync, external meeting" />
                        </Form.Item>
                        <Button htmlType="submit" type="primary" loading={addBlock.isPending}>Add Block</Button>
                      </Form>
                      <div className="mt-4 max-h-[260px] overflow-y-auto pr-1">
                        <Table
                          size="small"
                          rowKey="id"
                          dataSource={blocks}
                          pagination={false}
                          columns={[
                            { title: 'Start', dataIndex: 'starts_at', render: (value) => dayjs(value).format('MMM D HH:mm') },
                            { title: 'End', dataIndex: 'ends_at', render: (value) => dayjs(value).format('MMM D HH:mm') },
                            { title: 'Reason', dataIndex: 'reason' },
                          ]}
                        />
                      </div>
                    </Card>

                    <Card title="Calendar-Based Scheduling" className="border-slate-200">
                      <Alert type="info" showIcon message="Calendar support is optional. Configure Google, Outlook, Apple, or ICS only when needed." className="mb-4" />
                      <Form
                        form={calendarForm}
                        layout="vertical"
                        onFinish={(values) => calendarMutation.mutate(values)}
                      >
                        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                          <Form.Item name="provider" label="Provider" rules={[{ required: true }]}>
                            <Select options={[
                              { value: 'google_calendar', label: 'Google Calendar' },
                              { value: 'outlook_calendar', label: 'Outlook Calendar' },
                              { value: 'apple_calendar', label: 'Apple Calendar' },
                              { value: 'ics_external', label: 'ICS' },
                            ]} />
                          </Form.Item>
                          <Form.Item name="external_calendar_id" label="Calendar ID"><Input /></Form.Item>
                          <Form.Item name="account_email" label="Account Email"><Input /></Form.Item>
                          <Form.Item name="sync_enabled" label="Sync Enabled" initialValue={true}>
                            <Select options={[{ value: true, label: 'Enabled' }, { value: false, label: 'Config Only' }]} />
                          </Form.Item>
                        </div>
                        <Button htmlType="submit" loading={calendarMutation.isPending}>Save Connection</Button>
                      </Form>
                      <div className="mt-4 max-h-[180px] overflow-y-auto pr-1">
                        {connections.map((connection: any) => (
                          <Alert key={connection.id} type="success" showIcon message={`${connection.provider} • ${connection.account_email || 'No email'}`} description={connection.external_calendar_id || 'No calendar id'} className="mb-2" />
                        ))}
                      </div>
                    </Card>
                  </Space>
                </div>
              </div>
            ),
          },
          {
            key: 'candidate-self',
            label: 'Candidate Self Scheduling',
            children: (
              <div className="grid grid-cols-12 gap-6">
                <div className="col-span-12 xl:col-span-7">
                  <Card title="Generate Candidate Scheduling Link" className="border-slate-200">
                    <Form
                      form={selfScheduleForm}
                      layout="vertical"
                      initialValues={{ timezone: profile?.timezone || 'UTC', expires_in_days: 7 }}
                      onFinish={(values) => {
                        linkMutation.mutate({
                          id: values.interview_id,
                          payload: {
                            timezone: values.timezone,
                            expires_in_days: values.expires_in_days,
                          },
                        })
                      }}
                    >
                      <Form.Item name="interview_id" label="Interview" rules={[{ required: true }]}>
                        <Select
                          showSearch
                          optionFilterProp="label"
                          options={scheduledInterviews.map((interview: any) => ({
                            value: interview.id,
                            label: `${interview.title || getInterviewTypeLabel(interview.interview_type)} • ${candidateMap.get(interview.candidate_id)?.full_name || interview.candidate_id}`,
                          }))}
                        />
                      </Form.Item>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <Form.Item name="timezone" label="Timezone"><Input /></Form.Item>
                        <Form.Item name="expires_in_days" label="Expires In"><InputNumber min={1} max={30} className="w-full" addonAfter="days" /></Form.Item>
                      </div>
                      <Button type="primary" htmlType="submit" loading={linkMutation.isPending}>Generate Link</Button>
                    </Form>
                    {generatedLink ? (
                      <Alert
                        className="mt-4"
                        type="success"
                        showIcon
                        message={generatedLink}
                        description={<Button size="small" icon={<Copy size={12} />} onClick={() => navigator.clipboard?.writeText(generatedLink)}>Copy link</Button>}
                      />
                    ) : null}
                  </Card>
                </div>
                <div className="col-span-12 xl:col-span-5">
                  <Card title="Mode Coverage" className="border-slate-200">
                    <div className="space-y-3">
                      <Alert type="info" showIcon message="Manual Scheduling" description="Recruiter selects exact date, time, interviewers, and template." />
                      <Alert type="info" showIcon message="System Availability" description="Use working hours and blocked time to find valid interviewer slots." />
                      <Alert type="info" showIcon message="Calendar-Based" description="Optional provider configuration for Google, Outlook, Apple, or ICS." />
                      <Alert type="info" showIcon message="Candidate Self Scheduling" description="Share a scheduling link so the candidate picks a slot." />
                    </div>
                  </Card>
                </div>
              </div>
            ),
          },
          {
            key: 'upcoming',
            label: 'Upcoming Interviews',
            children: (
              <Card title="Upcoming / Scheduled Interviews" className="border-slate-200">
                <Table
                  rowKey="id"
                  loading={isLoading}
                  dataSource={upcomingInterviews}
                  columns={scheduleColumns}
                  pagination={{ pageSize: 8 }}
                />
              </Card>
            ),
          },
        ]}
      />

      <Modal
        open={rescheduleOpen}
        title="Reschedule Interview"
        onCancel={() => setRescheduleOpen(false)}
        onOk={() => rescheduleForm.submit()}
        confirmLoading={rescheduleMutation.isPending}
        destroyOnHidden
      >
        <Form
          form={rescheduleForm}
          layout="vertical"
          onFinish={(values) => {
            if (!selectedInterview?.id) return
            rescheduleMutation.mutate({
              id: selectedInterview.id,
              scheduled_at: values.scheduled_at?.toISOString(),
            })
          }}
        >
          <Form.Item name="scheduled_at" label="New Schedule" rules={[{ required: true }]}>
            <DatePicker showTime className="w-full" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={cancelOpen}
        title="Cancel Interview"
        onCancel={() => setCancelOpen(false)}
        onOk={() => cancelForm.submit()}
        confirmLoading={cancelMutation.isPending}
        destroyOnHidden
      >
        <Form
          form={cancelForm}
          layout="vertical"
          onFinish={(values) => {
            if (!selectedInterview?.id) return
            cancelMutation.mutate({ id: selectedInterview.id, reason: values.reason })
          }}
        >
          <Form.Item name="reason" label="Reason">
            <Input.TextArea rows={4} placeholder="Reason for cancellation and notification context" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
