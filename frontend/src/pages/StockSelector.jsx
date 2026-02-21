import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const StockSelector = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '48px' }}>
      <Result
        status="info"
        title="选股工具"
        subTitle="选股功能开发中..."
        extra={[
          <Button type="primary" key="toolbox" onClick={() => navigate('/toolbox')}>
            返回工具箱
          </Button>,
        ]}
      />
    </div>
  );
};

export default StockSelector;
