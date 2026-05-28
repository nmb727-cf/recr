import { useState, useRef, useEffect } from 'react'
import {
  Row, Col, List, Avatar, Input, Button, Typography, Space,
  Spin, Empty, Drawer, Form, message as antdMessage, Badge,
} from 'antd'
import {
  SendOutlined, UserOutlined, PlusOutlined, SearchOutlined,
} from '@ant-design/icons'

const { TextArea } = Input
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useApiQuery } from '@/hooks/useApiQuery'
import { messagesApi } from '@/api/messages'
import { useAuth } from '@/hooks/useAuth'
import type { MessageThread, Message } from '@/types'

dayjs.extend(relativeTime)
const { Title, Text } = Typography

// ─── Thread Detail Component ──────────────────────────────────────────────────

function ThreadView({ threadId }: { threadId: string }) {
  const { user } = useAuth()
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const { data, isLoading, refetch } = useApiQuery(
    ['messages', threadId],
    () => messagesApi.getThreadMessages(threadId),
    { enabled: !!threadId }
  )

  const messages = (data as { messages: Message[] } | undefined)?.messages ?? []

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!reply.trim()) return
    setSending(true)
    try {
      await messagesApi.replyToThread(threadId, reply)
      setReply('')
      refetch()
    } catch (err) {
      antdMessage.error('Failed to send message')
    } finally {
      setSending(false)
    }
  }

  if (isLoading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}
      >
        <List
          dataSource={messages}
          split={false}
          renderItem={(m) => {
            const isMe = m.sender_id === user?.id
            return (
              <div
                style={{
                  display: 'flex',
                  justifyContent: isMe ? 'flex-end' : 'flex-start',
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    maxWidth: '70%',
                    padding: '8px 16px',
                    borderRadius: 16,
                    background: isMe ? '#1890ff' : '#f0f0f0',
                    color: isMe ? '#fff' : '#000',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                  }}
                >
                  <div style={{ wordBreak: 'break-word' }}>{m.body}</div>
                  <div
                    style={{
                      fontSize: 10,
                      textAlign: 'right',
                      marginTop: 4,
                      opacity: 0.7,
                    }}
                  >
                    {dayjs(m.created_at).format('HH:mm')}
                  </div>
                </div>
              </div>
            )
          }}
        />
      </div>

      <div style={{ padding: '16px 24px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="Type your message..."
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            onPressEnter={handleSend}
            disabled={sending}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={sending}
          >
            Send
          </Button>
        </Space.Compact>
      </div>
    </div>
  )
}

// ─── Main Messages Page ───────────────────────────────────────────────────────

export default function Messages() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [newMsgOpen, setNewMsgOpen] = useState(false)
  const [form] = Form.useForm()
  const [creating, setCreating] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(['message_threads'], () => messagesApi.listThreads())
  const threads = (data as { threads: MessageThread[] } | undefined)?.threads ?? []

  const handleCreate = async (values: any) => {
    setCreating(true)
    try {
      const res = await messagesApi.createThread(values)
      antdMessage.success('Message sent')
      setNewMsgOpen(false)
      form.resetFields()
      refetch()
      setSelectedThreadId(res.data.data.thread.id)
    } catch (err) {
      antdMessage.error('Failed to start thread')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{ height: 'calc(100vh - 120px)', margin: '-24px' }}>
      <Row style={{ height: '100%' }}>
        {/* Thread List */}
        <Col xs={24} md={8} lg={6} style={{ borderRight: '1px solid #f0f0f0', background: '#fff', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Title level={4} style={{ margin: 0 }}>Messages</Title>
              <Button type="primary" shape="circle" icon={<PlusOutlined />} onClick={() => setNewMsgOpen(true)} />
            </div>
            <Input prefix={<SearchOutlined />} placeholder="Search messages..." allowClear />
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>
            ) : threads.length > 0 ? (
              <List
                dataSource={threads}
                renderItem={(item) => (
                  <List.Item
                    onClick={() => setSelectedThreadId(item.id)}
                    style={{
                      padding: '12px 24px',
                      cursor: 'pointer',
                      background: selectedThreadId === item.id ? '#f0f7ff' : '#fff',
                      borderLeft: selectedThreadId === item.id ? '4px solid #1890ff' : '4px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <List.Item.Meta
                      avatar={
                        <Badge dot={item.unread_count > 0} color="#ff4d4f">
                          <Avatar icon={<UserOutlined />} />
                        </Badge>
                      }
                      title={
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Text strong={item.unread_count > 0} style={{ fontSize: 13 }}>{item.subject}</Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>{dayjs(item.last_message_at).fromNow(true)}</Text>
                        </div>
                      }
                      description={
                        <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 12 }}>
                          {item.last_message_preview}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty style={{ marginTop: 40 }} description="No conversations" />
            )}
          </div>
        </Col>

        {/* Message Content */}
        <Col xs={24} md={16} lg={18} style={{ background: '#f5f7fa', height: '100%' }}>
          {selectedThreadId ? (
            <ThreadView threadId={selectedThreadId} />
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Empty description="Select a conversation to read" />
            </div>
          )}
        </Col>
      </Row>

      <Drawer
        title="New Message"
        open={newMsgOpen}
        onClose={() => setNewMsgOpen(false)}
        width={400}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="recipient_id" label="Recipient User ID" rules={[{ required: true }]}>
            <Input placeholder="Enter user UUID" />
          </Form.Item>
          <Form.Item name="subject" label="Subject" rules={[{ required: true }]}>
            <Input placeholder="What is this about?" />
          </Form.Item>
          <Form.Item name="message" label="Message" rules={[{ required: true }]}>
            <TextArea rows={4} placeholder="Type your message here..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={creating}>
              Send Message
            </Button>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}
