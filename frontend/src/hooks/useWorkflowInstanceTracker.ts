import { workflowInstanceTrackerApi } from '@/api/workflowInstanceTracker'
import type { WorkflowInstanceTrackerStatus } from '@/api/workflowInstanceTracker'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { useMemo } from 'react'

export function useWorkflowInstances(params?: {
  tenant_id?: string
  workflow_id?: string
  status?: WorkflowInstanceTrackerStatus
  entity_type?: string
  entity_id?: string
}) {
  return useApiQuery(['workflow-instance-tracker', 'instances', params], () => workflowInstanceTrackerApi.listInstances(params), {
    refetchInterval: 10000,
  })
}

export function useWorkflowInstance(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'instance', instanceId],
    () => workflowInstanceTrackerApi.getInstance(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowInstanceTimeline(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'timeline', instanceId],
    () => workflowInstanceTrackerApi.getTimeline(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowInstanceStages(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'stages', instanceId],
    () => workflowInstanceTrackerApi.getStages(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowInstanceWaitStates(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'wait-states', instanceId],
    () => workflowInstanceTrackerApi.getWaitStates(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowInstanceFailures(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'failures', instanceId],
    () => workflowInstanceTrackerApi.getFailures(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowInstanceActorOwnership(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'actor-ownership', instanceId],
    () => workflowInstanceTrackerApi.getActorOwnership(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowInstanceConditionLogs(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'condition-logs', instanceId],
    () => workflowInstanceTrackerApi.getConditionLogs(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowInstanceActionLogs(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'action-logs', instanceId],
    () => workflowInstanceTrackerApi.getActionLogs(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowInstanceHumanTasks(instanceId?: string) {
  return useApiQuery(
    ['workflow-instance-tracker', 'human-tasks', instanceId],
    () => workflowInstanceTrackerApi.getHumanTasks(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowInstanceProgress(instanceId?: string) {
  const instanceQuery = useWorkflowInstance(instanceId)
  const stagesQuery = useWorkflowInstanceStages(instanceId)

  const progress = useMemo(() => {
    const stages = (stagesQuery.data as Array<{ status?: string }>) || []
    if (!stages.length) return 0
    const completed = stages.filter((stage) =>
      ['completed', 'skipped'].includes(String(stage.status || '').toLowerCase())
    ).length
    return Math.round((completed / stages.length) * 100)
  }, [stagesQuery.data])

  const currentStage = useMemo(() => {
    const instance = instanceQuery.data as { current_stage_id?: string } | undefined
    const stages = (stagesQuery.data as Array<{ stage_id?: string; stage_name?: string; status?: string }>) || []
    const byCurrent = stages.find((s) => s.stage_id === instance?.current_stage_id)
    if (byCurrent) return byCurrent
    return stages.find((s) => String(s.status || '').toLowerCase() === 'running') || null
  }, [instanceQuery.data, stagesQuery.data])

  return {
    progress,
    currentStage,
    isLoading: instanceQuery.isLoading || stagesQuery.isLoading,
    isError: instanceQuery.isError || stagesQuery.isError,
  }
}

export function useRetryWorkflowInstance() {
  return useApiMutation(
    ({ id, context }: { id: string; context?: Record<string, unknown> }) =>
      workflowInstanceTrackerApi.retryInstance(id, { context }),
    {
      successMessage: 'Workflow retry initiated',
      invalidateKeys: [['workflow-instance-tracker']],
    }
  )
}

export function useResumeWorkflowWaitState() {
  return useApiMutation(
    ({ waitStateId, context }: { waitStateId: string; context?: Record<string, unknown> }) =>
      workflowInstanceTrackerApi.resumeWaitState(waitStateId, { context }),
    {
      successMessage: 'Wait state resumed',
      invalidateKeys: [['workflow-instance-tracker']],
    }
  )
}
