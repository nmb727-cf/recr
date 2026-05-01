import React, { useState, useMemo } from 'react'
import { 
  Typography, 
  Card, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Drawer, 
  Tabs, 
  Badge, 
  Descriptions, 
  Empty, 
  message,
  Modal,
  Form,
  Input,
  Select,
  Tooltip,
  Alert
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { 
  Activity, 
  Zap, 
  Layers, 
  Clock, 
  Bug, 
  Terminal,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Play
} from 'lucide-react'
import dayjs from 'dayjs'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery, useApiMutation } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

// --- Helpers ---
const statusColor = (v: string) => {
  const s = String(v).toLowerCase()
  if (['emitted', 'matched', 'executed', 'consumed'].includes(s)) return 'blue'
  if (['failed', 'blocked'].includes(s)) return 'red'
  if (['ignored', 'filtered_out'].includes(s)) return 'default'
  return 'default'
}

// --- Components ---

const EventRegistry = () => {
  const { data, isLoading } = useApiQuery(['workflow-events', 'registry'], () => intelligenceHubApi.listWorkflowEventRegistry())
  
  const columns: ColumnsType<any> = [
    { title: 'Event Name', dataIndex: 'event_name', key: 'name', render: (v) => <Text strong>{v}</Text> },
    { title: 'Key', dataIndex: 'event_key', key: 'key', render: (v) => <Tag color="blue" className="font-mono">{v}</Tag> },
    { title: 'Module', dataIndex: 'module_scope', key: 'module', render: (v) => <Tag>{v?.toUpperCase()}</Tag> },
    { title: 'Status', dataIndex: 'is_active', key: 'status', render: (v) => v ? <Badge status="processing" text="Active" /> : <Badge status="default" text="Inactive" /> },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={data?.data || []} loading={isLoading} pagination={{ pageSize: 20 }} />
    </Card>
  )
}

const EventLog = () => {
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const { data, isLoading, refetch } = useApiQuery(['workflow-events', 'logs'], () => intelligenceHubApi.listWorkflowEventLogs())
  
  const { data: detailData, isLoading: isDetailLoading } = useApiQuery(
    ['workflow-events', 'logs', selectedLogId], 
    () => intelligenceHubApi.getWorkflowEventLogDetail(selectedLogId!),
    { enabled: !!selectedLogId }
  )

  const { data: traceData } = useApiQuery(
    ['workflow-events', 'logs', selectedLogId, 'traces'],
    () => intelligenceHubApi.getWorkflowEventDebugTraces(selectedLogId!),
    { enabled: !!selectedLogId }
  )

  const columns: ColumnsType<any> = [
    { title: 'Event', dataIndex: 'event_key', key: 'event', render: (v) => <Text strong>{v}</Text> },
    { title: 'Source', dataIndex: 'source_module', key: 'source', render: (v) => <Tag>{v}</Tag> },
    { title: 'Entity', key: 'entity', render: (_, r) => <Text className="text-xs font-mono">{r.entity_type}:{r.entity_id.slice(0,8)}</Text> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v) => <Tag color={statusColor(v)}>{v?.toUpperCase()}</Tag> },
    { title: 'Time', dataIndex: 'created_at', key: 'time', render: (v) => dayjs(v).format('HH:mm:ss') },
    { 
      title: 'Action', 
      key: 'action', 
      render: (_, r) => <Button size="small" onClick={() => setSelectedLogId(r.id)}>Inspect</Button> 
    },
  ]

  return (
    <>
      <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <Text className="text-slate-500">Real-time stream of system events and workflow trigger evaluations.</Text>
          <Button icon={<RefreshCw size={14}/>} onClick={() => refetch()} />
        </div>
        <Table rowKey="id" columns={columns} dataSource={data?.data || []} loading={isLoading} pagination={{ pageSize: 15 }} />
      </Card>

      <Drawer
        title={<div className="flex items-center gap-2"><Bug size={18} className="text-indigo-500"/> Event Debug Trace</div>}
        open={!!selectedLogId}
        onClose={() => setSelectedLogId(null)}
        width={600}
        className="rounded-l-3xl"
      >
        {isDetailLoading ? <div className="p-10 text-center"><RefreshCw className="animate-spin inline mr-2"/> Loading trace...</div> : (
          <div className="space-y-8">
            <div className="rounded-3xl bg-slate-50 p-6 border border-slate-100">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Event Key"><Tag color="blue">{detailData?.data?.event_key}</Tag></Descriptions.Item>
                <Descriptions.Item label="Source Module">{detailData?.data?.source_module}</Descriptions.Item>
                <Descriptions.Item label="Entity">{detailData?.data?.entity_type}:{detailData?.data?.entity_id}</Descriptions.Item>
                <Descriptions.Item label="Status"><Tag color={statusColor(detailData?.data?.status)}>{detailData?.data?.status?.toUpperCase()}</Tag></Descriptions.Item>
              </Descriptions>
            </div>

            <div className="space-y-4">
               <Text className="text-[11px] font-black uppercase tracking-widest text-slate-400 px-2">Event Payload</Text>
               <pre className="p-4 bg-slate-950 text-indigo-300 text-[10px] rounded-2xl overflow-auto max-h-60">
                 {JSON.stringify(detailData?.data?.payload, null, 2)}
               </pre>
            </div>

            <div className="space-y-4">
               <Text className="text-[11px] font-black uppercase tracking-widest text-slate-400 px-2">Workflow Dispatch Traces</Text>
               {traceData?.data?.length ? (
                 <div className="space-y-3">
                   {traceData.data.map((trace: any, i: number) => (
                     <div key={i} className="p-4 rounded-2xl border border-slate-100 bg-white shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                           <Text strong className="text-slate-800">{trace.workflow_name}</Text>
                           <Tag color={statusColor(trace.decision)}>{trace.decision?.toUpperCase()}</Tag>
                        </div>
                        <Text className="text-xs text-slate-500 block mb-2">{trace.reason}</Text>
                        {trace.trace_payload && (
                          <pre className="p-2 bg-slate-50 rounded-lg text-[10px] text-slate-400">
                            {JSON.stringify(trace.trace_payload, null, 2)}
                          </pre>
                        )}
                     </div>
                   ))}
                 </div>
               ) : (
                 <div className="py-10 text-center border-2 border-dashed border-slate-100 rounded-3xl">
                    <Terminal size={32} className="text-slate-200 mx-auto mb-2"/>
                    <Text type="secondary" italic>No workflows matched this event trigger.</Text>
                 </div>
               )}
            </div>
          </div>
        )}
      </Drawer>
    </>
  )
}

