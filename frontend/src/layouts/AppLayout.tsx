import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Avatar, Dropdown, Button, theme, Tooltip } from 'antd'
import {
  LayoutDashboard,
  FileText,
  Users,
  GitBranch,
  Calendar,
  Building2,
  BarChart3,
  Settings,
  Bell,
  User as UserIcon,
  LogOut,
  Search,
  FileSearch,
  IdCard,
  Mail,
  ChevronLeft,
  ChevronRight,
  Check,
  Moon,
  Sun,
} from 'lucide-react'
import { Popover, message as antdMessage } from 'antd'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { notificationsApi } from '@/api/notifications'
import { useApiQuery } from '@/hooks/useApiQuery'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import type { Notification } from '@/types'
import { cn } from '@/utils/cn'

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

// ─── Sidebar Item ───────────────────────────────────────────────────────────

const SidebarItem = ({ 
  item, 
  collapsed, 
  active, 
  onClick 
}: { 
  item: any, 
  collapsed: boolean, 
  active: boolean,
  onClick?: () => void
}) => {
  const Icon = item.icon
  
  return (
    <Link 
      to={item.path || '#'} 
      onClick={onClick}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-200",
        active 
          ? "bg-blue-50 text-blue-700 shadow-sm" 
          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
      )}
    >
      <Icon className={cn(
        "h-5 w-5 shrink-0 transition-colors",
        active ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
      )} />
      
      {!collapsed && (
        <motion.span 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-sm font-medium whitespace-nowrap overflow-hidden text-ellipsis"
        >
          {item.label}
        </motion.span>
      )}
      
      {active && (
        <motion.div 
          layoutId="sidebar-active"
          className="absolute left-0 h-6 w-1 rounded-r-full bg-blue-600" 
        />
      )}
    </Link>
  )
}

// ─── AppLayout Component ─────────────────────────────────────────────────────

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  theme.useToken()

  // ── Candidate sees a single flat nav, company/agency roles see filtered nav
  const CANDIDATE_NAV = [
    { key: 'dashboard',               label: 'Dashboard',       icon: LayoutDashboard, path: '/dashboard' },
    { key: 'candidate_jobs',          label: 'Job Search',      icon: Search,          path: '/candidate/jobs' },
    { key: 'candidate_applications',  label: 'My Applications', icon: FileSearch,      path: '/candidate/applications' },
    { key: 'passport',                label: 'Passport',        icon: IdCard,          path: '/passport' },
    { key: 'interviews',              label: 'Interviews',      icon: Calendar,        path: '/interviews' },
    { key: 'messages',                label: 'Messages',        icon: Mail,            path: '/messages' },
    { key: 'settings',                label: 'Settings',        icon: Settings,        path: '/settings' },
  ]

  const COMPANY_NAV = [
    { key: 'dashboard',   label: 'Dashboard',  icon: LayoutDashboard, path: '/dashboard' },
    { key: 'jobs',        label: 'Jobs',       icon: FileText,        path: '/jobs',        roles: ['tenant_admin', 'recruiter', 'hiring_manager', 'interviewer', 'super_admin'] },
    { key: 'candidates',  label: 'Candidates', icon: Users,           path: '/candidates',  roles: ['tenant_admin', 'recruiter', 'hiring_manager', 'interviewer', 'super_admin'] },
    { key: 'pipeline',    label: 'Pipeline',   icon: GitBranch,       path: '/pipeline',    roles: ['tenant_admin', 'recruiter', 'hiring_manager', 'interviewer', 'super_admin'] },
    { key: 'interviews',  label: 'Interviews', icon: Calendar,        path: '/interviews',  roles: ['tenant_admin', 'recruiter', 'hiring_manager', 'interviewer', 'super_admin'] },
    { key: 'agencies',    label: 'Agencies',   icon: Building2,       path: '/agencies',    roles: ['tenant_admin', 'recruiter', 'super_admin'] },
    { key: 'messages',    label: 'Messages',   icon: Mail,            path: '/messages' },
    { key: 'analytics',   label: 'Analytics',  icon: BarChart3,       path: '/analytics',   roles: ['tenant_admin', 'recruiter', 'hiring_manager', 'super_admin', 'agency_admin', 'agency_recruiter'] },
    { key: 'settings',    label: 'Settings',   icon: Settings,        path: '/settings' },
  ]

  const isCandidate = user?.role === 'candidate'
  const sidebarItems = isCandidate
    ? CANDIDATE_NAV
    : COMPANY_NAV.filter(item => !item.roles || (user && item.roles.includes(user.role)))

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const userMenuItems = [
    { key: 'profile', label: 'My Profile', icon: <UserIcon className="h-4 w-4" />, onClick: () => navigate('/settings/profile') },
    { key: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" />, onClick: () => navigate('/settings') },
    { type: 'divider' as const },
    { key: 'logout', label: 'Sign out', icon: <LogOut className="h-4 w-4" />, danger: true, onClick: handleLogout },
  ]

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

        <div className="flex flex-col gap-1 p-4 overflow-y-auto max-h-[calc(100vh-140px)]">
          <p className={cn("px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400", collapsed && "text-center px-0")}>
            {collapsed ? '•••' : 'Main Menu'}
          </p>
          {sidebarItems.map(item => (
            <SidebarItem
              key={item.key}
              item={item}
              collapsed={collapsed}
              active={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
            />
          ))}
        </div>

        {/* User profile at bottom */}
        {!collapsed && user && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-3">
              <Avatar src={user.avatar_url} icon={<UserIcon />} className="bg-blue-100 text-blue-600 shrink-0" />
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
            icon={collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
            onClick={() => setCollapsed(!collapsed)}
            className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
          />

          <div className="flex items-center gap-2">
            <Tooltip title={darkMode ? "Light mode" : "Dark mode"}>
              <Button
                type="text"
                icon={darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                onClick={() => setDarkMode(!darkMode)}
                className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
              />
            </Tooltip>
            
            <NotificationDropdown />
            
            <div className="mx-2 h-6 w-[1px] bg-slate-200" />

            <Dropdown
              menu={{ items: userMenuItems.map(i => i.type === 'divider' ? i : { ...i, icon: i.icon, label: i.label, onClick: i.onClick }) }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div className="flex cursor-pointer items-center gap-2 rounded-xl p-1.5 transition-colors hover:bg-slate-100">
                <Avatar src={user?.avatar_url} icon={<UserIcon />} size="small" className="bg-blue-100 text-blue-600" />
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
    </Layout>
  )
}
