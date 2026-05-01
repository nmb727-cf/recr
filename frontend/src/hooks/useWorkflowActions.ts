import { workflowActionsApi } from '@/api/workflowActions'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowActions(params?: { workflow_id?: string; stage_id?: string; active?: boolean }) {
  return useApiQuery(
    ['workflow-actions', 'list', params],
    () => workflowActionsApi.listActions(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowAction(id?: string) {
  return useApiQuery(
    ['workflow-actions', 'detail', id],
    () => workflowActionsApi.getAction(id as string),
    { enabled: !!id }
  )
}

export function useWorkflowInstanceActionLogs(instanceId?: string) {
  return useApiQuery(
    ['workflow-actions', 'instance-logs', instanceId],
    () => workflowActionsApi.getInstanceActionLogs(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useCreateWorkflowAction() {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowActionsApi.createAction(payload),
    {
      successMessage: 'Workflow action created',
      invalidateKeys: [['workflow-actions'], ['workflow-instance-tracker']],
    }
  )
}

export function useUpdateWorkflowAction(id: string) {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowActionsApi.updateAction(id, payload),
    {
      successMessage: 'Workflow action updated',
      invalidateKeys: [['workflow-actions'], ['workflow-instance-tracker']],
    }
  )
}

export function useTestRunWorkflowAction(id: string) {
  return useApiMutation(
    (payload: { workflow_instance_id: string; stage_execution_id?: string | null; context?: Record<string, unknown> }) =>
      workflowActionsApi.testRunAction(id, payload),
    {
      successMessage: 'Workflow action test-run completed',
      invalidateKeys: [['workflow-actions'], ['workflow-instance-tracker']],
    }
  )
}
