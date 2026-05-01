import { workflowTemplateLibraryApi } from '@/api/workflowTemplateLibrary'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowTemplates(params?: {
  category?: string
  template_type?: 'system' | 'company' | 'agency' | 'custom'
  visibility?: 'private' | 'organization' | 'public'
  is_active?: boolean
}) {
  return useApiQuery(
    ['workflow-template-library', 'templates', params],
    () => workflowTemplateLibraryApi.listTemplates(params),
    { refetchInterval: 10000 }
  )
}

export function useWorkflowTemplate(templateId?: string) {
  return useApiQuery(
    ['workflow-template-library', 'template', templateId],
    () => workflowTemplateLibraryApi.getTemplate(templateId as string),
    { enabled: !!templateId }
  )
}

export function useWorkflowTemplateVersions(templateId?: string) {
  return useApiQuery(
    ['workflow-template-library', 'template-versions', templateId],
    () => workflowTemplateLibraryApi.getTemplateVersions(templateId as string),
    { enabled: !!templateId }
  )
}

export function useCreateWorkflowTemplate() {
  return useApiMutation(
    (payload: {
      name: string
      description?: string
      category?: string
      template_type?: 'system' | 'company' | 'agency' | 'custom'
      visibility?: 'private' | 'organization' | 'public'
      tenant_id?: string
      created_by?: string
      config_snapshot?: Record<string, unknown>
      metadata?: Record<string, unknown>
    }) => workflowTemplateLibraryApi.createTemplate(payload),
    {
      successMessage: 'Workflow template created',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}

export function useCloneWorkflowTemplate(templateId: string) {
  return useApiMutation(
    (payload?: { tenant_id?: string; created_by?: string; name?: string }) =>
      workflowTemplateLibraryApi.cloneTemplate(templateId, payload),
    {
      successMessage: 'Workflow template cloned',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}

export function useApplyWorkflowTemplate(templateId: string) {
  return useApiMutation(
    (payload: {
      tenant_id: string
      workflow_name?: string
      workflow_description?: string
      trigger_event?: string
      used_by?: string
    }) => workflowTemplateLibraryApi.applyTemplate(templateId, payload),
    {
      successMessage: 'Workflow created from template',
      invalidateKeys: [['workflow-template-library'], ['workflow-versioning']],
    }
  )
}

export function usePublishWorkflowTemplate(templateId: string) {
  return useApiMutation(
    (payload?: { visibility?: 'private' | 'organization' | 'public' }) =>
      workflowTemplateLibraryApi.publishTemplate(templateId, payload),
    {
      successMessage: 'Workflow template published',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}

export function useArchiveWorkflowTemplate(templateId: string) {
  return useApiMutation(
    () => workflowTemplateLibraryApi.archiveTemplate(templateId),
    {
      successMessage: 'Workflow template archived',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}

export function useImportWorkflowTemplate() {
  return useApiMutation(
    (payload: { tenant_id?: string; created_by?: string; payload: Record<string, unknown> }) =>
      workflowTemplateLibraryApi.importTemplate(payload),
    {
      successMessage: 'Workflow template imported',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}

export function useExportWorkflowTemplate(templateId?: string) {
  return useApiQuery(
    ['workflow-template-library', 'export', templateId],
    () => workflowTemplateLibraryApi.exportTemplate(templateId as string),
    { enabled: !!templateId }
  )
}

export function useRateWorkflowTemplate(templateId: string) {
  return useApiMutation(
    (payload: { rating: number; review?: string; tenant_id?: string; created_by?: string }) =>
      workflowTemplateLibraryApi.rateTemplate(templateId, payload),
    {
      successMessage: 'Template rating submitted',
      invalidateKeys: [['workflow-template-library']],
    }
  )
}
