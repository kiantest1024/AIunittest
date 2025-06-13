import React, { useState } from 'react';
import {
  Modal, Form, Input, Button, message, Tabs, Table, Space,
  Popconfirm, Select, InputNumber, Card, Alert
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  SettingOutlined, KeyOutlined, SaveOutlined 
} from '@ant-design/icons';
import { 
  getAIModels, verifyAIPassword, changeAIPassword, 
  addAIModel, updateAIModel, deleteAIModel, setDefaultAIModel 
} from '../services/api';

const { TabPane } = Tabs;
const { Option } = Select;

/**
 * AI配置管理模态框组件
 */
const AIConfigModal = ({ visible, onCancel, onConfigUpdated }) => {
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [modelForm] = Form.useForm();
  
  const [loading, setLoading] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [models, setModels] = useState([]);
  const [defaultModel, setDefaultModel] = useState('');
  const [editingModel, setEditingModel] = useState(null);
  const [activeTab, setActiveTab] = useState('models');

  // 加载AI模型配置
  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await getAIModels();
      if (response.success) {
        const modelList = Object.entries(response.models).map(([name, config]) => ({
          key: name,
          name,
          ...config
        }));
        setModels(modelList);
        setDefaultModel(response.default_model);
      } else {
        message.error('加载AI模型配置失败: ' + response.error, 3);
      }
    } catch (error) {
      console.error('Error loading AI models:', error);
      message.error('加载AI模型配置失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 验证密码
  const handlePasswordVerify = async (values) => {
    try {
      setLoading(true);
      const response = await verifyAIPassword(values.password);
      if (response.success && response.valid) {
        setAuthenticated(true);
        message.success('密码验证成功', 3);
        await loadModels();
      } else {
        message.error('密码错误', 3);
      }
    } catch (error) {
      console.error('Error verifying password:', error);
      message.error('密码验证失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handlePasswordChange = async (values) => {
    try {
      setLoading(true);
      const response = await changeAIPassword(values.oldPassword, values.newPassword);
      if (response.success) {
        message.success('密码修改成功', 3);
        passwordForm.resetFields();
      } else {
        message.error('密码修改失败: ' + response.error, 3);
      }
    } catch (error) {
      console.error('Error changing password:', error);
      message.error('密码修改失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 添加/更新模型
  const handleModelSave = async (values) => {
    try {
      setLoading(true);
      
      // 获取当前密码
      const password = form.getFieldValue('password');
      if (!password) {
        message.error('请先验证密码', 3);
        return;
      }

      const modelConfig = {
        provider: values.provider,
        api_key: values.api_key,
        api_base: values.api_base,
        model: values.model,
        temperature: values.temperature || 0.7,
        max_tokens: values.max_tokens || 4000,
        timeout: values.timeout || 60
      };

      let response;
      if (editingModel) {
        response = await updateAIModel(password, editingModel.name, modelConfig);
      } else {
        response = await addAIModel(password, values.name, modelConfig);
      }

      if (response.success) {
        message.success(response.message, 3);
        modelForm.resetFields();
        setEditingModel(null);
        await loadModels();
        if (onConfigUpdated) {
          onConfigUpdated();
        }
      } else {
        message.error(response.error, 3);
      }
    } catch (error) {
      console.error('Error saving model:', error);
      message.error('保存模型失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 删除模型
  const handleModelDelete = async (modelName) => {
    try {
      setLoading(true);
      const password = form.getFieldValue('password');
      const response = await deleteAIModel(password, modelName);
      if (response.success) {
        message.success(response.message, 3);
        await loadModels();
        if (onConfigUpdated) {
          onConfigUpdated();
        }
      } else {
        message.error(response.error, 3);
      }
    } catch (error) {
      console.error('Error deleting model:', error);
      message.error('删除模型失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 设置默认模型
  const handleSetDefault = async (modelName) => {
    try {
      setLoading(true);
      const password = form.getFieldValue('password');
      const response = await setDefaultAIModel(password, modelName);
      if (response.success) {
        message.success(response.message, 3);
        setDefaultModel(modelName);
        if (onConfigUpdated) {
          onConfigUpdated();
        }
      } else {
        message.error(response.error, 3);
      }
    } catch (error) {
      console.error('Error setting default model:', error);
      message.error('设置默认模型失败', 3);
    } finally {
      setLoading(false);
    }
  };

  // 编辑模型
  const handleModelEdit = (model) => {
    setEditingModel(model);
    modelForm.setFieldsValue({
      name: model.name,
      provider: model.provider,
      api_key: model.api_key,
      api_base: model.api_base,
      model: model.model,
      temperature: model.temperature,
      max_tokens: model.max_tokens,
      timeout: model.timeout
    });
    setActiveTab('add-model');
  };

  // 重置表单
  const handleCancel = () => {
    form.resetFields();
    passwordForm.resetFields();
    modelForm.resetFields();
    setAuthenticated(false);
    setEditingModel(null);
    setActiveTab('models');
    onCancel();
  };

  // 模型表格列定义
  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <span>
          {text}
          {text === defaultModel && <span style={{ color: '#52c41a', marginLeft: 8 }}>(默认)</span>}
          {record.is_system && <span style={{ color: '#1890ff', marginLeft: 8 }}>(系统)</span>}
        </span>
      )
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider'
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model'
    },
    {
      title: 'API地址',
      dataIndex: 'api_base',
      key: 'api_base',
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleModelEdit(record)}
            disabled={record.is_system}
          >
            编辑
          </Button>
          {record.name !== defaultModel && (
            <Button 
              type="link" 
              onClick={() => handleSetDefault(record.name)}
            >
              设为默认
            </Button>
          )}
          {!record.is_system && (
            <Popconfirm
              title="确定要删除这个模型吗？"
              onConfirm={() => handleModelDelete(record.name)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  return (
    <Modal
      title={<span><SettingOutlined /> AI配置管理</span>}
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={1000}
      destroyOnClose
    >
      {!authenticated ? (
        <Card title="密码验证" style={{ maxWidth: 400, margin: '0 auto' }}>
          <Alert
            message="访问AI配置需要管理员密码"
            description="请输入管理员密码以继续配置AI模型"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form
            form={form}
            onFinish={handlePasswordVerify}
            layout="vertical"
          >
            <Form.Item
              name="password"
              label="管理员密码"
              rules={[{ required: true, message: '请输入管理员密码' }]}
            >
              <Input.Password 
                placeholder="请输入管理员密码"
                prefix={<KeyOutlined />}
              />
            </Form.Item>
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                block
              >
                验证密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      ) : (
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="模型管理" key="models">
            <div style={{ marginBottom: 16 }}>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditingModel(null);
                  modelForm.resetFields();
                  setActiveTab('add-model');
                }}
              >
                添加自定义模型
              </Button>
            </div>
            <Table
              columns={columns}
              dataSource={models}
              loading={loading}
              pagination={false}
              scroll={{ y: 400 }}
            />
          </TabPane>
          
          <TabPane tab={editingModel ? "编辑模型" : "添加模型"} key="add-model">
            <Form
              form={modelForm}
              onFinish={handleModelSave}
              layout="vertical"
            >
              <Form.Item
                name="name"
                label="模型名称"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input 
                  placeholder="例如: my-custom-model"
                  disabled={!!editingModel}
                />
              </Form.Item>
              
              <Form.Item
                name="provider"
                label="提供商"
                rules={[{ required: true, message: '请选择提供商' }]}
              >
                <Select placeholder="选择AI提供商">
                  <Option value="openai">OpenAI</Option>
                  <Option value="anthropic">Anthropic</Option>
                  <Option value="google">Google</Option>
                  <Option value="deepseek">DeepSeek</Option>
                  <Option value="grok">Grok</Option>
                </Select>
              </Form.Item>
              
              <Form.Item
                name="api_key"
                label="API密钥"
                rules={[{ required: true, message: '请输入API密钥' }]}
              >
                <Input.Password placeholder="请输入API密钥" />
              </Form.Item>
              
              <Form.Item
                name="api_base"
                label="API地址"
                rules={[{ required: true, message: '请输入API地址' }]}
              >
                <Input placeholder="例如: https://api.openai.com/v1" />
              </Form.Item>
              
              <Form.Item
                name="model"
                label="模型名称"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="例如: gpt-4" />
              </Form.Item>
              
              <Form.Item
                name="temperature"
                label="温度"
                initialValue={0.7}
              >
                <InputNumber 
                  min={0} 
                  max={2} 
                  step={0.1} 
                  placeholder="0.7"
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item
                name="max_tokens"
                label="最大Token数"
                initialValue={4000}
              >
                <InputNumber 
                  min={1} 
                  max={100000} 
                  placeholder="4000"
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item
                name="timeout"
                label="超时时间(秒)"
                initialValue={60}
              >
                <InputNumber 
                  min={1} 
                  max={3600} 
                  placeholder="60"
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    icon={<SaveOutlined />}
                  >
                    {editingModel ? '更新模型' : '添加模型'}
                  </Button>
                  <Button 
                    onClick={() => {
                      modelForm.resetFields();
                      setEditingModel(null);
                      setActiveTab('models');
                    }}
                  >
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </TabPane>
          
          <TabPane tab="密码管理" key="password">
            <Card title="修改管理员密码" style={{ maxWidth: 500 }}>
              <Form
                form={passwordForm}
                onFinish={handlePasswordChange}
                layout="vertical"
              >
                <Form.Item
                  name="oldPassword"
                  label="当前密码"
                  rules={[{ required: true, message: '请输入当前密码' }]}
                >
                  <Input.Password placeholder="请输入当前密码" />
                </Form.Item>
                
                <Form.Item
                  name="newPassword"
                  label="新密码"
                  rules={[
                    { required: true, message: '请输入新密码' },
                    { min: 6, message: '密码至少6位' }
                  ]}
                >
                  <Input.Password placeholder="请输入新密码" />
                </Form.Item>
                
                <Form.Item
                  name="confirmPassword"
                  label="确认新密码"
                  dependencies={['newPassword']}
                  rules={[
                    { required: true, message: '请确认新密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('newPassword') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'));
                      },
                    }),
                  ]}
                >
                  <Input.Password placeholder="请再次输入新密码" />
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    icon={<KeyOutlined />}
                  >
                    修改密码
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </TabPane>
        </Tabs>
      )}
    </Modal>
  );
};

export default AIConfigModal;
