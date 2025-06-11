import React from 'react';
import { Card } from 'antd';
import { Editor } from '@monaco-editor/react';

/**
 * 代码编辑器组件
 *
 * @param {string} code - 代码内容
 * @param {string} language - 编程语言
 * @param {function} onChange - 代码变更回调函数
 * @param {boolean} readOnly - 是否只读
 * @param {string} height - 编辑器高度
 * @returns {JSX.Element} 代码编辑器组件
 */
const CodeEditor = ({
  code,
  language,
  onChange,
  readOnly = false,
  height = "500px"
}) => {
  // 处理编辑器加载
  const handleEditorDidMount = (editor, monaco) => {
    // 可以在这里添加编辑器加载后的逻辑
    editor.focus();
  };

  // 处理编辑器错误
  const handleEditorError = (error) => {
    console.error('Editor error:', error);
  };

  // 添加调试日志
  console.log('CodeEditor rendering with:', {
    language,
    codeLength: code ? code.length : 0,
    codePreview: code ? code.substring(0, 100) + '...' : 'No code',
    readOnly
  });

  return (
    <Card style={{
      width: '100%',
      maxWidth: '100%',
      overflow: 'hidden',
      boxSizing: 'border-box'
    }}>
      {code ? (
        <Editor
          height={height}
          width="100%"
          language={language}
          value={code}
          onChange={onChange}
          onMount={handleEditorDidMount}
          onError={handleEditorError}
          options={{
            readOnly,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            fontSize: 14,
            tabSize: 2,
            wordWrap: 'on',
            wordWrapColumn: 80,
            wordWrapMinified: true,
            wrappingIndent: 'indent',
            scrollbar: {
              horizontal: 'auto',
              vertical: 'auto',
              horizontalScrollbarSize: 8,
              verticalScrollbarSize: 8
            },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            overviewRulerBorder: false
          }}
        />
      ) : (
        <div style={{
          height,
          width: '100%',
          maxWidth: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
          boxSizing: 'border-box'
        }}>
          请选择或输入代码
        </div>
      )}
    </Card>
  );
};

export default CodeEditor;
