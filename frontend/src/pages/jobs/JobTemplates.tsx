import { useState } from 'react'
import {
  Button, Input, Select, Table, Tag, Modal, Form, Tooltip,
  message, Popconfirm, Empty, Drawer, Space, Badge,
} from 'antd'
import {
  Plus, Search, Copy, Trash2, Edit3, BookOpen, FileText,
  CheckCircle, ChevronRight, Layers,
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jdTemplatesApi } from '@/api/jobs'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

// ─── Types ────────────────────────────────────────────────────────────────────

interface JDTemplate {
  id: string
  name: string
  category: string
  job_type: string
  description: string
  requirements: string
  responsibilities: string
  skills_suggested: string[]
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// ─── API (thin wrappers over jdTemplatesApi for local use) ────────────────────

const templatesApi = {
  list: (params?: Record<string, string>) =>
    jdTemplatesApi.list(params).then((r: any) => r.data ?? r),
  create: (data: Partial<JDTemplate>) =>
    jdTemplatesApi.create(data).then((r: any) => r.data ?? r),
  update: (id: string, data: Partial<JDTemplate>) =>
    jdTemplatesApi.update(id, data).then((r: any) => r.data ?? r),
  delete: (id: string) =>
    jdTemplatesApi.delete(id).then((r: any) => r.data ?? r),
  duplicate: (id: string) =>
    jdTemplatesApi.duplicate(id).then((r: any) => r.data ?? r),
}

// ─── Constants ────────────────────────────────────────────────────────────────

const CATEGORIES = [
  { value: 'engineering', label: 'Engineering' },
  { value: 'product', label: 'Product' },
  { value: 'design', label: 'Design' },
  { value: 'sales', label: 'Sales' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'operations', label: 'Operations' },
  { value: 'finance', label: 'Finance' },
  { value: 'hr', label: 'HR' },
  { value: 'legal', label: 'Legal' },
  { value: 'other', label: 'Other' },
]

const CATEGORY_COLORS: Record<string, string> = {
  engineering: 'blue',
  product: 'purple',
  design: 'magenta',
  sales: 'green',
  marketing: 'orange',
  operations: 'cyan',
  finance: 'gold',
  hr: 'geekblue',
  legal: 'volcano',
  other: 'default',
}

const JOB_TYPES = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'freelance', label: 'Freelance' },
]

// ─── Template Form Drawer ─────────────────────────────────────────────────────

