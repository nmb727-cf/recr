import { useState } from 'react'
import { Checkbox, Input, InputNumber, Select, Button, Space } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'

const { Option } = Select

export const STANDARD_PAYMENT_TERMS = [
  { value: 'full_on_joining', label: 'Full payment on joining date' },
  { value: 'full_after_3months', label: 'Full payment after 3 months retention' },
  { value: 'full_after_6months', label: 'Full payment after 6 months retention' },
  { value: 'split_25_75', label: '25% on joining + 75% after 3 months' },
  { value: 'split_50_50', label: '50% on joining + 50% after 3 months' },
  { value: 'custom', label: 'Custom structured terms' },
]

interface ScheduleItem {
  trigger: 'on_joining' | 'days_after_joining'
  days?: number
  percentage: number
  description?: string
}

interface PaymentTermsFieldProps {
  value?: { terms: string[], schedule: ScheduleItem[] }
  onChange?: (val: { terms: string[], schedule: ScheduleItem[] }) => void
}

export default function PaymentTermsField({ value, onChange }: PaymentTermsFieldProps) {
  const terms = value?.terms || []
  const schedule = value?.schedule || []
  const showCustom = terms.includes('custom')

  const handleTermsChange = (checked: any) => {
    // antd Checkbox.Group returns string[]
    const termsArray = checked as string[]
    onChange?.({ terms: termsArray, schedule: termsArray.includes('custom') ? schedule : [] })
  }

  const addScheduleItem = () => {
    const newItem: ScheduleItem = { trigger: 'on_joining', percentage: 50 }
    onChange?.({ terms, schedule: [...schedule, newItem] })
  }

  const updateScheduleItem = (index: number, field: string, val: any) => {
    const updated = schedule.map((item, i) =>
      i === index ? { ...item, [field]: val } : item
    )
    onChange?.({ terms, schedule: updated as ScheduleItem[] })
  }

  const removeScheduleItem = (index: number) => {
    onChange?.({ terms, schedule: schedule.filter((_, i) => i !== index) })
  }

  const totalPercentage = schedule.reduce((sum, item) => sum + (item.percentage || 0), 0)

  return (
    <div className="space-y-3">
      <Checkbox.Group
        value={terms}
        onChange={handleTermsChange}
        className="flex flex-col gap-2"
      >
        {STANDARD_PAYMENT_TERMS.map(opt => (
          <Checkbox key={opt.value} value={opt.value}>
            <span className="text-[13px]">{opt.label}</span>
          </Checkbox>
        ))}
      </Checkbox.Group>

      {showCustom && (
        <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-3">
            Custom Payment Schedule
          </div>

          {schedule.map((item, index) => (
            <div key={index} className="flex items-center gap-2 mb-3 p-3 bg-white rounded-lg border border-slate-100">
              <InputNumber
                min={1}
                max={100}
                value={item.percentage}
                onChange={val => updateScheduleItem(index, 'percentage', val)}
                addonAfter="%"
                className="w-28"
              />
              <Select
                value={item.trigger}
                onChange={val => updateScheduleItem(index, 'trigger', val)}
                className="w-44"
              >
                <Option value="on_joining">On joining date</Option>
                <Option value="days_after_joining">Days after joining</Option>
              </Select>
              {item.trigger === 'days_after_joining' && (
                <InputNumber
                  min={1}
                  value={item.days}
                  onChange={val => updateScheduleItem(index, 'days', val)}
                  addonAfter="days"
                  className="w-32"
                  placeholder="90"
                />
              )}
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeScheduleItem(index)}
                size="small"
              />
            </div>
          ))}

          {totalPercentage > 0 && (
            <div className={`text-[12px] font-medium mb-2 ${totalPercentage === 100 ? 'text-green-600' : 'text-amber-600'}`}>
              Total: {totalPercentage}% {totalPercentage !== 100 ? '(must equal 100%)' : '✓'}
            </div>
          )}

          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={addScheduleItem}
            size="small"
            className="w-full"
          >
            Add Payment Milestone
          </Button>
        </div>
      )}
    </div>
  )
}
