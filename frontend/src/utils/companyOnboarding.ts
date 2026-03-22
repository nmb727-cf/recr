export const COMPANY_SIGNUP_PREFILL_KEY = 'company_signup_prefill'
export const AGENCY_SIGNUP_PREFILL_KEY = 'agency_signup_prefill'
export const KNOWN_AGENCIES_KEY = 'known_agencies_phase1'

export interface CompanySignupPrefill {
  name?: string
  company_name?: string
  email?: string
  country_code?: string
}

export interface AgencySignupPrefill {
  name?: string
  agency_name?: string
  email?: string
  country_code?: string
}

export interface KnownAgency {
  agency_tenant_id: string
  name: string
  email?: string
}

export function cacheCompanySignupPrefill(data: CompanySignupPrefill) {
  try {
    localStorage.setItem(COMPANY_SIGNUP_PREFILL_KEY, JSON.stringify(data))
  } catch {
    // ignore localStorage failures
  }
}

export function readCompanySignupPrefill(): CompanySignupPrefill | null {
  try {
    const raw = localStorage.getItem(COMPANY_SIGNUP_PREFILL_KEY)
    if (!raw) return null
    return JSON.parse(raw) as CompanySignupPrefill
  } catch {
    return null
  }
}

export function cacheAgencySignupPrefill(data: AgencySignupPrefill) {
  try {
    localStorage.setItem(AGENCY_SIGNUP_PREFILL_KEY, JSON.stringify(data))
  } catch {
    // ignore localStorage failures
  }
}

export function readAgencySignupPrefill(): AgencySignupPrefill | null {
  try {
    const raw = localStorage.getItem(AGENCY_SIGNUP_PREFILL_KEY)
    if (!raw) return null
    return JSON.parse(raw) as AgencySignupPrefill
  } catch {
    return null
  }
}

export function clearCompanySignupPrefill() {
  try {
    localStorage.removeItem(COMPANY_SIGNUP_PREFILL_KEY)
  } catch {
    // ignore localStorage failures
  }
}

export function clearAgencySignupPrefill() {
  try {
    localStorage.removeItem(AGENCY_SIGNUP_PREFILL_KEY)
  } catch {
    // ignore localStorage failures
  }
}

export function cacheKnownAgency(data: KnownAgency) {
  if (!data?.agency_tenant_id || !data?.name) return
  try {
    const current = readKnownAgencies()
    const byId = new Map(current.map((a) => [a.agency_tenant_id, a]))
    byId.set(data.agency_tenant_id, {
      agency_tenant_id: data.agency_tenant_id,
      name: data.name,
      email: data.email,
    })
    localStorage.setItem(KNOWN_AGENCIES_KEY, JSON.stringify(Array.from(byId.values())))
  } catch {
    // ignore localStorage failures
  }
}

export function readKnownAgencies(): KnownAgency[] {
  try {
    const raw = localStorage.getItem(KNOWN_AGENCIES_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as KnownAgency[]) : []
  } catch {
    return []
  }
}

export function isOrganisationSetupIncomplete(org: any): boolean {
  if (!org) return true

  const name = String(org.name || '').trim()
  if (!name) return true

  const lowered = name.toLowerCase()
  // Only reject exactly the default placeholder
  if (lowered === 'my organisation') return true

  // Phase 1 requires basic org identity and region to be set.
  // We check for presence of these essential fields.
  const hasCountry = !!String(org.country_code || '').trim()
  const hasIndustry = !!String(org.industry || '').trim()
  const hasTimezone = !!String(org.timezone || '').trim()

  return !(hasCountry && hasIndustry && hasTimezone)
}
