import { workflowVisualBuilderApi } from '@/api/workflowVisualBuilder'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowBuilderGraph(workflowId?: string) {
  return useApiQuery(
    ['workflow-visual-builder', 'graph', workflowId],
    () => workflowVisualBuilderApi.getWorkflowBuilderGraph(workflowId as string),
    { enabled: !!workflowId, refetchInterval: 5000 }
  )
}

export function useCreateWorkflowBuilderNode() {
  return useApiMutation(
    (payload: {
      workflow_id: string
      node_type: 'start' | 'stage' | 'decision' | 'action' | 'human_task' | 'approval' | 'delay' | 'end'
      node_name: string
      position_x?: number
      position_y?: number
      config?: Record<string, unknown>
      tenant_id?: string
      created_by?: string
    }) => workflowVisualBuilderApi.createBuilderNode(payload),
    {
      successMessage: 'Builder node created',
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useUpdateWorkflowBuilderNode(nodeId: string) {
  return useApiMutation(
    (payload: {
      node_name?: string
      position_x?: number
      position_y?: number
      config?: Record<string, unknown>
      is_active?: boolean
    }) => workflowVisualBuilderApi.updateBuilderNode(nodeId, payload),
    {
      successMessage: 'Builder node updated',
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useDeleteWorkflowBuilderNode(nodeId: string) {
  return useApiMutation(
    () => workflowVisualBuilderApi.deleteBuilderNode(nodeId),
    {
      successMessage: 'Builder node deleted',
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useCreateWorkflowBuilderConnection() {
  return useApiMutation(
    (payload: {
      workflow_id: string
      source_node_id: string
      target_node_id: string
      condition_label?: string
      connection_type?: 'default' | 'success' | 'failure' | 'conditional' | 'approval' | 'rejection'
      metadata?: Record<string, unknown>
      tenant_id?: string
      created_by?: string
    }) => workflowVisualBuilderApi.createBuilderConnection(payload),
    {
      successMessage: 'Builder connection created',
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useDeleteWorkflowBuilderConnection(connectionId: string) {
  return useApiMutation(
    () => workflowVisualBuilderApi.deleteBuilderConnection(connectionId),
    {
      successMessage: 'Builder connection deleted',
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useValidateWorkflowBuilder() {
  return useApiMutation(
    ({ workflowId }: { workflowId: string }) =>
      workflowVisualBuilderApi.validateBuilderGraph(workflowId),
    {
      invalidateKeys: [['workflow-visual-builder']],
    }
  )
}

export function useSaveWorkflowBuilder() {
  return useApiMutation(
    (payload: {
      workflow_id: string
      payload?: Record<string, unknown>
      tenant_id?: string
      created_by?: string
      auto_layout?: boolean
    }) => workflowVisualBuilderApi.saveBuilderGraph(payload),
    {
      successMessage: 'Workflow builder saved',
      invalidateKeys: [['workflow-visual-builder'], ['workflow-versioning']],
    }
  )
}
