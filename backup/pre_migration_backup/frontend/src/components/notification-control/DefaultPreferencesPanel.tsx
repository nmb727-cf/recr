import { Form, Switch, Select, Button, Spin, message as antMessage } from 'antd'
import { useEffect, useState } from 'react'
import type { NotificationPreferenceDefaults } from '@/api/notificationControl'

interface Props {
  prefs?: NotificationPreferenceDefaults
  isLoading: boolean
  onSave: (data: Partial<NotificationPreferenceDefaults>) => Promise<void>
}

const DIGEST_OPTIONS = [
  { value: 'immediate', label: 'Send immediately' },
  { value: 'hourly',    label: 'Hourly digest' },
  { value: 'daily',     label: 'Daily digest' },
]

export function DefaultPreferencesPanel({ prefs, isLoading, onSave }: Props) {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (prefs) {
      form.setFieldsValue({
        default_in_app_enabled:   prefs.default_in_app_enabled,
        default_email_enabled:    prefs.default_email_enabled,
        default_reminder_enabled: prefs.default_reminder_enabled,
        allow_user_override:      prefs.allow_user_override,
        digest_frequency:         prefs.digest_frequency,
      })
    }
  }, [prefs, form])

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      await onSave(values)
      antMessage.success('Default preferences saved')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200">
      <div className="px-5 py-4 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-900">Default user preferences</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          These defaults apply to new users. Existing user preferences are not changed.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Spin size="small" />
        </div>
      ) : (
        <Form form={form} layout="vertical" size="small" className="px-5 py-4">
          <div className="grid grid-cols-1 gap-y-1">
            <Form.Item name="default_in_app_enabled" label="In-app notifications on by default" valuePropName="checked" className="mb-2">
              <Switch />
            </Form.Item>
            <Form.Item name="default_email_enabled" label="Email notifications on by default" valuePropName="checked" className="mb-2">
              <Switch />
            </Form.Item>
            <Form.Item name="default_reminder_enabled" label="Reminders on by default" valuePropName="checked" className="mb-2">
              <Switch />
            </Form.Item>
            <Form.Item
              name="allow_user_override"
              label="Allow users to change their own preferences"
              valuePropName="checked"
              className="mb-2"
            >
              <Switch />
            </Form.Item>
            <Form.Item name="digest_frequency" label="Default delivery frequency">
              <Select options={DIGEST_OPTIONS} className="w-full" />
            </Form.Item>
          </div>

          <Button
            type="primary"
            onClick={handleSave}
            loading={saving}
            size="small"
            className="mt-2"
          >
            Save defaults
          </Button>
        </Form>
      )}
    </div>
  )
}
