import { Layout } from 'antd'

interface AuthLayoutProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <Layout className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <div className="mb-3 flex items-center justify-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-lg font-bold text-white">
              R
            </div>
            <span className="text-2xl font-bold text-gray-800">RecruitOS</span>
          </div>
          <p className="text-sm text-gray-500">Modern Recruitment Platform</p>
        </div>

        {/* Card */}
        <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
          {children}
        </div>

        <p className="mt-6 text-xs text-gray-400">
          © {new Date().getFullYear()} RecruitOS. All rights reserved.
        </p>
      </div>
    </Layout>
  )
}
