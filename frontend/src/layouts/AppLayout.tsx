import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES } from '@/i18n'
import i18n from '@/i18n'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Avatar, Dropdown, Button, Tooltip, Menu, Badge, Input, Tabs, Drawer } from 'antd'
import {
  LogoutOutlined,
  UserOutlined,
  GlobalOutlined,
  SettingOutlined,
  PlusOutlined,
  ProjectOutlined,
  TeamOutlined,
  CalendarOutlined,
  DashboardOutlined,
  RocketOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  DownOutlined,
  MenuOutlined,
  FileOutlined,
  InboxOutlined,
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
  Calendar as CalendarIcon,
  Clock3,
} from 'lucide-react'
import { Popover, message as antdMessage } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/authStore'
import { notificationsApi } from '@/api/notifications'
import { useCommunicationsStore } from '@/store/communicationsStore'
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
import type { Notification, User } from '@/types'
import { cn } from '@/utils/cn'
import JobCreateForm from '@/components/forms/JobCreateForm'
import AddCandidateWorkflowModal from '@/components/candidates/AddCandidateWorkflowModal'
import { AttentionEngine } from '../components/common/AttentionEngine'
import { canAccessMasterAdmin } from '@/utils/authAccess'
import { isAgencyRole, isCompanyAdminRole } from '@/config/routeAccess'

dayjs.extend(relativeTime)

const { Header, Content } = Layout

// ─── Notification Dropdown ──────────────────────────────────────────────────

