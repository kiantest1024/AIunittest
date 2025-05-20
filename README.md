# AI 单元测试生成工具

这个工具使用人工智能自动为多种编程语言生成单元测试。它支持多种 AI 模型，可以通过命令行、图形界面或 Web 界面使用。

## 最新优化 (2023年6月更新)

- **多语言支持**：现在支持 Python、Java、Go、C++ 和 C# 等多种编程语言
- **多 AI 模型支持**：支持 OpenAI、Google Gemini、Anthropic Claude、xAI Grok 和 DeepSeek 等多种 AI 模型
- **代码结构优化**：使用工厂模式和依赖注入，提高代码可维护性
- **错误处理改进**：添加全局异常处理和详细日志记录
- **Docker 优化**：使用多阶段构建减小镜像体积，添加健康检查和资源限制
- **前端优化**：使用 React Context API 进行状态管理，组件拆分和复用
- **启动脚本**：添加一键启动脚本，简化使用流程

## 功能特点

- 自动检测 Git 提交之间更改的 Python 文件
- 解析 Python 文件中的函数和方法
- 使用 OpenAI API 生成高质量的单元测试
- 支持类方法和独立函数的测试生成
- 自动保存生成的测试到指定目录

## 安装要求

- Python 3.8 或更高版本
- Git 命令行工具

### 安装依赖

所有依赖项都列在 `requirements.txt` 文件中。您可以使用以下命令一次性安装所有依赖:

```bash
pip install -r requirements.txt
```

这将安装以下主要依赖:

- requests: 用于API调用
- pytest: 用于运行生成的测试
- tk: 用于GUI界面
- fastapi, uvicorn: 用于Web版本
- javalang: 用于Java代码解析
- pygithub: 用于GitHub集成

## 配置

所有配置选项都在 `config.py` 文件中。您可以根据需要修改这些设置。

### API 密钥设置

在使用前，您需要设置 OpenAI API 密钥。有两种方式:

1. 在 `config.py` 文件中设置:

   ```python
   OPENAI_CONFIG = {
       "api_key": "您的API密钥",
       ...
   }
   ```

2. 设置环境变量:

   ```bash
   # Windows
   set OPENAI_API_KEY=您的API密钥

   # Linux/Mac
   export OPENAI_API_KEY=您的API密钥
   ```

### 其他配置选项

`config.py` 文件包含以下配置部分:

1. **GENERATED_TESTS_DIR**: 生成的测试文件保存目录
2. **OPENAI_CONFIG**: OpenAI API 相关设置
3. **GIT_CONFIG**: Git 相关设置
4. **TEST_CONFIG**: 测试生成相关设置
5. **PROMPT_TEMPLATE**: 用于生成测试的提示模板

## 使用方法

本工具提供三种使用方式：命令行界面、图形用户界面和Web界面。

## 图形用户界面 (GUI)

图形界面提供了更直观的操作方式，适合不熟悉命令行的用户。

### 启动 GUI

```bash
python gui.py
```

### GUI 功能

1. **选择 Python 文件**：通过"浏览"按钮选择要生成测试的 Python 文件
2. **选择 AI 模型**：从下拉菜单中选择要使用的 AI 模型
3. **选择保存目录**：指定生成的测试文件保存位置
4. **选择代码片段**：从加载的文件中选择要测试的函数或方法
5. **生成测试**：点击"生成测试"按钮，使用选定的 AI 模型生成测试
6. **保存测试**：将生成的测试保存到指定目录

### GUI 界面预览

GUI 界面分为左右两个区域：

- 左侧显示源代码
- 右侧显示生成的测试代码

顶部有控制区域，用于选择文件、模型和保存目录。底部有状态栏，显示当前操作状态。

## Web界面

Web界面是最新添加的功能，提供了通过浏览器访问的方式，支持多种编程语言和AI模型。

### 启动Web服务

有三种方式启动Web服务：

#### 1. 使用启动脚本（最简单）

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

启动脚本会自动启动后端和前端服务，并打开浏览器访问Web界面。

#### 2. 使用Docker Compose（推荐用于生产环境）

```bash
# 复制环境变量示例文件并编辑
cp .env.example .env
# 编辑.env文件，填入您的API密钥

# 启动服务
docker-compose up -d
```

