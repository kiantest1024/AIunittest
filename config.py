# -*- coding: utf-8 -*-
"""
配置文件 - AI单元测试生成工具

此文件包含AI单元测试生成工具的所有配置参数。
修改此文件以自定义工具的行为，而不需要更改主代码。
"""

import os
import pathlib

# 定义生成的测试文件保存目录
GENERATED_TESTS_DIR = pathlib.Path("tests/generated")

# AI 模型配置
AI_MODELS = {
    # 当前使用的模型名称
    "current_model": "openai_gpt35",

    # 可用模型配置
    "models": {
        # OpenAI ChatGPT (GPT-3.5) 配置
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
            "model": "claude-3-opus-20240229",  # 最新的Claude模型
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        },

        # Google Gemini 配置
        "google_gemini": {
            "provider": "google",
            "api_key": os.environ.get("GOOGLE_API_KEY", "AIzaSyC4FA2WJ82kygh_toL2oogCzu3E3Z9oeHg"),
            "api_base": "https://generativelanguage.googleapis.com/v1beta",
            "model": "gemini-2.5-flash",
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 30,
        },

        # xAI Grok 配置
        "xai_grok": {
            "provider": "grok",
            "api_key": os.environ.get("GROK_API_KEY", ""),
            "api_base": "https://api.grok.ai/v1",  # 假设的API基础URL
            "model": "grok-1",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        },

        # DeepSeek 配置
        "deepseek": {
            "provider": "deepseek",
            "api_key": os.environ.get("DEEPSEEK_API_KEY", "sk-60715e5eb341470cb8676c88cbdb0f53"),
            "api_base": "https://api.deepseek.com/v1",  # 假设的API基础URL
            "model": "deepseek-reasoner",
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

# 提示模板配置
PROMPT_TEMPLATE = """
请为以下 Python {code_type} 生成单元测试代码:

```python
{code}
```

请生成完整的测试代码，包括必要的导入语句、测试函数和断言。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用 pytest 框架，并遵循以下指南:

1. 测试函数名应以 'test_' 开头
2. 使用描述性的测试函数名称
3. 为每个测试用例添加清晰的注释
4. 包含必要的 mock 对象或测试夹具
5. 使用有意义的断言消息
6. 考虑边缘情况和异常处理

假设可以使用以下导入语句: {import_statement}

请仅返回测试代码，不要包含任何解释或额外的文本。
"""
