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
  ThunderboltOutlined,
  PlusOutlined,
  AppstoreOutlined as LayoutGridOutlined,
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
  { key: '/hiring-command-center', label: 'Mission Control', icon: <ControlOutlined /> },
  {
    key: 'work',
    label: 'Work',
    icon: <RocketOutlined />,
    children: [
      { key: '/jobs', label: 'Jobs', icon: <ProjectOutlined /> },
      { key: '/pipeline', label: 'Job Pipeline Command Center', icon: <RocketOutlined /> },
      { key: '/candidates', label: 'Candidate Database', icon: <DatabaseOutlined /> },
      { key: '/candidates/active', label: 'Active Work', icon: <RocketOutlined /> },
      { key: '/candidates/leads', label: 'Lead Candidates', icon: <UsergroupAddOutlined /> },
      { key: '/candidates/pools', label: 'General Pools', icon: <UsergroupAddOutlined /> },
      { key: '/applications', label: 'Submissions Flow', icon: <CheckCircleOutlined /> },
      { key: '/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
      { key: '/messages', label: 'Communication History', icon: <HistoryOutlined /> },
      { key: '/offers', label: 'Offers', icon: <FileDoneOutlined /> },
      { key: '/approvals', label: 'Approvals', icon: <CheckCircleOutlined /> },
    ],
  },
  {
    key: 'icc',
    label: 'Interview Command Center',
    icon: <CalendarOutlined />,
    children: [
      { key: '/interviews', label: 'ICC Dashboard', icon: <CalendarOutlined /> },
      { key: '/interviews/registry', label: 'Interview Registry', icon: <DatabaseOutlined /> },
      { key: '/interviews/templates', label: 'Interview Templates', icon: <LayoutGridOutlined /> },
      { key: '/interviews/scorecards', label: 'Scorecards', icon: <FileDoneOutlined /> },
      { key: '/interviews/scheduling', label: 'Scheduling', icon: <CalendarOutlined /> },
      { key: '/interviews/bulk-scheduling', label: 'Bulk Scheduling', icon: <CalendarOutlined /> },
      { key: '/interviews/dashboard', label: 'Recruiter Interview Views', icon: <TeamOutlined /> },
      { key: '/interviews/queue', label: 'Recruiter Interview Queue', icon: <CheckCircleOutlined /> },
      { key: '/interviews/productivity', label: 'Recruiter Productivity', icon: <RocketOutlined /> },
      { key: '/interviews/ai', label: 'AI Interview Engine', icon: <ControlOutlined /> },
      { key: '/interviews/technical', label: 'Technical Engine', icon: <ProjectOutlined /> },
      { key: '/interviews/human', label: 'Human Interview Engine', icon: <TeamOutlined /> },
      { key: '/interviews/video', label: 'Video Interview Engine', icon: <CalendarOutlined /> },
      { key: '/interviews/group-discussion', label: 'Group Discussion Engine', icon: <UsergroupAddOutlined /> },
      { key: '/interviews/presentation-interview', label: 'Presentation Engine', icon: <FileDoneOutlined /> },
      { key: '/interviews/portfolio-review', label: 'Portfolio Engine', icon: <ProjectOutlined /> },
      { key: '/interviews/campus-hiring', label: 'Campus Hiring', icon: <BankOutlined /> },
      { key: '/interviews/walkin-drive', label: 'Walk-in Drive', icon: <RocketOutlined /> },
      { key: '/interviews/live', label: 'Live Interview Center', icon: <ControlOutlined /> },
      { key: '/interviews/automation', label: 'Interview Automation', icon: <ControlOutlined /> },
      { key: '/interviews/integrations', label: 'Interview Integrations', icon: <ControlOutlined /> },
      { key: '/interviews/prequalification', label: 'Pre-Qualification', icon: <FileDoneOutlined /> },
    ],
  },
  {
    key: 'hdc',
    label: 'Hiring Decision Center',
    icon: <CheckCircleOutlined />,
    children: [
      { key: '/hiring-decisions', label: 'Decision Dashboard', icon: <DashboardOutlined /> },
      { key: '/hiring-decisions/committee', label: 'Committee', icon: <TeamOutlined /> },
      { key: '/hiring-decisions/comparison', label: 'Candidate Comparison', icon: <UsergroupAddOutlined /> },
      { key: '/offers', label: 'Offers', icon: <FileDoneOutlined /> },
      { key: '/approvals', label: 'Approvals', icon: <CheckCircleOutlined /> },
      { key: '/hiring-decisions/offer-intelligence', label: 'Offer Intelligence', icon: <BarChartOutlined /> },
      { key: '/hiring-decisions/compensation', label: 'Compensation', icon: <BankOutlined /> },
      { key: '/hiring-decisions/negotiation', label: 'Negotiation', icon: <TeamOutlined /> },
      { key: '/hiring-decisions/offer-release', label: 'Offer Release', icon: <FileDoneOutlined /> },
      { key: '/hiring-decisions/offer-acceptance', label: 'Offer Acceptance', icon: <CheckCircleOutlined /> },
      { key: '/hiring-decisions/joining', label: 'Joining Tracking', icon: <RocketOutlined /> },
    ],
  },
  {
    key: 'intelligence-hub',
    label: 'Intelligence Hub',
    icon: <ThunderboltOutlined />,
    children: [
      { key: '/intelligence', label: 'Suggestions', icon: <DashboardOutlined /> },
      { key: '/intelligence/automations', label: 'Automations', icon: <ControlOutlined /> },
      { key: '/intelligence/executions', label: 'Executions', icon: <HistoryOutlined /> },
      { key: '/intelligence/failures', label: 'Failures', icon: <CheckCircleOutlined /> },
      { key: '/intelligence/prompts', label: 'Prompts', icon: <LayoutGridOutlined /> },
      { key: '/intelligence/settings', label: 'Settings', icon: <SettingOutlined /> },
    ],
  },
  {
    key: 'records',
    label: 'Records',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/jobs/create', label: 'Create Job', icon: <PlusOutlined /> },
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
      { key: '/hiring-intelligence', label: 'Hiring Intelligence', icon: <ThunderboltOutlined /> },
      { key: '/recruiter-intelligence', label: 'Recruiter Intelligence', icon: <TeamOutlined /> },
      { key: '/analytics', label: 'Analytics', icon: <BarChartOutlined />, permission: 'analytics.dashboard.view' },
      { key: '/activity-log', label: 'Activity Log', icon: <HistoryOutlined /> },
      { key: '/notifications', label: 'Notifications', icon: <CheckCircleOutlined /> },
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
      { key: '/jobs', label: 'All Jobs', icon: <ProjectOutlined /> },
      { key: '/agencies/my-submissions', label: 'Submissions', icon: <CheckCircleOutlined /> },
      { key: '/candidates/active', label: 'Active Work', icon: <RocketOutlined /> },
      { key: '/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
      { key: '/interviews/automation', label: 'Interview Automation', icon: <ControlOutlined /> },
      { key: '/interviews/integrations', label: 'Interview Integrations', icon: <ControlOutlined /> },
      { key: '/offers', label: 'Offers', icon: <FileDoneOutlined /> },
    ],
  },
  {
    key: 'icc',
    label: 'Interview Command Center',
    icon: <CalendarOutlined />,
    children: [
      { key: '/interviews', label: 'ICC Dashboard', icon: <CalendarOutlined /> },
      { key: '/interviews/registry', label: 'Interview Registry', icon: <DatabaseOutlined /> },
      { key: '/interviews/templates', label: 'Interview Templates', icon: <FileDoneOutlined /> },
      { key: '/interviews/scorecards', label: 'Scorecards', icon: <FileDoneOutlined /> },
      { key: '/interviews/scheduling', label: 'Scheduling', icon: <CalendarOutlined /> },
      { key: '/interviews/bulk-scheduling', label: 'Bulk Scheduling', icon: <CalendarOutlined /> },
      { key: '/interviews/dashboard', label: 'Recruiter Interview Views', icon: <TeamOutlined /> },
      { key: '/interviews/queue', label: 'Recruiter Interview Queue', icon: <CheckCircleOutlined /> },
      { key: '/interviews/productivity', label: 'Recruiter Productivity', icon: <RocketOutlined /> },
      { key: '/interviews/campus-hiring', label: 'Campus Hiring', icon: <BankOutlined /> },
      { key: '/interviews/walkin-drive', label: 'Walk-in Drive', icon: <RocketOutlined /> },
    ],
  },
  {
    key: 'hdc',
    label: 'Hiring Decision Center',
    icon: <CheckCircleOutlined />,
    children: [
      { key: '/hiring-decisions', label: 'Decision Dashboard', icon: <DashboardOutlined /> },
      { key: '/hiring-decisions/committee', label: 'Committee', icon: <TeamOutlined /> },
      { key: '/hiring-decisions/comparison', label: 'Candidate Comparison', icon: <UsergroupAddOutlined /> },
      { key: '/hiring-decisions/offer-intelligence', label: 'Offer Intelligence', icon: <BarChartOutlined /> },
      { key: '/hiring-decisions/compensation', label: 'Compensation', icon: <BankOutlined /> },
      { key: '/hiring-decisions/negotiation', label: 'Negotiation', icon: <TeamOutlined /> },
      { key: '/hiring-decisions/offer-release', label: 'Offer Release', icon: <FileDoneOutlined /> },
      { key: '/hiring-decisions/offer-acceptance', label: 'Offer Acceptance', icon: <CheckCircleOutlined /> },
      { key: '/hiring-decisions/joining', label: 'Joining Tracking', icon: <RocketOutlined /> },
    ],
  },
  {
    key: 'intelligence-hub',
    label: 'Intelligence Hub',
    icon: <ThunderboltOutlined />,
    children: [
      { key: '/intelligence', label: 'Suggestions', icon: <DashboardOutlined /> },
      { key: '/intelligence/automations', label: 'Automations', icon: <ControlOutlined /> },
      { key: '/intelligence/executions', label: 'Executions', icon: <HistoryOutlined /> },
      { key: '/intelligence/failures', label: 'Failures', icon: <CheckCircleOutlined /> },
      { key: '/intelligence/prompts', label: 'Prompts', icon: <LayoutGridOutlined /> },
      { key: '/intelligence/settings', label: 'Settings', icon: <SettingOutlined /> },
    ],
  },
  {
    key: 'records',
    label: 'Records',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/jobs/create', label: 'Create Job', icon: <PlusOutlined /> },
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
      { key: '/hiring-intelligence', label: 'Hiring Intelligence', icon: <ThunderboltOutlined /> },
      { key: '/recruiter-intelligence', label: 'Recruiter Intelligence', icon: <TeamOutlined /> },
      { key: '/analytics', label: 'Analytics', icon: <BarChartOutlined />, permission: 'analytics.dashboard.view' },
      { key: '/activity-log', label: 'Activity Log', icon: <HistoryOutlined /> },
      { key: '/notifications', label: 'Notifications', icon: <CheckCircleOutlined /> },
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
  { key: '/candidate/dashboard', label: 'Dashboard', icon: <DashboardOutlined /> },
  {
    key: 'work',
    label: 'Work',
    icon: <RocketOutlined />,
    children: [
      { key: '/candidate/applications', label: 'Applications', icon: <RocketOutlined /> },
      { key: '/candidate/interviews', label: 'Interviews', icon: <CalendarOutlined /> },
      { key: '/candidate/jobs', label: 'Browse Jobs', icon: <ProjectOutlined /> },
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
