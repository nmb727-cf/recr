import React, { useState } from 'react'
import { 
  Typography, 
  Card, 
  Tag, 
  Button, 
  Tabs, 
  List, 
  Avatar, 
  Switch, 
  message, 
  Badge, 
  Empty, 
  Spin,
  Modal,
  Form,
  Input,
  Select,
  Alert
} from 'antd'
import { 
  Plus, 
  Settings, 
  Mail, 
  Calendar, 
  Briefcase, 
  CheckCircle2, 
  Globe, 
  Database, 
  ShieldCheck, 
  CreditCard, 
  FileText,
  RefreshCw,
  ExternalLink,
  Lock,
  ChevronRight,
  Puzzle,
  Box
} from 'lucide-react'
import { useApiQuery } from '@/hooks/useApiQuery'
import { integrationsApi } from '@/api/integrations'
import { cn } from '@/utils/cn'

const { Title, Text } = Typography

const INTEGRATION_CATEGORIES = [
  { key: 'all', label: 'All App Ecosystem', icon: <Box size={14}/> },
  { key: 'email', label: 'Email', icon: <Mail size={14}/> },
  { key: 'calendar', label: 'Calendar', icon: <Calendar size={14}/> },
  { key: 'job_board', label: 'Job Boards', icon: <Briefcase size={14}/> },
  { key: 'assessment', label: 'Assessments', icon: <Puzzle size={14}/> },
  { key: 'hrms', label: 'HRMS', icon: <Database size={14}/> },
  { key: 'background_verification', label: 'Background Check', icon: <ShieldCheck size={14}/> },
  { key: 'payroll', label: 'Payroll', icon: <CreditCard size={14}/> },
  { key: 'offer', label: 'Offer Tools', icon: <FileText size={14}/> },
]

const ECOSYSTEM_PROVIDERS = [
  { provider_key: 'gmail', name: 'Gmail', category: 'email', description: 'Sync recruiter emails and candidate communications.', icon: 'GM' },
  { provider_key: 'outlook_email', name: 'Outlook Mail', category: 'email', description: 'Enterprise email sync for Office 365 users.', icon: 'OM' },
  { provider_key: 'google_calendar', name: 'Google Calendar', category: 'calendar', description: 'Automate interview scheduling and availability.', icon: 'GC' },
  { provider_key: 'outlook_calendar', name: 'Outlook Calendar', category: 'calendar', description: 'Schedule sync for Microsoft Teams and Outlook.', icon: 'OC' },
  { provider_key: 'linkedin', name: 'LinkedIn', category: 'job_board', description: 'Post jobs directly and import candidate profiles.', icon: 'LI' },
  { provider_key: 'indeed', name: 'Indeed', category: 'job_board', description: 'Global job board integration for high-volume roles.', icon: 'IN' },
  { provider_key: 'naukri', name: 'Naukri', category: 'job_board', description: 'Specialized integration for the Indian job market.', icon: 'NK' },
  { provider_key: 'hackerrank', name: 'HackerRank', category: 'assessment', description: 'Send coding tests and sync results automatically.', icon: 'HR' },
  { provider_key: 'codility', name: 'Codility', category: 'assessment', description: 'Technical assessment integration for engineering.', icon: 'CD' },
  { provider_key: 'workday', name: 'Workday', category: 'hrms', description: 'Enterprise HRMS sync for employee and job data.', icon: 'WD' },
  { provider_key: 'bamboohr', name: 'BambooHR', category: 'hrms', description: 'Popular SMB HRMS for seamless hiring-to-onboarding.', icon: 'BH' },
  { provider_key: 'checkr', name: 'Checkr', category: 'background_verification', description: 'Automated background checks for candidates.', icon: 'CH' },
  { provider_key: 'docuSign', name: 'DocuSign', category: 'offer', description: 'Send offer letters for digital signature.', icon: 'DS' },
]

