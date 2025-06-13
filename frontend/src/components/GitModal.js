import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, Select, Spin, Tree, message, Tooltip, Radio } from 'antd';
import {
  QuestionCircleOutlined,
  FolderOutlined,
  FileOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { getRepositories, getDirectories, saveToGit, cloneGitLabRepo, cloneGitHubRepo } from '../services/api';

const { Option } = Select;
const { DirectoryTree } = Tree;

/**
 * Git保存模态框组件
 *
 * @param {boolean} visible - 是否显示模态框
 * @param {function} onCancel - 取消回调函数
 * @param {function} onSave - 保存成功回调函数
 * @param {Array} tests - 测试结果列表
 * @param {string} language - 编程语言
 * @param {boolean} loading - 是否正在加载
 * @param {function} setLoading - 设置加载状态的函数
 * @param {Object} gitInfo - Git信息，包含token、repo和path
 * @returns {JSX.Element} Git保存模态框组件
 */
const GitModal = ({ visible, onCancel, onSave, tests, language, loading, setLoading, gitInfo, isGeneratingTests = false }) => {
  // 状态管理
  const [gitPlatform, setGitPlatform] = useState('github'); // 'github' 或 'gitlab'
  const [gitMode, setGitMode] = useState('token'); // 'token' 或 'url' (GitHub的两种模式)
  const [gitToken, setGitToken] = useState('');
  const [gitlabUrl, setGitlabUrl] = useState('');
  const [githubUrl, setGithubUrl] = useState(''); // GitHub仓库URL
  const [gitlabServerUrl, setGitlabServerUrl] = useState('https://gitlab.com'); // GitLab服务器地址
  const [githubServerUrl, setGithubServerUrl] = useState('https://github.com'); // GitHub服务器地址
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [directories, setDirectories] = useState([]);
  const [selectedPath, setSelectedPath] = useState('');
  const [tokenError, setTokenError] = useState('');
  const [useSourceGitInfo, setUseSourceGitInfo] = useState(true);
  const [treeLoading, setTreeLoading] = useState(false);
  const [loadingPaths, setLoadingPaths] = useState([]);
  const [expandedKeys, setExpandedKeys] = useState([]);

  // 重置状态
  const resetState = () => {
    setRepositories([]);
    setSelectedRepo(null);
    setDirectories([]);
    setSelectedPath('');
    setExpandedKeys([]);
    setLoadingPaths([]);
    setTreeLoading(false);
    setTokenError('');
  };

  // 从gitInfo或localStorage加载token信息
  useEffect(() => {
    if (visible) {
      if (useSourceGitInfo && gitInfo && gitInfo.token) {
        setGitToken(gitInfo.token);
        setGitPlatform(gitInfo.platform || 'github');
        setGitMode(gitInfo.mode || 'token');
        if (gitInfo.gitlabUrl) {
          setGitlabUrl(gitInfo.gitlabUrl);
        }
        if (gitInfo.githubUrl) {
          setGithubUrl(gitInfo.githubUrl);
        }
      } else {
        const savedToken = localStorage.getItem('git_token');
        const savedPlatform = localStorage.getItem('git_platform');
        const savedMode = localStorage.getItem('git_mode');
        const savedGitlabUrl = localStorage.getItem('gitlab_url');
        const savedGithubUrl = localStorage.getItem('github_url');
        if (savedToken) {
          setGitToken(savedToken);
          setGitPlatform(savedPlatform || 'github');
          setGitMode(savedMode || 'token');
          if (savedGitlabUrl) {
            setGitlabUrl(savedGitlabUrl);
          }
          if (savedGithubUrl) {
            setGithubUrl(savedGithubUrl);
          }
        }
      }
    }

    if (!visible) {
      resetState();
    }
  }, [visible, gitInfo, useSourceGitInfo]);

  // 加载仓库列表
  const handleLoadRepositories = async () => {
    if (!gitToken) {
      setTokenError('Please enter a Git token!');
      message.error('Please enter a Git token!', 3);
      return;
    }

    // 验证URL模式下的必要输入
    if (gitMode === 'url') {
      const repoUrl = gitPlatform === 'github' ? githubUrl : gitlabUrl;
      if (!repoUrl) {
        setTokenError(`Please enter ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} repository URL!`);
        message.error(`Please enter ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} repository URL!`, 3);
        return;
      }
    }

    setTokenError('');
    setLoading(true);

    try {
      // 保存认证信息
      localStorage.setItem('git_token', gitToken);
      localStorage.setItem('git_platform', gitPlatform);
      localStorage.setItem('git_mode', gitMode);
      if (gitMode === 'url') {
        if (gitPlatform === 'github') {
          localStorage.setItem('github_url', githubUrl);
        } else {
          localStorage.setItem('gitlab_url', gitlabUrl);
        }
      }

      if (gitMode === 'token') {
        // 令牌模式：获取仓库列表
        const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
        const repos = await getRepositories(gitToken, gitPlatform, serverUrl);
        setRepositories(repos);

        if (repos.length === 0) {
          message.warning(`No repositories found for this ${gitPlatform} token.`, 3);
        } else {
          message.success(`Found ${repos.length} repositories`, 3);
        }
      } else {
        // URL模式：直接克隆指定仓库
        const repoUrl = gitPlatform === 'github' ? githubUrl : gitlabUrl;

        if (gitPlatform === 'github') {
          const repoInfo = await cloneGitHubRepo(repoUrl, gitToken);
          const repoData = {
            name: repoInfo.repo_info.name,
            full_name: repoInfo.repo_info.full_name,
            url: repoInfo.repo_info.url,
            description: repoInfo.repo_info.description
          };
          setRepositories([repoData]);
          message.success(`Successfully cloned GitHub repository: ${repoData.name}`, 3);
          handleSelectRepository(repoData);
        } else {
          const cloneResponse = await cloneGitLabRepo(repoUrl, gitToken, gitlabServerUrl);

          // 检查响应结构
          if (!cloneResponse || !cloneResponse.data) {
            throw new Error('Invalid clone response structure');
          }

          const responseData = cloneResponse.data;

          // 从克隆响应中提取仓库信息
          let repoInfo;

          // 构建fallback的full_name
          const fallbackFullName = repoUrl.split('/').slice(-2).join('/').replace('.git', '');

          if (responseData.repo_info) {
            // 使用服务器返回的完整仓库信息
            repoInfo = { ...responseData.repo_info };
            // 验证服务器返回的full_name
            if (!repoInfo.full_name || repoInfo.full_name.trim() === '') {
              console.warn('Server repo_info has empty full_name, using fallback');
              repoInfo.full_name = fallbackFullName;
            }
          } else {
            // 如果没有repo_info，构建基本信息
            repoInfo = {
              name: 'Repository',
              full_name: fallbackFullName,
              clone_path: responseData.clone_path
            };
          }

          // 最终验证full_name字段
          if (!repoInfo.full_name || repoInfo.full_name.trim() === '') {
            console.error('Critical: full_name is still empty, forcing fallback');
            repoInfo.full_name = fallbackFullName;
          }

          // 确保name字段也存在
          if (!repoInfo.name || repoInfo.name.trim() === '') {
            repoInfo.name = repoInfo.full_name.split('/').pop() || 'Repository';
          }
          setRepositories([repoInfo]);
          message.success(`Successfully cloned GitLab repository: ${repoInfo.name || 'Repository'}`, 3);
          handleSelectRepository(repoInfo);
        }
      }
    } catch (error) {
      console.error('Error loading repositories:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      setTokenError(`Failed to ${gitMode === 'token' ? 'load repositories' : 'clone repository'}: ${errorMessage}`);
      message.error(`Failed to ${gitMode === 'token' ? 'load repositories' : 'clone repository'}: ${errorMessage}`, 3);
    } finally {
      setLoading(false);
    }
  };

  // 选择仓库
  const handleSelectRepository = async (repo) => {
    // 验证repo对象
    if (!repo) {
      message.error('Repository information is missing', 3);
      console.error('handleSelectRepository: repo is null or undefined');
      return;
    }

    // 验证并修复full_name字段
    if (!repo.full_name || repo.full_name.trim() === '') {
      console.error('Repository full_name is missing or empty:', repo);

      // 尝试从其他字段构建full_name
      if (repo.name) {
        // 如果有name但没有full_name，可能是单独的仓库名
        console.warn('Attempting to construct full_name from name:', repo.name);
        // 这里需要更多信息来构建完整路径，暂时使用name作为fallback
        repo.full_name = repo.name;
      } else {
        message.error('Repository full_name is missing and cannot be constructed', 3);
        return;
      }
    }
    setSelectedRepo(repo);
    setDirectories([]);
    setSelectedPath('');
    setLoading(true);

    try {
      const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
      const dirs = await getDirectories(repo.full_name, gitToken, '', gitPlatform, serverUrl);

      const treeData = dirs.map(item => ({
        title: item.name,
        key: item.path,
        isLeaf: item.type === 'file',
        selectable: true, // 允许选择所有项目，包括文件和文件夹
        children: item.type === 'dir' ? [] : null,
        icon: item.type === 'file'
          ? <FileOutlined />
          : <FolderOutlined />,
        rawData: item
      }));
      setDirectories(treeData);
    } catch (error) {
      console.error('Error loading directories:', error);
      message.error('Failed to load directories: ' + (error.response?.data?.detail || error.message), 3);
    } finally {
      setLoading(false);
    }
  };

  // 更新目录树数据
  const updateTreeData = (list, key, children) => {
    return list.map(node => {
      if (node.key === key) {
        return { ...node, children };
      }
      if (node.children) {
        return {
          ...node,
          children: updateTreeData(node.children, key, children)
        };
      }
      return node;
    });
  };

  // 加载目录内容
  const handleLoadDirectory = async (treeNode) => {
    const { key } = treeNode;
    if (!selectedRepo || !gitToken) {
      message.error('Repository or token information is missing', 3);
      return [];
    }

    setTreeLoading(true);
    setLoadingPaths(prev => [...prev, key]);

    try {
      const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
      const dirs = await getDirectories(selectedRepo.full_name, gitToken, key, gitPlatform, serverUrl);

      const treeNodes = dirs.map(item => ({
        title: item.name,
        key: item.path,
        isLeaf: item.type === 'file',
        selectable: true, // 允许选择所有项目，包括文件和文件夹
        children: item.type === 'dir' ? [] : null,
        icon: item.type === 'file'
          ? <FileOutlined />
          : (loadingPaths.includes(item.path)
              ? <LoadingOutlined />
              : <FolderOutlined />),
        rawData: item
      }));

      // 更新目录树数据
      setDirectories(prevDirectories => {
        const newDirectories = updateTreeData(prevDirectories, key, treeNodes);
        return newDirectories;
      });

      return treeNodes;
    } catch (error) {
      console.error('Error loading directory:', error);
      message.error('Failed to load directory: ' + (error.response?.data?.detail || error.message), 3);
      return [];
    } finally {
      setTreeLoading(false);
      setLoadingPaths(prev => prev.filter(path => path !== key));
    }
  };

  // 选择目录
  const handleSelectDirectory = async (selectedKeys, info) => {
    try {
      if (selectedKeys.length > 0) {
        const path = selectedKeys[0];
        setSelectedPath(path);

        // 如果点击的是目录，自动展开并加载内容
        if (info && info.node && !info.node.isLeaf) {
          // 自动展开文件夹
          if (!expandedKeys.includes(path)) {
            setExpandedKeys(prev => [...prev, path]);
          }

          // 强制加载子内容（即使已经有内容也重新加载以确保最新）
          try {
            await handleLoadDirectory(info.node);
          } catch (error) {
            console.error('Auto-load directory failed:', error);
          }
        }

        message.success(`Selected directory: ${path}`, 3);
      }
    } catch (error) {
      message.error('Failed to select directory: ' + error.message, 3);
    }
  };

  // 保存到Git
  const handleSaveToGit = async () => {
    if (!selectedRepo || !selectedPath) {
      message.error('Please select repository and directory!', 3);
      return;
    }

    if (tests.length === 0) {
      message.error('No tests to save!', 3);
      return;
    }

    // 验证token
    if (!gitToken || gitToken.trim() === '') {
      message.error(`${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token is required for saving tests. Please enter your token above.`, 3);
      return;
    }
    setLoading(true);
    message.loading({ content: 'Saving tests...', key: 'saveGit', duration: 3 });

    try {
      const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
      const result = await saveToGit(tests, language, selectedRepo.full_name, selectedPath, gitToken, gitPlatform, serverUrl);
      message.success({ content: `Tests saved successfully! Created ${result.urls.length} files`, key: 'saveGit', duration: 3 });
      onSave();
    } catch (error) {
      console.error('Error saving to Git:', error);
      console.error('Error details:', error.response?.data || error.message);

      // 提供更详细的错误信息
      let errorMessage = 'Unknown error occurred';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;

        // 特殊处理401错误
        if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
          errorMessage = `Authentication failed. Please check your ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token and ensure it has the required permissions (api, write_repository).`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      message.error({ content: 'Failed to save: ' + errorMessage, key: 'saveGit', duration: 3 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={`Save to ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}`}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          key="save"
          type="primary"
          onClick={handleSaveToGit}
          loading={loading}
          disabled={!selectedRepo || !selectedPath || !gitToken || gitToken.trim() === ''}
          title={
            !gitToken || gitToken.trim() === ''
              ? 'Personal Access Token is required to save tests'
              : !selectedRepo || !selectedPath
                ? 'Please select repository and directory first'
                : 'Save tests to the selected directory'
          }
        >
          {(!gitToken || gitToken.trim() === '')
            ? '🔐 Token Required to Save'
            : 'Save to Selected Directory'
          }
        </Button>
      ]}
      width={800}
    >
      <Spin spinning={loading && !isGeneratingTests}>
        {/* Git平台选择 */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>Select Platform:</label>
          <Radio.Group
            value={gitPlatform}
            onChange={async (e) => {
              try {
                setGitPlatform(e.target.value);
                resetState();
                setLoading(false);
                // 重置模式为token
                if (e.target.value === 'github') {
                  setGitMode('token');
                }
              } catch (error) {
                message.error('Failed to change platform: ' + error.message, 3);
              }
            }}
          >
            <Radio.Button value="github">GitHub</Radio.Button>
            <Radio.Button value="gitlab">GitLab</Radio.Button>
          </Radio.Group>
        </div>

        {/* 访问模式选择 - 对GitHub和GitLab都显示 */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>
            {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Access Mode:
          </label>
          <Radio.Group
            value={gitMode}
            onChange={async (e) => {
              try {
                setGitMode(e.target.value);
                resetState();
                setLoading(false);
              } catch (error) {
                message.error('Failed to change mode: ' + error.message, 3);
              }
            }}
          >
            <Radio.Button value="token">
              <Tooltip title={`Use ${gitPlatform} token to browse and select from your repositories`}>
                🔑 Browse Repositories
              </Tooltip>
            </Radio.Button>
            <Radio.Button value="url">
              <Tooltip title={`Directly input ${gitPlatform} repository URL to clone`}>
                🔗 Direct Repository URL
              </Tooltip>
            </Radio.Button>
          </Radio.Group>
        </div>

        {/* 源Git信息选项 */}
        {gitInfo && gitInfo.token && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>
              Use source Git info:
              <Tooltip title="Use Git information from source code">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Tooltip>
            </label>
            <div>
              <Button
                type={useSourceGitInfo ? "primary" : "default"}
                onClick={() => {
                  resetState();
                  setUseSourceGitInfo(true);
                  if (gitInfo.token) {
                    setGitToken(gitInfo.token);
                    setGitPlatform(gitInfo.platform || 'github');
                    setGitMode(gitInfo.mode || 'token');
                    if (gitInfo.gitlabUrl) {
                      setGitlabUrl(gitInfo.gitlabUrl);
                    }
                    if (gitInfo.githubUrl) {
                      setGithubUrl(gitInfo.githubUrl);
                    }
                  }
                }}
                style={{ marginRight: 8 }}
              >
                Use Source Git Info
              </Button>
              <Button
                type={!useSourceGitInfo ? "primary" : "default"}
                onClick={() => {
                  resetState();
                  setUseSourceGitInfo(false);
                }}
              >
                Manual Selection
              </Button>
            </div>
          </div>
        )}

        {/* 操作步骤提示 */}
        {(!useSourceGitInfo || !gitInfo || !gitInfo.token) && (
          <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '4px' }}>
            <div style={{ fontSize: '14px', color: '#52c41a', fontWeight: 'bold', marginBottom: '4px' }}>
              📋 Save Tests to {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} - Step by Step:
            </div>
            <div style={{ fontSize: '12px', color: '#389e0d' }}>
              1️⃣ <strong>Enter your {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token</strong> (required for saving)<br/>
              2️⃣ Click "Load Repository Structure" to browse directories<br/>
              3️⃣ Select the target directory from the tree<br/>
              4️⃣ Click "Save to Selected Directory" to save your tests<br/>
              <br/>
              <span style={{ color: '#d46b08' }}>
                ⚠️ Note: Personal Access Token is mandatory for saving tests to ensure security.
              </span>
            </div>
          </div>
        )}

        {/* Git认证信息输入 */}
        {(!useSourceGitInfo || !gitInfo || !gitInfo.token) && (
          <div style={{ marginBottom: 16 }}>
            {/* Token输入 - 两种模式都需要 */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                <span style={{ color: '#d46b08', fontWeight: 'bold' }}>🔐 </span>
                {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token:
                <span style={{ color: '#ff4d4f', marginLeft: 4 }}>*</span>
                <Tooltip title={`Personal Access Token is required for saving tests. Token needs 'api' and 'write_repository' permissions.`}>
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </label>
              <Input.Password
                value={gitToken}
                onChange={e => setGitToken(e.target.value)}
                style={{
                  width: '100%',
                  borderColor: (!gitToken || gitToken.trim() === '') ? '#ffa940' : undefined
                }}
                placeholder={`🔑 Required: Enter your ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} token to enable saving`}
                status={tokenError ? 'error' : (!gitToken || gitToken.trim() === '') ? 'warning' : ''}
              />
              {(!gitToken || gitToken.trim() === '') && (
                <div style={{
                  marginTop: 4,
                  fontSize: '12px',
                  color: '#d46b08'
                }}>
                  ⚠️ Token is required for saving tests. Browsing works without token.
                </div>
              )}
              {gitToken && gitToken.trim() !== '' && (
                <div style={{
                  marginTop: 4,
                  fontSize: '12px',
                  color: '#52c41a'
                }}>
                  ✅ Token provided - saving enabled
                </div>
              )}
            </div>

            {/* 服务器地址输入 - GitLab需要自定义服务器地址 */}
            {gitPlatform === 'gitlab' && (
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 8 }}>
                  GitLab Server URL:
                  <Tooltip title="Enter your GitLab server address (e.g., http://172.16.1.30 or https://gitlab.com)">
                    <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                  </Tooltip>
                </label>
                <Input
                  value={gitlabServerUrl}
                  onChange={e => setGitlabServerUrl(e.target.value)}
                  style={{ width: '100%' }}
                  placeholder="e.g., http://172.16.1.30 or https://gitlab.com"
                />
              </div>
            )}

            {/* GitHub服务器地址输入 - 可选，默认为github.com */}
            {gitPlatform === 'github' && (
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 8 }}>
                  GitHub Server URL (Optional):
                  <Tooltip title="Enter custom GitHub server address (leave default for github.com)">
                    <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                  </Tooltip>
                </label>
                <Input
                  value={githubServerUrl}
                  onChange={e => setGithubServerUrl(e.target.value)}
                  style={{ width: '100%' }}
                  placeholder="https://github.com (default)"
                />
              </div>
            )}

            {/* 仓库URL输入 - 仅在URL模式下显示 */}
            {gitMode === 'url' && (
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 8 }}>
                  {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Repository URL:
                  <Tooltip title={`Enter your ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} repository URL`}>
                    <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                  </Tooltip>
                </label>
                <Input
                  value={gitPlatform === 'github' ? githubUrl : gitlabUrl}
                  onChange={e => {
                    if (gitPlatform === 'github') {
                      setGithubUrl(e.target.value);
                    } else {
                      setGitlabUrl(e.target.value);
                    }
                  }}
                  style={{ width: '100%' }}
                  placeholder={`e.g., https://${gitPlatform === 'github' ? 'github.com' : 'gitlab.com'}/username/repo.git`}
                />
              </div>
            )}

            <Button
              onClick={handleLoadRepositories}
              type="primary"
              size="large"
              style={{ width: '100%' }}
            >
              {gitMode === 'token'
                ? `🔍 Browse ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Repositories`
                : `📂 Load ${gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Repository Structure`
              }
            </Button>

            {tokenError && (
              <div style={{
                color: '#ff4d4f',
                marginTop: 8,
                padding: '8px 12px',
                backgroundColor: '#fff2f0',
                border: '1px solid #ffccc7',
                borderRadius: '4px'
              }}>
                ⚠️ {tokenError}
              </div>
            )}
          </div>
        )}

        {/* 仓库选择（令牌模式下显示） */}
        {gitMode === 'token' && repositories.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>
              📚 Select Repository ({repositories.length} found):
            </label>
            <Select
              style={{ width: '100%' }}
              placeholder={`Select a ${gitPlatform} repository`}
              onChange={async (value) => {
                try {
                  const repo = repositories.find(r =>
                    r.full_name === value || r.name === value
                  );
                  if (repo) {
                    await handleSelectRepository(repo);
                    message.success(`Selected repository: ${repo.name || repo.full_name}`, 3);
                  }
                } catch (error) {
                  message.error('Failed to select repository: ' + error.message, 3);
                }
              }}
              value={selectedRepo?.full_name || selectedRepo?.name}
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {repositories.map(repo => (
                <Option
                  key={repo.full_name || repo.name}
                  value={repo.full_name || repo.name}
                  title={repo.description}
                >
                  <div>
                    <strong>{repo.full_name || repo.name}</strong>
                    {repo.description && (
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {repo.description}
                      </div>
                    )}
                  </div>
                </Option>
              ))}
            </Select>
          </div>
        )}

        {/* Token验证提示 */}
        {(!gitToken || gitToken.trim() === '') && directories.length > 0 && (
          <div style={{
            marginBottom: 16,
            padding: '12px',
            backgroundColor: '#fff7e6',
            border: '1px solid #ffd591',
            borderRadius: '4px'
          }}>
            <div style={{ fontSize: '14px', color: '#d46b08', fontWeight: 'bold', marginBottom: '4px' }}>
              🔐 Personal Access Token Required for Saving
            </div>
            <div style={{ fontSize: '12px', color: '#ad6800' }}>
              To save tests to the repository, please enter your {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token above.
              The token is required for write operations to ensure security.
            </div>
          </div>
        )}

        {/* 目录树 */}
        {directories.length > 0 && (
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>
              Select Directory:
              {treeLoading && <Spin size="small" style={{ marginLeft: 8 }} />}
            </label>

            <div style={{
              height: '300px',
              overflow: 'auto',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              padding: '8px',
              backgroundColor: '#fafafa'
            }}>
              <DirectoryTree
                treeData={directories}
                onSelect={handleSelectDirectory}
                loadData={handleLoadDirectory}
                selectedKeys={selectedPath ? [selectedPath] : []}
                expandedKeys={expandedKeys}
                onExpand={(keys, { expanded, node }) => {
                  setExpandedKeys(keys);
                  // 如果是展开操作且节点没有子内容，则加载内容
                  if (expanded && (!node.children || node.children.length === 0)) {
                    handleLoadDirectory(node);
                  }
                }}
              />
            </div>

            {selectedPath && (
              <div style={{ marginTop: 8 }}>
                <div>Selected path: <strong>{selectedPath}</strong></div>
                {(!gitToken || gitToken.trim() === '') && (
                  <div style={{
                    marginTop: 4,
                    fontSize: '12px',
                    color: '#d46b08',
                    fontStyle: 'italic'
                  }}>
                    ⚠️ Personal Access Token required to save to this directory
                  </div>
                )}
                {gitToken && gitToken.trim() !== '' && (
                  <div style={{
                    marginTop: 4,
                    fontSize: '12px',
                    color: '#52c41a',
                    fontStyle: 'italic'
                  }}>
                    ✅ Ready to save (Token provided)
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Spin>
    </Modal>
  );
};

export default GitModal;
