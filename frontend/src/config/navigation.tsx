import {
  DashboardOutlined,
  RocketOutlined,
  ApartmentOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  FileDoneOutlined,
  ProjectOutlined,
  TeamOutlined,
  DatabaseOutlined,
  BankOutlined,
  BarChartOutlined,
  HistoryOutlined,
  UsergroupAddOutlined,
  ControlOutlined,
  SettingOutlined,
  IdcardOutlined,
} from '@ant-design/icons'
import { ReactNode } from 'react'

export interface NavItem {
  key: string
  label: ReactNode
  icon?: ReactNode
  permission?: string
  children?: NavItem[]
}

export const companySidebarConfig: NavItem[] = [
  { key: '/dashboard', label: 'Dashboard', icon: <DashboardOutlined /> },
  {
    key: 'work',
    label: 'Work',
    icon: <RocketOutlined />,
    children: [
      { key: '/candidates/active', label: 'Active Work', icon: <RocketOutlined /> },
      { key: '/pipeline', label: 'Pipeline', icon: <ApartmentOutlined /> },
      { key: '/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
      { key: '/offers', label: 'Offers', icon: <FileDoneOutlined /> },
      { key: '/approvals', label: 'Approvals', icon: <CheckCircleOutlined /> },
    ],
  },
  {
    key: 'records',
    label: 'Records',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/jobs', label: 'Jobs', icon: <ProjectOutlined /> },
      { key: '/candidates', label: 'Candidates', icon: <TeamOutlined />, permission: 'candidates.candidate.view' },
      { key: '/candidates/pools', label: 'Talent Pools', icon: <UsergroupAddOutlined /> },
    ],
  },
  {
    key: 'network',
    label: 'Network',
    icon: <BankOutlined />,
    children: [
      { key: '/agencies', label: 'Agencies', icon: <BankOutlined /> },
      { key: '/applications', label: 'Agency Submissions', icon: <CheckCircleOutlined /> },
    ],
  },
  {
    key: 'intelligence',
    label: 'Intelligence',
    icon: <BarChartOutlined />,
    children: [
      { key: '/analytics', label: 'Analytics', icon: <BarChartOutlined />, permission: 'analytics.dashboard.view' },
      { key: '/activity-log', label: 'Activity Log', icon: <HistoryOutlined /> },
    ],
  },
  {
    key: 'admin',
    label: 'Admin',
    icon: <ControlOutlined />,
    children: [
      { key: '/settings?tab=users', label: 'Team & Roles', icon: <TeamOutlined /> },
      { key: '/workflow-templates', label: 'Workflow Templates', icon: <ControlOutlined /> },
      { key: '/settings', label: 'Settings', icon: <SettingOutlined /> },
    ],
  },
]

export const agencySidebarConfig: NavItem[] = [
  { key: '/dashboard', label: 'Dashboard', icon: <DashboardOutlined /> },
  {
    key: 'work',
    label: 'Work',
    icon: <RocketOutlined />,
    children: [
      { key: '/candidates/active', label: 'Active Work', icon: <RocketOutlined /> },
      { key: '/pipeline', label: 'Pipeline', icon: <ApartmentOutlined /> },
      { key: '/agencies/my-submissions', label: 'Submissions', icon: <CheckCircleOutlined /> },
      { key: '/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
      { key: '/offers', label: 'Offers', icon: <FileDoneOutlined /> },
    ],
  },
  {
    key: 'records',
    label: 'Records',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/agencies/my-jobs', label: 'Jobs', icon: <ProjectOutlined /> },
      { key: '/candidates', label: 'Candidates', icon: <TeamOutlined />, permission: 'candidates.candidate.view' },
      { key: '/candidates/pools', label: 'Talent Pools', icon: <UsergroupAddOutlined /> },
    ],
  },
  {
    key: 'network',
    label: 'Network',
    icon: <BankOutlined />,
    children: [
      { key: '/agencies/my-clients', label: 'Clients', icon: <BankOutlined /> },
    ],
  },
  {
    key: 'intelligence',
    label: 'Intelligence',
    icon: <BarChartOutlined />,
    children: [
      { key: '/analytics', label: 'Analytics', icon: <BarChartOutlined />, permission: 'analytics.dashboard.view' },
      { key: '/activity-log', label: 'Activity Log', icon: <HistoryOutlined /> },
    ],
  },
  {
    key: 'admin',
    label: 'Admin',
    icon: <ControlOutlined />,
    children: [
      { key: '/settings?tab=users', label: 'Team & Roles', icon: <TeamOutlined /> },
      { key: '/workflow-templates', label: 'Workflow Templates', icon: <ControlOutlined /> },
      { key: '/settings', label: 'Settings', icon: <SettingOutlined /> },
    ],
  },
]

export const candidateSidebarConfig: NavItem[] = [
  { key: '/dashboard', label: 'Dashboard', icon: <DashboardOutlined /> },
  {
    key: 'work',
    label: 'Work',
    icon: <RocketOutlined />,
    children: [
      { key: '/candidate/applications', label: 'Applications', icon: <RocketOutlined /> },
      { key: '/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
    ],
  },
  {
    key: 'records',
    label: 'Records',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/candidate/jobs', label: 'Jobs', icon: <ProjectOutlined /> },
    ],
  },
  {
    key: 'admin',
    label: 'Admin',
    icon: <ControlOutlined />,
    children: [
      { key: '/passport', label: 'Passport', icon: <IdcardOutlined /> },
      { key: '/settings', label: 'Settings', icon: <SettingOutlined /> },
    ],
  },
]
