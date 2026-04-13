import { workflowExecutionOrchestratorApi } from '@/api/workflowExecutionOrchestrator'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowOrchestratorContext(instanceId?: string) {
  return useApiQuery(
    ['workflow-orchestrator', 'context', instanceId],
    () => workflowExecutionOrchestratorApi.getContext(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowOrchestratorDecisions(instanceId?: string) {
  return useApiQuery(
    ['workflow-orchestrator', 'decisions', instanceId],
    () => workflowExecutionOrchestratorApi.getDecisions(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowOrchestratorLogs(instanceId?: string) {
  return useApiQuery(
    ['workflow-orchestrator', 'logs', instanceId],
    () => workflowExecutionOrchestratorApi.getLogs(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useRunWorkflowOrchestrator(instanceId: string) {
  return useApiMutation(
    (payload: { context?: Record<string, unknown>; source_type?: 'workflow' | 'event' | 'stage' | 'actor' | 'routing' | 'system' }) =>
      workflowExecutionOrchestratorApi.run(instanceId, payload),
    {
      successMessage: 'Workflow orchestrator run completed',
      invalidateKeys: [['workflow-orchestrator'], ['workflow-instance-tracker']],
    }
  )
}

export function useResumeWorkflowOrchestrator(instanceId: string) {
  return useApiMutation(
    (payload: { resume_event?: string; context?: Record<string, unknown> }) =>
      workflowExecutionOrchestratorApi.resume(instanceId, payload),
    {
      successMessage: 'Workflow resumed by orchestrator',
      invalidateKeys: [['workflow-orchestrator'], ['workflow-instance-tracker']],
    }
  )
}

export function useRetryWorkflowOrchestrator(instanceId: string) {
  return useApiMutation(
    () => workflowExecutionOrchestratorApi.retry(instanceId),
    {
      successMessage: 'Workflow retry requested',
      invalidateKeys: [['workflow-orchestrator'], ['workflow-instance-tracker']],
    }
  )
}

export function useFailWorkflowOrchestrator(instanceId: string) {
  return useApiMutation(
    (payload?: { reason?: string }) => workflowExecutionOrchestratorApi.fail(instanceId, payload),
    {
      successMessage: 'Workflow failed by orchestrator',
      invalidateKeys: [['workflow-orchestrator'], ['workflow-instance-tracker']],
    }
  )
}
