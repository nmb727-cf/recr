import { useState } from 'react'
import { Button, Card, Col, Form, Input, Row, Select, Typography, message, Steps, Divider, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import { organisationApi } from '@/api/organisation'
import { useAuth } from '@/hooks/useAuth'
import { COUNTRIES, TIMEZONES } from '@/utils/locale'
import { 
  BankOutlined, 
  EnvironmentOutlined, 
  ClusterOutlined, 
  TeamOutlined,
  PlusOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  GlobalOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

export default function CompanyOnboarding() {
  const [currentStep, setCurrentStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { fetchMe } = useAuth()

  // State for hierarchy data
  const [locations, setLocations] = useState([{ name: 'Headquarters', city: '', is_headquarters: true }])
  const [departments, setDepartments] = useState([{ name: 'Engineering' }, { name: 'Human Resources' }, { name: 'Sales' }])
  const [teams, setTeams] = useState([{ name: 'Backend Team', department_name: 'Engineering', location_name: 'Headquarters' }])

  const next = () => setCurrentStep(currentStep + 1)
  const prev = () => setCurrentStep(currentStep - 1)

  const onFinish = async (values: any) => {
    setSaving(true)
    try {
      // 1. Update Profile
      await organisationApi.updateProfile({
        name: values.name,
        industry: values.industry,
        website: values.website,
        size_range: values.size_range,
        country_code: values.country_code,
        primary_language: values.primary_language,
        primary_currency: values.primary_currency,
        timezone: values.timezone,
        cin: values.cin,
        gst_number: values.gst_number,
      })

      // 2. Setup Hierarchy
      await organisationApi.setupHierarchy({
        locations,
        departments,
        teams
      })

      message.success('Enterprise setup completed successfully')
      await fetchMe()
      navigate('/dashboard', { replace: true })
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Failed to complete onboarding')
    } finally {
      setSaving(false)
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Organisation Profile
        return (
          <div className="space-y-6">
            <Title level={4}>Basic Information</Title>
            <Form.Item name="name" label="Company Name" rules={[{ required: true }]}>
              <Input size="large" prefix={<BankOutlined />} placeholder="Acme Corp" />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="industry" label="Industry" rules={[{ required: true }]}>
                  <Input size="large" placeholder="e.g. Technology" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="size_range" label="Company Size">
                  <Select size="large">
                    <Select.Option value="1-10">1-10</Select.Option>
                    <Select.Option value="11-50">11-50</Select.Option>
                    <Select.Option value="51-200">51-200</Select.Option>
                    <Select.Option value="201-500">201-500</Select.Option>
                    <Select.Option value="500+">500+</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="country_code" label="Country" rules={[{ required: true }]}>
                  <Select 
                    size="large" 
                    showSearch 
                    options={COUNTRIES.map(c => ({ label: c.name, value: c.code }))} 
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="primary_language" label="Language" rules={[{ required: true }]}>
                  <Select size="large">
                    <Select.Option value="en">English</Select.Option>
                    <Select.Option value="hi">Hindi</Select.Option>
                    <Select.Option value="es">Spanish</Select.Option>
                    <Select.Option value="fr">French</Select.Option>
                    <Select.Option value="de">German</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="primary_currency" label="Currency" rules={[{ required: true }]}>
                  <Select size="large">
                    <Select.Option value="INR">INR (₹)</Select.Option>
                    <Select.Option value="USD">USD ($)</Select.Option>
                    <Select.Option value="GBP">GBP (£)</Select.Option>
                    <Select.Option value="EUR">EUR (€)</Select.Option>
                    <Select.Option value="AED">AED</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="timezone" label="Timezone" rules={[{ required: true }]}>
              <Select size="large" showSearch options={TIMEZONES} />
            </Form.Item>

            <Divider orientation="left">Statutory Details (Optional)</Divider>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="cin" label="CIN / Registration No.">
                  <Input size="large" placeholder="Registration ID" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="gst_number" label="GST / Tax ID">
                  <Input size="large" placeholder="Tax Identification" />
                </Form.Item>
              </Col>
            </Row>
          </div>
        )

      case 1: // Locations
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <Title level={4}>Office Locations</Title>
              <Button 
                type="dashed" 
                icon={<PlusOutlined />} 
                onClick={() => setLocations([...locations, { name: '', city: '', is_headquarters: false }])}
              >
                Add Location
              </Button>
            </div>
            <Paragraph type="secondary">Define your physical offices or remote hubs.</Paragraph>
            {locations.map((loc, i) => (
              <Card key={i} size="small" className="mb-4 bg-slate-50 border-slate-200">
                <Row gutter={16} align="middle">
                  <Col span={10}>
                    <Input 
                      placeholder="Location Name (e.g. London Office)" 
                      value={loc.name} 
                      onChange={e => {
                        const newLocs = [...locations]
                        newLocs[i].name = e.target.value
                        setLocations(newLocs)
                      }}
                    />
                  </Col>
                  <Col span={10}>
                    <Input 
                      placeholder="City" 
                      value={loc.city} 
                      onChange={e => {
                        const newLocs = [...locations]
                        newLocs[i].city = e.target.value
                        setLocations(newLocs)
                      }}
                    />
                  </Col>
                  <Col span={4}>
                    <Button 
                      danger 
                      type="text" 
                      icon={<DeleteOutlined />} 
                      onClick={() => setLocations(locations.filter((_, idx) => idx !== i))}
                      disabled={locations.length === 1}
                    />
                  </Col>
                </Row>
              </Card>
            ))}
          </div>
        )

      case 2: // Departments
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <Title level={4}>Functional Departments</Title>
              <Button 
                type="dashed" 
                icon={<PlusOutlined />} 
                onClick={() => setDepartments([...departments, { name: '' }])}
              >
                Add Department
              </Button>
            </div>
            <Paragraph type="secondary">Create the primary departments in your organization.</Paragraph>
            {departments.map((dept, i) => (
              <div key={i} className="flex gap-2 mb-3">
                <Input 
                  size="large"
                  placeholder="e.g. Engineering, Sales, Product" 
                  value={dept.name} 
                  onChange={e => {
                    const newDepts = [...departments]
                    newDepts[i].name = e.target.value
                    setDepartments(newDepts)
                  }}
                  prefix={<ClusterOutlined className="text-slate-400" />}
                />
                <Button 
                  danger 
                  className="h-11"
                  icon={<DeleteOutlined />} 
                  onClick={() => setDepartments(departments.filter((_, idx) => idx !== i))}
                  disabled={departments.length === 1}
                />
              </div>
            ))}
          </div>
        )

      case 3: // Teams
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <Title level={4}>Team Structure</Title>
              <Button 
                type="dashed" 
                icon={<PlusOutlined />} 
                onClick={() => setTeams([...teams, { name: '', department_name: departments[0]?.name, location_name: locations[0]?.name }])}
              >
                Add Team
              </Button>
            </div>
            <Paragraph type="secondary">Map your squads/teams to departments and locations.</Paragraph>
            {teams.map((team, i) => (
              <Card key={i} size="small" className="mb-4 bg-slate-50 border-slate-200">
                <Row gutter={12} align="middle">
                  <Col span={8}>
                    <Input 
                      placeholder="Team Name (e.g. API SRE)" 
                      value={team.name} 
                      onChange={e => {
                        const newTeams = [...teams]
                        newTeams[i].name = e.target.value
                        setTeams(newTeams)
                      }}
                    />
                  </Col>
                  <Col span={7}>
                    <Select 
                      className="w-full"
                      placeholder="Dept" 
                      value={team.department_name}
                      options={departments.map(d => ({ label: d.name, value: d.name }))}
                      onChange={val => {
                        const newTeams = [...teams]
                        newTeams[i].department_name = val
                        setTeams(newTeams)
                      }}
                    />
                  </Col>
                  <Col span={7}>
                    <Select 
                      className="w-full"
                      placeholder="Location" 
                      value={team.location_name}
                      options={locations.map(l => ({ label: l.name, value: l.name }))}
                      onChange={val => {
                        const newTeams = [...teams]
                        newTeams[i].location_name = val
                        setTeams(newTeams)
                      }}
                    />
                  </Col>
                  <Col span={2}>
                    <Button 
                      danger 
                      type="text" 
                      icon={<DeleteOutlined />} 
                      onClick={() => setTeams(teams.filter((_, idx) => idx !== i))}
                      disabled={teams.length === 1}
                    />
                  </Col>
                </Row>
              </Card>
            ))}
          </div>
        )

      case 4: // Summary
        return (
          <div className="text-center py-8 space-y-6">
            <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a' }} />
            <div>
              <Title level={3}>Ready to Launch</Title>
              <Text type="secondary">
                We've configured your enterprise profile with {locations.length} locations, 
                {departments.length} departments, and {teams.length} teams.
              </Text>
            </div>
            <Divider />
            <div className="text-left bg-slate-50 p-6 rounded-2xl border border-slate-200">
              <div className="mb-4">
                <Text strong>Hierarchy Summary:</Text>
              </div>
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>Office Hubs:</Text>
                  <Text strong>{locations.map(l => l.name).join(', ')}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>Functional Units:</Text>
                  <Text strong>{departments.map(d => d.name).join(', ')}</Text>
                </div>
              </Space>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="text-center mb-12">
        <Title level={2}>Enterprise Onboarding</Title>
        <Paragraph type="secondary">Complete your organization's hierarchy to unlock full role management.</Paragraph>
      </div>

      <Steps current={currentStep} className="mb-12">
        <Step title="Profile" icon={<GlobalOutlined />} />
        <Step title="Locations" icon={<EnvironmentOutlined />} />
        <Step title="Departments" icon={<ClusterOutlined />} />
        <Step title="Teams" icon={<TeamOutlined />} />
        <Step title="Finish" icon={<CheckCircleOutlined />} />
      </Steps>

      <Card bordered={false} className="shadow-lg rounded-3xl border border-slate-100 overflow-hidden">
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={onFinish}
          initialValues={{
            country_code: 'IN',
            primary_language: 'en',
            primary_currency: 'INR',
            timezone: 'Asia/Kolkata',
            size_range: '11-50'
          }}
        >
          <div className="p-8">
            {renderStepContent()}
          </div>

          <div className="bg-slate-50 p-6 flex justify-between items-center border-t border-slate-100">
            <Button 
              size="large" 
              onClick={prev} 
              disabled={currentStep === 0 || saving}
              className="rounded-xl px-8"
            >
              Back
            </Button>
            
            {currentStep < 4 ? (
              <Button 
                type="primary" 
                size="large" 
                onClick={next}
                className="rounded-xl px-12 bg-blue-600 border-none shadow-md"
              >
                Continue
              </Button>
            ) : (
              <Button 
                type="primary" 
                size="large" 
                htmlType="submit"
                loading={saving}
                className="rounded-xl px-12 bg-green-600 border-none shadow-md"
              >
                Launch Workspace
              </Button>
            )}
          </div>
        </Form>
      </Card>
    </div>
  )
}
