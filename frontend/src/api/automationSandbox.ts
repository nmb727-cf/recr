import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationSandboxApi = {
  // Sandbox Runs
  listRuns: () => http.get<ApiResponse<any[]>>('/workflow-sandbox/runs/'),
  getRun: (id: string) => http.get<ApiResponse<any>>(`/workflow-sandbox/runs/${id}/`),
  getRunSteps: (id: string) => http.get<ApiResponse<any[]>>(`/workflow-sandbox/runs/${id}/steps/`),
  getRunArtifacts: (id: string) => http.get<ApiResponse<any[]>>(`/workflow-sandbox/runs/${id}/artifacts/`),
  cancelRun: (id: string) => http.post<ApiResponse<any>>(`/workflow-sandbox/runs/${id}/cancel/`, {}),

  // Scenarios
  listScenarios: () => http.get<ApiResponse<any[]>>('/workflow-sandbox/scenarios/'),
  createScenario: (data: any) => http.post<ApiResponse<any>>('/workflow-sandbox/scenarios/', data),

  // Simulation
  simulate: (data: { workflow_id: string; input_context: any; run_name?: string }) => 
    http.post<ApiResponse<any>>('/workflow-sandbox/simulate/', data),

  // Approvals
  listApprovals: () => http.get<ApiResponse<any[]>>('/workflow-sandbox/approvals/'),
  approveRun: (id: string, notes?: string) => 
    http.post<ApiResponse<any>>(`/workflow-sandbox/approvals/${id}/approve/`, { notes }),
  rejectRun: (id: string, notes?: string) => 
    http.post<ApiResponse<any>>(`/workflow-sandbox/approvals/${id}/reject/`, { notes }),
}
