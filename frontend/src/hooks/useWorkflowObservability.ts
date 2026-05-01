import { workflowObservabilityApi } from '@/api/workflowObservability'
import { useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowObservabilityTimeline(instanceId?: string) {
  return useApiQuery(
    ['workflow-observability', 'timeline', instanceId],
    () => workflowObservabilityApi.getInstanceTimeline(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowObservabilityTrace(instanceId?: string) {
  return useApiQuery(
    ['workflow-observability', 'trace', instanceId],
    () => workflowObservabilityApi.getInstanceTrace(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowObservabilitySnapshot(instanceId?: string) {
  return useApiQuery(
    ['workflow-observability', 'snapshot', instanceId],
    () => workflowObservabilityApi.getInstanceSnapshot(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowObservabilityMetrics(instanceId?: string) {
  return useApiQuery(
    ['workflow-observability', 'metrics', instanceId],
    () => workflowObservabilityApi.getInstanceMetrics(instanceId as string),
    { enabled: !!instanceId }
  )
}

export function useWorkflowObservabilityHealth(instanceId?: string) {
  return useApiQuery(
    ['workflow-observability', 'health', instanceId],
    () => workflowObservabilityApi.getInstanceHealth(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 5000 }
  )
}

export function useWorkflowObservabilitySummary(workflowId?: string) {
  return useApiQuery(
    ['workflow-observability', 'workflow-summary', workflowId],
    () => workflowObservabilityApi.getWorkflowSummary(workflowId as string),
    { enabled: !!workflowId }
  )
}

export function useWorkflowObservabilityFailures(workflowId?: string) {
  return useApiQuery(
    ['workflow-observability', 'workflow-failures', workflowId],
    () => workflowObservabilityApi.getWorkflowFailures(workflowId as string),
    { enabled: !!workflowId }
  )
}

export function useWorkflowObservabilitySlaRisks(workflowId?: string) {
  return useApiQuery(
    ['workflow-observability', 'workflow-sla-risks', workflowId],
    () => workflowObservabilityApi.getWorkflowSlaRisks(workflowId as string),
    { enabled: !!workflowId }
  )
}
