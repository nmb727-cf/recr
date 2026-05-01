import { Card, Empty, Spin, Tag, Timeline, Typography } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useMemo } from 'react'

import { useWorkflowInstanceSla } from '@/hooks/useWorkflowSla'
import { useWorkflowInstanceHumanTasks } from '@/hooks/useWorkflowHumanTasks'
import { useWorkflowInstanceTimeline, useWorkflowInstanceWaitStates, useWorkflowInstances } from '@/hooks/useWorkflowInstanceTracker'

dayjs.extend(relativeTime)

const { Text } = Typography

type WorkflowStatusPanelProps = {
  entityId?: string
  entityType?: string
  title?: string
  maxTimelineItems?: number
}

function normalizeTimelineRow(row: Record<string, unknown>) {
  const time =
    row.occurred_at ||
    row.timestamp ||
    row.created_at ||
    row.updated_at ||
    null

  const label =
    String(row.event_label || row.action || row.entry_label || row.event_type || row.entry_type || 'Workflow event')

  return {
    label,
    time: time ? String(time) : '',
  }
}

function pickPrimaryInstance(instances: Array<Record<string, unknown>>) {
  const statusPriority: Record<string, number> = {
    running: 5,
    waiting: 4,
    pending: 3,
    paused: 2,
    failed: 1,
    completed: 0,
    cancelled: 0,
  }

  return [...instances].sort((a, b) => {
    const ap = statusPriority[String(a.status || '').toLowerCase()] ?? -1
    const bp = statusPriority[String(b.status || '').toLowerCase()] ?? -1
    if (ap !== bp) return bp - ap
    return dayjs(String(b.started_at || b.created_at || 0)).valueOf() - dayjs(String(a.started_at || a.created_at || 0)).valueOf()
  })[0]
}

export default function WorkflowStatusPanel({
  entityId,
  entityType,
  title = 'Workflow Status',
  maxTimelineItems = 8,
}: WorkflowStatusPanelProps) {
  const { data: instancesData, isLoading: instancesLoading } = useWorkflowInstances({
    entity_id: entityId,
    entity_type: entityType,
  })

  const instances = useMemo(
    () => (Array.isArray(instancesData) ? (instancesData as Array<Record<string, unknown>>) : []),
    [instancesData]
  )
  const instance = useMemo(() => pickPrimaryInstance(instances), [instances])
  const instanceId = instance?.id ? String(instance.id) : undefined

  const { data: timelineData, isLoading: timelineLoading } = useWorkflowInstanceTimeline(instanceId)
  const { data: waitStatesData } = useWorkflowInstanceWaitStates(instanceId)
  const { data: humanTasksData } = useWorkflowInstanceHumanTasks(instanceId)
  const { data: slaData } = useWorkflowInstanceSla(instanceId)

  const timeline = ((timelineData as Array<Record<string, unknown>>) || [])
    .map(normalizeTimelineRow)
    .slice(-maxTimelineItems)
    .reverse()

  const waitStates = (Array.isArray(waitStatesData) ? (waitStatesData as Array<Record<string, unknown>>) : [])
  const openWait = waitStates.find((w) => String(w.status || '').toLowerCase() === 'waiting')
  const tasks = (Array.isArray(humanTasksData) ? (humanTasksData as Array<Record<string, unknown>>) : [])
  const openTasks = tasks.filter((t) => ['pending', 'in_progress'].includes(String(t.status || '').toLowerCase()))
  const pendingApprovals = openTasks.filter((t) => String(t.task_type || '').toLowerCase() === 'approval').length
  const slaTrackers = (Array.isArray(slaData) ? (slaData as Array<Record<string, unknown>>) : [])
  const slaRiskCount = slaTrackers.filter((s) => ['warning', 'breached', 'escalated'].includes(String(s.status || '').toLowerCase())).length
  const ownerTask = openTasks[0]
  const ownerLabel = ownerTask
    ? `${String(ownerTask.assigned_to_type || 'user')}${ownerTask.assigned_to_id ? `:${String(ownerTask.assigned_to_id).slice(0, 8)}` : ''}`
    : 'Unassigned'
  const latestTimelineAt = timeline[0]?.time || String(instance?.updated_at || instance?.started_at || '')
  const inactiveHours = latestTimelineAt ? dayjs().diff(dayjs(latestTimelineAt), 'hour') : 0
  const stuckRisk = ['running', 'waiting'].includes(String(instance?.status || '').toLowerCase()) && inactiveHours >= 24

  if (instancesLoading) {
    return (
      <Card title={title} bordered={false} className="shadow-soft-sm">
        <div className="py-8 text-center">
          <Spin />
        </div>
      </Card>
    )
  }

  if (!instanceId) {
    return (
      <Card title={title} bordered={false} className="shadow-soft-sm">
        <Empty description="No workflow instance found for this record" />
      </Card>
    )
  }

  return (
    <Card title={title} bordered={false} className="shadow-soft-sm">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-3 mb-5">
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">Current Stage</Text>
          <Text className="text-xs font-semibold text-slate-800">
            {instance.current_stage_id ? String(instance.current_stage_id) : 'N/A'}
          </Text>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">Status</Text>
          <Tag className="mt-1 mb-0 uppercase font-semibold">{String(instance.status || 'unknown')}</Tag>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">Waiting Reason</Text>
          <Text className="text-xs font-semibold text-slate-800">
            {instance.wait_reason
              ? String(instance.wait_reason)
              : openWait?.wait_reason
                ? String(openWait.wait_reason)
                : openWait?.wait_type
                  ? String(openWait.wait_type)
                  : 'None'}
          </Text>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">Owner</Text>
          <Text className="text-xs font-semibold text-slate-800">{ownerLabel}</Text>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">Pending Tasks</Text>
          <Text className="text-xs font-semibold text-slate-800">{openTasks.length}</Text>
          <Text className="block text-[10px] text-slate-500">Approvals: {pendingApprovals}</Text>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <Text className="block text-[10px] uppercase font-bold text-slate-500">SLA / Stuck Risk</Text>
          <Text className="text-xs font-semibold text-slate-800">
            {slaRiskCount > 0 ? `${slaRiskCount} alerts` : stuckRisk ? `Stuck (${inactiveHours}h)` : 'Healthy'}
          </Text>
        </div>
      </div>

      <div>
        <Text className="block text-[11px] uppercase font-bold text-slate-500 mb-3">Workflow Timeline</Text>
        {timelineLoading ? (
          <Spin size="small" />
        ) : timeline.length ? (
          <Timeline
            items={timeline.map((entry) => ({
              children: (
                <div>
                  <Text className="block text-sm font-medium text-slate-800">{entry.label}</Text>
                  <Text className="text-xs text-slate-500">{entry.time ? dayjs(entry.time).format('MMM D, YYYY HH:mm') : ''}</Text>
                </div>
              ),
            }))}
          />
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No timeline events yet" />
        )}
      </div>
    </Card>
  )
}
