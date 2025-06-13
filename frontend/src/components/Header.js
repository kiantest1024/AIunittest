import React, { useState } from 'react';
import { Layout, Menu, Button, Space } from 'antd';
import { HomeOutlined, ThunderboltOutlined, BookOutlined, ApiOutlined, SettingOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import AIConfigModal from './AIConfigModal';

const { Header: AntHeader } = Layout;

const Header = () => {
  const [aiConfigVisible, setAiConfigVisible] = useState(false);

  const handleConfigUpdated = () => {
    // 配置更新后的回调，刷新页面以重新加载模型配置
    window.location.reload();
  };

  return (
    <>
      <AntHeader className="app-header" style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo" style={{ marginRight: '20px' }}>
            AI单元测试生成工具
          </div>
          <div className="menu-container">
            <Menu
              theme="dark"
              mode="horizontal"
              defaultSelectedKeys={['1']}
              style={{ lineHeight: '64px', border: 'none', padding: '0 10px' }}
              items={[
                {
                  key: '1',
                  icon: <HomeOutlined style={{ fontSize: '16px', marginRight: '5px' }} />,
                  label: <Link to="/" style={{ fontSize: '16px', color: 'inherit' }}>首页</Link>,
                },
                {
                  key: '2',
                  icon: <ThunderboltOutlined style={{ fontSize: '16px', marginRight: '5px' }} />,
                  label: <span style={{ fontSize: '16px' }}>功能</span>,
                },
                {
                  key: '3',
                  icon: <BookOutlined style={{ fontSize: '16px', marginRight: '5px' }} />,
                  label: <span style={{ fontSize: '16px' }}>文档</span>,
                },
                {
                  key: '4',
                  icon: <ApiOutlined style={{ fontSize: '16px', marginRight: '5px' }} />,
                  label: <span style={{ fontSize: '16px' }}>API</span>,
                }
              ]}
            />
          </div>
        </div>

        <Space>
          <Button
            type="primary"
            icon={<SettingOutlined />}
            onClick={() => setAiConfigVisible(true)}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              borderColor: 'rgba(255, 255, 255, 0.3)',
              color: 'white'
            }}
          >
            AI配置
          </Button>
        </Space>
      </AntHeader>

      <AIConfigModal
        visible={aiConfigVisible}
        onCancel={() => setAiConfigVisible(false)}
        onConfigUpdated={handleConfigUpdated}
      />
    </>
  );
};

export default Header;
