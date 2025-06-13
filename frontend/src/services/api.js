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
  // 为大型代码文件和特定模型设置更长的超时时间
  let timeout = code.length > 10000 ? 600000 : 300000; // 10分钟或5分钟

  // 为 DeepSeek-R1 模型设置更长的超时时间
  if (model === 'deepseek-R1') {
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

    // 由于响应拦截器已经返回了 response.data，这里直接返回 response
    return response;
  } catch (error) {
    console.error('Error generating tests directly:', error);
    throw error;
  }
};

// 流式生成测试 - 使用EventSource进行服务器发送事件
export const generateTestsStream = async (code, language, model, onProgress, onTaskId = null) => {
  return new Promise((resolve, reject) => {
    try {
      // 使用XMLHttpRequest进行流式处理，这是最可靠的方法
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/generate-test-stream', true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('user-id', 'anonymous'); // 添加用户ID头

      let processedLength = 0;
      let processedLines = new Set();

      xhr.onprogress = function() {
        // 获取新的响应文本
        const responseText = xhr.responseText;
        const newText = responseText.substring(processedLength);
        processedLength = responseText.length;

        if (newText) {
          // 按行分割新文本
          const lines = newText.split('\n');

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) continue;

            // 避免重复处理
            if (processedLines.has(trimmedLine)) {
              continue;
            }
            processedLines.add(trimmedLine);

            try {
              const result = JSON.parse(trimmedLine);
              // 如果收到任务ID，通知调用者
              if (result.task_id && onTaskId && typeof onTaskId === 'function') {
                onTaskId(result.task_id);
              }

              if (onProgress && typeof onProgress === 'function') {
                onProgress(result);
              }
            } catch (e) {
              console.error('Error parsing JSON line:', e, trimmedLine);
            }
          }
        }
      };

      xhr.onload = function() {
        if (xhr.status === 200) {
          resolve({ status: 'completed' });
        } else {
          console.error('XHR failed with status:', xhr.status);
          reject(new Error(`HTTP error! status: ${xhr.status}`));
        }
      };

      xhr.onerror = function() {
        console.error('XHR error event');
        reject(new Error('Network error'));
      };

      xhr.ontimeout = function() {
        console.error('XHR timeout event');
        reject(new Error('Request timeout'));
      };

      // 设置30分钟超时
      xhr.timeout = 1800000;
      xhr.send(JSON.stringify({
        code,
        language,
        model
      }));

    } catch (error) {
      console.error('Error setting up streaming request:', error);
      reject(error);
    }
  });
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
    const params = { token, platform };
    if (serverUrl && serverUrl.trim()) {
      params.server_url = serverUrl.trim();
    }

    const response = await api.get('/git/repositories', { params });
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
  return {
    models: response.models,
    default_model: response.default_model
  };
};

// 获取队列状态
export const getQueueStatus = async () => {
  const response = await api.get('/queue/status');
  return response;
};

// 获取任务状态
export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/queue/task/${taskId}`, {
    headers: {
      'user-id': 'anonymous' // 可以根据实际用户系统调整
    }
  });
  return response;
};

// 取消任务
export const cancelTask = async (taskId) => {
  const response = await api.delete(`/queue/task/${taskId}`, {
    headers: {
      'user-id': 'anonymous' // 可以根据实际用户系统调整
    }
  });
  return response;
};

// 获取GitHub文件内容
export const getFileContent = async (repo, path, token, platform = 'github', serverUrl = '') => {
  try {
    const params = { repo, path, token, platform };
    if (serverUrl && serverUrl.trim()) {
      params.server_url = serverUrl.trim();
    }

    const response = await api.get('/git/file-content', { params });
    return response;
  } catch (error) {
    console.error(`Error fetching ${platform} file content:`, error);
    throw error;
  }
};

// 克隆 Git 仓库
export const cloneRepo = async (repoUrl, token, platform = 'github', serverUrl = '') => {
  try {
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
    const response = await api.post('/git/github/clone', {
      repo_url: repoUrl,
      token,
      path
    }, {
      timeout: 300000, // 5分钟超时
    });
    return response;
  } catch (error) {
    console.error('Error cloning GitHub repository:', error);
    console.error('Error details:', error.response?.data || error.message);
    throw error;
  }
};

// AI配置管理API
export const getAIModels = async () => {
  const response = await api.get('/ai-config/models');
  return response;
};

export const verifyAIPassword = async (password) => {
  const response = await api.post('/ai-config/verify-password', { password });
  return response;
};

export const changeAIPassword = async (oldPassword, newPassword) => {
  const response = await api.post('/ai-config/change-password', {
    old_password: oldPassword,
    new_password: newPassword
  });
  return response;
};

export const addAIModel = async (password, modelName, modelConfig) => {
  const response = await api.post('/ai-config/add-model', {
    password,
    model_name: modelName,
    model_config: modelConfig
  });
  return response;
};

export const updateAIModel = async (password, modelName, modelConfig) => {
  const response = await api.post('/ai-config/update-model', {
    password,
    model_name: modelName,
    model_config: modelConfig
  });
  return response;
};

export const deleteAIModel = async (password, modelName) => {
  const response = await api.post('/ai-config/delete-model', {
    password,
    model_name: modelName
  });
  return response;
};

export const setDefaultAIModel = async (password, modelName) => {
  const response = await api.post('/ai-config/set-default-model', {
    password,
    model_name: modelName
  });
  return response;
};

export default api;
