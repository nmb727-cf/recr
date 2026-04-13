import React, { useState, useEffect, useRef, useMemo } from 'react'
import { 
  Typography, 
  Card, 
  Button, 
  Space, 
  Tag, 
  message, 
  Spin, 
  Divider, 
  Input, 
  Select, 
  Form,
  Badge,
  Tooltip,
  Alert,
  Drawer,
  Collapse,
  Switch,
  InputNumber
} from 'antd'
import { 
  Play, 
  Pause, 
  Save, 
  CheckCircle2, 
  XCircle, 
  Plus, 
  Settings, 
  Trash2, 
  ChevronRight, 
  ArrowLeft,
  Copy,
  Zap,
  Activity,
  Box,
  Layers,
  Clock,
  Send,
  MoreVertical,
  Maximize,
  Minimize,
  RefreshCw,
  AlertTriangle,
  CheckSquare,
  User,
  Calendar,
  FileText,
  Globe,
  GitBranch,
  UserPlus,
  ShieldCheck,
  TrendingUp,
  FileSearch,
  Check
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useNavigate } from 'react-router-dom'
import { intelligenceHubApi } from '@/api/intelligenceHub'
import { useApiQuery } from '@/hooks/useApiQuery'
import { cn } from '@/utils/cn'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

// ─── Business Blocks Palette ───────────────────────────────────────────────

const BUSINESS_BLOCKS = [
  { type: 'stage', label: 'Stage', icon: <Layers size={16}/>, color: 'sky', description: 'General process step' },
  { type: 'interview', label: 'Interview', icon: <Calendar size={16}/>, color: 'blue', description: 'Schedule/capture feedback' },
  { type: 'decision', label: 'Decision', icon: <GitBranch size={16}/>, color: 'orange', description: 'Pass/Fail/Hold logic' },
  { type: 'approval', label: 'Approval', icon: <ShieldCheck size={16}/>, color: 'purple', description: 'Review gate' },
  { type: 'offer', label: 'Offer', icon: <TrendingUp size={16}/>, color: 'green', description: 'Terms & negotiation' },
  { type: 'assignment', label: 'Assignment', icon: <UserPlus size={16}/>, color: 'slate', description: 'Assign owner' },
  { type: 'wait', label: 'Wait', icon: <Clock size={16}/>, color: 'gray', description: 'Pause execution' },
  { type: 'notification', label: 'Notification', icon: <Zap size={16}/>, color: 'amber', description: 'Send alerts' },
  { type: 'document', label: 'Document', icon: <FileText size={16}/>, color: 'indigo', description: 'Generate/sign' },
  { type: 'handoff', label: 'Handoff', icon: <Send size={16}/>, color: 'emerald', description: 'System/HR handoff' },
  { type: 'custom', label: 'Custom Stage', icon: <Settings size={16}/>, color: 'rose', description: 'Advanced logic' },
]

const COLORS: Record<string, string> = {
  sky: '#0ea5e9',
  blue: '#3b82f6',
  orange: '#f97316',
  purple: '#a855f7',
  green: '#22c55e',
  gray: '#6b7280',
  amber: '#f59e0b',
  indigo: '#6366f1',
  emerald: '#10b981',
  rose: '#f43f5e',
  slate: '#475569',
}

// ─── Builder Component ─────────────────────────────────────────────────────