export default function IntegrationHub() {
  const [activeTab, setActiveTab] = useState('all')
  const [configureModal, setConfigureModal] = useState<any>(null)

  const { data, isLoading, refetch } = useApiQuery(
    ['integrations-list'],
    () => integrationsApi.listIntegrations(),
    { staleTime: 30000 }
  )

  const installedIntegrations = (data as any)?.data?.integrations || []

  const handleToggle = async (provider: any, checked: boolean) => {
    try {
      await integrationsApi.updateIntegration({
        provider_key: provider.provider_key,
        name: provider.name,
        category: provider.category,
        status: checked ? 'active' : 'inactive',
        is_connected: checked
      })
      message.success(`${provider.name} ${checked ? 'activated' : 'deactivated'}`)
      refetch()
    } catch (e) {
      message.error("Failed to update integration status")
    }
  }

  const filteredProviders = activeTab === 'all' 
    ? ECOSYSTEM_PROVIDERS 
    : ECOSYSTEM_PROVIDERS.filter(p => p.category === activeTab)

  return (
    <div className="mx-auto max-w-[1600px] p-6 lg:p-10 flex flex-col gap-8 min-h-screen bg-[#F8FAFC]">
      
      {/* ─── Header ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm">
        <div className="flex items-center gap-5">
          <div className="h-16 w-16 rounded-2xl bg-slate-900 flex items-center justify-center text-white shadow-xl">
            <Globe size={32} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge status="processing" color="blue" />
              <Text className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">Connectivity Platform / Ecosystem</Text>
            </div>
            <Title level={2} className="!m-0 tracking-tight text-slate-900 font-black">Integration Hub</Title>
          </div>
        </div>
        <div className="flex items-center gap-3">
           <Button icon={<RefreshCw size={14} />} onClick={() => refetch()} className="h-12 rounded-xl font-bold uppercase text-[10px] tracking-widest border-slate-200 shadow-sm">Refresh Status</Button>
           <Button type="primary" icon={<Plus size={16} />} className="h-12 rounded-xl font-black uppercase text-[10px] tracking-widest bg-slate-900 border-none shadow-lg">Request Custom App</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* ─── Sidebar Categories ─── */}
        <div className="lg:col-span-1">
           <div className="bg-white rounded-[2rem] border border-slate-200 p-4 sticky top-10">
              <Text className="px-4 py-2 text-[11px] font-black uppercase tracking-widest text-slate-400 block mb-2">Marketplace Categories</Text>
              <div className="flex flex-col gap-1">
                 {INTEGRATION_CATEGORIES.map(cat => (
                   <div 
                     key={cat.key}
                     onClick={() => setActiveTab(cat.key)}
                     className={cn(
                       "flex items-center justify-between px-4 py-3 rounded-2xl cursor-pointer transition-all group",
                       activeTab === cat.key ? "bg-slate-900 text-white shadow-lg" : "hover:bg-slate-50 text-slate-600"
                     )}
                   >
                      <div className="flex items-center gap-3">
                         {cat.icon}
                         <span className="text-xs font-black uppercase tracking-tight">{cat.label}</span>
                      </div>
                      {activeTab !== cat.key && <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />}
                   </div>
                 ))}
              </div>
           </div>
        </div>

        {/* ─── Integration Cards Grid ─── */}
        <div className="lg:col-span-3">
           {isLoading ? (
             <div className="flex h-64 items-center justify-center bg-white rounded-[2.5rem] border border-slate-100">
                <Spin tip="Loading App Ecosystem..." />
             </div>
           ) : (
             <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredProviders.map(provider => {
                  const installed = installedIntegrations.find((i: any) => i.provider_key === provider.provider_key)
                  return (
                    <Card 
                      key={provider.provider_key}
                      className={cn(
                        "rounded-[2rem] border-slate-200 transition-all hover:shadow-xl hover:border-blue-200 group overflow-hidden",
                        installed?.status === 'active' ? "bg-white" : "bg-slate-50/50"
                      )}
                      bodyStyle={{ padding: 0 }}
                    >
                       <div className="p-6">
                          <div className="flex items-start justify-between mb-6">
                             <div className="h-12 w-12 rounded-xl bg-white shadow-sm border border-slate-100 flex items-center justify-center font-black text-slate-400 text-xs">
                                {provider.icon}
                             </div>
                             <Switch 
                               checked={installed?.status === 'active'} 
                               onChange={(checked) => handleToggle(provider, checked)}
                             />
                          </div>
                          
                          <div className="mb-6">
                             <div className="flex items-center gap-2 mb-1">
                                <Text className="text-sm font-black text-slate-800">{provider.name}</Text>
                                {installed?.status === 'active' && <CheckCircle2 size={12} className="text-emerald-500" />}
                             </div>
                             <Text className="text-xs text-slate-500 leading-relaxed block h-10 overflow-hidden line-clamp-2">
                                {provider.description}
                             </Text>
                          </div>

                          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                             <Tag className="m-0 border-none bg-slate-100 text-slate-500 text-[9px] font-black uppercase px-2 rounded-full">
                                {provider.category.replace('_', ' ')}
                             </Tag>
                             <Button 
                               type="link" 
                               className="p-0 h-auto text-[10px] font-black uppercase tracking-widest flex items-center gap-1 group-hover:text-blue-600 transition-colors"
                               onClick={() => setConfigureModal(provider)}
                             >
                                Configure <ChevronRight size={12} />
                             </Button>
                          </div>
                       </div>
                       
                       {installed?.status !== 'active' && (
                         <div className="px-6 py-2 bg-slate-100/50 text-center">
                            <Text className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Disconnected</Text>
                         </div>
                       )}
                    </Card>
                  )
                })}
             </div>
           )}
           
           {!isLoading && filteredProviders.length === 0 && (
             <Empty className="my-20" description="No providers found in this category." />
           )}
        </div>

      </div>

      {/* ─── Global Config Modal ─── */}
      <Modal
        title={
          <div className="flex items-center gap-3">
             <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Settings size={16}/></div>
             <span className="text-xs font-black uppercase tracking-widest text-slate-800">Configure {configureModal?.name}</span>
          </div>
        }
        open={!!configureModal}
        onCancel={() => setConfigureModal(null)}
        footer={null}
        centered
        className="rounded-[2rem] overflow-hidden"
      >
        <div className="py-6">
           <Alert 
             className="mb-6 rounded-2xl"
             message={<Text className="text-xs font-bold text-blue-800">OAuth Sandbox Environment</Text>}
             description={<Text className="text-[11px] text-blue-600 leading-relaxed block">This integration is currently in Sandbox mode. Connection tokens will be mocked until production credentials are verified.</Text>}
             type="info"
             showIcon
           />

           <Form layout="vertical" onFinish={() => {
             message.success(`${configureModal?.name} Connection Authenticated`)
             setConfigureModal(null)
           }}>
              <Form.Item label="Environment" initialValue="production">
                 <Select className="rounded-xl">
                    <Select.Option value="production">Production</Select.Option>
                    <Select.Option value="sandbox">Sandbox / Testing</Select.Option>
                 </Select>
              </Form.Item>
              
              <Form.Item label="API Client ID" required>
                 <Input className="rounded-xl font-mono text-xs" placeholder={`Enter ${configureModal?.name} ID...`} prefix={<Lock size={14} className="text-slate-300"/>} />
              </Form.Item>

              <Form.Item label="API Secret Key" required>
                 <Input.Password className="rounded-xl font-mono text-xs" placeholder="••••••••••••••••" prefix={<Lock size={14} className="text-slate-300"/>} />
              </Form.Item>

              <div className="bg-slate-50 p-4 rounded-2xl mb-6 border border-slate-100">
                 <div className="flex items-center justify-between mb-3">
                    <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Permission Scopes</Text>
                    <Tag className="m-0 border-none bg-emerald-100 text-emerald-700 text-[8px] font-black uppercase">Verified</Tag>
                 </div>
                 <div className="space-y-2">
                    <div className="flex items-center gap-2">
                       <CheckCircle2 size={12} className="text-emerald-500" />
                       <Text className="text-[11px] text-slate-600">Read application and profile data</Text>
                    </div>
                    <div className="flex items-center gap-2">
                       <CheckCircle2 size={12} className="text-emerald-500" />
                       <Text className="text-[11px] text-slate-600">Sync calendar events and availability</Text>
                    </div>
                 </div>
              </div>

              <Button block type="primary" htmlType="submit" className="h-12 rounded-2xl font-black uppercase text-xs tracking-widest bg-slate-900 border-none shadow-lg">
                 Authenticate & Connect
              </Button>
           </Form>
        </div>
      </Modal>

    </div>
  )
}
