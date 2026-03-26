import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES } from '@/i18n'
import i18n from '@/i18n'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Avatar, Dropdown, Button, Tooltip, Menu, Badge, Input, Tabs } from 'antd'
import {
  LogoutOutlined,
  UserOutlined,
  GlobalOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import {
  Bell,
  Inbox,
  User as UserIcon,
  ChevronLeft,
  ChevronRight,
  Check,
  Search,
  Zap,
} from 'lucide-react'
import { Popover, message as antdMessage } from 'antd'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/authStore'
import { notificationsApi } from '@/api/notifications'
import { GlobalDrawer } from '../components/drawers/GlobalDrawer'
import { useApiQuery } from '@/hooks/useApiQuery'
import { 
  companySidebarConfig, 
  agencySidebarConfig, 
  candidateSidebarConfig,
  NavItem 
} from '@/config/navigation'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import type { Notification } from '@/types'

dayjs.extend(relativeTime)

const { Header, Sider, Content } = Layout

// ─── Notification Dropdown ──────────────────────────────────────────────────

function NotificationDropdown({ badgeOverrideCount }: { badgeOverrideCount?: number }) {
  const { data, refetch } = useApiQuery(['notifications', 'unread'], () =>
    notificationsApi.list({ is_read: false })
  , {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
  }
  )
  const notifications = (data as { notifications: Notification[] } | undefined)?.notifications ?? []
  const badgeCount = badgeOverrideCount ?? notifications.length

  const markAllRead = async () => {
    try {
      await notificationsApi.markAllRead()
      refetch()
    } catch (err) {
      antdMessage.error(i18n.t('common:messages.failed_mark_all_read'))
    }
  }

  const markRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id)
      refetch()
    } catch (err) {
      antdMessage.error(i18n.t('common:messages.failed_mark_read'))
    }
  }

  const content = (
    <div className="w-80 overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-black/5">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-4 py-3">
        <span className="text-sm font-semibold text-slate-900">{i18n.t('common:sidebar.notifications', 'Notifications')}</span>
        <button 
          onClick={markAllRead}
          disabled={notifications.length === 0}
          className="text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
        >
          {i18n.t('common:actions.mark_all_read')}
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
            <p className="mt-4 text-sm font-medium text-slate-900">{i18n.t('common:empty.all_caught_up')}</p>
            <p className="mt-1 text-xs text-slate-500 text-center">{i18n.t('common:empty.no_notifications')}</p>
          </div>
        )}
      </div>
      <div className="border-t border-slate-100 p-3 text-center">
        <Link to="/notifications" className="text-xs font-semibold text-slate-600 hover:text-slate-900">
          {i18n.t('common:actions.view_all')} {i18n.t('common:sidebar.notifications', 'notifications')}
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
        <Badge count={badgeCount} size="small" offset={[-2, 6]}>
          <Button
            type="text"
            icon={<Bell className="h-5 w-5 text-slate-600" />}
            className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
          />
        </Badge>
      </div>
    </Popover>
  )
}

// ─── Menu Items Logic ───────────────────────────────────────────────────────

const getMenuItems = (
  role: string,
  permissions: string[] = [],
  badgeCounts: Record<string, number> = {}
) => {
  const can = (code: string) => permissions.includes(code)
  
  let config: NavItem[] = []
  if (role === 'candidate') {
    config = candidateSidebarConfig
  } else if (role === 'agency_owner' || role === 'agency_admin' || role === 'agency_recruiter') {
    config = agencySidebarConfig
  } else {
    config = companySidebarConfig
  }

  const filterItems = (items: NavItem[]): any[] => {
    return items
      .filter(item => !item.permission || can(item.permission))
      .map(item => ({
        key: item.key,
        label: (
          <div className="flex w-full items-center justify-between gap-2">
            <span className="truncate">{item.label as string}</span>
            {badgeCounts[item.key] ? (
              <span className="rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                {badgeCounts[item.key]}
              </span>
            ) : null}
          </div>
        ),
        icon: item.icon,
        children: item.children ? filterItems(item.children) : undefined
      }))
  }

  return filterItems(config)
}

const ACTION_CENTER_ITEMS: Record<string, string[]> = {
  urgent: ['new_candidate_submitted', 'interview_today'],
  today: ['candidate_requested_info', 'client_reply'],
  upcoming: ['follow_up_due'],
}

