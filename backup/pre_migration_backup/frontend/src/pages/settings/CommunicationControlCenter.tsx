import { useState, useCallback } from 'react'
import { Tabs, message as antMessage } from 'antd'
import { useQueryClient } from '@tanstack/react-query'
import { Radio, Bell, BarChart2, Activity, Layers } from 'lucide-react'

import { useApiQuery } from '@/hooks/useApiQuery'
import { notificationControlApi } from '@/api/notificationControl'
import { channelControlApi } from '@/api/channelControl'

import { ChannelOverviewCards } from '@/components/channel-control/ChannelOverviewCards'
import { ChannelSettingsPanel } from '@/components/channel-control/ChannelSettingsPanel'
import { ProviderConfigDrawer } from '@/components/channel-control/ProviderConfigDrawer'
import { ChannelRoutingTable } from '@/components/channel-control/ChannelRoutingTable'
import { DeliveryLogTable } from '@/components/channel-control/DeliveryLogTable'
import { ChannelHealthPanel } from '@/components/channel-control/ChannelHealthPanel'

// Re-use the notification control components for Trigger Mapping tab
import { RulesTable } from '@/components/notification-control/RulesTable'
import { RuleEditDrawer } from '@/components/notification-control/RuleEditDrawer'

import type { ChannelSetting, NotificationRule, RuleCategory, RuleUpdatePayload } from '@/api/notificationControl'
import type { TenantChannelConfig, ChannelConfigCreatePayload, ChannelConfigPatchPayload } from '@/api/channelControl'

// ── Tab definitions ───────────────────────────────────────────────────────────

