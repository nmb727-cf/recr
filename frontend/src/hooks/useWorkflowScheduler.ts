import dayjs from 'dayjs'

import { workflowSchedulerApi } from '@/api/workflowScheduler'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowSchedulerTasks(params?: {
  tenant_id?: string
  workflow_instance_id?: string
  status?: string
  task_type?: string
}) {
  return useApiQuery(
    ['workflow-scheduler', 'tasks', params],
    () => workflowSchedulerApi.listTasks(params),
    { refetchInterval: 15000 }
  )
}

export function useWorkflowInstanceScheduledTasks(instanceId?: string) {
  const query = useApiQuery(
    ['workflow-scheduler', 'instance-tasks', instanceId],
    () => workflowSchedulerApi.getInstanceScheduledTasks(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 10000 }
  )

  const now = dayjs()
  const data = ((query.data as Array<Record<string, unknown>>) || []).map((task) => {
    const scheduledAt = dayjs(String(task.scheduled_at || ''))
    return {
      ...task,
      next_execution_in_seconds: scheduledAt.isValid() ? scheduledAt.diff(now, 'second') : null,
      is_delayed: String(task.status || '').toLowerCase() === 'scheduled' && scheduledAt.isValid() && now.isAfter(scheduledAt),
    }
  })

  return {
    ...query,
    data,
  }
}

export function useRetryWorkflowScheduledTask() {
  return useApiMutation(
    ({ id }: { id: string }) => workflowSchedulerApi.retryTask(id),
    {
      successMessage: 'Scheduled task retried',
      invalidateKeys: [['workflow-scheduler'], ['workflow-instance-tracker']],
    }
  )
}

export function useCancelWorkflowScheduledTask() {
  return useApiMutation(
    ({ id }: { id: string }) => workflowSchedulerApi.cancelTask(id),
    {
      successMessage: 'Scheduled task cancelled',
      invalidateKeys: [['workflow-scheduler'], ['workflow-instance-tracker']],
    }
  )
}
