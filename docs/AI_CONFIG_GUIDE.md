# AI配置管理指南

## 概述

AIunittest项目现在支持通过Web界面动态配置AI模型，无需重启服务即可添加、修改或删除AI模型配置。

## 主要功能

### 🔐 密码保护
- 所有AI配置操作都需要管理员密码验证
- 默认密码：`password`
- 支持在线修改管理员密码

### 🤖 模型管理
- **系统模型**：预置的AI模型（OpenAI、Anthropic、Google、DeepSeek、Grok）
- **自定义模型**：用户添加的自定义AI模型
- **动态配置**：配置修改后立即生效，无需重启服务

### ⚙️ 配置选项
- 模型名称（自定义）
- AI提供商（OpenAI、Anthropic、Google、DeepSeek、Grok）
- API密钥
- API地址
- 模型标识符
- 温度参数
- 最大Token数
- 超时时间

## 使用方法

### 1. 访问AI配置界面

在Web界面右上角点击 **"AI配置"** 按钮，或直接访问配置页面。

### 2. 密码验证

首次访问需要输入管理员密码：
- 默认密码：`password`
- 建议首次使用后立即修改密码

### 3. 管理模型

#### 查看现有模型
- 在"模型管理"标签页查看所有可用模型
- 系统模型标有"(系统)"标识
- 默认模型标有"(默认)"标识

#### 添加自定义模型
1. 点击"添加自定义模型"按钮
2. 填写模型配置信息：
   ```
   模型名称: my-custom-gpt4
   提供商: openai
   API密钥: sk-your-api-key-here
   API地址: https://api.openai.com/v1
   模型: gpt-4
   温度: 0.7
   最大Token数: 4000
   超时时间: 60
   ```
3. 点击"添加模型"保存

#### 编辑模型
- 点击模型列表中的"编辑"按钮
- 修改配置信息后点击"更新模型"
- 注意：系统模型不能编辑

#### 删除模型
- 点击模型列表中的"删除"按钮
- 确认删除操作
- 注意：系统模型不能删除

#### 设置默认模型
- 点击模型列表中的"设为默认"按钮
- 默认模型将在新的测试生成中自动选中

### 4. 密码管理

在"密码管理"标签页可以修改管理员密码：
1. 输入当前密码
2. 输入新密码（至少6位）
3. 确认新密码
4. 点击"修改密码"

## 配置文件

AI配置信息存储在 `backend/app/ai_config.json` 文件中：

```json
{
  "custom_models": {
    "my-custom-model": {
      "provider": "openai",
      "api_key": "sk-your-key",
      "api_base": "https://api.openai.com/v1",
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 4000,
      "timeout": 60,
      "is_system": false
    }
  },
  "system_models": {
    "deepseek-V3": {
      "provider": "deepseek",
      "api_key": "sk-your-deepseek-key",
      "api_base": "https://api.deepseek.com/v1",
      "model": "deepseek-chat",
      "temperature": 0.7,
      "max_tokens": 4000,
      "timeout": 300,
      "is_system": true
    }
  },
  "default_model": "deepseek-V3",
  "admin_password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "last_updated": "1704067200.0"
}
```

## API接口

### 获取模型列表
```http
GET /api/ai-config/models
```

### 验证密码
```http
POST /api/ai-config/verify-password
Content-Type: application/json

{
  "password": "your-password"
}
```

### 添加模型
```http
POST /api/ai-config/add-model
Content-Type: application/json

{
  "password": "admin-password",
  "model_name": "my-model",
  "model_config": {
    "provider": "openai",
    "api_key": "sk-key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 60
  }
}
```

### 更新模型
```http
POST /api/ai-config/update-model
Content-Type: application/json

{
  "password": "admin-password",
  "model_name": "my-model",
  "model_config": {
    // 更新的配置
  }
}
```

### 删除模型
```http
POST /api/ai-config/delete-model
Content-Type: application/json

{
  "password": "admin-password",
  "model_name": "my-model"
}
```

### 设置默认模型
```http
POST /api/ai-config/set-default-model
Content-Type: application/json

{
  "password": "admin-password",
  "model_name": "my-model"
}
```

## 安全注意事项

1. **密码保护**：所有配置操作都需要密码验证
2. **API密钥安全**：API密钥以明文存储在配置文件中，请确保文件权限安全
3. **HTTPS**：生产环境建议使用HTTPS协议
4. **定期备份**：建议定期备份配置文件

## 故障排除

### 配置不生效
- 检查密码是否正确
- 确认API密钥格式正确
- 查看后端日志获取详细错误信息

### 无法访问配置界面
- 确认后端服务正常运行
- 检查网络连接
- 查看浏览器控制台错误信息

### API密钥错误
- 验证API密钥是否有效
- 检查API地址是否正确
- 确认提供商选择正确

## 更新日志

### v1.1.0 (2024-01-XX)
- ✨ 新增Web端AI配置管理界面
- 🔐 添加密码保护机制
- 🤖 支持自定义AI模型配置
- ⚙️ 配置动态生效，无需重启
- 📝 完善配置管理文档

### v1.0.0 (2024-01-XX)
- 🎉 初始版本发布
- 支持多种AI模型
- 单元测试自动生成功能
