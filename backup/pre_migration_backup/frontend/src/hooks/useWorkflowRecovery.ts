import { workflowRecoveryApi } from '@/api/workflowRecovery'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowRecoveryCases(params?: { status?: string; workflow_instance_id?: string }) {
  return useApiQuery(
    ['workflow-recovery', 'cases', params],
    () => workflowRecoveryApi.listRecoveryCases(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowRecoveryCase(caseId?: string) {
  return useApiQuery(
    ['workflow-recovery', 'case', caseId],
    () => workflowRecoveryApi.getRecoveryCase(caseId as string),
    { enabled: !!caseId }
  )
}

export function useWorkflowInstanceRecovery(instanceId?: string) {
  return useApiQuery(
    ['workflow-recovery', 'instance-recovery', instanceId],
    () => workflowRecoveryApi.getInstanceRecovery(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowRecoveryPolicies(params?: { workflow_id?: string; active?: boolean }) {
  return useApiQuery(
    ['workflow-recovery', 'policies', params],
    () => workflowRecoveryApi.listRecoveryPolicies(params),
    { refetchInterval: 30000 }
  )
}

export function useCreateWorkflowRecoveryPolicy() {
  return useApiMutation(
    (payload: Record<string, unknown>) => workflowRecoveryApi.createRecoveryPolicy(payload),
    {
      successMessage: 'Recovery policy created',
      invalidateKeys: [['workflow-recovery']],
    }
  )
}

export function useRetryWorkflowRecoveryCase(caseId: string) {
  return useApiMutation(
    () => workflowRecoveryApi.retryRecoveryCase(caseId),
    {
      successMessage: 'Recovery retry started',
      invalidateKeys: [['workflow-recovery'], ['workflow-observability']],
    }
  )
}

export function useEscalateWorkflowRecoveryCase(caseId: string) {
  return useApiMutation(
    (payload?: { reason?: string }) => workflowRecoveryApi.escalateRecoveryCase(caseId, payload),
    {
      successMessage: 'Recovery case escalated',
      invalidateKeys: [['workflow-recovery'], ['workflow-observability']],
    }
  )
}

export function useManualResumeWorkflowRecoveryCase(caseId: string) {
  return useApiMutation(
    (payload?: { action_taken_by?: string }) => workflowRecoveryApi.manualResumeRecoveryCase(caseId, payload),
    {
      successMessage: 'Workflow resumed manually',
      invalidateKeys: [['workflow-recovery'], ['workflow-instance-tracker'], ['workflow-observability']],
    }
  )
}

export function useManualSkipWorkflowRecoveryCase(caseId: string) {
  return useApiMutation(
    (payload?: { action_taken_by?: string }) => workflowRecoveryApi.manualSkipRecoveryCase(caseId, payload),
    {
      successMessage: 'Workflow stage skipped manually',
      invalidateKeys: [['workflow-recovery'], ['workflow-instance-tracker'], ['workflow-observability']],
    }
  )
}

export function useManualFailWorkflowRecoveryCase(caseId: string) {
  return useApiMutation(
    (payload?: { action_taken_by?: string }) => workflowRecoveryApi.manualFailRecoveryCase(caseId, payload),
    {
      successMessage: 'Workflow failed manually',
      invalidateKeys: [['workflow-recovery'], ['workflow-instance-tracker'], ['workflow-observability']],
    }
  )
}
