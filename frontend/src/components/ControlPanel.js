import React from 'react';
import { Row, Col, Select, Button, Upload, Tooltip } from 'antd';
import { UploadOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

/**
 * 控制面板组件
 *
 * @param {string} language - 当前选择的编程语言
 * @param {string} model - 当前选择的AI模型
 * @param {Array} languages - 支持的编程语言列表
 * @param {Array} models - 支持的AI模型列表
 * @param {function} onLanguageChange - 语言变更回调函数
 * @param {function} onModelChange - 模型变更回调函数
 * @param {function} onFileUpload - 文件上传回调函数
 * @param {function} onGenerateTests - 生成测试回调函数
 * @param {boolean} loading - 是否正在加载
 * @param {Object} acceptedFileTypes - 接受的文件类型
 * @returns {JSX.Element} 控制面板组件
 */
const ControlPanel = ({
  language,
  model,
  languages,
  models,
  onLanguageChange,
  onModelChange,
  onFileUpload,
  onGenerateTests,
  loading,
  acceptedFileTypes = {}
}) => {
  // 获取当前语言的文件扩展名
  const getAcceptedFileTypes = () => {
    if (language && acceptedFileTypes[language]) {
      return acceptedFileTypes[language];
    }
    return Object.values(acceptedFileTypes).flat().join(',');
  };

  // 格式化模型名称显示
  const formatModelName = (modelName) => {
    return modelName.replace(/_/g, ' ').toUpperCase();
  };

  // 获取模型提示信息
  const getModelTooltip = (modelName) => {
    const tooltips = {
      'openai_gpt35': '需要 OpenAI API 密钥',
      'openai_gpt4': '需要 OpenAI API 密钥',
      'google_gemini': '需要 Google API 密钥',
      'anthropic_claude': '需要 Anthropic API 密钥',
      'xai_grok': '需要 xAI Grok API 密钥',
      'deepseek': '需要 DeepSeek API 密钥',
    };

    return tooltips[modelName] || '选择此模型';
  };

  // 格式化语言名称显示
  const formatLanguageName = (langName) => {
    return langName.charAt(0).toUpperCase() + langName.slice(1);
  };

  return (
    <Row gutter={16}>
      <Col span={8}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>
            编程语言:
            <Tooltip title="选择您的代码的编程语言">
              <QuestionCircleOutlined style={{ marginLeft: 8 }} />
            </Tooltip>
          </label>
          <Select
            value={language}
            onChange={onLanguageChange}
            style={{ width: '100%' }}
            placeholder="选择编程语言"
          >
            {languages.map(lang => (
              <Option key={lang} value={lang}>{formatLanguageName(lang)}</Option>
            ))}
          </Select>
        </div>
      </Col>
      <Col span={8}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>
            AI模型:
            <Tooltip title="选择用于生成测试的AI模型">
              <QuestionCircleOutlined style={{ marginLeft: 8 }} />
            </Tooltip>
          </label>
          <Select
            value={model}
            onChange={onModelChange}
            style={{ width: '100%' }}
            placeholder="选择AI模型"
          >
            {models.map(modelName => (
              <Option key={modelName} value={modelName}>
                <Tooltip title={getModelTooltip(modelName)}>
                  <div>{formatModelName(modelName)}</div>
                </Tooltip>
              </Option>
            ))}
          </Select>
          <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
            注意: 每个模型都需要相应的 API 密钥，请在后端 .env 文件中设置
          </div>
        </div>
      </Col>
      <Col span={8}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>
            操作:
            <Tooltip title="生成单元测试用例">
              <QuestionCircleOutlined style={{ marginLeft: 8 }} />
            </Tooltip>
          </label>
          <Button
            type="primary"
            onClick={onGenerateTests}
            loading={loading}
            style={{ width: '100%' }}
          >
            生成用例
          </Button>
        </div>
      </Col>
    </Row>
  );
};

export default ControlPanel;
