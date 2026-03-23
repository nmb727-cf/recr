import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Avatar, Dropdown, Button, Tooltip, Menu } from 'antd'
import {
  DashboardOutlined,
  FileSearchOutlined,
  CalendarOutlined,
  SettingOutlined,
  TeamOutlined,
  BankOutlined,
  BarChartOutlined,
  ApartmentOutlined,
  LogoutOutlined,
  UserOutlined,
  ProjectOutlined,
  FileDoneOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import {
  Bell,
  User as UserIcon,
  ChevronLeft,
  ChevronRight,
  Check,
  Moon,
  Sun,
} from 'lucide-react'
import { Popover, message as antdMessage } from 'antd'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/authStore'
import { notificationsApi } from '@/api/notifications'
import { GlobalDrawer } from '../components/drawers/GlobalDrawer'
import { useApiQuery } from '@/hooks/useApiQuery'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import type { Notification } from '@/types'

dayjs.extend(relativeTime)

const { Header, Sider, Content } = Layout

// ─── Notification Dropdown ──────────────────────────────────────────────────

function NotificationDropdown() {
  const { data, refetch } = useApiQuery(['notifications', 'unread'], () =>
    notificationsApi.list({ is_read: false })
  )
  const notifications = (data as { notifications: Notification[] } | undefined)?.notifications ?? []

  const markAllRead = async () => {
    try {
      await notificationsApi.markAllRead()
      refetch()
    } catch (err) {
      antdMessage.error('Failed to mark all as read')
    }
  }

  const markRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id)
      refetch()
    } catch (err) {
      antdMessage.error('Failed to mark as read')
    }
  }

  const content = (
    <div className="w-80 overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-black/5">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-4 py-3">
        <span className="text-sm font-semibold text-slate-900">Notifications</span>
        <button 
          onClick={markAllRead}
          disabled={notifications.length === 0}
          className="text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
        >
          Mark all as read
        </button>
      </div>
      <div className="max-h-[400px] overflow-y-auto">
        {notifications.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {notifications.map((item) => (
              <div
                key={item.id}
                onClick={() => markRead(item.id)}
                className="group relative flex cursor-pointer gap-3 p-4 transition-colors hover:bg-slate-50"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{item.body}</p>
                  <p className="mt-2 text-[10px] font-medium text-slate-400">
                    {dayjs(item.created_at).fromNow()}
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); markRead(item.id) }}
                  className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-blue-600"
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 text-slate-400">
              <Bell className="h-6 w-6" />
            </div>
            <p className="mt-4 text-sm font-medium text-slate-900">All caught up!</p>
            <p className="mt-1 text-xs text-slate-500">No new notifications to show.</p>
          </div>
        )}
      </div>
      <div className="border-t border-slate-100 p-3 text-center">
        <Link to="/notifications" className="text-xs font-semibold text-slate-600 hover:text-slate-900">
          View all notifications
        </Link>
      </div>
    </div>
  )

  return (
    <Popover
      content={content}
      trigger="click"
      placement="bottomRight"
      overlayInnerStyle={{ padding: 0 }}
      arrow={false}
    >
      <div className="relative">
        <Button
          type="text"
          icon={<Bell className="h-5 w-5 text-slate-600" />}
          className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
        />
        {notifications.length > 0 && (
          <span className="absolute right-2.5 top-2.5 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-600"></span>
          </span>
        )}
      </div>
    </Popover>
  )
}

// ─── Menu Items Logic ───────────────────────────────────────────────────────