function NotificationDropdown() {
  const setUnreadNotificationCount = useCommunicationsStore((s) => s.setUnreadNotificationCount)
  const { data, refetch } = useApiQuery(['notifications', 'unread'], () =>
    notificationsApi.list({ is_read: false })
  , {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
  }
  )
  const notifications = (data as { notifications: Notification[] } | undefined)?.notifications ?? []
  const badgeCount = notifications.length

  // Keep store in sync whenever count changes
  useEffect(() => {
    setUnreadNotificationCount(badgeCount)
  }, [badgeCount, setUnreadNotificationCount])

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

export const getSystemMenuItems = (
  user?: User | null
) => {
  const role = user?.role ?? ''
  const isCompanyAdmin = isCompanyAdminRole(role)
  const permissions = user?.permissions ?? []
  const can = (code: string) => permissions.includes(code)
  const canSeeAgencyIntelligence = ['super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager'].includes(role)
  const canAccessAdmin = canAccessMasterAdmin(user)
  
  let config: NavItem[] = []
  if (role === 'candidate') {
    config = candidateSidebarConfig
  } else if (isAgencyRole(role)) {
    config = agencySidebarConfig
  } else {
    config = companySidebarConfig
  }

  // Filter out Jobs, Candidates, Active Work, and Talent Pools from the dropdown
  const EXCLUDED_KEYS = ['/jobs', '/candidates', '/candidates/active', '/candidates/pools', '/agencies/my-jobs', '/candidate/jobs', 'work', 'records']
  const COMPANY_ALLOWED_KEYS = new Set([
    '/dashboard',
    '/jobs',
    '/pipeline',
    '/candidates',
    '/applications',
    '/interviews',
    '/offers',
    '/hiring-decisions',
    '/intelligence',
    '/analytics',
    '/communications',
    '/notifications',
    '/settings',
    '/admin',
    '/admin/tenants',
    '/admin/settings',
    '/admin/audit',
  ])
  const AGENCY_ALLOWED_KEYS = new Set([
    '/dashboard',
    '/agency/talent-pool',
    '/agency/pipeline',
    '/agency/hotlists',
    '/agency/followups',
    '/agency/jobs',
    '/agency/submissions',
    '/agency/clients',
    '/agency/analytics',
    '/interviews/dashboard',
    '/communications',
    '/notifications',
    '/settings',
    '/settings?tab=users',
  ])
  const CANDIDATE_ALLOWED_KEYS = new Set([
    '/candidate/dashboard',
    '/candidate/applications',
    '/candidate/interviews',
    '/candidate/jobs',
    '/passport',
  ])

  const filterItems = (items: NavItem[]): any[] => {
    return items
      .filter(item => {
        if (!canAccessAdmin && typeof item.key === 'string' && item.key.startsWith('/admin')) {
          return false
        }
        if (role === 'candidate' && typeof item.key === 'string' && item.key.startsWith('/') && !CANDIDATE_ALLOWED_KEYS.has(item.key)) {
          return false
        }
        if (isAgencyRole(role) && typeof item.key === 'string' && item.key.startsWith('/') && !AGENCY_ALLOWED_KEYS.has(item.key)) {
          return false
        }
        if (!isCompanyAdmin && role !== 'candidate' && !isAgencyRole(role) && typeof item.key === 'string' && item.key.startsWith('/') && !COMPANY_ALLOWED_KEYS.has(item.key)) {
          return false
        }
        return (!item.permission || can(item.permission)) && (item.key !== '/agency-intelligence' || canSeeAgencyIntelligence)
      })
      .reduce((acc: any[], item) => {
        if (EXCLUDED_KEYS.includes(item.key)) {
          if (item.children) {
            acc.push(...filterItems(item.children))
          }
        } else {
          acc.push({
            key: item.key,
            label: item.label,
            icon: item.icon,
            children: item.children ? filterItems(item.children) : undefined
          })
        }
        return acc
      }, [])
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
  const [rightPanelOpen, setRightPanelOpen] = useState(false)
  const [actionCenterTab, setActionCenterTab] = useState('urgent')
  const [jobCreateOpen, setJobCreateOpen] = useState(false)
  const [candidateCreateOpen, setCandidateCreateOpen] = useState(false)
  const [globalSearchText, setGlobalSearchText] = useState('')
  
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const user = useAuthStore(state => state.user)
  const { t } = useTranslation('common')
  const role = user?.role ?? ''
  const isCandidate = role === 'candidate'
  const isAgency = isAgencyRole(role)
  const homePath = isCandidate ? '/candidate/dashboard' : '/dashboard'
  const workspaceLabel = isCandidate ? 'Candidate Workspace' : isAgency ? 'Agency Workspace' : 'Company Workspace'

  const systemMenuItems = useMemo(() => getSystemMenuItems(user), [user])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode)
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
    { key: 'create_job', label: 'Create Job', icon: <PlusOutlined />, onClick: () => navigate('/jobs/create') },
    { type: 'divider' as const },
    { key: 'profile', label: t('user_menu.my_profile'), icon: <UserOutlined />, onClick: () => navigate('/settings/profile') },
    { key: 'settings', label: t('user_menu.settings'), icon: <SettingOutlined />, onClick: () => navigate('/settings') },
    { type: 'divider' as const },
    { key: 'logout', label: t('auth:logout'), icon: <LogoutOutlined />, danger: true, onClick: handleLogout },
  ]

  const actionCenterCount = 5
  const unreadThreadCount = useCommunicationsStore((s) => s.unreadThreadCount)
  const actionCenterTabItems = [
    { key: 'urgent', label: t('header.urgent', 'Urgent') },
    { key: 'today', label: t('header.today', 'Today') },
    { key: 'upcoming', label: t('header.upcoming', 'Upcoming') },
  ]
  const actionCenterItems = (ACTION_CENTER_ITEMS[actionCenterTab] || []).map((k) =>
    t(`header.action_items.${k}`, k.replace(/_/g, ' '))
  )

  return (
    <Layout className="min-h-screen bg-slate-50">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <Header className="sticky top-0 z-50 flex h-14 w-full items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm">
        {/* Left: Brand & Dropdown Menu */}
        <div className="flex items-center gap-4">
          <Link to={homePath} className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-lg">T</div>
            <div className="hidden sm:block">
              <span className="font-bold text-slate-900 tracking-tight text-lg block leading-tight">TalentOS</span>
              <span className="text-[10px] uppercase tracking-[0.18em] text-slate-400">{workspaceLabel}</span>
            </div>
          </Link>
          
          <Dropdown 
            menu={{ 
              items: systemMenuItems, 
              onClick: ({ key }) => navigate(key) 
            }} 
            trigger={['click']}
            placement="bottomLeft"
          >
            <Button 
              type="text" 
              className="flex items-center gap-1 px-2 py-1 h-8 rounded-lg hover:bg-slate-100 transition-all"
            >
              <MenuOutlined className="text-slate-500" />
              <DownOutlined className="text-[10px] text-slate-400" />
            </Button>
          </Dropdown>
        </div>

        {/* Center: Search */}
        <div className="flex-1 max-w-xl mx-8 hidden lg:block">
          <Input
            allowClear
            value={globalSearchText}
            placeholder={isCandidate ? 'Search jobs...' : t('search.placeholder', 'Search candidates, jobs, agencies...')}
            prefix={<Search className="h-4 w-4 text-slate-400" />}
            onChange={(e) => setGlobalSearchText(e.target.value)}
            onPressEnter={() => {
              const q = globalSearchText.trim()
              if (isCandidate) {
                navigate(q ? `/candidate/jobs?q=${encodeURIComponent(q)}` : '/candidate/jobs')
                return
              }
              navigate(q ? `/search?q=${encodeURIComponent(q)}` : '/search')
            }}
            className="w-full rounded-xl bg-slate-100 border-none hover:bg-slate-200/70 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all"
          />
        </div>

        {/* Right: Quick Access & Profile */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1 mr-2 border-r pr-2 border-slate-200">
            {!isCandidate && !isAgency && (
              <>
                <Dropdown
                  menu={{
                    items: [
                      { key: 'all', label: 'All Jobs', icon: <ProjectOutlined />, onClick: () => navigate('/jobs') },
                      { key: 'create', label: 'Create Job', icon: <PlusOutlined />, onClick: () => navigate('/jobs/create') },
                      { type: 'divider' },
                      { key: 'templates', label: 'JD Templates', icon: <FileOutlined />, onClick: () => navigate('/jobs/templates') },
                      { key: 'archived', label: 'Archived Jobs', icon: <InboxOutlined />, onClick: () => navigate('/jobs?status=cancelled') },
                    ]
                  }}
                  placement="bottomLeft"
                  trigger={['hover']}
                >
                  <Button
                    type="text"
                    className={cn(
                      "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                      location.pathname.startsWith('/jobs') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    )}
                  >
                    <ProjectOutlined className="h-4 w-4" />
                    {t('sidebar.jobs', 'Jobs')}
                    <DownOutlined className="text-[8px] opacity-60" />
                  </Button>
                </Dropdown>
                <Button
                  type="text"
                  icon={<TeamOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/candidates/active')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/candidates') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  {t('sidebar.candidates', 'Candidates')}
                </Button>
                <Button
                  type="text"
                  icon={<NodeIndexOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/workflows')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/workflows') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  Workflows
                </Button>
              </>
            )}
            {isAgency && (
              <>
                <Button
                  type="text"
                  icon={<ProjectOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/agencies/my-jobs')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/agencies/my-jobs') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  My Jobs
                </Button>
                <Button
                  type="text"
                  icon={<CheckCircleOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/agencies/my-submissions')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/agencies/my-submissions') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  Submissions
                </Button>
              </>
            )}
            {isCandidate && (
              <>
                <Button
                  type="text"
                  icon={<ProjectOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/candidate/jobs')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/candidate/jobs') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  Browse Jobs
                </Button>
                <Button
                  type="text"
                  icon={<InboxOutlined className="h-4 w-4" />}
                  onClick={() => navigate('/candidate/applications')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all h-9",
                    location.pathname.startsWith('/candidate/applications') ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  Applications
                </Button>
              </>
            )}
          </div>

          <Tooltip title={t('calendar.title', 'Calendar')}>
            <Button
              type="text"
              icon={<CalendarIcon className="h-5 w-5 text-slate-600" />}
              onClick={() => navigate(isCandidate ? '/candidate/interviews' : '/interviews')}
              className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
            />
          </Tooltip>

          <Badge count={unreadThreadCount} size="small" offset={[-2, 6]}>
            <Button
              type="text"
              icon={<Inbox className="h-5 w-5 text-slate-600" />}
              onClick={() => navigate('/communications')}
              className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-slate-100"
            />
          </Badge>

          <NotificationDropdown />

          {!isCandidate && (
            <Button
              type="text"
              icon={<Zap className={cn("h-5 w-5", rightPanelOpen ? "text-amber-600" : "text-slate-600")} />}
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={cn("flex h-10 w-10 items-center justify-center rounded-xl transition-colors", rightPanelOpen ? "bg-amber-50" : "hover:bg-slate-100")}
            />
          )}

          <div className="mx-1 h-6 w-[1px] bg-slate-200" />

          <Dropdown
            menu={{ items: (userMenuItems as any[]).map(i => i.type === 'divider' ? i : { ...i, icon: i.icon, label: i.label, onClick: i.onClick }) }}
            placement="bottomRight"
            trigger={['click']}
          >
            <div className="flex cursor-pointer items-center gap-2 rounded-xl p-1 transition-all hover:bg-slate-100 pr-2">
              <Avatar src={user?.avatar_url} icon={<UserIcon className="h-4 w-4" />} className="bg-blue-100 text-blue-600 h-8 w-8" />
              <div className="hidden sm:block">
                <p className="text-xs font-bold text-slate-900 leading-none">{user?.full_name}</p>
                <p className="text-[10px] text-slate-500 mt-0.5 capitalize">{user?.role?.replace(/_/g, ' ')}</p>
              </div>
            </div>
          </Dropdown>
        </div>
      </Header>

      <Layout>
        {/* ── Main Content Area ──────────────────────────────────────────────── */}
        <Layout 
          className="transition-all duration-300 ease-in-out min-h-[calc(100vh-56px)]"
          style={{ 
            marginLeft: 0,
            marginRight: 0
          }}
        >
          <Content className="p-6">
            <div className="max-w-[1600px] mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              >
                {children}
              </motion.div>
            </div>
          </Content>
        </Layout>

        {/* ── Right Quick Panel Trigger (Pull Handle) ─────────────────────── */}
        <AnimatePresence>
          {!rightPanelOpen && (
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 20, opacity: 0 }}
              whileHover={{ x: -4 }}
              className="fixed right-0 top-1/2 -translate-y-1/2 z-40 group cursor-pointer"
              onClick={() => setRightPanelOpen(true)}
            >
              <div className="flex h-24 w-8 items-center justify-center rounded-l-2xl border border-r-0 border-amber-200 bg-amber-50 shadow-[-4px_0_12px_rgba(245,158,11,0.15)] transition-all group-hover:w-10 group-hover:bg-amber-100">
                <div className="flex flex-col items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-600 animate-pulse" />
                  <div className="flex flex-col gap-1">
                    <div className="h-1.5 w-[2px] bg-amber-300 rounded-full" />
                    <div className="h-4 w-[2px] bg-amber-300 rounded-full" />
                    <div className="h-1.5 w-[2px] bg-amber-300 rounded-full" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Right Quick Panel (Overlay) ────────────────────────────────────── */}
        <AnimatePresence>
          {rightPanelOpen && (
            <>
              {/* Backdrop for outside click */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setRightPanelOpen(false)}
                className="fixed inset-0 z-30 bg-slate-900/5 backdrop-blur-[1px]"
              />
              
              <motion.aside
                initial={{ x: 360, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 360, opacity: 0 }}
                transition={{ type: "spring", damping: 28, stiffness: 220 }}
                className="fixed top-14 right-0 bottom-0 z-40 w-[360px] bg-white border-l border-slate-200 shadow-2xl overflow-visible flex flex-col"
              >
                {/* Push Handle (Close) - Same place as Pull Handle */}
                <div 
                  className="absolute -left-8 top-1/2 -translate-y-1/2 w-8 h-24 bg-white border border-r-0 border-slate-200 rounded-l-2xl flex items-center justify-center cursor-pointer shadow-[-4px_0_12px_rgba(0,0,0,0.05)] hover:bg-slate-50 transition-colors group"
                  onClick={() => setRightPanelOpen(false)}
                >
                  <div className="flex flex-col items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-slate-600" />
                    <div className="flex flex-col gap-1">
                      <div className="h-1.5 w-[2px] bg-slate-200 group-hover:bg-slate-300 rounded-full" />
                      <div className="h-4 w-[2px] bg-slate-200 group-hover:bg-slate-300 rounded-full" />
                      <div className="h-1.5 w-[2px] bg-slate-200 group-hover:bg-slate-300 rounded-full" />
                    </div>
                  </div>
                </div>

                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-600" />
                    <span className="text-sm font-bold text-slate-900 uppercase tracking-wider">{t('header.action_center', 'Quick Panel')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge count={actionCenterCount} className="action-badge-pulse" />
                  </div>
                </div>

              <div className="flex-1 overflow-y-auto">
                <Tabs
                  activeKey={actionCenterTab}
                  onChange={setActionCenterTab}
                  size="small"
                  className="px-4"
                  items={actionCenterTabItems.map((it) => ({ key: it.key, label: it.label }))}
                />
                
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Recent Activity</span>
                    <Button type="text" size="small" className="text-[11px] text-blue-600 font-semibold p-0 h-auto">View All</Button>
                  </div>
                  
                  {actionCenterItems.length > 0 ? (
                    actionCenterItems.map((item, idx) => (
                      <div 
                        key={idx} 
                        className="group p-3 rounded-xl border border-slate-100 bg-white hover:border-blue-200 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
                      >
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                          <div>
                            <p className="text-sm text-slate-700 font-medium leading-tight">{item}</p>
                            <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                              <Clock3 className="h-3 w-3" /> 2 hours ago
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="py-12 text-center">
                      <CheckCircleOutlined className="text-4xl text-slate-200 mb-4" />
                      <p className="text-sm text-slate-500">No pending items</p>
                    </div>
                  )}

                  <div className="pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Reminders</span>
                    </div>
                    <div className="space-y-2">
                      <div className="p-3 rounded-xl bg-amber-50 border border-amber-100">
                        <div className="flex items-center gap-2 mb-1">
                          <CalendarIcon className="h-3.5 w-3.5 text-amber-600" />
                          <span className="text-xs font-bold text-amber-900">Follow up with Sarah</span>
                        </div>
                        <p className="text-[11px] text-amber-700/80">Pending feedback for the Senior Dev role</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-slate-100 bg-slate-50/30">
                <Button block className="rounded-lg h-9 text-xs font-bold border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200">
                  Manage Tasks
                </Button>
              </div>
            </motion.aside>
            </>
          )}
        </AnimatePresence>
      </Layout>

      {/* Global Modals for Quick Create */}
      <Drawer
        title={t('actions.create_job', 'Create New Job')}
        open={jobCreateOpen}
        onClose={() => setJobCreateOpen(false)}
        width={640}
        destroyOnClose
      >
        <JobCreateForm onSuccess={() => {
          setJobCreateOpen(false)
          antdMessage.success('Job created successfully')
        }} />
      </Drawer>

      <AddCandidateWorkflowModal 
        open={candidateCreateOpen} 
        onClose={() => setCandidateCreateOpen(false)} 
        sourceSurface="global_header"
        onCompleted={() => {
          setCandidateCreateOpen(false)
          antdMessage.success('Candidate added successfully')
        }}
      />

      <AttentionEngine />
      <GlobalDrawer />
    </Layout>
  )
}
