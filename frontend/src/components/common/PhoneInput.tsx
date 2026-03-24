import { useState, useEffect } from 'react'
import { Select, Input } from 'antd'
import { useAuthStore } from '@/store/authStore'

const { Option } = Select

// Country data: code, dial_code, name, flag emoji
export const COUNTRIES = [
  { code: 'AF', dial: '+93', name: 'Afghanistan', flag: '🇦🇫' },
  { code: 'AL', dial: '+355', name: 'Albania', flag: '🇦🇱' },
  { code: 'DZ', dial: '+213', name: 'Algeria', flag: '🇩🇿' },
  { code: 'AR', dial: '+54', name: 'Argentina', flag: '🇦🇷' },
  { code: 'AU', dial: '+61', name: 'Australia', flag: '🇦🇺' },
  { code: 'AT', dial: '+43', name: 'Austria', flag: '🇦🇹' },
  { code: 'BH', dial: '+973', name: 'Bahrain', flag: '🇧🇭' },
  { code: 'BD', dial: '+880', name: 'Bangladesh', flag: '🇧🇩' },
  { code: 'BE', dial: '+32', name: 'Belgium', flag: '🇧🇪' },
  { code: 'BR', dial: '+55', name: 'Brazil', flag: '🇧🇷' },
  { code: 'CA', dial: '+1', name: 'Canada', flag: '🇨🇦' },
  { code: 'CN', dial: '+86', name: 'China', flag: '🇨🇳' },
  { code: 'CO', dial: '+57', name: 'Colombia', flag: '🇨🇴' },
  { code: 'HR', dial: '+385', name: 'Croatia', flag: '🇭🇷' },
  { code: 'CZ', dial: '+420', name: 'Czech Republic', flag: '🇨🇿' },
  { code: 'DK', dial: '+45', name: 'Denmark', flag: '🇩🇰' },
  { code: 'EG', dial: '+20', name: 'Egypt', flag: '🇪🇬' },
  { code: 'FI', dial: '+358', name: 'Finland', flag: '🇫🇮' },
  { code: 'FR', dial: '+33', name: 'France', flag: '🇫🇷' },
  { code: 'DE', dial: '+49', name: 'Germany', flag: '🇩🇪' },
  { code: 'GH', dial: '+233', name: 'Ghana', flag: '🇬🇭' },
  { code: 'GR', dial: '+30', name: 'Greece', flag: '🇬🇷' },
  { code: 'HK', dial: '+852', name: 'Hong Kong', flag: '🇭🇰' },
  { code: 'HU', dial: '+36', name: 'Hungary', flag: '🇭🇺' },
  { code: 'IN', dial: '+91', name: 'India', flag: '🇮🇳' },
  { code: 'ID', dial: '+62', name: 'Indonesia', flag: '🇮🇩' },
  { code: 'IR', dial: '+98', name: 'Iran', flag: '🇮🇷' },
  { code: 'IQ', dial: '+964', name: 'Iraq', flag: '🇮🇶' },
  { code: 'IE', dial: '+353', name: 'Ireland', flag: '🇮🇪' },
  { code: 'IL', dial: '+972', name: 'Israel', flag: '🇮🇱' },
  { code: 'IT', dial: '+39', name: 'Italy', flag: '🇮🇹' },
  { code: 'JP', dial: '+81', name: 'Japan', flag: '🇯🇵' },
  { code: 'JO', dial: '+962', name: 'Jordan', flag: '🇯🇴' },
  { code: 'KE', dial: '+254', name: 'Kenya', flag: '🇰🇪' },
  { code: 'KW', dial: '+965', name: 'Kuwait', flag: '🇰🇼' },
  { code: 'LB', dial: '+961', name: 'Lebanon', flag: '🇱🇧' },
  { code: 'MY', dial: '+60', name: 'Malaysia', flag: '🇲🇾' },
  { code: 'MX', dial: '+52', name: 'Mexico', flag: '🇲🇽' },
  { code: 'MA', dial: '+212', name: 'Morocco', flag: '🇲🇦' },
  { code: 'NL', dial: '+31', name: 'Netherlands', flag: '🇳🇱' },
  { code: 'NZ', dial: '+64', name: 'New Zealand', flag: '🇳🇿' },
  { code: 'NG', dial: '+234', name: 'Nigeria', flag: '🇳🇬' },
  { code: 'NO', dial: '+47', name: 'Norway', flag: '🇳🇴' },
  { code: 'OM', dial: '+968', name: 'Oman', flag: '🇴🇲' },
  { code: 'PK', dial: '+92', name: 'Pakistan', flag: '🇵🇰' },
  { code: 'PH', dial: '+63', name: 'Philippines', flag: '🇵🇭' },
  { code: 'PL', dial: '+48', name: 'Poland', flag: '🇵🇱' },
  { code: 'PT', dial: '+351', name: 'Portugal', flag: '🇵🇹' },
  { code: 'QA', dial: '+974', name: 'Qatar', flag: '🇶🇦' },
  { code: 'RO', dial: '+40', name: 'Romania', flag: '🇷🇴' },
  { code: 'RU', dial: '+7', name: 'Russia', flag: '🇷🇺' },
  { code: 'SA', dial: '+966', name: 'Saudi Arabia', flag: '🇸🇦' },
  { code: 'SG', dial: '+65', name: 'Singapore', flag: '🇸🇬' },
  { code: 'ZA', dial: '+27', name: 'South Africa', flag: '🇿🇦' },
  { code: 'KR', dial: '+82', name: 'South Korea', flag: '🇰🇷' },
  { code: 'ES', dial: '+34', name: 'Spain', flag: '🇪🇸' },
  { code: 'LK', dial: '+94', name: 'Sri Lanka', flag: '🇱🇰' },
  { code: 'SE', dial: '+46', name: 'Sweden', flag: '🇸🇪' },
  { code: 'CH', dial: '+41', name: 'Switzerland', flag: '🇨🇭' },
  { code: 'TW', dial: '+886', name: 'Taiwan', flag: '🇹🇼' },
  { code: 'TH', dial: '+66', name: 'Thailand', flag: '🇹🇭' },
  { code: 'TN', dial: '+216', name: 'Tunisia', flag: '🇹🇳' },
  { code: 'TR', dial: '+90', name: 'Turkey', flag: '🇹🇷' },
  { code: 'AE', dial: '+971', name: 'UAE', flag: '🇦🇪' },
  { code: 'GB', dial: '+44', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'US', dial: '+1', name: 'United States', flag: '🇺🇸' },
  { code: 'VN', dial: '+84', name: 'Vietnam', flag: '🇻🇳' },
]

