import { useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Modal,
  Radio,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import dayjs from 'dayjs'
import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  RefreshCw,
  XCircle,
} from 'lucide-react'

import { interviewsApi } from '@/api/interviews'
import { useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

type GroupedSlot = {
  dateKey: string
  dateLabel: string
  slots: Array<{
    label: string
    value: string
    timezone: string
    raw: any
  }>
}

function statusColor(status?: string) {
  switch (status) {
    case 'scheduled':
      return 'blue'
    case 'rescheduled':
      return 'purple'
    case 'cancelled':
      return 'red'
    case 'pending':
      return 'gold'
    default:
      return 'default'
  }
}

function formatInterviewType(value?: string) {
  if (!value) return '-'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export default function CandidateSelfSchedule() {
  const { token } = useParams()
  const [selectedSlot, setSelectedSlot] = useState<string>('')
  const [cancelModalOpen, setCancelModalOpen] = useState(false)
  const [cancelReason, setCancelReason] = useState('')

  const { data, isLoading, isError, refetch } = useApiQuery(
    ['candidate_self_schedule', token],
    () => interviewsApi.getPublicSchedulingLink(token || ''),
    { enabled: Boolean(token) },
  )

  const payload = (data as any)?.data || {}
  const interview = payload?.interview || {}
  const link = payload?.link || {}
  const slots = Array.isArray(payload?.slots) ? payload.slots : []
  const currentStatus = interview?.status || (link?.booking_count ? 'scheduled' : 'pending')
  const timezone = link?.timezone || slots?.[0]?.timezone || 'UTC'
  const interviewerNames = Array.isArray(interview?.panelists)
    ? interview.panelists.map((panelist: any) => panelist?.interviewer_name || panelist?.name).filter(Boolean)
    : []

  const confirm = useMutation({
    mutationFn: () => interviewsApi.bookPublicSchedulingLink(token || '', { slot_start: selectedSlot, timezone }),
    onSuccess: () => {
      message.success(link?.booking_count ? 'Interview rescheduled' : 'Interview slot confirmed')
      refetch()
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Unable to confirm slot')
    },
  })

  const cancelRequest = useMutation({
    mutationFn: () => interviewsApi.cancelInterviewFlex(interview.id, { reason: cancelReason || 'Candidate requested cancellation' }),
    onSuccess: () => {
      message.success('Cancellation request submitted')
      setCancelModalOpen(false)
      setCancelReason('')
      refetch()
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Unable to submit cancellation request')
    },
  })

  const groupedSlots = useMemo<GroupedSlot[]>(
    () => {
      const grouped = new Map<string, GroupedSlot>()
      slots.forEach((slot: any) => {
        const dateKey = dayjs(slot.starts_at).format('YYYY-MM-DD')
        if (!grouped.has(dateKey)) {
          grouped.set(dateKey, {
            dateKey,
            dateLabel: dayjs(slot.starts_at).format('dddd, DD MMM YYYY'),
            slots: [],
          })
        }
        grouped.get(dateKey)?.slots.push({
          label: `${dayjs(slot.starts_at).format('hh:mm A')} - ${dayjs(slot.ends_at).format('hh:mm A')}`,
          value: slot.starts_at,
          timezone: slot.timezone,
          raw: slot,
        })
      })
      return Array.from(grouped.values())
    },
    [slots],
  )

  const selectedSlotRecord = useMemo(
    () => groupedSlots.flatMap((group) => group.slots).find((slot) => slot.value === selectedSlot) || null,
    [groupedSlots, selectedSlot],
  )

  const schedulingMode = interviewerNames.length > 1 ? 'Panel availability slots' : link?.metadata?.mode === 'candidate_self' ? 'System generated slots' : 'Recruiter defined slots'

  if (isLoading) {
    return (
      <div className="p-8">
        <Spin />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-8">
        <Alert type="error" message="Scheduling link not available" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <Title level={3} className="!mb-2 !mt-0">Schedule / Reschedule Interview</Title>
                <Paragraph className="!mb-0 text-slate-500">
                  Choose the best available slot and confirm your interview schedule.
                </Paragraph>
              </div>
              <Tag color={statusColor(currentStatus)} className="w-fit">
                {currentStatus}
              </Tag>
            </div>
          </Card>

          <Card className="rounded-3xl border-slate-200">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interview Type</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{formatInterviewType(interview?.interview_type)}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Duration</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{interview?.duration_minutes || 60} minutes</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Timezone</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{timezone}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Scheduling Mode</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{schedulingMode}</div>
              </div>
            </div>
          </Card>

          <Card className="rounded-3xl border-slate-200">
            <div className="mb-4 flex items-center gap-3">
              <CalendarDays className="h-5 w-5 text-blue-600" />
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">Available Slots</div>
                <div className="text-sm text-slate-500">Select from recruiter defined, system generated, or panel availability slots.</div>
              </div>
            </div>

            {groupedSlots.length === 0 ? (
              <Empty description="No slots available right now" />
            ) : (
              <Radio.Group className="w-full" value={selectedSlot} onChange={(event) => setSelectedSlot(event.target.value)}>
                <div className="space-y-4">
                  {groupedSlots.map((group) => (
                    <div key={group.dateKey} className="rounded-2xl border border-slate-200 p-4">
                      <div className="mb-3 text-sm font-semibold text-slate-900">{group.dateLabel}</div>
                      <div className="grid gap-3 md:grid-cols-2">
                        {group.slots.map((slot) => (
                          <label
                            key={slot.value}
                            className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-4 transition ${
                              selectedSlot === slot.value ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                            }`}
                          >
                            <Radio value={slot.value} className="mt-0.5" />
                            <div className="min-w-0">
                              <div className="text-sm font-semibold text-slate-900">{slot.label}</div>
                              <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                                <Clock3 className="h-3.5 w-3.5" />
                                {slot.timezone}
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </Radio.Group>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="rounded-3xl border-slate-200">
            <div className="mb-4 flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <div>
                <div className="text-sm font-black uppercase tracking-wider text-slate-900">Confirmation</div>
                <div className="text-sm text-slate-500">Review your selected slot before confirming.</div>
              </div>
            </div>

            {selectedSlotRecord ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Selected Slot</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{dayjs(selectedSlotRecord.value).format('dddd, DD MMM YYYY')}</div>
                  <div className="mt-1 text-sm text-slate-600">{selectedSlotRecord.label}</div>
                  <div className="mt-1 text-xs text-slate-500">{selectedSlotRecord.timezone}</div>
                </div>

                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interviewer</div>
                  <div className="mt-2 text-sm text-slate-700">{interviewerNames.length ? interviewerNames.join(', ') : 'Assigned after booking if applicable'}</div>
                </div>

                <div className="rounded-2xl border border-slate-200 p-4">
                  <div className="text-[11px] font-black uppercase tracking-widest text-slate-400">Interview Type</div>
                  <div className="mt-2 text-sm text-slate-700">{formatInterviewType(interview?.interview_type)}</div>
                </div>

                <Button
                  type="primary"
                  block
                  loading={confirm.isPending}
                  onClick={() => confirm.mutate()}
                >
                  {link?.booking_count ? 'Confirm Reschedule' : 'Confirm Slot'}
                </Button>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500">
                Select a slot to review confirmation details.
              </div>
            )}
          </Card>

          <Card className="rounded-3xl border-slate-200">
            <div className="mb-4 text-sm font-black uppercase tracking-wider text-slate-900">Candidate Actions</div>
            <div className="space-y-3">
              <Button
                block
                icon={<RefreshCw className="h-4 w-4" />}
                disabled={!selectedSlot}
                loading={confirm.isPending}
                onClick={() => confirm.mutate()}
              >
                {link?.booking_count ? 'Reschedule Interview' : 'Schedule Interview'}
              </Button>
              <Button
                block
                danger
                icon={<XCircle className="h-4 w-4" />}
                disabled={!interview?.id}
                onClick={() => setCancelModalOpen(true)}
              >
                Cancel Request
              </Button>
            </div>
          </Card>

          <Card className="rounded-3xl border-slate-200">
            <div className="text-sm font-black uppercase tracking-wider text-slate-900">Notifications</div>
            <div className="mt-3 space-y-2 text-sm text-slate-500">
              <div>Schedule confirmation is triggered after booking.</div>
              <div>Reschedule notification is triggered after slot change.</div>
              <div>Interview reminders follow the scheduling workflow.</div>
            </div>
          </Card>
        </div>
      </div>

      <Modal
        open={cancelModalOpen}
        onCancel={() => setCancelModalOpen(false)}
        onOk={() => cancelRequest.mutate()}
        okText="Submit Cancel Request"
        confirmLoading={cancelRequest.isPending}
        title="Cancel Interview Request"
      >
        <div className="space-y-4">
          <Alert
            type="warning"
            showIcon
            message="Candidate cancellation request"
            description="This uses the interview cancellation workflow when candidate access is available."
          />
          <div>
            <Text className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Reason</Text>
            <TextArea
              rows={4}
              value={cancelReason}
              onChange={(event) => setCancelReason(event.target.value)}
              placeholder="Reason for cancellation or reschedule withdrawal"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