const Subscriptions = () => {
  const { data, isLoading } = useApiQuery(['workflow-events', 'subscriptions'], () => intelligenceHubApi.listWorkflowEventSubscriptions())
  
  const columns: ColumnsType<any> = [
    { title: 'Workflow', dataIndex: 'workflow_name', key: 'wf', render: (v) => <Text strong>{v}</Text> },
    { title: 'Listens To', dataIndex: 'event_definition_name', key: 'event', render: (v, r) => <div><Text>{v}</Text><br/><Text className="text-[10px] text-slate-400 font-mono">{r.event_definition_key}</Text></div> },
    { title: 'Filters', dataIndex: 'trigger_filters', key: 'filters', render: (v) => v && Object.keys(v).length ? Object.entries(v).map(([k, val]) => <Tag key={k} className="text-[10px]">{k}={String(val)}</Tag>) : <Text type="secondary" className="text-[10px]">No filters</Text> },
    { title: 'Status', dataIndex: 'is_active', key: 'status', render: (v) => v ? <Tag color="green">ACTIVE</Tag> : <Tag color="default">PAUSED</Tag> },
  ]

  return (
    <Card className="rounded-[2.5rem] border-slate-200 shadow-sm overflow-hidden" bodyStyle={{ padding: 0 }}>
      <Table rowKey="id" columns={columns} dataSource={data?.data || []} loading={isLoading} pagination={{ pageSize: 20 }} />
    </Card>
  )
}

export default function WorkflowEventWorkspace() {
  const [activeTab, setActiveTab] = useState('logs')
  const [isTestModalOpen, setIsTestModalOpen] = useState(false)
  const [testForm] = Form.useForm()

  const { data: registryData } = useApiQuery(['workflow-events', 'registry'], () => intelligenceHubApi.listWorkflowEventRegistry())

  const testMutation = useApiMutation(
    (payload: any) => intelligenceHubApi.testEmitWorkflowEvent(payload),
    {
      successMessage: 'Test event emitted successfully.',
      onSuccess: () => {
        setIsTestModalOpen(false)
        testForm.resetFields()
      }
    }
  )

  return (
    <div className="grid gap-8">
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex justify-between items-start">
          <div className="space-y-2">
            <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-indigo-400">Foundation Engine</Text>
            <Title level={2} className="!mb-0 !mt-0">Event Trigger System</Title>
            <Paragraph className="!mb-0 max-w-4xl text-slate-500">
              Open event-driven architecture. Monitor system events, manage workflow subscriptions, and debug trigger evaluations across all modules.
            </Paragraph>
          </div>
          <Button type="primary" icon={<Play size={14}/>} className="rounded-xl h-10 px-6 font-bold" onClick={() => setIsTestModalOpen(true)}>Emit Test Event</Button>
        </div>

        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          className="workflow-hub-tabs"
          items={[
            { key: 'logs', label: <div className="flex items-center gap-2"><Activity size={14}/> Activity Log</div> },
            { key: 'subscriptions', label: <div className="flex items-center gap-2"><Layers size={14}/> Subscriptions</div> },
            { key: 'registry', label: <div className="flex items-center gap-2"><Zap size={14}/> Event Registry</div> },
          ]}
        />
      </div>

      <div className="min-h-[400px]">
        {activeTab === 'logs' && <EventLog />}
        {activeTab === 'subscriptions' && <Subscriptions />}
        {activeTab === 'registry' && <EventRegistry />}
      </div>

      <Modal
        title="Emit Test Event"
        open={isTestModalOpen}
        onCancel={() => setIsTestModalOpen(false)}
        onOk={() => testForm.submit()}
        confirmLoading={testMutation.isPending}
        className="rounded-3xl"
        width={500}
      >
        <Form form={testForm} layout="vertical" onFinish={(v) => {
          try {
            const payload = JSON.parse(v.payload_json || '{}')
            testMutation.mutate({ ...v, payload })
          } catch (e) {
            message.error('Invalid JSON in payload field')
          }
        }} className="py-4">
          <Form.Item name="event_key" label="Event Type" rules={[{ required: true }]}>
            <Select 
              showSearch
              placeholder="Select an event to simulate"
              options={registryData?.data?.map((e: any) => ({ label: `${e.event_name} (${e.event_key})`, value: e.event_key }))}
              className="rounded-xl"
            />
          </Form.Item>
          <Form.Item name="payload_json" label="Payload Data (JSON)" initialValue='{"source": "test_studio"}'>
            <Input.TextArea rows={6} className="rounded-xl font-mono text-xs" />
          </Form.Item>
          <Alert 
            type="warning" 
            showIcon 
            message="This will trigger real workflows." 
            description="All active workflows subscribed to this event in your tenant will execute if filters match."
            className="rounded-xl"
          />
        </Form>
      </Modal>
    </div>
  )
}
