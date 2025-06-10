import React from 'react';
import { Spin, Progress } from 'antd';
import { LoadingOutlined, CloudDownloadOutlined, CloudUploadOutlined } from '@ant-design/icons';

const LoadingIndicator = ({ loading, type = 'default', progress, message, children }) => {
  if (!loading) {
    return children || null;
  }

  const getIcon = () => {
    switch (type) {
      case 'download':
        return <CloudDownloadOutlined style={{ fontSize: 24 }} spin />;
      case 'upload':
        return <CloudUploadOutlined style={{ fontSize: 24 }} spin />;
      default:
        return <LoadingOutlined style={{ fontSize: 24 }} spin />;
    }
  };

  const getMessage = () => {
    switch (type) {
      case 'download':
        return message || '正在获取数据...';
      case 'upload':
        return message || '正在上传数据...';
      case 'clone':
        return message || '正在克隆仓库...';
      default:
        return message || '加载中...';
    }
  };

  return (
    <div>
      {children}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '20px',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderRadius: '4px',
        marginTop: '16px'
      }}>
        <Spin indicator={getIcon()} />
        <div style={{ marginTop: 16, marginBottom: progress ? 8 : 0 }}>
          {getMessage()}
        </div>
        {progress !== undefined && (
          <Progress
            percent={Math.round(progress)}
            status="active"
            style={{ width: 200 }}
          />
        )}
      </div>
    </div>
  );
};

// 预定义的加载状态类型
LoadingIndicator.Type = {
  DEFAULT: 'default',
  DOWNLOAD: 'download',
  UPLOAD: 'upload',
  CLONE: 'clone'
};

export default LoadingIndicator;
