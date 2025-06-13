import React, { Suspense } from 'react';
import { Spin, Card } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

/**
 * 懒加载包装器组件
 * 为懒加载的组件提供加载状态显示
 */
const LazyLoader = ({ children, fallback, minHeight = '200px' }) => {
  const defaultFallback = (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight,
      padding: '40px'
    }}>
      <Card style={{ textAlign: 'center', border: 'none', boxShadow: 'none' }}>
        <Spin 
          indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />}
          size="large"
        />
        <div style={{ marginTop: '16px', color: '#666' }}>
          正在加载组件...
        </div>
      </Card>
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      {children}
    </Suspense>
  );
};

/**
 * 骨架屏加载组件
 */
export const SkeletonLoader = ({ rows = 3, avatar = false, title = true }) => {
  return (
    <div style={{ padding: '20px' }}>
      {avatar && (
        <div style={{ 
          width: '40px', 
          height: '40px', 
          borderRadius: '50%', 
          background: '#f0f0f0',
          marginBottom: '16px'
        }} />
      )}
      {title && (
        <div style={{ 
          width: '60%', 
          height: '20px', 
          background: '#f0f0f0',
          borderRadius: '4px',
          marginBottom: '16px'
        }} />
      )}
      {Array.from({ length: rows }).map((_, index) => (
        <div 
          key={index}
          style={{ 
            width: `${Math.random() * 40 + 60}%`, 
            height: '16px', 
            background: '#f0f0f0',
            borderRadius: '4px',
            marginBottom: '12px'
          }} 
        />
      ))}
    </div>
  );
};

/**
 * 代码编辑器加载组件
 */
export const CodeEditorLoader = () => {
  return (
    <div style={{ 
      border: '1px solid #d9d9d9',
      borderRadius: '6px',
      padding: '16px',
      background: '#fafafa',
      minHeight: '300px'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginBottom: '16px'
      }}>
        <div style={{ 
          width: '12px', 
          height: '12px', 
          borderRadius: '50%', 
          background: '#ff5f56',
          marginRight: '8px'
        }} />
        <div style={{ 
          width: '12px', 
          height: '12px', 
          borderRadius: '50%', 
          background: '#ffbd2e',
          marginRight: '8px'
        }} />
        <div style={{ 
          width: '12px', 
          height: '12px', 
          borderRadius: '50%', 
          background: '#27ca3f'
        }} />
      </div>
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px', color: '#666' }}>
          正在加载代码编辑器...
        </div>
      </div>
    </div>
  );
};

export default LazyLoader;
