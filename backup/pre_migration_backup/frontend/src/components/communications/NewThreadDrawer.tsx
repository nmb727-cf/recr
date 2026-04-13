import { useState } from 'react'
import { Drawer, Form, Input, Select, Switch, Button, message as antMessage } from 'antd'
import { messagesApi } from '@/api/messages'
import type { ThreadType } from '@/types/communications'
import { THREAD_TYPE_LABELS } from '@/types/communications'

interface Props {
  open: boolean
  onClose: () => void
  onCreated: (threadId: string) => void
}

interface FormValues {
  subject: string
  thread_type: ThreadType
  is_internal: boolean
  initial_message: string
}

const THREAD_TYPE_OPTIONS = (Object.keys(THREAD_TYPE_LABELS) as ThreadType[]).map((key) => ({
  value: key,
  label: THREAD_TYPE_LABELS[key],
}))

export function NewThreadDrawer({ open, onClose, onCreated }: Props) {
  const [form] = Form.useForm<FormValues>()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: FormValues) => {
    setLoading(true)
    try {
      const res = await messagesApi.createThread({
        subject: values.subject,
        thread_type: values.thread_type,
        is_internal: values.is_internal,
        message: values.initial_message,
      })
      const thread = res.data?.data?.thread
      if (thread) {
        antMessage.success('Conversation started')
        form.resetFields()
        onCreated(thread.id)
      }
    } catch {
      antMessage.error('Failed to create conversation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Drawer
      title="New Conversation"
      placement="right"
      width={420}
      open={open}
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" onClick={() => form.submit()} loading={loading}>
            Start Conversation
          </Button>
        </div>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ thread_type: 'internal', is_internal: true }}
      >
        <Form.Item
          name="subject"
          label="Subject"
          rules={[{ required: true, message: 'Please enter a subject' }]}
        >
          <Input placeholder="What is this conversation about?" />
        </Form.Item>

        <Form.Item name="thread_type" label="Type">
          <Select options={THREAD_TYPE_OPTIONS} />
        </Form.Item>

        <Form.Item name="is_internal" label="Internal only" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item
          name="initial_message"
          label="First message"
          rules={[{ required: true, message: 'Please write an initial message' }]}
        >
          <Input.TextArea
            rows={4}
            placeholder="Write your first message…"
            showCount
            maxLength={2000}
          />
        </Form.Item>
      </Form>
    </Drawer>
  )
}
