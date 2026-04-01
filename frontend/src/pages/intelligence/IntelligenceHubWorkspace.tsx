import {
  Alert,
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

type IntelligenceSection = 'suggestions' | 'automations' | 'executions' | 'failures' | 'prompts' | 'settings'
type AnyRecord = Record<string, any>

const SECTION_ITEMS: Array<{ key: IntelligenceSection; label: string }> = [
  { key: 'suggestions', label: 'Suggestions' },
  { key: 'automations', label: 'Automations' },
  { key: 'executions', label: 'Executions' },
  { key: 'failures', label: 'Failures' },
  { key: 'prompts', label: 'Prompts' },
  { key: 'settings', label: 'Settings' },
]

function normalizeSection(section?: string): IntelligenceSection {
  if (SECTION_ITEMS.some((item) => item.key === section)) {
    return section as IntelligenceSection
  }
  return 'suggestions'
}

function formatDateTime(value: unknown) {
  if (!value) return 'Not available'
  const parsed = dayjs(String(value))
  return parsed.isValid() ? parsed.format('DD MMM YYYY, HH:mm') : String(value)
}

function humanize(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Not set'
  return String(value).replace(/_/g, ' ')
}

function shortId(value: unknown) {
  if (!value) return 'n/a'
  const stringValue = String(value)
  return stringValue.length > 12 ? `${stringValue.slice(0, 8)}…` : stringValue
}

function prettyJson(value: unknown) {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

function statusColor(value: unknown) {
  const normalized = String(value ?? '').toLowerCase()
  if (/completed|approved|healthy|active|resolved|converted|valid/.test(normalized)) return 'green'
  if (/queued|pending|review|warning|retrying|scheduled|testing|partial/.test(normalized)) return 'gold'
  if (/failed|rejected|disabled|cancelled|expired|invalid/.test(normalized)) return 'red'
  return 'default'
}

function confidenceColor(value: unknown) {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized === 'high') return 'green'
  if (normalized === 'medium') return 'gold'
  if (normalized === 'low') return 'red'
  return 'default'
}

function countByStatus(items: AnyRecord[], status: string) {
  return items.filter((item) => String(item.status) === status).length
}

function parseJsonField(label: string, raw: string, fallback: unknown) {
  const value = raw.trim()
  if (!value) return fallback
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} must be valid JSON.`)
  }
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="flex min-h-[320px] items-center justify-center rounded-3xl border border-slate-200 bg-white">
      <Space direction="vertical" align="center" size={16}>
        <Spin size="large" />
        <Text className="text-slate-500">{label}</Text>
      </Space>
    </div>
  )
}

function ErrorState({ title, error }: { title: string; error: unknown }) {
  return (
    <Alert
      type="error"
      showIcon
      message={title}
      description={(error as { message?: string })?.message || 'The screen could not be loaded from the backend endpoint.'}
    />
  )
}

function SectionHeader({
  section,
  navigate,
}: {
  section: IntelligenceSection
  navigate: ReturnType<typeof useNavigate>
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <Text className="text-[11px] font-black uppercase tracking-[0.28em] text-slate-400">Intelligence Hub / Operational MVP</Text>
          <Title level={2} className="!mb-0 !mt-0">
            Intelligence Hub
          </Title>
          <Paragraph className="!mb-0 max-w-4xl text-slate-500">
            Backend-wired operational surfaces for suggestions, automations, executions, failures, prompts, and tenant intelligence settings.
          </Paragraph>
        </div>
        <Tag className="w-fit rounded-full border-slate-200 bg-slate-50 px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-700">
          MVP UI
        </Tag>
      </div>

      <div className="flex flex-wrap gap-2">
        {SECTION_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => navigate(item.key === 'suggestions' ? '/intelligence' : `/intelligence/${item.key}`)}
            className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.18em] transition ${
              item.key === section
                ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function DetailJson({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="space-y-2">
      <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">{title}</Text>
      <pre className="max-h-[280px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{prettyJson(value)}</pre>
    </div>
  )
}

function SuggestionsSection() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const suggestionsQuery = useApiQuery(['intelligence-hub', 'suggestions'], intelligenceHubApi.listSuggestions, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const selectedSuggestionQuery = useApiQuery(
    ['intelligence-hub', 'suggestion', selectedId],
    () => intelligenceHubApi.getSuggestion(selectedId as string),
    { enabled: Boolean(selectedId), retry: false, refetchOnWindowFocus: false },
  )

  const suggestions = (suggestionsQuery.data as AnyRecord[] | undefined) ?? []

  const columns = useMemo<ColumnsType<AnyRecord>>(
    () => [
      { title: 'Title', dataIndex: 'title', key: 'title' },
      {
        title: 'Category',
        key: 'category',
        render: (_, record) => (
          <Space size={6} wrap>
            <Tag color="blue">{humanize(record.category)}</Tag>
            <Tag>{humanize(record.payload_json?.suggestion_subtype || record.suggestion_key)}</Tag>
          </Space>
        ),
      },
      {
        title: 'Confidence',
        key: 'confidence',
        render: (_, record) => (
          <Space size={6} wrap>
            <Tag color={confidenceColor(record.confidence_band)}>{humanize(record.confidence_band)}</Tag>
            <Text>{record.confidence_score ?? '—'}</Text>
          </Space>
        ),
      },
      {
        title: 'Source',
        key: 'source',
        render: (_, record) => `${humanize(record.source_module)} / ${humanize(record.source_entity_type)}:${shortId(record.source_entity_id)}`,
      },
      {
        title: 'Status',
        key: 'status',
        render: (_, record) => <Tag color={statusColor(record.status)}>{humanize(record.status)}</Tag>,
      },
      { title: 'Updated', key: 'updated_at', render: (_, record) => formatDateTime(record.updated_at) },
    ],
    [],
  )

  if (suggestionsQuery.isLoading) return <LoadingState label="Loading suggestions from Intelligence Hub…" />
  if (suggestionsQuery.error) return <ErrorState title="Suggestions could not be loaded." error={suggestionsQuery.error} />

  const selectedSuggestion = selectedSuggestionQuery.data as AnyRecord | undefined

  return (
    <>
      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">Suggestions</Title>
          <Text className="text-slate-500">Review real AI suggestions with confidence, rationale, source execution, and current status.</Text>
        </div>
        {suggestions.length ? (
          <Table
            rowKey="id"
            columns={columns}
            dataSource={suggestions}
            pagination={{ pageSize: 10, hideOnSinglePage: true }}
            onRow={(record) => ({ onClick: () => setSelectedId(String(record.id)), className: 'cursor-pointer' })}
          />
        ) : (
          <div className="p-10"><Empty description="No suggestions exist yet for this tenant." /></div>
        )}
      </Card>

      <Drawer title="Suggestion Detail" width={720} open={Boolean(selectedId)} onClose={() => setSelectedId(null)} destroyOnClose>
        {selectedSuggestionQuery.isLoading ? (
          <LoadingState label="Loading suggestion detail…" />
        ) : selectedSuggestionQuery.error ? (
          <ErrorState title="Suggestion detail could not be loaded." error={selectedSuggestionQuery.error} />
        ) : selectedSuggestion ? (
          <Space direction="vertical" size={20} className="w-full">
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Title">{selectedSuggestion.title}</Descriptions.Item>
              <Descriptions.Item label="Category">
                <Space wrap>
                  <Tag color="blue">{humanize(selectedSuggestion.category)}</Tag>
                  <Tag>{humanize(selectedSuggestion.payload_json?.suggestion_subtype || selectedSuggestion.suggestion_key)}</Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Current status"><Tag color={statusColor(selectedSuggestion.status)}>{humanize(selectedSuggestion.status)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Confidence">
                <Space wrap>
                  <Tag color={confidenceColor(selectedSuggestion.confidence_band)}>{humanize(selectedSuggestion.confidence_band)}</Tag>
                  <Text>{selectedSuggestion.confidence_score ?? 'Not available'}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Summary">{selectedSuggestion.summary || 'No summary provided.'}</Descriptions.Item>
              <Descriptions.Item label="Source entity">{`${humanize(selectedSuggestion.source_module)} / ${humanize(selectedSuggestion.source_entity_type)}:${selectedSuggestion.source_entity_id}`}</Descriptions.Item>
              <Descriptions.Item label="Source execution">
                {selectedSuggestion.ai_request ? (
                  <Space direction="vertical" size={0}>
                    <Text>{String(selectedSuggestion.ai_request.id)}</Text>
                    <Text type="secondary">{`${humanize(selectedSuggestion.ai_request.module_scope)} / ${humanize(selectedSuggestion.ai_request.use_case_key)} / ${humanize(selectedSuggestion.ai_request.status)}`}</Text>
                  </Space>
                ) : 'Not linked'}
              </Descriptions.Item>
              <Descriptions.Item label="Created">{formatDateTime(selectedSuggestion.created_at)}</Descriptions.Item>
              <Descriptions.Item label="Updated">{formatDateTime(selectedSuggestion.updated_at)}</Descriptions.Item>
            </Descriptions>
            <DetailJson title="Rationale" value={selectedSuggestion.rationale_json} />
            <DetailJson title="Payload" value={selectedSuggestion.payload_json} />
            <DetailJson title="Audit Metadata" value={selectedSuggestion.audit_metadata_json} />
          </Space>
        ) : <Empty description="Suggestion detail is not available." />}
      </Drawer>
    </>
  )
}

function AutomationsSection() {
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null)
  const rulesQuery = useApiQuery(['intelligence-hub', 'automations'], intelligenceHubApi.listAutomations, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const automationRunsQuery = useApiQuery(['intelligence-hub', 'executions', 'automation'], intelligenceHubApi.listExecutionsAutomation, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const selectedRuleQuery = useApiQuery(
    ['intelligence-hub', 'automation', selectedRuleId],
    () => intelligenceHubApi.getAutomation(selectedRuleId as string),
    { enabled: Boolean(selectedRuleId), retry: false, refetchOnWindowFocus: false },
  )
  const selectedRuleRunsQuery = useApiQuery(
    ['intelligence-hub', 'automation', selectedRuleId, 'runs'],
    () => intelligenceHubApi.listAutomationRuns(selectedRuleId as string),
    { enabled: Boolean(selectedRuleId), retry: false, refetchOnWindowFocus: false },
  )

  const rules = (rulesQuery.data as AnyRecord[] | undefined) ?? []
  const allRuns = (automationRunsQuery.data as AnyRecord[] | undefined) ?? []
  const runsByRule = useMemo(() => {
    return allRuns.reduce<Record<string, AnyRecord[]>>((acc, run) => {
      const ruleId = String(run.rule)
      if (!acc[ruleId]) acc[ruleId] = []
      acc[ruleId].push(run)
      return acc
    }, {})
  }, [allRuns])

  const rows = useMemo(() => rules.map((rule) => {
    const runs = runsByRule[String(rule.id)] ?? []
    const lastRun = runs[0]
    return { ...rule, run_count: runs.length, last_run_at: lastRun?.created_at ?? '' }
  }), [rules, runsByRule])

  const columns = useMemo<ColumnsType<AnyRecord>>(
    () => [
      { title: 'Rule', dataIndex: 'rule_title', key: 'rule_title' },
      { title: 'Module', dataIndex: 'module_scope', key: 'module_scope', render: humanize },
      { title: 'Trigger', dataIndex: 'trigger_event', key: 'trigger_event' },
      { title: 'Status', key: 'status', render: (_, record) => <Tag color={statusColor(record.status)}>{humanize(record.status)}</Tag> },
      { title: 'Last run', key: 'last_run_at', render: (_, record) => record.last_run_at ? formatDateTime(record.last_run_at) : 'No runs yet' },
      { title: 'Run count', dataIndex: 'run_count', key: 'run_count' },
    ],
    [],
  )

  if (rulesQuery.isLoading || automationRunsQuery.isLoading) return <LoadingState label="Loading automation rules…" />
  if (rulesQuery.error) return <ErrorState title="Automation rules could not be loaded." error={rulesQuery.error} />
  if (automationRunsQuery.error) return <ErrorState title="Automation run history could not be loaded." error={automationRunsQuery.error} />

  const selectedRule = selectedRuleQuery.data as AnyRecord | undefined
  const selectedRuns = (selectedRuleRunsQuery.data as AnyRecord[] | undefined) ?? []

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.9fr)]">
      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">Automation Rules</Title>
          <Text className="text-slate-500">Real rule inventory with live status, last run visibility, and execution counts from backend runtime data.</Text>
        </div>
        {rows.length ? (
          <Table rowKey="id" columns={columns} dataSource={rows} pagination={{ pageSize: 10, hideOnSinglePage: true }} onRow={(record) => ({ onClick: () => setSelectedRuleId(String(record.id)), className: 'cursor-pointer' })} />
        ) : (
          <div className="p-10"><Empty description="No automation rules exist yet." /></div>
        )}
      </Card>

      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        {!selectedRuleId ? (
          <Empty description="Select an automation rule to inspect details and recent runs." />
        ) : selectedRuleQuery.isLoading || selectedRuleRunsQuery.isLoading ? (
          <LoadingState label="Loading automation detail…" />
        ) : selectedRuleQuery.error ? (
          <ErrorState title="Automation detail could not be loaded." error={selectedRuleQuery.error} />
        ) : selectedRule ? (
          <Space direction="vertical" size={20} className="w-full">
            <div>
              <Title level={4} className="!mb-1 !mt-0">{selectedRule.rule_title}</Title>
              <Text type="secondary">{selectedRule.rule_key}</Text>
            </div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Status"><Tag color={statusColor(selectedRule.status)}>{humanize(selectedRule.status)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Module">{humanize(selectedRule.module_scope)}</Descriptions.Item>
              <Descriptions.Item label="Trigger">{selectedRule.trigger_event}</Descriptions.Item>
              <Descriptions.Item label="Mode">{humanize(selectedRule.mode)}</Descriptions.Item>
              <Descriptions.Item label="Priority">{selectedRule.priority_order}</Descriptions.Item>
              <Descriptions.Item label="Duplicate window">{selectedRule.duplicate_window_seconds} seconds</Descriptions.Item>
              <Descriptions.Item label="Conditions">{selectedRule.conditions?.length ?? 0}</Descriptions.Item>
              <Descriptions.Item label="Actions">{selectedRule.actions?.length ?? 0}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="Run History">
              {selectedRuns.length ? (
                <Space direction="vertical" size={12} className="w-full">
                  <Space wrap>
                    <Tag color="blue">{selectedRuns.length} total</Tag>
                    <Tag color="green">{countByStatus(selectedRuns, 'completed')} completed</Tag>
                    <Tag color="gold">{countByStatus(selectedRuns, 'queued') + countByStatus(selectedRuns, 'scheduled')} queued</Tag>
                    <Tag color="red">{countByStatus(selectedRuns, 'failed')} failed</Tag>
                  </Space>
                  {selectedRuns.slice(0, 5).map((run, index) => (
                    <div key={String(run.id ?? index)} className="rounded-2xl border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-4">
                        <Text strong>{humanize(run.source_event)}</Text>
                        <Tag color={statusColor(run.status)}>{humanize(run.status)}</Tag>
                      </div>
                      <Text type="secondary">{`${humanize(run.source_entity_type)}:${run.source_entity_id}`}</Text>
                      <div className="mt-2 text-xs text-slate-500">{formatDateTime(run.created_at)}</div>
                    </div>
                  ))}
                </Space>
              ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No runs exist for this rule yet." />}
            </Card>
          </Space>
        ) : <Empty description="Automation detail is not available." />}
      </Card>
    </div>
  )
}

function ExecutionsSection() {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null)
  const aiExecutionsQuery = useApiQuery(['intelligence-hub', 'executions', 'ai'], intelligenceHubApi.listExecutionsAI, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const automationExecutionsQuery = useApiQuery(['intelligence-hub', 'executions', 'automation'], intelligenceHubApi.listExecutionsAutomation, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const selectedExecutionQuery = useApiQuery(
    ['intelligence-hub', 'execution', selectedExecutionId],
    () => intelligenceHubApi.getExecutionDetail(selectedExecutionId as string),
    { enabled: Boolean(selectedExecutionId), retry: false, refetchOnWindowFocus: false },
  )

  const rows = useMemo(() => {
    const aiRows = (((aiExecutionsQuery.data as AnyRecord[] | undefined) ?? []).map((item) => ({
      id: String(item.id),
      execution_type: 'ai',
      status: item.status,
      source_module: item.module_scope,
      source_entity_type: item.source_entity_type,
      source_entity_id: item.source_entity_id,
      source_event: item.source_event,
      created_at: item.created_at,
    })))
    const automationRows = (((automationExecutionsQuery.data as AnyRecord[] | undefined) ?? []).map((item) => ({
      id: String(item.id),
      execution_type: 'automation',
      status: item.status,
      source_module: item.source_module,
      source_entity_type: item.source_entity_type,
      source_entity_id: item.source_entity_id,
      source_event: item.source_event,
      created_at: item.created_at,
    })))
    return [...aiRows, ...automationRows].sort(
      (left, right) => dayjs(String(right.created_at || '')).valueOf() - dayjs(String(left.created_at || '')).valueOf(),
    )
  }, [aiExecutionsQuery.data, automationExecutionsQuery.data])

  const columns = useMemo<ColumnsType<AnyRecord>>(
    () => [
      { title: 'Type', key: 'execution_type', render: (_, record) => <Tag color={record.execution_type === 'ai' ? 'blue' : 'purple'}>{humanize(record.execution_type)}</Tag> },
      { title: 'Status', key: 'status', render: (_, record) => <Tag color={statusColor(record.status)}>{humanize(record.status)}</Tag> },
      { title: 'Module', dataIndex: 'source_module', key: 'source_module', render: humanize },
      { title: 'Source', key: 'source', render: (_, record) => `${humanize(record.source_entity_type)}:${shortId(record.source_entity_id)}` },
      { title: 'Event', dataIndex: 'source_event', key: 'source_event', render: humanize },
      { title: 'Created', key: 'created_at', render: (_, record) => formatDateTime(record.created_at) },
    ],
    [],
  )

  if (aiExecutionsQuery.isLoading || automationExecutionsQuery.isLoading) return <LoadingState label="Loading executions…" />
  if (aiExecutionsQuery.error) return <ErrorState title="AI executions could not be loaded." error={aiExecutionsQuery.error} />
  if (automationExecutionsQuery.error) return <ErrorState title="Automation executions could not be loaded." error={automationExecutionsQuery.error} />

  const selectedExecution = selectedExecutionQuery.data as AnyRecord | undefined

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.9fr)]">
      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">Executions</Title>
          <Text className="text-slate-500">Unified view of AI execution requests and automation runs with source context and timestamps.</Text>
        </div>
        {rows.length ? (
          <Table rowKey="id" columns={columns} dataSource={rows} pagination={{ pageSize: 10, hideOnSinglePage: true }} onRow={(record) => ({ onClick: () => setSelectedExecutionId(String(record.id)), className: 'cursor-pointer' })} />
        ) : (
          <div className="p-10"><Empty description="No executions exist yet." /></div>
        )}
      </Card>

      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        {!selectedExecutionId ? (
          <Empty description="Select an execution to inspect source details and timestamps." />
        ) : selectedExecutionQuery.isLoading ? (
          <LoadingState label="Loading execution detail…" />
        ) : selectedExecutionQuery.error ? (
          <ErrorState title="Execution detail could not be loaded." error={selectedExecutionQuery.error} />
        ) : selectedExecution ? (
          <Space direction="vertical" size={20} className="w-full">
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Execution type"><Tag color={selectedExecution.execution_type === 'ai' ? 'blue' : 'purple'}>{humanize(selectedExecution.execution_type)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Status"><Tag color={statusColor(selectedExecution.payload?.status)}>{humanize(selectedExecution.payload?.status)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Source module">{humanize(selectedExecution.payload?.source_module || selectedExecution.payload?.module_scope)}</Descriptions.Item>
              <Descriptions.Item label="Source entity">{`${humanize(selectedExecution.payload?.source_entity_type)}:${selectedExecution.payload?.source_entity_id}`}</Descriptions.Item>
              <Descriptions.Item label="Source event">{humanize(selectedExecution.payload?.source_event)}</Descriptions.Item>
              <Descriptions.Item label="Created">{formatDateTime(selectedExecution.payload?.created_at)}</Descriptions.Item>
              <Descriptions.Item label="Started">{formatDateTime(selectedExecution.payload?.started_at)}</Descriptions.Item>
              <Descriptions.Item label="Completed">{formatDateTime(selectedExecution.payload?.completed_at)}</Descriptions.Item>
            </Descriptions>
            <DetailJson title="Execution Payload" value={selectedExecution.payload} />
          </Space>
        ) : <Empty description="Execution detail is not available." />}
      </Card>
    </div>
  )
}

function FailuresSection() {
  const [selectedFailureId, setSelectedFailureId] = useState<string | null>(null)
  const failuresQuery = useApiQuery(['intelligence-hub', 'failures'], intelligenceHubApi.listFailures, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 30_000,
  })
  const failures = (failuresQuery.data as AnyRecord[] | undefined) ?? []
  const selectedFailure = failures.find((item) => String(item.id) === selectedFailureId) ?? null

  const columns = useMemo<ColumnsType<AnyRecord>>(
    () => [
      { title: 'Type', dataIndex: 'failure_type', key: 'failure_type', render: humanize },
      { title: 'Category', dataIndex: 'category', key: 'category', render: humanize },
      { title: 'Status', key: 'status', render: (_, record) => <Tag color={statusColor(record.status)}>{humanize(record.status)}</Tag> },
      { title: 'Retryable', key: 'retryable', render: (_, record) => <Tag color={record.retryable ? 'gold' : 'default'}>{record.retryable ? 'Yes' : 'No'}</Tag> },
      { title: 'Linked execution', key: 'related_request_id', render: (_, record) => shortId(record.related_request_id) },
      { title: 'Created', key: 'created_at', render: (_, record) => formatDateTime(record.created_at) },
    ],
    [],
  )

  if (failuresQuery.isLoading) return <LoadingState label="Loading failures…" />
  if (failuresQuery.error) return <ErrorState title="Failures could not be loaded." error={failuresQuery.error} />

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.9fr)]">
      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">Failures</Title>
          <Text className="text-slate-500">Operational failure list with retryability, reason, and linked execution visibility.</Text>
        </div>
        {failures.length ? (
          <Table rowKey="id" columns={columns} dataSource={failures} pagination={{ pageSize: 10, hideOnSinglePage: true }} onRow={(record) => ({ onClick: () => setSelectedFailureId(String(record.id)), className: 'cursor-pointer' })} />
        ) : (
          <div className="p-10"><Empty description="No failures are currently recorded." /></div>
        )}
      </Card>
      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        {!selectedFailure ? (
          <Empty description="Select a failure to inspect its reason and linkage." />
        ) : (
          <Space direction="vertical" size={20} className="w-full">
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Failure type">{humanize(selectedFailure.failure_type)}</Descriptions.Item>
              <Descriptions.Item label="Category">{humanize(selectedFailure.category)}</Descriptions.Item>
              <Descriptions.Item label="Status"><Tag color={statusColor(selectedFailure.status)}>{humanize(selectedFailure.status)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Retryable"><Tag color={selectedFailure.retryable ? 'gold' : 'default'}>{selectedFailure.retryable ? 'Yes' : 'No'}</Tag></Descriptions.Item>
              <Descriptions.Item label="Linked execution">{selectedFailure.related_request_id || 'Not linked'}</Descriptions.Item>
              <Descriptions.Item label="Reason">{selectedFailure.last_error_message || 'No reason recorded.'}</Descriptions.Item>
              <Descriptions.Item label="Created">{formatDateTime(selectedFailure.created_at)}</Descriptions.Item>
            </Descriptions>
          </Space>
        )}
      </Card>
    </div>
  )
}

function PromptsSection() {
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null)
  const promptsQuery = useApiQuery(['intelligence-hub', 'prompts'], intelligenceHubApi.listPrompts, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
  })
  const selectedPromptQuery = useApiQuery(
    ['intelligence-hub', 'prompt', selectedPromptId],
    () => intelligenceHubApi.getPrompt(selectedPromptId as string),
    { enabled: Boolean(selectedPromptId), retry: false, refetchOnWindowFocus: false },
  )

  const prompts = (promptsQuery.data as AnyRecord[] | undefined) ?? []
  const rows = useMemo(() => prompts.map((prompt) => {
    const versions = Array.isArray(prompt.versions) ? prompt.versions : []
    const activeVersion = versions.find((version: AnyRecord) => String(version.id) === String(prompt.active_version_id))
    return { ...prompt, version_count: versions.length, active_version_label: activeVersion ? `v${activeVersion.version_number}` : 'No active version' }
  }), [prompts])

  const columns = useMemo<ColumnsType<AnyRecord>>(
    () => [
      { title: 'Prompt', dataIndex: 'prompt_title', key: 'prompt_title' },
      { title: 'Module', dataIndex: 'module_scope', key: 'module_scope', render: humanize },
      { title: 'Use case', dataIndex: 'use_case_key', key: 'use_case_key', render: humanize },
      { title: 'Versions', dataIndex: 'version_count', key: 'version_count' },
      { title: 'Active version', dataIndex: 'active_version_label', key: 'active_version_label' },
      { title: 'State', key: 'status', render: (_, record) => <Tag color={statusColor(record.status)}>{humanize(record.status)}</Tag> },
    ],
    [],
  )

  if (promptsQuery.isLoading) return <LoadingState label="Loading prompts…" />
  if (promptsQuery.error) return <ErrorState title="Prompts could not be loaded." error={promptsQuery.error} />

  const selectedPrompt = selectedPromptQuery.data as AnyRecord | undefined

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.9fr)]">
      <Card className="rounded-3xl border border-slate-200 shadow-sm" bodyStyle={{ padding: 0 }}>
        <div className="border-b border-slate-200 px-6 py-4">
          <Title level={4} className="!m-0">Prompts</Title>
          <Text className="text-slate-500">Prompt registry inventory with module, use case, version info, and active state.</Text>
        </div>
        {rows.length ? (
          <Table rowKey="id" columns={columns} dataSource={rows} pagination={{ pageSize: 10, hideOnSinglePage: true }} onRow={(record) => ({ onClick: () => setSelectedPromptId(String(record.id)), className: 'cursor-pointer' })} />
        ) : (
          <div className="p-10"><Empty description="No prompts exist yet." /></div>
        )}
      </Card>
      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        {!selectedPromptId ? (
          <Empty description="Select a prompt to inspect version info and current state." />
        ) : selectedPromptQuery.isLoading ? (
          <LoadingState label="Loading prompt detail…" />
        ) : selectedPromptQuery.error ? (
          <ErrorState title="Prompt detail could not be loaded." error={selectedPromptQuery.error} />
        ) : selectedPrompt ? (
          <Space direction="vertical" size={20} className="w-full">
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Prompt">{selectedPrompt.prompt_title}</Descriptions.Item>
              <Descriptions.Item label="Module">{humanize(selectedPrompt.module_scope)}</Descriptions.Item>
              <Descriptions.Item label="Use case">{humanize(selectedPrompt.use_case_key)}</Descriptions.Item>
              <Descriptions.Item label="State"><Tag color={statusColor(selectedPrompt.status)}>{humanize(selectedPrompt.status)}</Tag></Descriptions.Item>
              <Descriptions.Item label="Active version">{selectedPrompt.active_version_id || 'No active version'}</Descriptions.Item>
              <Descriptions.Item label="Tenant override allowed">{selectedPrompt.tenant_override_allowed ? 'Yes' : 'No'}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="Versions">
              {selectedPrompt.versions?.length ? (
                <Space direction="vertical" size={12} className="w-full">
                  {selectedPrompt.versions.map((version: AnyRecord) => (
                    <div key={version.id} className="rounded-2xl border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-4">
                        <Text strong>{`Version ${version.version_number}`}</Text>
                        <Tag color={statusColor(version.status)}>{humanize(version.status)}</Tag>
                      </div>
                      <Text type="secondary">{version.approval_required ? 'Approval required' : 'Suggestion-ready'}</Text>
                    </div>
                  ))}
                </Space>
              ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No versions exist for this prompt." />}
            </Card>
          </Space>
        ) : <Empty description="Prompt detail is not available." />}
      </Card>
    </div>
  )
}

function SettingsSection() {
  const [form] = Form.useForm()
  const settingsQuery = useApiQuery(['intelligence-hub', 'settings'], intelligenceHubApi.getSettings, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
  })
  const updateSettingsMutation = useApiMutation(intelligenceHubApi.updateSettings, {
    successMessage: 'Intelligence Hub settings updated.',
    errorMessage: 'Settings could not be updated.',
    invalidateKeys: [['intelligence-hub', 'settings']],
  })

  useEffect(() => {
    if (!settingsQuery.data) return
    form.setFieldsValue({
      ai_enabled: settingsQuery.data.ai_enabled,
      automation_enabled: settingsQuery.data.automation_enabled,
      default_approval_mode: settingsQuery.data.default_approval_mode,
      allowed_provider_ids_json: prettyJson(settingsQuery.data.allowed_provider_ids_json ?? []),
      feature_flags_json: prettyJson(settingsQuery.data.feature_flags_json ?? {}),
      notification_preferences_json: prettyJson(settingsQuery.data.notification_preferences_json ?? {}),
      retry_policy_overrides_json: prettyJson(settingsQuery.data.retry_policy_overrides_json ?? {}),
      connector_enablement_json: prettyJson(settingsQuery.data.connector_enablement_json ?? {}),
      visibility_permissions_json: prettyJson(settingsQuery.data.visibility_permissions_json ?? {}),
    })
  }, [form, settingsQuery.data])

  if (settingsQuery.isLoading) return <LoadingState label="Loading tenant intelligence settings…" />
  if (settingsQuery.error) return <ErrorState title="Settings could not be loaded." error={settingsQuery.error} />

  const settings = settingsQuery.data as AnyRecord

  const submit = async (values: AnyRecord) => {
    try {
      await updateSettingsMutation.mutateAsync({
        ai_enabled: values.ai_enabled,
        automation_enabled: values.automation_enabled,
        default_approval_mode: values.default_approval_mode,
        allowed_provider_ids_json: parseJsonField('Allowed providers', values.allowed_provider_ids_json, []),
        feature_flags_json: parseJsonField('Feature flags', values.feature_flags_json, {}),
        notification_preferences_json: parseJsonField('Notification preferences', values.notification_preferences_json, {}),
        retry_policy_overrides_json: parseJsonField('Retry policy overrides', values.retry_policy_overrides_json, {}),
        connector_enablement_json: parseJsonField('Connector enablement', values.connector_enablement_json, {}),
        visibility_permissions_json: parseJsonField('Visibility permissions', values.visibility_permissions_json, {}),
      })
    } catch {}
  }

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.8fr)]">
      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        <div className="mb-6">
          <Title level={4} className="!mb-1 !mt-0">Tenant Intelligence Settings</Title>
          <Text className="text-slate-500">Functional settings form backed by the live tenant intelligence settings endpoint.</Text>
        </div>
        <Form form={form} layout="vertical" onFinish={submit}>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Form.Item label="AI enabled" name="ai_enabled" valuePropName="checked"><Switch /></Form.Item>
            <Form.Item label="Automation enabled" name="automation_enabled" valuePropName="checked"><Switch /></Form.Item>
          </div>
          <Form.Item label="Default approval mode" name="default_approval_mode">
            <Select options={[
              { label: 'Suggestion only', value: 'suggestion_only' },
              { label: 'Auto apply', value: 'auto_apply' },
              { label: 'Approval required', value: 'approval_required' },
            ]} />
          </Form.Item>
          <Form.Item label="Allowed provider IDs JSON" name="allowed_provider_ids_json"><TextArea rows={4} /></Form.Item>
          <Form.Item label="Feature flags JSON" name="feature_flags_json"><TextArea rows={6} /></Form.Item>
          <Form.Item label="Notification preferences JSON" name="notification_preferences_json"><TextArea rows={4} /></Form.Item>
          <Form.Item label="Retry policy overrides JSON" name="retry_policy_overrides_json"><TextArea rows={4} /></Form.Item>
          <Form.Item label="Connector enablement JSON" name="connector_enablement_json"><TextArea rows={4} /></Form.Item>
          <Form.Item label="Visibility permissions JSON" name="visibility_permissions_json"><TextArea rows={4} /></Form.Item>
          <div className="flex justify-end"><Button type="primary" htmlType="submit" loading={updateSettingsMutation.isPending}>Save settings</Button></div>
        </Form>
      </Card>

      <Card className="rounded-3xl border border-slate-200 shadow-sm">
        <Space direction="vertical" size={20} className="w-full">
          <div>
            <Text className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Current State</Text>
            <Title level={4} className="!mb-0 !mt-2">Operational Summary</Title>
          </div>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Tenant">{settings.tenant_id}</Descriptions.Item>
            <Descriptions.Item label="AI"><Tag color={settings.ai_enabled ? 'green' : 'red'}>{settings.ai_enabled ? 'Enabled' : 'Disabled'}</Tag></Descriptions.Item>
            <Descriptions.Item label="Automation"><Tag color={settings.automation_enabled ? 'green' : 'red'}>{settings.automation_enabled ? 'Enabled' : 'Disabled'}</Tag></Descriptions.Item>
            <Descriptions.Item label="Approval mode">{humanize(settings.default_approval_mode)}</Descriptions.Item>
            <Descriptions.Item label="Allowed providers">{Array.isArray(settings.allowed_provider_ids_json) ? settings.allowed_provider_ids_json.length : 0}</Descriptions.Item>
            <Descriptions.Item label="Updated">{formatDateTime(settings.updated_at)}</Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>
    </div>
  )
}

export default function IntelligenceHubWorkspace() {
  const params = useParams<{ section?: string }>()
  const navigate = useNavigate()
  const section = normalizeSection(params.section)

  return (
    <div className="mx-auto flex max-w-[1560px] flex-col gap-6 p-6">
      <SectionHeader section={section} navigate={navigate} />
      {section === 'suggestions' ? <SuggestionsSection /> : null}
      {section === 'automations' ? <AutomationsSection /> : null}
      {section === 'executions' ? <ExecutionsSection /> : null}
      {section === 'failures' ? <FailuresSection /> : null}
      {section === 'prompts' ? <PromptsSection /> : null}
      {section === 'settings' ? <SettingsSection /> : null}
    </div>
  )
}
