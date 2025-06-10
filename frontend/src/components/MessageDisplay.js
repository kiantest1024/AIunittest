import React from 'react';
import { Alert } from 'antd';

const MessageDisplay = ({ error, warning, info, onErrorClear }) => {
  if (!error && !warning && !info) {
    return null;
  }

  return (
    <div style={{ marginBottom: 16 }}>
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          closable
          onClose={onErrorClear}
          style={{ marginBottom: 8 }}
        />
      )}
      {warning && (
        <Alert
          message="警告"
          description={warning}
          type="warning"
          closable
          style={{ marginBottom: 8 }}
        />
      )}
      {info && (
        <Alert
          message="信息"
          description={info}
          type="info"
          closable
          style={{ marginBottom: 8 }}
        />
      )}
    </div>
  );
};

export default MessageDisplay;
