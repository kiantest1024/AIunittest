import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Select, Spin, Tree, message, Tooltip, List, Tag, Divider } from 'antd';
import {
  QuestionCircleOutlined,
  GithubOutlined,
  FileOutlined,
  FolderOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  FileMarkdownOutlined,
  FileJpgOutlined,
  FilePdfOutlined,
  FileZipOutlined,
  FileUnknownOutlined
} from '@ant-design/icons';
import { getRepositories, getDirectories } from '../services/api';

const { Option } = Select;

/**
 * Git代码获取组件
 *
 * @param {function} onCodeFetched - 代码获取成功回调函数
 * @param {boolean} loading - 是否正在加载
 * @param {function} setLoading - 设置加载状态的函数
 * @returns {JSX.Element} Git代码获取组件
 */
const GitCodeFetcher = ({ onCodeFetched, loading, setLoading }) => {
  // 状态管理
  const [gitToken, setGitToken] = useState('');
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [directories, setDirectories] = useState([]);
  const [selectedPath, setSelectedPath] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [tokenError, setTokenError] = useState('');
  const [loadedFiles, setLoadedFiles] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [expandedKeys, setExpandedKeys] = useState([]);

  // 从localStorage加载token
  useEffect(() => {
    const savedToken = localStorage.getItem('github_token');
    if (savedToken) {
      setGitToken(savedToken);
    }
  }, []);

  // 加载GitHub仓库列表
  const handleLoadRepositories = async () => {
    if (!gitToken) {
      setTokenError('请输入GitHub令牌！');
      message.error('请输入GitHub令牌！');
      return;
    }

    setTokenError('');
    setLoading(true);

    try {
      // 保存token到localStorage
      localStorage.setItem('github_token', gitToken);

      const repos = await getRepositories(gitToken);
      setRepositories(repos);
      setSelectedRepo(null);
      setDirectories([]);
      setSelectedPath('');
      setSelectedFile(null);

      if (repos.length === 0) {
        message.warning('未找到仓库。请确保您有权限访问仓库。');
      } else {
        message.success(`成功加载 ${repos.length} 个仓库`);
      }
    } catch (error) {
      console.error('加载仓库失败:', error);
      setTokenError('无效的令牌或网络错误');
      message.error('加载仓库失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 处理仓库选择
  const handleRepoChange = async (value) => {
    setSelectedRepo(value);
    setDirectories([]);
    setSelectedPath('');
    setSelectedFile(null);

    if (!value) return;

    // 查找选中的仓库对象
    const repo = repositories.find(r => r.full_name === value);
    if (repo) {
      setActiveRepo(repo);
    }

    setLoading(true);

    try {
      const dirs = await getDirectories(value, gitToken, '');
      setDirectories(buildTreeData(dirs));
    } catch (error) {
      console.error('加载目录失败:', error);
      message.error('加载目录失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 处理目录树选择
  const handleTreeSelect = async (selectedKeys, info) => {
    if (selectedKeys.length === 0) return;

    const path = selectedKeys[0];
    setSelectedPath(path);

    // 如果是文件，则获取文件内容
    if (info.node.isLeaf) {
      const fileType = getFileType(info.node.title);
      const newFile = {
        path: path,
        name: info.node.title,
        type: fileType,
        repo: selectedRepo,
        repoDetails: activeRepo,
        loadedAt: new Date()
      };

      setSelectedFile(newFile);

      // 添加到已加载文件列表，避免重复
      setLoadedFiles(prevFiles => {
        const fileExists = prevFiles.some(f => f.path === path && f.repo === selectedRepo);
        if (!fileExists) {
          return [...prevFiles, newFile];
        }
        return prevFiles;
      });

      // 通知父组件
      if (onCodeFetched) {
        onCodeFetched(path, gitToken, selectedRepo);
      }
    } else {
      // 如果是目录，则加载子目录
      setLoading(true);

      try {
        console.log(`Loading directory: repo=${selectedRepo}, path=${path}`);
        const dirs = await getDirectories(selectedRepo, gitToken, path);
        console.log('Directories loaded:', dirs);

        if (dirs && dirs.length > 0) {
          // 更新目录树
          updateTreeData(directories, path, buildTreeData(dirs));
          console.log('Directory tree updated');
        } else {
          console.log('No directories found');
          message.info('该目录为空');
        }
      } catch (error) {
        console.error('加载子目录失败:', error);
        message.error('加载子目录失败: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  // 获取文件图标
  const getFileIcon = (fileName) => {
    if (!fileName) return <FileUnknownOutlined />;

    const ext = fileName.split('.').pop().toLowerCase();

    switch (ext) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
      case 'py':
      case 'java':
      case 'go':
      case 'cpp':
      case 'c':
      case 'h':
      case 'hpp':
      case 'cs':
      case 'php':
      case 'rb':
      case 'swift':
      case 'kt':
      case 'rs':
        return <FileTextOutlined style={{ color: '#1890ff' }} />;
      case 'md':
      case 'markdown':
        return <FileMarkdownOutlined style={{ color: '#722ed1' }} />;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'svg':
        return <FileJpgOutlined style={{ color: '#13c2c2' }} />;
      case 'pdf':
        return <FilePdfOutlined style={{ color: '#fa541c' }} />;
      case 'zip':
      case 'rar':
      case 'tar':
      case 'gz':
      case '7z':
        return <FileZipOutlined style={{ color: '#faad14' }} />;
      default:
        return <FileOutlined />;
    }
  };

  // 构建目录树数据
  const buildTreeData = (dirs) => {
    return dirs.map(dir => ({
      title: dir.name,
      key: dir.path,
      isLeaf: dir.type === 'file',
      children: dir.type === 'dir' ? [] : null,
      icon: dir.type === 'dir' ? <FolderOutlined style={{ color: '#faad14' }} /> : getFileIcon(dir.name)
    }));
  };

  // 更新目录树数据
  const updateTreeData = (list, key, children) => {
    // 创建一个新的数组，避免直接修改原数组
    const updatedList = list.map(node => {
      if (node.key === key) {
        // 找到匹配的节点，更新其子节点
        return {
          ...node,
          children
        };
      }

      if (node.children) {
        // 递归更新子节点
        return {
          ...node,
          children: updateTreeData(node.children, key, children)
        };
      }

      // 保持节点不变
      return node;
    });

    // 更新状态
    setDirectories(updatedList);

    // 返回更新后的列表
    return updatedList;
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

  // 重新加载文件
  const handleReloadFile = (file) => {
    setSelectedFile(file);
    setSelectedRepo(file.repo);
    setSelectedPath(file.path);

    // 通知父组件
    if (onCodeFetched) {
      onCodeFetched(file.path, gitToken, file.repo);
    }

    message.success(`已重新加载文件: ${file.name}`);
  };

  // 清除已加载文件列表
  const handleClearLoadedFiles = () => {
    setLoadedFiles([]);
    message.info('已清除加载历史');
  };

  return (
    <Card title={
      <div>
        <GithubOutlined style={{ marginRight: 8 }} />
        从GitHub获取代码
      </div>
    }>
      <Spin spinning={loading}>
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

        {repositories.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <Divider orientation="left">
              已加载的仓库 ({repositories.length})
            </Divider>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                选择仓库:
              </label>
              <Select
                value={selectedRepo}
                onChange={handleRepoChange}
                style={{ width: '100%' }}
                placeholder="选择一个仓库"
                showSearch
                optionFilterProp="children"
                filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
              >
                {repositories.map(repo => (
                  <Option key={repo.full_name} value={repo.full_name}>{repo.full_name}</Option>
                ))}
              </Select>
            </div>

            <List
              className="loaded-repos-list"
              size="small"
              bordered
              dataSource={repositories}
              renderItem={repo => (
                <List.Item
                  key={repo.full_name}
                  actions={[
                    <Button
                      type="link"
                      size="small"
                      onClick={() => handleRepoChange(repo.full_name)}
                      icon={<FolderOutlined />}
                    >
                      浏览
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<GithubOutlined style={{ fontSize: 16 }} />}
                    title={repo.full_name}
                    description={
                      <div>
                        {repo.description && (
                          <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                            {repo.description.length > 50 ? repo.description.substring(0, 50) + '...' : repo.description}
                          </div>
                        )}
                        <div>
                          {repo.private && <Tag color="red">私有</Tag>}
                          {!repo.private && <Tag color="green">公开</Tag>}
                          {repo.language && <Tag color="blue">{repo.language}</Tag>}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        )}

        {directories.length > 0 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label>选择文件:</label>
              <div>
                <Button
                  type="link"
                  size="small"
                  onClick={() => setExpandedKeys([])}
                  style={{ marginRight: 8 }}
                >
                  全部收起
                </Button>
                <Button
                  type="link"
                  size="small"
                  onClick={() => {
                    // 获取所有非叶子节点的key
                    const getAllKeys = (nodes) => {
                      let keys = [];
                      nodes.forEach(node => {
                        if (!node.isLeaf) {
                          keys.push(node.key);
                          if (node.children) {
                            keys = [...keys, ...getAllKeys(node.children)];
                          }
                        }
                      });
                      return keys;
                    };

                    setExpandedKeys(getAllKeys(directories));
                  }}
                >
                  全部展开
                </Button>
              </div>
            </div>
            <div style={{ maxHeight: '300px', overflow: 'auto', border: '1px solid #d9d9d9', padding: '8px', borderRadius: '2px' }}>
              <Tree
                treeData={directories}
                onSelect={handleTreeSelect}
                selectedKeys={selectedPath ? [selectedPath] : []}
                expandedKeys={expandedKeys}
                onExpand={(keys) => setExpandedKeys(keys)}
                loadData={async (node) => {
                  // 如果是叶子节点，不需要加载
                  if (node.isLeaf) return;

                  // 加载子节点
                  try {
                    console.log(`Loading children for node: ${node.key}`);
                    const dirs = await getDirectories(selectedRepo, gitToken, node.key);
                    console.log('Children loaded:', dirs);

                    // 更新目录树
                    updateTreeData(directories, node.key, buildTreeData(dirs));

                    // 自动展开当前节点
                    if (!expandedKeys.includes(node.key)) {
                      setExpandedKeys([...expandedKeys, node.key]);
                    }
                  } catch (error) {
                    console.error('加载子目录失败:', error);
                    message.error('加载子目录失败: ' + (error.response?.data?.detail || error.message));
                  }
                }}
              />
            </div>
          </div>
        )}

        {selectedFile && (
          <div style={{ marginTop: 16 }}>
            <div style={{ color: 'green' }}>
              已选择文件: {selectedFile.name}
            </div>
          </div>
        )}

        {/* 已加载文件列表 */}
        {loadedFiles.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Divider orientation="left">
              已加载的代码文件
              <Button
                type="link"
                size="small"
                onClick={handleClearLoadedFiles}
                style={{ marginLeft: 8 }}
              >
                清除历史
              </Button>
            </Divider>
            <List
              className="loaded-files-list"
              size="small"
              bordered
              dataSource={[...loadedFiles].sort((a, b) => b.loadedAt - a.loadedAt)}
              renderItem={file => (
                <List.Item
                  key={`${file.repo}-${file.path}`}
                  actions={[
                    <Button
                      type="link"
                      size="small"
                      onClick={() => handleReloadFile(file)}
                      icon={<CheckCircleOutlined />}
                    >
                      加载
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <FileOutlined
                        style={{
                          fontSize: 16,
                          color: file.type === 'python' ? '#3572A5' :
                                 file.type === 'java' ? '#B07219' :
                                 file.type === 'go' ? '#00ADD8' :
                                 file.type === 'cpp' ? '#F34B7D' :
                                 file.type === 'csharp' ? '#178600' :
                                 '#1890ff'
                        }}
                      />
                    }
                    title={file.name}
                    description={
                      <div>
                        <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                          {file.repo}
                        </div>
                        {file.type && (
                          <Tag color="blue">{file.type}</Tag>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Spin>
    </Card>
  );
};

export default GitCodeFetcher;
