import React, { useState, useEffect } from 'react';
import FileSystemCache from '../services/FileSystemCache';
import { Card, Radio, Input, Button, Select, Tree, message, Tooltip, List, Switch, Divider } from 'antd';

import MessageDisplay from './MessageDisplay';
import LoadingIndicator from './LoadingIndicator';
import {
  QuestionCircleOutlined,
  GithubOutlined,
  GitlabOutlined,
  FileOutlined,
  FolderOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { getRepositories, getDirectories, cloneGitLabRepo } from '../services/api';

const { Option } = Select;

const GitSourceSelector = ({ onCodeFetched, loading, setLoading }) => {
  const [gitPlatform, setGitPlatform] = useState('github');
  const [gitMode, setGitMode] = useState('token');
  const [gitToken, setGitToken] = useState('');
  const [useCache, setUseCache] = useState(true);
  const [cacheStats, setCacheStats] = useState(null);
  const [gitlabUrl, setGitlabUrl] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [githubServerUrl, setGithubServerUrl] = useState('https://github.com');
  const [gitlabServerUrl, setGitlabServerUrl] = useState('https://gitlab.com');
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [directories, setDirectories] = useState([]);
  const [selectedPath, setSelectedPath] = useState('');

  const [tokenError, setTokenError] = useState('');
  const [loadedFiles, setLoadedFiles] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [info, setInfo] = useState('');
  const [loadingType, setLoadingType] = useState('default');
  const [loadingMessage, setLoadingMessage] = useState('');
  const [progress, setProgress] = useState(undefined);

  const clearErrors = () => {
    setError('');
    setWarning('');
    setInfo('');
    setTokenError('');
  };

  const updateProgress = (value) => {
    setProgress(value);
  };

  const handleError = (error, type) => {
    console.error(`${type}错误:`, error);
    const errorMessage = error.response?.data?.detail || error.message || `${type}操作失败`;
    setError(errorMessage);
    if (type === 'token') {
      setTokenError(errorMessage);
    }
    message.error(errorMessage, 3);
  };

  const updateCacheStats = async () => {
    try {
      const stats = FileSystemCache.getStatus();
      setCacheStats(stats);
    } catch (error) {
      console.error('Failed to update cache stats:', error);
    }
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('git_token');
    const savedPlatform = localStorage.getItem('git_platform');
    const savedMode = localStorage.getItem('git_mode');
    const savedGitlabUrl = localStorage.getItem('gitlab_url');
    const savedGithubUrl = localStorage.getItem('github_url');
    const savedGithubServerUrl = localStorage.getItem('github_server_url');
    const savedGitlabServerUrl = localStorage.getItem('gitlab_server_url');

    const statsInterval = setInterval(updateCacheStats, 30000);
    updateCacheStats();

    if (savedToken) {
      setGitToken(savedToken);
      if (savedPlatform) {
        setGitPlatform(savedPlatform);
      }
      if (savedMode) {
        setGitMode(savedMode);
      }
      if (savedGitlabUrl) {
        setGitlabUrl(savedGitlabUrl);
      }
      if (savedGithubUrl) {
        setGithubUrl(savedGithubUrl);
      }
    }

    if (savedGithubServerUrl) {
      setGithubServerUrl(savedGithubServerUrl);
    }
    if (savedGitlabServerUrl) {
      setGitlabServerUrl(savedGitlabServerUrl);
    }

    return () => {
      clearInterval(statsInterval);
      localStorage.setItem('use_cache', useCache.toString());
    };
  }, [useCache]);

  const handleLoadRepositories = async () => {
    clearErrors();

    if (gitMode === 'token' && !gitToken) {
      handleError('请输入访问令牌！', 'token');
      return;
    }

    if (gitMode === 'url') {
      const repoUrl = gitPlatform === 'github' ? githubUrl : gitlabUrl;
      if (!repoUrl) {
        handleError(`请输入${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库地址！`, 'token');
        return;
      }
    }

  setLoading(true);
  setLoadingType('loading');
  setLoadingMessage('正在加载仓库...');
  setProgress(0);

  try {
    const cachedData = useCache && FileSystemCache.getRepository(gitPlatform, `repos_${gitToken}`);
    if (cachedData) {
      setRepositories(cachedData);
      setInfo('从缓存加载仓库数据');
      return;
    }

    if (gitMode === 'token') {
      localStorage.setItem('git_token', gitToken);
    }
    localStorage.setItem('git_platform', gitPlatform);
    localStorage.setItem('git_mode', gitMode);
    localStorage.setItem('github_server_url', githubServerUrl);
    localStorage.setItem('gitlab_server_url', gitlabServerUrl);

    if (gitMode === 'url') {
      if (gitPlatform === 'github') {
        localStorage.setItem('github_url', githubUrl);
      } else {
        localStorage.setItem('gitlab_url', gitlabUrl);
      }
    }

    updateProgress(20);

    if (gitMode === 'token') {
      setLoadingMessage('正在获取仓库列表...');

      if (gitPlatform === 'github') {
        const repos = await getRepositories(gitToken, 'github', githubServerUrl);

        if (useCache) {
          FileSystemCache.cacheRepository(gitPlatform, `repos_${gitToken}`, repos);
        }

        setRepositories(repos);
        setSelectedRepo(null);
        setDirectories([]);
        setSelectedPath('');

        if (repos.length === 0) {
          setWarning('未找到仓库。请确保您有权限访问仓库。');
        } else {
          setInfo(`成功加载 ${repos.length} 个仓库`);
        }
      } else {
        const repos = await getRepositories(gitToken, 'gitlab', gitlabServerUrl);

        if (useCache) {
          FileSystemCache.cacheRepository(gitPlatform, `repos_${gitToken}`, repos);
        }

        setRepositories(repos);
        setSelectedRepo(null);
        setDirectories([]);
        setSelectedPath('');

        if (repos.length === 0) {
          setWarning('未找到仓库。请确保您有权限访问仓库。');
        } else {
          setInfo(`成功加载 ${repos.length} 个仓库`);
        }
      }
    } else {
      const repoUrl = gitPlatform === 'github' ? githubUrl : gitlabUrl;
      setLoadingMessage(`正在克隆${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库...`);
      updateProgress(30);

      const result = await cloneGitLabRepo(repoUrl, '');
      if (result.success) {
        const repoInfo = {
          full_name: repoUrl,
          clone_path: result.clone_path
        };
        setRepositories([repoInfo]);
        await handleRepoChange(repoUrl);
        setInfo('仓库克隆成功');
      } else {
        throw new Error('克隆仓库失败');
      }
    }
  } catch (error) {
    handleError(error.message || '加载仓库失败', 'repo');
  } finally {
    setLoading(false);
    setLoadingType('default');
    setProgress(undefined);
    setLoadingMessage('');
  }
  };

  const handleRepoChange = async (value) => {
    clearErrors();
    setSelectedRepo(value);
    setDirectories([]);
    setSelectedPath('');

    if (!value) return;

    const repo = repositories.find(r => r.full_name === value);
    if (repo) {
      setActiveRepo(repo);
    }

    setLoading(true);
    setLoadingType('loading');
    setLoadingMessage('正在加载仓库目录...');
    setProgress(0);

    try {
      updateProgress(30);
      let dirs;

      if (useCache) {
        dirs = FileSystemCache.getDirectory(gitPlatform, value, '');
      }
      
      if (!dirs) {
        const token = gitMode === 'token' ? gitToken : '';
        const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
        dirs = await getDirectories(value, token, '', gitPlatform, serverUrl);
        if (useCache) {
          FileSystemCache.cacheDirectory(gitPlatform, value, '', dirs);
        }
      }
      
      updateProgress(70);
      setLoadingMessage('正在处理目录数据...');
      setDirectories(buildTreeData(dirs));
      updateProgress(100);
      setInfo('目录加载完成');
    } catch (error) {
      handleError(error, 'directory');
    } finally {
      setLoading(false);
      setLoadingType('default');
      setProgress(undefined);
      setLoadingMessage('');
    }
  };

  const buildTreeData = (dirs) => {
    return dirs.map(dir => ({
      title: dir.name,
      key: dir.path,
      isLeaf: dir.type === 'file',
      children: dir.type === 'dir' ? [] : null,
      icon: dir.type === 'dir'
        ? <FolderOutlined style={{ color: '#faad14' }} />
        : getFileIcon(dir.name)
    }));
  };

  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.py')) return <FileTextOutlined style={{ color: '#3572A5' }} />;
    if (fileName.endsWith('.java')) return <FileTextOutlined style={{ color: '#b07219' }} />;
    if (fileName.endsWith('.go')) return <FileTextOutlined style={{ color: '#00ADD8' }} />;
    if (fileName.endsWith('.cpp') || fileName.endsWith('.h') || fileName.endsWith('.hpp')) 
      return <FileTextOutlined style={{ color: '#f34b7d' }} />;
    if (fileName.endsWith('.cs')) return <FileTextOutlined style={{ color: '#178600' }} />;
    return <FileOutlined />;
  };

  const updateTreeData = (list, key, children) => {
    const updatedList = list.map(node => {
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

    setDirectories(updatedList);
    return updatedList;
  };

  // 处理文件选择
  const handleFileSelect = async (selectedKeys, info) => {
    try {
      clearErrors();
      if (selectedKeys.length === 0) return;

      const path = selectedKeys[0];
      setSelectedPath(path);

      if (info.node.isLeaf) {
        setLoadingType('loading');
        setLoadingMessage('正在加载文件...');
        setProgress(0);

        try {
          const newFile = {
            path: path,
            name: info.node.title,
            type: getFileType(info.node.title),
            repo: selectedRepo,
            repoDetails: activeRepo,
            platform: gitPlatform,
            loadedAt: new Date()
          };

          updateProgress(30);


          setLoadedFiles(prevFiles => {
            const fileExists = prevFiles.some(f =>
              f.path === path && f.repo === selectedRepo && f.platform === gitPlatform
            );
            if (!fileExists) {
              return [...prevFiles, newFile];
            }
            return prevFiles;
          });

          updateProgress(60);

          if (onCodeFetched) {
            // URL模式下不需要令牌，传递空字符串
            const token = gitMode === 'token' ? gitToken : '';
            const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
            await onCodeFetched(gitPlatform, path, token, selectedRepo, serverUrl);
          }

          updateProgress(100);
          setInfo('文件加载完成');
        } catch (error) {
          handleError(error, 'file');
        } finally {
          setLoadingType('default');
          setProgress(undefined);
          setLoadingMessage('');
        }
      } else {
        // 处理文件夹点击：自动展开并加载内容
        await handleDirectoryExpand(path, info.node);
      }
    } catch (error) {
      console.error('File selection error:', error);
      setError('Failed to select file: ' + error.message);
    }
  };

  // 处理目录展开
  const handleDirectoryExpand = async (path, node) => {
    // 如果目录已经展开且有内容，则收起
    if (expandedKeys.includes(path) && node.children && node.children.length > 0) {
      setExpandedKeys(prev => prev.filter(key => key !== path));
      return;
    }

    // 如果目录还没有加载内容，则加载
    if (!node.children || node.children.length === 0) {
      setLoading(true);
      setLoadingType('loading');
      setLoadingMessage('正在加载目录...');
      setProgress(0);

      try {
        updateProgress(40);
        // URL模式下不需要令牌
        const token = gitMode === 'token' ? gitToken : '';
        const serverUrl = gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl;
        const dirs = await getDirectories(selectedRepo, token, path, gitPlatform, serverUrl);
        updateProgress(70);
        if (dirs && dirs.length > 0) {
          updateTreeData(directories, path, buildTreeData(dirs));
          setInfo('目录加载完成');
        } else {
          setWarning('该目录为空');
        }
        updateProgress(100);
      } catch (error) {
        handleError(error, 'directory');
        return;
      } finally {
        setLoading(false);
        setLoadingType('default');
        setProgress(undefined);
        setLoadingMessage('');
      }
    }

    // 展开目录
    if (!expandedKeys.includes(path)) {
      setExpandedKeys(prev => [...prev, path]);
    }
  };

  // 获取文件类型
  const getFileType = (fileName) => {
    if (fileName.endsWith('.py')) return 'python';
    if (fileName.endsWith('.java')) return 'java';
    if (fileName.endsWith('.go')) return 'go';
    if (fileName.endsWith('.cpp') || fileName.endsWith('.h') || fileName.endsWith('.hpp')) return 'cpp';
    if (fileName.endsWith('.cs')) return 'csharp';
    return null;
  };

  return (
    <Card
      title="代码获取方式"
      extra={
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>选择平台:</span>
          <Radio.Group
            value={gitPlatform}
            onChange={(e) => {
              setLoadingType('switch');
              setLoadingMessage('切换平台中...');
              setGitPlatform(e.target.value);
              setRepositories([]);
              setSelectedRepo(null);
              setDirectories([]);
              setSelectedPath('');

              setError('');
              setWarning('');
              setInfo('');
              setProgress(undefined);
              setTimeout(() => setLoadingType('default'), 500);
            }}
            size="small"
          >
            <Radio.Button value="github" style={{ minWidth: '90px', textAlign: 'center' }}>
              <GithubOutlined style={{ marginRight: '4px' }} />
              GitHub
            </Radio.Button>
            <Radio.Button value="gitlab" style={{ minWidth: '90px', textAlign: 'center' }}>
              <GitlabOutlined style={{ marginRight: '4px' }} />
              GitLab
            </Radio.Button>
          </Radio.Group>
        </div>
      }
    >
      <MessageDisplay error={error} warning={warning} info={info} onErrorClear={() => setError('')} />

      {/* 访问模式选择 */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 8 }}>
          {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} 访问模式:
        </label>
        <Radio.Group
          value={gitMode}
          onChange={(e) => {
            setGitMode(e.target.value);
            setRepositories([]);
            setSelectedRepo(null);
            setDirectories([]);
            setSelectedPath('');

            setError('');
            setWarning('');
            setInfo('');
          }}
        >
          <Radio.Button value="token">
            <Tooltip title={`使用${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}令牌浏览仓库列表`}>
              🔑 浏览仓库
            </Tooltip>
          </Radio.Button>
          <Radio.Button value="url">
            <Tooltip title={`直接输入${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库URL进行克隆`}>
              🔗 直接仓库URL
            </Tooltip>
          </Radio.Button>
        </Radio.Group>
      </div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
          <Switch
            checked={useCache}
            onChange={setUseCache}
            style={{ marginRight: 8 }}
          />
          <span>启用文件缓存</span>
        </div>
        {cacheStats && (
          <div style={{ fontSize: '12px', color: '#666' }}>
            <div>缓存大小: {cacheStats.size}</div>
            <div>缓存项数: {cacheStats.count}</div>
            <Button size="small" onClick={async () => {
              try {
                await FileSystemCache.clear();
                setInfo('缓存已清除');
                await updateCacheStats();
              } catch (error) {
                handleError(error, 'cache');
              }
            }}>
              清除缓存
            </Button>
          </div>
        )}
      </div>
      <div style={{ marginBottom: 16 }}>
        {/* 服务器地址输入 */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>
            {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} 服务器地址:
            <Tooltip title={`输入自定义服务器地址，留空则使用默认地址 (${gitPlatform === 'github' ? 'github.com' : 'gitlab.com'})`}>
              <QuestionCircleOutlined style={{ marginLeft: 8 }} />
            </Tooltip>
          </label>
            <Input
              value={gitPlatform === 'github' ? githubServerUrl : gitlabServerUrl}
              onChange={e => {
                if (gitPlatform === 'github') {
                  setGithubServerUrl(e.target.value);
                } else {
                  setGitlabServerUrl(e.target.value);
                }
              }}
              style={{ width: '70%', marginRight: 8 }}
              placeholder={gitPlatform === 'github'
                ? "例如: https://github.com 或 https://github.enterprise.com"
                : "例如: https://gitlab.com 或 http://172.16.1.30"
              }
              addonBefore={gitPlatform === 'github' ? <GithubOutlined /> : <GitlabOutlined />}
            />
            <Button
              size="small"
              onClick={() => {
                if (gitPlatform === 'github') {
                  setGithubServerUrl('https://github.com');
                } else {
                  setGitlabServerUrl('https://gitlab.com');
                }
              }}
            >
              重置为默认
            </Button>

            {/* 预设服务器地址快速选择 */}
            <div style={{ marginTop: 8, fontSize: '12px' }}>
              <span style={{ color: '#666', marginRight: 8 }}>快速选择:</span>
              {gitPlatform === 'github' ? (
                <>
                  <Button
                    size="small"
                    type="link"
                    style={{ padding: '0 4px', height: 'auto' }}
                    onClick={() => setGithubServerUrl('https://github.com')}
                  >
                    GitHub.com
                  </Button>
                  <Button
                    size="small"
                    type="link"
                    style={{ padding: '0 4px', height: 'auto' }}
                    onClick={() => setGithubServerUrl('https://github.enterprise.com')}
                  >
                    Enterprise示例
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    size="small"
                    type="link"
                    style={{ padding: '0 4px', height: 'auto' }}
                    onClick={() => setGitlabServerUrl('https://gitlab.com')}
                  >
                    GitLab.com
                  </Button>
                  <Button
                    size="small"
                    type="link"
                    style={{ padding: '0 4px', height: 'auto' }}
                    onClick={() => setGitlabServerUrl('http://172.16.1.30')}
                  >
                    本地GitLab
                  </Button>
                  <Button
                    size="small"
                    type="link"
                    style={{ padding: '0 4px', height: 'auto' }}
                    onClick={() => setGitlabServerUrl('https://gitlab.company.com')}
                  >
                    企业示例
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* 令牌输入 - 仅在令牌模式下显示 */}
          {gitMode === 'token' && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                {gitPlatform === 'github' ? 'GitHub令牌:' : 'GitLab令牌:'}
                <Tooltip title={`输入您的${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}访问令牌`}>
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </label>
              <Input.Password
                value={gitToken}
                onChange={e => setGitToken(e.target.value)}
                style={{ width: '70%', marginRight: 8 }}
                placeholder={`输入您的${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}访问令牌`}
                status={tokenError ? 'error' : ''}
              />
            </div>
          )}

          {/* 仓库URL输入 - 仅在URL模式下显示 */}
          {gitMode === 'url' && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                {gitPlatform === 'github' ? 'GitHub' : 'GitLab'} 仓库URL:
                <Tooltip title={`输入${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库的完整URL`}>
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
                style={{ width: '70%', marginRight: 8 }}
                placeholder={gitPlatform === 'github'
                  ? "例如: https://github.com/username/repo.git"
                  : "例如: https://gitlab.com/username/repo.git"
                }
              />
            </div>
          )}

          <Button
            onClick={handleLoadRepositories}
            type="primary"
          >
            {gitMode === 'token'
              ? `🔍 浏览${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库`
              : `📥 克隆${gitPlatform === 'github' ? 'GitHub' : 'GitLab'}仓库`
            }
          </Button>

          {tokenError && <div style={{ color: 'red', marginTop: 8 }}>{tokenError}</div>}
        </div>

        {/* 仓库文件区域 - 包含加载状态 */}
        <LoadingIndicator loading={loading} type={loadingType} message={loadingMessage} progress={progress}>
        {repositories.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <Divider orientation="left">仓库文件</Divider>
            {gitMode === 'token' && gitPlatform === 'github' && (
              <Select
                value={selectedRepo}
                onChange={handleRepoChange}
                style={{ width: '100%', marginBottom: 16 }}
                placeholder="选择一个仓库"
                showSearch
                optionFilterProp="children"
              >
                {repositories.map(repo => (
                  <Option key={repo.full_name} value={repo.full_name}>
                    {repo.full_name}
                  </Option>
                ))}
              </Select>
            )}
            {gitMode === 'token' && gitPlatform === 'gitlab' && (
              <Select
                value={selectedRepo}
                onChange={handleRepoChange}
                style={{ width: '100%', marginBottom: 16 }}
                placeholder="选择一个仓库"
                showSearch
                optionFilterProp="children"
              >
                {repositories.map(repo => (
                  <Option key={repo.full_name} value={repo.full_name}>
                    {repo.full_name}
                  </Option>
                ))}
              </Select>
            )}

            {directories.length > 0 && (
              <div style={{ maxHeight: '400px', overflow: 'auto', border: '1px solid #d9d9d9', padding: '16px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                <Tree
                  treeData={directories}
                  onSelect={handleFileSelect}
                  selectedKeys={selectedPath ? [selectedPath] : []}
                  expandedKeys={expandedKeys}
                  onExpand={async (keys, { expanded, node }) => {
                    if (expanded && (!node.children || node.children.length === 0)) {
                      // 如果是展开操作且节点没有子内容，则加载内容
                      await handleDirectoryExpand(node.key, node);
                    } else {
                      // 否则直接更新展开状态
                      setExpandedKeys(keys);
                    }
                  }}
                />
              </div>
            )}
          </div>
        )}
      </LoadingIndicator>

      {/* 已加载的文件区域 - 不受加载状态影响 */}
      {loadedFiles.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Divider orientation="left">已加载的文件</Divider>
          <List
            size="small"
            bordered
            dataSource={[...loadedFiles].sort((a, b) => b.loadedAt - a.loadedAt)}
            renderItem={file => (
              <List.Item
                key={`${file.platform}-${file.repo}-${file.path}`}
                actions={[
                  <Button
                    type="link"
                    size="small"
                    onClick={async () => {
                      try {
                        setGitPlatform(file.platform);
                        // URL模式下不需要令牌
                        const token = gitMode === 'token' ? gitToken : '';
                        const serverUrl = file.platform === 'github' ? githubServerUrl : gitlabServerUrl;
                        await onCodeFetched(file.platform, file.path, token, file.repo, serverUrl);
                      } catch (error) {
                        handleError(error, 'reload');
                      }
                    }}
                  >
                    重新加载
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={file.platform === 'github' ? <GithubOutlined /> : <GitlabOutlined />}
                  title={file.name}
                  description={`${file.repo} (${file.type || '未知类型'})`}
                />
              </List.Item>
            )}
          />
        </div>
      )}
    </Card>
  );
};

export default GitSourceSelector;