export default function AdvancedWorkflowBuilder() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const canvasRef = useRef<HTMLDivElement>(null)
  
  const [nodes, setNodes] = useState<any[]>([])
  const [edges, setEdges] = useState<any[]>([])
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [isSaving, setIsBuilderSaving] = useState(false)
  const [validationErrors, setErrors] = useState<string[]>([])
  const [workflowMetadata, setMetadata] = useState({ name: '', description: '', version: '1.0' })
  const [zoom, setZoom] = useState(1)

  const { data: workflowData, isLoading } = useApiQuery(
    ['workflow-builder', id],
    () => intelligenceHubApi.getWorkflowBuilder(id!),
    { enabled: !!id }
  )

  useEffect(() => {
    if (workflowData?.data) {
      const { name, description, version, nodes: initialNodes, edges: initialEdges } = workflowData.data
      setMetadata({ name, description, version: version || '1.0' })
      
      setNodes(initialNodes.map((n: any) => ({
        id: n.id,
        type: n.node_type,
        config: n.config || {},
        position: { x: n.position_x, y: n.position_y }
      })))
      
      setEdges(initialEdges.map((e: any) => ({
        id: e.id,
        source: e.source_node,
        target: e.target_node,
        condition: e.condition || {}
      })))
    }
  }, [workflowData])

  const handleAddStage = (type: string) => {
    // Auto-position next to last stage for horizontal flow
    const lastNode = nodes.length > 0 ? nodes[nodes.length - 1] : null
    const x = lastNode ? lastNode.position.x + 280 : 100
    const y = lastNode ? lastNode.position.y : 200

    const newNode = {
      id: `stage_${Math.random().toString(36).substr(2, 5)}`,
      type,
      config: { name: `New ${type.charAt(0).toUpperCase() + type.slice(1)}` },
      position: { x, y }
    }
    
    setNodes([...nodes, newNode])
    
    // Auto-connect if there was a previous stage
    if (lastNode && type !== 'decision') {
      const newEdge = {
        id: `edge_${Math.random().toString(36).substr(2, 5)}`,
        source: lastNode.id,
        target: newNode.id,
        condition: {}
      }
      setEdges([...edges, newEdge])
    }
    
    setSelectedNodeId(newNode.id)
  }

  const handleNodeDrag = (id: string, newPos: { x: number, y: number }) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, position: newPos } : n))
  }

  const updateNodeConfig = (id: string, config: any) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, config: { ...n.config, ...config } } : n))
  }

  const handleSave = async (statusOverride?: string) => {
    setIsBuilderSaving(true)
    try {
      if (id) {
        await intelligenceHubApi.saveWorkflowBuilder(id, {
          nodes,
          edges,
          metadata: workflowMetadata
        })
      } else {
        const res = await intelligenceHubApi.createWorkflow({
          ...workflowMetadata,
          nodes,
          edges
        })
        message.success('New workflow created.')
        navigate(`/workflows/advanced-builder/${res.data.id}`)
        return
      }
      message.success('Workflow configuration saved.')
    } catch (e) {
      message.error('Failed to save.')
    } finally {
      setIsBuilderSaving(false)
    }
  }

  const selectedNode = nodes.find(n => n.id === selectedNodeId)

  if (id && isLoading) {
    return <div className="flex h-screen items-center justify-center"><Spin size="large" tip="Intelligently building workspace..." /></div>
  }

  return (
    <div className="flex h-screen flex-col bg-[#F1F5F9]">
      
      {/* ─── Top Area ─── */}
      <div className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm z-50">
        <div className="flex items-center gap-4">
          <Button icon={<ArrowLeft size={16}/>} onClick={() => navigate('/workflows/hub')} className="rounded-xl border-none bg-slate-50 hover:bg-slate-100" />
          <div className="flex flex-col">
            <Input 
              value={workflowMetadata.name} 
              onChange={(e) => setMetadata({...workflowMetadata, name: e.target.value})}
              className="border-none p-0 text-lg font-black tracking-tight focus:shadow-none bg-transparent" 
              placeholder="Enterprise Hiring Workflow"
            />
            <div className="flex items-center gap-2">
              <Text className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Advanced Business Stage Builder</Text>
              <Badge status="processing" text={<Text className="text-[9px] font-bold text-indigo-500 uppercase">v{workflowMetadata.version}</Text>} />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button icon={<Activity size={16}/>} className="rounded-xl font-bold uppercase text-[10px] tracking-widest bg-amber-50 text-amber-600 border-none">Preview</Button>
          <Button icon={<Copy size={16}/>} className="rounded-xl font-bold uppercase text-[10px] tracking-widest">Version History</Button>
          <Button icon={<Save size={16}/>} onClick={() => handleSave()} loading={isSaving} className="rounded-xl font-bold uppercase text-[10px] tracking-widest border-slate-200">Save Draft</Button>
          <Button type="primary" icon={<Check size={16}/>} className="h-10 rounded-xl font-black uppercase text-[10px] tracking-widest bg-indigo-600 border-none shadow-lg">Publish</Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        
        {/* ─── Canvas ─── */}
        <div 
          className="flex-1 relative overflow-hidden"
          ref={canvasRef}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => setSelectedNodeId(null)}
        >
          {/* Subtle Grid */}
          <div className="absolute inset-0 opacity-[0.05] pointer-events-none" style={{ backgroundImage: 'linear-gradient(#000 1px, transparent 0), linear-gradient(90deg, #000 1px, transparent 0)', backgroundSize: '40px 40px' }} />
          
          <div 
            className="absolute inset-0 p-20 transition-transform duration-200 origin-top-left"
            style={{ transform: `scale(${zoom})` }}
          >
            {nodes.map(node => (
              <StageBlock 
                key={node.id} 
                node={node} 
                isSelected={selectedNodeId === node.id}
                onSelect={() => setSelectedNodeId(node.id)}
                onDrag={(pos) => handleNodeDrag(node.id, pos)}
              />
            ))}
            
            {/* ─── Connections ─── */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
              <defs>
                <marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#CBD5E1" />
                </marker>
              </defs>
              {edges.map(edge => {
                const sourceNode = nodes.find(n => n.id === edge.source)
                const targetNode = nodes.find(n => n.id === edge.target)
                if (!sourceNode || !targetNode) return null
                
                const sX = sourceNode.position.x + 224 // stage width
                const sY = sourceNode.position.y + 40 // middle of header
                const tX = targetNode.position.x
                const tY = targetNode.position.y + 40
                
                const midX = (sX + tX) / 2
                
                return (
                  <path 
                    key={edge.id}
                    d={`M ${sX} ${sY} C ${midX} ${sY}, ${midX} ${tY}, ${tX} ${tY}`}
                    stroke="#CBD5E1"
                    strokeWidth="2"
                    fill="none"
                    markerEnd="url(#arrowhead)"
                  />
                )
              })}
            </svg>
          </div>

          {/* ─── Zoom Controls ─── */}
          <div className="absolute bottom-24 right-8 z-50 flex flex-col gap-2">
            <Button icon={<Plus size={16}/>} className="rounded-full h-10 w-10 shadow-lg" onClick={() => setZoom(Math.min(zoom + 0.1, 2))} />
            <Button icon={<Minimize size={16}/>} className="rounded-full h-10 w-10 shadow-lg" onClick={() => setZoom(Math.max(zoom - 0.1, 0.5))} />
            <Button icon={<Maximize size={16}/>} className="rounded-full h-10 w-10 shadow-lg" onClick={() => setZoom(1)} />
          </div>

          {/* ─── Bottom Add Stage Toolbar ─── */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-50">
            <div className="flex items-center gap-2 p-2 bg-white rounded-3xl border border-slate-200 shadow-2xl">
              <Text className="text-[9px] font-black uppercase text-slate-400 px-4">Add Stage:</Text>
              <div className="flex gap-1">
                {BUSINESS_BLOCKS.map(block => (
                  <Tooltip key={block.type} title={block.description}>
                    <button 
                      onClick={() => handleAddStage(block.type)}
                      className={cn(
                        "p-2 rounded-2xl hover:bg-slate-50 transition-colors flex flex-col items-center gap-1 min-w-[60px]",
                        `text-${block.color}-600`
                      )}
                    >
                      {block.icon}
                      <span className="text-[8px] font-black uppercase text-slate-500">{block.label}</span>
                    </button>
                  </Tooltip>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ─── Configuration Panel ─── */}
        <div className={cn(
          "w-96 border-l border-slate-200 bg-white transition-all duration-300 overflow-y-auto z-50",
          !selectedNodeId && "translate-x-full absolute right-0"
        )}>
          {selectedNode ? (
            <div className="p-8 space-y-8">
              <div className="flex items-center justify-between">
                <Space direction="vertical" size={0}>
                  <Text className="text-[10px] font-black uppercase tracking-widest text-slate-400">{selectedNode.type} Stage</Text>
                  <Title level={4} className="!m-0">Configure Stage</Title>
                </Space>
                <Button icon={<Trash2 size={16}/>} danger type="text" className="rounded-xl" onClick={() => {
                  setNodes(nodes.filter(n => n.id !== selectedNode.id))
                  setEdges(edges.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id))
                  setSelectedNodeId(null)
                }} />
              </div>

              <Collapse ghost defaultActiveKey={['general']} expandIconPosition="end">
                <Panel header={<Text strong className="uppercase text-[11px] tracking-wider text-slate-500">General</Text>} key="general">
                  <Form layout="vertical">
                    <Form.Item label="Stage Name">
                      <Input value={selectedNode.config.name} onChange={e => updateNodeConfig(selectedNode.id, { name: e.target.value })} className="rounded-xl" />
                    </Form.Item>
                    <Form.Item label="Description">
                      <Input.TextArea value={selectedNode.config.description} onChange={e => updateNodeConfig(selectedNode.id, { description: e.target.value })} className="rounded-xl" rows={3} />
                    </Form.Item>
                  </Form>
                </Panel>

                <Panel header={<Text strong className="uppercase text-[11px] tracking-wider text-slate-500">Rules & Logic</Text>} key="rules">
                  <Form layout="vertical">
                    <Form.Item label="Entry Condition">
                      <Select placeholder="Select trigger..." options={[{label: 'Always', value: 'always'}]} className="w-full" />
                    </Form.Item>
                    <Form.Item label="Exit Action">
                      <Select placeholder="Action on complete..." options={[{label: 'Move to Next', value: 'move_next'}]} className="w-full" />
                    </Form.Item>
                  </Form>
                </Panel>

                <Panel header={<Text strong className="uppercase text-[11px] tracking-wider text-slate-500">Assignments</Text>} key="assignments">
                  <Form layout="vertical">
                    <Form.Item label="Assign to">
                      <Select mode="multiple" placeholder="Select roles..." options={[{label: 'Recruiter', value: 'recruiter'}, {label: 'Hiring Manager', value: 'hm'}]} className="w-full" />
                    </Form.Item>
                  </Form>
                </Panel>

                <Panel header={<Text strong className="uppercase text-[11px] tracking-wider text-slate-500">Automation</Text>} key="automation">
                   <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Text className="text-xs">Auto-advance on success</Text>
                        <Switch size="small" defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Text className="text-xs">Require Manual Approval</Text>
                        <Switch size="small" />
                      </div>
                   </div>
                </Panel>

                <Panel header={<Text strong className="uppercase text-[11px] tracking-wider text-slate-500">SLA & Timeout</Text>} key="sla">
                  <Form layout="vertical">
                    <Form.Item label="Maximum Duration (Hours)">
                      <InputNumber min={1} className="w-full rounded-xl" />
                    </Form.Item>
                    <Form.Item label="Escalation Rule">
                      <Select options={[{label: 'Notify Manager', value: 'notify'}]} className="w-full" />
                    </Form.Item>
                  </Form>
                </Panel>
              </Collapse>

              {/* Decision Branching Specific */}
              {selectedNode.type === 'decision' && (
                <div className="p-6 bg-orange-50 rounded-3xl border border-orange-100">
                  <Title level={5} className="!mt-0">Branching Logic</Title>
                  <Text className="text-xs text-orange-700 block mb-4">Connect to multiple stages to create branches.</Text>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center bg-white p-3 rounded-2xl">
                      <Text className="text-xs font-bold">If Passed</Text>
                      <Select size="small" className="w-24" placeholder="Next..." />
                    </div>
                    <div className="flex justify-between items-center bg-white p-3 rounded-2xl">
                      <Text className="text-xs font-bold text-rose-600">If Failed</Text>
                      <Select size="small" className="w-24" placeholder="Reject..." />
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-8 flex flex-col gap-3">
                 <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                    <Text className="text-[10px] font-black uppercase text-slate-400 block mb-2">Connect Next Stage</Text>
                    <Select 
                      placeholder="Select target..."
                      className="w-full"
                      onChange={(v) => {
                        setEdges([...edges, { id: `edge_${Math.random()}`, source: selectedNode.id, target: v, condition: {} }])
                      }}
                    >
                      {nodes.filter(n => n.id !== selectedNode.id).map(n => (
                        <Select.Option key={n.id} value={n.id}>{n.config.name} ({n.id.slice(-4)})</Select.Option>
                      ))}
                    </Select>
                 </div>
                 <Button className="rounded-xl h-10 font-bold" onClick={() => setSelectedNodeId(null)}>Close Settings</Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-12">
              <div className="p-8 rounded-full bg-slate-50 mb-6">
                <Maximize size={48} className="text-slate-200" />
              </div>
              <Title level={4}>Select a Stage</Title>
              <Paragraph className="text-slate-400">Click any business block on the canvas to configure its rules, assignments, and automation.</Paragraph>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

function StageBlock({ node, isSelected, onSelect, onDrag }: any) {
  const meta = BUSINESS_BLOCKS.find(p => p.type === node.type) || BUSINESS_BLOCKS[0]
  
  return (
    <motion.div
      drag
      dragMomentum={false}
      onDrag={(e, info) => onDrag({ x: node.position.x + info.delta.x, y: node.position.y + info.delta.y })}
      onClick={(e) => { e.stopPropagation(); onSelect(); }}
      style={{ x: node.position.x, y: node.position.y, position: 'absolute' }}
      className={cn(
        "w-56 bg-white rounded-[2rem] border-2 shadow-sm cursor-move overflow-hidden transition-all z-10",
        isSelected ? "border-indigo-500 shadow-indigo-100 shadow-2xl scale-105" : "border-slate-100 hover:border-slate-300"
      )}
    >
      <div 
        className="h-1.5 w-full" 
        style={{ backgroundColor: COLORS[meta.color] }} 
      />
      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div 
            className="p-2.5 rounded-2xl"
            style={{ backgroundColor: `${COLORS[meta.color]}15`, color: COLORS[meta.color] }}
          >
            {meta.icon}
          </div>
          <Tag className="m-0 border-none bg-slate-50 text-slate-400 text-[8px] font-black uppercase px-2 rounded-full">
            {node.type}
          </Tag>
        </div>
        
        <Title level={5} className="!m-0 !text-[13px] !font-black !uppercase !tracking-tight truncate">
          {node.config.name}
        </Title>
        <Text className="text-[10px] text-slate-400 mt-1 block truncate">
          {node.config.description || 'Configure this stage...'}
        </Text>

        <div className="mt-4 flex items-center justify-between pt-4 border-t border-slate-50">
           <div className="flex -space-x-2">
              <div className="h-5 w-5 rounded-full bg-slate-100 border border-white" />
              <div className="h-5 w-5 rounded-full bg-slate-200 border border-white" />
           </div>
           <Badge status="success" />
        </div>
      </div>
    </motion.div>
  )
}
