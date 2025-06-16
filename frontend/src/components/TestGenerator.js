import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, message, Tabs, Spin, Progress, Modal } from 'antd';
import { SaveOutlined, GithubOutlined, LoadingOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons';
import GitModal from './GitModal';
import CodeEditor from './CodeEditor';
import ControlPanel from './ControlPanel';
import GitSourceSelector from './GitSourceSelector';
import QueueStatus from './QueueStatus';
import { generateTestsStream, uploadFile, getLanguages, getModels, getFileContent, cancelTask } from '../services/api';
import { useAppContext, ActionTypes } from '../context/AppContext';
import './TestGenerator.css';

const { TabPane } = Tabs;

// 语言到文件扩展名的映射
const LANGUAGE_EXTENSIONS = {
  python: '.py',
  java: '.java',
  go: '.go',
  cpp: '.cpp',
  csharp: '.cs'
};

const TestGenerator = () => {
  const { state, dispatch } = useAppContext();
  const { code, language, model, generatedTests, loading } = state;
  const [activeTabKey, setActiveTabKey] = useState('code');
  const [gitModalVisible, setGitModalVisible] = useState(false);
  const [languages, setLanguages] = useState([]);
  const [models, setModels] = useState([]);

  const [streamProgress, setStreamProgress] = useState(0);
  const [isStreaming, setIsStreaming] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [totalSnippets, setTotalSnippets] = useState(0);
  const [currentSnippet, setCurrentSnippet] = useState('');
  const [generationStartTime, setGenerationStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [gitInfo, setGitInfo] = useState({
    token: '',
    repo: '',
    path: '',
    provider: 'github'
  });
  const [fullScreenProgress, setFullScreenProgress] = useState(false);
  const [backgroundGeneration, setBackgroundGeneration] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [cancellingTask, setCancellingTask] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [languagesData, modelsData] = await Promise.all([
          getLanguages(),
          getModels()
        ]);

        setLanguages(languagesData);
        setModels(modelsData.models);

        if (modelsData.default_model &&
            (!model || !modelsData.models.includes(model) || model !== modelsData.default_model)) {
          dispatch({ type: ActionTypes.SET_MODEL, payload: modelsData.default_model });
        }
      } catch (error) {
        console.error('Error loading languages and models:', error);
        message.error('Failed to load languages and models', 3);
      }
    };

    fetchData();
  }, [model, dispatch]);

  useEffect(() => {
    let timer;
    if (generationStartTime && loading) {
      timer = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now - generationStartTime) / 1000);
        setElapsedTime(elapsed);
      }, 1000);
    } else if (!loading) {
      setGenerationStartTime(null);
      setElapsedTime(0);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [generationStartTime, loading]);

  const handleLanguageChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_LANGUAGE, payload: value });
    setActiveTabKey('code');
  }, [dispatch]);

  const handleModelChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_MODEL, payload: value });
  }, [dispatch]);

  const handleCodeChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_CODE, payload: value });
  }, [dispatch]);

  const handleFileUpload = useCallback(async (file) => {
    try {
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      let fileLanguage = null;

      for (const [lang, ext] of Object.entries(LANGUAGE_EXTENSIONS)) {
        if (ext === fileExt) {
          fileLanguage = lang;
          break;
        }
      }

      if (!fileLanguage) {
        message.error('不支持的文件类型！', 3);
        return false;
      }

      const formData = new FormData();
      formData.append('file', file);

      dispatch({ type: ActionTypes.SET_LOADING, payload: true });

      try {
        const response = await uploadFile(formData);
        dispatch({ type: ActionTypes.SET_CODE, payload: response.content });
        dispatch({ type: ActionTypes.SET_LANGUAGE, payload: response.language || fileLanguage });
        message.success('文件上传成功！', 3);
      } catch (error) {
        console.error('Error uploading file:', error);
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        message.error('文件上传失败: ' + (error.response?.data?.detail || error.message), 3);
      } finally {
        dispatch({ type: ActionTypes.SET_LOADING, payload: false });
      }

      return false;
    } catch (error) {
      console.error('Error handling file upload:', error);
      message.error('文件上传处理失败', 3);
      return false;
    }
  }, [dispatch]);
  const handleCodeFetched = useCallback(async (platform, path, token, repo, serverUrl = '') => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: true });

    try {
      const response = await getFileContent(repo, path, token, platform, serverUrl);

      if (!response || !response.content) {
        throw new Error('Invalid response format: missing content');
      }

      dispatch({ type: ActionTypes.SET_CODE, payload: response.content });

      if (response.language) {
        dispatch({ type: ActionTypes.SET_LANGUAGE, payload: response.language });
      } else {
        const fileExt = path.split('.').pop().toLowerCase();
        let detectedLanguage = null;

        if (fileExt === 'py') detectedLanguage = 'python';
        else if (fileExt === 'java') detectedLanguage = 'java';
        else if (fileExt === 'go') detectedLanguage = 'go';
        else if (['cpp', 'h', 'hpp'].includes(fileExt)) detectedLanguage = 'cpp';
        else if (fileExt === 'cs') detectedLanguage = 'csharp';

        if (detectedLanguage) {
          dispatch({ type: ActionTypes.SET_LANGUAGE, payload: detectedLanguage });
        }
      }

      const dirPath = path.includes('/') ? path.substring(0, path.lastIndexOf('/')) : '';
      setGitInfo({
        platform,
        token,
        repo,
        path: dirPath
      });

      message.success('代码获取成功！', 3);
      setActiveTabKey('code');
    } catch (error) {
      console.error('Error fetching code:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      message.error('获取代码失败: ' + (error.response?.data?.detail || error.message), 3);
    } finally {
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [dispatch, setActiveTabKey]);

  const handleStreamGenerateTests = useCallback(async () => {
    if (!code.trim()) {
      message.error('请先输入或上传代码！', 3);
      return;
    }

    setStreamProgress(0);
    setIsStreaming(true);
    setGenerationProgress(5);
    setTotalSnippets(0);
    setCurrentSnippet('正在准备生成单元测试用例...');
    setGenerationStartTime(new Date());
    setFullScreenProgress(true);

    dispatch({ type: ActionTypes.SET_LOADING, payload: true });
    dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [] });

    try {
      message.info('正在生成单元测试用例，这可能需要几分钟时间...', 3);

      const functionMatches = code.match(/\b(function|def|class|method|func|public\s+\w+|private\s+\w+|protected\s+\w+)\b/g);
      const estimatedSnippets = functionMatches ? functionMatches.length : 1;
      setTotalSnippets(estimatedSnippets);
      setCurrentSnippet('正在解析代码...');
      setGenerationProgress(5);

      let tempTests = [];

      try {
        await generateTestsStream(code, language, model, (result) => {
          try {
            if (!result) {
              console.warn('Received empty result from stream');
              return;
            }

            if (result.error) {
              console.error('Error in test generation stream:', result.error);
              message.error('生成单元测试用例时出错: ' + result.error, 3);
              return;
            }

            if (result.status) {
              if (result.progress !== undefined) {
                setGenerationProgress(result.progress);
              }

              if (result.status === 'started') {
                setCurrentSnippet('开始生成单元测试用例...');
                message.info(result.message || '开始生成单元测试用例', 3);
                return;
              }

              if (result.status === 'parsing_completed') {
                setCurrentSnippet(`代码解析完成，找到 ${result.total_snippets || 0} 个代码片段`);
                if (result.total_snippets) {
                  setTotalSnippets(result.total_snippets);
                }
                return;
              }

              if (result.status === 'generating') {
                setCurrentSnippet(result.message || `正在为 ${result.current_snippet} 生成单元测试用例`);
                if (result.completed !== undefined && result.total !== undefined) {
                  setStreamProgress(result.completed);
                }
                return;
              }

              if (result.status === 'completed') {
                setCurrentSnippet('测试生成完成');
                setGenerationProgress(100);
                message.success(result.message || '测试生成完成', 3);
                return;
              }

              if (result.status === 'warning') {
                setCurrentSnippet('生成单元测试用例时出现警告');
                message.warning(result.message || '生成单元测试用例时出现警告', 3);
                return;
              }

              if (result.status === 'error') {
                setCurrentSnippet('生成单元测试用例时出错');
                message.error(result.message || '生成单元测试用例时出错', 3);
                return;
              }

              return;
            }

            if (!result.name || !result.test_code) {
              console.warn('Received incomplete test result:', result);
              return;
            }

            if (result.success) {
              message.success(result.message || `生成单元测试用例: ${result.name}`, 3);
            }

            const newTest = {
              name: result.name,
              type: result.type || 'function',
              test_code: result.test_code,
              original_snippet: {
                name: result.name,
                type: result.type || 'function',
                code: ''
              }
            };

            const existingIndex = tempTests.findIndex(test => test.name === result.name);
            if (existingIndex >= 0) {
              tempTests[existingIndex] = newTest;
            } else {
              tempTests = [...tempTests, newTest];
            }

            setTimeout(() => {
              dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [...tempTests] });
            }, 0);

            setStreamProgress(tempTests.length);

            if (result.progress !== undefined) {
              setGenerationProgress(result.progress);
            } else {
              const progressPercent = Math.min(95, 20 + (tempTests.length / Math.max(estimatedSnippets, 1)) * 75);
              setGenerationProgress(progressPercent);
            }

            if (result.completed !== undefined && result.total !== undefined) {
              setCurrentSnippet(`已生成单元测试用例: ${result.name} (${result.completed}/${result.total})`);
            } else {
              setCurrentSnippet(`已生成单元测试用例: ${result.name} (${tempTests.length}/${estimatedSnippets})`);
            }

            if (tempTests.length === 1) {
              setTimeout(() => {
                setActiveTabKey('test-0');
              }, 100);
            }

            if (!result.success) {
              message.success(`已生成单元测试用例: ${result.name}`, 3);
            }
          } catch (e) {
            console.error('Error processing test result:', e);
          }
        }, (taskId) => {
          setCurrentTaskId(taskId);
        });
      } catch (streamError) {
        console.error('Error in stream processing:', streamError);
        message.error('流式生成单元测试用例失败: ' + streamError.message, 3);
      }

      if (tempTests.length > 0) {
        message.success(`单元测试用例生成成功！共生成 ${tempTests.length} 个测试用例`, 3);
      } else {
        message.warning('没有找到可以生成单元测试用例的函数或方法。', 3);
      }
    } catch (error) {
      console.error('生成测试时出错:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      const errorMsg = error.response?.data?.detail || error.message;
      message.error('生成测试失败: ' + errorMsg, 3);

      if (errorMsg.includes('API key') || errorMsg.includes('Authentication') || errorMsg.includes('auth header')) {
        message.warning('请确保您已在后端设置了有效的API密钥。请查看.env文件或环境变量。', 10);
      }
    } finally {
      setIsStreaming(false);
      setGenerationProgress(100);
      setFullScreenProgress(false);

      const currentTests = state.generatedTests || [];
      setCurrentSnippet(currentTests.length > 0 ? '生成完成' : '未找到可测试的代码');
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [code, language, model, dispatch, setActiveTabKey, state.generatedTests]);
  const handleGenerateTests = useCallback(async () => {
    await handleStreamGenerateTests();
  }, [handleStreamGenerateTests]);

  const handleOpenGitModal = () => {
    setGitModalVisible(true);
  };

  const handleCloseGitModal = () => {
    setGitModalVisible(false);
  };
  const handleCancelTask = useCallback(async () => {
    if (!currentTaskId) {
      console.warn('No current task ID to cancel');
      return;
    }

    setCancellingTask(true);
    try {
      await cancelTask(currentTaskId);

      setIsStreaming(false);
      setFullScreenProgress(false);
      setCurrentTaskId(null);
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });

      message.success('任务已取消', 3);
    } catch (error) {
      console.error('Error cancelling task:', error);
      message.error('取消任务失败: ' + error.message, 3);
    } finally {
      setCancellingTask(false);
    }
  }, [currentTaskId, dispatch]);

  const handleSaveToLocal = (testCode, testName) => {
    const blob = new Blob([testCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${testName}${LANGUAGE_EXTENSIONS[language]}`;
    document.body.appendChild(a);
    a.click();

    // 清理
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    message.success('Test saved to local file!', 3);
  };

  return (
    <div className="test-generator test-generator-container">
      {/* 现代化内容网格 */}
      <div className="content-grid">
        {/* 左侧面板 - Git源码选择 */}
        <div className="left-panel">
          <h2 className="section-title" style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            marginBottom: '1.5rem',
            color: '#1e293b',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              width: '4px',
              height: '24px',
              background: 'linear-gradient(45deg, #4ade80, #06b6d4)',
              borderRadius: '2px',
              display: 'inline-block'
            }}></span>
            代码仓库获取代码
          </h2>

          <GitSourceSelector
            onCodeFetched={handleCodeFetched}
            loading={loading}
            setLoading={(value) => dispatch({ type: ActionTypes.SET_LOADING, payload: value })}
          />
        </div>

        {/* 右侧面板 - 代码与测试 */}
        <div className="right-panel">
          <h2 className="section-title" style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            marginBottom: '1.5rem',
            color: '#1e293b',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              width: '4px',
              height: '24px',
              background: 'linear-gradient(45deg, #4ade80, #06b6d4)',
              borderRadius: '2px',
              display: 'inline-block'
            }}></span>
            代码与测试
          </h2>

          <ControlPanel
            language={language}
            model={model}
            languages={languages}
            models={models}
            onLanguageChange={handleLanguageChange}
            onModelChange={handleModelChange}
            onFileUpload={handleFileUpload}
            onGenerateTests={handleGenerateTests}
            loading={loading}
            acceptedFileTypes={LANGUAGE_EXTENSIONS}
          />

          {/* 现代化代码区域 */}
          <div className="monaco-editor-container" style={{
            marginTop: '1rem',
            width: '100%',
            maxWidth: '100%',
            overflow: 'hidden',
            boxSizing: 'border-box'
          }}>
            <Spin spinning={loading} tip={isStreaming ? "正在生成单元测试用例，请耐心等待..." : "加载中..."}>
              {/* 统一的进度显示 */}
              {loading && (isStreaming || generationProgress > 0) && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ fontWeight: 'bold' }}>
                      {isStreaming ? '流式生成进度：' : '单元测试用例生成进度：'}
                    </span>
                    <span>{currentSnippet}</span>
                    {elapsedTime > 0 && (
                      <span style={{ float: 'right' }}>
                        已用时间: {Math.floor(elapsedTime / 60)}分{elapsedTime % 60}秒
                      </span>
                    )}
                  </div>
                  <Progress
                    percent={Math.round(generationProgress)}
                    status={generationProgress >= 100 ? (currentSnippet.includes('失败') ? 'exception' : 'success') : 'active'}
                    strokeColor={{
                      '0%': '#4ade80',
                      '100%': '#06b6d4',
                    }}
                  />
                  {isStreaming && streamProgress > 0 && (
                    <div style={{
                      marginTop: 8,
                      padding: '8px 16px',
                      background: 'rgba(24, 144, 255, 0.1)',
                      borderRadius: '6px',
                      border: '1px solid rgba(24, 144, 255, 0.2)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <span style={{ fontSize: '14px', color: '#1890ff', fontWeight: '500' }}>
                        📊 生成进度统计
                      </span>
                      <span style={{ fontSize: '14px', color: '#666', fontWeight: 'bold' }}>
                        已生成 {streamProgress} 个测试用例
                        {totalSnippets > 0 && ` / 预计 ${totalSnippets} 个`}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <Tabs
                activeKey={activeTabKey}
                onChange={setActiveTabKey}
                type="editable-card"
                hideAdd={true}
                tabPosition="top"
                style={{
                  marginTop: '50px',
                  width: '100%',
                  maxWidth: '100%',
                  overflow: 'hidden',
                  boxSizing: 'border-box'
                }}
                tabBarStyle={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px 12px 0 0',
                  margin: 0,
                  padding: '0 20px',
                  overflow: 'auto',
                  whiteSpace: 'nowrap',
                  scrollbarWidth: 'thin'
                }}
                tabBarGutter={8}
                size="small"
              >
                <TabPane
                  tab={
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      📝 源代码
                    </span>
                  }
                  key="code"
                >
                  <CodeEditor
                    code={code}
                    language={language}
                    onChange={handleCodeChange}
                    height="500px"
                  />
                </TabPane>



                {/* 确保 generatedTests 是数组并且有内容 */}
                {Array.isArray(generatedTests) && generatedTests.length > 0 ? (
                  generatedTests.map((test, index) => {
                    return (
                      <TabPane
                        tab={
                          <span
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              maxWidth: '150px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                            title={`测试: ${test.name}`}
                          >
                            🧪 {test.name.length > 12 ? test.name.substring(0, 12) + '...' : test.name}
                          </span>
                        }
                        key={`test-${index}`}
                      >
                        <Card
                          title={
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              {test.type === 'method' ? '⚙️' : '🔧'}
                              {test.type === 'method' ? '方法' : '函数'}: {test.name}
                            </span>
                          }
                          extra={
                            <div>
                              <Button
                                className="btn-modern btn-modern-secondary"
                                icon={<SaveOutlined />}
                                onClick={() => handleSaveToLocal(test.test_code, test.name)}
                                style={{ marginRight: 8 }}
                              >
                                💾 保存到本地
                              </Button>
                              <Button
                                className="btn-modern btn-modern-primary"
                                icon={<GithubOutlined />}
                                onClick={handleOpenGitModal}
                              >
                                📤 上传到Git
                              </Button>
                            </div>
                          }
                          style={{
                            border: 'none',
                            boxShadow: 'none',
                            width: '100%',
                            maxWidth: '100%',
                            overflow: 'hidden',
                            boxSizing: 'border-box'
                          }}
                        >
                          <CodeEditor
                            code={test.test_code}
                            language={language}
                            readOnly={true}
                            height="500px"
                          />
                        </Card>
                      </TabPane>
                    );
                  })
                ) : (
                  // 如果没有测试，显示一个空的 TabPane
                  <TabPane
                    tab={
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        ❌ 没有测试
                      </span>
                    }
                    key="no-tests"
                    disabled
                  >
                    <div style={{
                      padding: '3rem',
                      textAlign: 'center',
                      color: '#64748b',
                      background: '#f8fafc',
                      borderRadius: '12px',
                      border: '2px dashed #e2e8f0'
                    }}>
                      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
                      <h3 style={{ color: '#475569', marginBottom: '0.5rem' }}>没有找到可以生成测试的函数或方法</h3>
                      <p>请确保您的代码包含函数或方法定义</p>
                    </div>
                  </TabPane>
                )}
              </Tabs>
            </Spin>
          </div>
        </div>
      </div>

      {/* 全屏进度显示 */}
      <Modal
        title={null}
        open={fullScreenProgress}
        footer={null}
        closable={false}
        width="90%"
        style={{ top: 20 }}
        bodyStyle={{
          padding: '40px',
          minHeight: '500px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: '12px'
        }}
      >
        <div style={{ textAlign: 'center', width: '100%', maxWidth: '600px' }}>
          {/* 标题 */}
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'white', fontSize: '28px', marginBottom: '10px' }}>
              🤖 AI正在生成单元测试用例
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '16px' }}>
              请耐心等待，每个测试用例生成后会立即显示
            </p>
          </div>

          {/* 进度条 */}
          <div style={{ marginBottom: '30px' }}>
            <Progress
              percent={Math.round(generationProgress)}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              trailColor="rgba(255,255,255,0.3)"
              strokeWidth={8}
              format={(percent) => (
                <span style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
                  {percent}%
                </span>
              )}
            />
          </div>

          {/* 状态信息 */}
          <div style={{ marginBottom: '30px' }}>
            <p style={{ color: 'white', fontSize: '16px', marginBottom: '10px' }}>
              {currentSnippet || '正在准备生成单元测试用例...'}
            </p>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
              已生成: {streamProgress} / {totalSnippets > 0 ? totalSnippets : '?'} 个测试
            </p>
            {elapsedTime > 0 && (
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                已用时: {Math.floor(elapsedTime / 60)}分{elapsedTime % 60}秒
              </p>
            )}
          </div>

          {/* 操作按钮 */}
          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <Button
              type="default"
              icon={<EyeOutlined />}
              onClick={() => {
                setBackgroundGeneration(true);
                setFullScreenProgress(false);
              }}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid rgba(255,255,255,0.3)',
                color: 'white'
              }}
            >
              后台生成
            </Button>
            <Button
              type="primary"
              danger
              icon={<CloseOutlined />}
              loading={cancellingTask}
              onClick={handleCancelTask}
            >
              {cancellingTask ? '正在取消...' : '取消生成'}
            </Button>
          </div>

          {/* 提示信息 */}
          <div style={{ marginTop: '30px', padding: '20px', background: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px', margin: 0 }}>
              💡 提示：您可以点击"后台生成"继续使用其他功能，生成的测试会实时显示在测试标签页中
            </p>
          </div>
        </div>
      </Modal>

      {/* 后台生成进度提示 */}
      {backgroundGeneration && isStreaming && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          background: 'white',
          padding: '15px 20px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          border: '1px solid #d9d9d9',
          minWidth: '300px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <LoadingOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontWeight: 'bold' }}>后台生成中</span>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setBackgroundGeneration(false);
                setFullScreenProgress(true);
              }}
            >
              查看进度
            </Button>
          </div>
          <Progress
            percent={Math.round(generationProgress)}
            size="small"
            showInfo={false}
          />
          <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>
            {currentSnippet} ({streamProgress}/{totalSnippets > 0 ? totalSnippets : '?'})
          </p>
        </div>
      )}

      {/* GitHub保存模态框 */}
      <GitModal
        visible={gitModalVisible}
        onCancel={handleCloseGitModal}
        onSave={handleCloseGitModal}
        tests={generatedTests}
        language={language}
        loading={loading}
        setLoading={(value) => dispatch({ type: ActionTypes.SET_LOADING, payload: value })}
        gitInfo={gitInfo}
        isGeneratingTests={isStreaming}
      />

      {/* 队列状态显示 */}
      <QueueStatus
        visible={true}
        refreshInterval={2000}
      />
    </div>
  );
};

export default TestGenerator;
