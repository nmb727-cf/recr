import { useEffect } from 'react'
import { Drawer, Form, Input, Select, Switch, InputNumber, Divider, Button, message as antMessage, Tag } from 'antd'
import { Lock, Globe } from 'lucide-react'
import type { NotificationRule, RuleUpdatePayload } from '@/api/notificationControl'

interface Props {
  rule: NotificationRule | null
  open: boolean
  onClose: () => void
  onSave: (eventKey: string, data: RuleUpdatePayload) => Promise<void>
  isSaving: boolean
}

const PRIORITY_OPTIONS = [
  { value: 'info',     label: 'Info' },
  { value: 'medium',   label: 'Medium' },
  { value: 'high',     label: 'High' },
  { value: 'critical', label: 'Critical' },
]

const CATEGORY_OPTIONS = [
  { value: 'candidate',   label: 'Candidate' },
  { value: 'application', label: 'Application' },
  { value: 'interview',   label: 'Interview' },
  { value: 'offer',       label: 'Offer' },
  { value: 'approval',    label: 'Approval' },
  { value: 'agency',      label: 'Agency' },
  { value: 'deadline',    label: 'Deadline / SLA' },
  { value: 'messaging',   label: 'Messaging' },
  { value: 'passport',    label: 'Passport' },
  { value: 'system',      label: 'System' },
]

const ESCALATION_TARGET_OPTIONS = [
  { value: 'assigned_manager', label: "Assigned user's manager" },
  { value: 'hiring_manager',   label: 'Hiring manager' },
  { value: 'recruiter_lead',   label: 'Recruiter lead' },
  { value: 'tenant_admin',     label: 'Tenant admin' },
]

export function RuleEditDrawer({ rule, open, onClose, onSave, isSaving }: Props) {
  const [form] = Form.useForm()

  useEffect(() => {
    if (rule && open) {
      form.setFieldsValue({
        business_label:          rule.business_label,
        category:                rule.category,
        priority:                rule.priority,
        is_active:               rule.is_active,
        in_app_enabled:          rule.in_app_enabled,
        email_enabled:           rule.email_enabled,
        whatsapp_enabled:        rule.whatsapp_enabled,
        sms_enabled:             rule.sms_enabled,
        fallback_enabled:        rule.fallback_enabled,
        fallback_delay_minutes:  rule.fallback_delay_minutes,
        escalation_enabled:      rule.escalation_enabled,
        escalation_delay_minutes: rule.escalation_delay_minutes,
        escalation_target_type:  rule.escalation_target_type,
        allow_user_override:     rule.allow_user_override,
        admin_notes:             rule.admin_notes,
      })
    }
  }, [rule, open, form])

  const handleSave = async () => {
    if (!rule) return
    const values = await form.validateFields()
    await onSave(rule.event_key, values)
  }

  return (
    <Drawer
      title={
        <div className="flex items-center gap-2">
          {rule?.is_locked ? (
            <Lock className="h-4 w-4 text-slate-400" />
          ) : rule?.is_tenant_override ? (
            <Globe className="h-4 w-4 text-indigo-500" />
          ) : null}
          <span className="text-sm font-semibold">
            {rule?.business_label || 'Edit rule'}
          </span>
          {rule?.is_system && !rule?.is_tenant_override && (
            <Tag color="blue" className="text-[10px]">System default</Tag>
          )}
          {rule?.is_tenant_override && (
            <Tag color="purple" className="text-[10px]">Custom override</Tag>
          )}
        </div>
      }
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="primary"
            onClick={handleSave}
            loading={isSaving}
            disabled={rule?.is_locked}
          >
            Save changes
          </Button>
        </div>
      }
    >
      {rule && (
        <Form form={form} layout="vertical" size="small">
          {/* Event key — read-only reference */}
          <div className="bg-slate-50 rounded-lg px-3 py-2 mb-4">
            <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium mb-0.5">Event key</p>
            <p className="text-xs font-mono text-slate-700">{rule.event_key}</p>
            {rule.admin_notes && (
              <p className="text-xs text-slate-500 mt-1.5">{rule.admin_notes}</p>
            )}
          </div>

          <Form.Item name="business_label" label="Label shown to admin">
            <Input disabled={rule.is_locked} />
          </Form.Item>

          <div className="grid grid-cols-2 gap-3">
            <Form.Item name="category" label="Category">
              <Select options={CATEGORY_OPTIONS} disabled={rule.is_locked} />
            </Form.Item>
            <Form.Item name="priority" label="Priority / Severity">
              <Select options={PRIORITY_OPTIONS} disabled={rule.is_locked} />
            </Form.Item>
          </div>

          <Form.Item name="is_active" label="Rule active" valuePropName="checked">
            <Switch disabled={rule.is_locked} />
          </Form.Item>

          <Divider className="my-3 text-xs text-slate-400">Channels</Divider>

          <div className="grid grid-cols-2 gap-x-6 gap-y-1">
            <Form.Item name="in_app_enabled" label="In-app" valuePropName="checked" className="mb-2">
              <Switch size="small" disabled={rule.is_locked} />
            </Form.Item>
            <Form.Item name="email_enabled" label="Email" valuePropName="checked" className="mb-2">
              <Switch size="small" disabled={rule.is_locked} />
            </Form.Item>
            <Form.Item name="whatsapp_enabled" label="WhatsApp" valuePropName="checked" className="mb-2">
              <Switch size="small" disabled={rule.is_locked} />
            </Form.Item>
            <Form.Item name="sms_enabled" label="SMS" valuePropName="checked" className="mb-2">
              <Switch size="small" disabled={rule.is_locked} />
            </Form.Item>
          </div>

          <Divider className="my-3 text-xs text-slate-400">Fallback &amp; escalation</Divider>

          <Form.Item name="fallback_enabled" label="Enable fallback channel" valuePropName="checked">
            <Switch disabled={rule.is_locked} />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.fallback_enabled !== cur.fallback_enabled}>
            {({ getFieldValue }) => getFieldValue('fallback_enabled') ? (
              <Form.Item
                name="fallback_delay_minutes"
                label="Send fallback after (minutes)"
                rules={[{ type: 'number', min: 1, message: 'Must be at least 1 minute' }]}
              >
                <InputNumber min={1} max={10080} className="w-full" disabled={rule.is_locked} />
              </Form.Item>
            ) : null}
          </Form.Item>

          <Divider className="my-3 text-xs text-slate-400">Escalation</Divider>

          <Form.Item name="escalation_enabled" label="Enable escalation" valuePropName="checked">
            <Switch disabled={rule.is_locked} />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.escalation_enabled !== cur.escalation_enabled}>
            {({ getFieldValue }) => getFieldValue('escalation_enabled') ? (
              <>
                <Form.Item
                  name="escalation_delay_minutes"
                  label="Escalate after (minutes since fallback)"
                  rules={[{ type: 'number', min: 1, message: 'Must be at least 1 minute' }]}
                >
                  <InputNumber min={1} max={10080} className="w-full" disabled={rule.is_locked} />
                </Form.Item>
                <Form.Item name="escalation_target_type" label="Escalate to">
                  <Select options={ESCALATION_TARGET_OPTIONS} disabled={rule.is_locked} />
                </Form.Item>
              </>
            ) : null}
          </Form.Item>

          <Divider className="my-3 text-xs text-slate-400">Preferences</Divider>

          <Form.Item
            name="allow_user_override"
            label="Allow users to turn this notification off"
            valuePropName="checked"
          >
            <Switch disabled={rule.is_locked} />
          </Form.Item>
        </Form>
      )}
    </Drawer>
  )
}
