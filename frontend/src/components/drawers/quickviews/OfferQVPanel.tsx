import { Button, Tag, Descriptions, Typography } from 'antd'
import { Gift } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

const { Text } = Typography

export default function OfferQVPanel({ data }: { data: any }) {
  const role = useAuthStore(s => s.user?.role)
  const isCandidate = role === 'candidate'

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 rounded-2xl bg-gold-50 bg-amber-50 text-amber-600 flex items-center justify-center mb-4 shadow-sm border border-amber-100">
          <Gift className="h-8 w-8" />
        </div>
        <Tag color={data?.status === 'accepted' ? 'success' : data?.status === 'rejected' ? 'error' : 'processing'}
          className="m-0 border-none uppercase font-bold text-[10px] tracking-widest px-3 py-0.5 rounded-full mb-2">
          {data?.status || 'Pending'}
        </Tag>
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{data?.job_title || 'Offer Letter'}</h2>
      </div>

      <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
        <Descriptions column={1} size="small" labelStyle={{ color: '#8c8c8c', width: 120 }}>
          {data?.salary && <Descriptions.Item label="Offered Salary"><Text strong>{data.salary}</Text></Descriptions.Item>}
          {data?.joining_date && <Descriptions.Item label="Joining Date"><Text>{data.joining_date}</Text></Descriptions.Item>}
        </Descriptions>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {isCandidate ? (
          <>
            <Button block className="h-11 rounded-xl font-bold" danger>Decline</Button>
            <Button type="primary" block className="h-11 rounded-xl font-bold bg-emerald-600 border-none">Accept Offer</Button>
          </>
        ) : (
          <>
            <Button block className="h-11 rounded-xl font-bold" danger>Revoke</Button>
            <Button type="primary" block className="h-11 rounded-xl font-bold bg-blue-600 border-none">Send to Candidate</Button>
          </>
        )}
      </div>
    </div>
  )
}
