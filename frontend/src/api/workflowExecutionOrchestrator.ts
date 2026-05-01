import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export type OrchestratorSourceType = 'workflow' | 'event' | 'stage' | 'actor' | 'routing' | 'system'

export const workflowExecutionOrchestratorApi = {
  getContext: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-orchestrator/instances/${instanceId}/context/`),

  getDecisions: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-orchestrator/instances/${instanceId}/decisions/`),

  getLogs: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-orchestrator/instances/${instanceId}/logs/`),

  run: (instanceId: string, payload?: { context?: Record<string, unknown>; source_type?: OrchestratorSourceType }) =>
    http.post<ApiResponse<any>>(`/workflow-orchestrator/instances/${instanceId}/run/`, payload || {}),

  resume: (instanceId: string, payload?: { resume_event?: string; context?: Record<string, unknown> }) =>
    http.post<ApiResponse<any>>(`/workflow-orchestrator/instances/${instanceId}/resume/`, payload || {}),

  retry: (instanceId: string) =>
    http.post<ApiResponse<any>>(`/workflow-orchestrator/instances/${instanceId}/retry/`, {}),

  fail: (instanceId: string, payload?: { reason?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-orchestrator/instances/${instanceId}/fail/`, payload || {}),
}
