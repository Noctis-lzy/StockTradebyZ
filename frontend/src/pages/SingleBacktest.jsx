import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const SingleBacktest = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '48px' }}>
      <Result
        status="info"
        title="个股回测工具"
        subTitle="个股回测功能开发中..."
        extra={[
          <Button type="primary" key="toolbox" onClick={() => navigate('/toolbox')}>
            返回工具箱
          </Button>,
        ]}
      />
    </div>
  );
};

export default SingleBacktest;
