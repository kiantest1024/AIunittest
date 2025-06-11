# AI单元测试生成器

一个基于AI的智能单元测试生成工具，支持多种编程语言，能够自动分析代码并生成高质量的单元测试。

## ✨ 主要特性

- 🤖 **多AI模型支持**: 支持OpenAI GPT、Google Gemini、Anthropic Claude、xAI Grok、DeepSeek等多种AI模型
- 🌍 **多语言支持**: 支持Python、Java、JavaScript、Go、C++、C#等主流编程语言
- 📊 **实时进度显示**: 流式生成，实时显示测试生成进度
- 🔄 **并发控制**: 智能队列管理，支持多用户并发使用
- 📁 **Git集成**: 支持GitHub和GitLab仓库，可直接从代码仓库生成测试
- 💾 **测试保存**: 生成的测试可直接保存到Git仓库
- 🎯 **智能解析**: 自动识别函数、类、方法，生成针对性测试
- 📱 **现代UI**: 响应式设计，支持桌面和移动端

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 14+

### 一键启动

```bash
python start_server.py
```

启动脚本会自动：
- 检查依赖
- 启动后端服务
- 打开浏览器
- 显示访问地址

### 手动启动

如果需要手动启动：

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动后端
cd app
python main.py
```

### 配置AI模型

在 `backend/app/config.py` 中配置您的AI模型API密钥：

```python
AI_MODELS = {
    "deepseek-V3": {
        "provider": "deepseek",
        "api_key": "your-deepseek-api-key",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    }
}
```

## 📖 使用指南

### 基本使用

1. **选择编程语言**: 在下拉菜单中选择您的代码语言
2. **选择AI模型**: 选择用于生成测试的AI模型
3. **输入代码**: 在代码编辑器中粘贴或输入您的代码
4. **生成测试**: 点击"生成测试"按钮开始生成
5. **查看结果**: 在右侧面板查看生成的测试代码

### Git集成

1. **连接仓库**: 在Git标签页中输入仓库信息
2. **浏览文件**: 选择要生成测试的文件
3. **生成测试**: 系统会自动读取文件内容并生成测试
4. **保存测试**: 将生成的测试直接保存到仓库

## 🏗️ 项目结构

```
AIuintCode/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端应用
│   ├── build/              # 构建输出
│   └── src/                # 源代码
├── docs/                   # 文档
├── scripts/                # 工具脚本
├── start_server.py         # 启动脚本
└── README.md              # 项目说明
```

## 🔧 支持的语言和框架

| 语言 | 测试框架 | 状态 |
|------|----------|------|
| Python | pytest | ✅ 完全支持 |
| Java | JUnit 5 | ✅ 完全支持 |
| JavaScript | Jest | ✅ 完全支持 |
| Go | testing | ✅ 完全支持 |
| C++ | Google Test | ✅ 完全支持 |
| C# | NUnit | ✅ 完全支持 |

## 🛠️ 维护工具

### 项目清理

```bash
python scripts/cleanup_project.py
```

清理脚本会：
- 删除Python缓存文件
- 清空日志文件
- 清理临时目录

## 🆘 故障排除

### 常见问题

1. **服务启动失败**
   - 检查Python版本 (需要3.8+)
   - 确认端口8888未被占用
   - 检查依赖是否正确安装

2. **AI模型无响应**
   - 验证API密钥是否正确
   - 检查网络连接
   - 确认模型配置正确

3. **前端无法访问**
   - 确认后端服务正在运行
   - 检查防火墙设置
   - 尝试访问 http://localhost:8888

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [React](https://reactjs.org/) - 前端框架
- [Ant Design](https://ant.design/) - UI组件库
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - 代码编辑器
