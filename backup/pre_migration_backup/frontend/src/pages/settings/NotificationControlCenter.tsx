import { useState, useCallback } from 'react'
import { message as antMessage } from 'antd'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery, useApiMutation } from '@/hooks/useApiQuery'
import { notificationControlApi } from '@/api/notificationControl'
import { SummaryCards } from '@/components/notification-control/SummaryCards'
import { GlobalChannelSettings } from '@/components/notification-control/GlobalChannelSettings'
import { RulesTable } from '@/components/notification-control/RulesTable'
import { RuleEditDrawer } from '@/components/notification-control/RuleEditDrawer'
import { DefaultPreferencesPanel } from '@/components/notification-control/DefaultPreferencesPanel'
import type { NotificationRule, RuleCategory, RuleUpdatePayload, ChannelSetting, NotificationControlSummary, NotificationPreferenceDefaults } from '@/api/notificationControl'

export default function NotificationControlCenter() {
  const queryClient = useQueryClient()
  const [editRule, setEditRule] = useState<NotificationRule | null>(null)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<RuleCategory | 'all'>('all')
  const [isSavingRule, setIsSavingRule] = useState(false)

  // ── Data fetching ─────────────────────────────────────────────────────────
  const { data: summaryData, isLoading: summaryLoading } = useApiQuery(
    ['nc-summary'],
    () => notificationControlApi.getSummary(),
    { staleTime: 30_000 },
  )
  const summary = (summaryData as { summary: NotificationControlSummary } | undefined)?.summary

  const { data: rulesData, isLoading: rulesLoading } = useApiQuery(
    ['nc-rules'],
    () => notificationControlApi.listRules(),
    { staleTime: 30_000 },
  )
  const rules: NotificationRule[] = (rulesData as { rules: NotificationRule[] } | undefined)?.rules ?? []

  const { data: channelData, isLoading: channelLoading } = useApiQuery(
    ['nc-channel-settings'],
    () => notificationControlApi.getChannelSettings(),
    { staleTime: 60_000 },
  )
  const channelSettings: ChannelSetting[] =
    (channelData as { channel_settings: ChannelSetting[] } | undefined)?.channel_settings ?? []

  const { data: prefsData, isLoading: prefsLoading } = useApiQuery(
    ['nc-preferences'],
    () => notificationControlApi.getPreferenceDefaults(),
    { staleTime: 60_000 },
  )
  const prefs: NotificationPreferenceDefaults | undefined =
    (prefsData as { preferences: NotificationPreferenceDefaults } | undefined)?.preferences

  // ── Actions ───────────────────────────────────────────────────────────────
  const handleChannelToggle = useCallback(async (channelType: string, enabled: boolean) => {
    try {
      await notificationControlApi.updateChannelSettings([{ channel_type: channelType, is_enabled: enabled }])
      queryClient.invalidateQueries({ queryKey: ['nc-channel-settings'] })
      queryClient.invalidateQueries({ queryKey: ['nc-summary'] })
      antMessage.success(`${channelType} channel ${enabled ? 'enabled' : 'disabled'}`)
    } catch {
      antMessage.error('Failed to update channel setting')
    }
  }, [queryClient])

  const handleToggleActive = useCallback(async (rule: NotificationRule, active: boolean) => {
    try {
      await notificationControlApi.updateRule(rule.event_key, { is_active: active })
      queryClient.invalidateQueries({ queryKey: ['nc-rules'] })
      queryClient.invalidateQueries({ queryKey: ['nc-summary'] })
    } catch {
      antMessage.error('Failed to update rule')
    }
  }, [queryClient])

  const handleSaveRule = useCallback(async (eventKey: string, data: RuleUpdatePayload) => {
    setIsSavingRule(true)
    try {
      await notificationControlApi.updateRule(eventKey, data)
      queryClient.invalidateQueries({ queryKey: ['nc-rules'] })
      queryClient.invalidateQueries({ queryKey: ['nc-summary'] })
      antMessage.success('Rule saved')
      setEditRule(null)
    } catch {
      antMessage.error('Failed to save rule')
    } finally {
      setIsSavingRule(false)
    }
  }, [queryClient])

  const handleSavePreferences = useCallback(async (data: Partial<NotificationPreferenceDefaults>) => {
    await notificationControlApi.updatePreferenceDefaults(data)
    queryClient.invalidateQueries({ queryKey: ['nc-preferences'] })
  }, [queryClient])

  return (
    <div className="max-w-[1400px] mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Notification Control Center</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Control how your platform communicates across all events and channels.
        </p>
      </div>

      {/* Summary cards */}
      <SummaryCards summary={summary} isLoading={summaryLoading} />

      {/* Main content: 3-column layout on wide screens */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">

        {/* Left: rules table (full width on its own) */}
        <div className="space-y-6">
          <RulesTable
            rules={rules}
            isLoading={rulesLoading}
            search={search}
            categoryFilter={categoryFilter}
            onSearchChange={setSearch}
            onCategoryChange={setCategoryFilter}
            onEdit={setEditRule}
            onToggleActive={handleToggleActive}
          />
        </div>

        {/* Right sidebar */}
        <div className="space-y-6">
          <GlobalChannelSettings
            settings={channelSettings}
            isLoading={channelLoading}
            onToggle={handleChannelToggle}
          />
          <DefaultPreferencesPanel
            prefs={prefs}
            isLoading={prefsLoading}
            onSave={handleSavePreferences}
          />
        </div>
      </div>

      {/* Rule edit drawer */}
      <RuleEditDrawer
        rule={editRule}
        open={!!editRule}
        onClose={() => setEditRule(null)}
        onSave={handleSaveRule}
        isSaving={isSavingRule}
      />
    </div>
  )
}
