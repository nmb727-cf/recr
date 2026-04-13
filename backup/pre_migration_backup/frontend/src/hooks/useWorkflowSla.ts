import { useMemo } from 'react'
import dayjs from 'dayjs'

import { workflowSlaApi } from '@/api/workflowSla'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

export function useWorkflowSlaList(params?: { tenant_id?: string; workflow_instance_id?: string; status?: string }) {
  return useApiQuery(['workflow-sla', 'list', params], () => workflowSlaApi.listSla(params), {
    refetchInterval: 30000,
  })
}

export function useWorkflowInstanceSla(instanceId?: string) {
  const query = useApiQuery(
    ['workflow-sla', 'instance', instanceId],
    () => workflowSlaApi.getInstanceSla(instanceId as string),
    { enabled: !!instanceId, refetchInterval: 10000 }
  )

  const decorated = useMemo(() => {
    const rows = (query.data as Array<Record<string, unknown>>) || []
    const now = dayjs()
    return rows.map((row) => {
      const warningAt = dayjs(String(row.warning_at || ''))
      const breachAt = dayjs(String(row.breach_at || ''))
      const remainingSeconds = breachAt.isValid() ? breachAt.diff(now, 'second') : null
      const status = String(row.status || '').toLowerCase()
      return {
        ...row,
        remaining_seconds: remainingSeconds,
        warning_state: status === 'warning' || (warningAt.isValid() && now.isAfter(warningAt)),
        breach_state: status === 'breached' || status === 'escalated' || (breachAt.isValid() && now.isAfter(breachAt)),
        escalation_state: status === 'escalated',
      }
    })
  }, [query.data])

  return {
    ...query,
    data: decorated,
  }
}

export function useWorkflowStageSla(stageId?: string) {
  return useApiQuery(
    ['workflow-sla', 'stage', stageId],
    () => workflowSlaApi.getStageSla(stageId as string),
    { enabled: !!stageId }
  )
}

export function useResolveWorkflowSla() {
  return useApiMutation(
    ({ trackerId }: { trackerId: string }) => workflowSlaApi.resolveSla(trackerId),
    {
      successMessage: 'SLA resolved',
      invalidateKeys: [['workflow-sla'], ['workflow-instance-tracker']],
    }
  )
}
