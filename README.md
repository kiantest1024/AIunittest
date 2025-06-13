# AIunittest - AI单元测试生成工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-14+-green.svg)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个基于AI的单元测试自动生成工具，支持多种编程语言和AI模型，提供Web端AI配置管理功能。

## ✨ 功能特性

### 🤖 AI模型支持
- **系统预置模型**: OpenAI GPT-4、Google Gemini、Anthropic Claude、DeepSeek、Grok
- **自定义模型**: 支持添加任意AI提供商的模型
- **Web端配置**: 密码保护的配置管理界面
- **动态生效**: 配置修改后立即生效，无需重启

### 📝 编程语言支持
- **Python** (pytest, unittest)
- **Java** (JUnit 5, Mockito, AssertJ)
- **Go** (testing, testify)
- **C++** (Google Test)
- **C#** (NUnit, xUnit)

### 🔄 智能生成
- **流式生成**: 实时显示测试用例生成过程
- **智能分析**: 自动分析代码结构和依赖关系
- **框架选择**: 智能选择最适合的测试框架
- **覆盖率优化**: 生成高覆盖率的测试用例

### 🌐 Web界面
- **直观操作**: 简单易用的Web界面
- **实时反馈**: 操作结果立即显示
- **响应式设计**: 适配不同屏幕尺寸
- **任务队列**: 支持并发处理和进度跟踪

### 📁 Git集成
- **GitHub支持**: 支持公开和私有仓库
- **GitLab支持**: 支持自定义GitLab实例
- **代码获取**: 直接从仓库获取源代码
- **测试推送**: 将生成的测试用例推送回仓库

## 🚀 快速开始

### 方式一：使用启动脚本（推荐）

#### Windows
```bash
# 双击运行或在命令行执行
start_services.bat
```

#### Linux/Mac
```bash
# 给脚本执行权限
chmod +x start_services.sh
# 运行脚本
./start_services.sh
```

### 方式二：手动启动

#### 环境要求
- Python 3.8+
- Node.js 14+
- npm 或 yarn

#### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd AIunittest
```

2. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **安装前端依赖**
```bash
cd ../frontend
npm install
```

4. **配置环境变量**
```bash
# 复制环境变量模板
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入你的API密钥
```

5. **启动服务**
```bash
# 启动后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8888