function TemplateFormDrawer({
  open,
  template,
  onClose,
  onSaved,
}: {
  open: boolean
  template: JDTemplate | null
  onClose: () => void
  onSaved: () => void
}) {
  const [form] = Form.useForm()
  const isEdit = !!template

  const createMut = useMutation({
    mutationFn: (data: Partial<JDTemplate>) => templatesApi.create(data),
    onSuccess: () => { message.success('Template created'); onSaved(); onClose() },
    onError: () => message.error('Failed to save template'),
  })

  const updateMut = useMutation({
    mutationFn: (data: Partial<JDTemplate>) => templatesApi.update(template!.id, data),
    onSuccess: () => { message.success('Template updated'); onSaved(); onClose() },
    onError: () => message.error('Failed to update template'),
  })

  const handleSave = () => {
    form.validateFields().then((vals) => {
      const payload = {
        ...vals,
        skills_suggested: vals.skills_suggested
          ? vals.skills_suggested.split(',').map((s: string) => s.trim()).filter(Boolean)
          : [],
      }
      isEdit ? updateMut.mutate(payload) : createMut.mutate(payload)
    })
  }

  const loading = createMut.isPending || updateMut.isPending

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-indigo-600" />
          <span className="font-semibold">{isEdit ? 'Edit Template' : 'New JD Template'}</span>
        </div>
      }
      width={720}
      footer={
        <div className="flex justify-end gap-3">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" loading={loading} onClick={handleSave}
            className="bg-indigo-600 border-none">
            {isEdit ? 'Save Changes' : 'Create Template'}
          </Button>
        </div>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={template ? {
          ...template,
          skills_suggested: (template.skills_suggested || []).join(', '),
        } : { is_active: true, job_type: '', category: 'other' }}
        className="space-y-1"
      >
        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="name" label="Template Name" rules={[{ required: true }]} className="col-span-2">
            <Input placeholder="e.g. Senior Software Engineer — Backend" size="large" />
          </Form.Item>

          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select size="large" options={CATEGORIES} placeholder="Select category" />
          </Form.Item>

          <Form.Item name="job_type" label="Job Type">
            <Select size="large" options={[{ value: '', label: 'Any' }, ...JOB_TYPES]} placeholder="Any" />
          </Form.Item>
        </div>

        <Form.Item name="description" label="Job Description">
          <Input.TextArea
            rows={5}
            placeholder="Write the job description. This will pre-fill the Description field when applied to a job."
          />
        </Form.Item>

        <Form.Item name="requirements" label="Requirements">
          <Input.TextArea
            rows={4}
            placeholder="List the key requirements (education, certifications, must-haves)."
          />
        </Form.Item>

        <Form.Item name="responsibilities" label="Responsibilities">
          <Input.TextArea
            rows={4}
            placeholder="Describe the day-to-day responsibilities of this role."
          />
        </Form.Item>

        <Form.Item
          name="skills_suggested"
          label="Suggested Skills"
          extra="Comma-separated list of skills. e.g. Python, Django, PostgreSQL"
        >
          <Input placeholder="Python, Django, REST APIs, PostgreSQL" />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

// ─── Preview Drawer ───────────────────────────────────────────────────────────

function TemplatePreviewDrawer({
  template,
  onClose,
  onEdit,
  onDuplicate,
}: {
  template: JDTemplate | null
  onClose: () => void
  onEdit: () => void
  onDuplicate: () => void
}) {
  if (!template) return null

  return (
    <Drawer
      open={!!template}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-indigo-600" />
          <span className="font-semibold truncate">{template.name}</span>
        </div>
      }
      width={680}
      extra={
        <Space>
          <Button icon={<Copy size={14} />} onClick={onDuplicate}>Duplicate</Button>
          <Button type="primary" icon={<Edit3 size={14} />} onClick={onEdit}
            className="bg-indigo-600 border-none">Edit</Button>
        </Space>
      }
    >
      <div className="space-y-6">
        {/* Meta */}
        <div className="flex flex-wrap gap-2">
          <Tag color={CATEGORY_COLORS[template.category] || 'default'}>
            {CATEGORIES.find(c => c.value === template.category)?.label || template.category}
          </Tag>
          {template.job_type && (
            <Tag color="default">
              {JOB_TYPES.find(j => j.value === template.job_type)?.label || template.job_type}
            </Tag>
          )}
          <Tag color="green" icon={<CheckCircle size={10} className="inline mr-1" />}>
            Used {template.usage_count}×
          </Tag>
          <span className="text-xs text-slate-400 ml-auto self-center">
            Updated {dayjs(template.updated_at).fromNow()}
          </span>
        </div>

        {/* Description */}
        {template.description && (
          <div>
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Description</h4>
            <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{template.description}</p>
          </div>
        )}

        {/* Responsibilities */}
        {template.responsibilities && (
          <div>
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Responsibilities</h4>
            <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{template.responsibilities}</p>
          </div>
        )}

        {/* Requirements */}
        {template.requirements && (
          <div>
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Requirements</h4>
            <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{template.requirements}</p>
          </div>
        )}

        {/* Skills */}
        {template.skills_suggested?.length > 0 && (
          <div>
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Suggested Skills</h4>
            <div className="flex flex-wrap gap-2">
              {template.skills_suggested.map((s) => (
                <Tag key={s} className="rounded-full px-3">{s}</Tag>
              ))}
            </div>
          </div>
        )}
      </div>
    </Drawer>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function JobTemplates() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<JDTemplate | null>(null)
  const [previewTarget, setPreviewTarget] = useState<JDTemplate | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['jd-templates', search, categoryFilter],
    queryFn: () => templatesApi.list({
      ...(search ? { search } : {}),
      ...(categoryFilter ? { category: categoryFilter } : {}),
      active_only: 'false',
    }),
  })

  const templates: JDTemplate[] = (data as any)?.templates || (data as any)?.data?.templates || []

  const deleteMut = useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => { message.success('Template deleted'); qc.invalidateQueries({ queryKey: ['jd-templates'] }) },
    onError: () => message.error('Failed to delete'),
  })

  const duplicateMut = useMutation({
    mutationFn: (id: string) => templatesApi.duplicate(id),
    onSuccess: () => { message.success('Template duplicated'); qc.invalidateQueries({ queryKey: ['jd-templates'] }) },
    onError: () => message.error('Failed to duplicate'),
  })

  const handleEdit = (t: JDTemplate) => {
    setEditTarget(t)
    setPreviewTarget(null)
    setFormOpen(true)
  }

  const handleNew = () => {
    setEditTarget(null)
    setFormOpen(true)
  }

  const handleFormClose = () => {
    setFormOpen(false)
    setEditTarget(null)
  }

  const handleSaved = () => {
    qc.invalidateQueries({ queryKey: ['jd-templates'] })
  }

  const columns: ColumnsType<JDTemplate> = [
    {
      title: 'Template Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, row: JDTemplate) => (
        <button
          className="text-left group"
          onClick={() => setPreviewTarget(row)}
        >
          <div className="font-medium text-slate-800 group-hover:text-indigo-600 transition-colors flex items-center gap-1.5">
            {name}
            <ChevronRight size={12} className="opacity-0 group-hover:opacity-100 text-indigo-500 transition-opacity" />
          </div>
          {row.skills_suggested?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {row.skills_suggested.slice(0, 3).map((s) => (
                <span key={s} className="text-[10px] bg-slate-100 text-slate-500 rounded px-1.5 py-0.5">{s}</span>
              ))}
              {row.skills_suggested.length > 3 && (
                <span className="text-[10px] text-slate-400">+{row.skills_suggested.length - 3} more</span>
              )}
            </div>
          )}
        </button>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 140,
      render: (cat: string) => (
        <Tag color={CATEGORY_COLORS[cat] || 'default'} className="rounded-full">
          {CATEGORIES.find(c => c.value === cat)?.label || cat}
        </Tag>
      ),
    },
    {
      title: 'Job Type',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 130,
      render: (jt: string) => jt
        ? <Tag>{JOB_TYPES.find(j => j.value === jt)?.label || jt}</Tag>
        : <span className="text-slate-300 text-xs">Any</span>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active: boolean) => (
        <Badge
          status={active ? 'success' : 'default'}
          text={<span className="text-xs">{active ? 'Active' : 'Inactive'}</span>}
        />
      ),
    },
    {
      title: 'Used',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 80,
      align: 'center',
      render: (count: number) => (
        <span className={`text-sm font-semibold ${count > 0 ? 'text-indigo-600' : 'text-slate-300'}`}>
          {count}×
        </span>
      ),
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
      render: (d: string) => (
        <span className="text-xs text-slate-400">{dayjs(d).format('DD MMM YYYY')}</span>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 120,
      render: (_: any, row: JDTemplate) => (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Tooltip title="Edit">
            <Button
              type="text" size="small"
              icon={<Edit3 size={13} />}
              onClick={(e) => { e.stopPropagation(); handleEdit(row) }}
            />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button
              type="text" size="small"
              icon={<Copy size={13} />}
              onClick={(e) => { e.stopPropagation(); duplicateMut.mutate(row.id) }}
              loading={duplicateMut.isPending}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Popconfirm
              title="Delete this template?"
              okText="Delete" okButtonProps={{ danger: true }}
              onConfirm={() => deleteMut.mutate(row.id)}
            >
              <Button
                type="text" size="small" danger
                icon={<Trash2 size={13} />}
                onClick={(e) => e.stopPropagation()}
              />
            </Popconfirm>
          </Tooltip>
        </div>
      ),
    },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="bg-white border-b border-slate-200 px-8 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm">
              <Layers size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">JD Template Library</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Reusable job description templates to accelerate job creation
              </p>
            </div>
          </div>
          <Button
            type="primary"
            icon={<Plus size={16} />}
            size="large"
            onClick={handleNew}
            className="rounded-xl h-10 bg-indigo-600 border-none font-semibold shadow-sm"
          >
            New Template
          </Button>
        </div>
      </div>

      {/* ── Filters ────────────────────────────────────────────────────────── */}
      <div className="px-8 py-4 bg-white border-b border-slate-100 flex items-center gap-3 flex-wrap">
        <Input
          prefix={<Search size={14} className="text-slate-400" />}
          placeholder="Search templates…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-60 rounded-lg"
          allowClear
        />
        <Select
          placeholder="All categories"
          value={categoryFilter || undefined}
          onChange={(v) => setCategoryFilter(v || '')}
          allowClear
          style={{ width: 180 }}
          options={CATEGORIES}
          className="rounded-lg"
        />
        <span className="text-xs text-slate-400 ml-auto">
          {templates.length} template{templates.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      <div className="px-8 py-6">
        {templates.length === 0 && !isLoading ? (
          <div className="bg-white rounded-2xl border border-slate-200 flex flex-col items-center justify-center py-20">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center mb-4">
              <BookOpen size={26} className="text-indigo-400" />
            </div>
            <p className="text-slate-800 font-semibold text-lg mb-1">No templates yet</p>
            <p className="text-slate-400 text-sm mb-6">
              Create reusable job description templates to speed up your hiring.
            </p>
            <Button
              type="primary"
              icon={<Plus size={14} />}
              onClick={handleNew}
              className="bg-indigo-600 border-none rounded-xl"
            >
              Create First Template
            </Button>
          </div>
        ) : (
          <Table
            dataSource={templates}
            columns={columns}
            rowKey="id"
            loading={isLoading}
            pagination={{ pageSize: 20, hideOnSinglePage: true, size: 'small' }}
            rowClassName="group cursor-pointer"
            onRow={(row) => ({ onClick: () => setPreviewTarget(row) })}
            className="bg-white rounded-2xl border border-slate-200 overflow-hidden"
            size="middle"
          />
        )}
      </div>

      {/* ── Drawers ────────────────────────────────────────────────────────── */}
      <TemplateFormDrawer
        open={formOpen}
        template={editTarget}
        onClose={handleFormClose}
        onSaved={handleSaved}
      />

      <TemplatePreviewDrawer
        template={previewTarget}
        onClose={() => setPreviewTarget(null)}
        onEdit={() => handleEdit(previewTarget!)}
        onDuplicate={() => { duplicateMut.mutate(previewTarget!.id); setPreviewTarget(null) }}
      />
    </div>
  )
}
