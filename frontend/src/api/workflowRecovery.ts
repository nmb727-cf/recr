import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowRecoveryApi = {
  listRecoveryCases: (params?: { status?: string; workflow_instance_id?: string }) =>
    http.get<ApiResponse<any[]>>('/workflow-recovery/cases/', { params }),

  getRecoveryCase: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-recovery/cases/${id}/`),

  getInstanceRecovery: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/recovery/`),

  listRecoveryPolicies: (params?: { workflow_id?: string; active?: boolean }) =>
    http.get<ApiResponse<any[]>>('/workflow-recovery/policies/', { params }),

  createRecoveryPolicy: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<any>>('/workflow-recovery/policies/', payload),

  retryRecoveryCase: (id: string) =>
    http.post<ApiResponse<any>>(`/workflow-recovery/cases/${id}/retry/`, {}),

  escalateRecoveryCase: (id: string, payload?: { reason?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-recovery/cases/${id}/escalate/`, payload || {}),

  manualResumeRecoveryCase: (id: string, payload?: { action_taken_by?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-recovery/cases/${id}/manual-resume/`, payload || {}),

  manualSkipRecoveryCase: (id: string, payload?: { action_taken_by?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-recovery/cases/${id}/manual-skip/`, payload || {}),

  manualFailRecoveryCase: (id: string, payload?: { action_taken_by?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-recovery/cases/${id}/manual-fail/`, payload || {}),
}