const getMenuItems = (role: string) => {
  // ─── 1. CANDIDATE SIDEBAR ──────────────────────────────────────────────────
  if (role === 'candidate') {
    return [
      { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
      { key: '/candidate/jobs', icon: <ProjectOutlined />, label: 'Jobs' },
      { key: '/candidate/applications', icon: <FileSearchOutlined />, label: 'Applications' },
      { key: '/interviews', icon: <CalendarOutlined />, label: 'Interviews' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ]
  }
  
  // ─── 2. AGENCY SIDEBAR ─────────────────────────────────────────────────────
  if (role === 'agency_owner' || role === 'agency_admin' || role === 'agency_recruiter') {
    return [
      { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
      { 
        key: 'agency-jobs', 
        icon: <ProjectOutlined />, 
        label: 'Jobs',
        children: [
          { key: '/agencies/my-jobs', label: 'Incoming Jobs' },
          { key: '/jobs', label: 'Internal Jobs' },
        ]
      },
      { 
        key: 'agency-candidates', 
        icon: <TeamOutlined />, 
        label: 'Candidates',
        children: [
          { key: '/candidates', label: 'Database' },
        ]
      },
      { key: '/leads', icon: <UserOutlined />, label: 'Leads' },
      { key: '/agencies/my-submissions', icon: <FileSearchOutlined />, label: 'Submissions' },
      { key: '/agencies/my-clients', icon: <BankOutlined />, label: 'Clients' },
      { 
        key: 'agency-team', 
        icon: <TeamOutlined />, 
        label: 'Team',
        children: [
          { key: '/settings?tab=users', label: 'Recruiters' },
          { key: '/settings?tab=hierarchy', label: 'Hierarchy' },
        ]
      },
      { key: '/analytics', icon: <LineChartOutlined />, label: 'Performance' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ]
  }

  // ─── 3. COMPANY SIDEBAR (Default) ──────────────────────────────────────────
  return [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/jobs', icon: <ProjectOutlined />, label: 'Jobs' },
    { key: '/pipeline', icon: <ApartmentOutlined />, label: 'Pipeline' },
    {
      key: 'company-candidates',
      icon: <TeamOutlined />,
      label: 'Candidates',
      children: [
        { key: '/candidates', label: 'Database' },
      ],
    },
    { key: '/leads', icon: <TeamOutlined />, label: 'Leads' },
    { key: '/agencies', icon: <BankOutlined />, label: 'Agencies' },
    { key: '/interviews', icon: <CalendarOutlined />, label: 'Interviews' },
    { key: '/offers', icon: <FileDoneOutlined />, label: 'Offers' },
    { key: '/analytics', icon: <BarChartOutlined />, label: 'Reports' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
  ]
}

// ─── AppLayout Component ─────────────────────────────────────────────────────

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const user = useAuthStore(state => state.user)
  
  const menuItems = getMenuItems(user?.role || '')

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const userMenuItems = [
    { key: 'profile', label: 'My Profile', icon: <UserOutlined />, onClick: () => navigate('/settings/profile') },
    { key: 'settings', label: 'Settings', icon: <SettingOutlined />, onClick: () => navigate('/settings') },
    { type: 'divider' as const },
    { key: 'logout', label: 'Sign out', icon: <LogoutOutlined />, danger: true, onClick: handleLogout },
  ]

  // Determine selected keys based on pathname and query params
  const currentKey = location.pathname + (location.search ? location.search : '')
  
  // Logic to find which item/sub-item is active
  const findActiveKey = (items: any[]): string | undefined => {
    for (const item of items) {
      if (item.key === currentKey) return item.key
      if (item.key === location.pathname) return item.key
      if (item.children) {
        const childKey = findActiveKey(item.children)
        if (childKey) return childKey
      }
    }
    return undefined
  }

  const selectedKey = findActiveKey(menuItems) || location.pathname

  return (
    <Layout className="min-h-screen">
      {/* ── Sidebar ──────────────────────────────────────────────────────────── */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={260}
        collapsedWidth={80}
        className="fixed inset-y-0 left-0 z-50 !bg-white border-r border-slate-200 shadow-sm"
      >
        <div className="flex h-16 items-center px-6 border-b border-slate-100">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-lg">R</div>
          {!collapsed && (
            <motion.span 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
              className="ml-3 font-bold text-slate-900 tracking-tight text-lg"
            >
              RecruitOS
            </motion.span>
          )}
        </div>

        <div className="flex flex-col gap-1 p-2 overflow-y-auto max-h-[calc(100vh-140px)]">
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            className="border-none"
          />
        </div>

        {/* User profile at bottom */}
        {!collapsed && user && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-3">
              <Avatar src={user.avatar_url} icon={<UserOutlined />} className="bg-blue-100 text-blue-600 shrink-0" />
              <div className="flex-1 overflow-hidden">
                <p className="text-xs font-semibold text-slate-900 truncate">{user.full_name}</p>
                <p className="text-[10px] text-slate-500 capitalize">{user.role.replace(/_/g, ' ')}</p>
              </div>
            </div>
          </div>
        )}
      </Sider>

      {/* ── Main Layout ──────────────────────────────────────────────────────── */}
      <Layout 
        className="transition-all duration-200"
        style={{ marginLeft: collapsed ? 80 : 260 }}
      >
        <Header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200/60 bg-white/80 px-6 backdrop-blur-md">
          <Button
            type="text"
            icon={collapsed ? <ChevronRight className="h-5 w-5 text-slate-600" /> : <ChevronLeft className="h-5 w-5 text-slate-600" />}
            onClick={() => setCollapsed(!collapsed)}
            className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
          />

          <div className="flex items-center gap-2">
            <Tooltip title={darkMode ? "Light mode" : "Dark mode"}>
              <Button
                type="text"
                icon={darkMode ? <Sun className="h-5 w-5 text-slate-600" /> : <Moon className="h-5 w-5 text-slate-600" />}
                onClick={() => setDarkMode(!darkMode)}
                className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
              />
            </Tooltip>
            
            <NotificationDropdown />
            
            <div className="mx-2 h-6 w-[1px] bg-slate-200" />

            <Dropdown
              menu={{ items: (userMenuItems as any[]).map(i => i.type === 'divider' ? i : { ...i, icon: i.icon, label: i.label, onClick: i.onClick }) }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div className="flex cursor-pointer items-center gap-2 rounded-xl p-1.5 transition-colors hover:bg-slate-100">
                <Avatar src={user?.avatar_url} icon={<UserIcon className="h-4 w-4" />} size="small" className="bg-blue-100 text-blue-600" />
                <div className="hidden lg:block">
                  <p className="text-xs font-semibold text-slate-900 leading-none">{user?.full_name}</p>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content className="p-8 max-w-[1600px] mx-auto w-full">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </Content>
      </Layout>
      <GlobalDrawer />
    </Layout>
  )
}