// ─── AppLayout Component ─────────────────────────────────────────────────────

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [actionCenterOpen, setActionCenterOpen] = useState(false)
  const [actionCenterTab, setActionCenterTab] = useState('urgent')
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const user = useAuthStore(state => state.user)
  const { t } = useTranslation('common')
  const isAgencyTenant =
    user?.role === 'agency_owner' || user?.role === 'agency_admin' || user?.role === 'agency_recruiter'

  const sidebarAttentionCounts = useMemo(() => ({
    '/candidates/active': 3,
    '/pipeline': 2,
    ...(isAgencyTenant ? { '/agencies/my-submissions': 1 } : { '/applications': 1 }),
  }), [isAgencyTenant])

  const menuItems = getMenuItems(user?.role || '', user?.permissions ?? [], sidebarAttentionCounts)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode)
    // Persist to user profile in background (best-effort)
    import('@/api/auth').then(({ authApi }) => {
      authApi.updateMe({ language: langCode } as any).catch(() => {})
    })
  }

  const languageMenuItems = SUPPORTED_LANGUAGES.map((lang) => ({
    key: lang.code,
    label: `${lang.nativeLabel} (${lang.label})`,
    onClick: () => handleLanguageChange(lang.code),
  }))

  const userMenuItems = [
    { key: 'profile', label: t('user_menu.my_profile'), icon: <UserOutlined />, onClick: () => navigate('/settings/profile') },
    { key: 'settings', label: t('user_menu.settings'), icon: <SettingOutlined />, onClick: () => navigate('/settings') },
    { type: 'divider' as const },
    { key: 'logout', label: t('auth:logout'), icon: <LogoutOutlined />, danger: true, onClick: handleLogout },
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
  const actionCenterCount = 5
  const inboxCount = 4
  const notificationCount = 6
  const actionCenterTabItems = [
    { key: 'urgent', label: t('header.urgent', 'Urgent') },
    { key: 'today', label: t('header.today', 'Today') },
    { key: 'upcoming', label: t('header.upcoming', 'Upcoming') },
  ]
  const actionCenterItems = (ACTION_CENTER_ITEMS[actionCenterTab] || []).map((k) =>
    t(`header.action_items.${k}`, k.replace(/_/g, ' '))
  )

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
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-lg">T</div>
          {!collapsed && (
            <motion.span 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
              className="ml-3 font-bold text-slate-900 tracking-tight text-lg"
            >
              TalentOS
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
          <div className="flex items-center gap-3">
            <Button
              type="text"
              icon={collapsed ? <ChevronRight className="h-5 w-5 text-slate-600" /> : <ChevronLeft className="h-5 w-5 text-slate-600" />}
              onClick={() => setCollapsed(!collapsed)}
              className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
            />
            <Input
              allowClear
              placeholder={t('search.placeholder', 'Search')}
              prefix={<Search className="h-4 w-4 text-slate-400" />}
              className="w-[360px] rounded-xl"
            />
          </div>

          <div className="flex items-center gap-2">
            <Dropdown menu={{ items: languageMenuItems }} trigger={['click']} placement="bottomRight">
              <Tooltip title={t('language_switcher.label')}>
                <Button
                  type="text"
                  icon={<GlobalOutlined className="h-5 w-5 text-slate-600" />}
                  className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
                />
              </Tooltip>
            </Dropdown>

            <Badge count={actionCenterCount} size="small">
              <Button
                type="text"
                icon={<Zap className="h-5 w-5 text-amber-600" />}
                onClick={() => setActionCenterOpen((v) => !v)}
                className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-amber-50"
              />
            </Badge>

            <Badge count={inboxCount} size="small">
              <Button
                type="text"
                icon={<Inbox className="h-5 w-5 text-slate-600" />}
                onClick={() => navigate('/messages')}
                className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
              />
            </Badge>

            <NotificationDropdown badgeOverrideCount={notificationCount} />

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

      <div className="fixed bottom-6 right-6 z-[60]">
        <Badge count={actionCenterCount}>
          <Button
            type="primary"
            shape="circle"
            size="large"
            icon={<Zap className="h-5 w-5" />}
            onClick={() => setActionCenterOpen((v) => !v)}
            className="!h-14 !w-14 !bg-blue-600 !shadow-lg"
          />
        </Badge>
      </div>

      {actionCenterOpen && (
        <div className="fixed bottom-24 right-6 z-[60] w-[360px] rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <div className="border-b border-slate-100 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-amber-600" />
                <span className="text-sm font-semibold text-slate-900">{t('header.action_center', 'Action Center')}</span>
              </div>
              <Badge count={actionCenterCount} />
            </div>
          </div>
          <Tabs
            activeKey={actionCenterTab}
            onChange={setActionCenterTab}
            size="small"
            className="px-3 pt-2"
            items={actionCenterTabItems.map((it) => ({ key: it.key, label: it.label }))}
          />
          <div className="max-h-72 overflow-y-auto px-4 pb-4">
            <div className="space-y-2">
              {actionCenterItems.map((item) => (
                <div key={item} className="rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2">
                  <span className="text-sm text-slate-700">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <GlobalDrawer />
    </Layout>
  )
}
