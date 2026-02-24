import React, { useState } from 'react';
import { Layout, Card, Button, Tabs, Typography, Space, Tag } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

const StrategyManagement = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('strategies');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // 系统默认策略
  const systemStrategies = [
    {
      id: 'double-line',
      name: '双线策略',
      type: 'system',
      description: '基于两条移动平均线的交叉信号，适用于趋势判断'
    },
    {
      id: 'single-pin',
      name: '单针策略',
      type: 'system',
      description: '基于K线形态的反转信号，适用于短期反转判断'
    },
    {
      id: 'brick-chart',
      name: '砖型图策略',
      type: 'system',
      description: '基于价格突破的趋势信号，适用于趋势跟踪'
    }
  ];

  // 用户自定义策略
  const customStrategies = [
    {
      id: 'custom-1',
      name: '自定义策略 1',
      type: 'custom',
      description: '（规划中，先不实现）用户可自定义策略组合'
    }
  ];

  // 系统指标
  const metrics = [
    {
      id: 'close-price',
      name: '当日收盘价',
      description: '股票当日交易结束时的价格',
      params: '参数：无'
    },
    {
      id: 'retail-cost',
      name: '散户成本线',
      description: '反映散户平均持仓成本',
      params: '参数：计算周期'
    },
    {
      id: 'main-cost',
      name: '大哥成本线',
      description: '反映主力资金平均持仓成本',
      params: '参数：计算周期'
    },
    {
      id: 'kdj',
      name: 'KDJ指标',
      description: '随机指标，用于判断股票超买超卖',
      params: '参数：周期、平滑参数'
    },
    {
      id: 'ma',
      name: 'MA指标',
      description: '移动平均线，反映价格趋势',
      params: '参数：周期'
    },
    {
      id: 'volume-ma',
      name: '成交量MA',
      description: '成交量移动平均线，反映成交量趋势',
      params: '参数：周期'
    },
    {
      id: 'macd',
      name: 'MACD指标',
      description: '指数平滑异同移动平均线，用于判断价格动能',
      params: '参数：快线周期、慢线周期、信号周期'
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
        <Title level={3} style={{ margin: 0 }}>策略管理</Title>
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
          <Title level={2} style={{ marginBottom: '32px' }}>策略与指标管理</Title>
          
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            style={{ marginBottom: '24px' }}
          >
            <TabPane tab="策略管理" key="strategies" />
            <TabPane tab="指标管理" key="metrics" />
          </Tabs>
          
          <Card style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            {activeTab === 'strategies' ? (
              <div>
                <div style={{ marginBottom: '32px' }}>
                  <Title level={4} style={{ marginBottom: '16px' }}>系统默认策略</Title>
                  <Space size="large" wrap>
                    {systemStrategies.map((strategy) => (
                      <Card
                        key={strategy.id}
                        hoverable
                        style={{ width: 320 }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <Title level={5} style={{ margin: 0 }}>{strategy.name}</Title>
                          <Tag color="blue">系统</Tag>
                        </div>
                        <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>{strategy.description}</Text>
                        <Space>
                          <Button size="small">详情</Button>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                </div>
                
                <div>
                  <Title level={4} style={{ marginBottom: '16px' }}>用户自定义策略</Title>
                  <Space size="large" wrap>
                    {customStrategies.map((strategy) => (
                      <Card
                        key={strategy.id}
                        hoverable
                        style={{ width: 320 }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <Title level={5} style={{ margin: 0 }}>{strategy.name}</Title>
                          <Tag color="green">自定义</Tag>
                        </div>
                        <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>{strategy.description}</Text>
                        <Space>
                          <Button size="small" type="default">编辑</Button>
                          <Button size="small" danger>删除</Button>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                </div>
              </div>
            ) : (
              <div>
                <Title level={4} style={{ marginBottom: '16px' }}>系统指标列表</Title>
                <Space size="large" wrap>
                  {metrics.map((metric) => (
                    <Card
                      key={metric.id}
                      hoverable
                      style={{ width: 280 }}
                    >
                      <Title level={5} style={{ marginBottom: '8px' }}>{metric.name}</Title>
                      <Text type="secondary" style={{ marginBottom: '12px', display: 'block', fontSize: '12px' }}>{metric.description}</Text>
                      <Text style={{ fontSize: '12px', color: '#595959' }}>{metric.params}</Text>
                    </Card>
                  ))}
                </Space>
              </div>
            )}
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default StrategyManagement;