// Phone number length validation by country code
const PHONE_LENGTHS: Record<string, { min: number, max: number }> = {
  IN: { min: 10, max: 10 },
  US: { min: 10, max: 10 },
  CA: { min: 10, max: 10 },
  GB: { min: 10, max: 11 },
  AU: { min: 9, max: 9 },
  AE: { min: 9, max: 9 },
  SA: { min: 9, max: 9 },
  PK: { min: 10, max: 10 },
  BD: { min: 10, max: 10 },
  SG: { min: 8, max: 8 },
  HK: { min: 8, max: 8 },
  DE: { min: 10, max: 12 },
  FR: { min: 9, max: 9 },
  IT: { min: 9, max: 10 },
  ES: { min: 9, max: 9 },
  DEFAULT: { min: 7, max: 15 },
}

export interface PhoneValue {
  country_code: string   // e.g. 'IN'
  phone_number: string   // digits only, no dial code
}

interface PhoneInputProps {
  value?: PhoneValue
  onChange?: (val: PhoneValue) => void
  placeholder?: string
  disabled?: boolean
  size?: 'small' | 'middle' | 'large'
  defaultCountry?: string
}

export function getPhoneValidationRule() {
  return {
    validator: (_: any, value: PhoneValue) => {
      if (!value?.phone_number) return Promise.resolve()
      const digits = value.phone_number.replace(/\D/g, '')
      const lengths = PHONE_LENGTHS[value.country_code] || PHONE_LENGTHS.DEFAULT
      if (digits.length < lengths.min || digits.length > lengths.max) {
        return Promise.reject(
          new Error(`Phone number must be ${lengths.min === lengths.max ? lengths.min : `${lengths.min}–${lengths.max}`} digits for this country`)
        )
      }
      return Promise.resolve()
    }
  }
}

export default function PhoneInput({
  value,
  onChange,
  placeholder = 'Phone number',
  disabled = false,
  size = 'middle',
  defaultCountry = 'IN',
}: PhoneInputProps) {
  const user = useAuthStore(s => s.user)

  // Determine default country: value > user org country > prop default
  const resolvedDefault = value?.country_code || (user as any)?.country_code || defaultCountry

  const [countryCode, setCountryCode] = useState(resolvedDefault)
  const [phoneNumber, setPhoneNumber] = useState(value?.phone_number || '')

  useEffect(() => {
    if (value) {
      setCountryCode(value.country_code || resolvedDefault)
      setPhoneNumber(value.phone_number || '')
    }
  }, [value])

  const handleCountryChange = (code: string) => {
    setCountryCode(code)
    onChange?.({ country_code: code, phone_number: phoneNumber })
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/[^\d\s\-\(\)]/g, '')
    setPhoneNumber(digits)
    onChange?.({ country_code: countryCode, phone_number: digits })
  }

  return (
    <Input.Group compact style={{ display: 'flex' }}>
      <Select
        value={countryCode}
        onChange={handleCountryChange}
        disabled={disabled}
        size={size}
        showSearch
        optionFilterProp="label"
        style={{ width: 110, flexShrink: 0 }}
        popupMatchSelectWidth={280}
        filterOption={(input, option) => {
          const country = COUNTRIES.find(c => c.code === option?.value)
          return !!(
            country?.name.toLowerCase().includes(input.toLowerCase()) ||
            country?.dial.includes(input)
          )
        }}
      >
        {COUNTRIES.map(c => (
          <Option key={c.code} value={c.code} label={`${c.name} ${c.dial}`}>
            <span>{c.flag} {c.dial}</span>
          </Option>
        ))}
      </Select>
      <Input
        value={phoneNumber}
        onChange={handlePhoneChange}
        placeholder={placeholder}
        disabled={disabled}
        size={size}
        style={{ flex: 1 }}
        maxLength={15}
      />
    </Input.Group>
  )
}

// Helper to format phone for display
export function formatPhoneDisplay(countryCode: string, phoneNumber: string): string {
  if (!phoneNumber) return '—'
  const country = COUNTRIES.find(c => c.code === countryCode)
  if (!country) return phoneNumber
  return `${country.flag} ${country.dial} ${phoneNumber}`
}

// Helper to get combined phone string for backend (legacy single field)
export function getCombinedPhone(countryCode: string, phoneNumber: string): string {
  const country = COUNTRIES.find(c => c.code === countryCode)
  if (!country || !phoneNumber) return phoneNumber || ''
  return `${country.dial}${phoneNumber}`
}
