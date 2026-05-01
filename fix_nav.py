import re

with open('frontend/src/config/navigation.tsx', 'r') as f:
    content = f.read()

new_agency_config = '''export const agencySidebarConfig: NavItem[] = [
  { key: '/dashboard', label: 'Dashboard', icon: <DashboardOutlined /> },
  { key: '/agency/talent-pool', label: 'Talent Pool', icon: <DatabaseOutlined /> },
  { key: '/agency/pipeline', label: 'Pipeline', icon: <RocketOutlined /> },
  { key: '/agency/hotlists', label: 'Hotlists', icon: <ThunderboltOutlined /> },
  { key: '/agency/followups', label: 'Followups', icon: <CalendarOutlined /> },
  { key: '/agency/clients', label: 'Clients', icon: <BankOutlined /> },
  { key: '/agency/jobs', label: 'Jobs', icon: <ProjectOutlined /> },
  { key: '/agency/submissions', label: 'Submissions', icon: <CheckCircleOutlined /> },
  { key: '/settings?tab=users', label: 'Team', icon: <TeamOutlined /> },
  { key: '/agency/analytics', label: 'Analytics', icon: <BarChartOutlined /> },
  { key: '/settings', label: 'Settings', icon: <SettingOutlined /> },
]'''

content = re.sub(
    r'export const agencySidebarConfig: NavItem\[\] = \[.*?(?=\nexport const candidateSidebarConfig:)',
    new_agency_config,
    content,
    flags=re.DOTALL
)

with open('frontend/src/config/navigation.tsx', 'w') as f:
    f.write(content)
