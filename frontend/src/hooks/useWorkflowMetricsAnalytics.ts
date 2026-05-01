import { workflowMetricsAnalyticsApi } from '@/api/workflowMetricsAnalytics'
import { useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowAnalyticsWorkflows() {
  return useApiQuery(
    ['workflow-analytics', 'workflows'],
    () => workflowMetricsAnalyticsApi.listWorkflows(),
    { refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsSummary(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'summary', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowSummary(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 10000 }
  )
}

export function useWorkflowAnalyticsTimeline(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'timeline', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowTimeline(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 10000 }
  )
}

export function useWorkflowAnalyticsBottlenecks(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'bottlenecks', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowBottlenecks(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsFailures(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'failures', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowFailures(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsStages(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'stages', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowStages(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsActions(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'actions', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowActions(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsImpact(workflowId?: string) {
  return useApiQuery(
    ['workflow-analytics', 'impact', workflowId],
    () => workflowMetricsAnalyticsApi.getWorkflowImpact(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 30000 }
  )
}

export function useWorkflowAnalyticsTrends(workflowId?: string, days = 30) {
  return useApiQuery(
    ['workflow-analytics', 'trends', workflowId, days],
    () => workflowMetricsAnalyticsApi.getWorkflowTrends(workflowId as string, { days }),
    { enabled: !!workflowId, refetchInterval: 60000 }
  )
}
