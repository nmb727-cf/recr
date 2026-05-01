import { useEffect, useState } from 'react'
import {
  Drawer, Form, Input, Select, Switch, Button, Divider, Alert, Tag, Tooltip,
} from 'antd'
import { Eye, EyeOff, Lock, AlertCircle } from 'lucide-react'
import type { TenantChannelConfig, ChannelConfigCreatePayload, ChannelConfigPatchPayload } from '@/api/channelControl'

interface Props {
  open: boolean
  onClose: () => void
  /** If provided, editing an existing config; otherwise creating new */
  editConfig: TenantChannelConfig | null
  /** Pre-selected channel when creating new */
  newChannelType?: 'whatsapp' | 'sms' | 'push'
  onSave: (payload: ChannelConfigCreatePayload | ChannelConfigPatchPayload, id?: string) => Promise<void>
  isSaving: boolean
}

const WA_PROVIDERS = [
  { value: 'whatsapp_business_api', label: 'WhatsApp Business API (Meta)' },
  { value: 'twilio_whatsapp',       label: 'Twilio WhatsApp' },
  { value: 'mock',                  label: 'Mock / Dev testing' },
]

const SMS_PROVIDERS = [
  { value: 'twilio',       label: 'Twilio SMS' },
  { value: 'generic_http', label: 'Generic HTTP Gateway' },
  { value: 'mock',         label: 'Mock / Dev testing' },
]

const PUSH_PROVIDERS = [
  { value: 'web_push', label: 'Web Push (VAPID)' },
  { value: 'fcm',      label: 'Firebase Cloud Messaging (FCM)' },
  { value: 'apns',     label: 'Apple Push Notifications (APNs)' },
  { value: 'mock',     label: 'Mock / Dev testing' },
]

const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  push: 'Push Notifications',
}

function SecretInput({ placeholder, helpText }: { placeholder?: string; helpText?: string }) {
  const [show, setShow] = useState(false)
  return (
    <div>
      <Input.Password
        placeholder={placeholder ?? 'Enter new value to update (leave blank to keep existing)'}
        visibilityToggle={{ visible: show, onVisibleChange: setShow }}
        iconRender={(v) => v
          ? <Eye className="h-4 w-4 cursor-pointer text-slate-400" />
          : <EyeOff className="h-4 w-4 cursor-pointer text-slate-400" />
        }
      />
      {helpText && <p className="text-[11px] text-slate-400 mt-1">{helpText}</p>}
    </div>
  )
}

function MaskedDisplay({ masked }: { masked: string }) {
  if (!masked || masked === '****') return <span className="text-slate-400 italic text-xs">Not set</span>
  return (
    <div className="flex items-center gap-1.5">
      <Lock className="h-3 w-3 text-slate-400" />
      <span className="font-mono text-xs text-slate-600">{masked}</span>
      <span className="text-[10px] text-slate-400">(saved)</span>
    </div>
  )
}

