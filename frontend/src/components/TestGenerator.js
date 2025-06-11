import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, message, Tabs, Spin, Row, Col, Progress, Alert, Modal } from 'antd';
import { SaveOutlined, CopyOutlined, GithubOutlined, CodeOutlined, LoadingOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons';
import GitModal from './GitModal';
import CodeEditor from './CodeEditor';
import ControlPanel from './ControlPanel';
import GitSourceSelector from './GitSourceSelector';
import QueueStatus from './QueueStatus';
import { generateTests, generateTestsStream, generateTestsDirect, uploadFile, getLanguages, getModels, getFileContent, cancelTask } from '../services/api';
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
  // 添加生成进度状态
  const [generationProgress, setGenerationProgress] = useState(0);
  const [totalSnippets, setTotalSnippets] = useState(0);
  const [currentSnippet, setCurrentSnippet] = useState('');
  const [generationStartTime, setGenerationStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [gitInfo, setGitInfo] = useState({
    token: '',
    repo: '',
    path: '',
    provider: 'github' // 添加 provider 字段
  });

  // 全屏进度显示状态
  const [fullScreenProgress, setFullScreenProgress] = useState(false);
  const [backgroundGeneration, setBackgroundGeneration] = useState(false);

  // 任务管理状态
  const [currentTaskId, setCurrentTaskId] = useState(null); // 当前任务ID
  const [cancellingTask, setCancellingTask] = useState(false); // 取消任务状态

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
        message.error('Failed to load languages and models', 3);
      }
    };

    fetchData();
  }, []);

  // 计时器效果
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
        message.error('不支持的文件类型！', 3);
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
        message.success('文件上传成功！', 3);
      } catch (error) {
        console.error('Error uploading file:', error);
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        message.error('文件上传失败: ' + (error.response?.data?.detail || error.message), 3);
      } finally {
        dispatch({ type: ActionTypes.SET_LOADING, payload: false });
      }

      return false; // 阻止自动上传
    } catch (error) {
      console.error('Error handling file upload:', error);
      message.error('文件上传处理失败', 3);
      return false;
    }
  }, [dispatch]);

  // 处理从Git获取代码
  const handleCodeFetched = useCallback(async (platform, path, token, repo, serverUrl = '') => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: true });

    try {
      console.log(`Fetching code from ${platform} repo: ${repo}, path: ${path}, server: ${serverUrl || 'default'}`);
      const response = await getFileContent(repo, path, token, platform, serverUrl);

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

  // 流式生成测试
  const handleStreamGenerateTests = useCallback(async () => {
    if (!code.trim()) {
      message.error('请先输入或上传代码！', 3);
      return;
    }

    // 重置状态
    setStreamingTests([]);
    setStreamProgress(0);
    setIsStreaming(true);
    setGenerationProgress(5); // 立即设置初始进度
    setTotalSnippets(0);
    setCurrentSnippet('正在准备生成单元测试用例...');
    setGenerationStartTime(new Date());

    // 显示全屏进度
    setFullScreenProgress(true);

    dispatch({ type: ActionTypes.SET_LOADING, payload: true });
    dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [] });

    try {
      message.info('正在生成单元测试用例，这可能需要几分钟时间...', 3);

      // 估算代码中的函数/方法数量
      const functionMatches = code.match(/\b(function|def|class|method|func|public\s+\w+|private\s+\w+|protected\s+\w+)\b/g);
      const estimatedSnippets = functionMatches ? functionMatches.length : 1;
      setTotalSnippets(estimatedSnippets);
      setCurrentSnippet('正在解析代码...');
      setGenerationProgress(5);

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
              message.error('生成单元测试用例时出错: ' + result.error, 3);
              return;
            }

            // 处理状态消息
            if (result.status) {
              console.log(`Stream status: ${result.status}, message: ${result.message}`);

              // 更新进度
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

              // 其他状态消息
              return;
            }

            // 这里已经在上面处理了状态消息，不需要重复处理

            // 验证结果包含必要的字段
            if (!result.name || !result.test_code) {
              console.warn('Received incomplete test result:', result);
              return;
            }

            // 如果有成功标志，记录它
            if (result.success) {
              console.log(`Successfully generated test for ${result.name}: ${result.message}`);
              message.success(result.message || `生成单元测试用例: ${result.name}`, 3);
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

            // 立即更新全局状态，让新测试立即显示
            console.log('Updating global state with tempTests:', tempTests);
            setStreamingTests(tempTests);

            // 使用setTimeout确保状态更新不被React批量处理延迟
            setTimeout(() => {
              dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: [...tempTests] });
              console.log('Global state updated, tempTests length:', tempTests.length);
            }, 0);

            // 更新进度
            setStreamProgress(tempTests.length);

            // 使用后端提供的进度信息，如果没有则使用估算
            if (result.progress !== undefined) {
              setGenerationProgress(result.progress);
            } else {
              const progressPercent = Math.min(95, 20 + (tempTests.length / Math.max(estimatedSnippets, 1)) * 75);
              setGenerationProgress(progressPercent);
            }

            // 使用后端提供的进度信息更新当前状态
            if (result.completed !== undefined && result.total !== undefined) {
              setCurrentSnippet(`已生成单元测试用例: ${result.name} (${result.completed}/${result.total})`);
            } else {
              setCurrentSnippet(`已生成单元测试用例: ${result.name} (${tempTests.length}/${estimatedSnippets})`);
            }

            // 如果这是第一个测试，自动切换到测试标签页
            if (tempTests.length === 1) {
              setTimeout(() => {
                setActiveTabKey('test-0');
                console.log('Auto-switched to first test tab');
              }, 100);
            }

            // 显示成功消息（避免重复显示）
            if (!result.success) {
              message.success(`已生成单元测试用例: ${result.name}`, 3);
            }
          } catch (e) {
            console.error('Error processing test result:', e);
          }
        }, (taskId) => {
          // 任务ID回调
          console.log('Received task ID:', taskId);
          setCurrentTaskId(taskId);
        });
      } catch (streamError) {
        console.error('Error in stream processing:', streamError);
        message.error('流式生成单元测试用例失败: ' + streamError.message, 3);
      }

      // 确保最终状态更新
      console.log('Stream completed, tempTests:', tempTests);

      // 最终状态已经在每个测试生成时更新了，这里只需要显示完成消息
      if (tempTests.length > 0) {
        console.log('Stream generation completed with tests:', tempTests.length);
        message.success(`单元测试用例生成成功！共生成 ${tempTests.length} 个测试用例`, 3);
      } else {
        console.log('No tests were generated');
        message.warning('没有找到可以生成单元测试用例的函数或方法。', 3);
      }
    } catch (error) {
      console.error('生成测试时出错:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
      const errorMsg = error.response?.data?.detail || error.message;
      message.error('生成测试失败: ' + errorMsg, 3);

      // 检查是否是API密钥错误
      if (errorMsg.includes('API key') || errorMsg.includes('Authentication') || errorMsg.includes('auth header')) {
        message.warning('请确保您已在后端设置了有效的API密钥。请查看.env文件或环境变量。', 10);
      }
    } finally {
      setIsStreaming(false);
      setGenerationProgress(100);

      // 关闭全屏进度
      setFullScreenProgress(false);

      // 使用当前的generatedTests状态而不是streamingTests
      const currentTests = state.generatedTests || [];
      setCurrentSnippet(currentTests.length > 0 ? '生成完成' : '未找到可测试的代码');
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });

      // 确保最终状态正确
      console.log('Stream generation finally block - current tests:', currentTests.length);
    }
  }, [code, language, model, dispatch, setActiveTabKey]);

  // 使用直接 API 生成测试
  const handleDirectGenerateTests = useCallback(async () => {
    if (!code.trim()) {
      message.error('请先输入或上传代码！', 3);
      return;
    }

    // 重置进度状态
    setGenerationProgress(0);
    setTotalSnippets(0);
    setCurrentSnippet('');
    setGenerationStartTime(new Date());

    dispatch({ type: ActionTypes.SET_LOADING, payload: true });

    try {
      message.info('正在生成单元测试用例，这可能需要几分钟时间...', 3);

      // 使用正则表达式粗略估计代码中的函数/方法数量
      const functionMatches = code.match(/\b(function|def|class|method|func)\b/g);
      const estimatedSnippets = functionMatches ? functionMatches.length : 1;
      setTotalSnippets(estimatedSnippets);

      // 设置初始进度
      setGenerationProgress(5); // 开始时设置为5%表示已经开始处理

      // 模拟解析代码的进度
      setTimeout(() => {
        setGenerationProgress(10);
        setCurrentSnippet('正在解析代码...');
      }, 500);

      // 模拟进度更新 - 由于后端不提供实时进度，我们在前端模拟进度
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          // 进度最多到95%，剩下的5%留给最终完成
          if (prev < 95) {
            const increment = Math.random() * 5 + 1; // 每次增加1-6%
            const newProgress = Math.min(95, prev + increment);

            // 根据进度更新当前状态消息
            if (newProgress > 10 && newProgress <= 30) {
              setCurrentSnippet('正在分析代码结构...');
            } else if (newProgress > 30 && newProgress <= 60) {
              setCurrentSnippet('正在生成单元测试用例...');
            } else if (newProgress > 60 && newProgress < 95) {
              setCurrentSnippet('正在优化测试代码...');
            }

            return newProgress;
          }
          return prev;
        });
      }, 1000); // 每秒更新一次进度

      // 调用直接 API
      console.log('Calling generateTestsDirect...');
      const result = await generateTestsDirect(code, language, model);

      // 清除进度更新定时器
      clearInterval(progressInterval);

      console.log('Direct API result:', result);
      console.log('Result type:', typeof result);
      console.log('Result success:', result.success);
      console.log('Result tests:', result.tests);
      console.log('Result tests length:', result.tests ? result.tests.length : 0);

      // 检查 result 是否有效，并处理不同的响应格式
      if (result && ((result.tests && Array.isArray(result.tests) && result.tests.length > 0) ||
                     (Array.isArray(result) && result.length > 0))) {
        // 确定要使用的测试数据
        const testsData = Array.isArray(result) ? result : result.tests;

        // 设置进度为100%
        setGenerationProgress(100);
        setCurrentSnippet('生成完成');

        // 更新全局状态
        console.log('Dispatching tests data:', testsData);
        dispatch({ type: ActionTypes.SET_GENERATED_TESTS, payload: testsData });

        // 显示成功消息
        const testCount = testsData.length;
        message.success(result.message || `成功生成 ${testCount} 个单元测试用例`, 3);

        // 切换到第一个测试标签
        setActiveTabKey('test-0');
        console.log('Switched to first test tab');
      } else {
        // 设置进度为100%，但显示警告
        setGenerationProgress(100);
        setCurrentSnippet('未找到可测试的代码');

        // 显示警告消息
        message.warning(result.message || '没有找到可以生成单元测试用例的函数或方法', 3);
      }
    } catch (error) {
      console.error('生成测试时出错:', error);
      dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });

      // 设置进度为100%，但显示错误
      setGenerationProgress(100);
      setCurrentSnippet('生成失败');

      // 检查是否是超时错误
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        message.error('生成单元测试用例超时，DeepSeek-R1 模型可能需要更长时间。请尝试使用其他模型或稍后再试。', 3);
      } else if (error.response) {
        // 服务器返回了错误状态码
        const errorMsg = error.response.data?.detail || error.response.data?.message || error.message;
        message.error('生成单元测试用例失败: ' + errorMsg, 3);
      } else if (error.request) {
        // 请求已发送但没有收到响应
        message.error('服务器没有响应，请检查网络连接或稍后再试。', 3);
      } else {
        // 其他错误
        message.error('生成单元测试用例失败: ' + error.message, 3);
      }
    } finally {
      // 保持进度状态，但停止加载动画
      dispatch({ type: ActionTypes.SET_LOADING, payload: false });
    }
  }, [code, language, model, dispatch, setActiveTabKey]);

  // 生成测试 (使用流式生成替代直接生成)
  const handleGenerateTests = useCallback(async () => {
    // 使用流式生成测试，提供实时进度
    await handleStreamGenerateTests();
  }, [handleStreamGenerateTests]);

  // 复制测试代码
  const handleCopyTest = (testCode) => {
    navigator.clipboard.writeText(testCode)
      .then(() => message.success('Test code copied to clipboard!', 3))
      .catch(() => message.error('Failed to copy test code', 3));
  };

  // 打开Git保存模态框
  const handleOpenGitModal = () => {
    setGitModalVisible(true);
  };

  // 关闭Git保存模态框
  const handleCloseGitModal = () => {
    setGitModalVisible(false);
  };

  // 取消任务
  const handleCancelTask = useCallback(async () => {
    if (!currentTaskId) {
      console.warn('No current task ID to cancel');
      return;
    }

    setCancellingTask(true);
    try {
      console.log('Cancelling task:', currentTaskId);
      await cancelTask(currentTaskId);

      // 重置状态
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

                {/* 添加调试信息 */}
                {console.log('Rendering tabs with generatedTests:', generatedTests)}

                {/* 确保 generatedTests 是数组并且有内容 */}
                {Array.isArray(generatedTests) && generatedTests.length > 0 ? (
                  generatedTests.map((test, index) => {
                    console.log(`Rendering test tab ${index}:`, test);
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