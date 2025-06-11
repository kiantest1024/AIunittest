import { Select, Button, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

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
  onGenerateTests,
  loading
}) => {

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
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: '1rem',
      marginBottom: '1.5rem'
    }}>
      {/* 编程语言选择 */}
      <div className="form-group-modern">
        <label className="form-label-modern" style={{
          display: 'block',
          fontWeight: 600,
          marginBottom: '0.5rem',
          color: '#374151'
        }}>
          💻 编程语言
          <Tooltip title="选择您的代码的编程语言">
            <QuestionCircleOutlined style={{ marginLeft: 8, color: '#6b7280' }} />
          </Tooltip>
        </label>
        <Select
          value={language}
          onChange={onLanguageChange}
          style={{ width: '100%' }}
          placeholder="选择编程语言"
          size="large"
        >
          {languages.map(lang => (
            <Option key={lang} value={lang}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {lang === 'python' && '🐍'}
                {lang === 'java' && '☕'}
                {lang === 'javascript' && '🟨'}
                {lang === 'typescript' && '🔷'}
                {lang === 'go' && '🐹'}
                {lang === 'rust' && '🦀'}
                {lang === 'cpp' && '⚡'}
                {lang === 'csharp' && '🔷'}
                {formatLanguageName(lang)}
              </span>
            </Option>
          ))}
        </Select>
      </div>

      {/* AI模型选择 */}
      <div className="form-group-modern">
        <label className="form-label-modern" style={{
          display: 'block',
          fontWeight: 600,
          marginBottom: '0.5rem',
          color: '#374151'
        }}>
          🤖 AI模型
          <Tooltip title="选择用于生成测试的AI模型">
            <QuestionCircleOutlined style={{ marginLeft: 8, color: '#6b7280' }} />
          </Tooltip>
        </label>
        <Select
          value={model}
          onChange={onModelChange}
          style={{ width: '100%' }}
          placeholder="选择AI模型"
          size="large"
        >
          {models.map(modelName => (
            <Option key={modelName} value={modelName}>
              <Tooltip title={getModelTooltip(modelName)}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {modelName.includes('openai') && '🧠'}
                  {modelName.includes('google') && '🔍'}
                  {modelName.includes('anthropic') && '🎭'}
                  {modelName.includes('grok') && '🚀'}
                  {modelName.includes('deepseek') && '🔬'}
                  {formatModelName(modelName)}
                </span>
              </Tooltip>
            </Option>
          ))}
        </Select>
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          marginTop: '4px',
          fontStyle: 'italic'
        }}>
          💡 需要在后端配置相应的 API 密钥
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="form-group-modern">
        <label className="form-label-modern" style={{
          display: 'block',
          fontWeight: 600,
          marginBottom: '0.5rem',
          color: '#374151'
        }}>
          ⚡ 操作
          <Tooltip title="生成单元测试用例">
            <QuestionCircleOutlined style={{ marginLeft: 8, color: '#6b7280' }} />
          </Tooltip>
        </label>
        <Button
          className="btn-modern btn-modern-primary"
          onClick={onGenerateTests}
          loading={loading}
          style={{
            width: '100%',
            height: '40px',
            fontSize: '16px',
            fontWeight: 600
          }}
          size="large"
        >
          {loading ? '🔄 生成中...' : '⚡ 生成用例'}
        </Button>
      </div>
    </div>
  );
};

export default ControlPanel;
