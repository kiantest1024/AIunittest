import axios from 'axios';

// 创建一个取消令牌源
const CancelToken = axios.CancelToken;
let source = CancelToken.source();

// 重置取消令牌
export const resetCancelToken = () => {
  source = CancelToken.source();
};

// 取消所有请求
export const cancelAllRequests = (message = 'Operation canceled by the user') => {
  source.cancel(message);
  resetCancelToken();
};

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8888/api',
  headers: {
    'Content-Type': 'application/json',
    // 添加CORS相关头
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization, X-Request-With'
  },
  timeout: 600000, // 10分钟超时
  // 不携带凭证，避免CORS预检请求
  withCredentials: false,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加取消令牌到每个请求
    config.cancelToken = source.token;

    // 添加请求时间戳
    config.metadata = { startTime: new Date() };

    // 记录请求详情
    console.log(`Request: ${config.method.toUpperCase()} ${config.url}`);
    console.log('Request params:', config.params);
    console.log('Request data:', config.data);
    console.log('Request headers:', config.headers);

    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 计算请求耗时
    const endTime = new Date();
    const startTime = response.config.metadata.startTime;
    const duration = endTime - startTime;

    // 记录请求耗时（可用于性能监控）
    console.debug(`Request to ${response.config.url} took ${duration}ms`);

    return response.data;
  },
  (error) => {
    // 如果是取消请求，不显示错误
    if (axios.isCancel(error)) {
      console.log('Request canceled:', error.message);
      return Promise.reject(error);
    }

    // 处理错误响应
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API Error:', error.response.status, error.response.statusText);
      console.error('Error Data:', error.response.data);
      console.error('Request URL:', error.config.url);
      console.error('Request Method:', error.config.method);
      console.error('Request Headers:', error.config.headers);

      // 如果是代理错误，可能是CORS或网络问题
      if (error.response.status === 500) {
        console.error('Possible proxy error. Check if backend server is running and accessible.');
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('No response received:', error.request);
      console.error('Request URL:', error.config.url);
      console.error('Request Method:', error.config.method);
    } else {
      // 请求配置出错
      console.error('Request error:', error.message);
      console.error('Request Config:', error.config);
    }

    return Promise.reject(error);
  }
);

// 生成测试
export const generateTests = async (code, language, model) => {
  console.log(`Generating tests for ${language} code using model ${model}`);
  console.log(`Code length: ${code.length} characters`);

  // 为大型代码文件设置更长的超时时间
  const timeout = code.length > 10000 ? 600000 : 300000; // 10分钟或5分钟

  return api.post('/generate-test', {
    code,
    language,
    model,
  }, {
    timeout: timeout // 覆盖默认超时设置
  });
};

// 直接生成测试（非流式）
export const generateTestsDirect = async (code, language, model) => {
  console.log(`Directly generating tests for ${language} code using model ${model}`);
  console.log(`Code length: ${code.length} characters`);

  // 为大型代码文件和特定模型设置更长的超时时间
  let timeout = code.length > 10000 ? 600000 : 300000; // 10分钟或5分钟

  // 为 DeepSeek-R1 模型设置更长的超时时间
  if (model === 'deepseek-R1') {
    console.log('Using extended timeout for DeepSeek-R1 model');
    timeout = 1200000; // 20分钟
  }

  try {
    const response = await api.post('/generate-test-direct', {
      code,
      language,
      model,
    }, {
      timeout: timeout // 覆盖默认超时设置
    });

    console.log('Direct test generation response:', response);
    // 由于响应拦截器已经返回了 response.data，这里直接返回 response
    return response;
  } catch (error) {
    console.error('Error generating tests directly:', error);
    throw error;
  }
};

