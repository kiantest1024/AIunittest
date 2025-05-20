import React from 'react';
import { Layout, Menu } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Header: AntHeader } = Layout;

const Header = () => {
  return (
    <AntHeader className="app-header" style={{ position: 'fixed', zIndex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'flex-start', padding: '0' }}>
      <div className="logo">
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
              label: <Link to="/" style={{ fontSize: '16px' }}>首页</Link>,
            }
          ]}
        />
      </div>
    </AntHeader>
  );
};

export default Header;
