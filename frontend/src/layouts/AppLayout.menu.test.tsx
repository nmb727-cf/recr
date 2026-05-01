import { describe, expect, it } from 'vitest'
import { getSystemMenuItems } from './AppLayout'

function flattenKeys(items: any[]): string[] {
  const out: string[] = []
  const walk = (nodes: any[]) => {
    for (const node of nodes || []) {
      if (typeof node?.key === 'string') out.push(node.key)
      if (Array.isArray(node?.children)) walk(node.children)
    }
  }
  walk(items)
  return out
}

describe('AppLayout menu policy', () => {
  it('keeps full company menu visibility for tenant admins', () => {
    const items = getSystemMenuItems({
      role: 'tenant_admin',
      permissions: [],
      is_super_admin: false,
      is_superuser: false,
      is_staff: false,
    } as any)
    const keys = flattenKeys(items)
    expect(keys).toContain('/workflows/advanced-builder')
    expect(keys).toContain('/intelligence/learning')
  })

  it('keeps candidate menu restricted to candidate workspace routes', () => {
    const items = getSystemMenuItems({
      role: 'candidate',
      permissions: [],
    } as any)
    const keys = flattenKeys(items)
    expect(keys).toContain('/candidate/dashboard')
    expect(keys).toContain('/candidate/interviews')
    expect(keys).toContain('/candidate/applications')
    expect(keys).toContain('/passport')
    expect(keys).not.toContain('/candidate/jobs')
    expect(keys).not.toContain('/jobs')
    expect(keys).not.toContain('/settings')
    expect(keys).not.toContain('/integrations')
  })
})
