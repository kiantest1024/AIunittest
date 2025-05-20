import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider } from 'antd';
import TestGenerator from './components/TestGenerator';
import Header from './components/Header';
import { AppProvider } from './context/AppContext';
import './App.css';

const { Content, Footer } = Layout;

/**
 * 应用主组件
 *
 * @returns {JSX.Element} 应用主组件
 */
function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <AppProvider>
        <Router>
          <Layout className="layout">
            <Header />
            <Content style={{ padding: '0 50px', marginTop: 64 }}>
              <div className="site-layout-content">
                <Routes>
                  <Route path="/" element={<TestGenerator />} />
                </Routes>
              </div>
            </Content>
            <Footer style={{ textAlign: 'center' }}>
              AI单元测试生成工具{new Date().getFullYear()}
            </Footer>
          </Layout>
        </Router>
      </AppProvider>
    </ConfigProvider>
  );
}

export default App;
