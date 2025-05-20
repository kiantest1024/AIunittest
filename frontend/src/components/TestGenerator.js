import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, message, Tabs, Spin, Row, Col, Progress, Alert } from 'antd';
import { SaveOutlined, CopyOutlined, GithubOutlined, CodeOutlined, LoadingOutlined } from '@ant-design/icons';
import GitHubModal from './GitHubModal';
import CodeEditor from './CodeEditor';
import ControlPanel from './ControlPanel';
import GitCodeFetcher from './GitCodeFetcher';
import { generateTests, generateTestsStream, generateTestsDirect, uploadFile, getLanguages, getModels, getFileContent } from '../services/api';
import { useAppContext, ActionTypes } from '../context/AppContext';

const { TabPane } = Tabs;

// 语言到文件扩展名的映射
const LANGUAGE_EXTENSIONS = {
  python: '.py',
  java: '.java',
  go: '.go',
  cpp: '.cpp',
  csharp: '.cs'
};

/**
 * 测试生成器组件
 *
 * @returns {JSX.Element} 测试生成器组件
 */
const TestGenerator = () => {
  // 使用Context管理状态
  const { state, dispatch } = useAppContext();
  const { code, language, model, generatedTests, loading } = state;

  // 添加调试日志
  console.log('Current state:', state);

  // 本地状态
  const [activeTabKey, setActiveTabKey] = useState('code');
  const [gitModalVisible, setGitModalVisible] = useState(false);
  const [languages, setLanguages] = useState([]);
  const [models, setModels] = useState([]);
  const [streamingTests, setStreamingTests] = useState([]);
  const [streamProgress, setStreamProgress] = useState(0);
  const [isStreaming, setIsStreaming] = useState(false);
  const [gitInfo, setGitInfo] = useState({
    token: '',
    repo: '',
    path: ''
  });

  // 加载支持的语言和模型
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [languagesData, modelsData] = await Promise.all([
          getLanguages(),
          getModels()
        ]);

        setLanguages(languagesData);
        setModels(modelsData);
      } catch (error) {
        console.error('Error loading languages and models:', error);
        message.error('Failed to load languages and models');
      }
    };

    fetchData();
  }, []);

  // 处理语言变更
  const handleLanguageChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_LANGUAGE, payload: value });
    setActiveTabKey('code');
  }, [dispatch]);

  // 处理模型变更
  const handleModelChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_MODEL, payload: value });
  }, [dispatch]);

  // 处理代码变更
  const handleCodeChange = useCallback((value) => {
    dispatch({ type: ActionTypes.SET_CODE, payload: value });
  }, [dispatch]);

  // 处理文件上传
  const handleFileUpload = useCallback(async (file) => {
    try {
      // 检查文件类型
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      let fileLanguage = null;

      for (const [lang, ext] of Object.entries(LANGUAGE_EXTENSIONS)) {
        if (ext === fileExt) {
          fileLanguage = lang;
          break;
        }
      }

      if (!fileLanguage) {
        message.error('不支持的文件类型！');
        return false;
      }

      // 上传文件
      const formData = new FormData();
      formData.append('file', file);

      dispatch({ type: ActionTypes.SET_LOADING, payload: true });

      try {
        const response = await uploadFile(formData);
        dispatch({ type: ActionTypes.SET_CODE, payload: response.content });
        dispatch({ type: ActionTypes.SET_LANGUAGE, payload: response.language || fileLanguage });
        message.success('文件上传成功！');
      } catch (error) {
        console.error('Error uploading file:', error);
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        message.error('文件上传失败: ' + (error.response?.data?.detail || error.message));
      } finally {
        dispatch({ type: ActionTypes.SET_LOADING, payload: false });
      }

      return false; // 阻止自动上传
    } catch (error) {
      console.error('Error handling file upload:', error);
      message.error('文件上传处理失败');
      return false;
    }
  }, [dispatch]);

  // 处理从Git获取代码
  const handleCodeFetched = useCallback(async (path, token, repo) => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: true });

    try {
      console.log(`Fetching code from repo: ${repo}, path: ${path}`);
      const response = await getFileContent(repo, path, token);

      // 检查响应格式
      console.log('Response received:', response);

      if (!response || !response.content) {
        throw new Error('Invalid response format: missing content');
      }

      // 设置代码内容
      dispatch({ type: ActionTypes.SET_CODE, payload: response.content });

      // 设置语言
      if (response.language) {
        console.log(`Setting language to: ${response.language}`);
        dispatch({ type: ActionTypes.SET_LANGUAGE, payload: response.language });
      } else {
        // 尝试从文件扩展名推断语言
        const fileExt = path.split('.').pop().toLowerCase();
        let detectedLanguage = null;

        if (fileExt === 'py') detectedLanguage = 'python';
        else if (fileExt === 'java') detectedLanguage = 'java';
        else if (fileExt === 'go') detectedLanguage = 'go';
        else if (['cpp', 'h', 'hpp'].includes(fileExt)) detectedLanguage = 'cpp';
        else if (fileExt === 'cs') detectedLanguage = 'csharp';

        if (detectedLanguage) {
          console.log(`Detected language from extension: ${detectedLanguage}`);
          dispatch({ type: ActionTypes.SET_LANGUAGE, payload: detectedLanguage });
        }
      }

      // 保存Git信息，用于后续上传
      const dirPath = path.includes('/') ? path.substring(0, path.lastIndexOf('/')) : '';
      setGitInfo({
        token: token,
        repo: repo,
        path: dirPath
      });

      message.success('代码获取成功！');
      setActiveTabKey('code');
    } catch (error) {
      console.error('Error fetching code:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      message.error('获取代码失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [dispatch, setActiveTabKey]);

  // 流式生成测试
  const handleStreamGenerateTests = useCallback(async () => {
    if (!code.trim()) {
      message.error('请先输入或上传代码！');
      return;
    }

    // 重置状态
    setStreamingTests([]);
    setStreamProgress(0);
    setIsStreaming(true);
    dispatch({ type: ActionTypes.SET_LOADING, payload: true });
    dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [] });

    try {
      message.info({
        content: '正在生成测试用例，这可能需要几分钟时间...',
        duration: 3
      });

      // 创建一个临时数组来存储流式生成的测试
      let tempTests = [];

      // 调用流式API
      try {
        await generateTestsStream(code, language, model, (result) => {
          try {
            console.log('Received test result:', result);

            if (!result) {
              console.warn('Received empty result from stream');
              return;
            }

            // 处理错误消息
            if (result.error) {
              console.error('Error in test generation stream:', result.error);
              message.error('生成测试时出错: ' + result.error);
              return;
            }

            // 处理状态消息
            if (result.status) {
              console.log(`Stream status: ${result.status}, message: ${result.message}`);

              if (result.status === 'started') {
                message.info(result.message || '开始生成测试用例');
                return;
              }

              if (result.status === 'completed') {
                message.success(result.message || '测试生成完成');
                return;
              }

              if (result.status === 'warning') {
                message.warning(result.message || '生成测试时出现警告');
                return;
              }

              if (result.status === 'error') {
                message.error(result.message || '生成测试时出错');
                return;
              }

              // 其他状态消息
              return;
            }

            // 处理不同类型的消息
            if (result.status) {
              console.log(`Received status message: ${result.status}, message: ${result.message}`);

              // 如果是警告消息，但我们已经有测试，则忽略它
              if (result.status === 'warning' && tempTests.length > 0) {
                console.log('Ignoring warning message because we already have tests:', tempTests.length);
                return;
              }

              // 如果是完成消息
              if (result.status === 'completed') {
                console.log('Test generation completed with message:', result.message);

                // 如果有测试计数
                if (result.test_count && result.test_count > 0) {
                  console.log(`Completed with ${result.test_count} tests`);

                  // 如果我们的临时数组为空但后端报告有测试，显示错误
                  if (tempTests.length === 0) {
                    console.error('Backend reported tests but frontend has none!');
                    message.error('后端生成了测试，但前端未能接收。请检查控制台日志。');
                  } else {
                    // 更新全局状态
                    dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: tempTests });
                    message.success(`测试生成成功！共生成 ${result.test_count} 个测试用例`);
                  }
                } else {
                  console.log('Completed but no tests were generated');
                  message.warning('没有找到可以生成测试的函数或方法。');
                }
                return;
              }

              // 如果是其他状态消息，直接返回
              return;
            }

            // 验证结果包含必要的字段
            if (!result.name || !result.test_code) {
              console.warn('Received incomplete test result:', result);
              return;
            }

            // 如果有成功标志，记录它
            if (result.success) {
              console.log(`Successfully generated test for ${result.name}: ${result.message}`);
              message.success(result.message || `生成测试: ${result.name}`, 1);
            }

            console.log(`Received test for ${result.name} with code length: ${result.test_code.length}`);

            // 添加新的测试到临时数组
            const newTest = {
              name: result.name,
              type: result.type || 'function',  // 默认为函数类型
              test_code: result.test_code,
              original_snippet: {
                name: result.name,
                type: result.type || 'function',
                code: ''  // 我们没有原始代码片段
              }
            };

            // 检查是否已经存在相同名称的测试
            const existingIndex = tempTests.findIndex(test => test.name === result.name);
            if (existingIndex >= 0) {
              console.log(`Updating existing test for ${result.name}`);
              // 更新现有测试
              tempTests[existingIndex] = newTest;
            } else {
              console.log(`Adding new test for ${result.name}`);
              // 添加新测试
              tempTests = [...tempTests, newTest];
            }

            // 更新状态
            setStreamingTests(tempTests);

            // 更新进度
            setStreamProgress(tempTests.length);

            // 更新全局状态
            console.log('Updating global state with tests:', tempTests);
            dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [...tempTests] });

            // 检查全局状态是否更新
            setTimeout(() => {
              console.log('Current generatedTests in state:', state.generatedTests);
            }, 100);

            // 如果这是第一个测试，切换到测试标签
            if (tempTests.length === 1) {
              console.log('Switching to test tab: test-0');
              // 使用延迟切换，确保状态已更新
              setTimeout(() => {
                setActiveTabKey('test-0');
                console.log('Tab switched to test-0');
              }, 500);
            }

            // 显示成功消息
            message.success(`已生成测试: ${result.name}`, 1);
          } catch (e) {
            console.error('Error processing test result:', e);
          }
        });
      } catch (streamError) {
        console.error('Error in stream processing:', streamError);
        message.error('流式生成测试失败: ' + streamError.message);
      }

      // 确保最终状态更新
      console.log('Stream completed, tempTests:', tempTests);

      if (tempTests.length > 0) {
        console.log('Final update of global state with tests:', tempTests);
        // 使用延迟更新，确保所有流式响应都已处理
        setTimeout(() => {
          // 强制创建一个新数组，确保状态更新
          const finalTests = [...tempTests];
          console.log('Dispatching final tests:', finalTests);

          dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: finalTests });
          message.success(`测试生成成功！共生成 ${finalTests.length} 个测试用例`);

          // 如果有测试，切换到第一个测试标签
          setActiveTabKey(`test-0`);
          console.log('Switched to first test tab');

          // 再次检查状态是否更新
          setTimeout(() => {
            console.log('Final check of generatedTests:', state.generatedTests);

            // 如果状态仍然没有更新，尝试再次更新
            if (!state.generatedTests || state.generatedTests.length === 0) {
              console.log('State still not updated, trying again');
              dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: finalTests });
            }
          }, 1000);
        }, 500);
      } else {
        console.log('No tests were generated');
        message.warning('没有找到可以生成测试的函数或方法。');
      }
    } catch (error) {
      console.error('生成测试时出错:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      const errorMsg = error.response?.data?.detail || error.message;
      message.error('生成测试失败: ' + errorMsg);

      // 检查是否是API密钥错误
      if (errorMsg.includes('API key') || errorMsg.includes('Authentication') || errorMsg.includes('auth header')) {
        message.warning({
          content: '请确保您已在后端设置了有效的API密钥。请查看.env文件或环境变量。',
          duration: 10
        });
      }
    } finally {
      setIsStreaming(false);
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [code, language, model, dispatch, setActiveTabKey]);

  // 使用直接 API 生成测试
  const handleDirectGenerateTests = useCallback(async () => {
    if (!code.trim()) {
      message.error('请先输入或上传代码！');
      return;
    }

    dispatch({ type: ActionTypes.SET_LOADING, payload: true });

    try {
      message.info({
        content: '正在生成测试用例，这可能需要几分钟时间...',
        duration: 3
      });

      // 调用直接 API
      console.log('Calling generateTestsDirect...');
      const result = await generateTestsDirect(code, language, model);
      console.log('Direct API result:', result);
      console.log('Result type:', typeof result);
      console.log('Result success:', result.success);
      console.log('Result tests:', result.tests);
      console.log('Result tests length:', result.tests ? result.tests.length : 0);

      // 检查 result 是否有效
      if (result && result.tests && Array.isArray(result.tests) && result.tests.length > 0) {
        // 更新全局状态
        dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: result.tests });

        // 显示成功消息
        message.success(result.message || `成功生成 ${result.tests.length} 个测试用例`);

        // 切换到第一个测试标签
        setActiveTabKey('test-0');
        console.log('Switched to first test tab');
      } else {
        // 显示警告消息
        message.warning(result.message || '没有找到可以生成测试的函数或方法');
      }
    } catch (error) {
      console.error('生成测试时出错:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      const errorMsg = error.response?.data?.detail || error.message;
      message.error('生成测试失败: ' + errorMsg);
    } finally {
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [code, language, model, dispatch, setActiveTabKey]);

  // 生成测试 (使用直接 API 替代流式生成)
  const handleGenerateTests = useCallback(async () => {
    // 使用直接 API 生成测试
    await handleDirectGenerateTests();
  }, [handleDirectGenerateTests]);

  // 复制测试代码
  const handleCopyTest = (testCode) => {
    navigator.clipboard.writeText(testCode)
      .then(() => message.success('Test code copied to clipboard!'))
      .catch(() => message.error('Failed to copy test code'));
  };

  // 打开Git保存模态框
  const handleOpenGitModal = () => {
    setGitModalVisible(true);
  };

  // 关闭Git保存模态框
  const handleCloseGitModal = () => {
    setGitModalVisible(false);
  };

  // 保存到本地
  const handleSaveToLocal = (testCode, testName) => {
    // 创建Blob对象
    const blob = new Blob([testCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    // 创建下载链接
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${testName}${LANGUAGE_EXTENSIONS[language]}`;
    document.body.appendChild(a);
    a.click();

    // 清理
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    message.success('Test saved to local file!');
  };

  return (
    <div className="test-generator">
      <Card title={
        <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
          <CodeOutlined style={{ marginRight: 8 }} />
          AI单元测试生成工具
        </div>
      } style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={24}>
            <div style={{ marginBottom: 16, fontWeight: 'bold' }}>
              工作流程：1. 从GitHub获取代码 → 2. 选择代码语言和AI模型 → 3. 生成单元测试 → 4. 保存测试结果
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={8}>
          <GitCodeFetcher
            onCodeFetched={handleCodeFetched}
            loading={loading}
            setLoading={(value) => dispatch({ type: ActionTypes.SET_LOADING, payload: value })}
          />
        </Col>

        <Col span={16}>
          <Card title={
            <div>
              <span style={{ fontWeight: 'bold' }}>代码与测试</span>
            </div>
          }>
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

            <Spin spinning={loading} tip={isStreaming ? "正在生成测试用例，请耐心等待..." : "加载中..."}>
              {isStreaming && streamProgress > 0 && (
                <Alert
                  message="测试生成进行中"
                  description={`已生成 ${streamProgress} 个测试用例`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Tabs activeKey={activeTabKey} onChange={setActiveTabKey}>
                <TabPane tab="源代码" key="code">
                  <CodeEditor
                    code={code}
                    language={language}
                    onChange={handleCodeChange}
                    height="500px"
                  />
                </TabPane>

                {/* 添加调试信息 */}
                {console.log('Rendering tabs with generatedTests:', generatedTests)}

                {/* 确保 generatedTests 是数组并且有内容 */}
                {Array.isArray(generatedTests) && generatedTests.length > 0 ? (
                  generatedTests.map((test, index) => {
                    console.log(`Rendering test tab ${index}:`, test);
                    return (
                      <TabPane tab={`测试: ${test.name}`} key={`test-${index}`}>
                        <Card
                          title={`${test.type === 'method' ? '方法' : '函数'}: ${test.name}`}
                          extra={
                            <div>
                              <Button
                                icon={<SaveOutlined />}
                                onClick={() => handleSaveToLocal(test.test_code, test.name)}
                                style={{ marginRight: 8 }}
                              >
                                保存到本地
                              </Button>
                              <Button
                                type="primary"
                                icon={<GithubOutlined />}
                                onClick={handleOpenGitModal}
                              >
                                上传到Git
                              </Button>
                            </div>
                          }
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
                  <TabPane tab="没有测试" key="no-tests" disabled>
                    <div style={{ padding: '20px', textAlign: 'center' }}>
                      没有找到可以生成测试的函数或方法
                    </div>
                  </TabPane>
                )}
              </Tabs>
            </Spin>
            </Card>
          </Col>
        </Row>

      {/* GitHub保存模态框 */}
      <GitHubModal
        visible={gitModalVisible}
        onCancel={handleCloseGitModal}
        onSave={handleCloseGitModal}
        tests={generatedTests}
        language={language}
        loading={loading}
        setLoading={(value) => dispatch({ type: ActionTypes.SET_LOADING, payload: value })}
        gitInfo={gitInfo}
      />
    </div>
  );
};

export default TestGenerator;
