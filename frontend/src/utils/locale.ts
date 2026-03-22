// Phase 1 Localisation Foundations

export const COUNTRIES = [
  { code: 'IN', name: 'India', currency: 'INR', phoneCode: '+91' },
  { code: 'US', name: 'United States', currency: 'USD', phoneCode: '+1' },
  { code: 'GB', name: 'United Kingdom', currency: 'GBP', phoneCode: '+44' },
  { code: 'AU', name: 'Australia', currency: 'AUD', phoneCode: '+61' },
  { code: 'CA', name: 'Canada', currency: 'CAD', phoneCode: '+1' },
  { code: 'SG', name: 'Singapore', currency: 'SGD', phoneCode: '+65' },
  { code: 'AE', name: 'UAE', currency: 'AED', phoneCode: '+971' },
  { code: 'DE', name: 'Germany', currency: 'EUR', phoneCode: '+49' },
  { code: 'FR', name: 'France', currency: 'EUR', phoneCode: '+33' },
  { code: 'NL', name: 'Netherlands', currency: 'EUR', phoneCode: '+31' },
  { code: 'IE', name: 'Ireland', currency: 'EUR', phoneCode: '+353' },
]

export const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST)' },
  { value: 'America/New_York', label: 'America/New_York (EST/EDT)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
  { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Europe/Paris (CET/CEST)' },
  { value: 'Australia/Sydney', label: 'Australia/Sydney (AEST/AEDT)' },
  { value: 'Asia/Singapore', label: 'Asia/Singapore (SGT)' },
  { value: 'Asia/Dubai', label: 'Asia/Dubai (GST)' },
]

export const CURRENCIES = [
  { code: 'INR', symbol: '₹' },
  { code: 'USD', symbol: '$' },
  { code: 'GBP', symbol: '£' },
  { code: 'EUR', symbol: '€' },
  { code: 'AUD', symbol: 'A$' },
  { code: 'CAD', symbol: 'C$' },
  { code: 'SGD', symbol: 'S$' },
  { code: 'AED', symbol: 'د.إ' },
]

export const getCurrencySymbol = (code: string) => {
  return CURRENCIES.find(c => c.code === code)?.symbol || code
}

export const getCountryByCode = (code: string) => {
  return COUNTRIES.find(c => c.code === code)
}

export const getDefaultCurrency = (countryCode: string) => {
  return getCountryByCode(countryCode)?.currency || 'USD'
}

export const getDefaultPhoneCode = (countryCode: string) => {
  return getCountryByCode(countryCode)?.phoneCode || ''
}
