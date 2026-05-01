import http from '@/utils/http'
import type { ApiResponse } from '@/types'

// ─── Types ────────────────────────────────────────────────────────────────────

export type TaskPriority   = 'low' | 'medium' | 'high' | 'urgent'
export type TaskStatus     = 'pending' | 'in_progress' | 'completed' | 'overdue' | 'cancelled' | 'escalated'
export type AssigneeType   = 'assigned_recruiter' | 'hiring_manager' | 'recruiter_manager' | 'workflow_owner' | 'specific_user' | 'dynamic_field'

export interface TaskRule {
  id: string
  tenant_id: string
  workflow_id: string
  node_id: string
  task_title_template: string
  task_description_template: string
  assignee_type: AssigneeType
  assignee_field: string
  priority: TaskPriority
  due_in_minutes: number
  escalate_after_minutes: number
  is_active: boolean
  created_at: string
}

export interface TaskEscalation {
  id: string
  tenant_id: string
  task_execution: string
  escalation_level: number
  escalated_to: string | null
  escalated_to_role: string
  reason: string
  escalated_at: string
}

export interface TaskExecution {
  id: string
  tenant_id: string
  workflow_id: string
  execution_id: string | null
  rule: string | null
  task_title: string
  task_description: string
  assignee_user_id: string | null
  priority: TaskPriority
  due_at: string | null
  status: TaskStatus
  escalated: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
  escalations: TaskEscalation[]
}

export interface TaskAnalytics {
  total: number
  completed: number
  overdue: number
  escalated: number
  completion_rate: number
  escalation_rate: number
  by_priority: Record<TaskPriority, number>
  by_status: Record<TaskStatus, number>
}

export interface TaskRulePayload {
  workflow_id: string
  node_id?: string
  task_title_template: string
  task_description_template?: string
  assignee_type: AssigneeType
  assignee_field?: string
  priority?: TaskPriority
  due_in_minutes?: number
  escalate_after_minutes?: number
  is_active?: boolean
}

export interface TaskExecutionFilterParams {
  status?: TaskStatus
  assignee_user_id?: string
  priority?: TaskPriority
  workflow_id?: string
  escalated?: boolean
  limit?: number
  offset?: number
}

// ─── API client ───────────────────────────────────────────────────────────────

export const automationTasksApi = {
  // Rules
  listRules: (params?: { workflow_id?: string }) =>
    http.get<ApiResponse<{ rules: TaskRule[] }>>('/workflow-tasks/rules/', { params }),

  createRule: (data: TaskRulePayload) =>
    http.post<ApiResponse<{ rule: TaskRule }>>('/workflow-tasks/rules/', data),

  getRule: (id: string) =>
    http.get<ApiResponse<{ rule: TaskRule }>>(`/workflow-tasks/rules/${id}/`),

  updateRule: (id: string, data: Partial<TaskRulePayload>) =>
    http.put<ApiResponse<{ rule: TaskRule }>>(`/workflow-tasks/rules/${id}/`, data),

  deleteRule: (id: string) =>
    http.delete<ApiResponse<Record<string, never>>>(`/workflow-tasks/rules/${id}/`),

  // Executions
  listExecutions: (params?: TaskExecutionFilterParams) =>
    http.get<ApiResponse<{ executions: TaskExecution[]; meta: Record<string, number> }>>('/workflow-tasks/executions/', { params }),

  completeTask: (id: string) =>
    http.post<ApiResponse<{ result: Record<string, unknown> }>>(`/workflow-tasks/executions/${id}/complete/`),

  // Escalations
  listEscalations: (params?: { limit?: number; offset?: number }) =>
    http.get<ApiResponse<{ escalations: TaskEscalation[] }>>('/workflow-tasks/escalations/', { params }),

  // Analytics
  getAnalytics: () =>
    http.get<ApiResponse<{ analytics: TaskAnalytics }>>('/workflow-tasks/analytics/'),

  // SLA tracking (admin)
  trackSLA: () =>
    http.post<ApiResponse<{ result: Record<string, unknown> }>>('/workflow-tasks/track-sla/'),

  // Test task
  testTask: (data: { workflow_id: string; rule_id: string; context?: Record<string, unknown> }) =>
    http.post<ApiResponse<{ task: TaskExecution }>>('/workflow-tasks/test/', data),
}
