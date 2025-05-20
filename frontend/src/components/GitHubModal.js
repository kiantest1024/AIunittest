import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, Select, Spin, Tree, message, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { getRepositories, getDirectories, saveToGit } from '../services/api';

const { Option } = Select;
const { DirectoryTree } = Tree;

/**
 * GitHub保存模态框组件
 *
 * @param {boolean} visible - 是否显示模态框
 * @param {function} onCancel - 取消回调函数
 * @param {function} onSave - 保存成功回调函数
 * @param {Array} tests - 测试结果列表
 * @param {string} language - 编程语言
 * @param {boolean} loading - 是否正在加载
 * @param {function} setLoading - 设置加载状态的函数
 * @param {Object} gitInfo - Git信息，包含token、repo和path
 * @returns {JSX.Element} GitHub保存模态框组件
 */
const GitHubModal = ({ visible, onCancel, onSave, tests, language, loading, setLoading, gitInfo }) => {
  // 状态管理
  const [gitToken, setGitToken] = useState('');
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [directories, setDirectories] = useState([]);
  const [selectedPath, setSelectedPath] = useState('');
  const [tokenError, setTokenError] = useState('');
  const [useSourceGitInfo, setUseSourceGitInfo] = useState(true);

  // 从gitInfo或localStorage加载token和仓库信息
  useEffect(() => {
    // 只在模态框首次显示时加载数据
    if (visible && repositories.length === 0) {
      console.log('Modal became visible, loading repositories...');

      if (useSourceGitInfo && gitInfo && gitInfo.token) {
        // 使用源代码的Git信息
        setGitToken(gitInfo.token);

        // 自动加载仓库
        const loadRepos = async () => {
          setLoading(true);
          try {
            console.log('Loading repositories with token:', gitInfo.token ? 'token provided' : 'no token');
            const repos = await getRepositories(gitInfo.token);
            console.log('Loaded repositories:', repos.length);
            setRepositories(repos);

            // 查找匹配的仓库
            const matchingRepo = repos.find(r => r.full_name === gitInfo.repo);
            if (matchingRepo) {
              console.log('Found matching repository:', matchingRepo.full_name);
              // 自动选择仓库
              setSelectedRepo(matchingRepo);

              // 加载目录
              console.log('Loading directories for repository:', matchingRepo.full_name);
              const dirs = await getDirectories(matchingRepo.full_name, gitInfo.token, '');
              const treeData = dirs.map(item => ({
                title: item.name,
                key: item.path,
                isLeaf: item.type === 'file',
                selectable: item.type === 'dir'
              }));

              setDirectories(treeData);

              // 自动选择路径
              if (gitInfo.path) {
                console.log('Setting selected path:', gitInfo.path);
                setSelectedPath(gitInfo.path);
              }
            }
          } catch (error) {
            console.error('Error loading repositories:', error);
            message.error('加载仓库失败，请手动选择');
          } finally {
            setLoading(false);
          }
        };

        loadRepos();
      } else {
        // 使用localStorage中保存的token
        const savedToken = localStorage.getItem('github_token');
        if (savedToken) {
          console.log('Using saved token from localStorage');
          setGitToken(savedToken);
        }
      }
    }

    // 当模态框关闭时重置状态
    if (!visible) {
      console.log('Modal closed, resetting state');
      setRepositories([]);
      setSelectedRepo(null);
      setDirectories([]);
      setSelectedPath('');
    }
  }, [visible, gitInfo, useSourceGitInfo, setLoading, repositories.length]);

  // 加载GitHub仓库列表
  const handleLoadRepositories = async () => {
    if (!gitToken) {
      setTokenError('Please enter a GitHub token!');
      message.error('Please enter a GitHub token!');
      return;
    }

    setTokenError('');
    setLoading(true);

    try {
      console.log('Manually loading repositories with token');

      // 保存token到localStorage
      localStorage.setItem('github_token', gitToken);

      // 使用防抖，避免多次请求
      const timestamp = Date.now();
      console.log(`Repository request timestamp: ${timestamp}`);

      const repos = await getRepositories(gitToken);
      console.log(`Loaded ${repos.length} repositories manually`);

      // 重置相关状态
      setRepositories(repos);
      setSelectedRepo(null);
      setDirectories([]);
      setSelectedPath('');

      if (repos.length === 0) {
        message.warning('No repositories found for this token. Make sure you have access to repositories.');
      }
    } catch (error) {
      console.error('Error loading repositories:', error);
      setTokenError('Invalid token or network error');
      message.error('Failed to load repositories: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRepository = async (repo) => {
    console.log(`Selecting repository: ${repo.full_name}`);

    // 先更新状态，避免重复选择
    setSelectedRepo(repo);
    setDirectories([]);
    setSelectedPath('');
    setLoading(true);

    try {
      console.log(`Loading directories for repository: ${repo.full_name}`);
      const dirs = await getDirectories(repo.full_name, gitToken, '');
      console.log(`Loaded ${dirs.length} directories`);

      // 转换为Tree组件所需的格式
      const treeData = dirs.map(item => ({
        title: item.name,
        key: item.path,
        isLeaf: item.type === 'file',
        selectable: item.type === 'dir'
      }));

      setDirectories(treeData);
    } catch (error) {
      console.error('Error loading directories:', error);
      message.error('Failed to load directories: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDirectory = async (treeNode) => {
    const { key } = treeNode;
    console.log(`Loading directory: ${key}`);

    // 不设置全局loading状态，避免重新渲染
    // 使用局部变量跟踪加载状态
    let isLoading = true;

    try {
      // 添加时间戳，避免缓存
      const timestamp = Date.now();
      console.log(`Directory request timestamp: ${timestamp}`);

      const dirs = await getDirectories(selectedRepo.full_name, gitToken, key);
      console.log(`Loaded ${dirs.length} items in directory: ${key}`);

      // 转换为Tree组件所需的格式
      return dirs.map(item => ({
        title: item.name,
        key: item.path,
        isLeaf: item.type === 'file',
        selectable: item.type === 'dir'
      }));
    } catch (error) {
      console.error('Error loading directory:', error);
      message.error('Failed to load directory: ' + (error.response?.data?.detail || error.message));
      return [];
    } finally {
      isLoading = false;
    }
  };

  const handleSelectDirectory = (selectedKeys) => {
    if (selectedKeys.length > 0) {
      setSelectedPath(selectedKeys[0]);
    }
  };

  const handleSaveToGit = async () => {
    if (!selectedRepo || !selectedPath) {
      message.error('Please select a repository and directory!');
      return;
    }

    if (tests.length === 0) {
      message.error('No tests to save!');
      return;
    }

    setLoading(true);

    try {
      await saveToGit(tests, language, selectedRepo.full_name, selectedPath, gitToken);

      message.success('Tests saved to GitHub successfully!');
      onSave();
    } catch (error) {
      console.error('Error saving to Git:', error);
      message.error('Failed to save to Git: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="保存到GitHub"
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button
          key="save"
          type="primary"
          onClick={handleSaveToGit}
          loading={loading}
          disabled={!selectedRepo || !selectedPath}
        >
          保存
        </Button>
      ]}
      width={800}
    >
      <Spin spinning={loading}>
        {gitInfo && gitInfo.token && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>
              使用源代码的Git信息:
              <Tooltip title="使用获取源代码时的Git信息">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Tooltip>
            </label>
            <div>
              <Button
                type={useSourceGitInfo ? "primary" : "default"}
                onClick={() => {
                  console.log('Switching to use source Git info');
                  // 清空仓库列表，触发重新加载
                  setRepositories([]);
                  setUseSourceGitInfo(true);
                }}
                style={{ marginRight: 8 }}
              >
                使用源代码Git信息
              </Button>
              <Button
                type={!useSourceGitInfo ? "primary" : "default"}
                onClick={() => {
                  console.log('Switching to manual selection');
                  // 清空仓库列表，避免自动加载
                  setRepositories([]);
                  setSelectedRepo(null);
                  setDirectories([]);
                  setSelectedPath('');
                  setUseSourceGitInfo(false);
                }}
              >
                手动选择
              </Button>
            </div>
          </div>
        )}

        {(!useSourceGitInfo || !gitInfo || !gitInfo.token) && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>
              GitHub令牌:
              <Tooltip title="输入您的GitHub个人访问令牌，需要repo权限">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Tooltip>
            </label>
            <Input.Password
              value={gitToken}
              onChange={e => setGitToken(e.target.value)}
              style={{ width: '70%', marginRight: 8 }}
              placeholder="输入您的GitHub个人访问令牌"
              status={tokenError ? 'error' : ''}
            />
            <Button
              onClick={handleLoadRepositories}
              type="primary"
            >
              加载仓库
            </Button>
            {tokenError && <div style={{ color: 'red', marginTop: 8 }}>{tokenError}</div>}
          </div>
        )}

        {repositories.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>选择仓库:</label>
            <Select
              style={{ width: '100%' }}
              placeholder="选择一个仓库"
              onChange={value => {
                const repo = repositories.find(r => r.full_name === value);
                if (repo) handleSelectRepository(repo);
              }}
              value={selectedRepo?.full_name}
            >
              {repositories.map(repo => (
                <Option key={repo.full_name} value={repo.full_name}>
                  {repo.full_name}
                </Option>
              ))}
            </Select>
          </div>
        )}

        {directories.length > 0 && (
          <div>
            <label style={{ display: 'block', marginBottom: 8 }}>选择目录:</label>
            <DirectoryTree
              treeData={directories}
              onSelect={handleSelectDirectory}
              loadData={handleLoadDirectory}
              style={{ height: '300px', overflow: 'auto' }}
            />
            {selectedPath && (
              <div style={{ marginTop: 8 }}>
                已选择路径: <strong>{selectedPath}</strong>
              </div>
            )}
          </div>
        )}
      </Spin>
    </Modal>
  );
};

export default GitHubModal;
