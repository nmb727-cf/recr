import { workflowConditionsApi } from '@/api/workflowConditions'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowConditionRules(params?: { workflow_id?: string; stage_id?: string; active?: boolean }) {
  return useApiQuery(
    ['workflow-conditions', 'rules', params],
    () => workflowConditionsApi.listRules(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowConditionRule(id?: string) {
  return useApiQuery(
    ['workflow-conditions', 'rule', id],
    () => workflowConditionsApi.getRule(id as string),
    { enabled: !!id }
  )
}

export function useWorkflowConditionGroups(params?: { workflow_id?: string; stage_id?: string; active?: boolean }) {
  return useApiQuery(
    ['workflow-conditions', 'groups', params],
    () => workflowConditionsApi.listGroups(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowConditionGroup(id?: string) {
  return useApiQuery(
    ['workflow-conditions', 'group', id],
    () => workflowConditionsApi.getGroup(id as string),
    { enabled: !!id }
  )
}

export function useWorkflowInstanceConditionLogs(instanceId?: string) {
  return useApiQuery(
    ['workflow-conditions', 'instance-logs', instanceId],
    () => workflowConditionsApi.getInstanceConditionLogs(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useCreateWorkflowConditionRule() {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowConditionsApi.createRule(payload),
    {
      successMessage: 'Condition rule created',
      invalidateKeys: [['workflow-conditions'], ['workflow-instance-tracker']],
    }
  )
}

export function useUpdateWorkflowConditionRule(id: string) {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowConditionsApi.updateRule(id, payload),
    {
      successMessage: 'Condition rule updated',
      invalidateKeys: [['workflow-conditions'], ['workflow-instance-tracker']],
    }
  )
}

export function useCreateWorkflowConditionGroup() {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowConditionsApi.createGroup(payload),
    {
      successMessage: 'Condition group created',
      invalidateKeys: [['workflow-conditions'], ['workflow-instance-tracker']],
    }
  )
}

export function useUpdateWorkflowConditionGroup(id: string) {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowConditionsApi.updateGroup(id, payload),
    {
      successMessage: 'Condition group updated',
      invalidateKeys: [['workflow-conditions'], ['workflow-instance-tracker']],
    }
  )
}

export function useTestEvaluateWorkflowConditionGroup(groupId: string) {
  return useApiMutation(
    (payload: { workflow_instance_id: string; stage_execution_id?: string | null; context?: Record<string, unknown> }) =>
      workflowConditionsApi.testEvaluateGroup(groupId, payload),
    {
      successMessage: 'Condition group evaluated',
      invalidateKeys: [['workflow-conditions'], ['workflow-instance-tracker']],
    }
  )
}
