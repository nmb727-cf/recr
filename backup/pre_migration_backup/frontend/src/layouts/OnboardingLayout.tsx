import { Layout } from 'antd'

interface OnboardingLayoutProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  logo?: React.ReactNode
}

export default function OnboardingLayout({ children, title, subtitle, logo }: OnboardingLayoutProps) {
  return (
    <Layout className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 font-sans">
      <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <div className="mb-3 flex items-center justify-center gap-2">
            {logo || (
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white shadow-soft-md">
                R
              </div>
            )}
          </div>
          {title && <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{title}</h1>}
          {subtitle && <p className="text-sm font-medium text-slate-500 mt-1">{subtitle}</p>}
        </div>

        {/* Content Container */}
        <div className="w-full max-w-2xl">
          {children}
        </div>

        <p className="mt-12 text-xs font-medium text-slate-400 tracking-wide uppercase">
          © {new Date().getFullYear()} RecruitOS. All rights reserved.
        </p>
      </div>
    </Layout>
  )
}
