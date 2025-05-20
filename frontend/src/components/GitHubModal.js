import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, Select, Spin, Tree, message, Tooltip } from 'antd';
import {
  QuestionCircleOutlined,
  FolderOpenOutlined,
  FolderOutlined,
  FileOutlined,
  LoadingOutlined
} from '@ant-design/icons';
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
  const [treeLoading, setTreeLoading] = useState(false); // 目录树加载状态
  const [loadingPaths, setLoadingPaths] = useState([]); // 正在加载的路径
  const [expandedKeys, setExpandedKeys] = useState([]); // 展开的节点

  // 从gitInfo或localStorage加载token信息，但不自动发起请求
  useEffect(() => {
    // 只在模态框首次显示时设置token
    if (visible) {
      console.log('Modal became visible');

      if (useSourceGitInfo && gitInfo && gitInfo.token) {
        // 使用源代码的Git信息
        console.log('Using source Git info token');
        setGitToken(gitInfo.token);

        // 如果有仓库信息，设置为待选状态，但不自动加载
        if (gitInfo.repo) {
          console.log('Source has repo info:', gitInfo.repo);
        }

        // 如果有路径信息，记录下来，但不自动设置
        if (gitInfo.path) {
          console.log('Source has path info:', gitInfo.path);
        }
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
      setExpandedKeys([]);
      setLoadingPaths([]);
      setTreeLoading(false);
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
        // 只有目录可以被选择，文件不可选择
        selectable: item.type === 'dir',
        // 如果是目录，添加空的子节点数组，以便显示展开图标
        children: item.type === 'dir' ? [] : null,
        // 添加自定义图标
        icon: item.type === 'file'
          ? <FileOutlined />
          : <FolderOutlined />
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

    // 设置加载状态
    setTreeLoading(true);
    setLoadingPaths(prev => [...prev, key]);

    try {
      // 添加时间戳，避免缓存
      const timestamp = Date.now();
      console.log(`Directory request timestamp: ${timestamp}`);

      // 显示加载提示
      message.loading({ content: `正在加载 ${key} 的内容...`, key: `loading-${key}`, duration: 0 });

      // 构建请求参数
      const repoName = selectedRepo.full_name;
      const path = key;
      console.log(`Fetching directories for repo=${repoName}, token=${gitToken ? 'provided' : 'missing'}, path=${path}`);

      // 发送请求
      const dirs = await getDirectories(repoName, gitToken, path);
      console.log(`API Response:`, dirs);
      console.log(`Loaded ${dirs.length} items in directory: ${key}`);

      // 关闭加载提示
      message.success({ content: `已加载 ${dirs.length} 个项目`, key: `loading-${key}`, duration: 1 });

      // 转换为Tree组件所需的格式
      const treeNodes = dirs.map(item => ({
        title: item.name,
        key: item.path,
        isLeaf: item.type === 'file',
        // 只有目录可以被选择，文件不可选择
        selectable: item.type === 'dir',
        // 如果是目录，添加空的子节点数组，以便显示展开图标
        children: item.type === 'dir' ? [] : null,
        // 添加自定义图标
        icon: item.type === 'file'
          ? <FileOutlined />
          : (loadingPaths.includes(item.path)
              ? <LoadingOutlined />
              : <FolderOutlined />),
        // 保存原始数据
        rawData: item
      }));

      // 记录已加载的目录
      console.log(`Directory ${key} loaded with ${treeNodes.length} children`);
      console.log(`Converted tree nodes:`, treeNodes);

      return treeNodes;
    } catch (error) {
      console.error('Error loading directory:', error);
      console.error('Error details:', error.response?.data || error.message);
      message.error({ content: '加载目录失败: ' + (error.response?.data?.detail || error.message), key: `loading-${key}` });
      return [];
    } finally {
      // 清除加载状态
      setTreeLoading(false);
      setLoadingPaths(prev => prev.filter(path => path !== key));
    }
  };

  const handleSelectDirectory = (selectedKeys) => {
    if (selectedKeys.length > 0) {
      const path = selectedKeys[0];
      console.log(`Setting selected path to: ${path}`);
      setSelectedPath(path);

      // 显示成功消息
      message.success(`已选择目录: ${path}`);
    } else {
      console.log('No directory selected');
    }
  };

  // 递归渲染目录树
  const renderDirectoryTree = (items, level = 0) => {
    return (
      <ul style={{ listStyle: 'none', padding: level === 0 ? 0 : '0 0 0 20px', margin: 0 }}>
        {items.map(item => {
          const isDirectory = !item.isLeaf;
          const isLoading = loadingPaths.includes(item.key);
          const isExpanded = expandedKeys.includes(item.key);

          return (
            <li key={item.key} style={{ margin: '8px 0' }}>
              <div
                className={`directory-item ${isDirectory ? 'directory' : 'file'} ${selectedPath === item.key ? 'selected' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  cursor: isDirectory ? 'pointer' : 'not-allowed',
                  backgroundColor: selectedPath === item.key ? '#e6f7ff' : 'transparent',
                  border: selectedPath === item.key ? '1px solid #1890ff' : '1px solid transparent',
                  transition: 'all 0.3s'
                }}
                onClick={() => {
                  if (isDirectory) {
                    // 选择目录
                    handleSelectDirectory([item.key]);
                  } else {
                    // 文件不可选
                    message.info('请选择一个文件夹作为保存位置');
                  }
                }}
                title={isDirectory ? `点击选择 ${item.title} 作为保存位置` : '文件不可选择'}
              >
                {/* 展开/折叠图标 */}
                {isDirectory && (
                  <span
                    style={{
                      marginRight: '5px',
                      width: '16px',
                      display: 'inline-block',
                      textAlign: 'center',
                      cursor: 'pointer'
                    }}
                    onClick={(e) => {
                      e.stopPropagation(); // 阻止冒泡，避免触发选择

                      // 先设置展开状态，再加载子节点
                      if (isExpanded) {
                        // 折叠
                        console.log(`Collapsing directory: ${item.key}`);
                        setExpandedKeys(prev => prev.filter(key => key !== item.key));
                      } else {
                        // 先设置为展开状态
                        console.log(`Expanding directory: ${item.key}`);
                        setExpandedKeys(prev => [...prev, item.key]);

                        // 如果没有子节点或子节点为空，则加载子节点
                        if (!item.children || item.children.length === 0) {
                          console.log(`Loading children for directory: ${item.key}`);
                          // 使用setTimeout确保展开状态先被设置
                          setTimeout(() => {
                            handleLoadDirectoryAndExpand(item);
                          }, 0);
                        }
                      }
                    }}
                  >
                    {isLoading ? <LoadingOutlined /> : isExpanded ? '▼' : '►'}
                  </span>
                )}

                {/* 文件/文件夹图标 */}
                <span style={{ marginRight: '5px' }}>
                  {isDirectory ? <FolderOutlined style={{ color: '#1890ff' }} /> : <FileOutlined />}
                </span>

                {/* 名称 */}
                <span>{item.title}</span>
              </div>

              {/* 递归渲染子节点 */}
              {isDirectory && isExpanded && item.children && item.children.length > 0 && (
                renderDirectoryTree(item.children, level + 1)
              )}
            </li>
          );
        })}
      </ul>
    );
  };

  // 加载目录并展开
  const handleLoadDirectoryAndExpand = async (node) => {
    try {
      console.log(`Loading and expanding directory: ${node.key}`);

      // 确保节点已经在展开状态
      if (!expandedKeys.includes(node.key)) {
        console.log(`Ensuring directory ${node.key} is in expanded state`);
        setExpandedKeys(prev => [...prev, node.key]);
      }

      // 添加到加载路径
      setLoadingPaths(prev => [...prev, node.key]);

      // 加载子节点
      const children = await handleLoadDirectory(node);
      console.log(`Loaded ${children.length} children for directory: ${node.key}`);

      // 更新目录树 - 使用函数式更新确保使用最新状态
      setDirectories(prevDirectories => {
        // 更新目录树的辅助函数
        const updateTreeData = (list, key, children) => {
          return list.map(item => {
            if (item.key === key) {
              return { ...item, children };
            }
            if (item.children) {
              return { ...item, children: updateTreeData(item.children, key, children) };
            }
            return item;
          });
        };

        // 更新目录树
        const newDirectories = updateTreeData(prevDirectories, node.key, children);
        console.log(`Updated directory tree for ${node.key}`);
        return newDirectories;
      });

      // 再次确保节点保持展开状态
      setTimeout(() => {
        setExpandedKeys(prev => {
          if (!prev.includes(node.key)) {
            console.log(`Re-ensuring directory ${node.key} is expanded`);
            return [...prev, node.key];
          }
          return prev;
        });
      }, 100);
    } catch (error) {
      console.error('Failed to load and expand directory:', error);
      message.error('加载目录失败，请重试');

      // 如果加载失败，从展开状态中移除
      setExpandedKeys(prev => prev.filter(key => key !== node.key));
    } finally {
      // 移除加载状态
      setLoadingPaths(prev => prev.filter(path => path !== node.key));
    }
  };

  const handleSaveToGit = async () => {
    console.log('Save to Git button clicked');
    console.log('Selected repo:', selectedRepo);
    console.log('Selected path:', selectedPath);
    console.log('Tests to save:', tests);

    if (!selectedRepo || !selectedPath) {
      message.error('请选择仓库和目录！');
      return;
    }

    if (tests.length === 0) {
      message.error('没有测试可以保存！');
      return;
    }

    setLoading(true);
    message.loading({ content: '正在保存测试到 GitHub...', key: 'saveGit', duration: 0 });

    try {
      console.log(`Saving tests to ${selectedRepo.full_name} at path ${selectedPath}`);
      const result = await saveToGit(tests, language, selectedRepo.full_name, selectedPath, gitToken);
      console.log('Save to Git result:', result);

      message.success({ content: `测试已成功保存到 GitHub！保存了 ${result.urls.length} 个文件`, key: 'saveGit' });
      onSave();
    } catch (error) {
      console.error('Error saving to Git:', error);
      message.error({ content: '保存到 Git 失败: ' + (error.response?.data?.detail || error.message), key: 'saveGit' });
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
          保存到选中目录
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
                  // 清空仓库列表，避免自动加载
                  setRepositories([]);
                  setSelectedRepo(null);
                  setDirectories([]);
                  setSelectedPath('');
                  setUseSourceGitInfo(true);
                  // 设置token
                  if (gitInfo && gitInfo.token) {
                    setGitToken(gitInfo.token);
                  }
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

              {useSourceGitInfo && gitInfo && gitInfo.token && (
                <Button
                  type="primary"
                  onClick={handleLoadRepositories}
                  style={{ marginLeft: 8 }}
                >
                  加载仓库
                </Button>
              )}
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
            <label style={{ display: 'block', marginBottom: 8 }}>
              选择目录:
              {treeLoading && <Spin size="small" style={{ marginLeft: 8 }} />}
            </label>

            {/* 使用完全重写的目录树实现 */}
            <div
              style={{
                height: '300px',
                overflow: 'auto',
                border: '1px solid #d9d9d9',
                borderRadius: '4px',
                padding: '8px',
                backgroundColor: '#fafafa'
              }}
            >
              {/* 递归渲染目录树 */}
              {renderDirectoryTree(directories)}
            </div>

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
