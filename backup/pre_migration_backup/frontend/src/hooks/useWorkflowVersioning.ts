import { workflowVersioningApi } from '@/api/workflowVersioning'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowVersions(params?: { workflow_id?: string; status?: string }) {
  return useApiQuery(
    ['workflow-versioning', 'versions', params],
    () => workflowVersioningApi.listWorkflowVersions(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowVersion(versionId?: string) {
  return useApiQuery(
    ['workflow-versioning', 'version', versionId],
    () => workflowVersioningApi.getWorkflowVersion(versionId as string),
    { enabled: !!versionId }
  )
}

export function useWorkflowDraft(workflowId?: string) {
  return useApiQuery(
    ['workflow-versioning', 'draft', workflowId],
    () => workflowVersioningApi.getWorkflowDraft(workflowId as string),
    { enabled: !!workflowId, retry: false }
  )
}

export function useWorkflowVersionsByWorkflow(workflowId?: string) {
  return useApiQuery(
    ['workflow-versioning', 'workflow-versions', workflowId],
    () => workflowVersioningApi.getWorkflowVersionsByWorkflow(workflowId as string),
    { enabled: !!workflowId }
  )
}

export function useCompareWorkflowVersions(workflowId?: string, fromVersionId?: string, toVersionId?: string) {
  return useApiQuery(
    ['workflow-versioning', 'compare', workflowId, fromVersionId, toVersionId],
    () => workflowVersioningApi.compareWorkflowVersions(workflowId as string, fromVersionId as string, toVersionId as string),
    { enabled: !!workflowId && !!fromVersionId && !!toVersionId }
  )
}

export function useCreateWorkflowDraft(workflowId: string) {
  return useApiMutation(
    (payload?: { name?: string; description?: string; builder_mode?: 'guided' | 'advanced'; created_by?: string }) =>
      workflowVersioningApi.createWorkflowDraft(workflowId, payload),
    {
      successMessage: 'Workflow draft created',
      invalidateKeys: [['workflow-versioning']],
    }
  )
}

export function useSaveWorkflowDraft(workflowId: string) {
  return useApiMutation(
    (payload?: {
      draft_id?: string
      name?: string
      description?: string
      builder_mode?: 'guided' | 'advanced'
      config_snapshot?: Record<string, unknown>
      ready_for_publish?: boolean
      changed_by?: string
    }) => workflowVersioningApi.saveWorkflowDraft(workflowId, payload),
    {
      successMessage: 'Workflow draft saved',
      invalidateKeys: [['workflow-versioning']],
    }
  )
}

export function usePublishWorkflowDraft(workflowId: string) {
  return useApiMutation(
    (payload?: { draft_id?: string; notes?: string; changed_by?: string }) =>
      workflowVersioningApi.publishWorkflowDraft(workflowId, payload),
    {
      successMessage: 'Workflow draft published',
      invalidateKeys: [['workflow-versioning'], ['workflow-instance-tracker']],
    }
  )
}

export function useRollbackWorkflowVersion(workflowId: string, versionId: string) {
  return useApiMutation(
    (payload?: { changed_by?: string }) => workflowVersioningApi.rollbackWorkflowVersion(workflowId, versionId, payload),
    {
      successMessage: 'Workflow rolled back',
      invalidateKeys: [['workflow-versioning'], ['workflow-instance-tracker']],
    }
  )
}

export function useCloneWorkflowVersion(workflowId: string, versionId: string) {
  return useApiMutation(
    (payload?: { changed_by?: string }) => workflowVersioningApi.cloneWorkflowVersion(workflowId, versionId, payload),
    {
      successMessage: 'Workflow version cloned',
      invalidateKeys: [['workflow-versioning']],
    }
  )
}

export function useDiscardWorkflowDraft(workflowId: string) {
  return useApiMutation(
    (payload?: { draft_id?: string; changed_by?: string }) => workflowVersioningApi.discardWorkflowDraft(workflowId, payload),
    {
      successMessage: 'Workflow draft discarded',
      invalidateKeys: [['workflow-versioning']],
    }
  )
}