# 启动前端（新终端窗口）
cd ../frontend
npm start
```

6. **访问应用**
打开浏览器访问 http://localhost:3000

## 🔧 AI配置管理

### 访问配置界面
1. 点击Web界面右上角的"AI配置"按钮
2. 输入管理员密码（默认：`password`）
3. 进入配置管理界面

### 管理AI模型
- **查看模型**: 查看所有可用的AI模型
- **添加模型**: 添加自定义AI模型
- **编辑模型**: 修改模型配置（仅限自定义模型）
- **删除模型**: 删除自定义模型
- **设置默认**: 设置默认使用的AI模型

### 配置选项
每个AI模型支持以下配置：
- `provider` - AI提供商（openai、anthropic、google、deepseek、grok）
- `api_key` - API密钥
- `api_base` - API基础地址
- `model` - 模型标识符
- `temperature` - 温度参数 (0-2)
- `max_tokens` - 最大Token数
- `timeout` - 超时时间(秒)

## 📋 使用说明

### 基本使用流程

1. **选择代码来源**
   - 本地文件上传
   - GitHub仓库
   - GitLab仓库

2. **选择目标文件**
   - 浏览项目文件结构
   - 选择要生成测试的源文件

3. **配置生成选项**
   - 选择AI模型
   - 选择编程语言
   - 设置生成参数

4. **生成测试用例**
   - 点击"生成测试用例"按钮
   - 实时查看生成进度
   - 查看生成的测试代码

5. **保存和使用**
   - 下载测试文件
   - 推送到Git仓库
   - 在项目中使用

### Git集成使用

#### GitHub集成
- **公开仓库**: 直接输入仓库URL
- **私有仓库**: 需要提供Personal Access Token
- **推送测试**: 可将生成的测试推送回仓库

#### GitLab集成
- **公开仓库**: 直接输入仓库URL
- **私有仓库**: 需要提供Personal Access Token
- **自定义实例**: 支持自定义GitLab服务器地址

## 📊 项目结构

```
AIunittest/
├── backend/                    # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/               # API接口
│   │   │   └── endpoints.py   # 主要API端点
│   │   ├── services/          # 业务逻辑
│   │   │   ├── ai_factory.py  # AI模型工厂
│   │   │   ├── ai_service.py  # AI服务
│   │   │   ├── test_generator.py # 测试生成器
│   │   │   └── parsers/       # 代码解析器
│   │   ├── models/            # 数据模型
│   │   ├── utils/             # 工具函数
│   │   ├── config.py          # 配置管理
│   │   ├── main.py            # 应用入口
│   │   └── ai_config.json     # AI配置文件
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile            # Docker配置
├── frontend/                  # 前端应用 (React)
│   ├── src/
│   │   ├── components/        # React组件
│   │   │   ├── AIConfigModal.js # AI配置管理
│   │   │   ├── TestGenerator.js # 测试生成器
│   │   │   └── Header.js      # 头部组件
│   │   ├── services/          # API服务
│   │   │   └── api.js         # API调用
│   │   ├── context/           # 状态管理
│   │   ├── utils/             # 工具函数
│   │   └── hooks/             # React Hooks
│   ├── package.json           # Node.js依赖
│   ├── Dockerfile            # Docker配置
│   └── public/                # 静态资源
├── docs/                      # 文档
│   └── AI_CONFIG_GUIDE.md     # AI配置指南
├── logs/                      # 日志目录
│   └── app.log               # 应用日志
├── docker-compose.yml         # Docker编排配置
├── start_services.bat         # Windows启动脚本
├── start_services.sh          # Linux/Mac启动脚本
└── README.md                  # 本文件
```

## 🔒 安全特性

### 密码保护
- **加密存储**: 使用SHA256哈希存储密码
- **默认密码**: `password`（建议首次使用后修改）
- **操作验证**: 所有配置操作需要密码验证

### 权限控制
- **系统模型保护**: 预置模型不能删除或编辑
- **自定义模型管理**: 用户可完全控制自定义模型
- **配置文件保护**: 敏感信息安全存储

## 📚 API文档

启动后端服务后，访问以下地址查看API文档：
- **Swagger UI**: http://localhost:8888/docs
- **ReDoc**: http://localhost:8888/redoc

### 主要API端点

#### 基础功能
- `GET /api/models` - 获取可用AI模型
- `POST /api/generate-test` - 生成测试用例
- `POST /api/generate-test-stream` - 流式生成测试用例

#### AI配置管理
- `GET /api/ai-config/models` - 获取AI模型配置
- `POST /api/ai-config/verify-password` - 验证密码
- `POST /api/ai-config/add-model` - 添加自定义模型
- `POST /api/ai-config/update-model` - 更新模型配置
- `POST /api/ai-config/delete-model` - 删除自定义模型

#### Git集成
- `POST /api/clone-repo` - 克隆Git仓库
- `GET /api/repo-files` - 获取仓库文件列表
- `POST /api/upload-tests` - 上传测试到仓库

## 🧪 功能验证

项目提供完整的功能验证：

测试覆盖：
- ✅ AI配置管理器功能
- ✅ API接口响应
- ✅ 配置文件管理
- ✅ 前端组件完整性

## 🔧 故障排除

### 常见问题

1. **无法启动服务**
   - 检查Python和Node.js版本
   - 确认端口8888和3000未被占用
   - 查看错误日志

2. **AI模型无响应**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 查看API配置是否正确

3. **配置无法保存**
   - 检查文件权限
   - 确认密码是否正确
   - 查看后端日志

### 日志查看
- **后端日志**: 控制台输出或backend.log
- **前端日志**: 浏览器开发者工具控制台

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 代码规范
- Python: 遵循PEP 8
- JavaScript: 使用ESLint配置
- 提交信息: 使用常规提交格式

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和开源社区的支持！

---

**版本**: v1.1.0 (AI配置管理版本)
**更新时间**: 2024年12月
**维护者**: Augment Agent