// 流式生成测试
export const generateTestsStream = async (code, language, model, onProgress) => {
  console.log(`Streaming tests for ${language} code using model ${model}`);
  console.log(`Code length: ${code.length} characters`);

  // 为大型代码文件设置更长的超时时间
  const timeout = code.length > 10000 ? 600000 : 300000; // 10分钟或5分钟

  try {
    // 创建一个变量来存储累积的响应文本
    let accumulatedText = '';
    let processedLines = new Set();

    const response = await api.post('/generate-test-stream', {
      code,
      language,
      model,
    }, {
      timeout: timeout, // 覆盖默认超时设置
      responseType: 'text', // 设置响应类型为文本
      onDownloadProgress: (progressEvent) => {
        try {
          // 安全地获取响应文本
          let text = '';

          // 检查不同的属性路径，以适应不同浏览器
          if (progressEvent && progressEvent.currentTarget && progressEvent.currentTarget.response) {
            text = progressEvent.currentTarget.response;
          } else if (progressEvent && progressEvent.target && progressEvent.target.response) {
            text = progressEvent.target.response;
          } else if (progressEvent && progressEvent.response) {
            text = progressEvent.response;
          } else {
            console.log('Progress event received but no response text available:', progressEvent);
            return; // 如果没有响应文本，则退出
          }

          // 确保文本是字符串
          if (typeof text !== 'string') {
            console.log('Response is not a string:', text);
            return;
          }

          // 更新累积的文本
          accumulatedText = text;

          // 按行分割
          const lines = text.split('\n').filter(line => line.trim());

          console.log(`Received ${lines.length} lines of text`);

          // 处理每一行，但只处理新行
          lines.forEach(line => {
            try {
              // 如果已经处理过这一行，则跳过
              if (processedLines.has(line)) {
                return;
              }

              // 标记为已处理
              processedLines.add(line);

              console.log('Processing new line:', line);

              const result = JSON.parse(line);

              // 记录接收到的结果
              console.log('Parsed result:', result);

              if (onProgress && typeof onProgress === 'function') {
                // 调用回调函数
                onProgress(result);
                console.log('Called onProgress with result');
              }
            } catch (e) {
              // 只有当行不为空时才记录错误
              if (line.trim()) {
                console.error('Error parsing JSON:', e, line);
              }
            }
          });
        } catch (e) {
          console.error('Error in download progress handler:', e);
        }
      }
    });

    // 请求完成后，再次处理累积的文本，确保所有行都被处理
    console.log('Request completed, processing accumulated text');
    const finalLines = accumulatedText.split('\n').filter(line => line.trim());

    finalLines.forEach(line => {
      try {
        // 如果已经处理过这一行，则跳过
        if (processedLines.has(line)) {
          return;
        }

        // 标记为已处理
        processedLines.add(line);

        console.log('Processing final line:', line);

        const result = JSON.parse(line);

        if (onProgress && typeof onProgress === 'function') {
          onProgress(result);
          console.log('Called onProgress with final result');
        }
      } catch (e) {
        // 只有当行不为空时才记录错误
        if (line.trim()) {
          console.error('Error parsing final JSON:', e, line);
        }
      }
    });

    return response;
  } catch (error) {
    console.error('Error streaming tests:', error);
    throw error;
  }
};

