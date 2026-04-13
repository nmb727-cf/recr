import {
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Form,
  InputNumber,
  List,
  Row,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  Activity,
  AlertOctagon,
  FileText,
  Lock,
  ShieldCheck,
  ShieldOff,
  Sliders,
  Zap,
  ZapOff,
} from 'lucide-react'
import dayjs from 'dayjs'
import { useState } from 'react'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function IntelligenceGovernance() {
  const [isEditingLimits, setIsEditingLimits] = useState(false)
  
  const summaryQuery = useApiQuery(['intelligence-governance', 'summary'], intelligenceHubApi.getGovernanceSummary)
  const auditQuery = useApiQuery(['intelligence-governance', 'audit'], intelligenceHubApi.getGovernanceAudit)
  const policiesQuery = useApiQuery(['intelligence-hub', 'automation-policies'], intelligenceHubApi.listAutomationPolicies)

  const updateMutation = useApiMutation(
    (payload: any) => intelligenceHubApi.updateGovernanceSummary(payload),
    {
      successMessage: 'Governance settings updated successfully.',
      invalidateKeys: [['intelligence-governance', 'summary'], ['intelligence-governance', 'audit']],
      onSuccess: () => setIsEditingLimits(false),
    }
  )

  const isLoading = summaryQuery.isLoading || auditQuery.isLoading || policiesQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Loading AI governance controls...</Text>
        </Space>
      </div>
    )
  }

  const summary = (summaryQuery.data as any)?.data || { settings: {}, limits: {} }
  const auditLogs = (auditQuery.data as any)?.data || []
  const policies = (policiesQuery.data as any)?.data || []

  const handleToggleKillSwitch = (key: string, value: boolean) => {
    updateMutation.mutate({
      settings: { [key]: value }
    })
  }

  const handleUpdateLimits = (values: any) => {
    updateMutation.mutate({
      limits: values
    })
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0">AI Governance & Safety</Title>
        <Paragraph className="text-slate-500 max-w-3xl">
          Enterprise-grade controls for AI safety, risk management, usage limits, and a global kill switch for autonomous operations.
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {/* 1. Kill Switch Panel */}
        <Col lg={10}>
          <Card 
            title={<Space><AlertOctagon className="text-rose-600" size={18}/><span>Global Safety Switches</span></Space>}
            className="rounded-3xl border-rose-100 shadow-sm h-full"
            bodyStyle={{ padding: '24px' }}
          >
            <div className="space-y-6">
              <KillSwitchItem 
                title="AI Core Enablement"
                description="Globally enable or disable all LLM-based suggestion and analysis features."
                enabled={summary.settings.ai_enabled}
                onToggle={(val) => handleToggleKillSwitch('ai_enabled', val)}
                loading={updateMutation.isPending}
                icon={summary.settings.ai_enabled ? <Zap className="text-amber-500" size={20}/> : <ZapOff className="text-slate-400" size={20}/>}
              />
              <Divider className="my-0" />
              <KillSwitchItem 
                title="Autonomous Execution"
                description="Allow automation rules to trigger background tasks without direct human initiation."
                enabled={summary.settings.automation_enabled}
                onToggle={(val) => handleToggleKillSwitch('automation_enabled', val)}
                loading={updateMutation.isPending}
                icon={summary.settings.automation_enabled ? <Activity className="text-indigo-500" size={20}/> : <ShieldOff className="text-slate-400" size={20}/>}
              />
              <Divider className="my-0" />
              <KillSwitchItem 
                title="Direct State Application (Auto-Apply)"
                description="Permit the system to update business data (e.g., candidate stages) without manual review."
                enabled={summary.settings.auto_apply_enabled}
                onToggle={(val) => handleToggleKillSwitch('auto_apply_enabled', val)}
                loading={updateMutation.isPending}
                icon={summary.settings.auto_apply_enabled ? <ShieldCheck className="text-emerald-500" size={20}/> : <Lock className="text-slate-400" size={20}/>}
              />
            </div>
          </Card>
        </Col>

        {/* 2. Usage Limits Panel */}
        <Col lg={14}>
          <Card 
            title={<Space><Sliders className="text-indigo-600" size={18}/><span>Usage & Rate Limits</span></Space>}
            className="rounded-3xl border-slate-200 shadow-sm h-full"
            extra={!isEditingLimits && <Button type="link" onClick={() => setIsEditingLimits(true)}>Edit Limits</Button>}
          >
            <Form 
              layout="vertical" 
              initialValues={summary.limits} 
              onFinish={handleUpdateLimits}
              disabled={!isEditingLimits}
            >
              <Row gutter={24}>
                <Col span={12}>
                   <Form.Item name="daily_limit" label="Daily Automation Limit" extra="Max AI calls per 24h">
                      <InputNumber className="w-full rounded-xl" min={0} />
                   </Form.Item>
                </Col>
                <Col span={12}>
                   <Form.Item name="hourly_limit" label="Hourly Rate Limit" extra="Burst protection">
                      <InputNumber className="w-full rounded-xl" min={0} />
                   </Form.Item>
                </Col>
                <Col span={12}>
                   <Form.Item name="max_auto_apply" label="Max Daily Auto-Applies" extra="Safeguard for state changes">
                      <InputNumber className="w-full rounded-xl" min={0} />
                   </Form.Item>
                </Col>
                <Col span={12}>
                   <Form.Item name="max_failures" label="Failure Threshold (Auto-Kill)" extra="Stop automation if errors exceed this">
                      <InputNumber className="w-full rounded-xl" min={0} />
                   </Form.Item>
                </Col>
              </Row>
              {isEditingLimits && (
                <Space className="mt-4">
                  <Button type="primary" htmlType="submit" loading={updateMutation.isPending} className="rounded-xl">Save Limits</Button>
                  <Button onClick={() => setIsEditingLimits(false)} className="rounded-xl">Cancel</Button>
                </Space>
              )}
            </Form>
          </Card>
        </Col>
      </Row>

      {/* 3. Risk Control Panel (Policy Risk Levels) */}
      <Card 
        title={<Space><ShieldCheck className="text-indigo-600" size={18}/><span>Policy Risk Governance</span></Space>}
        className="rounded-3xl border-slate-200 shadow-sm overflow-hidden"
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          rowKey="id"
          columns={POLICY_RISK_COLUMNS}
          dataSource={policies}
          pagination={false}
        />
      </Card>

      {/* 4. Governance Audit Panel */}
      <Card 
        title={<Space><FileText className="text-slate-400" size={18}/><span>Governance Audit Trail</span></Space>}
        className="rounded-3xl border-slate-200 shadow-sm overflow-hidden"
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          rowKey="id"
          columns={AUDIT_COLUMNS}
          dataSource={auditLogs}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

function KillSwitchItem({ title, description, enabled, onToggle, loading, icon }: { title: string, description: string, enabled: boolean, onToggle: (val: boolean) => void, loading: boolean, icon: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex gap-4">
        <div className={cn("p-3 rounded-2xl", enabled ? "bg-slate-50" : "bg-slate-100 opacity-50")}>
          {icon}
        </div>
        <div>
          <Text strong className="block text-slate-800">{title}</Text>
          <Text className="text-xs text-slate-500">{description}</Text>
        </div>
      </div>
      <Switch 
        checked={enabled} 
        onChange={onToggle} 
        loading={loading} 
        className={enabled ? 'bg-indigo-600' : 'bg-slate-200'}
      />
    </div>
  )
}

const POLICY_RISK_COLUMNS: ColumnsType<any> = [
  {
    title: 'Policy / Suggestion Type',
    key: 'policy',
    render: (_, record) => (
      <Space direction="vertical" size={0}>
        <Text strong className="text-slate-800">{record.suggestion_type.replace(/_/g, ' ')}</Text>
        <Text type="secondary" className="text-[10px]">{record.module_scope || 'Global'}</Text>
      </Space>
    )
  },
  {
    title: 'Risk Level',
    dataIndex: 'risk_level',
    key: 'risk',
    render: (v) => (
      <Tag color={v === 'critical' ? 'red' : v === 'high' ? 'orange' : v === 'medium' ? 'blue' : 'green'} className="rounded-full px-3 uppercase text-[10px] font-black tracking-widest">
        {v}
      </Tag>
    )
  },
  {
    title: 'Auto-Apply Allowed',
    dataIndex: 'auto_apply_allowed',
    key: 'apply',
    render: (v) => v ? <Tag color="green">ENABLED</Tag> : <Tag color="default">DISABLED</Tag>
  },
  {
    title: 'Enforcement Rule',
    key: 'enforcement',
    render: (_, record) => {
      const v = record.risk_level
      if (v === 'critical') return <Text type="danger" strong className="text-xs">MANUAL ONLY</Text>
      if (v === 'high') return <Text type="warning" strong className="text-xs">ADMIN APPROVAL REQ.</Text>
      if (v === 'medium') return <Text strong className="text-xs text-indigo-600">APPROVAL REQUIRED</Text>
      return <Text className="text-xs text-emerald-600">AUTO-APPLY ALLOWED</Text>
    }
  }
]

const AUDIT_COLUMNS: ColumnsType<any> = [
  {
    title: 'Timestamp',
    dataIndex: 'timestamp',
    key: 'time',
    render: (v) => dayjs(v).format('MMM DD, HH:mm:ss')
  },
  {
    title: 'Action',
    dataIndex: 'action',
    key: 'action',
    render: (v) => (
      <Tag color={v === 'kill_switch_toggled' ? 'volcano' : v === 'limit_exceeded' ? 'red' : 'blue'}>
        {v.replace(/_/g, ' ').toUpperCase()}
      </Tag>
    )
  },
  {
    title: 'Performed By',
    dataIndex: 'performed_by',
    key: 'user',
    render: (v) => v ? <Text className="text-xs font-mono">{String(v).slice(0, 8)}</Text> : <Text italic className="text-slate-300">System</Text>
  },
  {
    title: 'Details',
    dataIndex: 'details',
    key: 'details',
    render: (v) => <Text className="text-[10px] text-slate-500 font-mono">{JSON.stringify(v)}</Text>
  }
]
