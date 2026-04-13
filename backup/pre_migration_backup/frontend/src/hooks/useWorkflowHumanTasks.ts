import { workflowHumanTasksApi } from '@/api/workflowHumanTasks'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowHumanTasks(params?: { tenant_id?: string; workflow_instance_id?: string; status?: string; assigned_to_id?: string }) {
  return useApiQuery(
    ['workflow-human-tasks', 'list', params],
    () => workflowHumanTasksApi.listHumanTasks(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowHumanTask(id?: string) {
  return useApiQuery(
    ['workflow-human-tasks', 'detail', id],
    () => workflowHumanTasksApi.getHumanTask(id as string),
    { enabled: !!id }
  )
}

export function useWorkflowInstanceHumanTasks(instanceId?: string) {
  return useApiQuery(
    ['workflow-human-tasks', 'instance', instanceId],
    () => workflowHumanTasksApi.getInstanceHumanTasks(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useCompleteWorkflowHumanTask(taskId: string) {
  return useApiMutation(
    (payload?: { actor_type?: string; actor_id?: string; comments?: string; context?: Record<string, unknown> }) =>
      workflowHumanTasksApi.completeHumanTask(taskId, payload),
    {
      successMessage: 'Human task completed',
      invalidateKeys: [['workflow-human-tasks'], ['workflow-instance-tracker']],
    }
  )
}

export function useRejectWorkflowHumanTask(taskId: string) {
  return useApiMutation(
    (payload?: { actor_type?: string; actor_id?: string; comments?: string; context?: Record<string, unknown> }) =>
      workflowHumanTasksApi.rejectHumanTask(taskId, payload),
    {
      successMessage: 'Human task rejected',
      invalidateKeys: [['workflow-human-tasks'], ['workflow-instance-tracker']],
    }
  )
}

export function useEscalateWorkflowHumanTask(taskId: string) {
  return useApiMutation(
    (payload?: { reason?: string }) => workflowHumanTasksApi.escalateHumanTask(taskId, payload),
    {
      successMessage: 'Human task escalated',
      invalidateKeys: [['workflow-human-tasks'], ['workflow-instance-tracker']],
    }
  )
}
