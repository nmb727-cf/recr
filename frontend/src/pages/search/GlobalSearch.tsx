import { useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, Empty, Input, List, Spin, Tag, Typography } from 'antd'
import { SearchOutlined } from '@ant-design/icons'

import { useApiQuery } from '@/hooks/useApiQuery'
import { organisationApi } from '@/api/organisation'

const { Title, Text } = Typography

export default function GlobalSearch() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const query = (params.get('q') || '').trim()

  const { data, isLoading } = useApiQuery(
    ['global-search', query],
    () => organisationApi.globalSearch({ q: query, limit: 6 }),
    { enabled: query.length > 0 }
  )

  const payload = (data || {}) as {
    candidates?: Array<{ id: string; name: string; email?: string; current_title?: string; current_company?: string }>
    jobs?: Array<{ id: string; title: string; status?: string; job_ref_id?: string; work_mode?: string }>
    agencies?: Array<{ id: string; name: string; status?: string; contact_email?: string }>
  }
  const candidates = payload.candidates || []
  const jobs = payload.jobs || []
  const agencies = payload.agencies || []

  const total = useMemo(() => candidates.length + jobs.length + agencies.length, [candidates, jobs, agencies])

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Title level={3} className="!mb-1">Global Search</Title>
          <Text type="secondary">Search candidates, jobs, and agencies within your allowed scope.</Text>
        </div>
      </div>

      <Card>
        <Input
          size="large"
          allowClear
          prefix={<SearchOutlined />}
          placeholder="Search candidates, jobs, agencies..."
          value={query}
          onChange={(e) => {
            const next = e.target.value
            setParams(next ? { q: next } : {})
          }}
        />
      </Card>

      {isLoading ? (
        <div className="py-10 text-center"><Spin /></div>
      ) : !query ? (
        <Card><Empty description="Type to search across candidates, jobs, and agencies." /></Card>
      ) : total === 0 ? (
        <Card><Empty description="No results found. Try a shorter or broader keyword." /></Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card title={`Candidates (${candidates.length})`}>
            <List
              size="small"
              dataSource={candidates}
              locale={{ emptyText: 'No candidates' }}
              renderItem={(item) => (
                <List.Item className="cursor-pointer" onClick={() => navigate('/candidates')}>
                  <div className="min-w-0">
                    <div className="truncate font-semibold">{item.name || 'Unnamed Candidate'}</div>
                    <div className="truncate text-xs text-slate-500">{item.current_title || item.email || '—'}</div>
                  </div>
                </List.Item>
              )}
            />
          </Card>

          <Card title={`Jobs (${jobs.length})`}>
            <List
              size="small"
              dataSource={jobs}
              locale={{ emptyText: 'No jobs' }}
              renderItem={(item) => (
                <List.Item className="cursor-pointer" onClick={() => navigate(`/jobs?id=${item.id}`)}>
                  <div className="min-w-0">
                    <div className="truncate font-semibold">{item.title}</div>
                    <div className="mt-1 flex items-center gap-1">
                      {item.status ? <Tag className="m-0">{item.status}</Tag> : null}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>

          <Card title={`Agencies (${agencies.length})`}>
            <List
              size="small"
              dataSource={agencies}
              locale={{ emptyText: 'No agencies' }}
              renderItem={(item) => (
                <List.Item className="cursor-pointer" onClick={() => navigate('/agencies')}>
                  <div className="min-w-0">
                    <div className="truncate font-semibold">{item.name}</div>
                    <div className="truncate text-xs text-slate-500">{item.contact_email || '—'}</div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </div>
      )}
    </div>
  )
}