服务启动后，打开浏览器访问 [http://localhost](http://localhost) 即可使用Web界面。

#### 3. 手动启动（适用于开发环境）

```bash
# 启动后端服务
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 在另一个终端中启动前端服务
cd frontend
npm install
npm start
```

后端服务启动后，打开浏览器访问 [http://localhost:3000](http://localhost:3000) 即可使用Web界面。

### Web界面功能

1. **选择编程语言**：支持Python、Java、Go、C++和C#
2. **选择AI模型**：支持多种AI模型，如GPT-3.5、GPT-4、Claude等
3. **上传代码文件**：上传要生成测试的代码文件
4. **编辑代码**：直接在浏览器中编辑代码
5. **生成测试**：点击"生成测试"按钮，使用选定的AI模型生成测试
6. **保存测试**：将生成的测试保存到本地文件或GitHub仓库

### Web界面预览

Web界面分为左右两个区域：

- 左侧显示源代码
- 右侧显示生成的测试代码

顶部有控制区域，用于选择语言、模型和上传文件。

## 命令行界面 (CLI)

命令行界面适合自动化脚本和 CI/CD 集成。

### 基本用法

```bash
python initial.py
```

这将比较当前提交 (HEAD) 与其父提交 (HEAD~1) 之间的变更，并为所有更改的 Python 文件生成测试。

### 指定 AI 模型

您可以使用 `--model` 参数指定要使用的 AI 模型：

```bash
python initial.py --model=<model_name>
```

其中 `<model_name>` 是配置文件中定义的模型名称，支持以下模型：

- `openai_gpt35`: OpenAI ChatGPT (GPT-3.5)
- `openai_gpt4`: OpenAI GPT-4
- `azure_openai`: Azure OpenAI 服务
- `anthropic_claude`: Anthropic Claude
- `google_gemini`: Google Gemini
- `xai_grok`: xAI Grok
- `deepseek`: DeepSeek

### 指定提交

```bash
# 指定当前提交
python initial.py [--model=<model_name>] <current_commit>

# 指定前一个提交和当前提交
python initial.py [--model=<model_name>] <previous_commit> <current_commit>
```

### 命令行示例

```bash
# 比较当前提交与其父提交，使用默认模型
python initial.py

# 使用 GPT-4 模型
python initial.py --model=openai_gpt4

# 比较特定提交与其父提交，使用 Claude 模型
python initial.py --model=anthropic_claude abc123def456

# 比较两个特定提交，使用 Azure OpenAI
python initial.py --model=azure_openai abc123def456 ghi789jkl012
```

## 生成的测试

生成的测试将保存在 `tests/generated` 目录中。每个测试文件的命名格式为:

- 对于函数: `test_generated_<原文件名>_<函数名>.py`
- 对于方法: `test_generated_<原文件名>_<类名>_<方法名>.py`

## 详细配置选项

您可以在 `config.py` 文件中修改以下设置:

```python
# 定义生成的测试文件保存目录
GENERATED_TESTS_DIR = pathlib.Path("tests/generated")

# AI 模型配置
AI_MODELS = {
    # 当前使用的模型名称
    "current_model": "openai_gpt35",

    # 可用模型配置
    "models": {
        # OpenAI GPT-3.5 配置
        "openai_gpt35": {
            "provider": "openai",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),  # 优先从环境变量获取API密钥
            "api_base": "https://api.openai.com/v1",  # OpenAI API 基础 URL
            "model": "gpt-3.5-turbo",  # 使用的 AI 模型
            "temperature": 0.7,  # 生成的随机性 (0.0-1.0)
            "max_tokens": 2000,  # 生成的最大令牌数
            "timeout": 30,  # API 请求超时时间（秒）
        },

        # OpenAI GPT-4 配置
        "openai_gpt4": {
            "provider": "openai",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        },

        # Azure OpenAI 配置
        "azure_openai": {
            "provider": "azure_openai",
            "api_key": os.environ.get("AZURE_OPENAI_API_KEY", ""),
            "api_base": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            "deployment_name": os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            "api_version": "2023-05-15",
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 30,
        },

        # Anthropic Claude 配置
        "anthropic_claude": {
            "provider": "anthropic",
            "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "api_base": "https://api.anthropic.com/v1",
            "model": "claude-2",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        }
    }
}

# Git配置
GIT_CONFIG = {
    "default_current_commit": "HEAD",  # 默认当前提交
    "default_previous_commit": None,   # 默认前一个提交（None表示使用当前提交的父提交）
}

# 测试生成配置
TEST_CONFIG = {
    "test_file_prefix": "test_generated_",  # 生成的测试文件前缀
    "use_pytest": True,  # 使用pytest框架
}
```

## 工作流程

1. 脚本使用 Git 命令获取两个提交之间更改的 Python 文件列表
2. 对每个更改的文件，使用 AST 解析器提取函数和方法
3. 对每个函数或方法，构建提示并调用选定的 AI 模型 API 生成测试代码
4. 将生成的测试代码保存到 `tests/generated` 目录

## 注意事项

- 确保您的 Git 仓库是最新的，并且工作目录干净
- API 调用可能会产生费用，取决于您选择的 AI 服务提供商的计费方式
- 生成的测试可能需要手动调整以适应特定的项目结构
- 对于复杂的函数，可能需要提供更多上下文或手动编写测试
- 不同的 AI 模型可能会生成质量不同的测试代码，请根据您的需求选择合适的模型

## 故障排除

### 常见问题

1. **后端服务启动失败**

   **问题**: `ModuleNotFoundError: No module named 'app'`

   **解决方案**:
   - 确保从正确的目录运行命令（backend 目录）
   - 使用 `python -m uvicorn app.main:app --reload` 而不是 `uvicorn app.main:app --reload`
   - 如果从 app 目录运行，使用 `uvicorn main:app --reload`

2. **前端构建错误**

   **问题**: `'setLoading' is not defined`

   **解决方案**:
   - 确保已安装所有依赖 `npm install`
   - 检查控制台错误信息
   - 如果是特定组件错误，可能需要修复组件代码

3. **API 请求失败**

   **问题**: 无法连接到后端 API

   **解决方案**:
   - 确保后端服务正在运行
   - 检查前端的代理配置（package.json 中的 proxy 字段）
   - 确保没有防火墙或网络问题阻止连接

### 其他问题

- 如果遇到 Git 命令错误，请确保您在 Git 仓库中运行脚本
- 如果 API 调用失败，请检查您的 API 密钥和网络连接
- 如果生成的测试不完整，尝试增加 `max_tokens` 参数
- 如果某个 AI 模型不可用，尝试切换到其他模型
- 对于 GUI 界面问题，请确保您的 Python 环境支持 Tkinter
- 对于 Web 界面问题：
  - 后端启动失败：检查依赖是否正确安装，API密钥是否设置
  - 前端启动失败：检查Node.js环境是否正确，依赖是否安装
  - Docker问题：确保Docker和Docker Compose已正确安装

## 贡献

欢迎提交问题报告和改进建议。

## 许可

[MIT 许可证](LICENSE)
