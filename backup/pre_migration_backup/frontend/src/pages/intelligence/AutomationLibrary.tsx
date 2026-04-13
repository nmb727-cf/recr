import {
  Badge,
  Button,
  Card,
  Col,
  Empty,
  List,
  Row,
  Space,
  Spin,
  Tabs,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd'
import {
  BookOpen,
  CheckCircle,
  Copy,
  ExternalLink,
  Layers,
  Layout,
  Plus,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { useState } from 'react'

import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography

export default function AutomationLibrary() {
  const [activeTab, setActiveTab] = useState('system')

  const systemTemplatesQuery = useApiQuery(['intelligence-templates', 'system'], intelligenceHubApi.listLibraryTemplates)
  const tenantTemplatesQuery = useApiQuery(['intelligence-templates', 'tenant'], intelligenceHubApi.listTenantTemplates)

  const cloneMutation = useApiMutation(
    (id: string) => intelligenceHubApi.cloneLibraryTemplate(id),
    {
      successMessage: 'Template cloned to your tenant library.',
      invalidateKeys: [['intelligence-templates', 'tenant']],
    }
  )

  const activateMutation = useApiMutation(
    (id: string) => intelligenceHubApi.activateLibraryTemplate(id),
    {
      successMessage: 'Template activated and policy created.',
      invalidateKeys: [['intelligence-hub', 'automation-policies']],
    }
  )

  const isLoading = systemTemplatesQuery.isLoading || tenantTemplatesQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Space direction="vertical" align="center">
          <Spin size="large" />
          <Text className="text-slate-500">Loading enterprise library...</Text>
        </Space>
      </div>
    )
  }

  const systemTemplates = (systemTemplatesQuery.data as any)?.data || []
  const tenantTemplates = (tenantTemplatesQuery.data as any)?.data || []

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <Title level={3} className="!m-0">Enterprise Automation Library</Title>
        <Paragraph className="text-slate-500 max-w-3xl">
          Browse and deploy prebuilt, industry-standard automation templates to accelerate your intelligence operations.
        </Paragraph>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        className="automation-library-tabs"
        items={[
          {
            key: 'system',
            label: <Space><BookOpen size={16}/><span>System Templates</span></Space>,
            children: <TemplateGrid 
              templates={systemTemplates} 
              onClone={(id) => cloneMutation.mutate(id)}
              onActivate={(id) => activateMutation.mutate(id)}
              isSystem
              loading={cloneMutation.isPending || activateMutation.isPending}
            />
          },
          {
            key: 'tenant',
            label: <Space><Layout size={16}/><span>My Templates</span></Space>,
            children: <TemplateGrid 
              templates={tenantTemplates} 
              onActivate={(id) => activateMutation.mutate(id)}
              loading={activateMutation.isPending}
            />
          }
        ]}
      />
    </div>
  )
}

function TemplateGrid({ templates, onClone, onActivate, isSystem, loading }: { templates: any[], onClone?: (id: string) => void, onActivate: (id: string) => void, isSystem?: boolean, loading?: boolean }) {
  if (templates.length === 0) {
    return <Card className="rounded-3xl border-slate-200"><Empty description="No templates found in this category." /></Card>
  }

  return (
    <Row gutter={[24, 24]}>
      {templates.map((template) => (
        <Col xs={24} md={12} lg={8} key={template.id}>
          <Card 
            className="rounded-3xl border-slate-200 shadow-sm hover:shadow-md transition-all h-full flex flex-col"
            bodyStyle={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column' }}
          >
            <div className="flex justify-between items-start mb-4">
              <Tag color="blue" className="rounded-full px-3 text-[10px] font-black uppercase tracking-widest">
                {template.category.replace(/_/g, ' ')}
              </Tag>
              <RiskBadge level={template.default_risk_level} />
            </div>
            
            <Title level={5} className="!m-0 mb-2">{template.name}</Title>
            <Paragraph className="text-slate-500 text-xs line-clamp-2 mb-4">
              {template.description}
            </Paragraph>

            <div className="bg-slate-50 rounded-2xl p-4 mb-6 space-y-3">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-indigo-500" />
                <Text className="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Trigger: {template.trigger_type.replace(/_/g, ' ')}</Text>
              </div>
              <div className="flex items-start gap-2">
                <Layers size={14} className="text-slate-400 mt-1" />
                <div className="flex flex-wrap gap-1">
                  {(template.action_set || []).map((action: any, idx: number) => (
                    <Tag key={idx} className="text-[9px] m-0 bg-white border-slate-200">{action.type || action}</Tag>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-auto flex gap-2">
              {isSystem ? (
                <>
                  <Button 
                    className="flex-1 rounded-xl font-bold text-xs h-10" 
                    icon={<Copy size={14}/>}
                    onClick={() => onClone?.(template.id)}
                    loading={loading}
                  >
                    Clone
                  </Button>
                  <Button 
                    type="primary" 
                    className="flex-1 rounded-xl font-bold text-xs h-10 bg-indigo-600" 
                    icon={<Plus size={14}/>}
                    onClick={() => onActivate(template.id)}
                    loading={loading}
                  >
                    Use
                  </Button>
                </>
              ) : (
                <Button 
                  type="primary" 
                  className="w-full rounded-xl font-bold text-xs h-10 bg-indigo-600" 
                  icon={<ShieldCheck size={14}/>}
                  onClick={() => onActivate(template.id)}
                  loading={loading}
                >
                  Activate Policy
                </Button>
              )}
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    low: 'green',
    medium: 'blue',
    high: 'orange',
    critical: 'red'
  }
  return (
    <Tooltip title={`Risk Level: ${level.toUpperCase()}`}>
      <Badge status={colors[level] as any} text={<Text className="text-[10px] font-black uppercase text-slate-400">{level}</Text>} />
    </Tooltip>
  )
}
