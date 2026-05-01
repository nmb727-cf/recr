import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export type WorkflowConditionType =
  | 'workflow_context'
  | 'entity_field'
  | 'actor_field'
  | 'score_field'
  | 'status_field'
  | 'time_field'
  | 'custom'

export type WorkflowConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'greater_or_equal'
  | 'less_or_equal'
  | 'contains'
  | 'not_contains'
  | 'in_list'
  | 'not_in_list'
  | 'is_true'
  | 'is_false'
  | 'exists'
  | 'not_exists'

export type WorkflowLogicalJoin = 'AND' | 'OR'

export const workflowConditionsApi = {
  listRules: (params?: { workflow_id?: string; stage_id?: string; active?: boolean }) =>
    http.get<ApiResponse<any[]>>('/workflow-conditions/', { params }),

  getRule: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-conditions/${id}/`),

  createRule: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<any>>('/workflow-conditions/', payload),

  updateRule: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<any>>(`/workflow-conditions/${id}/`, payload),

  listGroups: (params?: { workflow_id?: string; stage_id?: string; active?: boolean }) =>
    http.get<ApiResponse<any[]>>('/workflow-condition-groups/', { params }),

  getGroup: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-condition-groups/${id}/`),

  createGroup: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<any>>('/workflow-condition-groups/', payload),

  updateGroup: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<any>>(`/workflow-condition-groups/${id}/`, payload),

  testEvaluateGroup: (
    id: string,
    payload: {
      workflow_instance_id: string
      stage_execution_id?: string | null
      context?: Record<string, unknown>
    }
  ) => http.post<ApiResponse<any>>(`/workflow-condition-groups/${id}/test-evaluate/`, payload),

  getInstanceConditionLogs: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/condition-logs/`),
}