export function ProviderConfigDrawer({ open, onClose, editConfig, newChannelType, onSave, isSaving }: Props) {
  const [form] = Form.useForm()
  const [channelType, setChannelType] = useState<string>(
    editConfig?.channel_type ?? newChannelType ?? 'whatsapp',
  )
  const [provider, setProvider] = useState<string>(editConfig?.provider ?? '')

  useEffect(() => {
    if (open) {
      if (editConfig) {
        setChannelType(editConfig.channel_type)
        setProvider(editConfig.provider)
        form.setFieldsValue({
          provider:                        editConfig.provider,
          sender_name:                     editConfig.sender_name,
          sender_identifier:               editConfig.sender_identifier,
          api_key_id:                      editConfig.api_key_id,
          whatsapp_phone_number_id:        editConfig.whatsapp_phone_number_id,
          whatsapp_business_account_id:    editConfig.whatsapp_business_account_id,
          whatsapp_api_version:            editConfig.whatsapp_api_version || 'v19.0',
          sms_http_endpoint:               editConfig.sms_http_endpoint,
          push_vapid_public_key:           editConfig.push_vapid_public_key,
          push_fcm_project_id:             editConfig.push_fcm_project_id,
          is_active:                       editConfig.is_active,
        })
      } else {
        setChannelType(newChannelType ?? 'whatsapp')
        setProvider('')
        form.resetFields()
        form.setFieldsValue({
          whatsapp_api_version: 'v19.0',
          is_active: true,
        })
      }
    }
  }, [open, editConfig, newChannelType, form])

  const providerOptions =
    channelType === 'whatsapp' ? WA_PROVIDERS
    : channelType === 'sms'   ? SMS_PROVIDERS
    : PUSH_PROVIDERS

  const handleSave = async () => {
    const values = await form.validateFields()
    // Strip empty secret fields so they don't overwrite existing secrets
    const secretFields = ['api_token', 'webhook_secret', 'push_vapid_private_key']
    for (const f of secretFields) {
      if (!values[f]) delete values[f]
    }
    if (editConfig) {
      await onSave(values as ChannelConfigPatchPayload, editConfig.id)
    } else {
      await onSave({ ...values, channel_type: channelType } as ChannelConfigCreatePayload)
    }
  }

  const title = editConfig
    ? `Edit ${CHANNEL_LABELS[editConfig.channel_type]} provider`
    : `Set up ${CHANNEL_LABELS[channelType ?? 'whatsapp']} provider`

  return (
    <Drawer
      title={
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">{title}</span>
          {editConfig?.is_active && <Tag color="success" className="text-[10px]">Active</Tag>}
        </div>
      }
      placement="right"
      width={500}
      open={open}
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" onClick={handleSave} loading={isSaving}>
            {editConfig ? 'Save changes' : 'Create provider'}
          </Button>
        </div>
      }
    >
      <Form form={form} layout="vertical" size="small">
        {/* Credential masking notice (edit mode) */}
        {editConfig && (
          <Alert
            className="mb-4"
            type="info"
            showIcon
            icon={<Lock className="h-4 w-4" />}
            message="Credentials are encrypted at rest. Leave secret fields blank to keep the existing value."
          />
        )}

        {/* Channel type — read-only in edit, hidden in create (set by parent) */}
        {!editConfig && (
          <Form.Item label="Channel type">
            <Select
              value={channelType}
              onChange={(v) => { setChannelType(v); setProvider('') }}
              options={[
                { value: 'whatsapp', label: 'WhatsApp' },
                { value: 'sms',      label: 'SMS' },
                { value: 'push',     label: 'Push Notifications' },
              ]}
              disabled={!!newChannelType}
            />
          </Form.Item>
        )}

        <Form.Item
          name="provider"
          label="Provider"
          rules={[{ required: true, message: 'Select a provider' }]}
        >
          <Select
            placeholder="Select provider"
            options={providerOptions}
            onChange={(v) => setProvider(v)}
          />
        </Form.Item>

        <Form.Item name="is_active" label="Active" valuePropName="checked">
          <Switch />
        </Form.Item>

        {/* ── WhatsApp Business API ────────────────────────────────────────── */}
        {channelType === 'whatsapp' && provider === 'whatsapp_business_api' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">WhatsApp Business API (Meta)</Divider>
            <Form.Item
              name="whatsapp_phone_number_id"
              label="Phone number ID"
              tooltip="Found in Meta Business Manager → WhatsApp → Phone numbers"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="123456789012345" />
            </Form.Item>
            <Form.Item
              name="whatsapp_business_account_id"
              label="Business account ID (WABA)"
              tooltip="WhatsApp Business Account ID from Meta Business Manager"
            >
              <Input placeholder="987654321" />
            </Form.Item>
            <Form.Item name="api_token" label="API access token (Bearer)">
              {editConfig ? (
                <div>
                  <MaskedDisplay masked={editConfig.api_token_masked} />
                  <div className="mt-2">
                    <Form.Item name="api_token" noStyle>
                      <SecretInput helpText="Enter a new token to replace the saved one" />
                    </Form.Item>
                  </div>
                </div>
              ) : (
                <SecretInput placeholder="Enter Meta API access token" />
              )}
            </Form.Item>
            <Form.Item name="whatsapp_api_version" label="API version">
              <Input placeholder="v19.0" />
            </Form.Item>
            <Form.Item
              name="sender_identifier"
              label="Sender phone number (E.164)"
              tooltip="E.g. +14155238886 — the number registered with Meta"
            >
              <Input placeholder="+14155238886" />
            </Form.Item>
          </>
        )}

        {/* ── Twilio WhatsApp ──────────────────────────────────────────────── */}
        {channelType === 'whatsapp' && provider === 'twilio_whatsapp' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Twilio WhatsApp</Divider>
            <Form.Item
              name="api_key_id"
              label="Twilio Account SID"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="AC..." />
            </Form.Item>
            <Form.Item name="api_token" label="Twilio Auth Token">
              {editConfig ? (
                <div>
                  <MaskedDisplay masked={editConfig.api_token_masked} />
                  <div className="mt-2">
                    <Form.Item name="api_token" noStyle>
                      <SecretInput helpText="Enter a new auth token to replace" />
                    </Form.Item>
                  </div>
                </div>
              ) : (
                <SecretInput placeholder="Enter Twilio Auth Token" />
              )}
            </Form.Item>
            <Form.Item
              name="sender_identifier"
              label="WhatsApp sender number (E.164)"
              tooltip="E.g. +14155238886 — your Twilio WhatsApp-enabled number"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="+14155238886" />
            </Form.Item>
            <Form.Item name="sender_name" label="Display name">
              <Input placeholder="Talentos" />
            </Form.Item>
          </>
        )}

        {/* ── Twilio SMS ───────────────────────────────────────────────────── */}
        {channelType === 'sms' && provider === 'twilio' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Twilio SMS</Divider>
            <Form.Item
              name="api_key_id"
              label="Twilio Account SID"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="AC..." />
            </Form.Item>
            <Form.Item name="api_token" label="Twilio Auth Token">
              {editConfig ? (
                <div>
                  <MaskedDisplay masked={editConfig.api_token_masked} />
                  <div className="mt-2">
                    <Form.Item name="api_token" noStyle>
                      <SecretInput helpText="Enter a new auth token to replace" />
                    </Form.Item>
                  </div>
                </div>
              ) : (
                <SecretInput placeholder="Enter Twilio Auth Token" />
              )}
            </Form.Item>
            <Form.Item
              name="sender_identifier"
              label="Sender number or messaging service SID"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="+14155238886 or MGxxxxxxx" />
            </Form.Item>
          </>
        )}

        {/* ── Generic HTTP SMS ─────────────────────────────────────────────── */}
        {channelType === 'sms' && provider === 'generic_http' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Generic HTTP SMS Gateway</Divider>
            <Form.Item
              name="sms_http_endpoint"
              label="Gateway endpoint URL"
              rules={[{ required: true, message: 'Required' }, { type: 'url', message: 'Must be a valid URL' }]}
            >
              <Input placeholder="https://sms-gateway.example.com/send" />
            </Form.Item>
            <Form.Item name="sender_identifier" label="Sender ID">
              <Input placeholder="Talentos" />
            </Form.Item>
            <Form.Item name="api_token" label="API key / auth token">
              {editConfig ? (
                <div>
                  <MaskedDisplay masked={editConfig.api_token_masked} />
                  <div className="mt-2">
                    <Form.Item name="api_token" noStyle>
                      <SecretInput />
                    </Form.Item>
                  </div>
                </div>
              ) : (
                <SecretInput placeholder="API key for the gateway" />
              )}
            </Form.Item>
          </>
        )}

        {/* ── Web Push (VAPID) ─────────────────────────────────────────────── */}
        {channelType === 'push' && provider === 'web_push' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Web Push (VAPID)</Divider>
            <Alert
              className="mb-3"
              type="warning"
              showIcon
              icon={<AlertCircle className="h-4 w-4" />}
              message="Push delivery implementation is architecture-ready. Deliveries will be tracked but not sent until the push provider is fully implemented."
            />
            <Form.Item name="push_vapid_public_key" label="VAPID public key">
              <Input.TextArea rows={2} placeholder="BHxxx..." />
            </Form.Item>
            <Form.Item name="push_vapid_private_key" label="VAPID private key">
              {editConfig ? (
                <SecretInput helpText="Enter new VAPID private key to replace" />
              ) : (
                <SecretInput placeholder="VAPID private key" />
              )}
            </Form.Item>
          </>
        )}

        {/* ── FCM ──────────────────────────────────────────────────────────── */}
        {channelType === 'push' && provider === 'fcm' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Firebase Cloud Messaging</Divider>
            <Alert className="mb-3" type="warning" showIcon message="Push delivery is architecture-ready but not yet fully implemented." />
            <Form.Item name="push_fcm_project_id" label="Firebase project ID">
              <Input placeholder="my-project-12345" />
            </Form.Item>
            <Form.Item name="api_token" label="Firebase Server Key / Service Account JSON">
              {editConfig ? (
                <SecretInput helpText="Enter new key to replace" />
              ) : (
                <SecretInput placeholder="Server key or paste service account JSON" />
              )}
            </Form.Item>
          </>
        )}

        {/* ── Mock / Dev ───────────────────────────────────────────────────── */}
        {provider === 'mock' && (
          <>
            <Divider className="my-3 text-xs text-slate-400">Mock provider</Divider>
            <Alert
              type="info"
              message="Mock provider logs sends to memory. Use in development and test environments only."
            />
          </>
        )}
      </Form>
    </Drawer>
  )
}
