import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const agencyWorkflowApi = {
  listWorkflows: () => http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow/'),
  getWorkflow: (id: string) => http.get<ApiResponse<any>>(`/agency-workflow/agency-workflow/${id}/`),
  createWorkflow: (payload: any) => http.post<ApiResponse<any>>('/agency-workflow/agency-workflow/', payload),
  updateWorkflow: (id: string, payload: any) => http.put<ApiResponse<any>>(`/agency-workflow/agency-workflow/${id}/`, payload),
  deleteWorkflow: (id: string) => http.delete<ApiResponse<null>>(`/agency-workflow/agency-workflow/${id}/`),
  saveCanvas: (id: string, payload: { nodes: any[], edges: any[] }) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow/${id}/save_canvas/`, payload),

  // Event Trigger System
  listEventRegistry: () => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-events/registry/'),
  
  listEventSubscriptions: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-events/subscriptions/', { params }),
  
  createEventSubscription: (payload: any) => 
    http.post<ApiResponse<any>>('/agency-workflow/agency-workflow-events/subscriptions/', payload),
  
  updateEventSubscription: (id: string, payload: any) => 
    http.put<ApiResponse<any>>(`/agency-workflow/agency-workflow-events/subscriptions/${id}/`, payload),
  
  deleteEventSubscription: (id: string) => 
    http.delete<ApiResponse<null>>(`/agency-workflow/agency-workflow-events/subscriptions/${id}/`),
  
  listEventLogs: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-events/logs/', { params }),
  
  getEventLogDebug: (id: string) => 
    http.get<ApiResponse<any[]>>(`/agency-workflow/agency-workflow-events/logs/${id}/debug/`),
  
  testEmitEvent: (payload: any) => 
    http.post<ApiResponse<any>>('/agency-workflow/agency-workflow-events/test/test-emit/', payload),

  // Orchestration Engine
  listOrchestrationProcesses: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/processes/', { params }),
  getOrchestrationTimeline: (id: string) => 
    http.get<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/processes/${id}/timeline/`),
  startOrchestrationProcess: (payload: any) => 
    http.post<ApiResponse<any>>('/agency-workflow/agency-workflow-orchestration/processes/start/', payload),
  advanceOrchestrationProcess: (id: string, payload: any) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/processes/${id}/advance/`, payload),
  cancelOrchestrationProcess: (id: string) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/processes/${id}/cancel/`, {}),

  listOrchestrationApprovals: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/approvals/', { params }),
  approveOrchestrationRequest: (id: string, payload: any) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/approvals/${id}/approve/`, payload),
  rejectOrchestrationRequest: (id: string, payload: any) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/approvals/${id}/reject/`, payload),

  listOrchestrationClientResponses: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/client-responses/', { params }),
  followupClientResponse: (id: string) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/client-responses/${id}/followup/`, {}),
  completeClientResponse: (id: string) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/client-responses/${id}/complete/`, {}),

  listOrchestrationOffers: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/offers/', { params }),
  counterOrchestrationOffer: (id: string, payload: any) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/offers/${id}/counter/`, payload),
  acceptOrchestrationOffer: (id: string) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/offers/${id}/accept/`, {}),
  rejectOrchestrationOffer: (id: string) => 
    http.post<ApiResponse<any>>(`/agency-workflow/agency-workflow-orchestration/offers/${id}/reject/`, {}),

  listOrchestrationPlacements: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/placements/', { params }),
  listOrchestrationGuarantees: (params?: { tenant_id?: string }) => 
    http.get<ApiResponse<any[]>>('/agency-workflow/agency-workflow-orchestration/guarantees/', { params }),
}
