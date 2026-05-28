import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Input, Tag, Typography, Form, Modal, message, Select,
} from 'antd'
import {
  Search, Plus, RefreshCw, FileText, ChevronRight, ExternalLink,
} from 'lucide-react'
import type { ColumnsType } from 'antd/es/table'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useQueryClient } from '@tanstack/react-query'
import { prequalificationApi } from '@/api/prequalification'
import { cn } from '@/utils/cn'

const { Text } = Typography

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PrequalificationList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data, isLoading, refetch } = useApiQuery(
    ['prequal-forms-list'],
    () => prequalificationApi.listForms()
  )
  const forms: any[] = (data as any)?.forms ?? []

  const filteredForms = forms.filter((f: any) => {
    const matchesSearch = f.name.toLowerCase().includes(search.toLowerCase())
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && f.is_active) ||
      (statusFilter === 'inactive' && !f.is_active)
    return matchesSearch && matchesStatus
  })

  const handleCreate = async (values: any) => {
    setSubmitting(true)
    try {
      const res = await prequalificationApi.createForm(values)
      const newForm = (res as any)?.data?.form ?? (res as any)?.form
      message.success('Pre-qualification form created')
      queryClient.invalidateQueries({ queryKey: ['prequal-forms-list'] })
      setCreateModalOpen(false)
      form.resetFields()
      // Navigate directly to the builder
      if (newForm?.id) {
        navigate(`/interviews/prequalification/forms/${newForm.id}/builder`)
      }
    } catch {
      message.error('Failed to create form')
    } finally {
      setSubmitting(false)
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'Form Name',
      dataIndex: 'name',
      key: 'name',
      render: (name) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
            <FileText size={16} />
          </div>
          <Text className="font-bold text-slate-900">{name}</Text>
        </div>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      render: (d) => <Text className="text-slate-400 text-xs">{d || '—'}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      width: 120,
      render: (active) => (
        <Tag
          color={active ? 'success' : 'default'}
          className="m-0 border-none uppercase font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full"
        >
          {active ? 'Published' : 'Draft'}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created',
      width: 120,
      render: (d) => <Text className="text-slate-400 text-xs font-medium">{new Date(d).toLocaleDateString()}</Text>,
    },
    {
      title: '',
      key: 'action',
      width: 80,
      align: 'right' as const,
      render: (_, record) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            navigate(`/interviews/prequalification/forms/${record.id}/builder`)
          }}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-500 text-[10px] font-black uppercase tracking-widest hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all"
        >
          <ExternalLink size={11} /> Open
        </button>
      ),
    },
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-96px)] bg-[#F8FAFC] -m-4 overflow-hidden">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex h-14 flex-none items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm shadow-blue-100">
            <FileText size={18} />
          </div>
          <h1 className="text-base font-black text-slate-900 tracking-tight leading-none uppercase">
            Pre-Qualification Forms
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 transition-all"
          >
            <RefreshCw size={13} className={cn(isLoading && 'animate-spin')} />
          </button>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white hover:bg-blue-700 shadow-sm shadow-blue-100 active:scale-95 transition-all"
          >
            <Plus size={14} /> New Form
          </button>
        </div>
      </div>

      {/* ── Content ────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
          {/* Toolbar */}
          <div className="p-4 border-b border-slate-100 bg-slate-50/30 flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 focus-within:border-blue-300 transition-all max-w-sm flex-1">
                <Search size={14} className="text-slate-400 shrink-0" />
                <input
                  placeholder="Search forms..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-transparent text-[11px] font-bold text-slate-700 outline-none placeholder-slate-400 uppercase tracking-widest w-full"
                />
              </div>
              <Select
                value={statusFilter}
                onChange={(v) => setStatusFilter(v)}
                size="small"
                className="w-28"
                options={[
                  { value: 'all',      label: 'All Status' },
                  { value: 'active',   label: 'Published'  },
                  { value: 'inactive', label: 'Draft'      },
                ]}
              />
            </div>
            <Text className="text-[10px] font-black text-slate-400 uppercase tracking-widest shrink-0">
              {filteredForms.length} Forms
            </Text>
          </div>

          {/* Table */}
          <div className="flex-1 overflow-y-auto p-4">
            <Table
              columns={columns}
              dataSource={filteredForms}
              rowKey="id"
              loading={isLoading}
              pagination={{ pageSize: 15, hideOnSinglePage: true }}
              className="enterprise-table"
              locale={{
                emptyText: (
                  <div className="py-16 text-center">
                    <FileText className="h-10 w-10 text-slate-200 mx-auto mb-3" />
                    <Text className="text-slate-400 font-bold block">No forms yet</Text>
                    <Text className="text-slate-300 text-xs block mt-1">
                      Create your first pre-qualification form to get started
                    </Text>
                  </div>
                ),
              }}
              onRow={(record) => ({
                onClick: () => navigate(`/interviews/prequalification/forms/${record.id}/builder`),
                className: 'cursor-pointer',
              })}
            />
          </div>
        </div>
      </div>

      {/* ── Create Form Modal ───────────────────────────────────────────────── */}
      <Modal
        title={<span className="font-black text-slate-900 uppercase tracking-tight">Create Pre-Qualification Form</span>}
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        okText="Create & Open Builder"
        confirmLoading={submitting}
        destroyOnHidden
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} className="mt-6">
          <Form.Item name="name" label="Form Name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input placeholder="e.g. Engineering Candidate Screener" className="h-10 rounded-xl" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea
              rows={3}
              placeholder="What is this pre-qualification form used for?"
              className="rounded-xl"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