// 上传文件
export const uploadFile = async (formData) => {
  return api.post('/upload-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 获取GitHub仓库列表
export const getRepositories = async (token, platform = 'github', serverUrl = '') => {
  try {
    console.log(`Fetching ${platform} repositories with token:`, token ? 'token provided' : 'no token');
    console.log(`Using server URL:`, serverUrl || 'default');

    const params = { token, platform };
    if (serverUrl && serverUrl.trim()) {
      params.server_url = serverUrl.trim();
    }

    const response = await api.get('/git/repositories', { params });
    console.log('Repositories response:', response);

    // 确保返回的是仓库数组
    if (response && response.repositories && Array.isArray(response.repositories)) {
      return response.repositories;
    } else {
      console.error('Invalid repositories response format:', response);
      throw new Error('Invalid response format: missing repositories array');
    }
  } catch (error) {
    console.error(`Error fetching ${platform} repositories:`, error);
    throw error;
  }
};

// 获取GitHub目录列表
export const getDirectories = async (repo, token, path = '', platform = 'github', serverUrl = '') => {
  try {
    console.log(`Fetching directories: repo=${repo}, path=${path}, platform=${platform}`);
    console.log(`Using server URL:`, serverUrl || 'default');

    // 确保参数有效
    if (!repo) {
      throw new Error('Repository name is required');
    }

    // GitHub仍然需要token，GitLab在URL模式下可以不需要token
    if (!token && platform === 'github') {
      throw new Error('GitHub token is required');
    }

    // 发送请求
    const params = { repo, token, path, platform };
    if (serverUrl && serverUrl.trim()) {
      params.server_url = serverUrl.trim();
    }

    const response = await api.get('/git/directories', {
      params,
      timeout: 30000, // 30秒超时
    });

    console.log('Directories response:', response);
    console.log('Response data type:', typeof response);
    console.log('Response data:', JSON.stringify(response, null, 2));

    // 确保返回的是目录数组
    if (response && response.directories && Array.isArray(response.directories)) {
      return response.directories;
    } else {
      console.error('Invalid directories response format:', response);
      throw new Error('Invalid response format: missing directories array');
    }
  } catch (error) {
    console.error('Error fetching directories:', error);
    console.error('Error details:', error.response?.data || error.message);
    throw error;
  }
};

// 保存测试到GitHub
export const saveToGit = async (tests, language, repo, path, token, platform = 'github', serverUrl = '') => {
  try {
    console.log(`Saving to ${platform}: repo=${repo}, path=${path}, language=${language}, tests=${tests.length}, server=${serverUrl || 'default'}`);

    // 确保参数有效
    if (!repo) {
      throw new Error('Repository name is required');
    }

    if (!token) {
      throw new Error(`${platform.toUpperCase()} token is required`);
    }

    if (!tests || tests.length === 0) {
      throw new Error('No tests to save');
    }

    // 构建请求数据
    const requestData = {
      tests,
      language,
      repo,
      path,
      token,
      platform,
    };

    // 如果提供了服务器地址，添加到请求中
    if (serverUrl && serverUrl.trim()) {
      requestData.server_url = serverUrl.trim();
    }

    // 发送请求
    const response = await api.post('/git/save', requestData, {
      timeout: 60000, // 60秒超时
    });

    console.log('Save to Git response:', response);
    console.log('Response data type:', typeof response);
    console.log('Response data:', JSON.stringify(response, null, 2));

    return response;
  } catch (error) {
    console.error(`Error saving to ${platform}:`, error);
    console.error('Error details:', error.response?.data || error.message);
    throw error;
  }
};

// 获取支持的语言列表
export const getLanguages = async () => {
  const response = await api.get('/languages');
  return response.languages;
};

// 获取支持的模型列表
export const getModels = async () => {
  const response = await api.get('/models');
  return response.models;
};

// 获取GitHub文件内容
export const getFileContent = async (repo, path, token, platform = 'github', serverUrl = '') => {
  try {
    console.log(`Fetching file content: repo=${repo}, path=${path}, platform=${platform}, server=${serverUrl || 'default'}`);

    const params = { repo, path, token, platform };
    if (serverUrl && serverUrl.trim()) {
      params.server_url = serverUrl.trim();
    }

    const response = await api.get('/git/file-content', { params });
    console.log('File content response:', response);
    return response;
  } catch (error) {
    console.error(`Error fetching ${platform} file content:`, error);
    throw error;
  }
};

// 克隆 Git 仓库
export const cloneRepo = async (repoUrl, token, platform = 'github', serverUrl = '') => {
  try {
    console.log(`Cloning ${platform} repository:`, repoUrl, `server: ${serverUrl || 'default'}`);

    const requestData = {
      repo_url: repoUrl,  // 统一使用repo_url字段名
      token,
      platform
    };

    // 如果提供了服务器地址，添加到请求中
    if (serverUrl && serverUrl.trim()) {
      requestData.server_url = serverUrl.trim();
    }

    const response = await api.post(`/git/${platform}/clone`, requestData, {
      timeout: 300000, // 5分钟超时
    });
    console.log('Clone response:', response);
    return response;
  } catch (error) {
    console.error(`Error cloning ${platform} repository:`, error);
    console.error('Error details:', error.response?.data || error.message);
    throw error;
  }
};

// 保持原有的 GitLab 克隆函数作为兼容性支持
export const cloneGitLabRepo = async (repoUrl, token, serverUrl = '') => {
  return cloneRepo(repoUrl, token, 'gitlab', serverUrl);
};

// 克隆 GitHub 仓库
export const cloneGitHubRepo = async (repoUrl, token, path = '') => {
  try {
    console.log('Cloning GitHub repository:', repoUrl);
    const response = await api.post('/git/github/clone', {
      repo_url: repoUrl,
      token,
      path
    }, {
      timeout: 300000, // 5分钟超时
    });
    console.log('GitHub clone response:', response);
    return response;
  } catch (error) {
    console.error('Error cloning GitHub repository:', error);
    console.error('Error details:', error.response?.data || error.message);
    throw error;
  }
};

export default api;