import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider, Row, Col } from 'antd';
import TestGenerator from './components/TestGenerator';
import Header from './components/Header';
import { AppProvider } from './context/AppContext';
import './App.css';

const { Content, Footer } = Layout;

// Hero区域组件
const HeroSection = () => (
  <div style={{
    textAlign: 'center',
    padding: '4rem 0',
    color: 'white',
    maxWidth: '1400px',
    margin: '0 auto',
    paddingLeft: '20px',
    paddingRight: '20px'
  }}>
    <h1 style={{
      fontSize: '3.5rem',
      fontWeight: 800,
      marginBottom: '1rem',
      background: 'linear-gradient(45deg, #4ade80, #06b6d4)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    }}>
      智能测试，极速生成
    </h1>
    <p style={{
      fontSize: '1.25rem',
      opacity: 0.9,
      marginBottom: '2rem',
      maxWidth: '600px',
      marginLeft: 'auto',
      marginRight: 'auto'
    }}>
      基于AI技术的单元测试自动生成平台，支持多种编程语言，让测试开发更高效
    </p>

    {/* 工作流程步骤 */}
    <Row gutter={[16, 16]} justify="center" style={{ marginTop: '2rem' }}>
      {[
        { title: '1. 获取代码', desc: '从GitHub/GitLab获取代码' },
        { title: '2. AI分析', desc: '选择代码语言和AI模型' },
        { title: '3. 生成测试', desc: '生成单元测试代码' },
        { title: '4. 保存测试', desc: '保存测试结果' }
      ].map((step, index) => (
        <Col key={index} xs={24} sm={12} md={6}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)',
            borderRadius: '15px',
            padding: '1rem',
            minWidth: '200px',
            position: 'relative'
          }}>
            <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>{step.title}</h3>
            <p style={{ color: 'rgba(255, 255, 255, 0.8)', margin: 0 }}>{step.desc}</p>
          </div>
        </Col>
      ))}
    </Row>
  </div>
);

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
          colorPrimary: '#4ade80',
          borderRadius: 12,
        },
      }}
    >
      <AppProvider>
        <Router>
          <Layout className="layout">
            <Header />

            {/* Hero区域 */}
            <HeroSection />

            <Content style={{ padding: '0', marginTop: 0 }}>
              <div className="site-layout-content">
                <Routes>
                  <Route path="/" element={<TestGenerator />} />
                </Routes>
              </div>
            </Content>

            <Footer style={{
              textAlign: 'center',
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              backdropFilter: 'blur(10px)',
              border: 'none'
            }}>
              🤖 AI单元测试生成工具 © {new Date().getFullYear()} - 让测试开发更智能
            </Footer>
          </Layout>
        </Router>
      </AppProvider>
    </ConfigProvider>
  );
}

export default App;