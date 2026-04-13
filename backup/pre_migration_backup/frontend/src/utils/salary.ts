// Salary display config per country/currency
export interface SalaryConfig {
  unit: string        // 'LPA' | 'K/yr' | '/month' | '/yr'
  symbol: string      // '$' | '£' | '₹' | 'AED' etc
  divideBy?: number   // divide stored value for display
  // e.g. INR stored as full number, displayed as LPA
  placeholder: string
  example: string
}

const SALARY_CONFIG: Record<string, SalaryConfig> = {
  IN: {
    unit: 'LPA',
    symbol: '₹',
    placeholder: '18',
    example: '18 LPA'
  },
  US: {
    unit: 'K/yr',
    symbol: '$',
    placeholder: '120',
    example: '$120K/yr'
  },
  GB: {
    unit: 'K/yr',
    symbol: '£',
    placeholder: '55',
    example: '£55K/yr'
  },
  AE: {
    unit: '/month',
    symbol: 'AED',
    placeholder: '15000',
    example: 'AED 15,000/mo'
  },
  AU: {
    unit: 'K/yr',
    symbol: 'A$',
    placeholder: '95',
    example: 'A$95K/yr'
  },
  SG: {
    unit: 'K/yr',
    symbol: 'SGD',
    placeholder: '80',
    example: 'SGD 80K/yr'
  },
  CA: {
    unit: 'K/yr',
    symbol: 'CA$',
    placeholder: '85',
    example: 'CA$85K/yr'
  },
  DE: {
    unit: '/yr',
    symbol: '€',
    placeholder: '65000',
    example: '€65,000/yr'
  },
  FR: {
    unit: '/yr',
    symbol: '€',
    placeholder: '50000',
    example: '€50,000/yr'
  },
  NL: {
    unit: '/yr',
    symbol: '€',
    placeholder: '60000',
    example: '€60,000/yr'
  },
}

const DEFAULT_CONFIG: SalaryConfig = {
  unit: '/yr',
  symbol: '',
  placeholder: '50000',
  example: '50,000/yr'
}

export function getSalaryConfig(countryCode: string): SalaryConfig {
  return SALARY_CONFIG[countryCode?.toUpperCase()] ?? DEFAULT_CONFIG
}

export function formatSalaryLabel(
  config: SalaryConfig,
  fieldLabel: string
): string {
  return `${fieldLabel} (${config.symbol}${config.unit})`
}

export function formatSalaryDisplay(
  value: number | null | undefined,
  config: SalaryConfig
): string {
  if (!value) return '—'
  return `${config.symbol}${value.toLocaleString()} ${config.unit}`
}