const TABS = [
  { key: 'channels',  label: 'Channel Settings',   icon: <Radio className="h-4 w-4" /> },
  { key: 'routing',   label: 'Routing Rules',       icon: <Layers className="h-4 w-4" /> },
  { key: 'triggers',  label: 'Trigger Mapping',     icon: <Bell className="h-4 w-4" /> },
  { key: 'logs',      label: 'Delivery Logs',       icon: <BarChart2 className="h-4 w-4" /> },
  { key: 'health',    label: 'Health',              icon: <Activity className="h-4 w-4" /> },
]

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CommunicationControlCenter() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('channels')

  // ── Provider config drawer state ─────────────────────────────────────────
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editConfig, setEditConfig] = useState<TenantChannelConfig | null>(null)
  const [newChannelType, setNewChannelType] = useState<'whatsapp' | 'sms' | 'push' | undefined>()
  const [isSavingConfig, setIsSavingConfig] = useState(false)

  // ── Rule edit drawer state ────────────────────────────────────────────────
  const [editRule, setEditRule] = useState<NotificationRule | null>(null)
  const [isSavingRule, setIsSavingRule] = useState(false)
  const [ruleSearch, setRuleSearch] = useState('')
  const [ruleCategoryFilter, setRuleCategoryFilter] = useState<RuleCategory | 'all'>('all')

  // ── Data fetching ─────────────────────────────────────────────────────────

  const { data: channelSettingsData, isLoading: loadingChannelSettings } = useApiQuery(
    ['nc-channel-settings'],
    () => notificationControlApi.getChannelSettings(),
    { staleTime: 30_000 },
  )
  const channelSettings: ChannelSetting[] =
    (channelSettingsData as any)?.channel_settings ?? []

  const { data: channelConfigsData, isLoading: loadingConfigs } = useApiQuery(
    ['channel-configs'],
    () => channelControlApi.listChannelConfigs(),
    { staleTime: 30_000 },
  )
  const channelConfigs: TenantChannelConfig[] =
    (channelConfigsData as any)?.results ?? []

  const { data: statsData } = useApiQuery(
    ['channel-stats'],
    () => channelControlApi.getChannelStats(),
    { staleTime: 60_000 },
  )

  const { data: summaryData } = useApiQuery(
    ['nc-summary'],
    () => notificationControlApi.getSummary(),
    { staleTime: 30_000 },
  )
  const summary = (summaryData as any)?.summary

  const { data: rulesData, isLoading: loadingRules } = useApiQuery(
    ['nc-rules'],
    () => notificationControlApi.listRules(),
    { staleTime: 30_000 },
  )
  const rules: NotificationRule[] = (rulesData as any)?.rules ?? []

  // ── Actions: channel on/off toggle ───────────────────────────────────────

  const handleChannelToggle = useCallback(async (channelType: string, enabled: boolean) => {
    try {
      await notificationControlApi.updateChannelSettings([{ channel_type: channelType, is_enabled: enabled }])
      queryClient.invalidateQueries({ queryKey: ['nc-channel-settings'] })
      queryClient.invalidateQueries({ queryKey: ['nc-summary'] })
      antMessage.success(`${channelType} ${enabled ? 'enabled' : 'disabled'}`)
    } catch {
      antMessage.error('Failed to update channel setting')
    }
  }, [queryClient])

  // ── Actions: provider config CRUD ────────────────────────────────────────

  const openEditConfig = useCallback((cfg: TenantChannelConfig) => {
    setEditConfig(cfg)
    setNewChannelType(undefined)
    setDrawerOpen(true)
  }, [])

  const openNewConfig = useCallback((channelType: 'whatsapp' | 'sms' | 'push') => {
    setEditConfig(null)
    setNewChannelType(channelType)
    setDrawerOpen(true)
  }, [])

  const handleSaveConfig = useCallback(async (
    payload: ChannelConfigCreatePayload | ChannelConfigPatchPayload,
    id?: string,
  ) => {
    setIsSavingConfig(true)
    try {
      if (id) {
        await channelControlApi.patchChannelConfig(id, payload as ChannelConfigPatchPayload)
        antMessage.success('Provider configuration saved')
      } else {
        await channelControlApi.createChannelConfig(payload as ChannelConfigCreatePayload)
        antMessage.success('Provider added')
      }
      queryClient.invalidateQueries({ queryKey: ['channel-configs'] })
      queryClient.invalidateQueries({ queryKey: ['channel-health'] })
      setDrawerOpen(false)
    } catch {
      antMessage.error('Failed to save provider configuration')
    } finally {
      setIsSavingConfig(false)
    }
  }, [queryClient])

  // ── Actions: notification rules ──────────────────────────────────────────

  const handleToggleRuleActive = useCallback(async (rule: NotificationRule, active: boolean) => {
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

  // ── Tab items ─────────────────────────────────────────────────────────────

  const isOverviewLoading = loadingChannelSettings || loadingConfigs

  const tabItems = [
    {
      key: 'channels',
      label: (
        <span className="flex items-center gap-1.5 text-sm">
          <Radio className="h-4 w-4" />
          Channel Settings
        </span>
      ),
      children: (
        <ChannelSettingsPanel
          channelSettings={channelSettings}
          channelConfigs={channelConfigs}
          isLoadingSettings={loadingChannelSettings}
          isLoadingConfigs={loadingConfigs}
          onToggle={handleChannelToggle}
          onEditConfig={openEditConfig}
          onNewConfig={openNewConfig}
        />
      ),
    },
    {
      key: 'routing',
      label: (
        <span className="flex items-center gap-1.5 text-sm">
          <Layers className="h-4 w-4" />
          Routing Rules
        </span>
      ),
      children: <ChannelRoutingTable />,
    },
    {
      key: 'triggers',
      label: (
        <span className="flex items-center gap-1.5 text-sm">
          <Bell className="h-4 w-4" />
          Trigger Mapping
        </span>
      ),
      children: (
        <RulesTable
          rules={rules}
          isLoading={loadingRules}
          search={ruleSearch}
          categoryFilter={ruleCategoryFilter}
          onSearchChange={setRuleSearch}
          onCategoryChange={setRuleCategoryFilter}
          onEdit={setEditRule}
          onToggleActive={handleToggleRuleActive}
        />
      ),
    },
    {
      key: 'logs',
      label: (
        <span className="flex items-center gap-1.5 text-sm">
          <BarChart2 className="h-4 w-4" />
          Delivery Logs
        </span>
      ),
      children: <DeliveryLogTable />,
    },
    {
      key: 'health',
      label: (
        <span className="flex items-center gap-1.5 text-sm">
          <Activity className="h-4 w-4" />
          Health
        </span>
      ),
      children: <ChannelHealthPanel />,
    },
  ]

  return (
    <div className="max-w-[1400px] mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Communication Control Center</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Manage all outbound channels, provider credentials, routing rules, and delivery observability in one place.
        </p>
      </div>

      {/* Overview cards */}
      <ChannelOverviewCards
        channelSettings={channelSettings}
        channelStats={(statsData as any) ?? undefined}
        channelConfigs={channelConfigs}
        summary={summary}
        isLoading={isOverviewLoading}
      />

      {/* Tabbed content */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        className="communication-control-tabs"
        tabBarStyle={{ paddingLeft: 0, marginBottom: 0 }}
        destroyInactiveTabPane={false}
      />

      {/* Provider config drawer */}
      <ProviderConfigDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        editConfig={editConfig}
        newChannelType={newChannelType}
        onSave={handleSaveConfig}
        isSaving={isSavingConfig}
      />

      {/* Rule edit drawer (Trigger Mapping) */}
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
