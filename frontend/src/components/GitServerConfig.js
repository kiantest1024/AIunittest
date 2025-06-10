import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Button, Select, message, Space, Tooltip } from 'antd';
import { InfoCircleOutlined, GithubOutlined, GitlabOutlined } from '@ant-design/icons';

const { Option } = Select;

const GitServerConfig = ({ visible, onCancel, onOk, platform, initialValues = {} }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 预设的服务器配置
  const presetServers = {
    github: [
      { label: 'GitHub.com (公共)', value: 'https://github.com', description: '公共GitHub服务' },
      { label: 'GitHub Enterprise (自定义)', value: '', description: '企业版GitHub服务器' }
    ],
    gitlab: [
      { label: 'GitLab.com (公共)', value: 'https://gitlab.com', description: '公共GitLab服务' },
      { label: '本地GitLab (172.16.1.30)', value: 'http://172.16.1.30', description: '本地GitLab实例' },
      { label: '自定义GitLab服务器', value: '', description: '自定义GitLab实例' }
    ]
  };

  useEffect(() => {
    if (visible) {
      // 设置默认值
      const defaultValues = {
        platform: platform || 'github',
        server_url: initialValues.server_url || (platform === 'gitlab' ? 'https://gitlab.com' : 'https://github.com'),
        token: initialValues.token || '',
        ...initialValues
      };
      form.setFieldsValue(defaultValues);
    }
  }, [visible, platform, initialValues, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // 标准化服务器URL
      let serverUrl = values.server_url.trim();
      if (serverUrl && !serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
        // 对于IP地址使用http，对于域名使用https
        const isIP = /^(\d{1,3}\.){3}\d{1,3}(:\d+)?$/.test(serverUrl);
        serverUrl = isIP ? `http://${serverUrl}` : `https://${serverUrl}`;
      }

      const config = {
        ...values,
        server_url: serverUrl
      };

      onOk(config);
    } catch (error) {
      console.error('表单验证失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePresetChange = (value) => {
    form.setFieldsValue({ server_url: value });
  };

  const currentPlatform = form.getFieldValue('platform') || platform || 'github';
  const currentPresets = presetServers[currentPlatform] || [];

  return (
    <Modal
      title={
        <Space>
          {currentPlatform === 'github' ? <GithubOutlined /> : <GitlabOutlined />}
          配置 {currentPlatform === 'github' ? 'GitHub' : 'GitLab'} 服务器
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          platform: platform || 'github',
          server_url: platform === 'gitlab' ? 'https://gitlab.com' : 'https://github.com'
        }}
      >
        <Form.Item
          name="platform"
          label="平台类型"
          rules={[{ required: true, message: '请选择平台类型' }]}
        >
          <Select disabled={!!platform}>
            <Option value="github">
              <Space>
                <GithubOutlined />
                GitHub
              </Space>
            </Option>
            <Option value="gitlab">
              <Space>
                <GitlabOutlined />
                GitLab
              </Space>
            </Option>
          </Select>
        </Form.Item>

        <Form.Item
          label={
            <Space>
              服务器预设
              <Tooltip title="选择预设的服务器配置，或选择自定义输入">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
        >
          <Select
            placeholder="选择预设服务器或自定义"
            onChange={handlePresetChange}
            allowClear
          >
            {currentPresets.map((preset, index) => (
              <Option key={index} value={preset.value}>
                <div>
                  <div>{preset.label}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>{preset.description}</div>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="server_url"
          label={
            <Space>
              服务器地址
              <Tooltip title="输入完整的服务器地址，如 https://github.com 或 http://172.16.1.30">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
          rules={[
            { required: true, message: '请输入服务器地址' },
            {
              pattern: /^(https?:\/\/)?[\w\-.]+(:\d+)?(\/.*)?$/,
              message: '请输入有效的服务器地址'
            }
          ]}
        >
          <Input
            placeholder={`如: ${currentPlatform === 'github' ? 'https://github.com' : 'https://gitlab.com'} 或 http://172.16.1.30`}
            addonBefore={currentPlatform === 'github' ? <GithubOutlined /> : <GitlabOutlined />}
          />
        </Form.Item>

        <Form.Item
          name="token"
          label={
            <Space>
              访问令牌
              <Tooltip title={`输入您的 ${currentPlatform === 'github' ? 'GitHub Personal Access Token' : 'GitLab Personal Access Token'}`}>
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
          rules={[{ required: true, message: '请输入访问令牌' }]}
        >
          <Input.Password
            placeholder={`输入 ${currentPlatform === 'github' ? 'GitHub' : 'GitLab'} Personal Access Token`}
          />
        </Form.Item>

        <div style={{ background: '#f6f8fa', padding: '12px', borderRadius: '6px', marginTop: '16px' }}>
          <h4 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>💡 配置说明：</h4>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#666' }}>
            <li><strong>默认服务器</strong>: 使用公共的 {currentPlatform === 'github' ? 'GitHub.com' : 'GitLab.com'} 服务</li>
            <li><strong>企业服务器</strong>: 支持 GitHub Enterprise 或私有 GitLab 实例</li>
            <li><strong>本地服务器</strong>: 支持本地部署的 Git 服务器</li>
            <li><strong>令牌权限</strong>: 确保令牌具有 {currentPlatform === 'github' ? 'repo' : 'api'} 权限</li>
          </ul>
        </div>
      </Form>
    </Modal>
  );
};

export default GitServerConfig;
