import { Table, Switch, Button, Tooltip, Input, Empty } from 'antd'
import { Edit2, Lock, Globe, Mail, Bell, MessageCircle, Smartphone } from 'lucide-react'
import { cn } from '@/utils/cn'
import { RulePriorityBadge } from './RulePriorityBadge'
import type { NotificationRule, RuleCategory } from '@/api/notificationControl'

interface Props {
  rules: NotificationRule[]
  isLoading: boolean
  search: string
  categoryFilter: RuleCategory | 'all'
  onSearchChange: (v: string) => void
  onCategoryChange: (c: RuleCategory | 'all') => void
  onEdit: (rule: NotificationRule) => void
  onToggleActive: (rule: NotificationRule, active: boolean) => void
}

const CATEGORY_LABELS: Record<RuleCategory | 'all', string> = {
  all:         'All',
  candidate:   'Candidate',
  application: 'Application',
  interview:   'Interview',
  offer:       'Offer',
  approval:    'Approval',
  agency:      'Agency',
  deadline:    'Deadline / SLA',
  messaging:   'Messaging',
  passport:    'Passport',
  system:      'System',
}

const CATEGORIES = Object.keys(CATEGORY_LABELS) as (RuleCategory | 'all')[]

function ChannelDots({ rule }: { rule: NotificationRule }) {
  return (
    <div className="flex items-center gap-1.5">
      <Tooltip title="In-app">
        <Bell className={cn('h-3.5 w-3.5', rule.in_app_enabled ? 'text-indigo-500' : 'text-slate-300')} />
      </Tooltip>
      <Tooltip title="Email">
        <Mail className={cn('h-3.5 w-3.5', rule.email_enabled ? 'text-indigo-500' : 'text-slate-300')} />
      </Tooltip>
      <Tooltip title="WhatsApp">
        <MessageCircle className={cn('h-3.5 w-3.5', rule.whatsapp_enabled ? 'text-green-500' : 'text-slate-300')} />
      </Tooltip>
      <Tooltip title="SMS">
        <Smartphone className={cn('h-3.5 w-3.5', rule.sms_enabled ? 'text-blue-500' : 'text-slate-300')} />
      </Tooltip>
    </div>
  )
}

export function RulesTable({
  rules, isLoading, search, categoryFilter,
  onSearchChange, onCategoryChange, onEdit, onToggleActive,
}: Props) {
  const filtered = rules.filter((r) => {
    const matchesCategory = categoryFilter === 'all' || r.category === categoryFilter
    const matchesSearch = !search.trim() ||
      r.business_label.toLowerCase().includes(search.toLowerCase()) ||
      r.event_key.toLowerCase().includes(search.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const columns = [
    {
      title: 'Trigger / Event',
      dataIndex: 'business_label',
      key: 'business_label',
      render: (_: string, rule: NotificationRule) => (
        <div>
          <div className="flex items-center gap-1.5">
            {rule.is_locked ? (
              <Lock className="h-3 w-3 text-slate-400 flex-shrink-0" />
            ) : rule.is_tenant_override ? (
              <Globe className="h-3 w-3 text-indigo-400 flex-shrink-0" />
            ) : null}
            <span className="text-sm font-medium text-slate-900">{rule.business_label}</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">{rule.event_key}</span>
        </div>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (cat: RuleCategory) => (
        <span className="text-xs text-slate-600 capitalize">{CATEGORY_LABELS[cat] || cat}</span>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (p: any) => <RulePriorityBadge priority={p} />,
    },
    {
      title: 'Channels',
      key: 'channels',
      render: (_: unknown, rule: NotificationRule) => <ChannelDots rule={rule} />,
    },
    {
      title: 'Fallback',
      key: 'fallback',
      render: (_: unknown, rule: NotificationRule) => rule.fallback_enabled ? (
        <span className="text-xs text-slate-700">{rule.fallback_delay_minutes} min</span>
      ) : (
        <span className="text-xs text-slate-400">—</span>
      ),
    },
    {
      title: 'Escalation',
      key: 'escalation',
      render: (_: unknown, rule: NotificationRule) => rule.escalation_enabled ? (
        <span className="text-xs text-amber-700 bg-amber-50 rounded-full px-2 py-0.5">
          {rule.escalation_delay_minutes} min
        </span>
      ) : (
        <span className="text-xs text-slate-400">—</span>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: unknown, rule: NotificationRule) => (
        <Switch
          checked={rule.is_active}
          size="small"
          disabled={rule.is_locked}
          onChange={(checked) => onToggleActive(rule, checked)}
        />
      ),
    },
    {
      title: '',
      key: 'action',
      render: (_: unknown, rule: NotificationRule) => (
        <Button
          type="text"
          size="small"
          icon={<Edit2 className="h-3.5 w-3.5 text-slate-400" />}
          onClick={() => onEdit(rule)}
          disabled={rule.is_locked}
          className="flex items-center justify-center"
        />
      ),
    },
  ]

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Table header + filters */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-100 flex-wrap">
        <h3 className="text-sm font-semibold text-slate-900 flex-shrink-0">Notification rules</h3>
        <Input
          placeholder="Search rules…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          allowClear
          size="small"
          className="w-52 rounded-lg"
        />
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar ml-auto">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => onCategoryChange(cat)}
              className={cn(
                'px-2.5 py-1 text-xs font-medium rounded-lg whitespace-nowrap transition-colors',
                categoryFilter === cat
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
              )}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      <Table
        dataSource={filtered}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
        size="small"
        locale={{ emptyText: <Empty description="No rules match your filters" /> }}
        rowClassName={(rule) =>
          !rule.is_active ? 'opacity-50' : ''
        }
        className="notification-rules-table"
      />
    </div>
  )
}
