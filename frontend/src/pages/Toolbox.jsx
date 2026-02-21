import React from 'react';
import { Layout, Button, Card, Space, Typography } from 'antd';
import { LogoutOutlined, StockOutlined, LineChartOutlined, BarChartOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const Toolbox = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const tools = [
    {
      id: 'stock-selector',
      title: '选股工具',
      description: '智能选股分析',
      icon: <StockOutlined style={{ fontSize: '48px', color: '#1890ff' }} />,
      onClick: () => navigate('/stock-selector')
    },
    {
      id: 'batch-backtest',
      title: '批量回测工具',
      description: '策略回测分析',
      icon: <LineChartOutlined style={{ fontSize: '48px', color: '#52c41a' }} />,
      onClick: () => navigate('/batch-backtest')
    },
    {
      id: 'single-backtest',
      title: '个股回测工具',
      description: '个股买卖点分析',
      icon: <BarChartOutlined style={{ fontSize: '48px', color: '#fa8c16' }} />,
      onClick: () => navigate('/single-backtest')
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Title level={3} style={{ margin: 0 }}>个人工具箱</Title>
        <Button
          type="primary"
          danger
          icon={<LogoutOutlined />}
          onClick={handleLogout}
        >
          退出登录
        </Button>
      </Header>
      <Content style={{ padding: '48px', background: '#f0f2f5' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Title level={2} style={{ marginBottom: '32px' }}>欢迎使用股票交易系统</Title>
          <Space size="large" wrap>
            {tools.map((tool) => (
              <Card
                key={tool.id}
                hoverable
                style={{
                  width: 280,
                  height: 320,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
                onClick={tool.onClick}
              >
                <div style={{ marginBottom: '24px' }}>
                  {tool.icon}
                </div>
                <Title level={4} style={{ marginBottom: '12px' }}>{tool.title}</Title>
                <Text type="secondary">{tool.description}</Text>
              </Card>
            ))}
          </Space>
        </div>
      </Content>
    </Layout>
  );
};

export default Toolbox;
