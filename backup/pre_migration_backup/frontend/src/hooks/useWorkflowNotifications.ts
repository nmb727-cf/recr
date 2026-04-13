import { useMemo } from 'react'

import { workflowNotificationsApi } from '@/api/workflowNotifications'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowNotifications(params?: {
  tenant_id?: string
  workflow_instance_id?: string
  status?: string
  channel?: string
}) {
  return useApiQuery(
    ['workflow-notifications', 'list', params],
    () => workflowNotificationsApi.listNotifications(params),
    { refetchInterval: 15000 }
  )
}

export function useWorkflowInstanceNotifications(instanceId?: string) {
  const query = useApiQuery(
    ['workflow-notifications', 'instance', instanceId],
    () => workflowNotificationsApi.getInstanceNotifications(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 10000 }
  )

  const enriched = useMemo(() => {
    const rows = (query.data as Array<Record<string, unknown>>) || []
    return rows.map((row) => ({
      ...row,
      channel_badge: String(row.channel || '').toUpperCase(),
      is_failed: String(row.status || '').toLowerCase() === 'failed',
      is_sent: String(row.status || '').toLowerCase() === 'sent',
    }))
  }, [query.data])

  return {
    ...query,
    data: enriched,
  }
}

export function useWorkflowNotificationTestSend() {
  return useApiMutation(
    (payload: {
      workflow_instance_id: string
      stage_execution_id?: string
      trigger_type: string
      payload?: Record<string, unknown>
    }) => workflowNotificationsApi.testSend(payload),
    {
      successMessage: 'Workflow notification test send completed',
      invalidateKeys: [['workflow-notifications'], ['workflow-instance-tracker']],
    }
  )
}

export function useRetryWorkflowNotification() {
  return useApiMutation(
    ({ id }: { id: string }) => workflowNotificationsApi.retryNotification(id),
    {
      successMessage: 'Workflow notification retried',
      invalidateKeys: [['workflow-notifications'], ['workflow-instance-tracker']],
    }
  )
}
